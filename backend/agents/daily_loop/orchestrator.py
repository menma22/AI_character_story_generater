import json
import asyncio
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.config import AppConfig
from backend.models.character import CharacterPackage, MicroParameters
from backend.models.story import Event, DiaryEntry, Mood
from backend.agents.daily_loop.models import (
    ActivationLog, ImpulsiveOutput, ReflectiveOutput, IntegrationOutput,
    ValuesViolationResult, IntrospectionMemo, KeyMemory,
    EventPackage, DayProcessingState, ConsistencyCheckResult, SceneNarration
)
from backend.agents.daily_loop.checkers import (
    ProfileChecker, TemperamentChecker, PersonalityChecker, ValuesChecker
)
from backend.agents.daily_loop.sub_agents import (
    DynamicActivationAgent, OutputVerificationAgent, NextDayPlanningAgent,
    DiarySelfCritic, ThirdPartyReviewer, LinguisticExpressionValidator
)
from backend.tools.llm_api import call_llm, call_llm_agentic, call_llm_agentic_gemini, AgentTool
from backend.storage.memory_db import MemoryDB, ShortTermMemoryNormal
from backend.storage.memory_store import MemoryStore
from backend.storage.mood_store import MoodStore
from backend.storage.daily_log_store import DailyLogStore
from backend.storage.key_memory_store import KeyMemoryStore
from backend.utils.token_tracker import token_tracker

logger = logging.getLogger(__name__)

def wrap_context(title: str, content: str, role: str = "general") -> str:
    \"\"\"コンテキストをタグで囲むユーティリティ\"\"\"
    return f"<{title}>\n{content}\n</{title}>"

class DailyLoopOrchestrator:
    \"\"\"日次ループ（v10）のマスター・オーケストレーター\"\"\"

    def __init__(
        self,
        package: CharacterPackage,
        ws: Any = None,
        api_keys: Optional[dict] = None
    ):
        self.package = package
        self.ws = ws
        self.api_keys = api_keys or {}
        
        # 内部状態
        self.current_mood = Mood(valence=0.0, arousal=0.0, dominance=0.0)
        self.day_results: list[DayProcessingState] = []
        self.action_buffer: list[str] = [] # 1日の行動履歴（簡易）
        
        # ストレージ
        self._cname = package.macro_profile.basic_info.name if package.macro_profile else "default"
        self.memory_db = MemoryDB()
        self.memory_store = MemoryStore(self._cname)
        self.mood_store = MoodStore(self._cname)
        self.daily_log_store = DailyLogStore(self._cname)
        self.key_memory_store = KeyMemoryStore(self._cname)
        
        # サブエージェント初期化
        self.activation_agent = DynamicActivationAgent(package, api_keys=self.api_keys)
        self.verification_agent = OutputVerificationAgent(api_keys=self.api_keys)
        self.next_day_agent = NextDayPlanningAgent(package, api_keys=self.api_keys)
        self.diary_critic = DiarySelfCritic(package, api_keys=self.api_keys)
        self.third_party_reviewer = ThirdPartyReviewer(package, api_keys=self.api_keys)
        
        # 4つの個別チェッカー
        self.profile_checker = ProfileChecker(package, api_keys=self.api_keys)
        self.temperament_checker = TemperamentChecker(package, api_keys=self.api_keys)
        self.personality_checker = PersonalityChecker(package, api_keys=self.api_keys)
        self.values_checker = ValuesChecker(package, api_keys=self.api_keys)

        # 状態復旧
        self._load_state()

    def _load_state(self):
        \"\"\"最新の状態（メモリ、ムード）をストレージから読み込む\"\"\"
        latest_day = self.memory_store.get_latest_day()
        if latest_day > 0:
            db = self.memory_store.load(latest_day)
            if db:
                self.memory_db = db
            
            mood_state = self.mood_store.load(latest_day)
            if mood_state:
                # carry_over適用済みのものを現在のムードとする
                self.current_mood = Mood(**mood_state["mood_carry_over"])
        else:
            # 初回：MicroParametersから初期ムードを設定
            if self.package.micro_parameters:
                p = self.package.micro_parameters
                self.current_mood = Mood(valence=p.initial_v, arousal=p.initial_a, dominance=p.initial_d)

    async def _notify(self, message: str, status: str = "processing"):
        \"\"\"フロントエンドへ通知\"\"\"
        if self.ws:
            await self.ws.send_log("DailyLoop", message, status)
        logger.info(f"[DailyLoop] {message}")

    # ─── §4.4 動的活性化（Dynamic Activation）──────────────────
    async def _activate_params(self, event: Event) -> ActivationLog:
        \"\"\"動的活性化エージェントを呼び出し、今回発火するパラメータを決定\"\"\"
        if not self.activation_agent:
            return ActivationLog()
        
        # 過去1日の行動履歴、現在のムード、コンテキストを渡す
        history = "\n".join(self.action_buffer[-5:])
        return await self.activation_agent.activate(event, self.current_mood, history)

    # ─── コンテキスト構築 ──────────────────────────────────────
    def _build_macro_context(self) -> str:
        if not self.package.macro_profile: return ""
        p = self.package.macro_profile
        lines = [
            f"名前: {p.basic_info.name}",
            f"年齢: {p.basic_info.age}",
            f"性別: {p.basic_info.gender}",
            f"職業: {p.basic_info.occupation}",
            f"外見: {p.basic_info.appearance}",
            f"生い立ち: {p.life_history.biography[:300]}...",
            f"現在の状況: {p.life_history.current_status[:200]}...",
        ]
        return "\n".join(lines)

    def _build_world_context(self) -> str:
        if not self.package.world_setting: return ""
        w = self.package.world_setting
        return f"{w.world_name}\n概要: {w.world_description[:300]}\nルール: {w.special_rules[:200]}"

    def _build_supporting_characters_context(self) -> str:
        if not self.package.supporting_characters: return ""
        lines = []
        for char in self.package.supporting_characters:
            lines.append(f"- {char.name} ({char.role}): {char.relationship_to_protagonist}")
        return "\n".join(lines)

    def _build_memory_context(self) -> str:
        \"\"\"短期記憶（デイリーログ + key memory）を構築（忘却ロジック適用後）\"\"\"
        # DailyLogStore から最新の要約を取得
        logs = []
        for entry in self.daily_log_store.get_all_latest():
            age = (self.memory_store.get_latest_day() + 1) - entry.day
            label = "当日" if age == 0 else f"{age}日前"
            logs.append(f"【{label}のログ】\n{entry.content}")
        
        # KeyMemoryStore から重要な記憶を取得
        kms = self.key_memory_store.get_all()
        key_mems = []
        for km in kms:
            key_mems.append(f"【Day {km.day}の重要記憶】\n{km.content}")
        
        return "\n\n".join(logs + key_mems)

    def _build_action_buffer(self) -> str:
        if not self.action_buffer: return "（本日はまだ行動していません）"
        return "\n".join(self.action_buffer)

    def _build_episodes_context(self) -> str:
        if not self.package.autobiographical_episodes: return ""
        lines = []
        for ep in self.package.autobiographical_episodes:
            lines.append(f"- {ep.title}: {ep.content[:150]}")
        return "\n".join(lines)

    def _build_voice_context(self) -> str:
        if not self.package.linguistic_expression: return ""
        le = self.package.linguistic_expression
        lines = [
            f"一人称: {le.first_person}",
            f"口癖: {', '.join(le.signature_phrases)}",
            f"口調: {le.sentence_endings}",
            f"使わない言葉: {', '.join(le.prohibited_words)}",
            f"日記トーン: {le.diary_tone}",
            f"比喩頻度: {le.metaphor_frequency}",
        ]
        return "\n".join(lines)

    def _build_past_diary_context(self) -> str:
        # 互換性のため memory_db から取得
        if not self.memory_db.diary_store: return ""
        # 直近3日分
        diaries = self.memory_db.diary_store[-3:]
        lines = []
        for i, content in enumerate(diaries):
            lines.append(f"【過去の日記 {i+1}】\n{content[:200]}...")
        return "\n\n".join(lines)

    async def _run_consistency_checks(self, output_text: str, activation: ActivationLog, phase_label: str) -> list[ConsistencyCheckResult]:
        \"\"\"4つの個別チェックAIを並列実行して整合性を検証する\"\"\"
        macro_json = self.package.macro_profile.model_dump_json() if self.package.macro_profile else "{}"
        activated_temperament_text = self.activation_agent.get_activated_params_text(activation) if self.activation_agent else ""
        activated_personality_text = "" # 拡張用
        values_context = json.dumps(self.package.micro_parameters.schwartz_values, ensure_ascii=False) if self.package.micro_parameters else ""

        try:
            results = await asyncio.gather(
                self.profile_checker.check(output_text, macro_json),
                self.temperament_checker.check(output_text, activated_temperament_text),
                self.personality_checker.check(output_text, activated_personality_text),
                self.values_checker.check(output_text, values_context),
                return_exceptions=True,
            )
            # エラーをフィルタ
            valid_results = []
            for r in results:
                if isinstance(r, Exception):
                    logger.warning(f"[チェッカー] チェック失敗: {r}")
                else:
                    valid_results.append(r)
            return valid_results
        except Exception as e:
            logger.error(f"[チェッカー] 並列チェック全体エラー: {e}")
            return []

    # ─── 感情強度判定 ─────────────────────────────────────────
    async def _evaluate_emotion_intensity(self, impulsive: ImpulsiveOutput) -> EmotionIntensityResult:
        \"\"\"Impulsive Agent出力後に感情強度を判定。
        highの場合、理性ブランチ（Reflective Agent）をバイパスする。
        \"\"\"
        result = await call_llm(
            tier="gemini",
            system_prompt=\"\"\"あなたは感情強度の判定エージェントです。
衝動系エージェント（Impulsive Agent）の出力を見て、感情の強度を判定してください。

【判定基準】
- high: 身体反応が激しい（手が震える、涙が溢れる、息ができない等）、
  行動傾向が圧倒的（逃げ出したい、殴りたい、抱きしめたい等の切迫感）。
  理性的な判断が困難な状態。
- medium: 身体反応はあるが制御可能、行動傾向はあるが抑制できるレベル。
- low: 穏やかな反応、大きな身体反応なし。

出力形式: JSON
{"intensity": "high/medium/low", "reasoning": "判定理由（1文）"}\"\"\",
            user_message=(
                f"【衝動系エージェントの出力】\n{impulsive.raw_text}\n\n"
                f"【現在ムード】V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}"
            ),
            json_mode=True,
            api_keys=self.api_keys,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return EmotionIntensityResult(
            intensity=data.get("intensity", "medium"),
            reasoning=data.get("reasoning", ""),
        )

    # ─── §4.3+§4.6 Step 1: 衝動系エージェント（Perceiver + Impulsive 統合）────────
    async def _impulsive(self, event: Event, activation: ActivationLog) -> ImpulsiveOutput:
        \"\"\"衝動系エージェント: 知覚フィルター + 衝動的反応を統合（v10 §4.3 + §4.6 Step 1）\"\"\"
        activated_context = ""
        if self.activation_agent:
            activated_context = self.activation_agent.get_activated_params_text(activation)

        known_str = "既知（事前に知っている予定）" if event.known_to_protagonist else "未知（予想外の出来事）"
        source_str = f"source: {event.source}" if event.source else ""

        result = await call_llm(
            tier="gemini",
            system_prompt=\"\"\"あなたはこのキャラクターの「衝動的感覚を司るエージェント」です。
キャラ本人にとっては無意識下にある気質・性格パラメータを読み取り、
それに基づいて「今このキャラがイベントを受け取り、衝動的、感情的に生まれた内面的な心の動きを詳細に分析したレポート」を生成してください。
あなたの出力は、理性側の分析レポートと共に、キャラクター本人の意識下に渡されます。
これは「考える前の反応」です。理性的な判断はReflective Agentの仕事です。

以下のセクションは必ず、Markdownのセクションヘッダー（##）で区切って出力してください。

## 現象的記述
（五感を使った描写、4-6文。視覚・聴覚・触覚・嗅覚を含む具体的な知覚描写）

## 反射的感情反応
（身体感覚レベルの情動、2-3文。「胸がざわつく」「手のひらに汗がにじむ」「怒りがこみ上げる」等）

## 自動的注意配分
（何に目が行き何が視界から消えたか、2-3文）

## 生じた衝動
（直面した出来事を受けて、キャラクターが反射的に起こした内面的反応。
「思わず○○したくなった」「怒りがこみ上げ、殴りたくなった」など、理性が介入する前の生の反応をより詳細に描き出す。2-3文）

## 行動傾向
（approach/avoid/freeze のいずれかの方向性で「○○しそうになる」形式、1-2文）

【出してはいけないもの】
- 価値判断（「自分が悪い」「上司はひどい」）
- 原因帰属（「なぜそうなったか」の分析）
- 自己特性の言語化（「自分は怒りっぽい」）
- パラメータへの直接言及（「HA高」「感情パラメータ#5が発火」等）
- パラメータ名・ID・学術用語の直接言及\"\"\",
            user_message=(
                f"{wrap_context('マクロプロフィール', self._build_macro_context(), 'impulsive')}\n\n"
                f"{wrap_context('世界設定', self._build_world_context())}\n\n"
                f"{wrap_context('周囲の人物', self._build_supporting_characters_context())}\n\n"
                f"{wrap_context('活性化された気質・性格パラメータ', activated_context)}\n\n"
                f"{wrap_context('現在ムード', f'V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}')}\n\n"
                f"{wrap_context('今日の行動履歴', self._build_action_buffer())}\n\n"
                f"{wrap_context('過去の記憶', self._build_memory_context())}\n\n"
                f"{wrap_context('自伝的エピソード', self._build_episodes_context()[:600])}\n\n"
                f"{wrap_context('イベント', f'{event.content}\n（時間帯: {event.time_slot} | {known_str} {source_str} | 予想外度: {event.expectedness}）')}"
            ),
            json_mode=False,
            api_keys=self.api_keys,
        )
        raw_text = result["content"] if isinstance(result["content"], str) else str(result["content"])
        return ImpulsiveOutput(raw_text=raw_text)

    # ─── §4.6 Step 2: Reflective Agent ──────────────────────
    async def _reflective(self, event: Event, impulsive: ImpulsiveOutput, activation: ActivationLog) -> ReflectiveOutput:
        \"\"\"理性ブランチ: 規範層アクセス + 内面分析（v10 §4.6 Step 2）\"\"\"
        # 隠蔽原則: 規範層のみアクセス、気質・性格層アクセス不可
        normative_context = ""
        if self.activation_agent:
            normative_context = self.activation_agent.get_activated_normative_text(activation)

        known_str = "既知（事前に知っている予定）" if event.known_to_protagonist else "未知（予想外の出来事）"

        result = await call_llm(
            tier="gemini",
            system_prompt=\"\"\"あなたは主人公AIの理性ブランチ（Reflective Agent）です。
規範層（価値観、理想自己、義務自己）を参照し、このイベントに対する濃密な内面分析レポートを作成してください。

【重要】あなたは気質・性格パラメータにアクセスできません。
価値観と過去の記憶のみを根拠に分析してください。

主務は「濃密な内面分析レポート」であり、示唆と予測を明示的に含めてください。

以下の4セクションを、Markdownのセクションヘッダー（##）で区切って出力してください。

## 内面分析
（5-8文の濃密な内面分析レポート。「なぜそう感じるのか」「この状況は自分にとって何を意味するか」「価値観・知識・過去経験との接続」を記述）

## 価値観との接続
（3-4文。動的活性化された価値観・理想自己・義務自己との関連を明示的に記述）

## 示唆
（1-2文。この状況でどうすべきかの理性的な示唆）

## 予測
（1-2文。理性ルートで行動した場合の予測）\"\"\",
            user_message=(
                f"{wrap_context('マクロプロフィール', self._build_macro_context(), 'reflective')}\n\n"
                f"{wrap_context('世界設定', self._build_world_context())}\n\n"
                f"{wrap_context('周囲の人物', self._build_supporting_characters_context())}\n\n"
                f"{wrap_context('規範層', normative_context, 'reflective')}\n\n"
                f"{wrap_context('過去の記憶', self._build_memory_context())}\n\n"
                f"{wrap_context('自伝的エピソード', self._build_episodes_context()[:600])}\n\n"
                f"{wrap_context('衝動ブランチの報告', impulsive.raw_text)}\n\n"
                f"{wrap_context('イベント', f'{event.content}\n（{known_str} | source: {event.source}）')}"
            ),
            json_mode=False,
            api_keys=self.api_keys,
        )
        raw_text = result["content"] if isinstance(result["content"], str) else str(result["content"])
        return ReflectiveOutput(raw_text=raw_text)

    # ─── §4.6 Step 3+4: 出来事周辺情報統合エージェント (Agentic Loop) ────────
    async def _integration(self, event: Event, impulsive: ImpulsiveOutput, reflective: ReflectiveOutput, checker_feedback: str = "") -> IntegrationOutput:
        \"\"\"出来事周辺情報統合エージェント: 行動決定 + 周辺情報 + 情景描写 + ストーリー統合（Tool-calling 自律ループ）

        行動決定エージェントを拡張し、出来事の周辺情報や行動後の結果、
        主人公の動きと感情をストーリーとしてまとめる役割を統合。

        Args:
            checker_feedback: 前回のチェッカー不合格時のフィードバック（再生成時のみ）
        \"\"\"
        from backend.tools.llm_api import AgentTool, call_llm_agentic

        normative_context = ""
        values_context = ""
        if self.package.micro_parameters:
            normative_context = f"理想自己: {self.package.micro_parameters.ideal_self}\n義務自己: {self.package.micro_parameters.ought_self}"
            values_context = json.dumps(self.package.micro_parameters.schwartz_values, ensure_ascii=False)

        protagonist_plan_note = ""
        if event.source == "protagonist_plan":
            protagonist_plan_note = (
                "\\n\\n【重要: protagonist_plan】\\n"
                "このイベントは前日あなた（主人公）が日記の中で「やりたい」と計画したものです。\\n"
                "実際にやるかやらないかは、今の気分・状況・優先順位で自律的に判断してください。\\n"
            )

        # 感情強度が高い場合の理性バイパス判定
        reflective_bypassed = not reflective.raw_text

        final_decision_data = {}

        async def simulate_action_consequences(action_idea: str = None) -> dict:
            \"\"\"行動案をテストし、価値観違反や将来の予測をシミュレーションして事前に確認する\"\"\"
            if not action_idea:
                return {"status": "FAILED", "message": "ERROR: action_idea引数が欠落しています。"}
            await self._notify(f"行動案のシミュレーション中: {action_idea[:30]}...")

            res = await call_llm(
                tier=self.profile.worker_tier,
                system_prompt=\"\"\"あなたは主人公の行動シミュレーターです。この行動をとった場合の良い点・悪い点、および自身の持つ価値観への違反度（罪悪感を生むか）をフィードバックしてください。JSON形式: {"pros": "...", "cons": "...", "values_violation_risk": "high/medium/low", "feedback": "..."}\"\"\",
                user_message=f"【自己の価値観】\\n{values_context}\\n\\n【検討中の行動案】\\n{action_idea}",
                json_mode=True,
                api_keys=self.api_keys,
            )
            data = res["content"] if isinstance(res["content"], dict) else {"feedback": str(res["content"])}
            return data

        async def submit_final_decision(decision_package: dict = None) -> dict:
            \"\"\"最終的な行動決定と周辺情報・情景描写を統合して提出し、ミッションを完了する\"\"\"
            if not decision_package:
                return {"status": "FAILED", "message": "ERROR: decision_package引数が欠落しています。"}
            nonlocal final_decision_data
            final_decision_data = decision_package
            await self._notify("出来事周辺情報統合エージェント: 最終決定・ストーリー提出完了。", "complete")
            return {"status": "SUCCESS", "message": "Decision and story submitted successfully. Thank you."}

        # submit_final_decision用の拡張スキーマ
        decision_properties = {
            "impulse_route_good": {"type": "string", "description": "衝動ルートの良いこと予測"},
            "impulse_route_bad": {"type": "string", "description": "衝動ルートの悪いこと予測"},
            "reflective_route_good": {"type": "string", "description": "理性ルートの良いこと予測（感情強度高で省略時はN/A）"},
            "reflective_route_bad": {"type": "string", "description": "理性ルートの悪いこと予測（感情強度高で省略時はN/A）"},
            "higgins_ideal_gap": {"type": "string", "description": "Ideal不一致（落胆・がっかり系）"},
            "higgins_ought_gap": {"type": "string", "description": "Ought不一致（不安・罪悪感系）"},
            "final_action": {"type": "string", "description": "最終的な行動決定（具体的に、3-5文）"},
            "emotion_change": {"type": "string", "description": "気持ちの変化の短文記述"},
            "surrounding_context": {"type": "string", "description": "出来事の周辺情報・状況描写（3-5文。場所・時間・周囲の人々・雰囲気など）"},
            "action_consequences": {"type": "string", "description": "行動後の結果・影響（2-3文。周囲の反応、場の変化）"},
            "scene_description": {"type": "string", "description": "濃密な情景描写（5-8文。五感を含む文学的描写）"},
            "aftermath": {"type": "string", "description": "後日譚（2-4文。行動がもたらした小さな波紋）"},
            "protagonist_movement": {"type": "string", "description": "主人公の動き・感情状態（2-3文。身体の動き、表情、内面の変化）"},
            "story_segment": {"type": "string", "description": "統合ストーリーセグメント（上記全体を物語として自然に統合した文章、8-15文）"},
        }

        required_fields = [
            "impulse_route_good", "impulse_route_bad",
            "higgins_ideal_gap", "higgins_ought_gap",
            "final_action", "emotion_change",
            "surrounding_context", "scene_description", "aftermath",
            "protagonist_movement", "story_segment",
        ]
        if not reflective_bypassed:
            required_fields.extend(["reflective_route_good", "reflective_route_bad"])

        tools = [
            AgentTool(
                name="simulate_action_consequences",
                description="検討している行動案（action_idea）の長所・短所・価値観違反リスクを事前にシミュレーションし、客観的なフィードバックを得ます。必要に応じて何度でも呼び出して様々な案をテストしてください。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "action_idea": {"type": "string", "description": "検討中の具体的な行動案"}
                    },
                    "required": ["action_idea"]
                },
                handler=simulate_action_consequences
            ),
            AgentTool(
                name="submit_final_decision",
                description="行動決定に加え、出来事の周辺情報・情景描写・行動後の結果・主人公の動き・統合ストーリーを全て含む完全なパッケージを提出します。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "decision_package": {
                            "type": "object",
                            "properties": decision_properties,
                            "required": required_fields,
                        }
                    },
                    "required": ["decision_package"]
                },
                handler=submit_final_decision
            )
        ]

        # 理性バイパス時の追加指示
        bypass_note = ""
        if reflective_bypassed:
            bypass_note = "\\n\\n【重要: 感情強度が高いため理性ブランチの報告はありません】\\n衝動ブランチのみの情報で判断してください。reflective_route_good/badは 'N/A' としてください。\\n"

        known_str = "既知（事前に知っている予定）" if event.known_to_protagonist else "未知（予想外の出来事）"
        system_prompt = f\"\"\"あなたは主人公AIの「出来事周辺情報統合エージェント」です。
衝動ルートと理性ルートの意見を統合し、最終的な行動を決定するとともに、
この出来事に対して生じた事象やその前後の情報、主人公の動き、感情などをストーリーとしてまとめてください。
衝動的な無意識的な反応に関するレポートが【衝動ブランチの報告】で、理性的な意識的な反応に関するレポートが【理性ブランチの報告】であり、その二つを融合させます。状況によって、衝動的な反応を優先したりしてください。例えば、怒りが高まっているときは、衝動的な反応を優先します。
また、必ず、衝動적反応、理性的反応それぞれに従ったと仮定したときに起こりうる良い出来事と悪い出来事をそれぞれ2つ以上上げ、それも加味してストーリーを構築してください。

【あなたの役割】
1. 行動や選択など決定: 衝動と理性の2つのルートを踏まえて主人公のとる行動や選択・スタンスを決める
2. 周辺情報統合: 出来事の背景、周囲の状況、登場人物の反応を描写
3. 情景描写: 五感を含む文学的な場面描写を執筆
4. 結果と後日譚: 行動後に何が起こったか、小さな波紋を描く
5. ストーリー統合: 上記全てを1つの物語セグメントとして統合

【Higgins自己不一致理論(事象に当てはまればこの理論も使ってみてください。)】
- Ideal不一致（理想と現実のギャップ）→ 落胆・がっかり系の感情
- Ought不一致（義務と現実のギャップ）→ 不安・罪悪感系の感情

【エージェンティック行動指針】
1. 主人公AIに対して起こった出来事に対する主人公の反応や選択、行動を生成し、それに伴って生じた出来事などの周辺情報を提供されたマクロプロフィールなどのコンテキスト全てを加味して生成してください。エージェンティックに分析し、計画的に生成してください。
   行動決定 + 周辺情報 + 情景描写 + 後日譚 + 主人公の動き + 統合ストーリーを
   全て含む完全なパッケージを `submit_final_decision` で提出してください。{bypass_note}\"\"\"

        # 衝動・理性ブランチの出力をそのまま渡す
        impulsive_text = impulsive.raw_text
        reflective_text = reflective.raw_text if reflective.raw_text else "（感情強度が高いため省略）"

        # チェッカーフィードバックがある場合（再生成時）、user_messageに追加
        feedback_section = ""
        if checker_feedback:
            feedback_section = (
                f"\\n\\n【重要: 前回の出力に対するチェッカーフィードバック（必ず修正してください）】\\n"
                f"{checker_feedback}\\n"
                f"上記の不整合を解消した出力を生成してください。\\n"
            )

        user_message = (
            f"{wrap_context('マクロプロフィール', self._build_macro_context(), 'integration')}\\n\\n"
            f"{wrap_context('世界設定', self._build_world_context())}\\n\\n"
            f"{wrap_context('周囲の人物', self._build_supporting_characters_context())}\\n\\n"
            f"{wrap_context('規範層', f'{normative_context}{protagonist_plan_note}')}\\n\\n"
            f"{wrap_context('過去の記憶', self._build_memory_context())}\\n\\n"
            f"{wrap_context('自伝的エピソード', self._build_episodes_context()[:600])}\\n\\n"
            f"{wrap_context('衝動ブランチの報告', impulsive_text)}\\n\\n"
            f"{wrap_context('理性ブランチの報告', reflective_text)}\\n\\n"
            f"{wrap_context('イベント', f'{event.content}\\n（時間帯: {event.time_slot} | {known_str} | 予想外度: {event.expectedness}）')}"
            f"{feedback_section}"
        )

        retry_label = "（再生成）" if checker_feedback else ""
        await self._notify(f"出来事周辺情報統合エージェントをエージェンティックモードで起動{retry_label}...")

        from backend.tools.llm_api import call_llm_agentic_gemini

        if self.profile.worker_tier in ("opus", "sonnet"):
            try:
                await call_llm_agentic(
                    tier=self.profile.worker_tier,
                    system_prompt=system_prompt,
                    user_message=user_message,
                    tools=tools,
                    max_iterations=6,
                    api_keys=self.api_keys,
                )
            except Exception as e:
                logger.warning(f"[DailyLoop] Integration: Claude ({self.profile.worker_tier}) agentic failed: {e}. Falling back to Gemini.")
                try:
                    await call_llm_agentic_gemini(
                        system_prompt=system_prompt,
                        user_message=user_message,
                        tools=tools,
                        max_iterations=6,
                        api_keys=self.api_keys,
                    )
                except Exception as e2:
                    logger.error(f"[DailyLoop] Integration: Gemini fallback also failed: {e2}. Using default decision.")
        else:
            try:
                await call_llm_agentic_gemini(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    tools=tools,
                    max_iterations=6,
                    api_keys=self.api_keys,
                )
            except Exception as e:
                logger.error(f"[DailyLoop] Integration: Gemini agentic failed: {e}. Using default decision.")

        if not final_decision_data:
            # Fallback
            final_decision_data = {
                "impulse_route_good": "N/A", "impulse_route_bad": "N/A",
                "reflective_route_good": "N/A", "reflective_route_bad": "N/A",
                "higgins_ideal_gap": "N/A", "higgins_ought_gap": "N/A",
                "final_action": "（判断に迷い、何もできなかった）",
                "emotion_change": "混乱",
                "surrounding_context": "", "action_consequences": "",
                "scene_description": "", "aftermath": "",
                "protagonist_movement": "", "story_segment": "",
            }

        all_fields = [
            "impulse_route_good", "impulse_route_bad",
            "reflective_route_good", "reflective_route_bad",
            "higgins_ideal_gap", "higgins_ought_gap",
            "final_action", "emotion_change",
            "surrounding_context", "action_consequences",
            "scene_description", "aftermath",
            "protagonist_movement", "story_segment",
        ]
        return IntegrationOutput(**{k: final_decision_data.get(k, "") for k in all_fields})
    
    # NOTE: _scene_narration() は出来事周辺情報統合エージェント (_integration) に統合済み

    # ─── §4.6c: 価値観違反チェック ──────────────────────────
    async def _values_violation(self, integration: IntegrationOutput) -> ValuesViolationResult:
        \"\"\"価値観違反チェック（v10 §4.6c）\"\"\"
        values_context = ""
        if self.package.micro_parameters:
            values_context = json.dumps(self.package.micro_parameters.schwartz_values, ensure_ascii=False)
        
        result = await call_llm(
            tier="gemini",
            system_prompt=\"\"\"あなたは価値観違反チェッカーです。
行動決定が主人公の価値観に違反していないかチェックしてください。

出力形式: JSON
{
  "violation_detected": true/false,
  "violation_content": "違反内容（なければ空）",
  "guilt_emotion": "罪悪感の感情記述（なければ空）",
  "violation_type": "schwartz/mft/ideal/ought/none",
  "brief_reflection": "簡易内省メモ（違反時のみ、1-2文）"
}\"\"\",
            user_message=(
                f\"【行動決定】{integration.final_action}\\n\\n\"
                f\"【Higgins Ideal gap】{integration.higgins_ideal_gap}\\n\"
                f\"【Higgins Ought gap】{integration.higgins_ought_gap}\"
            ),
            json_mode=True,
            api_keys=self.api_keys,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return ValuesViolationResult(**{k: data.get(k, v) for k, v in [
            ("violation_detected", False), ("violation_content", ""), ("guilt_emotion", ""),
            ("violation_type", ""), ("brief_reflection", ""),
        ]})
    
    # ─── ムード更新（イベント単位、§4.5）─────────────────────
    def _update_mood_per_event(self, integration: IntegrationOutput, violation: ValuesViolationResult):
        \"\"\"PADムード更新（イベント単位、v10 §4.5）\"\"\"
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
        \"\"\"Peak-End Rule による日次集約ムード（§4.9.2）\"\"\"
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
        \"\"\"ムードcarry-over処理（§4.9.5）\"\"\"
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
        \"\"\"内省フェーズ: 3工程（v10 §4.7）\"\"\"
        action_summary = "\\n".join([f"- {ep.integration_output.final_action[:80]}..." for ep in events_processed])
        
        # 活性化ログの要約（内省で参照可能）
        activation_summary = ""
        for ep in events_processed:
            if ep.activation_log and ep.activation_log.activation_reasoning:
                activation_summary += f"- [{ep.event_id}] {ep.activation_log.activation_reasoning[:60]}...\\n"
        
        result = await call_llm(
            tier=self.profile.worker_tier,
            system_prompt=\"\"\"あなたは主人公AIの内省エージェントです。
今日1日の出来事を振り返り、キャラクターの主観で内省メモを生成してください。

【3工程】
1. 自己推測（Bem Self-Perception Theory）: 自分の行動パターンから自分はどういう人間かを推測する
   ※ 気質パラメータそのものにはアクセスできない。行動からの推測のみ。
2. 過去記録との統合: 記憶にある過去の出来事と今日の出来事に接続点があるか
3. 薄れた記憶の再解釈: 過去の出来事を今日の経験を通じて新たに意味づける

以下の4セクションを、Markdownのセクションヘッダー（##）で区切って出力してください。

## 自己推測
## 過去記録との統合
## 記憶の再解釈
## 内省メモ全文\"\"\",
            user_message=(
                f\"{wrap_context('マクロプロフィール', self._build_macro_context(), 'introspection')}\\n\\n\"
                f\"{wrap_context('世界設定', self._build_world_context())}\\n\\n\"
                f\"{wrap_context('今日の行動履歴', f'Day {day}の行動まとめ:\\n{action_summary}')}\\n\\n\"
                f\"{wrap_context('過去の記憶', self._build_memory_context())}\\n\\n\"
                f\"{wrap_context('自伝的エピソード', self._build_episodes_context()[:600])}\"
            ),
            json_mode=False,
            api_keys=self.api_keys,
        )
        raw_text = result["content"] if isinstance(result["content"], str) else str(result["content"])
        return IntrospectionMemo(raw_text=raw_text)
    
    # ─── §4.8 日記生成 (Agentic Loop) ─────────────────────────
    async def _generate_diary(self, day: int, events: list[EventPackage], introspection: IntrospectionMemo, next_day_plans: list[dict] | None = None, checker_feedback: str = "") -> DiaryEntry:
        \"\"\"日記生成（Tool-calling 自律ループ、v10 §4.8）\"\"\"
        from backend.tools.llm_api import AgentTool, call_llm_agentic
        
        voice = self._build_voice_context()
        event_summaries = "\\n".join([
            f"- [{ep.event_id}] {ep.integration_output.final_action[:100]}... → {ep.scene_narration.aftermath[:60]}..."
            for ep in events
        ])
        
        final_diary_content = ""
        check_passed = False
        last_checked_draft = ""
        third_party_passed = False
        last_third_party_draft = ""

        async def check_diary_rules(draft_diary_text: str = None) -> dict:
            nonlocal check_passed, last_checked_draft
            if not draft_diary_text: return {"status": "FAILED", "message": "ERROR: draft_diary_text引数が欠落しています。"}
            await self._notify("日記ドラフトの言語規則チェック中...")
            temp_diary = DiaryEntry(day=day, content=draft_diary_text, mood_at_writing=self.current_mood)
            result = await self.diary_critic.critique(temp_diary, self.current_mood)
            if result["passed"]:
                check_passed = True
                last_checked_draft = draft_diary_text
                return {"status": "SUCCESS", "message": "基本チェック通過。"}
            else:
                check_passed = False
                return {"status": "FAILED", "issues_found": result["issues"]}

        async def validate_linguistic_expression(draft_diary_text: str = None) -> dict:
            if not draft_diary_text: return {"status": "FAILED", "message": "ERROR: draft_diary_text引数が欠落しています。"}
            validator = LinguisticExpressionValidator(self.package.linguistic_expression, api_keys=self.api_keys)
            temp_diary = DiaryEntry(day=day, content=draft_diary_text, mood_at_writing=self.current_mood)
            result = await validator.validate(temp_diary, self.current_mood)
            return {"status": "SUCCESS" if result["passed"] else "FAILED", "feedback": result.get("feedback", "")}

        async def third_party_review(draft_diary_text: str = None) -> dict:
            nonlocal third_party_passed, last_third_party_draft
            if not draft_diary_text: return {"status": "FAILED", "message": "ERROR: draft_diary_text引数が欠落しています。"}
            temp_diary = DiaryEntry(day=day, content=draft_diary_text, mood_at_writing=self.current_mood)
            result = await self.third_party_reviewer.review(temp_diary, self.current_mood, event_summaries)
            if result["passed"]:
                third_party_passed = True
                last_third_party_draft = draft_diary_text
                return {"status": "SUCCESS", "message": "第三者視点チェックOK。"}
            else:
                third_party_passed = False
                return {"status": "FAILED", "issues_found": result["issues"]}

        async def submit_final_diary(final_diary_text: str = None) -> dict:
            nonlocal final_diary_content
            if not final_diary_text: return {"status": "FAILED", "message": "ERROR: final_diary_text引数が欠落しています。"}
            final_diary_content = final_diary_text
            await self._notify("最終日記が完成・提出されました。", "complete")
            return {"status": "SUCCESS", "message": "Diary submitted successfully."}

        tools = [
            AgentTool(name="check_diary_rules", handler=check_diary_rules, description="口癖・禁止語彙・口調チェック"),
            AgentTool(name="validate_linguistic_expression", handler=validate_linguistic_expression, description="詳細言語表現バリデーション"),
            AgentTool(name="third_party_review", handler=third_party_review, description="第三者視点レビュー"),
            AgentTool(name="submit_final_diary", handler=submit_final_diary, description="最終日記提出"),
        ]
        
        system_prompt = f\"\"\"あなたはキャラクター本人として日記を書くエージェントです。\\n{voice}\"\"\"
        user_message = f\"今日の出来事:\\n{event_summaries}\\n\\n内省:\\n{introspection.raw_text}\"

        await self._notify(f"日記生成エージェントを自律モードで起動...")
        
        try:
            await call_llm_agentic(
                tier=self.profile.worker_tier,
                system_prompt=system_prompt,
                user_message=user_message,
                tools=tools,
                max_iterations=10,
                api_keys=self.api_keys,
            )
        except Exception as e:
            logger.error(f"[DailyLoop] Diary Agentic failed: {e}")

        if not final_diary_content:
            final_diary_content = "(本日は何も書く気になれなかった)"
            
        return DiaryEntry(day=day, content=final_diary_content, mood_at_writing=self.current_mood.model_copy())
    
    # ─── key memory抽出 ──────────────────────────────────────────
    async def _extract_key_memory(self, day: int, diary: DiaryEntry) -> KeyMemory:
        result = await call_llm(
            tier="gemini",
            system_prompt=\"\"\"あなたはkey memory抽出エージェントです。日記から重要な瞬間を1つ抽出し要約してください。\"\"\",
            user_message=f"Day {day}の日記:\\n{diary.content}",
            json_mode=True,
            api_keys=self.api_keys,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return KeyMemory(day=day, content=data.get("key_memory", diary.content[:300]), mood_at_extraction=self.current_mood.model_dump())
    
    # ─── デイリーログ要約 ─────────────────────────────────────────
    async def _create_daily_log_and_summarize(self, day: int, events: list[EventPackage], introspection: IntrospectionMemo):
        full_log = "\\n".join([f"[{ep.event_id}] {ep.integration_output.final_action}" for ep in events])
        self.daily_log_store.save_full_log(day, full_log)
        summary_res = await call_llm(
            tier="gemini",
            system_prompt=\"\"\"要約エージェント。以下のテキストを簡潔に要約してください。\"\"\",
            user_message=full_log,
            json_mode=True,
            api_keys=self.api_keys,
        )
        summary = summary_res["content"].get("summary", full_log[:200]) if isinstance(summary_res["content"], dict) else full_log[:200]
        self.daily_log_store.save_summary(day, summary)

    # ─── メインループ ──────────────────────────────────────────
    async def run(self, days: int = 7) -> list[DayProcessingState]:
        start_day = self.memory_store.get_latest_day() + 1
        await self._notify(f"日次ループ開始: Day {start_day}〜{days}")

        for day in range(start_day, days + 1):
            await self._notify(f"=== Day {day} 開始 ===")
            events = self.package.weekly_events_store.get_day_events(day) if self.package.weekly_events_store else []
            day_state = DayProcessingState(day=day)
            
            for event in events:
                activation = await self._activate_params(event)
                impulsive = await self._impulsive(event, activation)
                intensity = await self._evaluate_emotion_intensity(impulsive)
                
                if intensity.intensity == "high":
                    reflective = ReflectiveOutput()
                else:
                    reflective = await self._reflective(event, impulsive, activation)
                
                integration = await self._integration(event, impulsive, reflective)
                violation = await self._values_violation(integration)
                self._update_mood_per_event(integration, violation)
                
                ep = EventPackage(
                    event_id=event.id, event_content=event.content, event_metadata={},
                    activation_log=activation, impulsive_output=impulsive, reflective_output=reflective,
                    integration_output=integration, scene_narration=SceneNarration(scene_description=integration.scene_description, aftermath=integration.aftermath),
                    values_violation=violation, mood_before=Mood(), mood_after=self.current_mood.model_copy()
                )
                day_state.events_processed.append(ep)
                self.action_buffer.append(integration.final_action)

            introspection = await self._introspection(day, day_state.events_processed)
            day_state.introspection = introspection
            
            diary = await self._generate_diary(day, day_state.events_processed, introspection)
            day_state.diary = diary
            
            self._update_mood_daily(day_state)
            key_mem = await self._extract_key_memory(day, diary)
            self.key_memory_store.save(key_mem)
            await self._create_daily_log_and_summarize(day, day_state.events_processed, introspection)
            
            self._mood_carry_over()
            self.memory_store.save(day, self.memory_db)
            self.mood_store.save(day, self.current_mood.model_copy(), self.current_mood.model_copy())
            self.day_results.append(day_state)
            
            if self.ws:
                await self.ws.send_diary_entry(day, diary.content)
            await self._notify(f"=== Day {day} 完了 ===", "complete")
            
        return self.day_results
