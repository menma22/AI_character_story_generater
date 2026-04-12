"""
Tier -1: Creative Director
specification_v10.md / script_ai_app_specification_v2.md §4 完全準拠。
内部ループ（Self-Critique + Self-Reflect）により品質を自律的に担保する。

v2 §4.7 の出力スキーマに完全準拠:
- character_concept: string (500-1000字の濃密な概念記述)
- story_outline: string (500-1000字の濃密な概念記述)
- narrative_theme, interestingness_hooks, genre_and_world
- reference_stories, critical_design_notes
- psychological_hints (temperament_direction, values_direction, want_and_need, ghost_wound_hint, lie_hint)
"""

import json
import logging
from typing import Optional, Any

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
-既存のストーリーや人物、キャラクターをそのまま真似することは絶対にせず、参考にしつつ独自のアイデアにする

【設計原則】
0. まずは、短い一文でキャラ設定と物語のコンセプトを生成する。この際に、ユーザーから受け取ったテーマを絶対に含める。
1. 面白さが最優先。「読みたい」と思わせるキャラクターを設計せよ
2. 内部矛盾（wantとneedのギャップ、気質と規範のギャップ）が面白さの源泉だが、ハートフルなエピソードを依頼されれば、なくてもよい
3. AI臭い無難なキャラクターは不合格。
4. 具体性が命。誰にでも書ける抽象的な記述は全て不合格
5. 7日間の物語で何が起きるかの骨格を示せ。山場があった方がいい場合は山場を設計してください。

【脚本論のベストプラクティス(参考程度、必須ではない)】
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
6. ただただ気持ちが暖かくなる日常系の物語、ハートフルな物語

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
  },
  "capabilities_hints": {
    "key_possessions_hint": "このキャラクターが持ち歩くべき重要なアイテムの方向性（1-3文）。物語や感情的意味と接続するものを含める",
    "core_abilities_hint": "物語で重要な役割を果たす能力・スキルの方向性（1-3文）。職業・背景・wantとneedから自然に導かれるもの",
    "signature_actions_hint": "このキャラクターならではの行動パターンの方向性（1-3文）。他のキャラクターには真似できない固有の行動"
  }
}

【絶対に守ること】
- AI臭い無難な設定を作らないこと
- 「優しい」「元気」「好奇心旺盛」のような曖昧な形容詞で済ませないこと
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
  □ 設定がむやみやたらに複雑で意味の分からないところや整合性が保たれていないところがないか

[B] 個性の深さ:
  □ want/needのギャップは物語を生む可能性があるか
  □ ghost_wound_hint と lie_hint が具体的か
  □ temperament_direction と values_direction の間にギャップがあるか

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
  □ capabilities_hintsの3フィールドが具体的でキャラクターの職業・価値観・wantと整合しているか

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

SELF_REFLECT_PROMPT = """あなたはCreative Directorの内なる声です。
外部批評（request_critique）はpassしました。しかし、本当にこれでいいのでしょうか？

以下のconcept_packageを読み、正直に自問してください:

1. 【読みたいか？】このキャラクターの7日間を、あなたは本当に読みたいと思うか？
   退屈だと感じる瞬間はないか？
2. 【既視感】他のAIが生成しそうな設定に似ていないか？本当にユニークか？
3. 【妥協】どこかで「まあこれでいいか」と妥協した箇所はないか？
4. 【心に刺さるか】character_conceptを読んだとき、心が動くか？
   story_outlineを読んだとき、続きが気になるか？
5. 【改善余地】もし1つだけ改善するとしたら、どこを変えるか？
   その改善は小さな修正か、根本的な再設計か？

【判定】
心から「これは面白い。自信を持って提出できる」と思えるなら:
  {"convinced": true, "reason": "なぜ確信が持てるか"}
まだ妥協や不安があるなら:
  {"convinced": false, "reason": "何が引っかかるか", "improvement_suggestion": "具体的改善案"}

正直に。甘い判定は下流の全品質を損なう。
"""


class CreativeDirector:
    """Tier -1: Creative Director"""
    
    def __init__(self, profile: EvaluationProfile, ws_manager=None, regeneration_context: Optional[str] = None, api_keys: Optional[dict] = None):
        self.profile = profile
        self.ws = ws_manager
        self.max_iterations = profile.director_self_critique_max_iterations
        self.regeneration_context = regeneration_context
        self.api_keys = api_keys
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("Creative Director", content, status)
    
    async def run(self, theme: Optional[str] = None) -> ConceptPackage:
        """
        concept_packageを生成する。エージェント自身がツールを駆使して自律的に品質を担保する。
        """
        from backend.tools.llm_api import AgentTool, call_llm_agentic
        
        await self._notify("Creative Directorを起動します（エージェンティック・モード）...")

        min_searches = self.profile.min_research_searches

        user_msg = f"独創的で面白いキャラクターのconcept_packageを生成してください。必ず事前にsearch_webを最低{min_searches}回使用して多角的にリサーチしてください。検索{min_searches}回未満ではrequest_critiqueもsubmitも受け付けません。character_conceptは500字以上、story_outlineも500字以上で具体的に書いてください。"
        if theme:
            user_msg = f"以下のテーマに基づいて、独創的で面白いキャラクターのconcept_packageを生成してください。必ず事前にsearch_webを最低{min_searches}回使用して多角的にリサーチし、インスピレーションを得てからドラフトを作成してください。検索{min_searches}回未満ではrequest_critiqueもsubmitも受け付けません。\n\nテーマ: {theme}"
        if self.regeneration_context:
            user_msg += f"\n\n{self.regeneration_context}"

        final_concept_data = None
        self_critique_history = []
        critique_iteration = 0
        search_count = 0
        critique_passed = False
        self_reflect_convinced = False
        
        async def search_web(query: str = None, max_results: int = 3) -> dict:
            """指定したキーワードでWeb検索を行い、上位記事の要約や関連情報を取得する"""
            if not query:
                return {"status": "FAILED", "message": "ERROR: query引数が欠落しています。検索キーワードを指定してください。"}

            nonlocal search_count
            search_count += 1
            await self._notify(f"Web検索中 ({search_count}回目): {query}")
            try:
                from duckduckgo_search import DDGS

                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(r)

                if results:
                    return {"status": "SUCCESS", "search_count": search_count, "results": results}
                else:
                    return {"status": "SUCCESS", "search_count": search_count, "message": "No results found."}
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                return {"status": "FAILED", "message": f"Web search explicitly failed: {e}"}

        async def request_critique(concept_package: dict = None) -> dict:
            """現在のドラフトに対する批判的フィードバックを要求する"""
            if not concept_package:
                return {"status": "FAILED", "message": "ERROR: concept_package引数が欠落しています。"}

            nonlocal critique_iteration, critique_passed, search_count
            if search_count < min_searches:
                return {"status": "BLOCKED", "message": f"ERROR: Web検索が{search_count}回しか実行されていません。最低{min_searches}回のsearch_webを実行してからrequest_critiqueを呼び出してください。"}

            critique_iteration += 1
            await self._notify(f"Self-Critiqueを依頼中...（試行 {critique_iteration}）")

            critique_result = await call_llm(
                tier="opus",
                system_prompt=SELF_CRITIQUE_PROMPT,
                user_message=f"以下のconcept_packageを評価してください:\n\n{json.dumps(concept_package, ensure_ascii=False, indent=2)}",
                json_mode=True,
                cache_system=True,
                api_keys=self.api_keys,
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
                critique_passed = True
                return {"status": "SUCCESS", "message": "CRITIQUE PASSED. 次にself_reflectツールで自己内省を行い、本当にこれで良いか確認してください。"}
            else:
                critique_passed = False
                return {"status": "FAILED", "feedback": critique}

        async def self_reflect(concept_package: dict = None) -> dict:
            """外部批評pass後、自分自身に「本当にこれでいいのか」を問う内省ツール"""
            if not concept_package:
                return {"status": "FAILED", "message": "ERROR: concept_package引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed:
                return {"status": "BLOCKED", "message": "ERROR: 先にrequest_critiqueでpassを得てください。"}

            await self._notify("自己内省中...「本当にこれでいいのか？」")

            reflect_result = await call_llm(
                tier="opus",
                system_prompt=SELF_REFLECT_PROMPT,
                user_message=f"以下のconcept_packageについて、本当にこれでいいか正直に自問してください:\n\n{json.dumps(concept_package, ensure_ascii=False, indent=2)}",
                json_mode=True,
                cache_system=True,
                api_keys=self.api_keys,
            )

            reflection = reflect_result["content"] if isinstance(reflect_result["content"], dict) else {}
            convinced = reflection.get("convinced", False)

            if convinced:
                self_reflect_convinced = True
                await self._notify(f"自己内省結果: 確信あり ✓ — {reflection.get('reason', '')[:80]}")
                return {"status": "SUCCESS", "message": "SELF-REFLECT PASSED. 確信が持てました。submit_final_conceptで提出してください。"}
            else:
                self_reflect_convinced = False
                critique_passed = False
                reason = reflection.get("reason", "不明")
                suggestion = reflection.get("improvement_suggestion", "")
                await self._notify(f"自己内省結果: まだ妥協あり ✗ — {reason[:80]}")
                return {"status": "FAILED", "message": f"まだ確信が持てません。理由: {reason}。改善案: {suggestion}"}

        async def submit_final_concept(concept_package: dict = None) -> dict:
            """最終確定版を提出し、ミッションを完了する"""
            if not concept_package:
                return {"status": "FAILED", "message": "ERROR: concept_package引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed or not self_reflect_convinced:
                blocked_reasons = []
                if not critique_passed: blocked_reasons.append("request_critiqueでpassを得ていない")
                if not self_reflect_convinced: blocked_reasons.append("self_reflectで確信を得ていない")
                return {"status": "BLOCKED", "message": f"ERROR: 提出がブロックされました。理由: {', '.join(blocked_reasons)}"}

            nonlocal final_concept_data
            final_concept_data = concept_package
            await self._notify("最終concept_packageが提出されました。", "complete")
            return {"status": "SUCCESS", "message": "Task complete. Thank you."}

        async def file_read(file_path: str = None) -> dict:
            """参考資料ファイルを読み込む"""
            if not file_path:
                return {"status": "FAILED", "message": "ERROR: file_path引数が欠落しています。"}
            from backend.config import AppConfig
            ref_dir = AppConfig.REFERENCE_DIR
            target = ref_dir / file_path
            try:
                target.resolve().relative_to(ref_dir.resolve())
            except ValueError:
                return {"status": "FAILED", "message": "アクセス制限エラー。"}
            if not target.exists():
                available = [f.name for f in ref_dir.glob("*") if f.is_file()] if ref_dir.exists() else []
                return {"status": "FAILED", "message": f"ファイルが見つかりません: {file_path}", "available_files": available}
            try:
                content = target.read_text(encoding="utf-8")
                await self._notify(f"参考資料読み込み: {file_path}")
                return {"status": "SUCCESS", "content": content[:5000]}
            except Exception as e:
                return {"status": "FAILED", "message": f"読み込みエラー: {e}"}

        # JSON変換ラッパー
        async def _request_critique_wrapper(concept_package_json: str = None, **kw) -> dict:
            try: data = json.loads(concept_package_json) if isinstance(concept_package_json, str) else concept_package_json
            except: return {"status": "FAILED", "message": "JSONエラー"}
            return await request_critique(data)

        async def _self_reflect_wrapper(concept_package_json: str = None, **kw) -> dict:
            try: data = json.loads(concept_package_json) if isinstance(concept_package_json, str) else concept_package_json
            except: return {"status": "FAILED", "message": "JSONエラー"}
            return await self_reflect(data)

        async def _submit_final_concept_wrapper(concept_package_json: str = None, **kw) -> dict:
            try: data = json.loads(concept_package_json) if isinstance(concept_package_json, str) else concept_package_json
            except: return {"status": "FAILED", "message": "JSONエラー"}
            return await submit_final_concept(data)

        tools = [
            AgentTool(
                name="file_read",
                description="参考資料を読み込みます。",
                input_schema={"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]},
                handler=file_read
            ),
            AgentTool(
                name="search_web",
                description=f"Web検索を行います。最低{min_searches}回必須。",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]},
                handler=search_web
            ),
            AgentTool(
                name="request_critique",
                description="ドラフトを評価します。JSON文字列推奨。",
                input_schema={"type": "object", "properties": {"concept_package_json": {"type": "string"}}, "required": ["concept_package_json"]},
                handler=_request_critique_wrapper
            ),
            AgentTool(
                name="self_reflect",
                description="自己内省を行います。JSON文字列推奨。",
                input_schema={"type": "object", "properties": {"concept_package_json": {"type": "string"}}, "required": ["concept_package_json"]},
                handler=_self_reflect_wrapper
            ),
            AgentTool(
                name="submit_final_concept",
                description="最終提出を行います。JSON文字列推奨。",
                input_schema={"type": "object", "properties": {"concept_package_json": {"type": "string"}}, "required": ["concept_package_json"]},
                handler=_submit_final_concept_wrapper
            )
        ]

        agentic_sys_prompt = SYSTEM_PROMPT + f"\n\n【エージェンティック行動指針 — 5フェーズ厳守】\nリサーチ(search_web最低{min_searches}回) → ドラフト → request_critique → self_reflect(convinced=true) → submit の手順を必ず踏んでください。"
        
        logger.info(f"[CreativeDirector] Starting agentic loop for theme: {theme}")
        if self.ws:
            await self.ws.send_agent_thought("Creative Director", f"テーマ '{theme}' に基づくキャラクター設計を開始します。エージェンティック・ループを起動します...", "thinking")
        
        if self.profile.director_tier in ("opus", "sonnet"):
            try:
                await call_llm_agentic(
                    tier=self.profile.director_tier,
                    system_prompt=agentic_sys_prompt,
                    user_message=user_msg,
                    tools=tools,
                    max_iterations=max(10, self.max_iterations * 3),
                    api_keys=self.api_keys,
                )
            except Exception as e:
                logger.warning(f"[CreativeDirector] Claude agentic failed: {e}. Falling back to Gemini.")
                from backend.tools.llm_api import call_llm_agentic_gemini
                await call_llm_agentic_gemini(
                    system_prompt=agentic_sys_prompt,
                    user_message=user_msg,
                    tools=tools,
                    max_iterations=max(10, self.max_iterations * 3),
                    api_keys=self.api_keys,
                )
        elif self.profile.director_tier == "gemini":
            from backend.tools.llm_api import call_llm_agentic_gemini
            await call_llm_agentic_gemini(
                system_prompt=agentic_sys_prompt,
                user_message=user_msg,
                tools=tools,
                max_iterations=max(10, self.max_iterations * 3),
                api_keys=self.api_keys,
            )
        else:
            raise ValueError(f"Unsupported director tier: {self.profile.director_tier}")
        
        if not final_concept_data:
            logger.warning("[CreativeDirector] Agentic loop failed to submit. Falling back to non-agentic.")
            fallback_result = await call_llm(
                tier="gemini",
                system_prompt=SYSTEM_PROMPT,
                user_message=user_msg + "\n\nJSONで出力してください。",
                json_mode=True,
                api_keys=self.api_keys,
            )
            if isinstance(fallback_result["content"], dict):
                final_concept_data = fallback_result["content"]
            else:
                raise RuntimeError("Creative Director failed.")
            
        final_concept_data["iteration_count"] = critique_iteration
        final_concept_data["self_critique_history"] = self_critique_history
        
        try:
            package = ConceptPackage(**final_concept_data)
        except Exception as e:
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
