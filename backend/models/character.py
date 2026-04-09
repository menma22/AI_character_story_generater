"""
データモデル定義（Pydantic v2）
specification_v10.md および script_ai_app_specification_v2.md に基づく
脚本パッケージの全データ構造を定義する
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# Tier -1: Creative Director 出力（v2 §4.7 完全準拠）
# ═══════════════════════════════════════════════════════════════

class ReferenceStory(BaseModel):
    """参考となる既存物語"""
    title: str = ""
    author_or_source: str = ""
    relevance: str = ""

class WantAndNeed(BaseModel):
    """Want/Need構造（McKee脚本論）"""
    want: str = Field("", description="本人が自覚している外的目標")
    need: str = Field("", description="本人が気づいていない本質的な内的必要")
    tension: str = Field("", description="両者の緊張関係")

class PsychologicalHints(BaseModel):
    """心理学的パラメータの方向性（v2 §4.7準拠）"""
    temperament_direction: str = Field("", description="Cloninger系の気質方向性")
    values_direction: str = Field("", description="Schwartz系の価値観方向性")
    want_and_need: WantAndNeed = Field(default_factory=WantAndNeed)
    ghost_wound_hint: str = Field("", description="過去の傷の方向性")
    lie_hint: str = Field("", description="誤った信念の方向性")

class ConceptPackage(BaseModel):
    """Creative Director の出力パッケージ（v2 §4.7 完全準拠）"""
    character_concept: str = Field("", description="キャラクター設定の大まかな概要（500-1000字の濃密な概念記述）")
    story_outline: str = Field("", description="物語設定の大まかな概要（500-1000字の濃密な概念記述）")
    narrative_theme: str = Field("", description="物語的テーマ（1-2文）")
    interestingness_hooks: list[str] = Field(default_factory=list, description="面白さのフック（3-5個）")
    genre_and_world: str = Field("", description="ジャンルと世界観の方向性")
    reference_stories: list[ReferenceStory] = Field(default_factory=list, description="参考となる既存物語")
    critical_design_notes: list[str] = Field(default_factory=list, description="下流への設計上の指示")
    psychological_hints: PsychologicalHints = Field(default_factory=PsychologicalHints)
    iteration_count: int = Field(0, description="Self-Critique反復回数")
    self_critique_history: list[dict] = Field(default_factory=list)
    verdict: str = Field("pass", description="最終判定")


# ═══════════════════════════════════════════════════════════════
# Phase A-1: マクロプロフィール
# ═══════════════════════════════════════════════════════════════

class BasicInfo(BaseModel):
    """基本情報"""
    name: str
    age: int
    gender: str
    appearance: str = ""
    occupation: str = ""

class SocialPosition(BaseModel):
    """社会的位置"""
    occupation_detail: str = ""
    economic_status: str = ""
    living_area: str = ""

class FamilyAndIntimacy(BaseModel):
    """家族・親密な関係"""
    family_structure: str = ""
    key_relationships: list[dict] = Field(default_factory=list)

class CurrentLifeOutline(BaseModel):
    """現在の生活の輪郭"""
    daily_routine: str = ""
    weekly_schedule: list[dict] = Field(default_factory=list)
    living_situation: str = ""

class DreamTimeline(BaseModel):
    """夢の時系列"""
    childhood_dream: str = ""
    current_dream: str = ""
    dream_origin: str = Field("", description="夢の根にある何か（1文）")
    timeline: list[dict] = Field(default_factory=list)

class VoiceFingerprint(BaseModel):
    """言語的指紋"""
    first_person: str = Field("", description="一人称")
    speech_patterns: list[str] = Field(default_factory=list, description="口癖")
    sentence_endings: list[str] = Field(default_factory=list, description="文末表現")
    kanji_hiragana_tendency: str = ""
    avoided_words: list[str] = Field(default_factory=list, description="避ける語彙")

class ValuesCore(BaseModel):
    """価値観の核"""
    most_important: str = ""
    absolutely_unforgivable: str = ""
    pride: str = ""
    shame: str = ""

class Secret(BaseModel):
    """秘密"""
    public_secrets: list[str] = Field(default_factory=list)
    private_secrets: list[str] = Field(default_factory=list, description="日記にも書かないかもしれないこと")

class RelationshipEntry(BaseModel):
    """関係性ネットワークの一人分"""
    name: str
    relationship: str
    quality: str = Field("", description="好き/苦手/複雑 等")
    brief_note: str = ""

class MacroProfile(BaseModel):
    """マクロプロフィール（Phase A-1出力、v10 §3.1準拠）"""
    basic_info: BasicInfo
    social_position: SocialPosition = Field(default_factory=SocialPosition)
    family_and_intimacy: FamilyAndIntimacy = Field(default_factory=FamilyAndIntimacy)
    current_life_outline: CurrentLifeOutline = Field(default_factory=CurrentLifeOutline)
    dream_timeline: DreamTimeline = Field(default_factory=DreamTimeline)
    voice_fingerprint: VoiceFingerprint = Field(default_factory=VoiceFingerprint)
    values_core: ValuesCore = Field(default_factory=ValuesCore)
    secrets: Secret = Field(default_factory=Secret)
    relationship_network: list[RelationshipEntry] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# Phase A-2: ミクロパラメータ（52パラメータ）
# ═══════════════════════════════════════════════════════════════

class ParameterEntry(BaseModel):
    """1パラメータ分のエントリ"""
    id: int
    name: str
    name_en: str = ""
    value: float = Field(..., ge=1.0, le=5.0, description="1-5の連続値")
    natural_language: str = Field("", description="自然言語での記述")
    biological_basis: str = Field("", description="生物学的基盤（参考情報）")

class MicroParameters(BaseModel):
    """ミクロパラメータ（Phase A-2出力, v10 §3.3準拠）"""
    temperament: list[ParameterEntry] = Field(default_factory=list, description="気質23個")
    personality: list[ParameterEntry] = Field(default_factory=list, description="性格27個")
    other_cognition: list[ParameterEntry] = Field(default_factory=list, description="対他者認知2個")
    
    # 規範層（v10 §3.4）
    schwartz_values: dict[str, str] = Field(default_factory=dict, description="Schwartz 19価値 strong/medium/weak")
    moral_foundations: dict[str, str] = Field(default_factory=dict, description="道徳基盤")
    ideal_self: str = Field("", description="理想自己")
    ought_self: str = Field("", description="義務自己")
    goals: list[str] = Field(default_factory=list, description="目標リスト")
    
    # 自動導出の認知パラメータ
    learning_rate_alpha: float = Field(0.5, description="学習率α")
    emotional_inertia: float = Field(0.5, description="感情慣性")
    rpe_sensitivity: float = Field(0.5, description="RPE感受性")
    decay_lambda: dict[str, float] = Field(default_factory=dict, description="減衰係数λ（V/A/D各次元）")


# ═══════════════════════════════════════════════════════════════
# Phase A-3: 自伝的エピソード
# ═══════════════════════════════════════════════════════════════

class EpisodeMetadata(BaseModel):
    """エピソードのメタデータ"""
    life_period: str = Field(..., description="childhood/adolescence/young_adult/adult等")
    category: str = Field(..., description="redemption/contamination/ambivalent/loss/dream_origin等")
    involved_others: list[str] = Field(default_factory=list)
    connected_to: dict = Field(default_factory=dict, description="values/fears/dreamsとの接続")
    unresolved: bool = False

class AutobiographicalEpisode(BaseModel):
    """1つの自伝的エピソード（v10 §2.1.3準拠）"""
    id: str = Field(..., description="ep_001形式")
    narrative: str = Field(..., description="200-400字のnarrative")
    metadata: EpisodeMetadata

class AutobiographicalEpisodes(BaseModel):
    """自伝的エピソードDB（Phase A-3出力）"""
    episodes: list[AutobiographicalEpisode] = Field(default_factory=list, min_length=5, max_length=8)


# ═══════════════════════════════════════════════════════════════
# Phase D: 週間イベントストア
# ═══════════════════════════════════════════════════════════════

class WorldContext(BaseModel):
    """世界設定"""
    name: str = ""
    description: str = ""
    time_period: str = ""
    genre: str = ""

class SupportingCharacter(BaseModel):
    """周囲の人物"""
    name: str
    role: str = ""
    relationship_to_protagonist: str = ""
    brief_profile: str = ""
    own_small_want: str = Field("", description="その人自身の小さな欲求")

class NarrativeArc(BaseModel):
    """物語アーク設計"""
    type: str = Field("", description="Vonnegut型アーク名")
    description: str = ""
    day5_climax_design: str = ""
    foreshadowing_plan: list[dict] = Field(default_factory=list)
    recurring_motifs: list[str] = Field(default_factory=list)
    day6_aftermath_direction: str = ""
    day7_convergence_direction: str = ""

class Event(BaseModel):
    """1イベント（v10 §2.5, v2 §6.6.6準拠）"""
    id: str = Field(..., description="evt_001形式")
    day: int = Field(..., ge=1, le=7)
    time_slot: str = Field(..., description="morning/late_morning/noon/afternoon/evening/night/late_night")
    known_to_protagonist: bool
    source: Optional[str] = Field(None, description="routine/prior_appointment/protagonist_plan")
    expectedness: str = Field(..., description="low/medium/high")
    content: str = Field(..., description="3-5文の具体的記述")
    involved_characters: list[str] = Field(default_factory=list)
    meaning_to_character: str = Field(..., description="1-3文、なぜこのキャラに意味を持つか")
    narrative_arc_role: str = Field(..., description="day5_foreshadowing/previous_day_callback/daily_rhythm/standalone_ripple")
    conflict_type: Optional[str] = None
    connected_episode_id: Optional[str] = None
    connected_values: list[str] = Field(default_factory=list)

class ConflictIntensityArc(BaseModel):
    """葛藤強度アーク"""
    day_1: str = "weak"
    day_2: str = "weak_to_medium"
    day_3: str = "medium"
    day_4: str = "medium_to_strong"
    day_5: str = "strong"
    day_6: str = "aftermath"
    day_7: str = "convergence"

class WeeklyEventsStore(BaseModel):
    """週間イベントストア（Phase D出力）"""
    world_context: WorldContext = Field(default_factory=WorldContext)
    supporting_characters: list[SupportingCharacter] = Field(default_factory=list)
    narrative_arc: NarrativeArc = Field(default_factory=NarrativeArc)
    conflict_intensity_arc: ConflictIntensityArc = Field(default_factory=ConflictIntensityArc)
    events: list[Event] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# 脚本パッケージ統合
# ═══════════════════════════════════════════════════════════════

class PackageMetadata(BaseModel):
    """パッケージメタデータ"""
    version: str = "2.0"
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    generator: str = "script-ai-app v2"
    upstream_spec: str = "specification_v10.md"
    total_llm_calls: int = 0
    total_cost_usd: float = 0.0

class CharacterPackage(BaseModel):
    """脚本パッケージ全体（v2 §9.1準拠）"""
    metadata: PackageMetadata = Field(default_factory=PackageMetadata)
    concept_package: Optional[ConceptPackage] = None
    macro_profile: Optional[MacroProfile] = None
    micro_parameters: Optional[MicroParameters] = None
    autobiographical_episodes: Optional[AutobiographicalEpisodes] = None
    weekly_events_store: Optional[WeeklyEventsStore] = None
    audit_report: dict = Field(default_factory=dict)
