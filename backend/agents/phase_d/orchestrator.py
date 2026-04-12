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


# ── Step 5: イベント生成（エージェンティック化） ──

WEEKLY_EVENT_WRITER_PROMPT = """あなたは7日間のイベント列を一括生成するWeeklyEventWriterです。
NarrativeArcDesignerの設計に従い、各日2-4件、合計14-28件のイベントを生成してください。
イベントには、主人公の心情などの主観的な内容は入れず、あくまで、主人公にその状況を与えることで面白い反応が得られそうな出来事を記述するだけです。感情や主観的な反応を生み出すのはキャラクター本人に任せます。

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

EVENT_CRITIQUE_PROMPT = """あなたはイベント列品質評価者です。
以下の7日分イベント列を厳しく評価してください。

【評価基準】
[A] 物語アーク整合性:
  □ Day 5が山場として機能しているか
  □ Day 1-4に伏線(day5_foreshadowing)が最低2件あるか
  □ Day 6が余波を描いているか
  □ Day 7が収束しているか（完全解決ではなく、問いが残る形）

[B] メタデータ品質:
  □ expectedness分布: highが半分以上か
  □ lowはDay5以外で各日最大1件か
  □ protagonist_planが0件か
  □ meaning_to_characterが曖昧語（面白い、大変、普通等）を使っていないか

[C] 物語的接続:
  □ previous_day_callbackが最低2件あるか
  □ connected_episode_idが最低2件で使用されているか
  □ 繰り返しのモチーフが感じられるか

[D] キャラクター固有性:
  □ イベントがこのキャラクターの職業・価値観・人間関係と整合するか
  □ supporting_charactersが自分の欲求に基づいて行動しているか

[E] コンテンツ品質:
  □ 各イベントのcontentが3-5文で具体的か
  □ involved_charactersが適切に設定されているか
  □ 時間帯(time_slot)が1日の中で自然な分布か

【判定】
全項目passなら "verdict": "pass"
1つでも不十分なら "verdict": "refine" と改善指示を出す

出力形式:
{
  "checks": {
    "A_narrative_arc": {"passed": true/false, "comment": "..."},
    "B_metadata_quality": {"passed": true/false, "comment": "..."},
    "C_narrative_connection": {"passed": true/false, "comment": "..."},
    "D_character_specificity": {"passed": true/false, "comment": "..."},
    "E_content_quality": {"passed": true/false, "comment": "..."}
  },
  "verdict": "pass" or "refine",
  "refinement_instructions": "改善指示（refine時のみ）"
}
"""

EVENT_SELF_REFLECT_PROMPT = """あなたはイベント列エージェントの内なる声です。
外部批評（request_critique）はpassしました。しかし、本当にこれでいいのでしょうか？

以下の7日分イベント列を読み、正直に自問してください:

1. 【面白いか？】この7日間を日記として読んだとき、退屈な日はないか？
2. 【Day 5は衝撃的か？】山場として本当に機能するか？読者の心が動くか？
3. 【日常と非日常のバランス】routineイベントばかりで単調ではないか？
   逆に、非日常ばかりでリアリティがないのでは？
4. 【キャラクターらしさ】このキャラクターだからこそ起きるイベントか？
   別のキャラに差し替えても成立するような汎用イベントはないか？
5. 【妥協】数合わせのために適当に作ったイベントはないか？

【判定】
心から「この7日間は面白い。読者を引き込める」と思えるなら:
  {"convinced": true, "reason": "なぜ確信が持てるか"}
まだ妥協や不安があるなら:
  {"convinced": false, "reason": "何が引っかかるか", "improvement_suggestion": "具体的改善案"}
"""


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
        await self._notify("Step 1-2: 世界設定 + 周囲人物を並列生成")

        world_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=WORLD_CONTEXT_PROMPT,
            user_message=f"{context}\n\n世界設定を生成してください。",
            api_keys=self.api_keys,
        )
        chars_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=SUPPORTING_CHARACTERS_PROMPT,
            user_message=f"{context}\n\n周囲の人物を設計してください。",
            api_keys=self.api_keys,
        )

        world_result, chars_result = await asyncio.gather(world_task, chars_task)

        world_text = world_result["content"] if isinstance(world_result["content"], str) else json.dumps(world_result["content"], ensure_ascii=False)
        chars_text = chars_result["content"] if isinstance(chars_result["content"], str) else json.dumps(chars_result["content"], ensure_ascii=False)

        world_context = WorldContext(description=world_text)

        # chars_text（自然言語）から SupportingCharacter オブジェクトをパース
        supporting_chars = []
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
        except Exception as e:
            logger.warning(f"[Phase D] SupportingCharacter パース失敗（空リストで続行）: {e}")

        if self.ws:
            await self.ws.send_agent_thought("[Phase D] WorldContext", "世界設定生成完了", "complete")
            await self.ws.send_agent_thought("[Phase D] SupportingCharacters", "周囲人物設計完了", "complete")

        # ── Step 2.5: CharacterCapabilitiesAgent（エージェンティックループ） ──
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
        caps_text = self.character_capabilities.raw_text

        # ── Step 3-4: NarrativeArcDesigner + ConflictIntensityDesigner (並列、自然言語) ──
        await self._notify("Step 3-4: 物語アーク + 葛藤強度設計")

        arc_task = call_llm(
            tier=self.profile.director_tier, system_prompt=NARRATIVE_ARC_PROMPT,
            user_message=f"{context}\n\n世界: {world_text}\n\n人物: {chars_text}\n\nアーク設計してください。",
            cache_system=True,
            api_keys=self.api_keys,
        )
        conflict_task = call_llm(
            tier=self.profile.worker_tier, system_prompt=CONFLICT_INTENSITY_PROMPT,
            user_message=f"葛藤強度アークを設定してください。",
            api_keys=self.api_keys,
        )

        arc_result, conflict_result = await asyncio.gather(arc_task, conflict_task)
        arc_text = arc_result["content"] if isinstance(arc_result["content"], str) else json.dumps(arc_result["content"], ensure_ascii=False)
        conflict_text = conflict_result["content"] if isinstance(conflict_result["content"], str) else json.dumps(conflict_result["content"], ensure_ascii=False)

        narrative_arc = NarrativeArc(description=arc_text)
        conflict_intensity = ConflictIntensityArc()

        # ── Step 5: WeeklyEventWriter（エージェンティックループ） ──
        await self._notify("Step 5: エージェンティック・イベント生成を開始...")

        final_events_data = None
        critique_passed = False
        self_reflect_convinced = False
        upstream_context = f"{context}\n\n世界: {world_text}\n\n人物: {chars_text}\n\nアーク: {arc_text}\n\n強度: {conflict_text}\n\n所持品・能力: {caps_text}"

        async def draft_events(events_json: str = None, **kw) -> dict:
            nonlocal critique_passed, self_reflect_convinced
            critique_passed = False
            self_reflect_convinced = False
            try: data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except: return {"status": "FAILED", "message": "JSONパースエラー。"}
            evts = data.get("events", [])
            if len(evts) < 14: return {"status": "NEEDS_FIX", "message": "イベント数が足りません。"}
            await self._notify(f"イベントドラフト受領: {len(evts)}件")
            return {"status": "SUCCESS", "message": "受領しました。"}

        async def request_critique(events_json: str = None, **kw) -> dict:
            nonlocal critique_passed
            try: data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except: return {"status": "FAILED", "message": "JSONパースエラー。"}
            res = await call_llm(
                tier="sonnet", system_prompt=EVENT_CRITIQUE_PROMPT,
                user_message=f"評価してください:\n\n{upstream_context}\n\n{json.dumps(data, ensure_ascii=False)}",
                json_mode=True, cache_system=True, api_keys=self.api_keys,
            )
            critique = res["content"] if isinstance(res["content"], dict) else {}
            verdict = critique.get("verdict", "pass")
            await self._notify(f"批評結果: {verdict}")
            if verdict == "pass":
                critique_passed = True
                return {"status": "SUCCESS", "message": "PASSED."}
            return {"status": "FAILED", "feedback": critique}

        async def self_reflect_events(events_json: str = None, **kw) -> dict:
            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed: return {"status": "BLOCKED", "message": "先に批評を。"}
            try: data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except: return {"status": "FAILED", "message": "JSONパースエラー。"}
            res = await call_llm(
                tier="sonnet", system_prompt=EVENT_SELF_REFLECT_PROMPT,
                user_message=f"自問してください:\n\n{json.dumps(data, ensure_ascii=False)}",
                json_mode=True, cache_system=True, api_keys=self.api_keys,
            )
            convinced = res["content"].get("convinced", False)
            if convinced:
                self_reflect_convinced = True
                return {"status": "SUCCESS", "message": "PASSED."}
            critique_passed = False
            return {"status": "FAILED", "message": "まだ妥協があります。"}

        async def submit_final_events(events_json: str = None, **kw) -> dict:
            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed or not self_reflect_convinced: return {"status": "BLOCKED", "message": "品質ゲート。"}
            try: data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except: return {"status": "FAILED", "message": "JSONパースエラー。"}
            nonlocal final_events_data
            final_events_data = data
            return {"status": "SUCCESS", "message": "Task complete."}

        tools = [
            AgentTool(name="draft_events", description="ドラフト提出。", input_schema={"type": "object", "properties": {"events_json": {"type": "string"}}, "required": ["events_json"]}, handler=draft_events),
            AgentTool(name="request_critique", description="品質批評。", input_schema={"type": "object", "properties": {"events_json": {"type": "string"}}, "required": ["events_json"]}, handler=request_critique),
            AgentTool(name="self_reflect", description="自己内省。", input_schema={"type": "object", "properties": {"events_json": {"type": "string"}}, "required": ["events_json"]}, handler=self_reflect_events),
            AgentTool(name="submit_final_events", description="最終提出。", input_schema={"type": "object", "properties": {"events_json": {"type": "string"}}, "required": ["events_json"]}, handler=submit_final_events),
        ]

        agentic_sys_prompt = WEEKLY_EVENT_WRITER_PROMPT + "\n\n【行動指針】draft → request_critique → self_reflect → submit の順で。"
        event_user_msg = f"{upstream_context}\n\n生成してください。"
        max_iter = max(10, self.profile.worker_regeneration_max_iterations * 3)

        if self.profile.director_tier in ("opus", "sonnet"):
            try:
                await call_llm_agentic(tier=self.profile.director_tier, system_prompt=agentic_sys_prompt, user_message=event_user_msg, tools=tools, max_iterations=max_iter, api_keys=self.api_keys)
            except Exception as e:
                logger.warning(f"Claude agentic failed: {e}. Falling back.")
                from backend.tools.llm_api import call_llm_agentic_gemini
                await call_llm_agentic_gemini(system_prompt=agentic_sys_prompt, user_message=event_user_msg, tools=tools, max_iterations=max_iter, api_keys=self.api_keys)
        elif self.profile.director_tier in ("gemini", "gemini_pro"):
            from backend.tools.llm_api import call_llm_agentic_gemini
            gemini_model = LLMModels.GEMINI_3_1_PRO if self.profile.director_tier == "gemini_pro" else None
            await call_llm_agentic_gemini(system_prompt=agentic_sys_prompt, user_message=event_user_msg, tools=tools, max_iterations=max_iter, api_keys=self.api_keys, model=gemini_model)

        # ── フォールバック ──
        if not final_events_data:
            logger.warning("[Phase D] Falling back to one-shot.")
            res = await call_llm(tier=self.profile.director_tier, system_prompt=WEEKLY_EVENT_WRITER_PROMPT, user_message=event_user_msg, json_mode=True, cache_system=True, api_keys=self.api_keys)
            final_events_data = res["content"] if isinstance(res["content"], dict) else {}

        # ── パース ──
        events_raw = final_events_data.get("events", [])
        events = []
        for i, evt in enumerate(events_raw):
            if isinstance(evt, dict):
                try:
                    event = Event(
                        id=evt.get("id", f"evt_{len(events)+1:03d}"),
                        day=int(evt.get("day", 1)),
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
                    events.append(event)
                except Exception as e: logger.warning(f"Event parse error: {e}")

        store = WeeklyEventsStore(world_context=world_context, supporting_characters=supporting_chars, narrative_arc=narrative_arc, conflict_intensity_arc=conflict_intensity, events=events)
        await self._notify(f"Phase D完了: {len(events)}件のイベント生成", "complete")
        return store
