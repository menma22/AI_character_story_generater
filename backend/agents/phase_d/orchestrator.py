"""
Phase D Orchestrator
7日分のイベント列を一括事前生成する。
v10 §2.5 / v2 §6.6 準拠。

責務:
- WorldContextWorker: 世界設定
- SupportingCharactersWorker: 周囲の人物
- NarrativeArcDesigner: 物語アーク + Day5山場設計
- ConflictIntensityDesigner: 葛藤強度アーク
- WeeklyEventWriter: 14-28件のイベント一括生成（エージェンティック化）

設計方針:
- Step 1-4はプロンプトコンテキストとしてのみ使用されるため、
  JSON出力を強制せず自然言語テキストで受け渡す。
- Step 5（イベント生成）はエージェンティックループ（draft → critique → self_reflect → submit）で品質を担保。
- フォールバック: agenticループ失敗時は従来のone-shot JSON出力に切り替え。
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
イベントには、主人公の信条などは一切起こらず、あくまで、どんな出来事が起こるかを記述するだけです。感情や主観的な反応を生み出すのはキャラクター本人に任せます。

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
    ):
        self.concept = concept
        self.macro = macro_profile
        self.micro = micro_parameters
        self.episodes = episodes
        self.profile = profile
        self.ws = ws_manager
        self.regeneration_context = regeneration_context

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[Phase D] Orchestrator", content, status)

    def _full_context(self) -> str:
        """上流の全成果物を文字列化"""
        ctx = (
            f"concept_package:\n{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            f"macro_profile:\n{json.dumps(self.macro.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            f"micro_parameters (主要):\n"
            f"  気質: {json.dumps([p.model_dump(mode='json') for p in self.micro.temperament[:4]], ensure_ascii=False)}\n"
            f"  価値観: {json.dumps(self.micro.schwartz_values, ensure_ascii=False)}\n"
            f"  理想自己: {self.micro.ideal_self}\n"
            f"  義務自己: {self.micro.ought_self}\n\n"
            f"autobiographical_episodes:\n{json.dumps([e.model_dump(mode='json') for e in self.episodes.episodes], ensure_ascii=False, indent=2)}"
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

        # ── Step 5: WeeklyEventWriter（エージェンティックループ） ──
        await self._notify("Step 5: エージェンティック・イベント生成を開始...")

        # 状態変数
        final_events_data = None
        critique_history = []
        critique_iteration = 0
        critique_passed = False
        self_reflect_convinced = False

        # Step 1-4の全コンテキスト
        upstream_context = (
            f"{context}\n\n"
            f"--- 世界設定 ---\n{world_text}\n\n"
            f"--- 周囲人物 ---\n{chars_text}\n\n"
            f"--- 物語アーク ---\n{arc_text}\n\n"
            f"--- 葛藤強度 ---\n{conflict_text}"
        )

        # ── ツールハンドラ ──

        async def draft_events(events_json: str = None, **kw) -> dict:
            """イベントドラフトを提出し、構造バリデーションを受ける"""
            if not events_json:
                return {"status": "FAILED", "message": "ERROR: events_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            critique_passed = False
            self_reflect_convinced = False

            try:
                data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。正しいJSON文字列を渡してください。"}

            events = data.get("events", [])
            issues = []

            # イベント数チェック
            if len(events) < 14:
                issues.append(f"イベント数が{len(events)}件です（最低14件必要）。")
            if len(events) > 28:
                issues.append(f"イベント数が{len(events)}件です（最大28件）。")

            # 日別分布チェック
            day_counts = {}
            for evt in events:
                day = evt.get("day", 0)
                day_counts[day] = day_counts.get(day, 0) + 1
            for day in range(1, 8):
                count = day_counts.get(day, 0)
                if count < 2:
                    issues.append(f"Day {day}のイベントが{count}件です（最低2件必要）。")
                if count > 4:
                    issues.append(f"Day {day}のイベントが{count}件です（最大4件）。")

            # protagonist_planチェック
            for evt in events:
                if evt.get("source") == "protagonist_plan":
                    issues.append("protagonist_planソースが検出されました（Phase Dでは禁止）。")
                    break

            # expectedness分布チェック
            high_count = sum(1 for e in events if e.get("expectedness") == "high")
            if len(events) > 0 and high_count < len(events) / 2:
                issues.append(f"expectedness=highが{high_count}/{len(events)}件です（半分以上必要）。")

            # Day5以外のlow制限チェック
            for day in range(1, 8):
                if day == 5:
                    continue
                low_count = sum(1 for e in events if e.get("day") == day and e.get("expectedness") == "low")
                if low_count > 1:
                    issues.append(f"Day {day}にlow expectednessが{low_count}件あります（Day5以外は最大1件）。")

            await self._notify(f"イベントドラフト受領: {len(events)}件")

            if issues:
                return {"status": "NEEDS_FIX", "message": f"構造的な問題があります: {'; '.join(issues)}。修正してから再度draft_eventsを呼び出してください。"}
            else:
                return {"status": "SUCCESS", "message": f"{len(events)}件のイベントを受領しました。request_critiqueで品質評価を受けてください。"}

        async def request_critique(events_json: str = None, **kw) -> dict:
            """別LLMインスタンスによるイベント列品質批評"""
            if not events_json:
                return {"status": "FAILED", "message": "ERROR: events_json引数が欠落しています。"}

            nonlocal critique_iteration, critique_passed

            try:
                data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。"}

            critique_iteration += 1
            await self._notify(f"イベント批評を依頼中...（試行 {critique_iteration}）")

            critique_result = await call_llm(
                tier="sonnet",
                system_prompt=EVENT_CRITIQUE_PROMPT,
                user_message=f"以下のキャラクターコンテキストとイベント列を評価してください:\n\n--- コンテキスト ---\n{upstream_context}\n\n--- イベント列 ---\n{json.dumps(data, ensure_ascii=False, indent=2)}",
                json_mode=True,
                cache_system=True,
            )

            critique = critique_result["content"] if isinstance(critique_result["content"], dict) else {}
            critique_history.append(critique)

            checks = critique.get("checks", {})
            check_summary = []
            for key, val in checks.items():
                status_mark = "✓" if val.get("passed", False) else "✗"
                check_summary.append(f"  [{status_mark}] {key}: {val.get('comment', '')[:60]}")

            verdict = critique.get("verdict", "pass")
            await self._notify(f"イベント批評結果（Verdict: {verdict}）:\n" + "\n".join(check_summary))

            if verdict == "pass":
                critique_passed = True
                return {"status": "SUCCESS", "message": "CRITIQUE PASSED. 次にself_reflectツールで自己内省を行い、本当にこれで良いか確認してください。"}
            else:
                critique_passed = False
                return {"status": "FAILED", "feedback": critique}

        async def self_reflect_events(events_json: str = None, **kw) -> dict:
            """外部批評pass後の自己内省"""
            if not events_json:
                return {"status": "FAILED", "message": "ERROR: events_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced

            if not critique_passed:
                return {"status": "BLOCKED", "message": "ERROR: 先にrequest_critiqueでpassを得てください。"}

            try:
                data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。"}

            await self._notify("自己内省中...「本当にこの7日間でいいのか？」")

            reflect_result = await call_llm(
                tier="sonnet",
                system_prompt=EVENT_SELF_REFLECT_PROMPT,
                user_message=f"以下のキャラクターとイベント列について、本当にこれでいいか正直に自問してください:\n\n--- コンテキスト ---\n{upstream_context}\n\n--- イベント列 ---\n{json.dumps(data, ensure_ascii=False, indent=2)}",
                json_mode=True,
                cache_system=True,
            )

            reflection = reflect_result["content"] if isinstance(reflect_result["content"], dict) else {}
            convinced = reflection.get("convinced", False)

            if convinced:
                self_reflect_convinced = True
                await self._notify(f"自己内省結果: 確信あり ✓ — {reflection.get('reason', '')[:80]}")
                return {"status": "SUCCESS", "message": "SELF-REFLECT PASSED. submit_final_eventsで提出してください。"}
            else:
                self_reflect_convinced = False
                critique_passed = False
                reason = reflection.get("reason", "不明")
                suggestion = reflection.get("improvement_suggestion", "")
                await self._notify(f"自己内省結果: まだ妥協あり ✗ — {reason[:80]}")
                return {"status": "FAILED", "message": f"まだ確信が持てません。理由: {reason}。改善案: {suggestion}。ドラフトを改善し、再度draft_events → request_critique → self_reflectの順で進めてください。"}

        async def submit_final_events(events_json: str = None, **kw) -> dict:
            """最終イベントデータを提出"""
            if not events_json:
                return {"status": "FAILED", "message": "ERROR: events_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed or not self_reflect_convinced:
                blocked_reasons = []
                if not critique_passed:
                    blocked_reasons.append("request_critiqueでpassを得ていない")
                if not self_reflect_convinced:
                    blocked_reasons.append("self_reflectで確信を得ていない")
                return {"status": "BLOCKED", "message": f"ERROR: 提出がブロックされました。理由: {', '.join(blocked_reasons)}。"}

            try:
                data = json.loads(events_json) if isinstance(events_json, str) else events_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。"}

            nonlocal final_events_data
            final_events_data = data
            await self._notify("最終イベントデータが提出されました。", "complete")
            return {"status": "SUCCESS", "message": "Task complete. Thank you."}

        # ── ツール定義 ──
        tools = [
            AgentTool(
                name="draft_events",
                description="7日分14-28件のイベントドラフトを提出し、構造バリデーションを受けます。新しいドラフトを提出するとcritique/self_reflectの結果はリセットされます。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "events_json": {"type": "string", "description": "イベントデータ全体のJSON文字列（{\"events\": [...]}形式）"}
                    },
                    "required": ["events_json"]
                },
                handler=draft_events
            ),
            AgentTool(
                name="request_critique",
                description="現在のイベントドラフトを別のLLMが厳しく評価します。物語アーク整合性、メタデータ品質、物語的接続、キャラクター固有性等をチェックします。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "events_json": {"type": "string", "description": "イベントデータ全体のJSON文字列"}
                    },
                    "required": ["events_json"]
                },
                handler=request_critique
            ),
            AgentTool(
                name="self_reflect",
                description="request_critiqueでpassを得た後に呼び出す内省ツール。「本当にこの7日間でいいのか？」を自問します。確信が持てない場合はcritique_passedもリセットされます。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "events_json": {"type": "string", "description": "イベントデータ全体のJSON文字列"}
                    },
                    "required": ["events_json"]
                },
                handler=self_reflect_events
            ),
            AgentTool(
                name="submit_final_events",
                description="request_critiqueでpass かつ self_reflectでconvinced=trueを得た後にのみ呼び出せます。最終イベントデータをシステムに提出します。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "events_json": {"type": "string", "description": "完成したイベントデータ全体のJSON文字列"}
                    },
                    "required": ["events_json"]
                },
                handler=submit_final_events
            ),
        ]

        agentic_sys_prompt = WEEKLY_EVENT_WRITER_PROMPT + """

【エージェンティック行動指針 — 4フェーズ厳守】

【Phase 1: 計画】
- 物語アーク設計と葛藤強度設計を注意深く読む
- Day 5の山場を中心に、7日間の流れを計画する
- 各日のイベント数と種類を事前に設計する

【Phase 2: ドラフト → 外部批評】
- draft_eventsツールで7日分のイベント列ドラフトを提出する
- request_critiqueで品質評価を受ける
- refineの場合は指摘に基づいて改善し、再度draft_events → request_critique

【Phase 3: 自己内省 — 「本当にこれでいいのか？」】
- request_critiqueでpassを得たら、self_reflectツールを呼び出す
- 「この7日間は本当に面白いか？Day5は山場として機能するか？退屈なイベントはないか？」を正直に自問
- convinced=falseが返った場合: critique_passedもリセット。改善してPhase 2からやり直す

【Phase 4: 確信を持って提出】
- critique_passed=True かつ self_reflect_convinced=True でのみ
- submit_final_eventsツールで提出する
"""

        event_user_msg = f"{upstream_context}\n\n上記全てを参照し、7日分のイベント列をJSON形式で生成してください。"

        logger.info("[Phase D] Starting agentic event generation loop")
        if self.ws:
            await self.ws.send_agent_thought("[Phase D] WeeklyEventWriter", "エージェンティック・ループを起動します...", "thinking")

        max_iter = max(10, self.profile.worker_regeneration_max_iterations * 3)

        if self.profile.director_tier in ("opus", "sonnet"):
            try:
                await call_llm_agentic(
                    tier=self.profile.director_tier,
                    system_prompt=agentic_sys_prompt,
                    user_message=event_user_msg,
                    tools=tools,
                    max_iterations=max_iter,
                )
            except Exception as e:
                logger.warning(f"[Phase D] Claude agentic failed: {e}. Falling back to Gemini.")
                from backend.tools.llm_api import call_llm_agentic_gemini
                await call_llm_agentic_gemini(
                    system_prompt=agentic_sys_prompt,
                    user_message=event_user_msg,
                    tools=tools,
                    max_iterations=max_iter,
                )
        elif self.profile.director_tier == "gemini":
            from backend.tools.llm_api import call_llm_agentic_gemini
            await call_llm_agentic_gemini(
                system_prompt=agentic_sys_prompt,
                user_message=event_user_msg,
                tools=tools,
                max_iterations=max_iter,
            )

        # ── フォールバック: 従来のone-shot JSON出力 ──
        if not final_events_data:
            logger.warning("[Phase D] Agentic loop failed. Falling back to one-shot.")
            await self._notify("エージェンティックループ不完全終了。一発出しフォールバック実行中...", "warning")

            event_result = await call_llm(
                tier=self.profile.director_tier,
                system_prompt=WEEKLY_EVENT_WRITER_PROMPT,
                user_message=event_user_msg,
                json_mode=True,
                cache_system=True,
                cache_context=context,
            )

            if isinstance(event_result["content"], dict):
                final_events_data = event_result["content"]
            else:
                logger.error(
                    f"[Phase D] WeeklyEventWriter returned non-dict "
                    f"(type={type(event_result['content']).__name__}). "
                    f"Raw preview: {str(event_result.get('raw', ''))[:300]}"
                )
                await self._notify("CRITICAL: イベントJSON解析失敗", "error")
                final_events_data = {}

        # ── イベントJSONパース ──
        events_raw = final_events_data.get("events", [])

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
                f"events_data keys: {list(final_events_data.keys()) if final_events_data else 'EMPTY DICT'}"
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
