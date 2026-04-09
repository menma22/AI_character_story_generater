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
        concept_packageを生成する。内部ループでSelf-Critiqueを行い品質を担保。
        
        Args:
            theme: ユーザー指定のテーマ（省略時は完全自動）
        
        Returns:
            ConceptPackage
        """
        await self._notify("Creative Directorを起動します...")
        
        # 初回生成
        user_msg = "独創的で面白いキャラクターのconcept_packageを生成してください。character_conceptは必ず500字以上、story_outlineも500字以上で具体的に書いてください。"
        if theme:
            user_msg = f"以下のテーマに基づいて、独創的で面白いキャラクターのconcept_packageを生成してください。character_conceptは必ず500字以上、story_outlineも500字以上で具体的に書いてください。\n\nテーマ: {theme}"
        
        await self._notify(f"concept_package初回生成中..." + (f" テーマ: {theme}" if theme else " (完全自動)"))
        
        result = await call_llm(
            tier="opus",
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            max_tokens=8000,
            json_mode=True,
            cache_system=True,
        )
        
        concept_data = result["content"] if isinstance(result["content"], dict) else {}
        self_critique_history = []
        
        # Self-Critiqueループ
        for iteration in range(self.max_iterations):
            await self._notify(f"Self-Critique iteration {iteration + 1}/{self.max_iterations}...")
            
            critique_result = await call_llm(
                tier="opus",
                system_prompt=SELF_CRITIQUE_PROMPT,
                user_message=f"以下のconcept_packageを評価してください:\n\n{json.dumps(concept_data, ensure_ascii=False, indent=2)}",
                max_tokens=2048,
                json_mode=True,
                cache_system=True,
            )
            
            critique = critique_result["content"] if isinstance(critique_result["content"], dict) else {}
            verdict = critique.get("verdict", "pass")
            
            # 履歴に記録
            self_critique_history.append(critique)
            
            # チェック結果の通知
            checks = critique.get("checks", {})
            check_summary = []
            for key, val in checks.items():
                status = "✓" if val.get("passed", False) else "✗"
                check_summary.append(f"  [{status}] {key}: {val.get('comment', '')[:60]}")
            await self._notify(f"Self-Critique結果:\n" + "\n".join(check_summary) + f"\n\nVerdict: {verdict}")
            
            if verdict == "pass":
                await self._notify(f"concept_package承認（iteration {iteration + 1}）", "complete")
                break
            
            # 改善
            refinement = critique.get("refinement_instructions", "")
            await self._notify(f"改善中: {refinement[:100]}...")
            
            refine_result = await call_llm(
                tier="opus",
                system_prompt=SYSTEM_PROMPT,
                user_message=(
                    f"以下のconcept_packageを改善してください。\n\n"
                    f"【現在のconcept_package】\n{json.dumps(concept_data, ensure_ascii=False, indent=2)}\n\n"
                    f"【改善指示】\n{refinement}\n\n"
                    f"改善後のconcept_package全体をJSON形式で出力してください。"
                ),
                max_tokens=8000,
                json_mode=True,
                cache_system=True,
            )
            concept_data = refine_result["content"] if isinstance(refine_result["content"], dict) else concept_data
        
        # iteration_count と self_critique_history を埋め込む
        concept_data["iteration_count"] = len(self_critique_history)
        concept_data["self_critique_history"] = self_critique_history
        concept_data["verdict"] = verdict if 'verdict' in dir() else "pass"
        
        # ConceptPackageモデルに変換
        try:
            package = ConceptPackage(**concept_data)
        except Exception as e:
            logger.warning(f"ConceptPackage validation warning: {e}")
            package = ConceptPackage(
                character_concept=concept_data.get("character_concept", ""),
                story_outline=concept_data.get("story_outline", ""),
                narrative_theme=concept_data.get("narrative_theme", ""),
                genre_and_world=concept_data.get("genre_and_world", ""),
                interestingness_hooks=concept_data.get("interestingness_hooks", []),
                critical_design_notes=concept_data.get("critical_design_notes", []),
                psychological_hints=concept_data.get("psychological_hints", {}),
                reference_stories=concept_data.get("reference_stories", []),
                iteration_count=len(self_critique_history),
                self_critique_history=self_critique_history,
            )
        
        cc_preview = package.character_concept[:60] if package.character_concept else "(empty)"
        await self._notify(f"concept_package生成完了: {cc_preview}...", "complete")
        return package
