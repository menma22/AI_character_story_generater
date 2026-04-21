"""
FastAPI メインエントリポイント
脚本AI + 日記生成ワークフロー統合アプリケーション
"""

import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from backend.config import AppConfig, PROFILES
from backend.websocket.handler import manager
from backend.tools.llm_api import token_tracker

# ロギング設定
log_file = Path(__file__).parent.parent / "app.log"
logging.basicConfig(
    level=getattr(logging, AppConfig.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# FastAPIアプリ
app = FastAPI(
    title="AIキャラクターストーリー生成システム",
    description="specification_v10.md準拠 - 脚本AI + 日記生成ワークフロー",
    version="2.0.0"
)

# 静的ファイル配信
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# ─── HTTP エンドポイント ──────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """フロントエンドのindex.htmlを返す"""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>AIキャラクターストーリー生成システム</h1><p>frontend/index.html が見つかりません</p>")


@app.get("/api/profiles")
async def get_profiles():
    """利用可能な品質プロファイル一覧"""
    return {
        name: {
            "name": p.name,
            "director_iterations": p.director_self_critique_max_iterations,
            "evaluators_enabled": sum([
                p.consistency_checker_enabled,
                p.bias_auditor_enabled,
                p.interestingness_evaluator_enabled,
                p.event_metadata_auditor_enabled,
                p.narrative_connection_auditor_enabled,
            ]),
        }
        for name, p in PROFILES.items()
    }


@app.get("/api/cost")
async def get_cost():
    """現在のトークン消費とコスト情報"""
    return token_tracker.summary()


@app.get("/api/packages")
async def list_packages():
    """生成済み脚本パッケージ一覧（完了・未完了の両方を含む）"""
    storage = AppConfig.STORAGE_DIR
    packages = []
    if storage.exists():
        for d in sorted(storage.iterdir(), reverse=True):
            if d.is_dir():
                pkg_file = d / "package.json"
                chk_file = d / "checkpoint.json"

                # 完了パッケージ（package.json あり）
                if pkg_file.exists():
                    try:
                        data = json.loads(pkg_file.read_text(encoding="utf-8"))
                        packages.append({
                            "name": d.name,
                            "status": "complete",
                            "checkpoint_phase": "complete",
                            "generated_at": data.get("metadata", {}).get("generated_at", ""),
                            "character_name": data.get("macro_profile", {}).get("basic_info", {}).get("name", "不明"),
                        })
                    except Exception:
                        packages.append({"name": d.name, "status": "complete", "error": "読み込みエラー"})

                # 未完了パッケージ（checkpoint.json のみ）
                elif chk_file.exists():
                    try:
                        chk_data = json.loads(chk_file.read_text(encoding="utf-8"))

                        # チェックポイントフェーズを判定
                        checkpoint_phase = "unknown"
                        if chk_data.get("weekly_events_store"):
                            checkpoint_phase = "phase_d"
                        elif chk_data.get("autobiographical_episodes"):
                            checkpoint_phase = "phase_a3"
                        elif chk_data.get("micro_parameters"):
                            checkpoint_phase = "phase_a2"
                        elif chk_data.get("macro_profile"):
                            checkpoint_phase = "phase_a1"
                        elif chk_data.get("concept_package"):
                            checkpoint_phase = "creative_director"

                        # キャラクター名取得（未生成の場合は"未生成"）
                        char_name = "未生成"
                        if chk_data.get("macro_profile", {}).get("basic_info", {}).get("name"):
                            char_name = chk_data["macro_profile"]["basic_info"]["name"]

                        generated_at = chk_data.get("metadata", {}).get("generated_at", "")

                        packages.append({
                            "name": d.name,
                            "status": "incomplete",
                            "checkpoint_phase": checkpoint_phase,
                            "generated_at": generated_at,
                            "character_name": char_name,
                        })
                    except Exception:
                        packages.append({"name": d.name, "status": "incomplete", "error": "チェックポイント読み込みエラー"})

    return {"packages": packages}


@app.get("/api/packages/{package_name}")
async def get_package(package_name: str):
    """特定の脚本パッケージを取得"""
    base_dir = AppConfig.STORAGE_DIR / package_name
    pkg_path = base_dir / "package.json"
    if pkg_path.exists():
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
        
        # 日記データも読み込む (最新セッションがあればそれを優先)
        diaries = []
        sessions_dir = base_dir / "sessions"
        latest_diaries_dir = base_dir / "diaries"
        
        if sessions_dir.exists():
            session_folders = sorted([d for d in sessions_dir.iterdir() if d.is_dir()])
            if session_folders:
                latest_session_dir = session_folders[-1]
                if (latest_session_dir / "diaries").exists():
                    latest_diaries_dir = latest_session_dir / "diaries"
        
        if latest_diaries_dir.exists():
            for d in sorted(latest_diaries_dir.glob("day_*.md")):
                try:
                    day_num = int(d.stem.split("_")[1])
                    content = d.read_text(encoding="utf-8")
                    diaries.append({"day": day_num, "content": content})
                except Exception:
                    pass
        data["diaries"] = diaries
        return data
    return {"error": "パッケージが見つかりません"}


@app.get("/api/debug/thoughts")
async def get_debug_thoughts():
    """現在の接続マネージャー内の思考ログ履歴を取得"""
    return {
        "count": len(manager.thought_history),
        "history": manager.thought_history
    }


# ─── WebSocket エンドポイント ─────────────────────────────────

# クライアントごとに実行中のタスクを保持（キャンセル機能のため）
ws_active_tasks = {}
# 現在実行中のMasterOrchestratorインスタンスへの参照（HIL応答のため）
active_orchestrator = None
# 日記生成中のオーケストレーターを管理（中断用）
active_diary_orchestrators = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """メインWebSocket接続"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_ws_message(data, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_ws_message(data: dict, websocket: WebSocket):
    """WebSocketメッセージの処理"""
    global active_orchestrator
    action = data.get("action", "")
    logger.debug(f"[WS] Received action: {action} with data: {data}")
    
    if action == "generate_character":
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        theme = data.get("theme", None)
        evaluators_override = data.get("evaluators_override", {})
        api_keys = data.get("api_keys", {})
        composition_preferences = data.get("composition_preferences", None)
        task = asyncio.create_task(run_character_generation(profile_name, theme, evaluators_override, api_keys, composition_preferences))
        ws_active_tasks[id(websocket)] = task
        task.add_done_callback(lambda t: ws_active_tasks.pop(id(websocket), None))
    
    elif action == "resume_generation":
        character_name = data.get("character_name", "")
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        evaluators_override = data.get("evaluators_override", {})
        api_keys = data.get("api_keys", {})
        task = asyncio.create_task(resume_character_generation(character_name, profile_name, evaluators_override, api_keys))
        ws_active_tasks[id(websocket)] = task
        task.add_done_callback(lambda t: ws_active_tasks.pop(id(websocket), None))
    
    elif action == "generate_diary":
        package_name = data.get("package_name", "")
        days = data.get("days", 7)
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        api_keys = data.get("api_keys", {})
        instructions = data.get("instructions", "")
        asyncio.create_task(run_diary_generation(package_name, days, profile_name, api_keys, instructions))
    
    elif action == "cancel_diary":
        package_name = data.get("package_name", "")
        if package_name in active_diary_orchestrators:
            active_diary_orchestrators[package_name].cancel()
            await websocket.send_json({"type": "info", "content": f"パッケージ {package_name} の日記生成を中断します。"})
        else:
            await websocket.send_json({"type": "error", "content": "実行中の日記生成プロセスが見つかりません。"})
            
    elif action == "cancel_character_generation":
        task_id = id(websocket)
        package_name = None
        if active_orchestrator:
            active_orchestrator.cancel()
        if task_id in ws_active_tasks:
            ws_active_tasks[task_id].cancel()
            ws_active_tasks.pop(task_id, None)
        await websocket.send_json({
            "type": "generation_cancelled",
            "message": "生成が中断されました。"
        })

    elif action == "regenerate_artifact":
        package_name = data.get("package_name", "")
        artifact_name = data.get("artifact_name", "")
        instructions = data.get("instructions", "")
        cascade = data.get("cascade", False)
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        api_keys = data.get("api_keys", {})
        # 日記の場合は専用フローに転送（UI統合のため）
        if artifact_name == "daily_logs":
            asyncio.create_task(run_diary_generation(package_name, 7, profile_name, api_keys, instructions))
        else:
            asyncio.create_task(run_artifact_regeneration(package_name, artifact_name, instructions, cascade, profile_name, api_keys))

    elif action == "save_artifact_edit":
        package_name = data.get("package_name", "")
        artifact_name = data.get("artifact_name", "")
        edited_data = data.get("data", {})
        asyncio.create_task(save_manual_edit(package_name, artifact_name, edited_data))

    elif action == "approve_concept":
        if active_orchestrator: active_orchestrator.handle_review_response("approve")
    elif action == "revise_concept":
        if active_orchestrator: active_orchestrator.handle_review_response("revise", feedback=data.get("feedback", ""))
    elif action == "edit_concept_direct":
        if active_orchestrator: active_orchestrator.handle_review_response("edit", edited_concept=data.get("concept_package", {}))
    elif action == "get_status":
        await websocket.send_json({"type": "status", "cost": token_tracker.summary()})
    else:
        await websocket.send_json({"type": "error", "content": f"Unknown action: {action}"})


async def run_character_generation(profile_name: str, theme: str = None, evaluators_override: dict = None, api_keys: dict = None, composition_preferences: dict = None):
    try:
        from backend.agents.master_orchestrator.orchestrator import MasterOrchestrator
        from backend.models.character import StoryCompositionPreferences
        import dataclasses
        base_profile = PROFILES.get(profile_name, PROFILES["draft"])
        target_profile = dataclasses.replace(base_profile, **{k: v for k, v in (evaluators_override or {}).items() if hasattr(base_profile, k)})
        
        prefs = StoryCompositionPreferences(**composition_preferences) if composition_preferences else None
        session_id = f"SID_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await manager.send_progress("init", 0.0, "キャラクター生成を開始します...")
        
        global active_orchestrator
        orchestrator = MasterOrchestrator(profile=target_profile, ws_manager=manager, session_id=session_id, api_keys=api_keys, composition_preferences=prefs)
        active_orchestrator = orchestrator
        package = await orchestrator.run(theme=theme)
        await _finalize_character_generation(package)
    except Exception as e:
        logger.error(f"Character generation failed: {e}", exc_info=True)
        await manager.send_error(f"キャラクター生成エラー: {str(e)}")
    finally:
        active_orchestrator = None

async def resume_character_generation(character_name: str, profile_name: str, evaluators_override: dict = None, api_keys: dict = None):
    try:
        from backend.agents.master_orchestrator.orchestrator import MasterOrchestrator
        from backend.storage.md_storage import load_checkpoint
        import dataclasses
        package = await load_checkpoint(character_name)
        if not package:
            await manager.send_error(f"チェックポイントが見つかりませんでした: {character_name}")
            return
        base_profile = PROFILES.get(profile_name, PROFILES["draft"])
        target_profile = dataclasses.replace(base_profile, **{k: v for k, v in (evaluators_override or {}).items() if hasattr(base_profile, k)})
        
        global active_orchestrator
        orchestrator = MasterOrchestrator(profile=target_profile, ws_manager=manager, existing_package=package, session_id=character_name, api_keys=api_keys)
        active_orchestrator = orchestrator
        package = await orchestrator.run()
        await _finalize_character_generation(package)
    except Exception as e:
        logger.error(f"Resume failed: {e}", exc_info=True)
        await manager.send_error(f"再開エラー: {str(e)}")
    finally:
        active_orchestrator = None

async def _finalize_character_generation(package):
    from backend.storage.md_storage import safe_name
    char_name = package.macro_profile.basic_info.name if package.macro_profile and package.macro_profile.basic_info else "unknown"
    save_dir = AppConfig.STORAGE_DIR / safe_name(char_name)
    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / "package.json").write_text(json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    await manager.send_progress("complete", 1.0, f"「{char_name}」の生成が完了しました")
    from backend.storage.md_storage import save_versioned_package
    await save_versioned_package(char_name, package, manager.thought_history)
    await manager.send_phase_result("complete", {"package_name": save_dir.name, "character_name": char_name, "cost": token_tracker.summary()})

async def run_diary_generation(package_name: str, days: int = 7, profile_name: str = None, api_keys: dict = None, instructions: str = None):
    """日記生成プロセスを実行"""
    from backend.agents.daily_loop.orchestrator import DailyLoopOrchestrator
    from backend.models.character import CharacterPackage
    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    if not pkg_path.exists():
        await manager.send_error(f"パッケージが見つかりません: {package_name}")
        return
    try:
        package = CharacterPackage(**json.loads(pkg_path.read_text(encoding="utf-8")))
        char_name = package.macro_profile.basic_info.name if package.macro_profile and package.macro_profile.basic_info else package_name
        session_id = f"diary_{char_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}".replace(" ", "_")
        
        orchestrator = DailyLoopOrchestrator(
            package=package, profile=PROFILES.get(profile_name, PROFILES["draft"]),
            ws_manager=manager, api_keys=api_keys, session_id=session_id,
            regeneration_context=instructions
        )
        
        global active_diary_orchestrators
        active_diary_orchestrators[package_name] = orchestrator
        
        await manager.send_progress("diary_init", 0.0, f"日記生成を開始します... (session: {session_id})")
        try:
            results = await orchestrator.run(days=days)
            await manager.send_progress("diary_complete", 1.0, f"{len(results)}日分の日記生成が完了しました")
        finally:
            active_diary_orchestrators.pop(package_name, None)
    except Exception as e:
        logger.error(f"Diary generation failed: {e}", exc_info=True)
        await manager.send_error(f"日記生成エラー: {str(e)}")

async def run_artifact_regeneration(package_name: str, artifact_name: str, instructions: str, cascade: bool, profile_name: str, api_keys: dict = None):
    from backend.models.character import CharacterPackage
    from backend.regeneration import regenerate_artifact, ARTIFACT_TO_PHASE, ARTIFACT_LABELS
    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    try:
        package = CharacterPackage(**json.loads(pkg_path.read_text(encoding="utf-8")))
        label = ARTIFACT_LABELS.get(artifact_name, artifact_name)
        await manager.send_progress("regeneration", 0.0, f"「{label}」を再生成中...")
        
        package = await regenerate_artifact(package, artifact_name, instructions, PROFILES.get(profile_name, PROFILES["draft"]), manager, api_keys=api_keys)
        
        save_dir = AppConfig.STORAGE_DIR / package_name
        (save_dir / "package.json").write_text(json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        from backend.storage.md_storage import save_versioned_package
        await save_versioned_package(package.macro_profile.basic_info.name, package, manager.thought_history)
        await manager.send_progress("regeneration", 1.0, "再生成完了")
        await manager.send_phase_result("regenerate_complete", {"package_name": package_name, "regenerated": [artifact_name], "cost": token_tracker.summary()})
    except Exception as e:
        logger.error(f"Regeneration failed: {e}", exc_info=True)
        await manager.send_error(f"再生成エラー: {str(e)}")

async def save_manual_edit(package_name: str, artifact_name: str, edited_data: dict):
    from backend.models.character import CharacterPackage, ConceptPackage, MacroProfile, LinguisticExpression, MicroParameters, AutobiographicalEpisodes, WeeklyEventsStore
    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    model_map = {"concept_package": ConceptPackage, "macro_profile": MacroProfile, "linguistic_expression": LinguisticExpression, "micro_parameters": MicroParameters, "autobiographical_episodes": AutobiographicalEpisodes, "weekly_events_store": WeeklyEventsStore}
    try:
        package = CharacterPackage(**json.loads(pkg_path.read_text(encoding="utf-8")))
        model_cls = model_map.get(artifact_name)
        if model_cls: setattr(package, artifact_name, model_cls(**edited_data))
        else: setattr(package, artifact_name, edited_data)
        
        pkg_path.write_text(json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        await manager.broadcast({"type": "edit_saved", "artifact": artifact_name, "package_name": package_name, "message": f"「{artifact_name}」の編集を保存しました"})
    except Exception as e:
        logger.error(f"Save edit failed: {e}", exc_info=True)
        await manager.send_error(f"編集保存エラー: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=AppConfig.HOST, port=AppConfig.PORT, reload=False, log_level=AppConfig.LOG_LEVEL.lower())
