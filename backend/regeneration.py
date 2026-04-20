"""
アーティファクト個別再生成モジュール
各フェーズオーケストレータを直接呼び出し、特定のアーティファクトのみを再生成する。
MasterOrchestratorをバイパスすることで、既存パイプラインに影響を与えない。
"""

import json
import logging
from typing import Optional

from backend.config import EvaluationProfile
from backend.models.character import CharacterPackage

logger = logging.getLogger(__name__)

# ─── アーティファクト定義 ──────────────────────────────────────

ARTIFACT_TO_PHASE = {
    "concept_package": "creative_director",
    "macro_profile": "phase_a1",
    "linguistic_expression": "phase_a1",  # macro_profileと同時再生成
    "micro_parameters": "phase_a2",
    "autobiographical_episodes": "phase_a3",
    "weekly_events_store": "phase_d",
    "daily_logs": "daily_loop",
}

ARTIFACT_DEPENDENTS = {
    "concept_package": ["macro_profile", "linguistic_expression", "micro_parameters", "autobiographical_episodes", "weekly_events_store", "daily_logs"],
    "macro_profile": ["micro_parameters", "autobiographical_episodes", "weekly_events_store", "daily_logs"],
    "linguistic_expression": ["daily_logs"],
    "micro_parameters": ["autobiographical_episodes", "weekly_events_store", "daily_logs"],
    "autobiographical_episodes": ["weekly_events_store", "daily_logs"],
    "weekly_events_store": ["daily_logs"],
    "daily_logs": [],
}

ARTIFACT_LABELS = {
    "concept_package": "コンセプト",
    "macro_profile": "マクロプロフィール + 言語的表現",
    "linguistic_expression": "マクロプロフィール + 言語的表現",
    "micro_parameters": "ミクロパラメータ",
    "autobiographical_episodes": "自伝的エピソード",
    "weekly_events_store": "イベント列",
    "daily_logs": "日記 (7日分)",
}


def get_downstream_artifacts(artifact_name: str) -> list[str]:
    """指定アーティファクトに依存する下流アーティファクトを返す"""
    return ARTIFACT_DEPENDENTS.get(artifact_name, [])


def build_regeneration_context(original_json: str, user_instructions: str) -> str:
    """再生成時にLLMに渡すコンテキスト文字列を構築する"""
    parts = [
        "\n\n═══ 【再生成モード】 ═══",
        "以下は前回の生成結果です。ユーザーの指示に従って改善してください。",
        "前回の結果と全く異なるものを作るのではなく、ユーザーの指示に沿った改善・修正を行ってください。",
        "",
        "【前回の生成結果】",
        original_json,
    ]
    if user_instructions:
        parts.extend([
            "",
            "【ユーザーからの追加指示】",
            user_instructions,
        ])
    parts.append("═══════════════════════")
    return "\n".join(parts)


async def regenerate_artifact(
    package: CharacterPackage,
    artifact_name: str,
    user_instructions: str,
    profile: EvaluationProfile,
    ws_manager=None,
    api_keys: Optional[dict] = None,
) -> CharacterPackage:
    """
    指定されたアーティファクトを再生成し、パッケージを更新して返す。

    Args:
        package: 既存のCharacterPackage
        artifact_name: 再生成対象（ARTIFACT_TO_PHASEのキー）
        user_instructions: ユーザーからの自然言語指示
        profile: 品質プロファイル
        ws_manager: WebSocket通知用

    Returns:
        更新されたCharacterPackage
    """
    if artifact_name not in ARTIFACT_TO_PHASE:
        raise ValueError(f"不明なアーティファクト: {artifact_name}")

    phase = ARTIFACT_TO_PHASE[artifact_name]
    label = ARTIFACT_LABELS.get(artifact_name, artifact_name)

    if ws_manager:
        await ws_manager.send_agent_thought(
            "Regeneration", f"「{label}」の再生成を開始します...", "thinking"
        )

    # ── 元のアーティファクトをJSON化（LLM参照用） ──
    original_artifact = getattr(package, artifact_name, None)
    if original_artifact is not None:
        if hasattr(original_artifact, "model_dump"):
            original_json = json.dumps(original_artifact.model_dump(mode="json"), ensure_ascii=False, indent=2)
        else:
            original_json = json.dumps(original_artifact, ensure_ascii=False, indent=2)
    else:
        original_json = "(前回の生成結果なし)"

    regen_context = build_regeneration_context(original_json, user_instructions)

    # ── フェーズ別再生成 ──

    if phase == "creative_director":
        await _regenerate_concept(package, regen_context, profile, ws_manager, api_keys)

    elif phase == "phase_a1":
        # macro_profile + linguistic_expression を同時再生成
        if original_artifact is not None and artifact_name == "linguistic_expression":
            # linguistic_expression指定でも、元のmacro_profileもコンテキストに含める
            mp = package.macro_profile
            if mp and hasattr(mp, "model_dump"):
                mp_json = json.dumps(mp.model_dump(mode="json"), ensure_ascii=False, indent=2)
                regen_context += f"\n\n【参考: 現在のmacro_profile】\n{mp_json}"
        await _regenerate_phase_a1(package, regen_context, profile, ws_manager, api_keys)

    elif phase == "phase_a2":
        await _regenerate_phase_a2(package, regen_context, profile, ws_manager, api_keys)

    elif phase == "phase_a3":
        await _regenerate_phase_a3(package, regen_context, profile, ws_manager, api_keys)

    elif phase == "phase_d":
        await _regenerate_phase_d(package, regen_context, profile, ws_manager, api_keys)

    elif phase == "daily_loop":
        await _regenerate_daily_loop(package, regen_context, profile, ws_manager, api_keys)

    if ws_manager:
        await ws_manager.send_agent_thought(
            "Regeneration", f"「{label}」の再生成が完了しました", "complete"
        )

    return package


# ─── フェーズ別再生成ヘルパー ──────────────────────────────────

async def _regenerate_concept(package: CharacterPackage, regen_context: str, profile: EvaluationProfile, ws_manager, api_keys: Optional[dict]):
    """Creative Directorの再生成"""
    from backend.agents.creative_director.director import CreativeDirector

    package.concept_package = None
    director = CreativeDirector(profile=profile, ws_manager=ws_manager, regeneration_context=regen_context, api_keys=api_keys)
    concept = await director.run(theme=None)
    package.concept_package = concept


async def _regenerate_phase_a1(package: CharacterPackage, regen_context: str, profile: EvaluationProfile, ws_manager, api_keys: Optional[dict]):
    """Phase A-1（macro_profile + linguistic_expression）の再生成"""
    from backend.agents.phase_a1.orchestrator import PhaseA1Orchestrator

    if not package.concept_package:
        raise ValueError("concept_packageが未生成のため、Phase A-1を再生成できません")

    package.macro_profile = None
    package.linguistic_expression = None
    orch = PhaseA1Orchestrator(
        concept=package.concept_package,
        profile=profile,
        ws_manager=ws_manager,
        regeneration_context=regen_context,
        api_keys=api_keys,
    )
    result = await orch.run()
    package.macro_profile = result.macro_profile
    package.linguistic_expression = result.linguistic_expression


async def _regenerate_phase_a2(package: CharacterPackage, regen_context: str, profile: EvaluationProfile, ws_manager, api_keys: Optional[dict]):
    """Phase A-2（micro_parameters）の再生成"""
    from backend.agents.phase_a2.orchestrator import PhaseA2Orchestrator

    if not package.concept_package or not package.macro_profile:
        raise ValueError("上流アーティファクトが未生成のため、Phase A-2を再生成できません")

    package.micro_parameters = None
    orch = PhaseA2Orchestrator(
        concept=package.concept_package,
        macro_profile=package.macro_profile,
        profile=profile,
        ws_manager=ws_manager,
        regeneration_context=regen_context,
        api_keys=api_keys,
    )
    result = await orch.run()
    package.micro_parameters = result


async def _regenerate_phase_a3(package: CharacterPackage, regen_context: str, profile: EvaluationProfile, ws_manager, api_keys: Optional[dict]):
    """Phase A-3（autobiographical_episodes）の再生成"""
    from backend.agents.phase_a3.orchestrator import PhaseA3Orchestrator

    if not package.concept_package or not package.macro_profile or not package.micro_parameters:
        raise ValueError("上流アーティファクトが未生成のため、Phase A-3を再生成できません")

    package.autobiographical_episodes = None
    orch = PhaseA3Orchestrator(
        concept=package.concept_package,
        macro_profile=package.macro_profile,
        micro_parameters=package.micro_parameters,
        profile=profile,
        ws_manager=ws_manager,
        regeneration_context=regen_context,
        api_keys=api_keys,
    )
    result = await orch.run()
    package.autobiographical_episodes = result


async def _regenerate_phase_d(package: CharacterPackage, regen_context: str, profile: EvaluationProfile, ws_manager, api_keys: Optional[dict]):
    """Phase D（weekly_events_store）の再生成"""
    from backend.agents.phase_d.orchestrator import PhaseDOrchestrator

    if not package.concept_package or not package.macro_profile or not package.micro_parameters or not package.autobiographical_episodes:
        raise ValueError("上流アーティファクトが未生成のため、Phase Dを再生成できません")

    package.weekly_events_store = None
    orch = PhaseDOrchestrator(
        concept=package.concept_package,
        macro_profile=package.macro_profile,
        micro_parameters=package.micro_parameters,
        episodes=package.autobiographical_episodes,
        profile=profile,
        ws_manager=ws_manager,
        regeneration_context=regen_context,
        api_keys=api_keys,
    )
    result = await orch.run()
    package.weekly_events_store = result


async def _regenerate_daily_loop(package: CharacterPackage, regen_context: str, profile: EvaluationProfile, ws_manager, api_keys: Optional[dict]):
    """Daily Loop（日記 7日分）の再生成"""
    from backend.agents.daily_loop.orchestrator import DailyLoopOrchestrator
    from backend.config import AppConfig
    
    if not package.weekly_events_store:
        raise ValueError("上流アーティファクトが未生成のため、日記を再生成できません")

    cname = package.macro_profile.basic_info.name if package.macro_profile and package.macro_profile.basic_info else "Unknown_Character"
    safe_name = cname.replace("/", "_").replace("\\", "_")

    from datetime import datetime
    session_id = f"diary_regen_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    import shutil
    
    # 既存の状態（記憶、ムード、ログ）を退避して、Day 1から強制的に再生成させる（バージョン管理）
    base_dir = AppConfig.STORAGE_DIR / safe_name
    backup_root = base_dir / "backups" / session_id
    backup_root.mkdir(parents=True, exist_ok=True)
    
    for sub_dir in ["daily_logs", "mood_states", "short_term_memory", "key_memories", "diaries"]:
        target = base_dir / sub_dir
        if target.exists():
            dest = backup_root / sub_dir
            logger.info(f"[_regenerate_daily_loop] Backing up {target} to {dest}")
            try:
                shutil.move(str(target), str(dest))
            except Exception as e:
                logger.error(f"[_regenerate_daily_loop] Failed to backup {sub_dir}: {e}")

    orch = DailyLoopOrchestrator(
        package=package,
        profile=profile,
        ws_manager=ws_manager,
        api_keys=api_keys,
        session_id=session_id,
        regeneration_context=regen_context
    )
    # 状態をクリア（退避）したため、run(days=7) は必ず Day 1 から開始される
    results = await orch.run(days=7)

    # 日記を保存
    save_dir = AppConfig.STORAGE_DIR / safe_name / "diaries"
    save_dir.mkdir(parents=True, exist_ok=True)

    for day_state in results:
        if day_state.diary:
            diary_path = save_dir / f"day_{day_state.day:02d}.md"
            diary_path.write_text(day_state.diary.content, encoding="utf-8")
