"""
Tier -1: Creative Director
specification_v10.md に基づくキャラクターの概念設計を行う最上位エージェント。
内部ループ（Self-Critique）により品質を自律的に担保する。

責務:
- character_concept（核心・欲求・内部矛盾）
- psychological_hints（気質・価値観の方向性）
- story_outline（物語テーマ・Day5山場・感情アーク）
- interestingness_hooks（面白さのフック）
- critical_design_notes（下流への設計指示）
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

【設計原則】
1. 面白さが最優先。「読みたい」と思わせるキャラクターを設計せよ
2. 内部矛盾（want と needのギャップ、気質と規範のギャップ）が面白さの源泉
3. AI臭い無難なキャラクターは不合格。「優しくて元気で好奇心旺盛」は最悪の例
4. 具体性が命。抽象的な記述は全て不合格
5. redemption bias（全てが成長と救済に向かう傾向）を警戒せよ
6. 陰影のある人物を設計せよ。弱さ・恥・後悔を持つキャラクターが面白い
7. 7日間の物語で何が起きるかの骨格を示せ。Day 5が山場

【心理学的基盤（参照すべき理論）】
- Cloninger精神生物学的気質モデル（NS/HA/RD/Persistence）
- Big Five / HEXACO 性格特性
- Schwartz 19価値理論
- Higgins 自己不一致理論（Ideal/Ought/Actual Self）
- McAdams ナラティブ・アイデンティティ
- Strack & Deutsch Reflective-Impulsive Model

【出力形式】
以下のJSON形式で出力してください:
{
  "character_concept": {
    "core_identity": "キャラの核心（1文）",
    "want": "本人が自覚している欲求",
    "need": "本人が気づいていない本当の必要",
    "internal_contradiction": "内部矛盾（面白さの源泉）"
  },
  "genre_and_world": "ジャンルと世界観の方向性",
  "psychological_hints": {
    "temperament_direction": "気質方向性への示唆",
    "values_direction": "価値観方向性への示唆",
    "key_tension": "気質と規範の間のギャップの設計意図"
  },
  "story_outline": {
    "narrative_theme": "通奏低音テーマ",
    "day5_climax_hint": "Day5山場の方向性",
    "emotional_arc": "感情アーク"
  },
  "interestingness_hooks": ["面白さのフック1", "フック2", "フック3"],
  "critical_design_notes": ["下流への設計指示1", "指示2"]
}
"""

SELF_CRITIQUE_PROMPT = """あなたはCreative Directorの内部批評者です。
以下のconcept_packageを厳しく評価してください。

【評価基準】
[A] 面白さ: このキャラクターの日記を7日間読みたいか？最初の1文で引き込まれるか？
[B] 個性の深さ: 内部矛盾は具体的か？want/needのギャップは物語を生むか？
[C] Redemption Bias回避: 全てが成長と救済に向かっていないか？
[D] 時間的連続性の種: 7日間の物語が連続する構造的な仕掛けがあるか？
[E] 整合性: psychological_hintsとstory_outlineは矛盾しないか？
[F] 実装可能性: 52パラメータとイベント列に落とし込めるか？

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
        user_msg = "独創的で面白いキャラクターのconcept_packageを生成してください。"
        if theme:
            user_msg = f"以下のテーマに基づいて、独創的で面白いキャラクターのconcept_packageを生成してください。\n\nテーマ: {theme}"
        
        await self._notify(f"concept_package初回生成中..." + (f" テーマ: {theme}" if theme else " (完全自動)"))
        
        result = await call_llm(
            tier="opus",
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            max_tokens=4096,
            json_mode=True,
            cache_system=True,
        )
        
        concept_data = result["content"] if isinstance(result["content"], dict) else {}
        
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
                max_tokens=4096,
                json_mode=True,
                cache_system=True,
            )
            concept_data = refine_result["content"] if isinstance(refine_result["content"], dict) else concept_data
        
        # ConceptPackageモデルに変換
        try:
            package = ConceptPackage(**concept_data)
        except Exception as e:
            logger.warning(f"ConceptPackage validation warning: {e}")
            package = ConceptPackage(
                character_concept=concept_data.get("character_concept", {
                    "core_identity": "未定義",
                    "want": "未定義",
                    "need": "未定義",
                    "internal_contradiction": "未定義",
                }),
                genre_and_world=concept_data.get("genre_and_world", "現代日本"),
                psychological_hints=concept_data.get("psychological_hints", {
                    "temperament_direction": "", "values_direction": "", "key_tension": ""
                }),
                story_outline=concept_data.get("story_outline", {
                    "narrative_theme": "", "day5_climax_hint": "", "emotional_arc": ""
                }),
                interestingness_hooks=concept_data.get("interestingness_hooks", []),
                critical_design_notes=concept_data.get("critical_design_notes", []),
            )
        
        await self._notify(f"concept_package生成完了: {package.character_concept.core_identity}", "complete")
        return package
