"""
Phase A-2 Orchestrator
52パラメータ（気質23 + 性格27 + 対他者認知2）+ 規範層を生成する。
v2 §6.4.2 / v10 §3.3 準拠: 15 Worker構成（10 Parameter + 4 Normative + 1 CognitiveDerivation）
"""

import json
import asyncio
import logging

from pydantic import BaseModel, Field

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, MicroParameters, ParameterEntry,
    ParameterList, NormativeLayer,
)
from backend.tools.agent_utils import run_worker_with_validation

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# パラメータ定義テーブル（v10 §3.3 準拠、15 Worker用にサブグループ化）
# ═══════════════════════════════════════════════════════════════

# --- Step 1: パラメータ Worker群（10 workers） ---

# A1: 情動反応系 (#1-9)
TEMPERAMENT_A1_EMOTIONAL_REACTIVITY = [
    (1,  "Novelty Seeking",         "新奇性追求"),
    (2,  "Harm Avoidance",          "損害回避"),
    (3,  "Reward Dependence",       "報酬依存"),
    (4,  "Persistence",             "固執"),
    (5,  "Threat Sensitivity",      "脅威感受性"),
    (6,  "Behavioral Inhibition",   "行動抑制"),
    (7,  "Emotional Intensity",     "感情強度"),
    (8,  "Positive Mood Baseline",  "ポジティブ気分基線"),
    (9,  "Negative Mood Baseline",  "ネガティブ気分基線"),
]

# A2: 活性・エネルギー系 (#10-14)
TEMPERAMENT_A2_ENERGY = [
    (10, "Activity Level",    "活動性"),
    (11, "Stamina",           "持久力"),
    (12, "Arousal Baseline",  "覚醒基線"),
    (13, "Impulsivity",       "衝動性"),
    (14, "Sensory Threshold", "感覚閾値"),
]

# A3: 社会的志向系 (#15-18)
TEMPERAMENT_A3_SOCIAL_ORIENTATION = [
    (15, "Sociability",           "社交性"),
    (16, "Interpersonal Warmth",  "対人温かさ"),
    (17, "Playfulness",           "遊戯性"),
    (18, "Dominance",             "支配性"),
]

# A4: 認知スタイル系 (#19-23)
TEMPERAMENT_A4_COGNITIVE_STYLE = [
    (19, "Attention Span",        "注意持続性"),
    (20, "Attentional Shifting",  "注意転換性"),
    (21, "Intellectual Curiosity", "知的好奇心"),
    (22, "Imagination",           "想像力"),
    (23, "Rhythmicity",           "規則性志向"),
]

# B1: 自己調整・目標追求系 (#24-30)
PERSONALITY_B1_SELF_REGULATION = [
    (24, "Industriousness",      "勤勉性"),
    (25, "Self-Discipline",      "自己規律"),
    (26, "Orderliness",          "秩序性"),
    (27, "Dutifulness",          "義務感"),
    (28, "Achievement Striving", "達成追求"),
    (29, "Deliberation",         "慎重さ"),
    (30, "Self-Efficacy",        "自己効力感"),
]

# B2: 対人・社会的態度系 (#31-38)
PERSONALITY_B2_INTERPERSONAL = [
    (31, "Trust",              "信頼"),
    (32, "Straightforwardness", "率直さ"),
    (33, "Altruism",           "利他性"),
    (34, "Compliance",         "従順性"),
    (35, "Modesty",            "謙虚性"),
    (36, "Empathy",            "共感性"),
    (37, "Honesty-Humility",   "誠実-謙虚"),
    (38, "Greed Avoidance",    "貪欲回避"),
]

# B3: 経験への開放性系 (#39-43)
PERSONALITY_B3_OPENNESS = [
    (39, "Aesthetics",            "美への感受性"),
    (40, "Feelings Openness",     "感情への開放"),
    (41, "Actions Openness",      "行動への開放"),
    (42, "Intellectual Openness",  "知的開放性"),
    (43, "Values Flexibility",     "価値柔軟性"),
]

# B4: 自己概念・実存系 (#44-48)
PERSONALITY_B4_SELF_CONCEPT = [
    (44, "Self-Directedness",   "自己志向性"),
    (45, "Self-Acceptance",     "自己受容"),
    (46, "Self-Transcendence",  "自己超越"),
    (47, "Identity Consistency", "アイデンティティ一貫性"),
    (48, "Reflectiveness",      "内省傾向"),
]

# B5: ライフスタイル・表出系 (#49-50)
PERSONALITY_B5_EXPRESSION = [
    (49, "Emotional Expressiveness", "感情表出性"),
    (50, "Humor Orientation",        "ユーモア志向"),
]

# 対他者認知 (#51-52)
SOCIAL_COGNITION_PARAMS = [
    (51, "Social Comparison Orientation", "社会的比較傾向"),
    (52, "Dispositional Envy",            "嫉妬気質"),
]


# ═══════════════════════════════════════════════════════════════
# 規範層サブモデル（各 Normative Worker の出力スキーマ）
# ═══════════════════════════════════════════════════════════════

class SchwartzValuesOutput(BaseModel):
    """ValuesWorker 出力: Schwartz 19価値"""
    schwartz_values: dict[str, str] = Field(
        default_factory=dict,
        description="Schwartz 19価値それぞれに strong/medium/weak を付与"
    )

class MoralFoundationsOutput(BaseModel):
    """MFTWorker 出力: 道徳基盤理論"""
    moral_foundations: dict[str, str] = Field(
        default_factory=dict,
        description="Care, Fairness, Loyalty, Authority, Sanctity, Liberty の重み"
    )

class IdealOughtSelfOutput(BaseModel):
    """IdealOughtSelfWorker 出力: 理想自己・義務自己"""
    ideal_self: str = Field("", description="理想自己の方向性")
    ought_self: str = Field("", description="義務自己の方向性")

class GoalsDreamsOutput(BaseModel):
    """GoalsDreamsWorker 出力: 目標"""
    goals: list[str] = Field(default_factory=list, description="長期・中期目標リスト")


# ═══════════════════════════════════════════════════════════════
# Worker 定義テーブル（メタデータ）
# ═══════════════════════════════════════════════════════════════

PARAMETER_WORKERS = [
    {
        "name": "TemperamentWorker_A1",
        "label": "情動反応系",
        "params": TEMPERAMENT_A1_EMOTIONAL_REACTIVITY,
        "description": (
            "Cloningerの気質4次元（NS, HA, RD, Persistence）と、情動反応の基盤となる "
            "脅威感受性、行動抑制、感情強度、気分基線を決定します。"
            "これらはキャラクターの情動的な「地盤」であり、後続の全パラメータに影響します。"
        ),
    },
    {
        "name": "TemperamentWorker_A2",
        "label": "活性・エネルギー系",
        "description": (
            "身体的エネルギー水準、持久力、覚醒の基線、衝動性、感覚閾値を決定します。"
            "キャラクターの「エンジン」の強さと反応の速さを形作ります。"
        ),
        "params": TEMPERAMENT_A2_ENERGY,
    },
    {
        "name": "TemperamentWorker_A3",
        "label": "社会的志向系",
        "description": (
            "社交性、対人温かさ、遊戯性、支配性を決定します。"
            "キャラクターが他者との関わりにおいてどのようなスタンスを取るかの基盤です。"
        ),
        "params": TEMPERAMENT_A3_SOCIAL_ORIENTATION,
    },
    {
        "name": "TemperamentWorker_A4",
        "label": "認知スタイル系",
        "description": (
            "注意の持続性と転換性、知的好奇心、想像力、規則性志向を決定します。"
            "キャラクターの「認知的クセ」を形作ります。"
        ),
        "params": TEMPERAMENT_A4_COGNITIVE_STYLE,
    },
    {
        "name": "PersonalityWorker_B1",
        "label": "自己調整・目標追求系",
        "description": (
            "勤勉性、自己規律、秩序性、義務感、達成追求、慎重さ、自己効力感を決定します。"
            "キャラクターが目標に向かってどれだけ組織立てて行動できるかを規定します。"
        ),
        "params": PERSONALITY_B1_SELF_REGULATION,
    },
    {
        "name": "PersonalityWorker_B2",
        "label": "対人・社会的態度系",
        "description": (
            "信頼、率直さ、利他性、従順性、謙虚性、共感性、誠実-謙虚、貪欲回避を決定します。"
            "キャラクターが他者とどのように関わるかの態度・姿勢です。"
        ),
        "params": PERSONALITY_B2_INTERPERSONAL,
    },
    {
        "name": "PersonalityWorker_B3",
        "label": "経験への開放性系",
        "description": (
            "美への感受性、感情への開放、行動への開放、知的開放性、価値柔軟性を決定します。"
            "キャラクターが新しい経験にどれだけオープンかを規定します。"
        ),
        "params": PERSONALITY_B3_OPENNESS,
    },
    {
        "name": "PersonalityWorker_B4",
        "label": "自己概念・実存系",
        "description": (
            "自己志向性、自己受容、自己超越、アイデンティティ一貫性、内省傾向を決定します。"
            "キャラクターの自己認識の深さと安定性を規定します。"
        ),
        "params": PERSONALITY_B4_SELF_CONCEPT,
    },
    {
        "name": "PersonalityWorker_B5",
        "label": "ライフスタイル・表出系",
        "description": (
            "感情表出性とユーモア志向を決定します。"
            "キャラクターが感情をどのように外に表すかのスタイルです。"
        ),
        "params": PERSONALITY_B5_EXPRESSION,
    },
    {
        "name": "SocialCognitionWorker",
        "label": "対他者認知",
        "description": (
            "社会的比較傾向と嫉妬気質を決定します。"
            "キャラクターが他者と自分をどのように比較し、それにどう反応するかです。"
        ),
        "params": SOCIAL_COGNITION_PARAMS,
    },
]


# ═══════════════════════════════════════════════════════════════
# プロンプトテンプレート
# ═══════════════════════════════════════════════════════════════

PARAM_SYSTEM_PROMPT = """あなたはキャラクターの心理パラメータを生成する専門Workerです。
Creative Directorのconcept_packageとmacro_profileに基づき、指定されたパラメータ群を生成してください。

各パラメータは 1.0〜5.0 の値と、その値が意味する自然言語記述を出力してください。
- 1.0: その特性が極めて低い
- 3.0: 中程度
- 5.0: その特性が極めて高い

【重要な設計原則】
- 気質と規範は独立に設定されるべき（Parks-Leduc et al. 2015）
- 気質=低でも規範=高は許容される（例: 怠惰な気質だが勤勉であるべきと信じている）
- このギャップが内省の源泉となる → 意図的にギャップを作ること
- concept_packageのpsychological_hints.key_tensionを必ず反映すること
- 同じサブグループ内のパラメータ間の一貫性を確保すること
- ただし全パラメータが中央値付近に集中するのは避け、個性的な偏りを持たせること

【出力形式】 JSON
"""

VALUES_SYSTEM_PROMPT = """あなたはキャラクターのSchwartz 19価値を決定する専門Workerです。
concept_packageとmacro_profileのvalues_coreに基づき、以下の19価値それぞれにstrong/medium/weakを付与してください。

Schwartz 19価値:
Self-Direction-Thought, Self-Direction-Action, Stimulation, Hedonism,
Achievement, Power-Dominance, Power-Resources, Face, Security-Personal,
Security-Societal, Tradition, Conformity-Rules, Conformity-Interpersonal,
Humility, Benevolence-Caring, Benevolence-Dependability,
Universalism-Concern, Universalism-Nature, Universalism-Tolerance

【重要】気質・性格層と規範層は独立に決定されるべき（v10 §3.2）。
キャラクターの自覚的な価値観は、気質的傾向と一致しない場合があり、そのギャップこそが物語を生む。

出力形式: {"schwartz_values": {"Self-Direction-Thought": "strong", ...}}
"""

MFT_SYSTEM_PROMPT = """あなたはキャラクターの道徳基盤（Moral Foundations Theory）を決定する専門Workerです。
concept_packageとmacro_profileに基づき、6つの道徳基盤それぞれの重みを決定してください。

道徳基盤6つ:
- Care/Harm（ケア/危害）
- Fairness/Cheating（公正/不正）
- Loyalty/Betrayal（忠誠/裏切り）
- Authority/Subversion（権威/転覆）
- Sanctity/Degradation（神聖/堕落）
- Liberty/Oppression（自由/抑圧）

各基盤に high/medium/low で重みを付与し、その根拠を簡潔に説明してください。

【重要】規範層は気質と独立（v10 §3.2）。

出力形式: {"moral_foundations": {"Care": "high - ...", "Fairness": "medium - ...", ...}}
"""

IDEAL_OUGHT_SYSTEM_PROMPT = """あなたはキャラクターの理想自己と義務自己を決定する専門Workerです。
concept_packageとmacro_profileに基づき、以下を生成してください。

- 理想自己 (Ideal Self): キャラクターが「こうなりたい」と願う自己像（方向性のみ、2-4文）
- 義務自己 (Ought Self): キャラクターが「こうあるべき」と感じている自己像（方向性のみ、2-4文）

【重要】
- 理想自己と義務自己が一致しない場合も多い（Higgins Self-Discrepancy Theory）
- このギャップが内的葛藤の源泉となる
- concept_packageのpsychological_hints.want_and_needと連動させること

出力形式: {"ideal_self": "...", "ought_self": "..."}
"""

GOALS_SYSTEM_PROMPT = """あなたはキャラクターの目標を決定する専門Workerです。
concept_packageとmacro_profileに基づき、長期・中期目標を生成してください。

- 長期目標 (1-2個): 5-10年スパンの大きな方向性
- 中期目標 (2-3個): 1-3年スパンの具体的目標

【重要】
- 目標は理想自己・義務自己と整合すべきだが、矛盾する目標があっても良い
- macro_profileのdream_timelineと連動させること
- 達成可能性のグラデーションを持たせること

出力形式: {"goals": ["長期: ...", "長期: ...", "中期: ...", ...]}
"""


class PhaseA2Orchestrator:
    """
    Phase A-2 Orchestrator（v2 §6.4.2 準拠）

    15 Worker構成:
      Step 1: 10 Parameter Workers（並列）
      Step 2:  4 Normative Workers（並列）
      Step 3:  1 CognitiveDerivation（逐次、気質出力に依存）
    """

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

    # ─── ユーティリティ ─────────────────────────────────────────

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[A-2] Orchestrator", content, status)

    def _build_context_json(self) -> str:
        """concept_package + macro_profile の共通コンテキストを生成"""
        return (
            f"concept_package:\n"
            f"{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            f"macro_profile (basic_info):\n"
            f"{json.dumps(self.macro.basic_info.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            f"values_core:\n"
            f"{json.dumps(self.macro.values_core.model_dump(mode='json'), ensure_ascii=False)}"
        )

    # ─── Step 1: パラメータ Worker ─────────────────────────────

    async def _run_param_worker(
        self,
        worker_name: str,
        label: str,
        description: str,
        param_list: list[tuple],
    ) -> list[ParameterEntry]:
        """
        1つのパラメータサブグループを生成する Worker。
        run_worker_with_validation でバリデーション付き LLM 呼び出しを行う。
        """
        await self._notify(f"{worker_name}: {label}（{len(param_list)}パラメータ）生成中...")

        param_desc = "\n".join([f"  #{p[0]} {p[1]} ({p[2]})" for p in param_list])

        user_message = (
            f"{self._build_context_json()}\n\n"
            f"【Worker: {worker_name}】\n"
            f"カテゴリ: {label}\n"
            f"心理学的背景: {description}\n\n"
            f"以下のパラメータを生成してください:\n{param_desc}\n\n"
            f"出力形式: {{\"parameters\": ["
            f"{{\"id\": 番号, \"name\": \"英語名\", \"value\": 1.0-5.0, "
            f"\"natural_language\": \"この値がこのキャラクターにとって何を意味するか詳細に\"}}]}}"
        )

        result = await run_worker_with_validation(
            worker_name,
            PARAM_SYSTEM_PROMPT,
            user_message,
            ParameterList,
            self.ws,
            tier=self.profile.worker_tier,
        )

        await self._notify(f"{worker_name}: {label} 完了（{len(result.parameters)}個）", "complete")
        return result.parameters

    # ─── Step 2: 規範層 Worker群 ──────────────────────────────

    async def _run_values_worker(self) -> SchwartzValuesOutput:
        """ValuesWorker: Schwartz 19価値を生成"""
        await self._notify("ValuesWorker: Schwartz 19価値生成中...")

        result = await run_worker_with_validation(
            "ValuesWorker",
            VALUES_SYSTEM_PROMPT,
            (
                f"{self._build_context_json()}\n\n"
                f"Schwartz 19価値それぞれに strong/medium/weak を付与してください。"
            ),
            SchwartzValuesOutput,
            self.ws,
            tier=self.profile.worker_tier,
        )

        await self._notify("ValuesWorker: Schwartz 19価値 完了", "complete")
        return result

    async def _run_mft_worker(self) -> MoralFoundationsOutput:
        """MFTWorker: 道徳基盤理論の6基盤を生成"""
        await self._notify("MFTWorker: 道徳基盤（MFT）生成中...")

        result = await run_worker_with_validation(
            "MFTWorker",
            MFT_SYSTEM_PROMPT,
            (
                f"{self._build_context_json()}\n\n"
                f"6つの道徳基盤それぞれの重みを決定してください。"
            ),
            MoralFoundationsOutput,
            self.ws,
            tier=self.profile.worker_tier,
        )

        await self._notify("MFTWorker: 道徳基盤 完了", "complete")
        return result

    async def _run_ideal_ought_worker(self) -> IdealOughtSelfOutput:
        """IdealOughtSelfWorker: 理想自己・義務自己を生成"""
        await self._notify("IdealOughtSelfWorker: 理想自己・義務自己生成中...")

        result = await run_worker_with_validation(
            "IdealOughtSelfWorker",
            IDEAL_OUGHT_SYSTEM_PROMPT,
            (
                f"{self._build_context_json()}\n\n"
                f"dream_timeline:\n"
                f"{json.dumps(self.macro.dream_timeline.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"理想自己と義務自己を生成してください。"
            ),
            IdealOughtSelfOutput,
            self.ws,
            tier=self.profile.worker_tier,
        )

        await self._notify("IdealOughtSelfWorker: 理想自己・義務自己 完了", "complete")
        return result

    async def _run_goals_worker(self) -> GoalsDreamsOutput:
        """GoalsDreamsWorker: 長期・中期目標を生成"""
        await self._notify("GoalsDreamsWorker: 目標生成中...")

        result = await run_worker_with_validation(
            "GoalsDreamsWorker",
            GOALS_SYSTEM_PROMPT,
            (
                f"{self._build_context_json()}\n\n"
                f"dream_timeline:\n"
                f"{json.dumps(self.macro.dream_timeline.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"長期・中期目標を生成してください。"
            ),
            GoalsDreamsOutput,
            self.ws,
            tier=self.profile.worker_tier,
        )

        await self._notify("GoalsDreamsWorker: 目標 完了", "complete")
        return result

    # ─── Step 3: CognitiveDerivation（ルールベース自動導出）────

    @staticmethod
    def _derive_cognitive_params(
        temperament_params: list[ParameterEntry],
    ) -> dict:
        """
        CognitiveDerivation: 気質パラメータからルールベースで認知パラメータを自動導出。
        LLM不使用。v10 §2.1.2 の公式に準拠。

        Returns:
            dict with keys: learning_rate_alpha, emotional_inertia,
                           rpe_sensitivity, decay_lambda
        """
        # 気質パラメータを ID で引く（デフォルト 3.0）
        param_map = {p.id: p.value for p in temperament_params}
        ns          = param_map.get(1, 3.0)   # Novelty Seeking
        ha          = param_map.get(2, 3.0)   # Harm Avoidance
        rd          = param_map.get(3, 3.0)   # Reward Dependence
        persistence = param_map.get(4, 3.0)   # Persistence

        learning_rate_alpha = 0.3  + 0.1  * (ns / 5.0)
        emotional_inertia   = 0.5  + 0.1  * (ha / 5.0)
        rpe_sensitivity     = 0.3  + 0.14 * (ns / 5.0)

        decay_v = 0.15 + 0.05 * ((5 - persistence) / 5.0)
        decay_a = 0.20 + 0.05 * ((5 - ha) / 5.0)
        decay_d = 0.10 + 0.05 * (rd / 5.0)

        return {
            "learning_rate_alpha": round(learning_rate_alpha, 3),
            "emotional_inertia":   round(emotional_inertia, 3),
            "rpe_sensitivity":     round(rpe_sensitivity, 3),
            "decay_lambda": {
                "V": round(decay_v, 3),
                "A": round(decay_a, 3),
                "D": round(decay_d, 3),
            },
        }

    # ─── メイン実行 ─────────────────────────────────────────────

    async def run(self) -> MicroParameters:
        """
        Phase A-2 を実行。3ステップで15 Workerを駆動する。

        Step 1: 10 Parameter Workers（並列）
        Step 2:  4 Normative Workers（並列）
        Step 3:  1 CognitiveDerivation（逐次）
        """
        await self._notify("Phase A-2: ミクロパラメータ生成開始（52パラメータ + 規範層、15 Worker構成）")

        # ─── Step 1: 10 Parameter Workers を並列実行 ────────────
        await self._notify(
            "Step 1/3: パラメータ Worker 10基を並列起動 "
            "(気質A1-A4, 性格B1-B5, 対他者認知)..."
        )

        param_tasks = [
            self._run_param_worker(
                w["name"], w["label"], w["description"], w["params"]
            )
            for w in PARAMETER_WORKERS
        ]
        param_results = await asyncio.gather(*param_tasks)

        # 結果を気質 / 性格 / 対他者認知に分類
        # Workers 0-3: 気質 (A1-A4), 4-8: 性格 (B1-B5), 9: 対他者認知
        temperament: list[ParameterEntry] = []
        for result in param_results[0:4]:
            temperament.extend(result)

        personality: list[ParameterEntry] = []
        for result in param_results[4:9]:
            personality.extend(result)

        other_cognition: list[ParameterEntry] = list(param_results[9])

        logger.info(
            "Step 1 完了: 気質=%d, 性格=%d, 対他者認知=%d",
            len(temperament), len(personality), len(other_cognition)
        )

        # ─── Step 2: 4 Normative Workers を並列実行 ────────────
        await self._notify(
            "Step 2/3: 規範層 Worker 4基を並列起動 "
            "(Values, MFT, IdealOughtSelf, GoalsDreams)..."
        )

        values_result, mft_result, ideal_ought_result, goals_result = await asyncio.gather(
            self._run_values_worker(),
            self._run_mft_worker(),
            self._run_ideal_ought_worker(),
            self._run_goals_worker(),
        )

        logger.info("Step 2 完了: 規範層4要素生成済み")

        # ─── Step 3: CognitiveDerivation（ルールベース自動導出）─
        await self._notify("Step 3/3: CognitiveDerivation（認知パラメータ自動導出）...")

        cognitive = self._derive_cognitive_params(temperament)

        logger.info(
            "Step 3 完了: α=%.3f, inertia=%.3f, rpe=%.3f, λ=%s",
            cognitive["learning_rate_alpha"],
            cognitive["emotional_inertia"],
            cognitive["rpe_sensitivity"],
            cognitive["decay_lambda"],
        )

        # ─── 組み立て ──────────────────────────────────────────
        micro = MicroParameters(
            temperament=temperament,
            personality=personality,
            other_cognition=other_cognition,
            schwartz_values=values_result.schwartz_values,
            moral_foundations=mft_result.moral_foundations,
            ideal_self=ideal_ought_result.ideal_self,
            ought_self=ideal_ought_result.ought_self,
            goals=goals_result.goals,
            learning_rate_alpha=cognitive["learning_rate_alpha"],
            emotional_inertia=cognitive["emotional_inertia"],
            rpe_sensitivity=cognitive["rpe_sensitivity"],
            decay_lambda=cognitive["decay_lambda"],
        )

        await self._notify(
            f"Phase A-2 完了: "
            f"気質{len(temperament)}個 + 性格{len(personality)}個 + "
            f"対他者認知{len(other_cognition)}個 + 規範層4要素 + 認知パラメータ自動導出",
            "complete",
        )
        return micro
