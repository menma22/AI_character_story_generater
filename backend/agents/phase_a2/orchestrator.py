"""
Phase A-2 Orchestrator
52パラメータ（気質23 + 性格27 + 対他者認知2）+ 規範層を生成する。
MVP版では簡略化し、主要なWorkerグループを統合して実行する。
"""

import json
import asyncio
import logging

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, MicroParameters, ParameterEntry,
)
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)

# ─── パラメータ定義テーブル ────────────────────────────────────

TEMPERAMENT_PARAMS = [
    (1, "Novelty Seeking", "新奇性追求"), (2, "Harm Avoidance", "損害回避"),
    (3, "Reward Dependence", "報酬依存"), (4, "Persistence", "固執"),
    (5, "Threat Sensitivity (BIS)", "脅威感受性"), (6, "Behavioral Inhibition", "行動抑制"),
    (7, "Emotional Intensity", "感情強度"), (8, "Positive Mood Baseline", "ポジティブ気分基線"),
    (9, "Negative Mood Baseline", "ネガティブ気分基線"),
    (10, "EAS Activity", "活動性"), (11, "Sociability", "社交性"),
    (12, "Shyness", "シャイネス"), (13, "Impulsivity", "衝動性"),
    (14, "Approach Tendency", "接近傾向"), (15, "Adaptability", "適応性"),
    (16, "Rhythmicity", "規則性志向"), (17, "Attention Span", "注意持続性"),
    (18, "Sensory Sensitivity", "感覚感受性"),
    (19, "Effortful Control", "努力制御"), (20, "Frustration Tolerance", "忍耐力"),
    (21, "Soothability", "鎮静回復性"), (22, "Attentional Shifting", "注意転換性"),
    (23, "Perceptual Sensitivity", "知覚感受性"),
]

PERSONALITY_PARAMS = [
    (24, "Openness to Fantasy", "空想への開放"), (25, "Openness to Aesthetics", "美への感受性"),
    (26, "Openness to Feelings", "感情への開放"), (27, "Openness to Actions", "行動への開放"),
    (28, "Openness to Ideas", "知的好奇心"),
    (29, "Conscientiousness: Deliberation", "慎重さ"), (30, "Conscientiousness: Self-Discipline", "自己規律"),
    (31, "Conscientiousness: Order", "秩序性"), (32, "Conscientiousness: Achievement Striving", "達成追求"),
    (33, "Conscientiousness: Dutifulness", "義務感"),
    (34, "Extraversion: Warmth", "温かさ"), (35, "Extraversion: Gregariousness", "群居性"),
    (36, "Extraversion: Assertiveness", "自己主張"), (37, "Extraversion: Activity", "活動水準"),
    (38, "Extraversion: Positive Emotions", "ポジティブ感情"),
    (39, "Agreeableness: Trust", "信頼"), (40, "Agreeableness: Altruism", "利他性"),
    (41, "Agreeableness: Compliance", "従順性"), (42, "Agreeableness: Modesty", "謙虚性"),
    (43, "Agreeableness: Tender-Mindedness", "優しさ"),
    (44, "Neuroticism: Self-Consciousness", "自己意識"), (45, "Neuroticism: Vulnerability", "脆弱性"),
    (46, "Neuroticism: Angry Hostility", "怒り敵意"), (47, "Neuroticism: Depression", "抑うつ傾向"),
    (48, "Reflectiveness", "内省傾向"),
    (49, "HEXACO Honesty-Humility", "誠実-謙虚"), (50, "HEXACO Emotionality", "情動性"),
]

OTHER_COGNITION_PARAMS = [
    (51, "Social Comparison Orientation", "社会的比較傾向"),
    (52, "Dispositional Envy", "嫉妬気質"),
]


GENERATION_PROMPT = """あなたはキャラクターの心理パラメータを生成するWorkerです。
Creative Directorのconcept_packageとmacro_profileに基づき、以下のパラメータ群を生成してください。

各パラメータは 1.0〜5.0 の値と、その値が意味する自然言語記述を出力してください。
- 1.0: その特性が極めて低い
- 3.0: 中程度
- 5.0: その特性が極めて高い

【重要な設計原則】
- 気質と規範は独立に設定されるべき（Parks-Leduc et al. 2015）
- 気質=低でも規範=高は許容される（例: 怠惰な気質だが勤勉であるべきと信じている）
- このギャップが内省の源泉となる → 意図的にギャップを作ること
- concept_packageのpsychological_hints.key_tensionを必ず反映すること

【出力形式】 JSON
"""


class PhaseA2Orchestrator:
    """Phase A-2 Orchestrator（MVP簡略版）"""
    
    def __init__(
        self,
        concept: ConceptPackage,
        macro_profile: MacroProfile,
        profile: EvaluationProfile,
        ws_manager=None,
    ):
        self.concept = concept
        self.macro = macro_profile
        self.profile = profile
        self.ws = ws_manager
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[A-2] Orchestrator", content, status)
    
    async def _generate_params(self, param_list: list, category: str) -> list[ParameterEntry]:
        """パラメータ群を一括生成"""
        param_desc = "\n".join([f"  #{p[0]} {p[1]} ({p[2]})" for p in param_list])
        
        result = await call_llm(
            tier="gemma",
            system_prompt=GENERATION_PROMPT,
            user_message=(
                f"concept_package:\n{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
                f"macro_profile (basic_info):\n{json.dumps(self.macro.basic_info.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"values_core:\n{json.dumps(self.macro.values_core.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"カテゴリ: {category}\n"
                f"以下のパラメータを生成してください:\n{param_desc}\n\n"
                f"出力形式: {{'parameters': [{{'id': 番号, 'name': '英語名', 'name_en': '英語名', 'value': 1.0-5.0, 'natural_language': '自然言語記述'}}]}}"
            ),
            max_tokens=4000,
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        params_raw = data.get("parameters", [])
        
        entries = []
        for p in params_raw:
            if isinstance(p, dict):
                try:
                    entry = ParameterEntry(
                        id=int(p.get("id", 0)),
                        name=p.get("name", ""),
                        name_en=p.get("name_en", p.get("name", "")),
                        value=float(p.get("value", 3.0)),
                        natural_language=p.get("natural_language", ""),
                    )
                    entries.append(entry)
                except Exception as e:
                    logger.warning(f"Parameter parse error: {e}")
        
        return entries
    
    async def _generate_values(self) -> dict:
        """Schwartz 19価値 + 道徳基盤 + 理想自己/義務自己を生成"""
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたはキャラクターの規範層（価値観）を生成するWorkerです。
Schwartz 19価値それぞれにstrong/medium/weakを付与し、
道徳基盤、理想自己、義務自己、目標も生成してください。

【重要】気質・性格層と規範層は独立に決定されるべき（v10 §3.2）。
気質で「怠惰」でも、規範層で「達成 = strong（勤勉であるべき）」は許容される。

出力形式: JSON
{
  "schwartz_values": {"Self-Direction-Thought": "strong/medium/weak", ...全19個},
  "moral_foundations": {"Care": "strong/medium/weak", ...},
  "ideal_self": "理想自己の記述",
  "ought_self": "義務自己の記述",
  "goals": ["目標1", "目標2", ...]
}""",
            user_message=(
                f"concept_package:\n{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
                f"macro_profile (values_core):\n{json.dumps(self.macro.values_core.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"規範層を生成してください。"
            ),
            max_tokens=3000,
            json_mode=True,
        )
        
        return result["content"] if isinstance(result["content"], dict) else {}
    
    async def run(self) -> MicroParameters:
        """Phase A-2を実行"""
        await self._notify("Phase A-2: ミクロパラメータ生成開始（52パラメータ + 規範層）")
        
        # 並列実行: 気質、性格、対他者認知、規範層
        await self._notify("気質(23個)、性格(27個+2個)、対他者認知(2個)、規範層を並列生成中...")
        
        temperament_task = self._generate_params(TEMPERAMENT_PARAMS, "気質（Temperament）")
        personality_task = self._generate_params(PERSONALITY_PARAMS, "性格（Personality）")
        other_task = self._generate_params(OTHER_COGNITION_PARAMS, "対他者認知")
        values_task = self._generate_values()
        
        temperament, personality, other_cognition, values_data = await asyncio.gather(
            temperament_task, personality_task, other_task, values_task
        )
        
        # 認知パラメータの自動導出（v10 §3.3）
        ns = next((p.value for p in temperament if p.id == 1), 3.0)
        ha = next((p.value for p in temperament if p.id == 2), 3.0)
        rd = next((p.value for p in temperament if p.id == 3), 3.0)
        persistence = next((p.value for p in temperament if p.id == 4), 3.0)
        
        learning_rate = 0.3 + 0.1 * (ns / 5.0)
        emotional_inertia = 0.5 + 0.1 * (ha / 5.0)
        rpe_sensitivity = 0.3 + 0.14 * (ns / 5.0)
        
        decay_v = 0.15 + 0.05 * ((5 - persistence) / 5.0)
        decay_a = 0.20 + 0.05 * ((5 - ha) / 5.0)
        decay_d = 0.10 + 0.05 * (rd / 5.0)
        
        micro = MicroParameters(
            temperament=temperament,
            personality=personality,
            other_cognition=other_cognition,
            schwartz_values=values_data.get("schwartz_values", {}),
            moral_foundations=values_data.get("moral_foundations", {}),
            ideal_self=values_data.get("ideal_self", ""),
            ought_self=values_data.get("ought_self", ""),
            goals=values_data.get("goals", []),
            learning_rate_alpha=round(learning_rate, 3),
            emotional_inertia=round(emotional_inertia, 3),
            rpe_sensitivity=round(rpe_sensitivity, 3),
            decay_lambda={"V": round(decay_v, 3), "A": round(decay_a, 3), "D": round(decay_d, 3)},
        )
        
        await self._notify(
            f"Phase A-2完了: 気質{len(temperament)}個 + 性格{len(personality)}個 + 対他者認知{len(other_cognition)}個",
            "complete"
        )
        return micro
