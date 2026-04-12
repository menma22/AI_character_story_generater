"""
設定管理モジュール
環境変数・モデル設定・品質プロファイルを一元管理する
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pathlib import Path

# .envファイルの読み込み
load_dotenv(Path(__file__).parent.parent / ".env")


# ─── LLM モデル設定 ─────────────────────────────────────────

class LLMModels:
    """使用するLLMモデルの定義"""
    # Anthropic
    OPUS = "claude-opus-4-6"
    SONNET = "claude-sonnet-4-6"
    
    # Google AI Studio
    GEMINI_2_5_PRO = "models/gemini-2.5-pro"
    GEMINI_2_0_FLASH = "models/gemini-2.0-flash"


# ─── API キー ────────────────────────────────────────────────

class APIKeys:
    ANTHROPIC = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_AI = os.getenv("GOOGLE_AI_API_KEY", "")


# ─── 品質プロファイル ─────────────────────────────────────────

@dataclass
class EvaluationProfile:
    """品質評価プロファイル（v2仕様 §8.9.2準拠）"""
    name: str
    director_self_critique_max_iterations: int
    schema_validator_enabled: bool = True           # 常にTrue
    consistency_checker_enabled: bool = False
    bias_auditor_enabled: bool = False
    bias_auditor_phases: list = field(default_factory=list)
    interestingness_evaluator_enabled: bool = False
    event_metadata_auditor_enabled: bool = False
    distribution_validator_enabled: bool = True     # ルールベース、常にTrue推奨
    narrative_connection_auditor_enabled: bool = False
    worker_regeneration_max_iterations: int = 1
    min_research_searches: int = 3                 # Creative Directorが批評前に必須の検索回数
    director_tier: str = "opus"                    # "opus" | "sonnet" | "gemini"
    worker_tier: str = "sonnet"                    # "opus" | "sonnet" | "gemini"


PROFILES = {
    "high_quality": EvaluationProfile(
        name="high_quality",
        director_self_critique_max_iterations=10,
        consistency_checker_enabled=True,
        bias_auditor_enabled=True,
        bias_auditor_phases=["A-3"],
        interestingness_evaluator_enabled=True,
        event_metadata_auditor_enabled=True,
        narrative_connection_auditor_enabled=True,
        worker_regeneration_max_iterations=4,
        min_research_searches=5,
    ),
    "standard": EvaluationProfile(
        name="standard",
        director_self_critique_max_iterations=8,
        consistency_checker_enabled=True,
        bias_auditor_enabled=True,
        bias_auditor_phases=["A-3"],
        interestingness_evaluator_enabled=False,
        event_metadata_auditor_enabled=True,
        narrative_connection_auditor_enabled=True,
        worker_regeneration_max_iterations=3,
        director_tier="sonnet",
        worker_tier="sonnet",
    ),
    "fast": EvaluationProfile(
        name="fast",
        director_self_critique_max_iterations=2,
        consistency_checker_enabled=False,
        bias_auditor_enabled=True,
        bias_auditor_phases=["A-3"],
        interestingness_evaluator_enabled=False,
        event_metadata_auditor_enabled=True,
        narrative_connection_auditor_enabled=False,
        worker_regeneration_max_iterations=2,
        min_research_searches=2,
        director_tier="sonnet",
        worker_tier="gemini",
    ),
    "draft": EvaluationProfile(
        name="draft",
        director_self_critique_max_iterations=1,
        consistency_checker_enabled=False,
        bias_auditor_enabled=False,
        bias_auditor_phases=[],
        interestingness_evaluator_enabled=False,
        event_metadata_auditor_enabled=False,
        narrative_connection_auditor_enabled=False,
        worker_regeneration_max_iterations=2,
        min_research_searches=1,
        director_tier="sonnet",
        worker_tier="gemini",
    ),
}


# ─── アプリケーション設定 ─────────────────────────────────────

class AppConfig:
    """アプリケーション全体の設定"""
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8001"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEFAULT_PROFILE = os.getenv("DEFAULT_PROFILE", "draft")
    
    # ストレージパス
    BASE_DIR = Path(__file__).parent
    STORAGE_DIR = BASE_DIR / "storage" / "character_packages"
    SCHEMAS_DIR = BASE_DIR / "schemas"
    REFERENCE_DIR = BASE_DIR / "reference"
    
    @classmethod
    def get_profile(cls) -> EvaluationProfile:
        return PROFILES.get(cls.DEFAULT_PROFILE, PROFILES["draft"])
