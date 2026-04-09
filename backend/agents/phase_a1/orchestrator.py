"""
Phase A-1 Orchestrator
マクロプロフィールを8つのWorkerで並列/逐次生成する。
依存関係: BasicInfo → (Family, Lifestyle, Dream, Voice, ValuesCore) → Secret → RelationshipNetwork
"""

import json
import asyncio
import logging
from typing import Optional

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, BasicInfo, SocialPosition,
    FamilyAndIntimacy, CurrentLifeOutline, DreamTimeline,
    VoiceFingerprint, ValuesCore, Secret, RelationshipEntry,
)
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)

# ─── 共通Worker呼び出し関数 ──────────────────────────────────

async def run_worker(
    worker_name: str,
    system_prompt: str,
    user_message: str,
    ws_manager=None,
    tier: str = "gemma",
) -> dict:
    """共通Worker呼び出し"""
    if ws_manager:
        await ws_manager.send_agent_thought(f"[A-1] {worker_name}", "実行中...", "thinking")
    
    result = await call_llm(
        tier=tier,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=3000,
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
  "appearance": "外見の具体的描写（3-5文）",
  "occupation": "職業"
}

【制約】
- 具体的で個性的な内容にすること
- AI臭い無難な記述を避けること
- concept_packageのcore_identityと整合すること
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
  "weekly_schedule": [
    {"day": "月曜", "events": "その曜日の定例予定"},
    ...
  ],
  "living_situation": "住居環境の具体的記述"
}
"""

DREAM_PROMPT = """あなたはキャラクターの「夢の時系列」を生成するWorkerです。
子供時代から現在までの夢の変遷を、物語的に記述してください。

【出力形式】JSON:
{
  "childhood_dream": "幼少期の夢",
  "current_dream": "現在の夢や目標",
  "dream_origin": "夢の根にある何か（1文。後のPhase A-3で接続する）",
  "timeline": [
    {"period": "時期", "dream": "その頃の夢", "context": "なぜその夢を持ったか"}
  ]
}
"""

VOICE_PROMPT = """あなたはキャラクターの「言語的指紋」を生成するWorkerです。
このキャラクター固有の話し方・書き方のパターンを具体的に定義してください。
これは日記生成時に最も重要な要素の1つです。

【出力形式】JSON:
{
  "first_person": "一人称（俺/私/僕/あたし/etc.）",
  "speech_patterns": ["口癖1", "口癖2", "口癖3"],
  "sentence_endings": ["文末表現1", "文末表現2"],
  "kanji_hiragana_tendency": "漢字/ひらがなの使い分け傾向",
  "avoided_words": ["避ける語彙1（例：成長）", "避ける語彙2（例：気づき）", "避ける語彙3"]
}

【重要】
- 「避ける語彙」は必ず2-3個指定すること。日記生成時の省略指示として機能する
- AI臭い語彙（「成長」「気づき」「学び」等）は候補に含めることを推奨
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


class PhaseA1Orchestrator:
    """Phase A-1 Orchestrator"""
    
    def __init__(
        self,
        concept: ConceptPackage,
        profile: EvaluationProfile,
        ws_manager=None,
    ):
        self.concept = concept
        self.profile = profile
        self.ws = ws_manager
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[A-1] Orchestrator", content, status)
    
    def _concept_context(self) -> str:
        return json.dumps(self.concept.model_dump(mode="json"), ensure_ascii=False, indent=2)
    
    async def run(self) -> MacroProfile:
        """Phase A-1を実行し、MacroProfileを返す"""
        await self._notify("Phase A-1: 8つのWorkerを実行します")
        concept_json = self._concept_context()
        
        # Step 1: BasicInfo（最上流、他の全Workerが参照）
        await self._notify("Step 1: BasicInfoWorker")
        basic_data = await run_worker(
            "BasicInfoWorker",
            BASIC_INFO_PROMPT,
            f"concept_package:\n{concept_json}",
            self.ws,
        )
        basic_info = BasicInfo(**{k: basic_data.get(k, "") for k in ["name", "age", "gender", "appearance", "occupation"]})
        if isinstance(basic_info.age, str):
            try:
                basic_info.age = int(basic_info.age)
            except ValueError:
                basic_info.age = 30
        
        basic_json = json.dumps(basic_data, ensure_ascii=False)
        
        # Step 2: 並列実行可能なWorker群
        await self._notify("Step 2: Family, Lifestyle, Dream, Voice, ValuesCore を並列実行")
        
        results = await asyncio.gather(
            run_worker("FamilyWorker", FAMILY_PROMPT,
                       f"concept_package:\n{concept_json}\n\nbasic_info:\n{basic_json}", self.ws),
            run_worker("LifestyleWorker", LIFESTYLE_PROMPT,
                       f"concept_package:\n{concept_json}\n\nbasic_info:\n{basic_json}", self.ws),
            run_worker("DreamWorker", DREAM_PROMPT,
                       f"concept_package:\n{concept_json}\n\nbasic_info:\n{basic_json}", self.ws),
            run_worker("VoiceWorker", VOICE_PROMPT,
                       f"concept_package:\n{concept_json}\n\nbasic_info:\n{basic_json}", self.ws),
            run_worker("ValuesCoreWorker", VALUES_CORE_PROMPT,
                       f"concept_package:\n{concept_json}\n\nbasic_info:\n{basic_json}", self.ws),
        )
        
        family_data, lifestyle_data, dream_data, voice_data, values_data = results
        
        # Step 3: Secret（ValuesCore依存）
        await self._notify("Step 3: SecretWorker")
        secret_data = await run_worker(
            "SecretWorker", SECRET_PROMPT,
            f"concept_package:\n{concept_json}\n\nbasic_info:\n{basic_json}\n\nvalues_core:\n{json.dumps(values_data, ensure_ascii=False)}",
            self.ws,
        )
        
        # Step 4: RelationshipNetwork（Family依存）
        await self._notify("Step 4: RelationshipNetworkWorker")
        rel_data = await run_worker(
            "RelationshipNetworkWorker", RELATIONSHIP_PROMPT,
            f"concept_package:\n{concept_json}\n\nbasic_info:\n{basic_json}\n\nfamily:\n{json.dumps(family_data, ensure_ascii=False)}",
            self.ws,
        )
        
        # MacroProfile組み立て
        macro = MacroProfile(
            basic_info=basic_info,
            social_position=SocialPosition(
                occupation_detail=basic_data.get("occupation", ""),
                living_area=lifestyle_data.get("living_situation", ""),
            ),
            family_and_intimacy=FamilyAndIntimacy(
                family_structure=family_data.get("family_structure", ""),
                key_relationships=family_data.get("key_relationships", []),
            ),
            current_life_outline=CurrentLifeOutline(
                daily_routine=lifestyle_data.get("daily_routine", ""),
                weekly_schedule=lifestyle_data.get("weekly_schedule", []),
                living_situation=lifestyle_data.get("living_situation", ""),
            ),
            dream_timeline=DreamTimeline(
                childhood_dream=dream_data.get("childhood_dream", ""),
                current_dream=dream_data.get("current_dream", ""),
                dream_origin=dream_data.get("dream_origin", ""),
                timeline=dream_data.get("timeline", []),
            ),
            voice_fingerprint=VoiceFingerprint(
                first_person=voice_data.get("first_person", ""),
                speech_patterns=voice_data.get("speech_patterns", []),
                sentence_endings=voice_data.get("sentence_endings", []),
                kanji_hiragana_tendency=voice_data.get("kanji_hiragana_tendency", ""),
                avoided_words=voice_data.get("avoided_words", []),
            ),
            values_core=ValuesCore(
                most_important=values_data.get("most_important", ""),
                absolutely_unforgivable=values_data.get("absolutely_unforgivable", ""),
                pride=values_data.get("pride", ""),
                shame=values_data.get("shame", ""),
            ),
            secrets=Secret(
                public_secrets=secret_data.get("public_secrets", []),
                private_secrets=secret_data.get("private_secrets", []),
            ),
            relationship_network=[
                RelationshipEntry(**r) for r in rel_data.get("relationships", [])
                if isinstance(r, dict) and "name" in r
            ],
        )
        
        await self._notify(f"Phase A-1完了: {macro.basic_info.name}", "complete")
        return macro
