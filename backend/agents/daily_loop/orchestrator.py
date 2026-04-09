"""
日次ループオーケストレータ（v10 §4 完全準拠）

外層ループ: Day 1 → Day 7
内層ループ: 各日のイベント4-6個を順次処理
各イベント処理:
  §4.4 パラメータ動的活性化
  §4.3 Perceiver
  §4.6 Step 1 Impulsive Agent  } RIM並列
  §4.6 Step 2 Reflective Agent }
  §4.6b 裏方出力検証
  §4.6 Step 3 統合エージェント（protagonist_plan対応）
  §4.6 Step 4 情景描写・後日譚
  §4.6c 価値観違反チェック
  §4.6d イベントパッケージ完成
  ムード更新（イベント単位）
1日の終わり:
  §4.7 内省フェーズ
  §4.8 日記生成
  §4.9.1 日記Self-Critic
  §4.9.2 ムード更新（Peak-End Rule）
  §4.9.3 key memory抽出 + 記憶圧縮
  §4.9.4 翌日予定追加（Stage 1 + Stage 2）
  §4.9.5 DB更新 + ムードcarry-over
"""

import json
import asyncio
import logging
import math
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
    DiaryEntry, ActivationLog,
)
from backend.tools.llm_api import call_llm
from backend.agents.daily_loop.activation import DynamicActivationAgent
from backend.agents.daily_loop.verification import OutputVerificationAgent
from backend.agents.daily_loop.next_day_planning import NextDayPlanningAgent
from backend.agents.daily_loop.diary_critic import DiarySelfCritic

logger = logging.getLogger(__name__)


class DailyLoopOrchestrator:
    """Day 1-7 日次ループオーケストレータ（v10 §4 完全準拠）"""
    
    def __init__(self, package: CharacterPackage, ws_manager=None):
        self.package = package
        self.ws = ws_manager
        
        # 状態
        self.current_mood = MoodState()
        self.memory_db = ShortTermMemoryDB()
        self.day_results: list[DayProcessingState] = []
        self.action_buffer: list[str] = []
        
        # サブエージェント初期化
        self.activation_agent = None
        if self.package.micro_parameters:
            self.activation_agent = DynamicActivationAgent(
                self.package.micro_parameters, ws_manager
            )
        
        self.verification_agent = OutputVerificationAgent(ws_manager)
        self.next_day_agent = NextDayPlanningAgent(ws_manager)
        
        self.diary_critic = None
        if (self.package.macro_profile and 
            self.package.macro_profile.voice_fingerprint):
            self.diary_critic = DiarySelfCritic(
                self.package.macro_profile.voice_fingerprint, ws_manager
            )
    
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
    
    def _build_voice_context(self) -> str:
        """言語的指紋のコンテキスト"""
        if self.package.macro_profile and self.package.macro_profile.voice_fingerprint:
            vf = self.package.macro_profile.voice_fingerprint
            return (
                f"一人称: {vf.first_person}\n"
                f"口癖: {', '.join(vf.speech_patterns)}\n"
                f"文末表現: {', '.join(vf.sentence_endings)}\n"
                f"漢字/ひらがな: {vf.kanji_hiragana_tendency}\n"
                f"避ける語彙: {', '.join(vf.avoided_words)}"
            )
        return ""
    
    # ─── §4.4 パラメータ動的活性化 ─────────────────────────────
    async def _activate_params(self, event: Event) -> ActivationLog:
        """動的活性化（§3.5, §4.4）"""
        if self.activation_agent:
            return await self.activation_agent.activate(event.content, self.current_mood)
        return ActivationLog()
    
    # ─── §4.3 Perceiver ────────────────────────────────────────
    async def _perceiver(self, event: Event, activation: ActivationLog) -> PerceiverOutput:
        """Perceiver: 現象的記述 + 反射感情 + 自動注意（v10 §4.3）"""
        # 動的活性化されたパラメータのみを使用
        activated_context = ""
        if self.activation_agent:
            activated_context = self.activation_agent.get_activated_params_text(activation)
        
        # イベントメタデータ
        known_str = "既知（事前に知っている予定）" if event.known_to_protagonist else "未知（予想外の出来事）"
        source_str = f"source: {event.source}" if event.source else ""
        
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたはこのキャラクターの「裏方の知覚エージェント（Perceiver）」です。
キャラ本人には見えない気質・性格パラメータを読み取り、
それに基づいて「今このキャラが知覚した内容」を生成してください。

【出力する3要素のみ】
1. 現象的記述（五感を使った描写、4-6文）
2. 反射的感情反応（身体感覚レベルの情動、2-3文）
3. 自動的注意配分（何に目が行き何が視界から消えたか、2-3文）

【出してはいけないもの】
- 価値判断（「自分が悪い」「上司はひどい」）
- 原因帰属（「なぜそうなったか」の分析）
- 行動意思決定（「どうすべきか」）
- 自己特性の言語化（「自分は怒りっぽい」）
- パラメータへの直接言及（「HA高」「感情パラメータ#5が発火」等）

【出力形式】JSON:
{
  "phenomenal_description": "五感を使った現象的記述（4-6文）",
  "reflexive_emotion": "反射的に浮かぶ感情（身体感覚レベル、2-3文）",
  "automatic_attention": "自動的に注意が向く点（2-3文）"
}""",
            user_message=(
                f"【活性化された気質・性格パラメータ】\n{activated_context}\n\n"
                f"【マクロ層】\n{self._build_macro_context()[:400]}\n\n"
                f"【現在ムード】V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}\n\n"
                f"【今日の行動履歴】\n{self._build_action_buffer()}\n\n"
                f"【イベント】\n{event.content}\n"
                f"（時間帯: {event.time_slot} | {known_str} {source_str} | 予想外度: {event.expectedness}）"
            ),
            max_tokens=1200,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return PerceiverOutput(**{k: data.get(k, "") for k in ["phenomenal_description", "reflexive_emotion", "automatic_attention"]})
    
    # ─── §4.6 Step 1: Impulsive Agent ────────────────────────
    async def _impulsive(self, event: Event, perceiver: PerceiverOutput, activation: ActivationLog) -> ImpulsiveOutput:
        """Impulsive Agent: 気質・性格層への反射反応（v10 §4.6 Step 1）"""
        activated_context = ""
        if self.activation_agent:
            activated_context = self.activation_agent.get_activated_params_text(activation)
        
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは主人公AIのImpulsive Agent（衝動系エージェント）です。
活性化された気質・性格パラメータを参照し、このイベントに対する衝動的な反応を生成してください。
これは「考える前の反応」です。理性的な判断はReflective Agentの仕事です。

【出力形式】JSON:
{
  "impulse_reaction": "衝動的な反応（「思わず○○したくなった」形式、2-3文）",
  "bodily_sensation": "身体感覚（胃がきゅっとする、手に汗が、等、1-2文）",
  "action_tendency": "行動傾向（「○○しそうになる」形式、1-2文）"
}

【禁止】パラメータ名・ID・学術用語の直接言及""",
            user_message=(
                f"【活性化パラメータ】\n{activated_context}\n\n"
                f"【知覚output】\n{json.dumps(perceiver.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"【イベント】{event.content}"
            ),
            max_tokens=800,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return ImpulsiveOutput(**{k: data.get(k, "") for k in ["impulse_reaction", "bodily_sensation", "action_tendency"]})
    
    # ─── §4.6 Step 2: Reflective Agent ──────────────────────
    async def _reflective(self, event: Event, perceiver: PerceiverOutput, activation: ActivationLog) -> ReflectiveOutput:
        """理性ブランチ: 規範層アクセス + 内面分析（v10 §4.6 Step 2）"""
        # 隠蔽原則: 規範層のみアクセス、気質・性格層アクセス不可
        normative_context = ""
        if self.activation_agent:
            normative_context = self.activation_agent.get_activated_normative_text(activation)
        
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは主人公AIの理性ブランチ（Reflective Agent）です。
規範層（価値観、理想自己、義務自己）を参照し、このイベントに対する濃密な内面分析レポートを作成してください。

【重要】あなたは気質・性格パラメータにアクセスできません。
価値観と過去の記憶のみを根拠に分析してください。

主務は「濃密な内面分析レポート」であり、示唆と予測を明示的に含めてください。

【出力形式】JSON:
{
  "inner_analysis": "濃密な内面分析レポート（5-8文。何を考え、何を連想し、どう判断するかを記述）",
  "value_connections": "価値観・知識・過去経験との接続（3-4文）",
  "suggestion": "この状況でどうすべきかの示唆（1-2文）",
  "prediction": "理性ルートで行動した場合の予測（1-2文）"
}""",
            user_message=(
                f"【規範層（活性化済み）】\n{normative_context}\n\n"
                f"【過去の記憶】\n{self._build_memory_context()}\n\n"
                f"【自伝的エピソード】\n{self._build_episodes_context()[:600]}\n\n"
                f"【知覚output】\n{json.dumps(perceiver.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"【イベント】{event.content}\n"
                f"（known: {event.known_to_protagonist} | source: {event.source}）"
            ),
            max_tokens=1500,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return ReflectiveOutput(**{k: data.get(k, "") for k in ["inner_analysis", "value_connections", "suggestion", "prediction"]})
    
    # ─── §4.6 Step 3: 統合エージェント ─────────────────────
    async def _integration(self, event: Event, impulsive: ImpulsiveOutput, reflective: ReflectiveOutput) -> IntegrationOutput:
        """統合エージェント: 2ルート予測 + Higgins評価 + 行動決定（v10 §4.6 Step 3）"""
        normative_context = ""
        if self.package.micro_parameters:
            normative_context = f"理想自己: {self.package.micro_parameters.ideal_self}\n義務自己: {self.package.micro_parameters.ought_self}"
        
        # protagonist_plan 対応（§4.2, §4.6 Step 3）
        protagonist_plan_note = ""
        if event.source == "protagonist_plan":
            protagonist_plan_note = (
                "\n\n【重要: protagonist_plan】\n"
                "このイベントは前日あなた（主人公）が日記の中で「やりたい」と計画したものです。\n"
                "実際にやるかやらないか、どのようにやるかは、今のあなたの気分・状況・優先順位で判断してください。\n"
                "計画を放棄することも、変形することも自由です。\n"
            )
        
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
                f"{normative_context}{protagonist_plan_note}\n\n"
                f"【衝動反応】\n{json.dumps(impulsive.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"【理性分析】\n{json.dumps(reflective.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                f"【イベント】{event.content}"
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
    
    # ─── §4.6 Step 4: 情景描写 ─────────────────────────────
    async def _scene_narration(self, event: Event, integration: IntegrationOutput) -> SceneNarration:
        """情景描写 + 後日譚（v10 §4.6 Step 4）"""
        known_str = "既知イベント" if event.known_to_protagonist else "未知イベント（予想外）"
        
        result = await call_llm(
            tier="gemma",
            system_prompt="""あなたは情景描写の執筆者です。
行動決定に基づいて、その場面の濃密な情景描写と、直後の後日譚を書いてください。

【出力形式】JSON:
{
  "scene_description": "濃密な情景描写（5-8文、五感を含む、その場の空気感・色彩・音・匂い）",
  "aftermath": "直後の後日譚（2-4文、行動の結果として何が起きたか、周囲の反応）"
}""",
            user_message=(
                f"【イベント】{event.content}\n"
                f"（{known_str} | 予想外度: {event.expectedness}）\n\n"
                f"【行動決定】{integration.final_action}\n\n"
                f"【気持ち変化】{integration.emotion_change}"
            ),
            max_tokens=1000,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return SceneNarration(**{k: data.get(k, "") for k in ["scene_description", "aftermath"]})
    
    # ─── §4.6c: 価値観違反チェック ──────────────────────────
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
  "guilt_emotion": "罪悪感の感情記述（なければ空）",
  "violation_type": "schwartz/mft/ideal/ought/none",
  "brief_reflection": "簡易内省メモ（違反時のみ、1-2文）"
}""",
            user_message=(
                f"【価値観】\n{values_context}\n\n"
                f"【行動決定】{integration.final_action}\n\n"
                f"【Higgins Ideal gap】{integration.higgins_ideal_gap}\n"
                f"【Higgins Ought gap】{integration.higgins_ought_gap}"
            ),
            max_tokens=500,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return ValuesViolationResult(**{k: data.get(k, v) for k, v in [
            ("violation_detected", False), ("violation_content", ""), ("guilt_emotion", ""),
            ("violation_type", ""), ("brief_reflection", ""),
        ]})
    
    # ─── ムード更新（イベント単位、§4.5）─────────────────────
    def _update_mood_per_event(self, integration: IntegrationOutput, violation: ValuesViolationResult):
        """PADムード更新（イベント単位、v10 §4.5）"""
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
    
    # ─── §4.9.2 ムード更新（Peak-End Rule、日次）──────────
    def _update_mood_daily(self, day_state: DayProcessingState):
        """Peak-End Rule による日次集約ムード（§4.9.2）"""
        if not day_state.events_processed:
            return
        
        # Peak の検出（最もValenceが極端だったイベント）
        peak_v = 0.0
        peak_a = 0.0
        peak_d = 0.0
        max_abs_v = 0.0
        
        for ep in day_state.events_processed:
            v = ep.mood_after.valence
            if abs(v) > max_abs_v:
                max_abs_v = abs(v)
                peak_v = v
                peak_a = ep.mood_after.arousal
                peak_d = ep.mood_after.dominance
        
        # End（最後のイベントのムード）
        end = day_state.events_processed[-1].mood_after
        
        # Peak-End 加重平均（Peak 60%, End 40%）
        self.current_mood.valence = peak_v * 0.6 + end.valence * 0.4
        self.current_mood.arousal = peak_a * 0.6 + end.arousal * 0.4
        self.current_mood.dominance = peak_d * 0.6 + end.dominance * 0.4
        
        # クリップ
        self.current_mood.valence = max(-5, min(5, self.current_mood.valence))
        self.current_mood.arousal = max(-5, min(5, self.current_mood.arousal))
        self.current_mood.dominance = max(-5, min(5, self.current_mood.dominance))
    
    # ─── §4.9.5 ムードcarry-over ────────────────────────────
    def _mood_carry_over(self):
        """ムードcarry-over処理（§4.9.5）"""
        decay = self.package.micro_parameters.decay_lambda if self.package.micro_parameters else {"V": 0.15, "A": 0.2, "D": 0.1}
        threshold = 0.3
        
        # 減衰適用
        self.current_mood.valence *= (1 - decay.get("V", 0.15))
        self.current_mood.arousal *= (1 - decay.get("A", 0.2))
        self.current_mood.dominance *= (1 - decay.get("D", 0.1))
        
        # 閾値以下ならリセット
        if abs(self.current_mood.valence) < threshold:
            self.current_mood.valence = 0.0
        if abs(self.current_mood.arousal) < threshold:
            self.current_mood.arousal = 0.0
        if abs(self.current_mood.dominance) < threshold:
            self.current_mood.dominance = 0.0
    
    # ─── 内省フェーズ（§4.7）─────────────────────────────────
    async def _introspection(self, day: int, events_processed: list[EventPackage]) -> IntrospectionMemo:
        """内省フェーズ: 3工程（v10 §4.7）"""
        action_summary = "\n".join([f"- {ep.integration_output.final_action[:80]}..." for ep in events_processed])
        
        # 活性化ログの要約（内省で参照可能）
        activation_summary = ""
        for ep in events_processed:
            if ep.activation_log and ep.activation_log.activation_reasoning:
                activation_summary += f"- [{ep.event_id}] {ep.activation_log.activation_reasoning[:60]}...\n"
        
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
  "self_perception": "自己推測（3-4文。「今日の私は〇〇な行動をとった。これは…」形式）",
  "past_connection": "過去記録との統合（2-3文。接続点がなければその旨記述）",
  "memory_reinterpretation": "記憶の再解釈（2-3文。なければ空）",
  "full_memo": "内省メモ全文（200-400字。日記の素材となる。上記3工程の統合）"
}""",
            user_message=(
                f"Day {day}の行動まとめ:\n{action_summary}\n\n"
                f"活性化されたパラメータの傾向:\n{activation_summary}\n\n"
                f"現在のムード: V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}\n\n"
                f"記憶:\n{self._build_memory_context()}\n\n"
                f"自伝的エピソード:\n{self._build_episodes_context()[:600]}"
            ),
            max_tokens=1500,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return IntrospectionMemo(**{k: data.get(k, "") for k in [
            "self_perception", "past_connection", "memory_reinterpretation", "full_memo"
        ]})
    
    # ─── §4.8 日記生成 ─────────────────────────────────────────
    async def _generate_diary(self, day: int, events: list[EventPackage], introspection: IntrospectionMemo) -> DiaryEntry:
        """日記生成（v10 §4.8）"""
        voice = self._build_voice_context()
        
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
        
        return DiaryEntry(
            day=day,
            content=data.get("diary_content", ""),
            mood_at_writing=self.current_mood.model_copy(),
        )
    
    # ─── key memory抽出（§4.9.3.1）────────────────────────────
    async def _extract_key_memory(self, day: int, diary: DiaryEntry) -> KeyMemory:
        """key memory抽出（v10 §4.9.3.1）"""
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
    
    # ─── 記憶圧縮（§4.9.3.2）───────────────────────────────
    async def _compress_memories(self, day: int, diary: DiaryEntry):
        """段階圧縮方式（v10 §4.9.3.2）— LLMによる意味的要約"""
        # 新しい日の記録を追加
        self.memory_db.normal_area.append(ShortTermMemoryNormal(
            day=day,
            stage="current",
            summary=diary.content,
            char_count=len(diary.content),
        ))
        
        # 段階をシフト + 圧縮
        for mem in self.memory_db.normal_area:
            if mem.day < day:
                diff = day - mem.day
                if diff == 1:
                    mem.stage = "one_day_ago"
                elif diff == 2:
                    mem.stage = "two_days_ago"
                    # LLMで2/3に圧縮
                    if mem.char_count > 200:
                        compressed = await call_llm(
                            tier="gemma",
                            system_prompt="以下のテキストを、重要な出来事を保持しつつ元の2/3程度に圧縮してください。JSON: {\"compressed\": \"...\"}",
                            user_message=mem.summary,
                            max_tokens=500,
                            json_mode=True,
                        )
                        d = compressed["content"] if isinstance(compressed["content"], dict) else {}
                        mem.summary = d.get("compressed", mem.summary[:len(mem.summary) * 2 // 3])
                        mem.char_count = len(mem.summary)
                elif diff >= 3:
                    mem.stage = "three_plus_days_ago"
                    if mem.char_count > 200:
                        mem.summary = mem.summary[:200]
                        mem.char_count = 200
        
        # 日記をストアに追加
        self.memory_db.diary_store.append(diary.content)
    
    # ─── メインループ ──────────────────────────────────────────
    async def run(self, days: int = 7) -> list[DayProcessingState]:
        """日次ループを実行（v10 §4 完全準拠）"""
        await self._notify(f"日次ループ開始: {days}日間")
        
        for day in range(1, days + 1):
            await self._notify(f"=== Day {day} 開始 ===")
            if self.ws:
                await self.ws.send_progress("daily_loop", (day - 1) / days, f"Day {day} 処理中")
            
            events = self._get_day_events(day)
            await self._notify(f"Day {day}: {len(events)}件のイベント")
            
            day_state = DayProcessingState(day=day)
            self.action_buffer = []  # 日次リセット
            
            # ─── 内層イベントループ ─────────────────────────
            for i, event in enumerate(events):
                await self._notify(f"  イベント {i+1}/{len(events)}: {event.content[:50]}...")
                
                # §4.4 動的活性化
                activation = await self._activate_params(event)
                
                # §4.3 Perceiver
                perceiver = await self._perceiver(event, activation)
                
                # §4.6 Step 1+2: RIM並列処理
                impulsive, reflective = await asyncio.gather(
                    self._impulsive(event, perceiver, activation),
                    self._reflective(event, perceiver, activation),
                )
                
                # §4.6b 裏方出力検証
                verification = await self.verification_agent.verify(perceiver, impulsive)
                if not verification["passed"]:
                    if verification["corrected_perceiver"]:
                        perceiver = verification["corrected_perceiver"]
                    if verification["corrected_impulsive"]:
                        impulsive = verification["corrected_impulsive"]
                
                # §4.6 Step 3: 統合
                integration = await self._integration(event, impulsive, reflective)
                
                # §4.6 Step 4: 情景描写
                scene = await self._scene_narration(event, integration)
                
                # §4.6c: 価値観違反チェック
                violation = await self._values_violation(integration)
                
                # ムード更新（イベント単位）
                self._update_mood_per_event(integration, violation)
                
                # 行動バッファに追加
                self.action_buffer.append(f"[{event.time_slot}] {integration.final_action[:100]}")
                
                # §4.6d: イベントパッケージ完成
                event_pkg = EventPackage(
                    event_id=event.id,
                    event_content=event.content,
                    event_metadata={
                        "known_to_protagonist": event.known_to_protagonist,
                        "source": event.source,
                        "expectedness": event.expectedness,
                    },
                    activation_log=activation,
                    perceiver_output=perceiver,
                    impulsive_output=impulsive,
                    reflective_output=reflective,
                    integration_output=integration,
                    scene_narration=scene,
                    values_violation=violation,
                    mood_before=self.current_mood.model_copy(),
                    mood_after=self.current_mood.model_copy(),
                )
                day_state.events_processed.append(event_pkg)
            
            # ─── 外層（1日の終わり）────────────────────────
            
            # §4.7 内省フェーズ
            await self._notify(f"Day {day}: 内省フェーズ")
            introspection = await self._introspection(day, day_state.events_processed)
            day_state.introspection = introspection
            
            # §4.8 日記生成
            await self._notify(f"Day {day}: 日記生成")
            diary = await self._generate_diary(day, day_state.events_processed, introspection)
            
            # §4.9.1 日記Self-Critic
            if self.diary_critic:
                critique = await self.diary_critic.critique(diary, self.current_mood)
                if not critique["passed"] and critique["corrected_diary"]:
                    diary.content = critique["corrected_diary"]
            
            day_state.diary = diary
            
            # 日記をストリーミング
            if self.ws:
                await self.ws.send_diary_entry(day, diary.content)
            
            # §4.9.2 ムード更新（Peak-End Rule）
            self._update_mood_daily(day_state)
            
            # §4.9.3.1 key memory抽出
            key_mem = await self._extract_key_memory(day, diary)
            day_state.key_memory = key_mem
            self.memory_db.key_memories.append(key_mem)
            
            # §4.9.3.2 記憶圧縮
            await self._compress_memories(day, diary)
            
            # §4.9.4 翌日予定追加（Day 7以外）
            if day < days:
                await self._notify(f"Day {day}: 翌日予定の計画")
                plans = await self.next_day_agent.stage1_protagonist_plan(
                    day=day,
                    diary=diary,
                    introspection=introspection,
                    current_mood=self.current_mood,
                    macro_context=self._build_macro_context()[:500],
                    voice_context=self._build_voice_context(),
                )
                
                if plans and self.package.weekly_events_store:
                    new_event = await self.next_day_agent.stage2_consistency_check(
                        plans=plans,
                        next_day=day + 1,
                        events_store=self.package.weekly_events_store,
                    )
                    if new_event:
                        self.package.weekly_events_store.events.append(new_event)
                        day_state.next_day_plans = [p.model_dump() for p in plans]
            
            # §4.9.5 ムードcarry-over
            day_state.daily_mood = self.current_mood.model_copy()
            self._mood_carry_over()
            
            self.day_results.append(day_state)
            await self._notify(f"=== Day {day} 完了 ===", "complete")
        
        await self._notify(f"全{days}日分の日記生成完了！", "complete")
        return self.day_results
