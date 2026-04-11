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


WORLD_CONTEXT_PROMPT = """あなたはキャラクターが生活する世界の設定を具体化するWorkerです。

出力形式: JSON
{
  "name": "世界名/舞台名",
  "description": "世界の具体的記述（3-5文）",
  "time_period": "時代設定",
  "genre": "ジャンル"
}"""

SUPPORTING_CHARACTERS_PROMPT = """あなたはキャラクターの周囲の人物を設計するWorkerです。
macro_profileのrelationship_networkを参照しつつ、7日間の物語に登場する3-6人の人物を設計してください。

【重要】各人物は「自分自身の小さな欲求(own_small_want)」を持つこと。
これにより、イベントが主人公のためだけに存在するのではなく、
キャラクター同士の欲求のぶつかり合いから自然に生まれる。

出力形式: JSON
{
  "supporting_characters": [
    {"name": "人名", "role": "役割", "relationship_to_protagonist": "関係",
     "brief_profile": "短い人物描写", "own_small_want": "その人自身の欲求"}
  ]
}"""

NARRATIVE_ARC_PROMPT = """あなたは7日間の物語アークを設計するNarrativeArcDesignerです。
Opus級の品質で、Day5を山場とする具体的な物語構造を設計してください。

【制約（v10 §2.5準拠）】
- Day 5が山場（最大の葛藤・転換点）
- Day 1-4は準備・伏線・日常の中にある予兆
- Day 6は山場の余波
- Day 7は収束（解決ではなく、問いが残る形）

【出力形式】JSON
{
  "type": "Vonnegut型アーク名（Man in a Hole / Boy Meets Girl等）",
  "description": "アークの概要",
  "day5_climax_design": "Day5の具体的な事件の設計（3-5文）",
  "foreshadowing_plan": [
    {"day": 1-4, "target": "day5のどの要素の伏線か", "approach": "どう伏線を張るか"}
  ],
  "recurring_motifs": ["繰り返しのモチーフ1", "モチーフ2"],
  "day6_aftermath_direction": "Day6の方向性",
  "day7_convergence_direction": "Day7の方向性"
}"""

CONFLICT_INTENSITY_PROMPT = """あなたは7日間の葛藤強度アークを設計するDesignerです。
各日の葛藤強度レベルを設定してください。

出力形式: JSON
{
  "day_1": "weak",
  "day_2": "weak_to_medium",
  "day_3": "medium",
  "day_4": "medium_to_strong",
  "day_5": "strong",
  "day_6": "aftermath",
  "day_7": "convergence"
}"""

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
        
        # Step 1-2: WorldContext + SupportingCharacters (並列)
        await self._notify("Step 1-2: 世界設定 + 周囲人物を並列生成")
        
        world_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=WORLD_CONTEXT_PROMPT,
            user_message=f"{context}\n\n世界設定を生成してください。",
            json_mode=True,
        )
        chars_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=SUPPORTING_CHARACTERS_PROMPT,
            user_message=f"{context}\n\n周囲の人物を設計してください。",
            json_mode=True,
        )
        
        world_result, chars_result = await asyncio.gather(world_task, chars_task)
        
        world_data = world_result["content"] if isinstance(world_result["content"], dict) else {}
        chars_data = chars_result["content"] if isinstance(chars_result["content"], dict) else {}
        
        world_context = WorldContext(**{k: world_data.get(k, "") for k in ["name", "description", "time_period", "genre"]})
        supporting_chars = [
            SupportingCharacter(**c) for c in chars_data.get("supporting_characters", [])
            if isinstance(c, dict) and "name" in c
        ]
        
        if self.ws:
            await self.ws.send_agent_thought("[Phase D] WorldContext", f"世界: {world_context.name}", "complete")
            await self.ws.send_agent_thought("[Phase D] SupportingCharacters", f"{len(supporting_chars)}人設計完了", "complete")
        
        # Step 3-4: NarrativeArcDesigner + ConflictIntensityDesigner (並列)
        await self._notify("Step 3-4: 物語アーク + 葛藤強度設計")
        
        chars_json = json.dumps([c.model_dump(mode="json") for c in supporting_chars], ensure_ascii=False)
        
        arc_task = call_llm(
            tier=self.profile.director_tier, system_prompt=NARRATIVE_ARC_PROMPT,
            user_message=f"{context}\n\n世界設定:\n{json.dumps(world_data, ensure_ascii=False)}\n\n周囲人物:\n{chars_json}\n\n物語アークを設計してください。",
            json_mode=True, cache_system=True,
        )
        conflict_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=CONFLICT_INTENSITY_PROMPT,
            user_message=f"concept_package:\n{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False)}\n\n葛藤強度アークを設定してください。",
            json_mode=True,
        )
        
        arc_result, conflict_result = await asyncio.gather(arc_task, conflict_task)
        
        arc_data = arc_result["content"] if isinstance(arc_result["content"], dict) else {}
        conflict_data = conflict_result["content"] if isinstance(conflict_result["content"], dict) else {}
        
        narrative_arc = NarrativeArc(**{k: arc_data.get(k, "") for k in [
            "type", "description", "day5_climax_design",
            "foreshadowing_plan", "recurring_motifs",
            "day6_aftermath_direction", "day7_convergence_direction",
        ]})
        
        conflict_intensity = ConflictIntensityArc(**{k: conflict_data.get(k, "medium") for k in [
            "day_1", "day_2", "day_3", "day_4", "day_5", "day_6", "day_7"
        ]})
        
        if self.ws:
            await self.ws.send_agent_thought("[Phase D] NarrativeArc", f"アーク: {narrative_arc.type}", "complete")
        
        # Step 5: WeeklyEventWriter (最重要、Opus使用)
        await self._notify("Step 5: 28-42件のイベントを一括生成中... (Opus)")
        
        event_result = await call_llm(
            tier=self.profile.director_tier,
            system_prompt=WEEKLY_EVENT_WRITER_PROMPT,
            user_message=(
                f"{context}\n\n"
                f"世界設定:\n{json.dumps(world_data, ensure_ascii=False)}\n\n"
                f"周囲人物:\n{chars_json}\n\n"
                f"物語アーク:\n{json.dumps(arc_data, ensure_ascii=False, indent=2)}\n\n"
                f"葛藤強度:\n{json.dumps(conflict_data, ensure_ascii=False)}\n\n"
                f"上記全てを参照し、7日分のイベント列を生成してください。"
            ),
            json_mode=True,
            cache_system=True,
            cache_context=context,
        )
        
        events_data = event_result["content"] if isinstance(event_result["content"], dict) else {}
        events_raw = events_data.get("events", [])
        
        events = []
        for evt in events_raw:
            if isinstance(evt, dict):
                try:
                    # source: "protagonist_plan" は Phase D では禁止
                    source = evt.get("source", "routine")
                    if source == "protagonist_plan":
                        source = "routine"
                        logger.warning(f"protagonist_plan source detected in Phase D, corrected to routine")
                    
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
                    logger.warning(f"Event parse error: {e}")
        
        store = WeeklyEventsStore(
            world_context=world_context,
            supporting_characters=supporting_chars,
            narrative_arc=narrative_arc,
            conflict_intensity_arc=conflict_intensity,
            events=events,
        )
        
        await self._notify(f"Phase D完了: {len(events)}件のイベント生成", "complete")
        return store
