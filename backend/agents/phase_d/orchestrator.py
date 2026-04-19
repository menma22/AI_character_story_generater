"""
Phase D Orchestrator
7日分のイベント列を一括事前生成する。
v10 §2.5 / v2 §6.6 準拠。

責務:
- WorldContextWorker: 世界設定
- SupportingCharactersWorker: 周囲の人物
- CharacterCapabilitiesAgent: 所持品・能力・可能行動（エージェンティック化、Web検索2回以上+批評+内省）
- NarrativeArcDesigner: 物語アーク + Day5山場設計
- ConflictIntensityDesigner: 葛藤強度アーク
- WeeklyEventWriter: 14-28件のイベント一括生成（エージェンティック化）

設計方針:
- Step 1-2（WorldContext, SupportingCharacters）は自然言語テキストで受け渡す。
- Step 2.5（CharacterCapabilities）はエージェンティックループ（search×2+ → draft → critique → self_reflect → submit）で品質を担保。
- Step 5（イベント生成）はエージェンティックループ（draft → critique → self_reflect → submit）で品質を担保。
- フォールバック: agenticループ失敗時は従来のone-shot出力に切り替え。
"""

import json
import asyncio
import logging
from typing import Optional

from backend.config import EvaluationProfile, LLMModels
from backend.models.character import (
    ConceptPackage, MacroProfile, MicroParameters,
    AutobiographicalEpisodes, WeeklyEventsStore,
    WorldContext, SupportingCharacter, NarrativeArc,
    ConflictIntensityArc, Event,
    CharacterCapabilities,
)
from backend.tools.llm_api import call_llm
from backend.agents.context_descriptions import wrap_context

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
プロの脚本家です。

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


# ── Step 5: イベント生成（1日ずつ順次） ──

DAILY_EVENT_WRITER_PROMPT = """あなたはキャラクターの1日分のイベントを生成するDailyEventWriterです。
前日までのイベント文脈とNarrativeArcDesignerの設計に従い、**指定された1日分（Day X）のイベントを2-4件生成**してください。

イベントには、主人公の心情などの主観的な内容は入れず、あくまで、主人公にその状況を与えることで面白い反応が得られそうな出来事を記述するだけです。感情や主観的な反応を生み出すのはキャラクター本人に任せます。
イベントには主人公に降り注ぐ外部からの出来事のみを記述してください。主人公の具体的な行動や心情などの主人公の能動的な反応については一切記述しないでください。

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

(4) meaning_to_character:
  - 必須。「なぜこのキャラクターにとってこのイベントが意味を持つか」を1-3文で記述

(5) narrative_arc_role:
  - "day5_foreshadowing": Day5山場への伏線
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
        regeneration_context: str | None = None,
        api_keys: Optional[dict] = None,
    ):
        self.concept = concept
        self.macro = macro_profile
        self.micro = micro_parameters
        self.episodes = episodes
        self.profile = profile
        self.ws = ws_manager
        self.regeneration_context = regeneration_context
        self.api_keys = api_keys
        self.character_capabilities: Optional[CharacterCapabilities] = None
        self._master_orch = None

    def set_master_orch(self, master_orch):
        """マスターオーケストレータの参照をセット（キャンセルチェック用）"""
        self._master_orch = master_orch

    def _check_cancelled(self):
        if self._master_orch and getattr(self._master_orch, "_cancelled", False):
            raise asyncio.CancelledError("User requested cancellation")

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[Phase D] Orchestrator", content, status)

    def _full_context(self) -> str:
        """上流の全成果物を文字列化"""
        micro_summary = (
            f"  気質: {json.dumps([p.model_dump(mode='json') for p in self.micro.temperament[:4]], ensure_ascii=False)}\n"
            f"  価値観: {json.dumps(self.micro.schwartz_values, ensure_ascii=False)}\n"
            f"  理想自己: {self.micro.ideal_self}\n"
            f"  義務自己: {self.micro.ought_self}"
        )
        # capabilities_hints が存在する場合は明示的にコンテキストに追加
        caps_hints = self.concept.capabilities_hints
        caps_hints_text = ""
        if caps_hints and (caps_hints.key_possessions_hint or caps_hints.core_abilities_hint or caps_hints.signature_actions_hint):
            caps_hints_text = (
                f"\n\n【Creative Director capabilities_hints (capabilities生成の方向性指示)】\n"
                f"- key_possessions_hint: {caps_hints.key_possessions_hint}\n"
                f"- core_abilities_hint: {caps_hints.core_abilities_hint}\n"
                f"- signature_actions_hint: {caps_hints.signature_actions_hint}"
            )
        ctx = (
            f"{wrap_context('concept_package', json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2))}\n\n"
            f"{wrap_context('macro_profile', json.dumps(self.macro.model_dump(mode='json'), ensure_ascii=False, indent=2), 'event')}\n\n"
            f"{wrap_context('micro_parameters', micro_summary)}\n\n"
            f"{wrap_context('autobiographical_episodes', json.dumps([e.model_dump(mode='json') for e in self.episodes.episodes], ensure_ascii=False, indent=2))}"
            f"{caps_hints_text}"
        )
        if self.regeneration_context:
            ctx += f"\n\n{self.regeneration_context}"
        return ctx

    async def run(self) -> WeeklyEventsStore:
        """Phase Dを実行"""
        from backend.tools.llm_api import AgentTool, call_llm_agentic

        await self._notify("Phase D: 7日分イベント列一括生成開始")
        context = self._full_context()

        # ── Step 1-2: WorldContext + SupportingCharacters (並列、自然言語テキスト) ──
        world_context = None
        supporting_chars = []
        
        # 既存チェック
        status = self._master_orch.package.status if self._master_orch else None
        
        if status and status.phase_d_world_complete:
            await self._notify("Step 1: 既存の世界設定を読み込み (Skip)")
            world_context = self._master_orch.package.weekly_events_store.world_context
            world_text = world_context.description
        else:
            await self._notify("Step 1: 世界設定を生成")
            world_res = await call_llm(
                tier=self.profile.worker_tier, system_prompt=WORLD_CONTEXT_PROMPT,
                user_message=f"{context}\n\n世界設定を生成してください。",
                api_keys=self.api_keys,
            )
            world_text = world_res["content"] if isinstance(world_res["content"], str) else json.dumps(world_res["content"], ensure_ascii=False)
            world_context = WorldContext(description=world_text)
            if self._master_orch:
                if not self._master_orch.package.weekly_events_store:
                    self._master_orch.package.weekly_events_store = WeeklyEventsStore(world_context=world_context, supporting_characters=[], narrative_arc=NarrativeArc(description=""), conflict_intensity_arc=ConflictIntensityArc(), events=[])
                else:
                    self._master_orch.package.weekly_events_store.world_context = world_context
                self._master_orch.package.status.phase_d_world_complete = True
                await self._master_orch._checkpoint()

        self._check_cancelled()

        if status and status.phase_d_chars_complete:
            await self._notify("Step 2: 既存の周囲人物を読み込み (Skip)")
            supporting_chars = self._master_orch.package.weekly_events_store.supporting_characters
            chars_text = "読み込み済み人物データがあります。" 
        else:
            await self._notify("Step 2: 周囲人物を設計")
            chars_res = await call_llm(
                tier=self.profile.worker_tier, system_prompt=SUPPORTING_CHARACTERS_PROMPT,
                user_message=f"{context}\n\n周囲の人物を設計してください。",
                api_keys=self.api_keys,
            )
            chars_text = chars_res["content"] if isinstance(chars_res["content"], str) else json.dumps(chars_res["content"], ensure_ascii=False)
            
            # パース
            try:
                parse_result = await call_llm(
                    tier=self.profile.worker_tier,
                    system_prompt=(
                        "以下の人物設計テキストをJSONに変換してください。\n"
                        "出力形式: {\"characters\": [{\"name\": \"...\", \"role\": \"...\", "
                        "\"relationship_to_protagonist\": \"...\", \"brief_profile\": \"...\", "
                        "\"own_small_want\": \"...\"}]}\n"
                        "テキストに含まれる全人物を漏れなく含めること。"
                    ),
                    user_message=chars_text,
                    json_mode=True,
                    api_keys=self.api_keys,
                )
                parse_data = parse_result["content"] if isinstance(parse_result["content"], dict) else {}
                for c in parse_data.get("characters", []):
                    supporting_chars.append(SupportingCharacter(
                        name=c.get("name", ""),
                        role=c.get("role", ""),
                        relationship_to_protagonist=c.get("relationship_to_protagonist", ""),
                        brief_profile=c.get("brief_profile", ""),
                        own_small_want=c.get("own_small_want", ""),
                    ))
                
                if self._master_orch:
                    if not self._master_orch.package.weekly_events_store:
                        self._master_orch.package.weekly_events_store = WeeklyEventsStore(world_context=world_context, supporting_characters=supporting_chars, narrative_arc=NarrativeArc(description=""), conflict_intensity_arc=ConflictIntensityArc(), events=[])
                    else:
                        self._master_orch.package.weekly_events_store.supporting_characters = supporting_chars
                    self._master_orch.package.status.phase_d_chars_complete = True
                    await self._master_orch._checkpoint()
            except Exception as e:
                logger.warning(f"[Phase D] SupportingCharacter パース失敗: {e}")

        self._check_cancelled()

        if self.ws:
            await self.ws.send_agent_thought("[Phase D] WorldContext", "世界設定完了", "complete")
            await self.ws.send_agent_thought("[Phase D] SupportingCharacters", "周囲人物設計完了", "complete")

        # ── Step 2.5: CharacterCapabilitiesAgent（エージェンティックループ） ──
        if status and status.phase_d_caps_complete:
            await self._notify("Step 2.5: 既存の所持品・能力を読み込み (Skip)")
            self.character_capabilities = self._master_orch.package.character_capabilities
        else:
            await self._notify("Step 2.5: CharacterCapabilitiesAgent 起動（所持品・能力・行動をエージェントで設計）...")
            from backend.agents.phase_d.capabilities_agent import CharacterCapabilitiesAgent
            caps_agent = CharacterCapabilitiesAgent(
                concept=self.concept,
                macro_profile=self.macro,
                context=context,
                profile=self.profile,
                ws_manager=self.ws,
                api_keys=self.api_keys,
            )
            self.character_capabilities = await caps_agent.run()
            if self._master_orch:
                self._master_orch.package.character_capabilities = self.character_capabilities
                self._master_orch.package.status.phase_d_caps_complete = True
                await self._master_orch._checkpoint()
        
        caps_text = self.character_capabilities.raw_text

        self._check_cancelled()

        # ── Step 3-4: NarrativeArcDesigner + ConflictIntensityDesigner (並列、自然言語) ──
        arc_text = None
        conflict_text = None
        
        if status and status.phase_d_arc_complete:
            await self._notify("Step 3: 既存の物語アークを読み込み (Skip)")
            narrative_arc = self._master_orch.package.weekly_events_store.narrative_arc
            arc_text = narrative_arc.description
        else:
            await self._notify("Step 3: 物語アークを設計")
            arc_res = await call_llm(
                tier=self.profile.director_tier, system_prompt=NARRATIVE_ARC_PROMPT,
                user_message=f"{context}\n\n世界: {world_text}\n\n人物: {chars_text}\n\nアーク設計してください。",
                cache_system=True,
                api_keys=self.api_keys,
            )
            arc_text = arc_res["content"] if isinstance(arc_res["content"], str) else json.dumps(arc_res["content"], ensure_ascii=False)
            narrative_arc = NarrativeArc(description=arc_text)
            if self._master_orch:
                self._master_orch.package.weekly_events_store.narrative_arc = narrative_arc
                self._master_orch.package.status.phase_d_arc_complete = True
                await self._master_orch._checkpoint()

        self._check_cancelled()

        if status and status.phase_d_intensity_complete:
            await self._notify("Step 4: 既存の葛藤強度アークを読み込み (Skip)")
            conflict_intensity = self._master_orch.package.weekly_events_store.conflict_intensity_arc
            conflict_text = conflict_intensity.raw_text
        else:
            await self._notify("Step 4: 葛藤強度アークを設計")
            conflict_res = await call_llm(
                tier=self.profile.worker_tier, system_prompt=CONFLICT_INTENSITY_PROMPT,
                user_message=f"葛藤強度アークを設定してください。",
                api_keys=self.api_keys,
            )
            conflict_text = conflict_res["content"] if isinstance(conflict_res["content"], str) else json.dumps(conflict_res["content"], ensure_ascii=False)
            conflict_intensity = ConflictIntensityArc(raw_text=conflict_text) # テキストを維持して保存
            if self._master_orch:
                self._master_orch.package.weekly_events_store.conflict_intensity_arc = conflict_intensity
                self._master_orch.package.status.phase_d_intensity_complete = True
                await self._master_orch._checkpoint()

        self._check_cancelled()

        # ── Step 5: WeeklyEventWriter（エージェンティックループ） ──
        await self._notify("Step 5: エージェンティック・イベント生成を開始...")

        final_events_data = None
        critique_passed = False
        self_reflect_convinced = False
        upstream_context = f"{context}\n\n世界: {world_text}\n\n人物: {chars_text}\n\nアーク: {arc_text}\n\n強度: {conflict_text}\n\n所持品・能力: {caps_text}"

        # ── Step 5: WeeklyEventWriter（1日ずつ順次生成） ──
        await self._notify("Step 5: イベント順次生成を開始...")

        events = []
        if self._master_orch and self._master_orch.package.weekly_events_store.events:
            events = self._master_orch.package.weekly_events_store.events
            await self._notify(f"既存のイベントを {len(events)} 件読み込みました。")

        upstream_context = f"{context}\n\n世界: {world_text}\n\n人物: {chars_text}\n\nアーク: {arc_text}\n\n強度: {conflict_text}\n\n所持品・能力: {caps_text}"

        for day in range(1, 8):
            self._check_cancelled()
            
            # 既にその日のイベントが生成されているかチェック
            existing_day_events = [e for e in events if e.day == day]
            if len(existing_day_events) > 0:
                await self._notify(f"Day {day}/{7}: 既存イベントあり。スキップ (計 {len(existing_day_events)}件)")
                continue

            await self._notify(f"Day {day}/{7} のイベントを生成中...", "thinking")
            
            # 前日までのイベントをコンテキストに追加
            previous_events_text = ""
            if len(events) > 0:
                previous_events_text = "【これまでのイベント】\n"
                for e in events:
                    previous_events_text += f"- Day {e.day} {e.time_slot}: {e.content} (影響: {e.meaning_to_character})\n"
            else:
                previous_events_text = "【これまでのイベント】\nまだありません。Day 1から始まります。\n"
            
            # この日の物語上の役割（Day5なら山場など）をプロンプトに入れる
            role_hint = ""
            if day <= 4:
                role_hint = "物語の前半〜中盤。日常を描きつつ、Day 5への伏線を張る時期。"
            elif day == 5:
                role_hint = "【重要】Day 5は物語の山場（最大の葛藤・転換点）です。最も衝撃的で重要なイベントを含めてください。"
            elif day == 6:
                role_hint = "Day 6は山場の「余波」を描く時期です。昨日の出来事がどう影響したかを描いてください。"
            elif day == 7:
                role_hint = "Day 7は「収束」です。完全に解決するわけではなく、問いが残る形で終わらせてください。"
                
            day_instruction = f"以上の文脈を踏まえ、**Day {day} のイベントを2-4件**生成してください。\n役割: {role_hint}"

            # 1日分のイベント生成
            res = await call_llm(
                tier=self.profile.director_tier,
                system_prompt=DAILY_EVENT_WRITER_PROMPT,
                user_message=f"{upstream_context}\n\n{previous_events_text}\n\n{day_instruction}",
                json_mode=True,
                api_keys=self.api_keys,
            )
            
            day_data = res["content"] if isinstance(res["content"], dict) else {}
            events_raw = day_data.get("events", [])
            
            day_events_parsed = []
            for evt in events_raw:
                if isinstance(evt, dict):
                    try:
                        # expectednessの確率的制約などはここで強制適用も可能だが、現状はLLMに従う
                        event = Event(
                            id=evt.get("id", f"evt_{(len(events) + len(day_events_parsed) + 1):03d}"),
                            day=day, # 必ず現在のDayにする
                            time_slot=evt.get("time_slot", "morning"),
                            known_to_protagonist=evt.get("known_to_protagonist", True),
                            source=evt.get("source", "routine"),
                            expectedness=evt.get("expectedness", "high"),
                            content=evt.get("content", ""),
                            involved_characters=evt.get("involved_characters", []),
                            meaning_to_character=evt.get("meaning_to_character", ""),
                            narrative_arc_role=evt.get("narrative_arc_role", "daily_rhythm"),
                            conflict_type=evt.get("conflict_type"),
                            connected_episode_id=evt.get("connected_episode_id"),
                            connected_values=evt.get("connected_values", []),
                        )
                        day_events_parsed.append(event)
                    except Exception as e:
                        logger.warning(f"Event parse error on Day {day}: {e}")
            
            if not day_events_parsed:
                logger.warning(f"Day {day} でイベントが1件も生成されませんでした。")
                
            events.extend(day_events_parsed)
            await self._notify(f"Day {day}/{7} 完了: {len(day_events_parsed)}件のイベントを生成", "complete")
            
            # 各日終了後にチェックポイント保存
            if self._master_orch:
                self._master_orch.package.weekly_events_store.events = events
                self._master_orch.package.status.phase_d_current_day = day
                if day == 7:
                    self._master_orch.package.status.phase_d_events_complete = True
                await self._master_orch._checkpoint()

        self._check_cancelled()

        store = WeeklyEventsStore(
            world_context=world_context, 
            supporting_characters=supporting_chars, 
            narrative_arc=narrative_arc, 
            conflict_intensity_arc=conflict_intensity, 
            events=events
        )
        await self._notify(f"Phase D完了: 計 {len(events)}件のイベント生成", "complete")
        return store
