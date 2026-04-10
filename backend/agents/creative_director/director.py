"""
Tier -1: Creative Director
specification_v10.md / script_ai_app_specification_v2.md §4 完全準拠。
内部ループ（Self-Critique）により品質を自律的に担保する。

v2 §4.7 の出力スキーマに完全準拠:
- character_concept: string (500-1000字の濃密な概念記述)
- story_outline: string (500-1000字の濃密な概念記述)
- narrative_theme, interestingness_hooks, genre_and_world
- reference_stories, critical_design_notes
- psychological_hints (temperament_direction, values_direction, want_and_need, ghost_wound_hint, lie_hint)
"""

import json
import logging
from typing import Optional

from backend.tools.llm_api import call_llm
from backend.models.character import ConceptPackage
from backend.config import EvaluationProfile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """あなたは「脚本AI」の最上位存在であるCreative Directorです。
あなたの役割は、1人のキャラクターの概念設計（concept_package）を行うことです。

あなたが出力するconcept_packageは、下流の全Phase（A-1マクロプロフィール生成、A-2ミクロパラメータ生成、A-3自伝的エピソード生成、Phase Dイベント列生成）の起点となります。

【重要: character_conceptとstory_outlineについて】
この2つは concept_package の中核であり、下位エージェント（Phase A-1からPhase Dまでの
全Worker）が具体化作業をするときに常に参照する設計拠点です。ここが薄いと、下位エージェントは
何を作ればいいか迷い、AI臭い無難なアウトプットに流れます。

- character_concept は必ず500字以上で、キャラの「大まかな特徴・核・背景・魅力の源泉」を
  概念レベルで濃密に書くこと
- story_outline は必ず500字以上で、物語の「大まかな概要・7日間のあらすじ・通奏低音・
  この1週間の特徴」を概念レベルで濃密に書くこと
- 両者の間に矛盾がないこと

【設計原則】
1. 面白さが最優先。「読みたい」と思わせるキャラクターを設計せよ
2. 内部矛盾（wantとneedのギャップ、気質と規範のギャップ）が面白さの源泉
3. AI臭い無難なキャラクターは不合格。「優しくて元気で好奇心旺盛」は最悪の例
4. 具体性が命。抽象的な記述は全て不合格
5. redemption bias（全てが成長と救済に向かう傾向）を警戒せよ
6. 陰影のある人物を設計せよ。弱さ・恥・後悔を持つキャラクターが面白い
7. 7日間の物語で何が起きるかの骨格を示せ。Day 5が山場

【脚本論のベストプラクティス】
1. Want と Need の構造（McKee系統）
   - Want: キャラが意識的に追求する外的目標
   - Need: 本人が自覚していない本質的な内的必要
   - 両者はしばしば対立する
2. Ghost / Wound（過去の傷）
   - 物語が始まる前に起きた、主人公を脆弱にしている出来事
3. Lie / Misbelief
   - Ghostから形成された誤った世界観・自己認識
4. Character Arc
   - Lieからの解放。ただし7日間で完全解放する必要はなく小さな揺らぎで十分
5. Redemption bias の回避
   - 未解決・曖昧さ・contamination の要素を必ず含める

【心理学的基盤】
- Cloninger精神生物学的気質モデル（NS/HA/RD/Persistence）
- Big Five / HEXACO 性格特性
- Schwartz 19価値理論
- Higgins 自己不一致理論（Ideal/Ought/Actual Self）
- McAdams ナラティブ・アイデンティティ
- Strack & Deutsch Reflective-Impulsive Model

【出力形式】
以下のJSON形式で出力してください:
{
  "character_concept": "500-1000字のキャラクター概念記述（核・背景・魅力の源泉を含む）",
  "story_outline": "500-1000字の物語概念記述（7日間のあらすじ・通奏低音を含む）",
  "narrative_theme": "通奏低音テーマ（1-2文）",
  "interestingness_hooks": ["具体的な面白さのフック1", "フック2", "フック3"],
  "genre_and_world": "ジャンルと世界観（1パラグラフ）",
  "reference_stories": [{"title": "作品名", "author_or_source": "著者", "relevance": "なぜ参照したか"}],
  "critical_design_notes": ["下流への設計指示1", "指示2"],
  "psychological_hints": {
    "temperament_direction": "Cloninger系の気質方向性",
    "values_direction": "Schwartz系の価値観方向性",
    "want_and_need": {
      "want": "外的目標",
      "need": "内的必要",
      "tension": "両者の緊張関係"
    },
    "ghost_wound_hint": "過去の傷の方向性",
    "lie_hint": "誤った信念の方向性"
  }
}

【絶対に守ること】
- AI臭い無難な設定を作らないこと
- 「優しい」「元気」「好奇心旺盛」のような曖昧な形容詞で済ませないこと
- キャラクターには必ず矛盾・陰影・未解決を含めること
- character_concept は必ず500字以上
- story_outline は必ず500字以上
"""

SELF_CRITIQUE_PROMPT = """あなたはCreative Directorの内部批評者です。
以下のconcept_packageを厳しく評価してください。

【評価基準】
[A] 面白さ:
  □ character_concept は500字以上で具体的か
  □ story_outline は500字以上で具体的か
  □ AI臭い無難さが出ていないか
  □ interestingness_hooks は概念的抽象ではなく具体的な状況として書かれているか

[B] 個性の深さ:
  □ want/needのギャップは物語を生むか
  □ ghost_wound_hint と lie_hint が具体的か
  □ temperament_direction と values_direction の間にギャップがあるか

[C] Redemption Bias回避:
  □ 「困難→救済→成長」一辺倒になっていないか
  □ 未解決・曖昧さ・contaminationの要素があるか

[D] 時間的連続性の種:
  □ 7日間通じて現れる通奏低音があるか
  □ story_outlineに1週間のあらすじが読み取れるか
  □ Day 5山場の方向性が示されているか

[E] 整合性:
  □ character_concept と story_outline は矛盾しないか
  □ genre_and_world と character_concept は矛盾しないか

[F] 実装可能性:
  □ 52パラメータとイベント列に落とし込めるか
  □ 下位エージェントが理解できる粒度で書かれているか

【判定】
全項目passなら "verdict": "pass"
1つでも不十分なら "verdict": "refine" と改善指示を出す

出力形式:
{
  "checks": {
    "A_interestingness": {"passed": true/false, "comment": "..."},
    "B_depth": {"passed": true/false, "comment": "..."},
    "C_redemption_bias": {"passed": true/false, "comment": "..."},
    "D_temporal_continuity": {"passed": true/false, "comment": "..."},
    "E_consistency": {"passed": true/false, "comment": "..."},
    "F_implementability": {"passed": true/false, "comment": "..."}
  },
  "verdict": "pass" or "refine",
  "refinement_instructions": "改善指示（refine時のみ）"
}
"""


class CreativeDirector:
    """Tier -1: Creative Director"""
    
    def __init__(self, profile: EvaluationProfile, ws_manager=None):
        self.profile = profile
        self.ws = ws_manager
        self.max_iterations = profile.director_self_critique_max_iterations
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("Creative Director", content, status)
    
    async def run(self, theme: Optional[str] = None) -> ConceptPackage:
        """
        concept_packageを生成する。エージェント自身がツールを駆使して自律的に品質を担保する。
        """
        from backend.tools.llm_api import AgentTool, call_llm_agentic
        
        await self._notify("Creative Directorを起動します（エージェンティック・モード）...")
        
        user_msg = "独創的で面白いキャラクターのconcept_packageを生成してください。必ず事前にsearch_webを用いて面白い関連アイデアや記事を複数回検索し、リサーチを行ってからドラフトを作成してください。character_conceptは500字以上、story_outlineも500字以上で具体的に書いてください。"
        if theme:
            user_msg = f"以下のテーマに基づいて、独創的で面白いキャラクターのconcept_packageを生成してください。必ず事前にsearch_webを用いて面白くユニークな関連情報をリサーチし、インスピレーションを得てからドラフトを作成してください。\n\nテーマ: {theme}"
        
        final_concept_data = None
        self_critique_history = []
        critique_iteration = 0
        
        async def search_web(query: str = None, max_results: int = 3) -> dict:
            """指定したキーワードでWeb検索を行い、上位記事の要約や関連情報を取得する"""
            if not query:
                return {"status": "FAILED", "message": "ERROR: query引数が欠落しています。検索キーワードを指定してください。"}
            
            await self._notify(f"Web検索中: {query}")
            try:
                from duckduckgo_search import DDGS
                
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(r)
                
                if results:
                    return {"status": "SUCCESS", "results": results}
                else:
                    return {"status": "SUCCESS", "message": "No results found."}
            except Exception as e:
                import logging
                logging.getLogger("creative_director").error(f"Web search failed: {e}")
                return {"status": "FAILED", "message": f"Web search explicitly failed: {e}"}

        async def request_critique(concept_package: dict = None) -> dict:
            """現在のドラフトに対する批判的フィードバック（心理学的な矛盾や面白さの採点）を要求する"""
            if not concept_package:
                return {"status": "FAILED", "message": "ERROR: concept_package引数が欠落しています。ツールのパラメータとして、作成したJSONデータを必ず渡してください。自然言語テキストに書き出すだけでは無効です。"}
            nonlocal critique_iteration
            critique_iteration += 1
            await self._notify(f"Self-Critiqueを依頼中...（試行 {critique_iteration}）")
            
            critique_result = await call_llm(
                tier="opus",
                system_prompt=SELF_CRITIQUE_PROMPT,
                user_message=f"以下のconcept_packageを評価してください:\n\n{json.dumps(concept_package, ensure_ascii=False, indent=2)}",
                max_tokens=2048,
                json_mode=True,
                cache_system=True,
            )
            
            critique = critique_result["content"] if isinstance(critique_result["content"], dict) else {}
            self_critique_history.append(critique)
            
            checks = critique.get("checks", {})
            check_summary = []
            for key, val in checks.items():
                status = "✓" if val.get("passed", False) else "✗"
                check_summary.append(f"  [{status}] {key}: {val.get('comment', '')[:60]}")
            
            verdict = critique.get("verdict", "pass")
            await self._notify(f"Self-Critique結果（Verdict: {verdict}）:\n" + "\n".join(check_summary))
            
            if verdict == "pass":
                return {"status": "SUCCESS", "message": "CRITIQUE PASSED. Please call submit_final_concept to finish."}
            else:
                return {"status": "FAILED", "feedback": critique}

        async def submit_final_concept(concept_package: dict = None) -> dict:
            """最終確定版を提出し、ミッションを完了する"""
            if not concept_package:
                return {"status": "FAILED", "message": "ERROR: concept_package引数が欠落しています。最終データをパラメータとして渡してください。"}
            nonlocal final_concept_data
            final_concept_data = concept_package
            await self._notify("最終concept_packageが提出されました。", "complete")
            return {"status": "SUCCESS", "message": "Task complete. Thank you."}

        tools = [
            AgentTool(
                name="search_web",
                description="指定したキーワードでWeb検索を行い、記事や情報を取得します。キャラクター設定や物語のネタ集め、面白い設定の調査など、執筆前のリサーチに必ず使用してください。複数回呼び出すことも可能です。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "検索キーワード"},
                        "max_results": {"type": "integer", "description": "取得する検索結果の最大数 (デフォルト3)"}
                    },
                    "required": ["query"]
                },
                handler=search_web
            ),
            AgentTool(
                name="request_critique",
                description="現在のconcept_packageドラフトを厳しく評価し、面白さや心理学的深さ、Redemption Biasの有無を判定してもらいます。結果が 'pass' になるまで必ず繰り返してください。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "concept_package": {"type": "object", "description": "現在のドラフトデータ全体"}
                    },
                    "required": ["concept_package"]
                },
                handler=request_critique
            ),
            AgentTool(
                name="submit_final_concept",
                description="request_critiqueでの評価が 'pass' になった後、十分な品質を満たした最終的なconcept_packageをシステムに提出し、タスクを終了します。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "concept_package": {"type": "object", "description": "完成したデータ全体"}
                    },
                    "required": ["concept_package"]
                },
                handler=submit_final_concept
            )
        ]
        
        agentic_sys_prompt = SYSTEM_PROMPT + "\n\n【エージェンティック行動指針】\n1. まずドラフトを作成する\n2. 必ず `request_critique` ツールを用いて自身のドラフトを自身で客観的に評価する\n3. 評価が 'refine'（不合格）だったら、指摘事項に沿って自身の構成案を修正し、再度 `request_critique` を呼び出す\n4. 評価が 'pass'（合格）になったら、絶対に妥協せず、`submit_final_concept` ツールを呼び出して最終データを提出する"
        
        # 指定されたTierに応じて独立したAgentic Loopを呼び出す
        # Claude優先: opus/sonnet指定時はまずClaudeを試行し、失敗時にGeminiへフォールバック
        if self.profile.director_tier in ("opus", "sonnet"):
            try:
                await call_llm_agentic(
                    tier=self.profile.director_tier,
                    system_prompt=agentic_sys_prompt,
                    user_message=user_msg,
                    tools=tools,
                    max_iterations=self.max_iterations * 3,
                )
            except Exception as e:
                logger.warning(f"[CreativeDirector] Claude ({self.profile.director_tier}) agentic failed: {e}. Falling back to Gemini.")
                from backend.tools.llm_api import call_llm_agentic_gemini
                await call_llm_agentic_gemini(
                    system_prompt=agentic_sys_prompt,
                    user_message=user_msg,
                    tools=tools,
                    max_iterations=self.max_iterations * 3,
                )
        elif self.profile.director_tier == "gemini":
            from backend.tools.llm_api import call_llm_agentic_gemini
            await call_llm_agentic_gemini(
                system_prompt=agentic_sys_prompt,
                user_message=user_msg,
                tools=tools,
                max_iterations=self.max_iterations * 3,
            )
        else:
            raise ValueError(f"Unsupported director tier: {self.profile.director_tier}")
        
        if not final_concept_data:
            raise RuntimeError("Creative Directorがコンセプトの提出（submit_final_concept）を行わずに終了しました。リサーチ不足またはAIの判断エラーの可能性があります。")
            
        final_concept_data["iteration_count"] = critique_iteration
        final_concept_data["self_critique_history"] = self_critique_history
        
        try:
            package = ConceptPackage(**final_concept_data)
        except Exception as e:
            logger.warning(f"ConceptPackage validation warning: {e}")
            package = ConceptPackage(
                character_concept=final_concept_data.get("character_concept", ""),
                story_outline=final_concept_data.get("story_outline", ""),
                narrative_theme=final_concept_data.get("narrative_theme", ""),
                genre_and_world=final_concept_data.get("genre_and_world", ""),
                interestingness_hooks=final_concept_data.get("interestingness_hooks", []),
                critical_design_notes=final_concept_data.get("critical_design_notes", []),
                psychological_hints=final_concept_data.get("psychological_hints", {}),
                reference_stories=final_concept_data.get("reference_stories", []),
                iteration_count=critique_iteration,
                self_critique_history=self_critique_history,
            )
            
        return package
