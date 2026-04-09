"""
記憶システムのデータモデル（v10 §5準拠）
短期記憶DB（key memory + 通常領域）、行動履歴バッファ、日記本文ストア
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class KeyMemory(BaseModel):
    """key memory（1日1個、300字以内、7日間フル保持、段階圧縮対象外）"""
    day: int
    content: str = Field(..., max_length=300, description="本当に重要だった瞬間")
    mood_at_extraction: dict = Field(default_factory=dict, description="抽出時のPAD")


class ShortTermMemoryNormal(BaseModel):
    """短期記憶通常領域（段階圧縮方式）"""
    day: int
    stage: str = Field(..., description="current/one_day_ago/two_days_ago/three_plus_days_ago")
    summary: str = ""
    char_count: int = 0


class ShortTermMemoryDB(BaseModel):
    """短期記憶DB（2領域構造、v10 §5.1準拠）"""
    key_memories: list[KeyMemory] = Field(default_factory=list, description="7日間フル保持")
    normal_area: list[ShortTermMemoryNormal] = Field(default_factory=list, description="段階圧縮")


class MoodState(BaseModel):
    """
    現在ムードパラメータ（PAD 3次元、v10 §4.5準拠）
    各次元 -5 ~ +5 の連続値
    """
    valence: float = Field(0.0, ge=-5.0, le=5.0, description="感情価（快-不快）")
    arousal: float = Field(0.0, ge=-5.0, le=5.0, description="覚醒度（興奮-沈静）")
    dominance: float = Field(0.0, ge=-5.0, le=5.0, description="支配感（支配-服従）")


class PerceiverOutput(BaseModel):
    """Perceiverの出力（v10 §4.3準拠）"""
    phenomenal_description: str = Field("", description="現象的記述")
    reflexive_emotion: str = Field("", description="反射感情")
    automatic_attention: str = Field("", description="自動注意")


class ImpulsiveOutput(BaseModel):
    """Impulsive Agentの出力（v10 §4.6 Step 1準拠）"""
    impulse_reaction: str = Field("", description="衝動的反応")
    bodily_sensation: str = Field("", description="身体感覚")
    action_tendency: str = Field("", description="行動傾向")


class ReflectiveOutput(BaseModel):
    """理性ブランチの出力（v10 §4.6 Step 2準拠）"""
    inner_analysis: str = Field("", description="濃密な内面分析レポート")
    value_connections: str = Field("", description="価値観・知識・過去経験との接続")
    suggestion: str = Field("", description="示唆")
    prediction: str = Field("", description="理性側ルートの予測")


class IntegrationOutput(BaseModel):
    """統合エージェントの出力（v10 §4.6 Step 3準拠）"""
    impulse_route_good: str = Field("", description="衝動ルートの良いこと予測")
    impulse_route_bad: str = Field("", description="衝動ルートの悪いこと予測")
    reflective_route_good: str = Field("", description="理性ルートの良いこと予測")
    reflective_route_bad: str = Field("", description="理性ルートの悪いこと予測")
    higgins_ideal_gap: str = Field("", description="Ideal不一致（落胆系）")
    higgins_ought_gap: str = Field("", description="Ought不一致（不安系）")
    final_action: str = Field("", description="最終行動決定")
    emotion_change: str = Field("", description="気持ちの変化の短文記述")


class SceneNarration(BaseModel):
    """情景描写・後日譚（v10 §4.6 Step 4準拠）"""
    scene_description: str = Field("", description="濃密な情景描写")
    aftermath: str = Field("", description="後日譚")


class ValuesViolationResult(BaseModel):
    """価値観違反チェック（v10 §4.6c準拠）"""
    violation_detected: bool = False
    violation_content: str = ""
    guilt_emotion: str = ""


class EventPackage(BaseModel):
    """1イベントの処理結果パッケージ（v10 §4.6d準拠）"""
    event_id: str
    event_content: str = ""
    perceiver_output: PerceiverOutput = Field(default_factory=PerceiverOutput)
    impulsive_output: ImpulsiveOutput = Field(default_factory=ImpulsiveOutput)
    reflective_output: ReflectiveOutput = Field(default_factory=ReflectiveOutput)
    integration_output: IntegrationOutput = Field(default_factory=IntegrationOutput)
    scene_narration: SceneNarration = Field(default_factory=SceneNarration)
    values_violation: ValuesViolationResult = Field(default_factory=ValuesViolationResult)
    mood_after: MoodState = Field(default_factory=MoodState)


class IntrospectionMemo(BaseModel):
    """内省メモ（v10 §4.7準拠）"""
    self_perception: str = Field("", description="自己推測（Bem Self-Perception）")
    past_connection: str = Field("", description="過去記録との統合")
    memory_reinterpretation: str = Field("", description="薄れた記憶の再解釈")
    full_memo: str = Field("", description="内省メモ全文（200-400字）")


class DiaryEntry(BaseModel):
    """日記1日分"""
    day: int
    content: str = ""
    mood_at_writing: MoodState = Field(default_factory=MoodState)


class DayProcessingState(BaseModel):
    """1日の処理状態"""
    day: int
    events_processed: list[EventPackage] = Field(default_factory=list)
    introspection: Optional[IntrospectionMemo] = None
    diary: Optional[DiaryEntry] = None
    daily_mood: MoodState = Field(default_factory=MoodState, description="日次集約ムード（Peak-End Rule）")
    key_memory: Optional[KeyMemory] = None
    next_day_plans: list[dict] = Field(default_factory=list)
