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
  §4.6 Step 3+4 出来事周辺情報統合エージェント（行動決定+情景描写+ストーリー統合）
  §4.6c 価値観違反チェック
  §4.6d イベントパッケージ完成
  ムード更新（イベント単位）
1日の終わり:
  §4.7 内省フェーズ
  §4.9.4 翌日予定追加（Stage 1 + Stage 2）★ 日記の前に移動
  §4.8 日記生成（翌日予定を参照可能）
  §4.9.1 日記Self-Critic
  §4.9.2 ムード更新（Peak-End Rule）
  §4.9.3.1 key memory抽出
  §4.9.3.2 デイリーログ保存 & 要約（日別フォルダ管理）
  §4.9.5 DB更新 + ムードcarry-over
"""

import json
import asyncio
import logging
import math
from pathlib import Path
from typing import Optional

from backend.models.character import (
    CharacterPackage, MacroProfile, MicroParameters,
    AutobiographicalEpisodes, WeeklyEventsStore, Event,
)
from backend.models.memory import (
    MoodState, ShortTermMemoryDB, KeyMemory, ShortTermMemoryNormal,
    DayProcessingState, ImpulsiveOutput,
    ReflectiveOutput, IntegrationOutput, SceneNarration,
    ValuesViolationResult, EventPackage, IntrospectionMemo,
    DiaryEntry, ActivationLog, EmotionIntensityResult,
    DailyLogEntry,
)
from backend.tools.llm_api import call_llm, token_tracker
from backend.config import EvaluationProfile, AppConfig
from backend.agents.daily_loop.activation import DynamicActivationAgent
from backend.agents.daily_loop.verification import OutputVerificationAgent
from backend.agents.daily_loop.next_day_planning import NextDayPlanningAgent
from backend.agents.daily_loop.diary_critic import DiarySelfCritic
from backend.agents.daily_loop.third_party_reviewer import ThirdPartyReviewer
from backend.agents.context_descriptions import wrap_context
from backend.agents.daily_loop.checkers import (
    ProfileChecker, TemperamentChecker, PersonalityChecker, ValuesChecker,
)
from backend.agents.daily_loop.linguistic_validator import LinguisticExpressionValidator

logger = logging.getLogger(__name__)


class KeyMemoryStore:
    """key memoryを短期記憶とは別の個別ファイルとして管理（1日1ファイル、7日間フル保持）"""

    def __init__(self, character_name: str):
        safe_name = character_name.replace("/", "_").replace("\\", "_")
        self.dir = AppConfig.STORAGE_DIR / safe_name / "key_memories"
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, km: KeyMemory) -> Path:
        """key memoryを個別JSONファイルとして保存"""
        path = self.dir / f"day_{km.day:02d}.json"
        path.write_text(json.dumps(km.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[KeyMemoryStore] Day {km.day} key memory saved to {path}")
        return path

    def load_all(self) -> list[KeyMemory]:
        """全key memoryをロード（日付順）"""
        memories = []
        for p in sorted(self.dir.glob("day_*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                memories.append(KeyMemory(**data))
            except Exception as e:
                logger.warning(f"[KeyMemoryStore] Failed to load {p}: {e}")
        return memories

    def load_day(self, day: int) -> Optional[KeyMemory]:
        """指定日のkey memoryをロード"""
        path = self.dir / f"day_{day:02d}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return KeyMemory(**data)
            except Exception as e:
                logger.warning(f"[KeyMemoryStore] Failed to load day {day}: {e}")
        return None


class ShortTermMemoryStore:
    """短期記憶DB（normal_area + diary_store）を日単位でファイル永続化。
    各日のスナップショットを保持し、最新ファイル＝現在状態。"""

    def __init__(self, character_name: str):
        safe_name = character_name.replace("/", "_").replace("\\", "_")
        self.dir = AppConfig.STORAGE_DIR / safe_name / "short_term_memory"
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, day: int, memory_db: ShortTermMemoryDB) -> Path:
        """その日の記憶圧縮完了後のスナップショットを保存"""
        path = self.dir / f"day_{day:02d}.json"
        data = {
            "day": day,
            "normal_area": [m.model_dump(mode="json") for m in memory_db.normal_area],
            "diary_store": memory_db.diary_store,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[ShortTermMemoryStore] Day {day} snapshot saved to {path}")
        return path

    def load_latest(self) -> Optional[ShortTermMemoryDB]:
        """最新日のスナップショットをロードして復元"""
        files = sorted(self.dir.glob("day_*.json"))
        if not files:
            return None
        try:
            data = json.loads(files[-1].read_text(encoding="utf-8"))
            db = ShortTermMemoryDB(
                normal_area=[ShortTermMemoryNormal(**m) for m in data.get("normal_area", [])],
                diary_store=data.get("diary_store", []),
            )
            logger.info(f"[ShortTermMemoryStore] Restored from {files[-1].name} ({len(db.normal_area)} entries)")
            return db
        except Exception as e:
            logger.warning(f"[ShortTermMemoryStore] Failed to load latest: {e}")
            return None

    def load_day(self, day: int) -> Optional[ShortTermMemoryDB]:
        """指定日のスナップショットをロード"""
        path = self.dir / f"day_{day:02d}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return ShortTermMemoryDB(
                    normal_area=[ShortTermMemoryNormal(**m) for m in data.get("normal_area", [])],
                    diary_store=data.get("diary_store", []),
                )
            except Exception as e:
                logger.warning(f"[ShortTermMemoryStore] Failed to load day {day}: {e}")
        return None

    def get_latest_day(self) -> int:
        """最新の保存済み日数を返す（0 = まだ保存なし）"""
        files = sorted(self.dir.glob("day_*.json"))
        if not files:
            return 0
        try:
            return int(files[-1].stem.split("_")[1])
        except (IndexError, ValueError):
            return 0


class MoodStateStore:
    """ムード状態（PAD 3次元）を日単位でファイル永続化。
    daily_mood（Peak-End集約）とcarry_over_mood（翌日開始値）の両方を保持。"""

    def __init__(self, character_name: str):
        safe_name = character_name.replace("/", "_").replace("\\", "_")
        self.dir = AppConfig.STORAGE_DIR / safe_name / "mood_states"
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, day: int, daily_mood: MoodState, carry_over_mood: MoodState) -> Path:
        """その日のムード状態を保存"""
        path = self.dir / f"day_{day:02d}.json"
        data = {
            "day": day,
            "daily_mood": daily_mood.model_dump(mode="json"),
            "carry_over_mood": carry_over_mood.model_dump(mode="json"),
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[MoodStateStore] Day {day} mood saved to {path}")
        return path

    def load_latest_carry_over(self) -> Optional[MoodState]:
        """最新日のcarry_over_mood（翌日開始ムード）をロード"""
        files = sorted(self.dir.glob("day_*.json"))
        if not files:
            return None
        try:
            data = json.loads(files[-1].read_text(encoding="utf-8"))
            mood = MoodState(**data["carry_over_mood"])
            logger.info(f"[MoodStateStore] Restored carry-over mood from {files[-1].name}: V={mood.valence:.1f} A={mood.arousal:.1f} D={mood.dominance:.1f}")
            return mood
        except Exception as e:
            logger.warning(f"[MoodStateStore] Failed to load latest: {e}")
            return None

    def load_day(self, day: int) -> Optional[dict]:
        """指定日のdaily_mood + carry_over_moodをロード"""
        path = self.dir / f"day_{day:02d}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return {
                    "daily_mood": MoodState(**data["daily_mood"]),
                    "carry_over_mood": MoodState(**data["carry_over_mood"]),
                }
            except Exception as e:
                logger.warning(f"[MoodStateStore] Failed to load day {day}: {e}")
        return None

    def get_latest_day(self) -> int:
        """最新の保存済み日数を返す（0 = まだ保存なし）"""
        files = sorted(self.dir.glob("day_*.json"))
        if not files:
            return 0
        try:
            return int(files[-1].stem.split("_")[1])
        except (IndexError, ValueError):
            return 0


class DailyLogStore:
    """デイリーログ（行動ログ）の日別フォルダ管理。

    フォルダ構造:
        daily_logs/day_01/001_full.json    ← 1日の全行動ログ
        daily_logs/day_01/002_summary.json ← 要約（~半分）
        daily_logs/day_01/003_summary.json ← さらに要約

    エージェントに渡す「短期記憶」= 各日の最新IDファイルを全て渡す。
    """

    def __init__(self, character_name: str):
        safe_name = character_name.replace("/", "_").replace("\\", "_")
        self.dir = AppConfig.STORAGE_DIR / safe_name / "daily_logs"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _day_dir(self, day: int) -> Path:
        d = self.dir / f"day_{day:02d}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_full_log(self, day: int, content: str) -> Path:
        """1日の全行動ログを保存（001_full.json）"""
        entry = DailyLogEntry(
            day=day, version=1, content=content,
            char_count=len(content), is_summary=False, created_at_day=day,
        )
        path = self._day_dir(day) / "001_full.json"
        path.write_text(
            json.dumps(entry.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"[DailyLogStore] Day {day} full log saved ({len(content)} chars)")
        return path

    def save_summary(self, day: int, content: str, version: int, created_at_day: int) -> Path:
        """要約版を保存（NNN_summary.json）"""
        entry = DailyLogEntry(
            day=day, version=version, content=content,
            char_count=len(content), is_summary=True, created_at_day=created_at_day,
        )
        path = self._day_dir(day) / f"{version:03d}_summary.json"
        path.write_text(
            json.dumps(entry.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"[DailyLogStore] Day {day} summary v{version} saved ({len(content)} chars)")
        return path

    def get_latest(self, day: int) -> Optional[DailyLogEntry]:
        """最新IDのファイルを読み込み（＝エージェントに渡す短期記憶）"""
        day_dir = self.dir / f"day_{day:02d}"
        if not day_dir.exists():
            return None
        files = sorted(day_dir.glob("*.json"))
        if not files:
            return None
        try:
            data = json.loads(files[-1].read_text(encoding="utf-8"))
            return DailyLogEntry(**data)
        except Exception as e:
            logger.warning(f"[DailyLogStore] Failed to load latest for day {day}: {e}")
            return None

    def get_all_latest(self) -> list[DailyLogEntry]:
        """全日の最新ログを取得（日付順）"""
        entries = []
        day_dirs = sorted(self.dir.glob("day_*"))
        for day_dir in day_dirs:
            if not day_dir.is_dir():
                continue
            files = sorted(day_dir.glob("*.json"))
            if not files:
                continue
            try:
                data = json.loads(files[-1].read_text(encoding="utf-8"))
                entries.append(DailyLogEntry(**data))
            except Exception as e:
                logger.warning(f"[DailyLogStore] Failed to load {day_dir.name}: {e}")
        return entries


class DailyLoopOrchestrator:
    """Day 1-7 日次ループオーケストレータ（v10 §4 完全準拠）"""

    def __init__(self, package: CharacterPackage, profile: EvaluationProfile, ws_manager=None):
        self.package = package
        self.profile = profile
        self.ws = ws_manager

        # キャラ名解決（全Storeで共通使用）
        cname = ""
        if self.package.macro_profile and self.package.macro_profile.basic_info:
            cname = self.package.macro_profile.basic_info.name
        self._cname = cname or "Unknown_Character"

        # 各Store初期化
        self.key_memory_store = KeyMemoryStore(self._cname)
        self.memory_store = ShortTermMemoryStore(self._cname)
        self.mood_store = MoodStateStore(self._cname)
        self.daily_log_store = DailyLogStore(self._cname)

        # 状態: 既存スナップショットがあれば復元、なければ初期値
        restored_mood = self.mood_store.load_latest_carry_over()
        self.current_mood = restored_mood if restored_mood else MoodState()

        restored_memory = self.memory_store.load_latest()
        self.memory_db = restored_memory if restored_memory else ShortTermMemoryDB()

        self.day_results: list[DayProcessingState] = []
        self.action_buffer: list[str] = []

        if restored_mood or restored_memory:
            logger.info(f"[DailyLoop] 既存状態を復元: mood={'restored' if restored_mood else 'fresh'}, memory={'restored' if restored_memory else 'fresh'}")
        
        # サブエージェント初期化
        self.activation_agent = None
        if self.package.micro_parameters:
            self.activation_agent = DynamicActivationAgent(
                self.package.micro_parameters,
                ws_manager,
                tier=self.profile.worker_tier,
                macro_profile=self.package.macro_profile,
                episodes=self.package.autobiographical_episodes,
            )
        
        self.verification_agent = OutputVerificationAgent(ws_manager, tier=self.profile.worker_tier)
        self.next_day_agent = NextDayPlanningAgent(ws_manager, tier=self.profile.worker_tier)
        
        self.diary_critic = None
        # LinguisticExpression を優先、フォールバックで macro_profile.voice_fingerprint
        voice_fp = None
        if (self.package.linguistic_expression and
            self.package.linguistic_expression.speech_characteristics.concrete_features):
            voice_fp = self.package.linguistic_expression.speech_characteristics.concrete_features
        elif (self.package.macro_profile and
              self.package.macro_profile.voice_fingerprint):
            voice_fp = self.package.macro_profile.voice_fingerprint
        if voice_fp:
            self.diary_critic = DiarySelfCritic(
                voice_fp,
                macro_profile=self.package.macro_profile,
                ws_manager=ws_manager,
                tier=self.profile.worker_tier,
            )

        # 第三者視点の検証AI
        self.third_party_reviewer = ThirdPartyReviewer(
            macro_profile=self.package.macro_profile,
            ws_manager=ws_manager,
            tier=self.profile.worker_tier,
        )

        # 4つの個別チェックAI
        self.profile_checker = ProfileChecker(ws_manager, tier="gemini")
        self.temperament_checker = TemperamentChecker(ws_manager, tier="gemini")
        self.personality_checker = PersonalityChecker(ws_manager, tier="gemini")
        self.values_checker = ValuesChecker(ws_manager, tier="gemini")
    
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
        """短期記憶（最重要）: デイリーログ最新版 + key memory を全日分個別に渡す"""
        parts = []
        # key memory（日付順）
        key_mems = {km.day: km for km in self.key_memory_store.load_all()}
        # デイリーログ最新版（日付順）
        daily_logs = {entry.day: entry for entry in self.daily_log_store.get_all_latest()}
        # 全日分を統合（日付でソート）
        all_days = sorted(set(list(key_mems.keys()) + list(daily_logs.keys())))
        for d in all_days:
            if d in key_mems:
                parts.append(f"[Day {d} key memory]: {key_mems[d].content}")
            if d in daily_logs:
                entry = daily_logs[d]
                label = "全文" if not entry.is_summary else f"要約v{entry.version}"
                parts.append(f"[Day {d} デイリーログ（{label}）]: {entry.content}")
        # フォールバック: DailyLogStore未使用時は旧normal_areaを使用
        if not parts:
            for km in self.key_memory_store.load_all():
                parts.append(f"[Day {km.day} key memory]: {km.content}")
            for nm in self.memory_db.normal_area:
                parts.append(f"[Day {nm.day} {nm.stage}]: {nm.summary[:200]}")
        return "\n".join(parts) if parts else "(まだ記憶なし)"

    def _build_past_diary_context(self) -> str:
        """過去の日記を独立DBとして読み込み（参照用）"""
        parts = []
        # diaries/ フォルダから直接読み込み
        diaries_dir = AppConfig.STORAGE_DIR / self._cname.replace("/", "_").replace("\\", "_") / "diaries"
        if diaries_dir.exists():
            for diary_file in sorted(diaries_dir.glob("day_*.md")):
                try:
                    content = diary_file.read_text(encoding="utf-8").strip()
                    day_num = int(diary_file.stem.split("_")[1])
                    parts.append(f"[Day {day_num}の日記]: {content}")
                except Exception:
                    pass
        # フォールバック: diary_storeから
        if not parts and self.memory_db.diary_store:
            for i, diary_text in enumerate(self.memory_db.diary_store, 1):
                parts.append(f"[Day {i}の日記]: {diary_text}")
        return "\n".join(parts) if parts else ""
    
    def _build_action_buffer(self) -> str:
        """行動履歴バッファ"""
        return "\n".join(self.action_buffer[-10:]) if self.action_buffer else "(行動履歴なし)"
    
    def _build_world_context(self) -> str:
        """世界設定コンテキスト"""
        if self.package.weekly_events_store and self.package.weekly_events_store.world_context:
            wc = self.package.weekly_events_store.world_context
            parts = []
            if wc.name:
                parts.append(f"世界名: {wc.name}")
            if wc.description:
                parts.append(f"世界設定: {wc.description}")
            if wc.time_period:
                parts.append(f"時代: {wc.time_period}")
            if wc.genre:
                parts.append(f"ジャンル: {wc.genre}")
            return "\n".join(parts) if parts else "(世界設定なし)"
        return "(世界設定なし)"

    def _build_supporting_characters_context(self) -> str:
        """周囲人物コンテキスト"""
        if self.package.weekly_events_store and self.package.weekly_events_store.supporting_characters:
            lines = []
            for sc in self.package.weekly_events_store.supporting_characters:
                line = f"- {sc.name}（{sc.role}）: {sc.relationship_to_protagonist}"
                if sc.brief_profile:
                    line += f" — {sc.brief_profile}"
                lines.append(line)
            return "\n".join(lines)
        return "(周囲人物情報なし)"

    def _build_voice_context(self) -> str:
        """言語的表現方法のコンテキスト（日記生成プロンプトに注入、すべてのフィールドを網羅）"""
        le = self.package.linguistic_expression
        if le:
            vf = le.speech_characteristics.concrete_features
            parts = [
                f"一人称: {vf.first_person}",
            ]

            # 二人称の使い分け（context-dependent）
            if vf.second_person_by_context:
                spc = vf.second_person_by_context
                second_person_parts = []
                if spc.to_intimate:
                    second_person_parts.append(f"親しい人への二人称: {spc.to_intimate}")
                if spc.to_superior:
                    second_person_parts.append(f"目上への二人称: {spc.to_superior}")
                if spc.to_stranger:
                    second_person_parts.append(f"知らない人への二人称: {spc.to_stranger}")
                if second_person_parts:
                    parts.append("二人称の使い分け:\n  " + "\n  ".join(second_person_parts))

            parts.extend([
                f"口癖: {', '.join(vf.speech_patterns)}",
                f"文末表現: {', '.join(vf.sentence_endings)}",
                f"漢字/ひらがな: {vf.kanji_hiragana_tendency}",
                f"絵文字・記号の使用: {vf.emoji_usage}",
                f"自問形式の頻度: {vf.self_questioning_frequency}",
                f"比喩・反語の頻度: {vf.metaphor_irony_frequency}",
                f"避ける語彙: {', '.join(vf.avoided_words)}",
            ])

            # 抽象的な喋り方の雰囲気
            if le.speech_characteristics.abstract_feel:
                parts.append(f"喋り方の雰囲気: {le.speech_characteristics.abstract_feel}")
            if le.speech_characteristics.conversation_style:
                parts.append(f"会話スタイル: {le.speech_characteristics.conversation_style}")
            if le.speech_characteristics.emotional_expression_tendency:
                parts.append(f"感情表現の傾向: {le.speech_characteristics.emotional_expression_tendency}")

            # 日記の書き方の雰囲気
            da = le.diary_writing_atmosphere
            if da.tone:
                parts.append(f"日記のトーン: {da.tone}")
            if da.structure_tendency:
                parts.append(f"日記の構成傾向: {da.structure_tendency}")
            if da.introspection_depth:
                parts.append(f"内省の深さ: {da.introspection_depth}")
            if da.what_gets_written:
                parts.append(f"書く内容の方針: {da.what_gets_written}")
            if da.what_gets_omitted:
                parts.append(f"省略する傾向: {da.what_gets_omitted}")
            if da.raw_atmosphere_description:
                parts.append(f"日記の空気感: {da.raw_atmosphere_description}")

            return "\n".join(parts)

        # フォールバック: 旧形式（linguistic_expressionがない場合）
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
    
    # ─── 4つの個別チェックAI ──────────────────────────────────
    async def _run_consistency_checks(self, output_text: str, activation: ActivationLog, label: str) -> list:
        """4つのチェッカーを並列実行して整合性を検証する"""
        await self._notify(f"{label}: 4つの個別チェックAIを並列実行中...")

        # コンテキスト構築
        macro_json = self._build_macro_context()[:1500]

        # 活性化パラメータのテキスト取得
        activated_temperament_text = ""
        activated_personality_text = ""
        values_context = ""
        if self.activation_agent:
            activated_temperament_text = self.activation_agent.get_activated_params_text(
                ActivationLog(
                    activated_temperament_ids=activation.activated_temperament_ids,
                    activated_personality_ids=[],
                    activated_cognition_ids=[],
                )
            )
            activated_personality_text = self.activation_agent.get_activated_params_text(
                ActivationLog(
                    activated_temperament_ids=[],
                    activated_personality_ids=activation.activated_personality_ids,
                    activated_cognition_ids=[],
                )
            )
        if self.package.micro_parameters:
            values_parts = []
            if self.package.micro_parameters.schwartz_values:
                values_parts.append(f"Schwartz価値観: {json.dumps(self.package.micro_parameters.schwartz_values, ensure_ascii=False)}")
            if self.package.micro_parameters.ideal_self:
                values_parts.append(f"理想自己: {self.package.micro_parameters.ideal_self}")
            if self.package.micro_parameters.ought_self:
                values_parts.append(f"義務自己: {self.package.micro_parameters.ought_self}")
            values_context = "\n".join(values_parts)

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
        """Impulsive Agent出力後に感情強度を判定。
        highの場合、理性ブランチ（Reflective Agent）をバイパスする。
        """
        result = await call_llm(
            tier="gemini",
            system_prompt="""あなたは感情強度の判定エージェントです。
衝動系エージェント（Impulsive Agent）の出力を見て、感情の強度を判定してください。

【判定基準】
- high: 身体反応が激しい（手が震える、涙が溢れる、息ができない等）、
  行動傾向が圧倒的（逃げ出したい、殴りたい、抱きしめたい等の切迫感）。
  理性的な判断が困難な状態。
- medium: 身体反応はあるが制御可能、行動傾向はあるが抑制できるレベル。
- low: 穏やかな反応、大きな身体反応なし。

出力形式: JSON
{"intensity": "high/medium/low", "reasoning": "判定理由（1文）"}""",
            user_message=(
                f"【衝動系エージェントの出力】\n{impulsive.raw_text}\n\n"
                f"【現在ムード】V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}"
            ),
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return EmotionIntensityResult(
            intensity=data.get("intensity", "medium"),
            reasoning=data.get("reasoning", ""),
        )

    # ─── §4.3+§4.6 Step 1: 衝動系エージェント（Perceiver + Impulsive 統合）────────
    async def _impulsive(self, event: Event, activation: ActivationLog) -> ImpulsiveOutput:
        """衝動系エージェント: 知覚フィルター + 衝動的反応を統合（v10 §4.3 + §4.6 Step 1）"""
        activated_context = ""
        if self.activation_agent:
            activated_context = self.activation_agent.get_activated_params_text(activation)

        known_str = "既知（事前に知っている予定）" if event.known_to_protagonist else "未知（予想外の出来事）"
        source_str = f"source: {event.source}" if event.source else ""

        result = await call_llm(
            tier="gemini",
            system_prompt="""あなたはこのキャラクターの「衝動的感覚を司るエージェント」です。
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
- パラメータ名・ID・学術用語の直接言及""",
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
        )
        raw_text = result["content"] if isinstance(result["content"], str) else str(result["content"])
        return ImpulsiveOutput(raw_text=raw_text)
    
    # ─── §4.6 Step 2: Reflective Agent ──────────────────────
    async def _reflective(self, event: Event, impulsive: ImpulsiveOutput, activation: ActivationLog) -> ReflectiveOutput:
        """理性ブランチ: 規範層アクセス + 内面分析（v10 §4.6 Step 2）"""
        # 隠蔽原則: 規範層のみアクセス、気質・性格層アクセス不可
        normative_context = ""
        if self.activation_agent:
            normative_context = self.activation_agent.get_activated_normative_text(activation)

        known_str = "既知（事前に知っている予定）" if event.known_to_protagonist else "未知（予想外の出来事）"

        result = await call_llm(
            tier="gemini",
            system_prompt="""あなたは主人公AIの理性ブランチ（Reflective Agent）です。
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
（1-2文。理性ルートで行動した場合の予測）""",
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
        )
        raw_text = result["content"] if isinstance(result["content"], str) else str(result["content"])
        return ReflectiveOutput(raw_text=raw_text)
    
    # ─── §4.6 Step 3+4: 出来事周辺情報統合エージェント (Agentic Loop) ────────
    async def _integration(self, event: Event, impulsive: ImpulsiveOutput, reflective: ReflectiveOutput, checker_feedback: str = "") -> IntegrationOutput:
        """出来事周辺情報統合エージェント: 行動決定 + 周辺情報 + 情景描写 + ストーリー統合（Tool-calling 自律ループ）

        行動決定エージェントを拡張し、出来事の周辺情報や行動後の結果、
        主人公の動きと感情をストーリーとしてまとめる役割を統合。

        Args:
            checker_feedback: 前回のチェッカー不合格時のフィードバック（再生成時のみ）
        """
        from backend.tools.llm_api import AgentTool, call_llm_agentic

        normative_context = ""
        values_context = ""
        if self.package.micro_parameters:
            normative_context = f"理想自己: {self.package.micro_parameters.ideal_self}\n義務自己: {self.package.micro_parameters.ought_self}"
            values_context = json.dumps(self.package.micro_parameters.schwartz_values, ensure_ascii=False)

        protagonist_plan_note = ""
        if event.source == "protagonist_plan":
            protagonist_plan_note = (
                "\n\n【重要: protagonist_plan】\n"
                "このイベントは前日あなた（主人公）が日記の中で「やりたい」と計画したものです。\n"
                "実際にやるかやらないかは、今の気分・状況・優先順位で自律的に判断してください。\n"
            )

        # 感情強度が高い場合の理性バイパス判定
        reflective_bypassed = not reflective.raw_text

        final_decision_data = {}

        async def simulate_action_consequences(action_idea: str = None) -> dict:
            """行動案をテストし、価値観違反や将来の予測をシミュレーションして事前に確認する"""
            if not action_idea:
                return {"status": "FAILED", "message": "ERROR: action_idea引数が欠落しています。"}
            await self._notify(f"行動案のシミュレーション中: {action_idea[:30]}...")

            res = await call_llm(
                tier=self.profile.worker_tier,
                system_prompt="あなたは主人公の行動シミュレーターです。この行動をとった場合の良い点・悪い点、および自身の持つ価値観への違反度（罪悪感を生むか）をフィードバックしてください。JSON形式: {\"pros\": \"...\", \"cons\": \"...\", \"values_violation_risk\": \"high/medium/low\", \"feedback\": \"...\"}",
                user_message=f"【自己の価値観】\n{values_context}\n\n【検討中の行動案】\n{action_idea}",
                json_mode=True
            )
            data = res["content"] if isinstance(res["content"], dict) else {"feedback": str(res["content"])}
            return data

        async def submit_final_decision(decision_package: dict = None) -> dict:
            """最終的な行動決定と周辺情報・情景描写を統合して提出し、ミッションを完了する"""
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
            bypass_note = "\n\n【重要: 感情強度が高いため理性ブランチの報告はありません】\n衝動ブランチのみの情報で判断してください。reflective_route_good/badは 'N/A' としてください。\n"

        known_str = "既知（事前に知っている予定）" if event.known_to_protagonist else "未知（予想外の出来事）"
        system_prompt = f"""あなたは主人公AIの「出来事周辺情報統合エージェント」です。
衝動ルートと理性ルートの意見を統合し、最終的な行動を決定するとともに、
この出来事に対して生じた事象やその前後の情報、主人公の動き、感情などをストーリーとしてまとめてください。
衝動的な無意識的な反応に関するレポートが【衝動ブランチの報告】で、理性的な意識的な反応に関するレポートが【理性ブランチの報告】であり、その二つを融合させます。状況によって、衝動的な反応を優先したりしてください。例えば、怒りが高まっているときは、衝動的な反応を優先します。
また、必ず、衝動的反応、理性的反応それぞれに従ったと仮定したときに起こりうる良い出来事と悪い出来事をそれぞれ2つ以上上げ、それも加味してストーリーを構築してください。

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
   全て含む完全なパッケージを `submit_final_decision` で提出してください。{bypass_note}"""

        # 衝動・理性ブランチの出力をそのまま渡す
        impulsive_text = impulsive.raw_text
        reflective_text = reflective.raw_text if reflective.raw_text else "（感情強度が高いため省略）"

        # チェッカーフィードバックがある場合（再生成時）、user_messageに追加
        feedback_section = ""
        if checker_feedback:
            feedback_section = (
                f"\n\n【重要: 前回の出力に対するチェッカーフィードバック（必ず修正してください）】\n"
                f"{checker_feedback}\n"
                f"上記の不整合を解消した出力を生成してください。\n"
            )

        user_message = (
            f"{wrap_context('マクロプロフィール', self._build_macro_context(), 'integration')}\n\n"
            f"{wrap_context('世界設定', self._build_world_context())}\n\n"
            f"{wrap_context('周囲の人物', self._build_supporting_characters_context())}\n\n"
            f"{wrap_context('規範層', f'{normative_context}{protagonist_plan_note}')}\n\n"
            f"{wrap_context('過去の記憶', self._build_memory_context())}\n\n"
            f"{wrap_context('自伝的エピソード', self._build_episodes_context()[:600])}\n\n"
            f"{wrap_context('衝動ブランチの報告', impulsive_text)}\n\n"
            f"{wrap_context('理性ブランチの報告', reflective_text)}\n\n"
            f"{wrap_context('イベント', f'{event.content}\n（時間帯: {event.time_slot} | {known_str} | 予想外度: {event.expectedness}）')}"
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
                )
            except Exception as e:
                logger.warning(f"[DailyLoop] Integration: Claude ({self.profile.worker_tier}) agentic failed: {e}. Falling back to Gemini.")
                try:
                    await call_llm_agentic_gemini(
                        system_prompt=system_prompt,
                        user_message=user_message,
                        tools=tools,
                        max_iterations=6,
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
        """価値観違反チェック（v10 §4.6c）"""
        values_context = ""
        if self.package.micro_parameters:
            values_context = json.dumps(self.package.micro_parameters.schwartz_values, ensure_ascii=False)
        
        result = await call_llm(
            tier="gemini",
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
                f"{wrap_context('規範層', normative_context, 'reflective')}\n\n"
                f"【行動決定】{integration.final_action}\n\n"
                f"【Higgins Ideal gap】{integration.higgins_ideal_gap}\n"
                f"【Higgins Ought gap】{integration.higgins_ought_gap}"
            ),
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
            tier=self.profile.worker_tier,
            system_prompt="""あなたは主人公AIの内省エージェントです。
今日1日の出来事を振り返り、キャラクターの主観で内省メモを生成してください。

【3工程】
1. 自己推測（Bem Self-Perception Theory）: 自分の行動パターンから自分はどういう人間かを推測する
   ※ 気質パラメータそのものにはアクセスできない。行動からの推測のみ。
2. 過去記録との統合: 記憶にある過去の出来事と今日の出来事に接続点があるか
3. 薄れた記憶の再解釈: 過去の出来事を今日の経験を通じて新たに意味づける

以下の4セクションを、Markdownのセクションヘッダー（##）で区切って出力してください。

## 自己推測
（3-4文。「今日の私は〇〇な行動をとった。これは…」形式。
行動パターンから自分がどういう人間かを推測する。気質パラメータは知らない前提）

## 過去記録との統合
（2-3文。記憶にある過去の出来事と今日の出来事の接続点。なければその旨記述）

## 記憶の再解釈
（2-3文。過去の出来事を今日の経験を通じて新たに意味づける。
「あの時のあれは、こういうことだったのかもしれない」形式。なければ省略可）

## 内省メモ全文
（200-400字。日記の素材となる統合的な内省。上記3工程を自然に統合した文章）""",
            user_message=(
                f"{wrap_context('マクロプロフィール', self._build_macro_context(), 'introspection')}\n\n"
                f"{wrap_context('世界設定', self._build_world_context())}\n\n"
                f"{wrap_context('今日の行動履歴', f'Day {day}の行動まとめ:\n{action_summary}')}\n\n"
                f"{wrap_context('活性化された気質・性格パラメータ', f'活性化されたパラメータの傾向:\n{activation_summary}')}\n\n"
                f"{wrap_context('現在ムード', f'V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}')}\n\n"
                f"{wrap_context('過去の記憶', self._build_memory_context())}\n\n"
                f"{wrap_context('自伝的エピソード', self._build_episodes_context()[:600])}"
                f"{wrap_context('規範層', f'{normative_context}{protagonist_plan_note}')}\n\n"
            ),
            json_mode=False,
        )
        raw_text = result["content"] if isinstance(result["content"], str) else str(result["content"])
        return IntrospectionMemo(raw_text=raw_text)
    
    # ─── §4.8 日記生成 (Agentic Loop) ─────────────────────────
    async def _generate_diary(self, day: int, events: list[EventPackage], introspection: IntrospectionMemo, next_day_plans: list[dict] | None = None, checker_feedback: str = "") -> DiaryEntry:
        """日記生成（Tool-calling 自律ループ、v10 §4.8）"""
        from backend.tools.llm_api import AgentTool, call_llm_agentic
        
        voice = self._build_voice_context()
        event_summaries = "\n".join([
            f"- [{ep.event_id}] {ep.integration_output.final_action[:100]}... → {ep.scene_narration.aftermath[:60]}..."
            for ep in events
        ])
        
        final_diary_content = ""
        check_passed = False  # check_diary_rules がSUCCESSを返したかのフラグ
        last_checked_draft = ""  # チェック済みドラフトの内容
        third_party_passed = False  # third_party_review がSUCCESSを返したかのフラグ
        last_third_party_draft = ""  # 第三者レビュー済みドラフトの内容

        async def check_diary_rules(draft_diary_text: str = None) -> dict:
            """現在書き上げたドラフトが言語的指紋（口癖や避ける語彙）に違反していないかチェックする"""
            nonlocal check_passed, last_checked_draft
            if not draft_diary_text:
                return {"status": "FAILED", "message": "ERROR: draft_diary_text引数が欠落しています。"}
            await self._notify("日記ドラフトの言語規則チェック中...")
            if not self.diary_critic:
                # critic不在でも最低限のルールベースチェックを実施
                issues = []
                for word in ["成長", "気づき", "学び", "視野が広がっ", "新たな発見",
                             "自己成長", "大切なこと", "心の成長", "前向き", "ポジティブ",
                             "チャレンジ", "ステップアップ", "自分を見つめ直", "大事にしたい"]:
                    if word in draft_diary_text:
                        issues.append(f"AI臭い語彙: {word}")
                if len(draft_diary_text) > 500:
                    issues.append(f"日記が長すぎる ({len(draft_diary_text)}字、500字以下にしてください)")
                if len(draft_diary_text) < 200:
                    issues.append(f"日記が短すぎる ({len(draft_diary_text)}字、最低200字推奨)")
                if issues:
                    check_passed = False
                    return {"status": "FAILED", "issues_found": issues, "advice": f"以下の問題を修正して再度ドラフトを作成してください:\n- " + "\n- ".join(issues)}
                check_passed = True
                last_checked_draft = draft_diary_text
                return {"status": "SUCCESS", "message": "基本チェック通過。このまま submit_final_diary で提出してください。"}

            temp_diary = DiaryEntry(day=day, content=draft_diary_text, mood_at_writing=self.current_mood)
            # Critic（ルールベース + 違反指摘）を呼び出すが、添削済テキストは使わず「指摘（issues）」のみを返す
            result = await self.diary_critic.critique(temp_diary, self.current_mood)

            if result["passed"]:
                check_passed = True
                last_checked_draft = draft_diary_text
                return {"status": "SUCCESS", "message": "完璧です。禁止語彙もAI臭さもありません。このまま submit_final_diary で提出してください。"}
            else:
                check_passed = False
                issues = "\n- ".join(result["issues"])
                return {"status": "FAILED", "issues_found": result["issues"], "advice": f"以下の問題を修正して再度ドラフトを作成してください:\n- {issues}"}

        async def validate_linguistic_expression(draft_diary_text: str = None) -> dict:
            """言語表現バリデーター：LinguisticExpressionのすべての要素が守られているかを詳細に検証"""
            nonlocal check_passed
            if not draft_diary_text:
                return {"status": "FAILED", "message": "ERROR: draft_diary_text引数が欠落しています。"}
            if not check_passed or last_checked_draft != draft_diary_text:
                return {"status": "BLOCKED", "message": "先にcheck_diary_rulesでSUCCESSを得てください。"}

            await self._notify("言語表現の詳細バリデーション中...")

            if not self.package.linguistic_expression:
                return {"status": "SUCCESS", "message": "言語表現定義が未設定のため、スキップします。"}

            validator = LinguisticExpressionValidator(self.package.linguistic_expression)
            temp_diary = DiaryEntry(day=day, content=draft_diary_text, mood_at_writing=self.current_mood)
            result = await validator.validate(temp_diary, self.current_mood)

            if result["passed"]:
                passed_count = len(result["passed_items"])
                return {
                    "status": "SUCCESS",
                    "message": f"言語表現バリデーション合格。{passed_count}項目の言語特性が適切に表現されています。",
                    "score": result["score"],
                }
            else:
                issues = "\n- ".join(result["issues"])
                return {
                    "status": "FAILED",
                    "score": result["score"],
                    "issues_found": result["issues"],
                    "advice": f"以下の言語表現の問題を修正してください：\n- {issues}\n\n修正アドバイス：{result['feedback']}",
                }

        async def third_party_review(draft_diary_text: str = None) -> dict:
            """第三者（読者）の視点で日記の品質をチェックする"""
            nonlocal third_party_passed, last_third_party_draft, check_passed
            if not draft_diary_text:
                return {"status": "FAILED", "message": "ERROR: draft_diary_text引数が欠落しています。"}
            if not check_passed or last_checked_draft != draft_diary_text:
                return {"status": "BLOCKED", "message": "先に check_diary_rules → validate_linguistic_expression でSUCCESSを得てください。"}

            await self._notify("第三者視点での日記レビュー中...")

            event_summaries_for_review = "\n".join([
                f"- [{ep.event_id}] {ep.integration_output.final_action[:100]}"
                for ep in events
            ])

            temp_diary = DiaryEntry(day=day, content=draft_diary_text, mood_at_writing=self.current_mood)
            past_diary_ctx = self._build_past_diary_context()
            result = await self.third_party_reviewer.review(
                temp_diary, self.current_mood, event_summaries_for_review,
                past_diaries=past_diary_ctx,
            )

            if result["passed"]:
                third_party_passed = True
                last_third_party_draft = draft_diary_text
                return {"status": "SUCCESS", "message": "第三者視点チェックOK。submit_final_diary で提出してください。"}
            else:
                # 第三者レビュー不合格: テキスト修正が必要なので言語チェックもリセット
                third_party_passed = False
                check_passed = False
                issues = "\n- ".join(result["issues"])
                return {
                    "status": "FAILED",
                    "issues_found": result["issues"],
                    "advice": f"第三者（読者）視点での問題:\n- {issues}\n修正後、再度 check_diary_rules → third_party_review の順で通してください。",
                }

        async def submit_final_diary(final_diary_text: str = None) -> dict:
            """全てのチェックを通過した最終的な日記テキストを提出する"""
            nonlocal check_passed, last_checked_draft, final_diary_content, third_party_passed, last_third_party_draft
            if not final_diary_text:
                return {"status": "FAILED", "message": "ERROR: final_diary_text引数が欠落しています。"}
            # check_diary_rules, validate_linguistic_expression, third_party_review の全てを経由していない場合は強制チェック
            if not check_passed or last_checked_draft != final_diary_text:
                await self._notify("提出前の強制チェック（言語ルール）を実行中...")
                check_result = await check_diary_rules(final_diary_text)
                if check_result["status"] != "SUCCESS":
                    return {"status": "FAILED", "message": f"提出拒否: check_diary_rules を先に通過させてください。{check_result.get('advice', '')}"}
                await self._notify("提出前の強制チェック（言語表現）を実行中...")
                validate_result = await validate_linguistic_expression(final_diary_text)
                if validate_result["status"] != "SUCCESS":
                    return {"status": "FAILED", "message": f"提出拒否: validate_linguistic_expression を先に通過させてください。{validate_result.get('advice', '')}"}
            if not third_party_passed or last_third_party_draft != final_diary_text:
                await self._notify("提出前の強制チェック（第三者レビュー）を実行中...")
                review_result = await third_party_review(final_diary_text)
                if review_result["status"] != "SUCCESS":
                    return {"status": "FAILED", "message": f"提出拒否: third_party_review を先に通過させてください。{review_result.get('advice', '')}"}
            final_diary_content = final_diary_text
            await self._notify("最終日記が完成・提出されました。", "complete")
            return {"status": "SUCCESS", "message": "Diary submitted successfully."}

        tools = [
            AgentTool(
                name="check_diary_rules",
                description="執筆した日記ドラフトがキャラクターの言語的指紋（口癖・禁止語彙・口調等）に違反していないかを厳密にチェックします。提出前に必ず呼び出し、'SUCCESS' が返るまで何度でも修正して再チェックしてください。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "draft_diary_text": {"type": "string", "description": "現在の日記ドラフト"}
                    },
                    "required": ["draft_diary_text"]
                },
                handler=check_diary_rules
            ),
            AgentTool(
                name="validate_linguistic_expression",
                description="check_diary_rulesでSUCCESS後に呼び出してください。キャラクターの言語表現方法（一人称、口癖、文末表現、絵文字使用、自問頻度、比喩頻度、日記のトーン等）がすべて正しく守られているかを詳細に検証します。SUCCESSが返るまで修正・再チェックを繰り返してください。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "draft_diary_text": {"type": "string", "description": "check_diary_rulesでSUCCESS済みの日記ドラフト全文"}
                    },
                    "required": ["draft_diary_text"]
                },
                handler=validate_linguistic_expression
            ),
            AgentTool(
                name="third_party_review",
                description="check_diary_rules と validate_linguistic_expression でSUCCESS後に呼び出してください。第三者（読者）の視点で日記を評価します。理解しやすいか、面白いか、矛盾がないか、自然な日記として成立しているかを検証します。SUCCESSが返るまで修正・再チェックを繰り返してください。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "draft_diary_text": {"type": "string", "description": "check_diary_rules と validate_linguistic_expression でSUCCESS済みの日記ドラフト全文"}
                    },
                    "required": ["draft_diary_text"]
                },
                handler=third_party_review
            ),
            AgentTool(
                name="submit_final_diary",
                description="check_diary_rules と third_party_review の両方でSUCCESSを得た最終的な完成版の日記を提出して完了します。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "final_diary_text": {"type": "string", "description": "最終的な日記の全文（約400字、500字以下）。一人称視点で本人が書いたように。"}
                    },
                    "required": ["final_diary_text"]
                },
                handler=submit_final_diary
            )
        ]
        
        system_prompt = f"""あなたはキャラクター本人として日記を書く自律エージェントです。

【言語的指紋（厳守事項）】
{voice}

【日記のルール】
- 一人称視点で、そのキャラクターらしい文体で書くこと
- 避ける語彙は絶対に使わないこと（「成長」「気づき」「学び」等のAI臭い語彙）
- 全ての出来事を書く必要はない。主観的に重要だと感じたことだけを書く。しかし、1日全体を見渡しての所感を書くのは推奨
- 日々の経験や記憶、感情、認識の変化が反映されているとよい。昨日までの出来事が今日の日記の語り方に影響を及ぼし、時間が進むにつれて、キャラクターの輪郭が立ち上がっていくことを期待します。
- ただの、出来事の羅列ではなく、キャラクタ独自の経験や感性、記憶、キャラクター設定に基づき、深くキャラクターの内面を反映した文章にする必要がある。
- 第3者が日記だけを見て、理解でき、納得でき、面白い日記である必要がある。
- 与えられた、マクロプロフィール、世界設定、今日の出来事、内省メモ、現在のムード、短期記憶、規範層、過去の日記を全て加味して、日記を作成してください。
- 「短期記憶（デイリーログ + key memory）」は最重要項目です。必ず保持し、日記の中に自然に反映してください。
- 「過去の日記」は参照用です。言及すべき点があれば自然に触れてください。
- 「明日の予定」がある場合、明日への意向・期待・不安などを日記の中で自然に触れてください。
- 日記は必ず、400字以上500字以下で書くこと


【エージェンティック行動指針】
1. まず日記のドラフトをPlanを立て計画的に執筆し、`check_diary_rules` ツールを使って自身の口癖や禁止語彙に反していないか自発的にテストしてください。
2. もし不合格（FAILED）が返ってきたら、指摘された点に基づいて自ら文章を書き直し、再度ツールでチェックしてください。
3. `check_diary_rules` で合格（SUCCESS）が返ってきたら、同じドラフトを `validate_linguistic_expression` ツールに渡して言語表現がすべて守られているか検証してください。
4. `validate_linguistic_expression` で合格（SUCCESS）が返ってきたら、同じドラフトを `third_party_review` ツールに渡して第三者視点のチェックを受けてください。
5. いずれかのツールで不合格（FAILED）が返ってきたら、指摘に基づいて修正し、再度 `check_diary_rules` → `validate_linguistic_expression` → `third_party_review` の順で通してください。
6. 3つすべてのチェックで合格（SUCCESS）が返ってきたら、`submit_final_diary` ツールで提出して任務を完了してください。"""

        # Day1特別処理: 世界観・設定紹介セクション
        if day == 1:
            system_prompt += f"""

【Day 1 特別指示: 世界観・設定紹介】
これは物語の第1日目の日記です。読者がこの日記を読み始めるにあたって、
以下の情報を「あなた（主人公）自身の言葉と声で」自然に織り込んでください:

- あなたは誰で、どういう存在なのか
- なぜここ（この世界・この場所）にいるのか
- この世界はどんな場所なのか（あなたの目を通して）
- あなたが今置かれている状況

※ 説明的・辞書的な記述は禁止。あなた自身が日記の冒頭で自然に触れる形で書くこと。
※ 世界観紹介と今日の出来事の感想を合わせて約400字（500字以下）に収めること。
※ この日記が「物語の入口」として機能するよう、読者の興味を引く書き方を心がけること。"""

        # チェッカーフィードバック（再生成時のみ）
        diary_feedback_section = ""
        if checker_feedback:
            diary_feedback_section = (
                f"\n\n【重要: 前回の日記に対するチェッカーフィードバック（必ず修正してください）】\n"
                f"{checker_feedback}\n"
                f"上記の不整合を解消した日記を書いてください。\n"
            )

        # 翌日予定セクション（日記の前に計画済みの場合のみ）
        next_day_section = ""
        if next_day_plans:
            plan_lines = []
            for p in next_day_plans:
                if isinstance(p, dict):
                    plan_lines.append(f"- {p.get('action', '')}（{p.get('preferred_time', '')}頃、理由: {p.get('motivation', '')}）")
            if plan_lines:
                next_day_section = f"\n\n{wrap_context('明日の予定', '明日やりたいと考えていること:\n' + chr(10).join(plan_lines))}"

        # 過去の日記セクション（独立DB、参照用）
        past_diary_ctx = self._build_past_diary_context()
        past_diary_section = ""
        if past_diary_ctx:
            past_diary_section = (
                f"\n\n{wrap_context('過去の日記（参照用）', '以下は過去に書いた日記です。参照し、言及すべき点があれば自然に触れてください。\n' + past_diary_ctx, 'diary')}"
            )

        user_message = (
            f"{wrap_context('マクロプロフィール', self._build_macro_context(), 'diary')}\n\n"
            f"{wrap_context('世界設定', self._build_world_context())}\n\n"
            f"{wrap_context('今日の出来事', f'Day {day}の出来事:\n{event_summaries}', 'diary')}\n\n"
            f"{wrap_context('内省メモ', introspection.raw_text, 'diary')}\n\n"
            f"{wrap_context('現在ムード', f'V={self.current_mood.valence:.1f} A={self.current_mood.arousal:.1f} D={self.current_mood.dominance:.1f}')}\n\n"
            f"{wrap_context('短期記憶（最重要 — デイリーログ + key memory）', self._build_memory_context(), 'diary')}"
            f"{wrap_context('規範層', f'{normative_context}{protagonist_plan_note}')}\n\n"
            f"{past_diary_section}"
            f"{next_day_section}"
            f"{diary_feedback_section}"
        )

        retry_label = "（再生成）" if checker_feedback else ""
        await self._notify(f"日記生成エージェントを自律モードで起動{retry_label}...")
        
        from backend.tools.llm_api import call_llm_agentic_gemini as _diary_gemini_fallback

        if self.profile.worker_tier in ("opus", "sonnet"):
            try:
                await call_llm_agentic(
                    tier=self.profile.worker_tier,
                    system_prompt=system_prompt,
                    user_message=user_message,
                    tools=tools,
                    max_iterations=10,
                )
            except Exception as e:
                logger.warning(f"[DailyLoop] Diary: Claude ({self.profile.worker_tier}) agentic failed: {e}. Falling back to Gemini.")
                try:
                    await _diary_gemini_fallback(
                        system_prompt=system_prompt,
                        user_message=user_message,
                        tools=tools,
                        max_iterations=10,
                    )
                except Exception as e2:
                    logger.error(f"[DailyLoop] Diary: Gemini fallback also failed: {e2}.")
        else:
            try:
                await _diary_gemini_fallback(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    tools=tools,
                    max_iterations=10,
                )
            except Exception as e:
                logger.error(f"[DailyLoop] Diary: Gemini agentic failed: {e}.")

        if not final_diary_content:
            logger.warning("Agentic loop finished without submitting final diary.")
            final_diary_content = "(本日は何も書く気になれなかった)"
            
        return DiaryEntry(
            day=day,
            content=final_diary_content,
            mood_at_writing=self.current_mood.model_copy(),
        )
    
    # ─── key memory抽出（§4.9.3.1）────────────────────────────
    async def _extract_key_memory(self, day: int, diary: DiaryEntry) -> KeyMemory:
        """key memory抽出（v10 §4.9.3.1）"""
        result = await call_llm(
            tier="gemini",
            system_prompt="""あなたはkey memory抽出エージェントです。
日記から「本当に重要だった瞬間」を1つだけ抽出し、300字以内で要約してください。
このキャラクターにとって重要な経験や事柄を記録してください。
価値観が変わるような経験、強い感情を感じた経験とその内省、キャラクターが大事にしたいと考えたこと、キャラクターがポジティブな気持ちを得たこと、楽しいと思ったこと、失敗したことは必ずこのキーメモリに含めてください。

出力形式: JSON
{"key_memory": "300字以内の要約"}""",
            user_message=(f"Day {day}の日記:\n{diary.content}\n\n"
                         f"{wrap_context('マクロプロフィール', self._build_macro_context(), 'introspection')}\n\n"
                         f"{wrap_context('世界設定', self._build_world_context())}\n\n"
                         f"{wrap_context('今日の行動履歴', f'Day {day}の行動まとめ:\n{action_summary}')}\n\n"
                         f"{wrap_context('過去の記憶', self._build_memory_context())}\n\n"
                         f"{wrap_context('自伝的エピソード', self._build_episodes_context()[:600])}"),
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return KeyMemory(
            day=day,
            content=data.get("key_memory", diary.content[:300]),
            mood_at_extraction=self.current_mood.model_dump(),
        )
    
    # ─── デイリーログ保存 & 要約（§4.9.3.2 置換）─────────────────
    def _build_full_daily_log(self, events: list[EventPackage], introspection: IntrospectionMemo) -> str:
        """1日の全行動ログをテキストとして構築する"""
        parts = []
        for ep in events:
            action = ep.integration_output.final_action or "(行動なし)"
            scene = ep.scene_narration.scene_description or ""
            aftermath = ep.scene_narration.aftermath or ""
            emotion = ep.integration_output.emotion_change or ""
            line = f"[{ep.event_id}] {action}"
            if scene:
                line += f"\n  情景: {scene[:150]}"
            if aftermath:
                line += f"\n  後日譚: {aftermath[:100]}"
            if emotion:
                line += f"\n  感情変化: {emotion[:80]}"
            parts.append(line)
        log_text = "\n\n".join(parts)
        if introspection and introspection.raw_text:
            log_text += f"\n\n[内省]: {introspection.raw_text}"
        return log_text

    async def _llm_summarize(self, text: str, target_ratio: float = 0.5) -> str:
        """LLMでテキストを要約する（target_ratio = 目標圧縮率）"""
        target_chars = max(30, int(len(text) * target_ratio))
        result = await call_llm(
            tier="gemini",
            system_prompt=(
                f"以下のテキストを{target_chars}字程度に要約してください。"
                "重要な出来事・感情・人間関係の変化を保持し、些末な描写は省いてください。"
                '出力形式: JSON {{"summary": "要約テキスト"}}'
            ),
            user_message=text,
            json_mode=True,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        return data.get("summary", text[:target_chars])

    async def _create_daily_log_and_summarize(
        self, day: int, events: list[EventPackage], introspection: IntrospectionMemo,
    ):
        """1日の行動ログを保存し、当日の要約 + 過去日の再要約を行う。

        日記生成の後、1日の最後に実行される。
        各日のフォルダに最新IDファイルとして蓄積していく。
        """
        # 1. 当日の全行動ログを作成（001_full.json）
        full_log = self._build_full_daily_log(events, introspection)
        self.daily_log_store.save_full_log(day, full_log)

        # 2. 当日の要約を作成（002_summary.json）— 約半分に圧縮
        summary = await self._llm_summarize(full_log, target_ratio=0.5)
        self.daily_log_store.save_summary(day, summary, version=2, created_at_day=day)
        await self._notify(f"Day {day}: デイリーログ要約完了（{len(full_log)}字→{len(summary)}字）")

        # 3. 過去の日のさらなる要約（古い日ほどさらに圧縮していく忘却プロセス）
        for past_day in range(1, day):
            latest = self.daily_log_store.get_latest(past_day)
            if not latest:
                continue
            age = day - past_day
            # 3日以上前かつまだ圧縮余地がある場合、さらに半分に要約
            if age >= 3 and latest.char_count > 80:
                re_summary = await self._llm_summarize(latest.content, target_ratio=0.5)
                self.daily_log_store.save_summary(
                    past_day, re_summary,
                    version=latest.version + 1, created_at_day=day,
                )
                logger.info(
                    f"[DailyLogStore] Day {past_day} re-summarized: "
                    f"v{latest.version}({latest.char_count}字)→v{latest.version+1}({len(re_summary)}字)"
                )

        # 4. normal_area を DailyLogStore の最新データで同期（互換性維持）
        self.memory_db.normal_area.clear()
        for entry in self.daily_log_store.get_all_latest():
            stage = "current" if entry.day == day else (
                "one_day_ago" if day - entry.day == 1 else (
                    "two_days_ago" if day - entry.day == 2 else "three_plus_days_ago"
                )
            )
            self.memory_db.normal_area.append(ShortTermMemoryNormal(
                day=entry.day, stage=stage,
                summary=entry.content, char_count=entry.char_count,
            ))
    
    # ─── メインループ ──────────────────────────────────────────
    async def run(self, days: int = 7) -> list[DayProcessingState]:
        """日次ループを実行（v10 §4 完全準拠）"""
        # 既に保存済みの日がある場合、その翌日から再開
        start_day = self.memory_store.get_latest_day() + 1
        if start_day > 1:
            await self._notify(f"Day {start_day - 1}まで保存済み → Day {start_day}から再開")
        await self._notify(f"日次ループ開始: Day {start_day}〜{days}")

        for day in range(start_day, days + 1):
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

                # §4.3+§4.6 Step 1: 衝動系エージェント（Perceiver + Impulsive 統合）
                impulsive = await self._impulsive(event, activation)

                # 感情強度判定: highなら理性ブランチをバイパス
                emotion_intensity = await self._evaluate_emotion_intensity(impulsive)
                if emotion_intensity.intensity == "high":
                    await self._notify(f"  感情強度: 高 → 理性ブランチをバイパス（理由: {emotion_intensity.reasoning[:40]}）")
                    reflective = ReflectiveOutput()  # 空のReflective出力
                else:
                    # §4.6 Step 2: Reflective Agent（通常実行）
                    reflective = await self._reflective(event, impulsive, activation)

                # §4.6b 裏方出力検証
                verification = await self.verification_agent.verify(impulsive)
                if not verification["passed"]:
                    if verification["corrected_impulsive"]:
                        impulsive = verification["corrected_impulsive"]
                
                # §4.6 Step 3+4: 出来事周辺情報統合（行動決定 + 情景描写 統合）
                # チェッカーフィードバック付き再生成ループ（最大2回再試行）
                max_integration_retries = 2
                checker_feedback_for_integration = ""
                for _retry_i in range(1 + max_integration_retries):
                    integration = await self._integration(
                        event, impulsive, reflective,
                        checker_feedback=checker_feedback_for_integration,
                    )

                    # 4つの個別チェックAI: 統合エージェント出力を検証
                    integration_check_text = (
                        f"行動決定: {integration.final_action}\n"
                        f"情景描写: {integration.scene_description}\n"
                        f"後日譚: {integration.aftermath}\n"
                        f"主人公の動き: {integration.protagonist_movement}\n"
                        f"ストーリー: {integration.story_segment}"
                    )
                    check_results = await self._run_consistency_checks(
                        integration_check_text, activation, "統合エージェント出力"
                    )

                    # major不整合があるか判定
                    major_issues = [cr for cr in check_results if not cr.passed and cr.severity == "major"]
                    if not major_issues:
                        # minor以下はログのみで通過
                        for cr in check_results:
                            if not cr.passed:
                                logger.info(f"[チェッカー] {cr.checker_type} minor不整合（許容）: {'; '.join(cr.issues[:2])}")
                        break

                    # major不整合: フィードバックを構築して再生成
                    feedback_parts = []
                    for cr in major_issues:
                        feedback_parts.append(
                            f"【{cr.checker_type}チェッカー不合格】問題: {'; '.join(cr.issues)}。修正案: {cr.suggestion}"
                        )
                    checker_feedback_for_integration = "\n".join(feedback_parts)
                    logger.warning(
                        f"[チェッカー] 統合出力にmajor不整合 ({len(major_issues)}件) → 再生成 (試行{_retry_i+2}/{1+max_integration_retries})"
                    )
                    await self._notify(f"  チェッカー不合格({len(major_issues)}件major) → フィードバック付き再生成...")
                else:
                    # 最大再試行でも通過しなかった場合はそのまま使用
                    logger.warning("[チェッカー] 統合出力: 最大再試行回数超過。現在の出力をそのまま使用。")

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
                    impulsive_output=impulsive,
                    reflective_output=reflective,
                    integration_output=integration,
                    scene_narration=SceneNarration(
                        scene_description=integration.scene_description,
                        aftermath=integration.aftermath,
                    ),
                    values_violation=violation,
                    mood_before=self.current_mood.model_copy(),
                    mood_after=self.current_mood.model_copy(),
                )
                day_state.events_processed.append(event_pkg)
            
            # ─── 外層（1日の終わり）────────────────────────

            # §4.7 内省フェーズ
            await self._notify(f"Day {day}: 内省フェーズ")
            snap_introspection = token_tracker.snapshot()
            try:
                introspection = await self._introspection(day, day_state.events_processed)
            except Exception as e:
                logger.error(f"[DailyLoop] Day {day} 内省フェーズエラー: {e}")
                introspection = IntrospectionMemo(full_memo="（内省生成に失敗しました）")
            day_state.introspection = introspection
            day_state.cost_records.append(token_tracker.cost_since(snap_introspection, "内省フェーズ"))

            # §4.9.4 翌日予定追加（Day 7以外）★ 日記生成の前に実行
            if day < days:
                await self._notify(f"Day {day}: 翌日予定の計画")
                snap_next_day = token_tracker.snapshot()
                try:
                    plans = await self.next_day_agent.stage1_protagonist_plan(
                        day=day,
                        events=day_state.events_processed,
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
                        # stage2がNoneの場合、plans[0]から直接フォールバックEvent生成
                        if not new_event:
                            logger.warning(f"[DailyLoop] Day {day}: stage2がNone → plans[0]からフォールバックEvent生成")
                            valid_slots = {"morning", "late_morning", "noon", "afternoon", "evening", "night", "late_night"}
                            preferred = plans[0].preferred_time if plans[0].preferred_time in valid_slots else "afternoon"
                            plan_count = sum(1 for e in self.package.weekly_events_store.events if e.source == "protagonist_plan")
                            new_event = Event(
                                id=f"evt_plan_{plan_count + 1:03d}",
                                day=day + 1,
                                time_slot=preferred,
                                known_to_protagonist=True,
                                source="protagonist_plan",
                                expectedness="high",
                                content=plans[0].action,
                                involved_characters=[],
                                meaning_to_character=plans[0].motivation,
                                narrative_arc_role="standalone_ripple",
                                conflict_type=None,
                                connected_episode_id=None,
                                connected_values=[],
                            )
                            plans[0].inserted = True
                        self.package.weekly_events_store.events.append(new_event)
                        day_state.next_day_plans = [p.model_dump() for p in plans]
                    day_state.cost_records.append(token_tracker.cost_since(snap_next_day, "翌日予定"))
                except Exception as e:
                    logger.error(f"[DailyLoop] Day {day} 翌日予定計画エラー: {e}")
                    day_state.cost_records.append(token_tracker.cost_since(snap_next_day, "翌日予定（失敗）"))

            # §4.8 日記生成 & §4.9.1 Self-Critic (Agentic統合済)
            # チェッカーフィードバック付き再生成ループ（最大2回再試行）
            await self._notify(f"Day {day}: 日記生成（自律チェック込み）")
            snap_diary = token_tracker.snapshot()
            max_diary_retries = 2
            checker_feedback_for_diary = ""
            last_activation = day_state.events_processed[-1].activation_log if day_state.events_processed else ActivationLog()

            for _diary_retry in range(1 + max_diary_retries):
                try:
                    diary = await self._generate_diary(
                        day, day_state.events_processed, introspection,
                        next_day_plans=day_state.next_day_plans,
                        checker_feedback=checker_feedback_for_diary,
                    )
                except Exception as e:
                    logger.error(f"[DailyLoop] Day {day} 日記生成エラー: {e}")
                    diary = DiaryEntry(day=day, content="（日記生成に失敗しました）", mood_at_writing=self.current_mood.model_copy())
                    break

                # 4つの個別チェックAI: 日記出力を検証
                if diary.content and diary.content != "（日記生成に失敗しました）":
                    diary_check_results = await self._run_consistency_checks(
                        diary.content, last_activation, "日記出力"
                    )

                    major_diary_issues = [cr for cr in diary_check_results if not cr.passed and cr.severity == "major"]
                    if not major_diary_issues:
                        for cr in diary_check_results:
                            if not cr.passed:
                                logger.info(f"[日記チェッカー] {cr.checker_type} minor不整合（許容）: {'; '.join(cr.issues[:2])}")
                        break

                    # major不整合: フィードバックを構築して再生成
                    feedback_parts = []
                    for cr in major_diary_issues:
                        feedback_parts.append(
                            f"【{cr.checker_type}チェッカー不合格】問題: {'; '.join(cr.issues)}。修正案: {cr.suggestion}"
                        )
                    checker_feedback_for_diary = "\n".join(feedback_parts)
                    logger.warning(
                        f"[日記チェッカー] Day {day} 日記にmajor不整合 ({len(major_diary_issues)}件) → 再生成 (試行{_diary_retry+2}/{1+max_diary_retries})"
                    )
                    await self._notify(f"  日記チェッカー不合格({len(major_diary_issues)}件major) → フィードバック付き再生成...")
                else:
                    break
            else:
                logger.warning(f"[日記チェッカー] Day {day}: 最大再試行回数超過。現在の日記をそのまま使用。")

            day_state.diary = diary
            day_state.cost_records.append(token_tracker.cost_since(snap_diary, "日記生成"))

            # 日記をストリーミング
            if self.ws:
                await self.ws.send_diary_entry(day, diary.content)

            # §4.9.2 ムード更新（Peak-End Rule）
            self._update_mood_daily(day_state)

            # §4.9.3.1 key memory抽出
            snap_key_memory = token_tracker.snapshot()
            try:
                key_mem = await self._extract_key_memory(day, diary)
            except Exception as e:
                logger.error(f"[DailyLoop] Day {day} key memory抽出エラー: {e}")
                key_mem = KeyMemory(day=day, content=diary.content[:300], mood_at_extraction=self.current_mood.model_dump())
            day_state.key_memory = key_mem
            day_state.cost_records.append(token_tracker.cost_since(snap_key_memory, "key memory抽出"))
            self.key_memory_store.save(key_mem)

            # §4.9.3.2 デイリーログ保存 & 要約（日記生成の後に実行）
            snap_daily_log = token_tracker.snapshot()
            try:
                await self._create_daily_log_and_summarize(day, day_state.events_processed, introspection)
            except Exception as e:
                logger.error(f"[DailyLoop] Day {day} デイリーログ要約エラー: {e}")
            day_state.cost_records.append(token_tracker.cost_since(snap_daily_log, "デイリーログ要約"))

            # diary_store にも追記（互換性維持）
            self.memory_db.diary_store.append(diary.content)
            self.memory_store.save(day, self.memory_db)

            # §4.9.5 ムードcarry-over
            daily_mood_snapshot = self.current_mood.model_copy()
            day_state.daily_mood = daily_mood_snapshot
            self._mood_carry_over()
            # ムード状態をファイルに永続化（daily_mood + carry_over後のmood）
            self.mood_store.save(day, daily_mood_snapshot, self.current_mood.model_copy())

            self.day_results.append(day_state)

            try:
                from backend.storage.md_storage import save_daily_log
                cname = self.package.macro_profile.basic_info.name if (self.package.macro_profile and self.package.macro_profile.basic_info) else "Unknown_Character"
                await save_daily_log(cname, day, day_state)
            except Exception as e:
                import logging
                logging.getLogger("daily_loop").error(f"MD保存エラー: {e}")

            # protagonist_planイベントを含む最新パッケージをpackage.jsonに保存
            # （中断時にも翌日予定が失われないよう、各Day完了後に必ず永続化）
            try:
                from backend.storage.md_storage import safe_name as _safe_name
                pkg_dir = AppConfig.STORAGE_DIR / _safe_name(self._cname)
                pkg_dir.mkdir(parents=True, exist_ok=True)
                pkg_path = pkg_dir / "package.json"
                pkg_path.write_text(
                    json.dumps(self.package.model_dump(mode="json"), ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                logger.info(f"[DailyLoop] Day {day} 完了: package.json を更新しました")
            except Exception as e:
                logger.warning(f"[DailyLoop] Day {day} package.json保存エラー: {e}")

            # WebSocket でコスト更新を配信
            if self.ws:
                await self.ws.send_cost_update(token_tracker.summary())

            await self._notify(f"=== Day {day} 完了 ===", "complete")
        
        await self._notify(f"全{days}日分の日記生成完了！", "complete")
        return self.day_results
