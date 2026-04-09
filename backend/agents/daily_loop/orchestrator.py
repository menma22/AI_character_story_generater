"""
日次ループオーケストレータ
v10 §4 に準拠した日記生成ワークフロー。

外層ループ: Day 1 → Day 7
内層ループ: 各日のイベント4-6個を順次処理
各イベント処理: Perceiver → RIM(並列) → 統合 → 情景描写 → 違反チェック
1日の終わり: 内省 → 日記生成 → key memory → 記憶圧縮 → 翌日予定
"""

import json
import asyncio
import logging
from typing import Optional

from backend.models.character import (
    CharacterPackage, MacroProfile, MicroParameters,
    AutobiographicalEpisodes, WeeklyEventsStore, Event,
)
from backend.models.memory import (
    MoodState, ShortTermMemoryDB, KeyMemory, ShortTermMemoryNormal,
    DayProcessingState, PerceiverOutput, ImpulsiveOutput,
    ReflectiveOutput, IntegrationOutput, SceneNarration,
    ValuesViolationResult, EventPackage, IntrospectionMemo,
    DiaryEntry,
)
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


class DailyLoopOrchestrator:
    """Day 1-7 日次ループオーケストレータ"""
    
    def __init__(self, package: CharacterPackage, ws_manager=None):
        self.package = package
        self.ws = ws_manager
        
        # 状態
        self.current_mood = MoodState()
        self.memory_db = ShortTermMemoryDB()
        self.day_results: list[DayProcessingState] = []
        self.action_buffer: list[str] = []
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[日次ループ]", content, status)
    
    def _get_day_events(self, day: int) -> list[Event]:
        """指定日のイベントを取得（時刻順にソート）"""
        if not self.package.weekly_events_store:
            return []
        
        time_order = {"morning": 0, "late_morning": 1, "noon": 2, "afternoon": 3,
                      "evening": 4, "night": 5, "late_night": 6}
        
        events = [e for e in self.package.weekly_events_store.events if e.day == day]
        events.sort(key=lambda e: time_order.get(e.time_slot, 0))
        return events
    
    def _build_macro_context(self) -> str:
        """マクロプロフィール(常時プロンプト同梱)"""
        if self.package.macro_profile:
            return json.dumps(self.package.macro_profile.model_dump(mode="json"), ensure_ascii=False, indent=2)
        return "{}"
    
    def _build_episodes_context(self) -> str:
        """自伝的エピソード(全文ベタ貼り)"""
        if self.package.autobiographical_episodes:
            return json.dumps(
                [e.model_dump(mode="json") for e in self.package.autobiographical_episodes.episodes],
                ensure_ascii=False, indent=2
            )
        return "[]"
    
    def _build_memory_context(self) -> str:
        """短期記憶DBのコンテキスト"""
        parts = []
        for km in self.memory_db.key_memories:
            parts.append(f"[Day {km.day} key memory]: {km.content}")
        for nm in self.memory_db.normal_area:
            parts.append(f"[Day {nm.day} {nm.stage}]: {nm.summary[:200]}")
        return "\n".join(parts) if parts else "(まだ記憶なし)"
    
    def _build_action_buffer(self) -> str:
        """行動履歴バッファ"""
        return "\n".join(self.action_buffer[-10:]) if self.action_buffer else "(行動履歴なし)"
    
    # ─── Perceiver ────────────────────────────────────────────
    async def _perceiver(self, event: Event) -> PerceiverOutput:
        """Perceiver: 現象的記述 + 反射感情 + 自動注意（v10 §4.3）"""
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは主人公AIのPerceiver（知覚エージェント）です。
与えられたイベントに対して、主人公がどう知覚するかを記述してください。

【出力形式】JSON:
{
  "phenomenal_description": "五感を使った現象的記述（何が見え、聞こえ、感じられるか）",
  "reflexive_emotion": "反射的に浮かぶ感情（考える前の感覚）",
  "automatic_attention": "自動的に注意が向く点（何が気になるか）"
}""",
            user_message=(
                f"主人公プロフィール:\n{self._build_macro_context()}\n\n"
                f"現在のムード: V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}\n\n"
                f"今日これまでの行動:\n{self._build_action_buffer()}\n\n"
                f"【イベント】\n{event.content}\n（時間帯: {event.time_slot}）"
            ),
            max_tokens=1000,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return PerceiverOutput(**{k: data.get(k, "") for k in ["phenomenal_description", "reflexive_emotion", "automatic_attention"]})
    
    # ─── Impulsive Agent ──────────────────────────────────────
    async def _impulsive(self, event: Event, perceiver: PerceiverOutput) -> ImpulsiveOutput:
        """Impulsive Agent: 気質・性格層への反射反応（v10 §4.6 Step 1）"""
        # 隠蔽原則: このエージェントは気質・性格層にアクセス可能
        temperament_context = ""
        if self.package.micro_parameters:
            temperament_context = json.dumps(
                [p.model_dump(mode="json") for p in self.package.micro_parameters.temperament],
                ensure_ascii=False
            )
        
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは主人公AIのImpulsive Agent（衝動系エージェント）です。
気質・性格パラメータを参照し、このイベントに対する衝動的な反応を生成してください。
これは「考える前の反応」です。理性的な判断はReflective Agentの仕事です。

【出力形式】JSON:
{
  "impulse_reaction": "衝動的な反応（「思わず○○したくなった」形式）",
  "bodily_sensation": "身体感覚（胃がきゅっとする、手に汗が、等）",
  "action_tendency": "行動傾向（「○○しそうになる」形式）"
}""",
            user_message=(
                f"気質パラメータ:\n{temperament_context}\n\n"
                f"知覚output:\n{json.dumps(perceiver.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"イベント: {event.content}"
            ),
            max_tokens=800,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return ImpulsiveOutput(**{k: data.get(k, "") for k in ["impulse_reaction", "bodily_sensation", "action_tendency"]})
    
    # ─── Reflective Agent ─────────────────────────────────────
    async def _reflective(self, event: Event, perceiver: PerceiverOutput) -> ReflectiveOutput:
        """理性ブランチ: 規範層アクセス + 内面分析（v10 §4.6 Step 2）"""
        # 隠蔽原則: このエージェントは気質・性格層にアクセス不可、規範層にアクセス可
        normative_context = ""
        if self.package.micro_parameters:
            normative_context = json.dumps({
                "schwartz_values": self.package.micro_parameters.schwartz_values,
                "ideal_self": self.package.micro_parameters.ideal_self,
                "ought_self": self.package.micro_parameters.ought_self,
                "goals": self.package.micro_parameters.goals,
            }, ensure_ascii=False)
        
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは主人公AIの理性ブランチ（Reflective Agent）です。
規範層（価値観、理想自己、義務自己）を参照し、このイベントに対する内面分析を行ってください。
「何を考え、何を連想し、どう判断するか」を記述します。

【重要】あなたは気質・性格パラメータにアクセスできません。
価値観と過去の記憶のみを根拠に分析してください。

【出力形式】JSON:
{
  "inner_analysis": "濃密な内面分析レポート（3-5文）",
  "value_connections": "価値観・知識・過去経験との接続（2-3文）",
  "suggestion": "この状況でどうすべきかの示唆",
  "prediction": "理性ルートで行動した場合の予測"
}""",
            user_message=(
                f"規範層:\n{normative_context}\n\n"
                f"過去の記憶:\n{self._build_memory_context()}\n\n"
                f"自伝的エピソード:\n{self._build_episodes_context()}\n\n"
                f"知覚output:\n{json.dumps(perceiver.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"イベント: {event.content}"
            ),
            max_tokens=1200,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return ReflectiveOutput(**{k: data.get(k, "") for k in ["inner_analysis", "value_connections", "suggestion", "prediction"]})
    
    # ─── 統合エージェント ──────────────────────────────────────
    async def _integration(self, event: Event, impulsive: ImpulsiveOutput, reflective: ReflectiveOutput) -> IntegrationOutput:
        """統合エージェント: 2ルート予測 + Higgins評価 + 行動決定（v10 §4.6 Step 3）"""
        normative_context = ""
        if self.package.micro_parameters:
            normative_context = f"理想自己: {self.package.micro_parameters.ideal_self}\n義務自己: {self.package.micro_parameters.ought_self}"
        
        result = await call_llm(
            tier="sonnet",
            system_prompt="""あなたは主人公AIの統合エージェントです。
衝動ルートと理性ルートの2つの反応を統合し、最終的な行動を決定してください。

【Higgins自己不一致理論を適用】
- Ideal不一致（理想と現実のギャップ）→ 落胆・がっかり系の感情
- Ought不一致（義務と現実のギャップ）→ 不安・罪悪感系の感情
- 不一致が大きいほど感情変化が強い

【出力形式】JSON:
{
  "impulse_route_good": "衝動に従った場合の良い予測",
  "impulse_route_bad": "衝動に従った場合の悪い予測",
  "reflective_route_good": "理性に従った場合の良い予測",
  "reflective_route_bad": "理性に従った場合の悪い予測",
  "higgins_ideal_gap": "Ideal不一致の記述",
  "higgins_ought_gap": "Ought不一致の記述",
  "final_action": "最終的な行動決定（具体的に、3-5文）",
  "emotion_change": "気持ちの変化の短文記述"
}""",
            user_message=(
                f"{normative_context}\n\n"
                f"衝動反応:\n{json.dumps(impulsive.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"理性分析:\n{json.dumps(reflective.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"イベント: {event.content}"
            ),
            max_tokens=1500,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return IntegrationOutput(**{k: data.get(k, "") for k in [
            "impulse_route_good", "impulse_route_bad",
            "reflective_route_good", "reflective_route_bad",
            "higgins_ideal_gap", "higgins_ought_gap",
            "final_action", "emotion_change",
        ]})
    
    # ─── 情景描写・後日譚 ──────────────────────────────────────
    async def _scene_narration(self, event: Event, integration: IntegrationOutput) -> SceneNarration:
        """情景描写 + 後日譚（v10 §4.6 Step 4）"""
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは情景描写の執筆者です。
行動決定に基づいて、その場面の濃密な情景描写と、直後の後日譚を書いてください。

【出力形式】JSON:
{
  "scene_description": "濃密な情景描写（3-5文、五感を含む）",
  "aftermath": "直後の後日譚（1-3文、行動の結果として何が起きたか）"
}""",
            user_message=(
                f"イベント: {event.content}\n\n"
                f"行動決定: {integration.final_action}\n\n"
                f"気持ち変化: {integration.emotion_change}"
            ),
            max_tokens=800,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return SceneNarration(**{k: data.get(k, "") for k in ["scene_description", "aftermath"]})
    
    # ─── 価値観違反チェック ────────────────────────────────────
    async def _values_violation(self, integration: IntegrationOutput) -> ValuesViolationResult:
        """価値観違反チェック（v10 §4.6c）"""
        values_context = ""
        if self.package.micro_parameters:
            values_context = json.dumps(self.package.micro_parameters.schwartz_values, ensure_ascii=False)
        
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは価値観違反チェッカーです。
行動決定が主人公の価値観に違反していないかチェックしてください。

出力形式: JSON
{
  "violation_detected": true/false,
  "violation_content": "違反内容（なければ空）",
  "guilt_emotion": "罪悪感の感情記述（なければ空）"
}""",
            user_message=(
                f"価値観:\n{values_context}\n\n"
                f"行動決定: {integration.final_action}\n\n"
                f"Higgins Ideal gap: {integration.higgins_ideal_gap}\n"
                f"Higgins Ought gap: {integration.higgins_ought_gap}"
            ),
            max_tokens=500,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return ValuesViolationResult(**{k: data.get(k, v) for k, v in [
            ("violation_detected", False), ("violation_content", ""), ("guilt_emotion", "")
        ]})
    
    # ─── ムード更新 ───────────────────────────────────────────
    def _update_mood(self, integration: IntegrationOutput, violation: ValuesViolationResult):
        """PADムード更新（簡易版、v10 §4.5）"""
        # 感情慣性に基づく減衰
        inertia = 0.5
        if self.package.micro_parameters:
            inertia = self.package.micro_parameters.emotional_inertia
        
        decay = self.package.micro_parameters.decay_lambda if self.package.micro_parameters else {"V": 0.15, "A": 0.2, "D": 0.1}
        
        # 減衰適用
        self.current_mood.valence *= (1 - decay.get("V", 0.15))
        self.current_mood.arousal *= (1 - decay.get("A", 0.2))
        self.current_mood.dominance *= (1 - decay.get("D", 0.1))
        
        # 違反時の影響
        if violation.violation_detected:
            self.current_mood.valence = max(-5, self.current_mood.valence - 1.0)
            self.current_mood.dominance = max(-5, self.current_mood.dominance - 0.5)
    
    # ─── 内省フェーズ ──────────────────────────────────────────
    async def _introspection(self, day: int, events_processed: list[EventPackage]) -> IntrospectionMemo:
        """内省フェーズ: 3工程（v10 §4.7）"""
        action_summary = "\n".join([f"- {ep.integration_output.final_action[:80]}..." for ep in events_processed])
        
        result = await call_llm(
            tier="sonnet",
            system_prompt="""あなたは主人公AIの内省エージェントです。
今日1日の出来事を振り返り、内省メモを生成してください。

【3工程】
1. 自己推測（Bem Self-Perception Theory）: 自分の行動パターンから自分はどういう人間かを推測する
   ※ 気質パラメータそのものにはアクセスできない。行動からの推測のみ。
2. 過去記録との統合: 記憶にある過去の出来事と今日の出来事に接続点があるか
3. 薄れた記憶の再解釈: 過去の出来事を今日の経験を通じて新たに意味づける

【出力形式】JSON
{
  "self_perception": "自己推測（2-3文）",
  "past_connection": "過去記録との統合（1-2文）",
  "memory_reinterpretation": "記憶の再解釈（1-2文、なければ空）",
  "full_memo": "内省メモ全文（200-400字、日記の素材となる）"
}""",
            user_message=(
                f"Day {day}の行動まとめ:\n{action_summary}\n\n"
                f"現在のムード: V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}\n\n"
                f"記憶:\n{self._build_memory_context()}\n\n"
                f"自伝的エピソード:\n{self._build_episodes_context()}"
            ),
            max_tokens=1500,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return IntrospectionMemo(**{k: data.get(k, "") for k in [
            "self_perception", "past_connection", "memory_reinterpretation", "full_memo"
        ]})
    
    # ─── 日記生成 ──────────────────────────────────────────────
    async def _generate_diary(self, day: int, events: list[EventPackage], introspection: IntrospectionMemo) -> DiaryEntry:
        """日記生成（v10 §4.8）"""
        voice = ""
        if self.package.macro_profile and self.package.macro_profile.voice_fingerprint:
            vf = self.package.macro_profile.voice_fingerprint
            voice = (
                f"一人称: {vf.first_person}\n"
                f"口癖: {', '.join(vf.speech_patterns)}\n"
                f"文末表現: {', '.join(vf.sentence_endings)}\n"
                f"漢字/ひらがな: {vf.kanji_hiragana_tendency}\n"
                f"避ける語彙: {', '.join(vf.avoided_words)}"
            )
        
        event_summaries = "\n".join([
            f"- [{ep.event_id}] {ep.integration_output.final_action[:100]}... → {ep.scene_narration.aftermath[:60]}..."
            for ep in events
        ])
        
        result = await call_llm(
            tier="sonnet",
            system_prompt=f"""あなたはキャラクター本人として日記を書くエージェントです。

【言語的指紋（厳守）】
{voice}

【日記のルール】
- 一人称視点で、そのキャラクターらしい文体で書くこと
- 避ける語彙は絶対に使わないこと（「成長」「気づき」「学び」等のAI臭い語彙）
- 全ての出来事を書く必要はない。主観的に重要だと感じたことだけを書く
- 省略は自然に行う（日記に全てを書く人間はいない）
- 内省メモの内容を日記に反映するが、そのまま引用はしない
- 300-600字程度

【出力形式】JSON
{{"diary_content": "日記本文"}}""",
            user_message=(
                f"Day {day}の出来事:\n{event_summaries}\n\n"
                f"内省メモ:\n{introspection.full_memo}\n\n"
                f"現在のムード: V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}\n\n"
                f"記憶コンテキスト:\n{self._build_memory_context()}"
            ),
            max_tokens=2000,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        
        entry = DiaryEntry(
            day=day,
            content=data.get("diary_content", ""),
            mood_at_writing=self.current_mood.model_copy(),
        )
        
        return entry
    
    # ─── key memory抽出 ───────────────────────────────────────
    async def _extract_key_memory(self, day: int, diary: DiaryEntry) -> KeyMemory:
        """key memory抽出（v10 §5.1）"""
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたはkey memory抽出エージェントです。
日記から「本当に重要だった瞬間」を1つだけ抽出し、300字以内で要約してください。

出力形式: JSON
{"key_memory": "300字以内の要約"}""",
            user_message=f"Day {day}の日記:\n{diary.content}",
            max_tokens=500,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return KeyMemory(
            day=day,
            content=data.get("key_memory", diary.content[:300]),
            mood_at_extraction=self.current_mood.model_dump(),
        )
    
    # ─── 記憶圧縮 ──────────────────────────────────────────────
    def _compress_memories(self, day: int, diary: DiaryEntry):
        """段階圧縮方式（v10 §5.2）"""
        # 新しい日の記録を追加
        self.memory_db.normal_area.append(ShortTermMemoryNormal(
            day=day,
            stage="current",
            summary=diary.content,
            char_count=len(diary.content),
        ))
        
        # 段階をシフト
        for mem in self.memory_db.normal_area:
            if mem.day < day:
                diff = day - mem.day
                if diff == 1:
                    mem.stage = "one_day_ago"
                elif diff == 2:
                    mem.stage = "two_days_ago"
                    mem.summary = mem.summary[:len(mem.summary) * 2 // 3]
                elif diff >= 3:
                    mem.stage = "three_plus_days_ago"
                    mem.summary = mem.summary[:200]
    
    # ─── メインループ ──────────────────────────────────────────
    async def run(self, days: int = 7) -> list[DayProcessingState]:
        """日次ループを実行"""
        await self._notify(f"日次ループ開始: {days}日間")
        
        for day in range(1, days + 1):
            await self._notify(f"=== Day {day} 開始 ===")
            if self.ws:
                await self.ws.send_progress("daily_loop", (day - 1) / days, f"Day {day} 処理中")
            
            events = self._get_day_events(day)
            await self._notify(f"Day {day}: {len(events)}件のイベント")
            
            day_state = DayProcessingState(day=day)
            self.action_buffer = []  # 日次リセット
            
            # イベントループ
            for i, event in enumerate(events):
                await self._notify(f"  イベント {i+1}/{len(events)}: {event.content[:50]}...")
                
                # Perceiver
                perceiver = await self._perceiver(event)
                
                # RIM並列処理
                impulsive, reflective = await asyncio.gather(
                    self._impulsive(event, perceiver),
                    self._reflective(event, perceiver),
                )
                
                # 統合
                integration = await self._integration(event, impulsive, reflective)
                
                # 情景描写
                scene = await self._scene_narration(event, integration)
                
                # 価値観違反チェック
                violation = await self._values_violation(integration)
                
                # ムード更新
                self._update_mood(integration, violation)
                
                # 行動バッファに追加
                self.action_buffer.append(f"[{event.time_slot}] {integration.final_action[:100]}")
                
                # イベントパッケージ
                event_pkg = EventPackage(
                    event_id=event.id,
                    event_content=event.content,
                    perceiver_output=perceiver,
                    impulsive_output=impulsive,
                    reflective_output=reflective,
                    integration_output=integration,
                    scene_narration=scene,
                    values_violation=violation,
                    mood_after=self.current_mood.model_copy(),
                )
                day_state.events_processed.append(event_pkg)
            
            # 内省フェーズ
            await self._notify(f"Day {day}: 内省フェーズ")
            introspection = await self._introspection(day, day_state.events_processed)
            day_state.introspection = introspection
            
            # 日記生成
            await self._notify(f"Day {day}: 日記生成")
            diary = await self._generate_diary(day, day_state.events_processed, introspection)
            day_state.diary = diary
            
            # 日記をストリーミング
            if self.ws:
                await self.ws.send_diary_entry(day, diary.content)
            
            # key memory抽出
            key_mem = await self._extract_key_memory(day, diary)
            day_state.key_memory = key_mem
            self.memory_db.key_memories.append(key_mem)
            
            # 記憶圧縮
            self._compress_memories(day, diary)
            
            # ムード情報
            day_state.daily_mood = self.current_mood.model_copy()
            
            self.day_results.append(day_state)
            await self._notify(f"=== Day {day} 完了 ===", "complete")
        
        await self._notify(f"全{days}日分の日記生成完了！", "complete")
        return self.day_results
