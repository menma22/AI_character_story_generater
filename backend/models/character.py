"""
データモデル定義（Pydantic v2）
specification_v10.md および script_ai_app_specification_v2.md に基づく
脚本パッケージの全データ構造を定義する
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator
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

class CapabilitiesHints(BaseModel):
    """所持品・能力の方向性ヒント（Creative Director が設計、Phase D capabilities生成で参照）"""
    key_possessions_hint: str = Field("", description="キャラクターが持ち歩くべき重要なアイテムの方向性（1-3文）")
    core_abilities_hint: str = Field("", description="物語に重要な能力・スキルの方向性（1-3文）")
    signature_actions_hint: str = Field("", description="このキャラクターならではの行動パターンの方向性（1-3文）")

class ConceptPackage(BaseModel):
    """Creative Director の出力パッケージ（v2 §4.7 完全準拠）"""
    character_concept: str = Field("", description="キャラクター設定の大まかな概要（500-1000字の濃密な概念記述）")
    story_outline: str = Field("", description="物語設定の大まかな概要（500-1000字の濃密な概念記述）")
    narrative_theme: str = Field("", description="物語的テーマ（1-2文）")
    interestingness_hooks: list[str] = Field(default_factory=list, description="面白さのフック（3-5個）")
    genre_and_world: str = Field("", description="ジャンルと世界観の方向性")
    raw_prose_markdown: str = Field("", description="コンセプト・あらすじ等のMarkdown全文")
    reference_stories: list[ReferenceStory] = Field(default_factory=list, description="参考となる既存物語")
    critical_design_notes: list[str] = Field(default_factory=list, description="下流への設計上の指示")
    psychological_hints: PsychologicalHints = Field(default_factory=PsychologicalHints)
    capabilities_hints: CapabilitiesHints = Field(default_factory=CapabilitiesHints)
    iteration_count: int = Field(0, description="Self-Critique反復回数")
    self_critique_history: list[dict] = Field(default_factory=list)
    verdict: str = Field("pass", description="最終判定")

    @field_validator("character_concept", "story_outline")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("このフィールドは空にできません。生成に失敗した可能性があります。")
        return v


# ═══════════════════════════════════════════════════════════════
# Phase A-1: マクロプロフィール
# ═══════════════════════════════════════════════════════════════

class BasicInfo(BaseModel):
    """基本情報"""
    name: str = ""
    age: int = 30
    gender: str = ""
    appearance: str = ""
    occupation: str = ""

    @field_validator("age", mode="before")
    @classmethod
    def parse_age(cls, v):
        if isinstance(v, str):
            if v.strip() == "":
                return 30
            try:
                return int(v)
            except ValueError:
                # 数字が含まれている場合は抽出を試みる
                import re
                nums = re.findall(r"\d+", v)
                if nums:
                    return int(nums[0])
                return 30
        return v

class SocialPosition(BaseModel):
    """社会的位置（v2 §6.3.4準拠）"""
    occupation_detail: str = ""
    workplace_or_org: str = Field("", description="職場・所属組織（具体名+規模感）")
    economic_status: str = ""
    living_area: str = ""
    social_class: str = Field("", description="社会階層・出自")

class FamilyAndIntimacy(BaseModel):
    """家族・親密な関係"""
    family_structure: str = ""
    key_relationships: list[dict] = Field(default_factory=list)

class CurrentLifeOutline(BaseModel):
    """現在の生活の輪郭（v2 §6.3.4準拠）"""
    daily_routine: str = ""
    typical_weekday: str = Field("", description="典型的な平日の概形（1パラグラフ）")
    typical_weekend: str = Field("", description="典型的な週末の概形（1パラグラフ）")
    habits_routines: list[str] = Field(default_factory=list, description="習慣・ルーティン（3-5個）")
    hobbies_leisure: list[str] = Field(default_factory=list, description="趣味・余暇の使い方（2-3個）")
    weekly_schedule: list[dict] = Field(default_factory=list)
    living_situation: str = ""

class DreamTimeline(BaseModel):
    """夢の時系列（v2 §6.3.4準拠）"""
    childhood_dream: str = ""
    late_teens_dream: str = Field("", description="10代後半の夢")
    setback_or_turning_point: str = Field("", description="挫折・転機（いつ、何が起きてどう変わったか）")
    current_dream: str = ""
    long_term_dream: str = Field("", description="長期的な夢・目標")
    mid_term_dream: str = Field("", description="中期的な目標")
    short_term_dream: str = Field("", description="短期的な目標")
    dream_origin: str = Field("", description="夢の根にある何か（1文、価値観との接続）")
    timeline: list[dict] = Field(default_factory=list)

class VoiceFingerprint(BaseModel):
    """言語的指紋（v2 §6.3.4準拠）"""
    first_person: str = Field("", description="一人称")
    second_person_by_context: dict[str, str] = Field(default_factory=dict, description="状況別二人称（to_intimate/to_superior/to_stranger）")
    speech_patterns: list[str] = Field(default_factory=list, description="口癖")
    catchphrases: list[str] = Field(default_factory=list, description="口癖（実際のフレーズ、3-5個）")
    sentence_endings: list[str] = Field(default_factory=list, description="文末表現")
    kanji_hiragana_tendency: str = ""
    emoji_usage: str = Field("", description="絵文字・記号の使用傾向（使う/使わない/限定的）")
    self_questioning_frequency: str = Field("", description="自問形式の頻度（よく自問する/しない）")
    metaphor_irony_frequency: str = Field("", description="比喩・反語の頻度（よく使う/控えめ）")
    avoided_words: list[str] = Field(default_factory=list, description="避ける語彙")

class SpeechCharacteristics(BaseModel):
    """喋り方の特徴"""
    concrete_features: VoiceFingerprint = Field(default_factory=VoiceFingerprint)
    abstract_feel: str = Field("", description="喋り方の抽象的な雰囲気（例：『壊れかけのラジオのように、途切れ途切れで感情が滲む』）")
    conversation_style: str = Field("", description="会話のテンポ・間の取り方・話題の転がし方")
    emotional_expression_tendency: str = Field("", description="感情をどう言語化するか（直接的/婉曲/沈黙で示す等）")

class DiaryWritingAtmosphere(BaseModel):
    """日記の書き方の雰囲気"""
    tone: str = Field("", description="日記全体のトーン（内省的/事務的/感情的/詩的/報告書的等）")
    structure_tendency: str = Field("", description="日記の構成傾向（時系列/感情起点/断片的等）")
    introspection_depth: str = Field("", description="内省の深さとスタイル")
    what_gets_written: str = Field("", description="何を書いて何を書かないかの方針")
    what_gets_omitted: str = Field("", description="意図的に省略・隠す傾向があるもの")
    raw_atmosphere_description: str = Field("", description="この人の日記から漂う空気感（2-3文の散文記述）")

class LinguisticExpression(BaseModel):
    """キャラクターの言語的表現方法（Day 0独立生成アイテム）"""
    speech_characteristics: SpeechCharacteristics = Field(default_factory=SpeechCharacteristics)
    diary_writing_atmosphere: DiaryWritingAtmosphere = Field(default_factory=DiaryWritingAtmosphere)
    raw_prose_markdown: str = Field("", description="言語的表現方法の全体記述Markdown")

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

class RelationshipNetwork(BaseModel):
    """関係性ネットワーク全体 (A-1 Worker出力用)"""
    relationships: list[RelationshipEntry] = Field(default_factory=list)

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
    raw_prose_markdown: str = Field("", description="マクロプロフィール全体のMarkdown記述")


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

class ParameterList(BaseModel):
    """パラメータ群 (A-2 Worker一括出力用)"""
    parameters: list[ParameterEntry] = Field(default_factory=list)

class NormativeLayer(BaseModel):
    """規範層 (A-2 Worker出力用)"""
    schwartz_values: dict[str, str] = Field(default_factory=dict)
    moral_foundations: dict[str, str] = Field(default_factory=dict)
    ideal_self: str = ""
    ought_self: str = ""
    goals: list[str] = Field(default_factory=list)

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
# Phase D: 所持品・能力・可能行動
# ═══════════════════════════════════════════════════════════════

class PossessedItem(BaseModel):
    """所持品"""
    name: str = ""
    description: str = Field("", description="アイテムの説明（見た目・用途）")
    always_carried: bool = Field(False, description="常時持ち歩きか")
    emotional_significance: str = Field("", description="キャラクターにとっての感情的意味")

class CharacterAbility(BaseModel):
    """能力・スキル"""
    name: str = ""
    description: str = Field("", description="能力の説明")
    proficiency: str = Field("medium", description="novice/medium/expert")
    origin: str = Field("", description="どこで身につけたか")

class AvailableAction(BaseModel):
    """能動的に取れるアクション"""
    action: str = ""
    context: str = Field("", description="どんな場面で使えるか")
    prerequisites: str = Field("", description="前提条件")

class CharacterCapabilities(BaseModel):
    """所持品・能力・可能行動（Phase D生成、Creative Director方針準拠）"""
    possessions: list[PossessedItem] = Field(default_factory=list)
    abilities: list[CharacterAbility] = Field(default_factory=list)
    available_actions: list[AvailableAction] = Field(default_factory=list)
    raw_text: str = Field("", description="生成時の自然言語テキスト")


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

class StoryCompositionPreferences(BaseModel):
    """ユーザー指定の物語構成プリファレンス（Human in the Loop）

    各フィールドはOptional。未指定の場合はAIが自律判断する。
    選択肢は knowledge/fact/story_composition_theory.md の文献ベースカタログに準拠。
    """
    narrative_structure: Optional[str] = Field(None, description="物語構造: three_act, kishotenketsu, heros_journey, story_circle, freytag, save_the_cat, fichtean, in_medias_res, circular, episodic, parallel, nonlinear")
    emotional_tone: Optional[str] = Field(None, description="感情トーン: heartwarming, bittersweet, comedic, tragic, melancholic, suspenseful, nostalgic, serene, hopeful, eerie, passionate, ironic")
    character_arc: Optional[str] = Field(None, description="キャラクターアーク: positive_change, flat, disillusionment, fall, corruption, coming_of_age, redemption, transformation")
    theme_weight: Optional[str] = Field(None, description="テーマの重さ: escapist, slice_of_life, emotional, social, psychological, philosophical, spiritual, allegorical")
    climax_structure: Optional[str] = Field(None, description="クライマックス構造: single, multiple_peaks, gradual, wave, back_loaded, anti_climax, front_loaded, symmetric")
    genre: Optional[str] = Field(None, description="ジャンル: coming_of_age, healing, workplace, mystery, romance, family, friendship, adventure, magical_realism, introspection, seasonal, survival")
    pacing: Optional[str] = Field(None, description="ペーシング: slow_burn, fast_paced, rhythmic, pulse, accelerating, decelerating, even, breath")
    narrative_voice: Optional[str] = Field(None, description="語り口: introspective, observational, emotional, detached, stream_of_consciousness, humorous, poetic, conversational, fragmentary, unreliable")
    free_notes: Optional[str] = Field(None, description="ユーザーの自由記述による追加指示")


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
    linguistic_expression: Optional[LinguisticExpression] = None
    micro_parameters: Optional[MicroParameters] = None
    autobiographical_episodes: Optional[AutobiographicalEpisodes] = None
    weekly_events_store: Optional[WeeklyEventsStore] = None
    character_capabilities: Optional[CharacterCapabilities] = None
    composition_preferences: Optional[StoryCompositionPreferences] = None
    audit_report: dict = Field(default_factory=dict)
