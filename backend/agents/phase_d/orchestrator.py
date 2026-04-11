"""
Phase D Orchestrator
7日分のイベント列を一括事前生成する。
v10 §2.5 / v2 §6.6 準拠。

責務:
- WorldContextWorker: 世界設定
- SupportingCharactersWorker: 周囲の人物
- NarrativeArcDesigner: 物語アーク + Day5山場設計
- ConflictIntensityDesigner: 葛藤強度アーク
- WeeklyEventWriter: 28-42件のイベント一括生成

設計方針:
- Step 1-4はプロンプトコンテキストとしてのみ使用されるため、
  JSON出力を強制せず自然言語テキストで受け渡す。
- Step 5（イベント生成）のみ、機械的にパースする必要があるためJSON出力を使用。
"""

import json
import asyncio
import logging

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, MicroParameters,
    AutobiographicalEpisodes, WeeklyEventsStore,
    WorldContext, SupportingCharacter, NarrativeArc,
    ConflictIntensityArc, Event,
)
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


# ── Step 1-4: 自然言語テキスト出力（JSON不要） ──────────────────

WORLD_CONTEXT_PROMPT = """あなたはキャラクターが生活する世界の設定を具体化するWorkerです。

以下を含む世界設定を3-5文で具体的に記述してください:
- 世界名/舞台名
- 世界の具体的記述
- 時代設定
- ジャンル

自然な文章で回答してください。"""

SUPPORTING_CHARACTERS_PROMPT = """あなたはキャラクターの周囲の人物を設計するWorkerです。
macro_profileのrelationship_networkを参照しつつ、7日間の物語に登場する3-6人の人物を設計してください。

【重要】各人物は「自分自身の小さな欲求(own_small_want)」を持つこと。
これにより、イベントが主人公のためだけに存在するのではなく、
キャラクター同士の欲求のぶつかり合いから自然に生まれる。

各人物について: 名前、役割、主人公との関係、短い人物描写、その人自身の欲求を記述してください。
自然な文章で回答してください。"""

NARRATIVE_ARC_PROMPT = """あなたは7日間の物語アークを設計するNarrativeArcDesignerです。
Opus級の品質で、Day5を山場とする具体的な物語構造を設計してください。

【制約（v10 §2.5準拠）】
- Day 5が山場（最大の葛藤・転換点）
- Day 1-4は準備・伏線・日常の中にある予兆
- Day 6は山場の余波
- Day 7は収束（解決ではなく、問いが残る形）

以下を含めて記述してください:
- Vonnegut型アーク名（Man in a Hole / Boy Meets Girl等）
- アークの概要
- Day5の具体的な事件の設計（3-5文）
- Day1-4の伏線計画（各日、何の伏線をどう張るか）
- 繰り返しのモチーフ
- Day6の余波の方向性
- Day7の収束の方向性

自然な文章で回答してください。"""

CONFLICT_INTENSITY_PROMPT = """あなたは7日間の葛藤強度アークを設計するDesignerです。
各日の葛藤強度レベルを設定し、その理由を簡潔に説明してください。

典型的なパターン:
- Day 1: weak（日常への導入）
- Day 2: weak_to_medium（小さな違和感）
- Day 3: medium（葛藤の顕在化）
- Day 4: medium_to_strong（避けられない対峙）
- Day 5: strong（山場・最大の葛藤）
- Day 6: aftermath（余波）
- Day 7: convergence（収束）

自然な文章で回答してください。"""

# ── Step 5: イベント生成（JSON必須 — 機械的にパースしてEventモデルに格納） ──

WEEKLY_EVENT_WRITER_PROMPT = """あなたは7日間のイベント列を一括生成するWeeklyEventWriterです。
NarrativeArcDesignerの設計に従い、各日4-6件、合計28-42件のイベントを生成してください。

【メタデータ制約（v10 §2.5, v2 §6.6.6 厳守）】

(1) known_to_protagonist:
  - true: 主人公が事前に予定として知っている
  - false: 主人公が知らない（突発イベント、他者起因の出来事）

(2) source:
  - "routine": 日常の繰り返し（通勤、ルーティン等）
  - "prior_appointment": 事前にスケジュールされた約束
  - 注意: "protagonist_plan" は Phase D では 1 件も生成してはならない！

(3) expectedness:
  - "high": 予想通りの展開
  - "medium": ある程度予想できるが細部は異なる
  - "low": 予想外の展開
  分布制約: high が半分以上、low は Day 5 以外で各日最大1件

(4) meaning_to_character:
  - 必須。「なぜこのキャラクターにとってこのイベントが意味を持つか」を1-3文で記述
  - 「面白い」「大変」等の曖昧な記述は不合格

(5) narrative_arc_role:
  - "day5_foreshadowing": Day5山場への伏線（Day1-4のイベントに）
  - "previous_day_callback": 前日のイベントへの参照
  - "daily_rhythm": 日常リズムの構成
  - "standalone_ripple": 独立した波紋

【出力形式】JSON
{
  "events": [
    {
      "id": "evt_001",
      "day": 1,
      "time_slot": "morning/late_morning/noon/afternoon/evening/night/late_night",
      "known_to_protagonist": true/false,
      "source": "routine/prior_appointment",
      "expectedness": "high/medium/low",
      "content": "3-5文の具体的な記述",
      "involved_characters": ["人名"],
      "meaning_to_character": "なぜ意味を持つか（1-3文）",
      "narrative_arc_role": "daily_rhythm/day5_foreshadowing/previous_day_callback/standalone_ripple",
      "conflict_type": "internal/interpersonal/situational/null",
      "connected_episode_id": "ep_XXX or null",
      "connected_values": ["Schwartz価値名"]
    }
  ]
}"""


class PhaseDOrchestrator:
    """Phase D Orchestrator"""

    def __init__(
        self,
        concept: ConceptPackage,
        macro_profile: MacroProfile,
        micro_parameters: MicroParameters,
        episodes: AutobiographicalEpisodes,
        profile: EvaluationProfile,
        ws_manager=None,
    ):
        self.concept = concept
        self.macro = macro_profile
        self.micro = micro_parameters
        self.episodes = episodes
        self.profile = profile
        self.ws = ws_manager

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[Phase D] Orchestrator", content, status)

    def _full_context(self) -> str:
        """上流の全成果物を文字列化"""
        return (
            f"concept_package:\n{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            f"macro_profile:\n{json.dumps(self.macro.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            f"micro_parameters (主要):\n"
            f"  気質: {json.dumps([p.model_dump(mode='json') for p in self.micro.temperament[:4]], ensure_ascii=False)}\n"
            f"  価値観: {json.dumps(self.micro.schwartz_values, ensure_ascii=False)}\n"
            f"  理想自己: {self.micro.ideal_self}\n"
            f"  義務自己: {self.micro.ought_self}\n\n"
            f"autobiographical_episodes:\n{json.dumps([e.model_dump(mode='json') for e in self.episodes.episodes], ensure_ascii=False, indent=2)}"
        )

    async def run(self) -> WeeklyEventsStore:
        """Phase Dを実行"""
        await self._notify("Phase D: 7日分イベント列一括生成開始")
        context = self._full_context()

        # ── Step 1-2: WorldContext + SupportingCharacters (並列、自然言語テキスト) ──
        await self._notify("Step 1-2: 世界設定 + 周囲人物を並列生成")

        world_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=WORLD_CONTEXT_PROMPT,
            user_message=f"{context}\n\n世界設定を生成してください。",
        )
        chars_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=SUPPORTING_CHARACTERS_PROMPT,
            user_message=f"{context}\n\n周囲の人物を設計してください。",
        )

        world_result, chars_result = await asyncio.gather(world_task, chars_task)

        # 自然言語テキストとして取得（JSONパース不要）
        world_text = world_result["content"] if isinstance(world_result["content"], str) else json.dumps(world_result["content"], ensure_ascii=False, indent=2)
        chars_text = chars_result["content"] if isinstance(chars_result["content"], str) else json.dumps(chars_result["content"], ensure_ascii=False, indent=2)

        logger.info(f"[Phase D] WorldContext text length: {len(world_text)}")
        logger.info(f"[Phase D] SupportingCharacters text length: {len(chars_text)}")

        # Pydanticモデルは最小限（テキストをdescriptionに格納）
        world_context = WorldContext(description=world_text)
        supporting_chars = []  # 個別パース不要。テキストとして次ステップに渡す

        if self.ws:
            await self.ws.send_agent_thought("[Phase D] WorldContext", f"世界設定生成完了 ({len(world_text)}字)", "complete")
            await self.ws.send_agent_thought("[Phase D] SupportingCharacters", f"周囲人物設計完了 ({len(chars_text)}字)", "complete")

        # ── Step 3-4: NarrativeArcDesigner + ConflictIntensityDesigner (並列、自然言語) ──
        await self._notify("Step 3-4: 物語アーク + 葛藤強度設計")

        arc_task = call_llm(
            tier=self.profile.director_tier, system_prompt=NARRATIVE_ARC_PROMPT,
            user_message=f"{context}\n\n世界設定:\n{world_text}\n\n周囲人物:\n{chars_text}\n\n物語アークを設計してください。",
            cache_system=True,
        )
        conflict_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=CONFLICT_INTENSITY_PROMPT,
            user_message=f"concept_package:\n{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False)}\n\n葛藤強度アークを設定してください。",
        )

        arc_result, conflict_result = await asyncio.gather(arc_task, conflict_task)

        # 自然言語テキストとして取得
        arc_text = arc_result["content"] if isinstance(arc_result["content"], str) else json.dumps(arc_result["content"], ensure_ascii=False, indent=2)
        conflict_text = conflict_result["content"] if isinstance(conflict_result["content"], str) else json.dumps(conflict_result["content"], ensure_ascii=False, indent=2)

        logger.info(f"[Phase D] NarrativeArc text length: {len(arc_text)}")
        logger.info(f"[Phase D] ConflictIntensity text length: {len(conflict_text)}")

        # Pydanticモデルは最小限
        narrative_arc = NarrativeArc(description=arc_text)
        conflict_intensity = ConflictIntensityArc()  # デフォルト値で十分

        if self.ws:
            await self.ws.send_agent_thought("[Phase D] NarrativeArc", f"物語アーク設計完了 ({len(arc_text)}字)", "complete")

        # ── Step 5: WeeklyEventWriter (イベント生成、JSON必須) ──
        await self._notify("Step 5: 28-42件のイベントを一括生成中...")

        event_result = await call_llm(
            tier=self.profile.director_tier,
            system_prompt=WEEKLY_EVENT_WRITER_PROMPT,
            user_message=(
                f"{context}\n\n"
                f"--- 世界設定 ---\n{world_text}\n\n"
                f"--- 周囲人物 ---\n{chars_text}\n\n"
                f"--- 物語アーク ---\n{arc_text}\n\n"
                f"--- 葛藤強度 ---\n{conflict_text}\n\n"
                f"上記全てを参照し、7日分のイベント列をJSON形式で生成してください。"
            ),
            json_mode=True,
            cache_system=True,
            cache_context=context,
        )

        # イベントJSONパース（ここだけ機械的処理が必要）
        if isinstance(event_result["content"], dict):
            events_data = event_result["content"]
        else:
            logger.error(
                f"[Phase D] WeeklyEventWriter returned non-dict "
                f"(type={type(event_result['content']).__name__}, "
                f"len={len(str(event_result['content']))}). "
                f"Raw preview: {str(event_result.get('raw', ''))[:300]}"
            )
            await self._notify("CRITICAL: イベントJSON解析失敗", "error")
            events_data = {}

        events_raw = events_data.get("events", [])

        events = []
        for i, evt in enumerate(events_raw):
            if isinstance(evt, dict):
                try:
                    source = evt.get("source", "routine")
                    if source == "protagonist_plan":
                        source = "routine"
                        logger.warning("protagonist_plan source detected in Phase D, corrected to routine")

                    event = Event(
                        id=evt.get("id", f"evt_{len(events)+1:03d}"),
                        day=int(evt.get("day", 1)),
                        time_slot=evt.get("time_slot", "morning"),
                        known_to_protagonist=evt.get("known_to_protagonist", True),
                        source=source,
                        expectedness=evt.get("expectedness", "high"),
                        content=evt.get("content", ""),
                        involved_characters=evt.get("involved_characters", []),
                        meaning_to_character=evt.get("meaning_to_character", ""),
                        narrative_arc_role=evt.get("narrative_arc_role", "daily_rhythm"),
                        conflict_type=evt.get("conflict_type"),
                        connected_episode_id=evt.get("connected_episode_id"),
                        connected_values=evt.get("connected_values", []),
                    )
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Event parse error (index {i}): {e}. Data: {json.dumps(evt, ensure_ascii=False)[:200]}")

        if len(events) == 0:
            logger.error(
                f"[Phase D] CRITICAL: Zero events parsed. "
                f"events_raw had {len(events_raw)} items. "
                f"events_data keys: {list(events_data.keys()) if events_data else 'EMPTY DICT'}"
            )
            await self._notify("CRITICAL: イベント0件 — Phase評価で失敗します", "error")
        elif len(events) < 28:
            logger.warning(f"[Phase D] Only {len(events)} events parsed (need 28+).")

        store = WeeklyEventsStore(
            world_context=world_context,
            supporting_characters=supporting_chars,
            narrative_arc=narrative_arc,
            conflict_intensity_arc=conflict_intensity,
            events=events,
        )

        await self._notify(f"Phase D完了: {len(events)}件のイベント生成", "complete")
        return store
