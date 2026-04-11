"""
Phase A-1 Orchestrator
マクロプロフィールを8つのWorkerで並列/逐次生成する。
依存関係: BasicInfo → (Family, Lifestyle, Dream, ValuesCore) → Secret → RelationshipNetwork → LinguisticExpression
"""

import json
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, BasicInfo, SocialPosition,
    FamilyAndIntimacy, CurrentLifeOutline, DreamTimeline,
    VoiceFingerprint, ValuesCore, Secret, RelationshipEntry, RelationshipNetwork,
    LinguisticExpression,
)
from backend.tools.llm_api import call_llm
from backend.tools.agent_utils import run_worker_with_validation
from backend.agents.context_descriptions import wrap_context


@dataclass
class PhaseA1Result:
    """Phase A-1の戻り値（MacroProfile + LinguisticExpression）"""
    macro_profile: MacroProfile
    linguistic_expression: LinguisticExpression

logger = logging.getLogger(__name__)

# ─── 共通Worker呼び出し関数 ──────────────────────────────────

async def run_worker(
    worker_name: str,
    system_prompt: str,
    user_message: str,
    ws_manager=None,
    tier: str = "gemini",
) -> dict:
    """共通Worker呼び出し"""
    if ws_manager:
        await ws_manager.send_agent_thought(f"[A-1] {worker_name}", "実行中...", "thinking")
    
    result = await call_llm(
        tier=tier,
        system_prompt=system_prompt,
        user_message=user_message,
        json_mode=True,
    )
    
    data = result["content"] if isinstance(result["content"], dict) else {}
    
    if ws_manager:
        await ws_manager.send_agent_thought(f"[A-1] {worker_name}", "完了 ✓", "complete")
    
    return data


# ─── Worker プロンプト定義 ────────────────────────────────────

BASIC_INFO_PROMPT = """あなたはキャラクターの基本情報を生成するWorkerです。
Creative Directorのconcept_packageに基づき、キャラクターの基本情報を具体的に生成してください。

【出力形式】JSON:
{
  "name": "フルネーム",
  "age": 数値,
  "gender": "性別",
  "appearance": "外見の具体的描写（3-5文。服装の癖、姿勢、表情の特徴を含む）",
  "occupation": "具体的な職種・肩書"
}

【制約】
- 具体的で個性的な内容にすること
- AI臭い無難な記述を避けること
- concept_packageのcharacter_conceptと整合すること
"""

SOCIAL_POSITION_PROMPT = """あなたはキャラクターの「社会的位置」を生成するWorkerです。
concept_packageとbasic_infoに基づいて、キャラクターの社会的立ち位置を具体的に生成してください。

【出力形式】JSON:
{
  "occupation_detail": "職業の詳細（役職、担当領域、専門性）",
  "workplace_or_org": "職場・所属組織（具体的な名前+規模感）",
  "economic_status": "経済状況（生活水準を示す程度、ざっくり）",
  "living_area": "住んでいる場所（都市、地域、住居形態）",
  "social_class": "社会階層・出自（1文）"
}
"""

FAMILY_PROMPT = """あなたはキャラクターの家族構成・親密な関係を生成するWorkerです。
concept_packageとbasic_infoに基づいて、家族構成と親密な関係を具体的に生成してください。

【出力形式】JSON:
{
  "family_structure": "家族構成の記述",
  "key_relationships": [
    {"name": "人名", "relation": "続柄/関係", "quality": "関係の質感", "note": "特記事項"}
  ]
}
"""

LIFESTYLE_PROMPT = """あなたはキャラクターの生活の輪郭を生成するWorkerです。
concept_packageとbasic_infoに基づいて、日常生活のリズムと習慣を具体的に生成してください。

【出力形式】JSON:
{
  "daily_routine": "平日の典型的な1日（3-5文、具体的な時刻を含む）",
  "typical_weekday": "典型的な平日の概形（1パラグラフ。朝起きてから夜寝るまでの流れ）",
  "typical_weekend": "典型的な週末の概形（1パラグラフ。平日との違いを明示）",
  "habits_routines": ["習慣1", "習慣2", "習慣3", "習慣4"],
  "hobbies_leisure": ["趣味1", "趣味2"],
  "weekly_schedule": [
    {"day": "月曜", "events": "その曜日の定例予定"}
  ],
  "living_situation": "住居環境の具体的記述"
}

【重要】
- habits_routinesは3-5個、hobbies_leisureは2-3個を具体的に
- Phase Dの脚本AIはルーティンを参照してsource: routineの既知イベントを生成するため、具体的に
"""

DREAM_PROMPT = """あなたはキャラクターの「夢の時系列」を生成するWorkerです。
子供時代から現在までの夢の変遷を、物語的に記述してください。

【出力形式】JSON:
{
  "childhood_dream": "子供時代の夢（何になりたかったか、なぜか）",
  "late_teens_dream": "10代後半の夢（同上）",
  "setback_or_turning_point": "挫折・転機（いつ、何が起きてどう変わったか）",
  "current_dream": "現在の夢や目標",
  "long_term_dream": "長期的な夢・目標（5-10年）",
  "mid_term_dream": "中期的な目標（1-3年）",
  "short_term_dream": "短期的な目標（数ヶ月以内）",
  "dream_origin": "夢の根にある何か（1文、価値観との接続）",
  "timeline": [
    {"period": "時期", "dream": "その頃の夢", "context": "なぜその夢を持ったか"}
  ]
}

【重要】
- setback_or_turning_pointは必ず含めること（夢の変遷には必ず挫折や転機がある）
- dream_originはPhase A-3の自伝的エピソードと接続する重要な要素
"""

LINGUISTIC_EXPRESSION_PROMPT = """あなたはキャラクターの「言語的表現方法」を総合的に設計するWorkerです。
このキャラクターがどのように喋り、どのように日記を書くのか——その人の「言葉のすべて」を定義してください。
これは日記生成時に最も重要な要素であり、キャラクターの個性を最も強く決定づけるものです。

キャラクターの経歴・価値観・社会的立場・人間関係のすべてを踏まえて、
「この人はこういう喋り方をする」「この人の日記はこういう空気がある」という像を鮮明に描いてください。

【出力形式】JSON:
{
  "speech_characteristics": {
    "concrete_features": {
      "first_person": "一人称（俺/私/僕/あたし/etc.）",
      "second_person_by_context": {
        "to_intimate": "親しい人への二人称",
        "to_superior": "目上への二人称",
        "to_stranger": "知らない人への二人称"
      },
      "speech_patterns": ["口癖1", "口癖2", "口癖3"],
      "sentence_endings": ["文末表現1", "文末表現2"],
      "kanji_hiragana_tendency": "漢字/ひらがなの使い分け傾向（硬い/柔らかい/揺れる）",
      "emoji_usage": "絵文字・記号の使用傾向（使う/使わない/限定的）",
      "self_questioning_frequency": "自問形式の頻度（よく自問する/しない）",
      "metaphor_irony_frequency": "比喩・反語の頻度（よく使う/控えめ）",
      "avoided_words": ["避ける語彙1", "避ける語彙2", "避ける語彙3"]
    },
    "abstract_feel": "この人の喋り方を一言で表現するなら（例：『壊れかけのラジオのように途切れ途切れで、でも確かに何かを伝えようとしている』『春風のように柔らかいが、芯には冷たい鉄がある』、「楽観的で親しみやすく、マスコットのような喋り方」など）",
    "conversation_style": "会話のテンポ・間の取り方・話題の転がし方を具体的に（例：『質問に対して一拍置いてから答える。話題を自分から振ることは少なく、相手の言葉を反芻するように返す』）",
    "emotional_expression_tendency": "感情をどう言語化するか（例：『怒りは沈黙で表す。喜びは事実の羅列に微かに混ぜる。悲しみは語彙が極端に減る形で現れる』）"
  },
  "diary_writing_atmosphere": {
    "tone": "日記全体のトーン（例：『観測報告書のように乾いた文体だが、稀に感情が水面に浮上する瞬間がある』）",
    "structure_tendency": "日記の構成傾向（例：『時系列ではなく、最も印象に残った一場面から書き始め、そこから記憶を辿るように遡る』）",
    "introspection_depth": "内省の深さとスタイル（例：『表面的な出来事の記録に徹するが、文末の微妙な揺れに本音が漏れる』）",
    "what_gets_written": "何を書いて何を書かないか（例：『他者の行動は詳細に記録するが、自分の感情については「特に問題ない」の一言で片付ける』）",
    "what_gets_omitted": "意図的に省略・隠す傾向があるもの（例：『家族に関する話題は一切書かない。夢の内容も避ける』）",
    "raw_atmosphere_description": "この人の日記を読んだときに漂う空気感を2-3文で（例：『冷たい実験室の蛍光灯の下で書かれたような、無機質だが不思議と温度を感じる文章。行間に「ここにいる」という静かな主張が滲んでいる。』）"
  }
}

【重要】
- abstract_feelは最重要フィールド。具体的な特徴の羅列ではなく、「この人の喋り方の空気感」を比喩や印象で描写すること
- 「避ける語彙」(avoided_words)は必ず3-5個指定すること。日記生成時の禁止語として厳密に機能する
- AI臭い語彙（「成長」「気づき」「学び」「素敵」「前向き」「温かさ」等）は避ける語彙に含めることを強く推奨
- catchphrasesは実際に口にするフレーズをそのまま書くこと
- diary_writing_atmosphereの各フィールドは、このキャラクターの日記が「どういう読後感を持つか」を定義する極めて重要な指示である
- キャラクターの社会的立場・価値観・秘密・人間関係が喋り方と日記の書き方にどう反映されるか、必ず意識すること
"""

VALUES_CORE_PROMPT = """あなたはキャラクターの「価値観の核」を生成するWorkerです。
narrative形式（箇条書きではなく、1-2文の自然な表現で）記述してください。

【出力形式】JSON:
{
  "most_important": "最も大事にしていること（1-2文）",
  "absolutely_unforgivable": "絶対に許せないこと（1-2文）",
  "pride": "誇りに思っていること（1-2文）",
  "shame": "恥じていること（1-2文）"
}
"""

SECRET_PROMPT = """あなたはキャラクターの「秘密」を生成するWorkerです。
公にしないこと、日記にも書かないかもしれないことを具体的に生成してください。

【出力形式】JSON:
{
  "public_secrets": ["周囲には言わない秘密1", "秘密2"],
  "private_secrets": ["日記にも書かないかもしれないこと1", "こと2"]
}

【重要】
- private_secretsは必ず1-2個含めること
- これは日記生成時に意図的に欠落するべき情報として機能する
"""

RELATIONSHIP_PROMPT = """あなたはキャラクターの「関係性ネットワーク」を拡張するWorkerです。
familyの情報をベースに、家族以外の重要人物を追加してください。

【出力形式】JSON:
{
  "relationships": [
    {"name": "人名", "relationship": "関係（同僚/友人/恩師等）", "quality": "好き/苦手/複雑", "brief_note": "その人との関係の質感（1文）"}
  ]
}

【制約】
- 既存のfamily関係者を含め、合計5-8人程度にする
- 各人物に「質感」（好き/苦手/複雑）を明示する
- 新規追加は2-3人まで
"""

SUMMARY_PROMPT = """あなたはキャラクタープロフィールを美しいMarkdown形式で統合するWorkerです。
これまでのWorkerが生成した断片的な情報を統合し、一つの読み物として魅力的なプロフィールを作成してください。

【出力形式】
JSONではなく、純粋なMarkdownテキストとして出力してください。
以下のセクションを含めること：
# [名前]
## 1. 基本・外見
## 2. 価値観と核
## 3. 生活と習慣
## 4. 人間関係
## 5. 夢と時系列
## 6. 秘密と陰影（※示唆に留める）

【制約】
- AI臭いまとめ（「〜です。これからの活躍が期待されます」等）は一切不要。
- 物語の設計書として、下流のAIが読み取ってキャラクターを憑依させられる濃密な記述にすること。
"""


class PhaseA1Orchestrator:
    """Phase A-1 Orchestrator"""
    
    def __init__(
        self,
        concept: ConceptPackage,
        profile: EvaluationProfile,
        ws_manager=None,
        regeneration_context: str | None = None,
    ):
        self.concept = concept
        self.profile = profile
        self.ws = ws_manager
        self.regeneration_context = regeneration_context
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[A-1] Orchestrator", content, status)
    
    def _concept_context(self) -> str:
        return json.dumps(self.concept.model_dump(mode="json"), ensure_ascii=False, indent=2)
    
    async def run(self) -> PhaseA1Result:
        """Phase A-1を実行し、MacroProfile + LinguisticExpression を返す"""
        await self._notify("Phase A-1: 9つのWorkerを実行します")
        concept_json = self._concept_context()
        if self.regeneration_context:
            concept_json += f"\n\n{self.regeneration_context}"

        # Step 1: BasicInfo（最上流、他の全Workerが参照）
        await self._notify("Step 1: BasicInfoWorker")
        basic_info = await run_worker_with_validation(
            "BasicInfoWorker",
            BASIC_INFO_PROMPT,
            wrap_context("concept_package", concept_json),
            BasicInfo,
            self.ws,
            tier=self.profile.worker_tier,
        )

        basic_json = json.dumps(basic_info.model_dump(mode="json"), ensure_ascii=False)

        # Step 2: 並列実行可能なWorker群（5 Workers — Voice は独立生成に移行）
        await self._notify("Step 2: SocialPosition, Family, Lifestyle, Dream, ValuesCore を並列実行")

        step2_context = f"{wrap_context('concept_package', concept_json)}\n\n{wrap_context('basic_info', basic_json)}"

        results = await asyncio.gather(
            run_worker_with_validation("SocialPositionWorker", SOCIAL_POSITION_PROMPT,
                       step2_context, SocialPosition, self.ws, tier=self.profile.worker_tier),
            run_worker_with_validation("FamilyWorker", FAMILY_PROMPT,
                       step2_context, FamilyAndIntimacy, self.ws, tier=self.profile.worker_tier),
            run_worker_with_validation("LifestyleWorker", LIFESTYLE_PROMPT,
                       step2_context, CurrentLifeOutline, self.ws, tier=self.profile.worker_tier),
            run_worker_with_validation("DreamWorker", DREAM_PROMPT,
                       step2_context, DreamTimeline, self.ws, tier=self.profile.worker_tier),
            run_worker_with_validation("ValuesCoreWorker", VALUES_CORE_PROMPT,
                       step2_context, ValuesCore, self.ws, tier=self.profile.worker_tier),
        )

        social_obj, family_obj, lifestyle_obj, dream_obj, values_obj = results

        # Step 3: Secret（ValuesCore依存）
        await self._notify("Step 3: SecretWorker")
        secret_obj = await run_worker_with_validation(
            "SecretWorker", SECRET_PROMPT,
            f"{wrap_context('concept_package', concept_json)}\n\n{wrap_context('basic_info', basic_json)}\n\n{wrap_context('values_core', json.dumps(values_obj.model_dump(mode='json'), ensure_ascii=False))}",
            Secret,
            self.ws,
            tier=self.profile.worker_tier,
        )

        # Step 4: RelationshipNetwork（Family依存）
        await self._notify("Step 4: RelationshipNetworkWorker")
        rel_net_obj = await run_worker_with_validation(
            "RelationshipNetworkWorker", RELATIONSHIP_PROMPT,
            f"{wrap_context('concept_package', concept_json)}\n\n{wrap_context('basic_info', basic_json)}\n\n{wrap_context('family_and_intimacy', json.dumps(family_obj.model_dump(mode='json'), ensure_ascii=False))}",
            RelationshipNetwork,
            self.ws,
            tier=self.profile.worker_tier,
        )

        # Step 5: LinguisticExpression（全Worker結果を踏まえた言語的表現方法の生成）
        await self._notify("Step 5: LinguisticExpressionWorker（キャラクターの言語的表現方法を生成中...）")
        all_context = (
            f"{wrap_context('concept_package', concept_json)}\n\n"
            f"{wrap_context('basic_info', basic_json)}\n\n"
            f"{wrap_context('social_position', json.dumps(social_obj.model_dump(mode='json'), ensure_ascii=False))}\n\n"
            f"{wrap_context('family_and_intimacy', json.dumps(family_obj.model_dump(mode='json'), ensure_ascii=False))}\n\n"
            f"{wrap_context('current_life_outline', json.dumps(lifestyle_obj.model_dump(mode='json'), ensure_ascii=False))}\n\n"
            f"{wrap_context('dream_timeline', json.dumps(dream_obj.model_dump(mode='json'), ensure_ascii=False))}\n\n"
            f"{wrap_context('values_core', json.dumps(values_obj.model_dump(mode='json'), ensure_ascii=False))}\n\n"
            f"{wrap_context('secrets', json.dumps(secret_obj.model_dump(mode='json'), ensure_ascii=False))}\n\n"
            f"{wrap_context('relationship_network', json.dumps(rel_net_obj.model_dump(mode='json'), ensure_ascii=False))}"
        )
        ling_expr = await run_worker_with_validation(
            "LinguisticExpressionWorker",
            LINGUISTIC_EXPRESSION_PROMPT,
            all_context,
            LinguisticExpression,
            self.ws,
            tier=self.profile.worker_tier,
        )

        # Step 6: 全情報を統合したMarkdownプロセの生成 (ハイブリッド化)
        await self._notify("Step 6: プロフィール統合Markdownを生成中...")
        summary_prose = await call_llm(
            tier=self.profile.worker_tier,
            system_prompt=SUMMARY_PROMPT,
            user_message=f"これまでの生成結果:\n{json.dumps(basic_info.model_dump(), ensure_ascii=False)}\n{json.dumps(family_obj.model_dump(), ensure_ascii=False)}\n{json.dumps(lifestyle_obj.model_dump(), ensure_ascii=False)}\n{json.dumps(dream_obj.model_dump(), ensure_ascii=False)}\n{json.dumps(ling_expr.speech_characteristics.concrete_features.model_dump(), ensure_ascii=False)}\n{json.dumps(values_obj.model_dump(), ensure_ascii=False)}\n{json.dumps(secret_obj.model_dump(), ensure_ascii=False)}",
            json_mode=False
        )

        # MacroProfile構築（voice_fingerprintは後方互換のためconcrete_featuresからコピー）
        macro = MacroProfile(
            basic_info=basic_info,
            social_position=social_obj,
            family_and_intimacy=family_obj,
            current_life_outline=lifestyle_obj,
            dream_timeline=dream_obj,
            voice_fingerprint=ling_expr.speech_characteristics.concrete_features,
            values_core=values_obj,
            secrets=secret_obj,
            relationship_network=rel_net_obj.relationships,
            raw_prose_markdown=summary_prose["content"]
        )

        await self._notify(f"Phase A-1完了: {macro.basic_info.name}", "complete")
        return PhaseA1Result(macro_profile=macro, linguistic_expression=ling_expr)
