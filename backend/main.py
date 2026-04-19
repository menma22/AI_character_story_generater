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
    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    if pkg_path.exists():
        return json.loads(pkg_path.read_text(encoding="utf-8"))
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
# 現在実行中のMasterOrchestratorインスタンスへの参照（concept_review応答のため）
active_orchestrator = None
# 日記生成中のパッケージ名を追跡（同時実行防止）
_diary_generation_active: set = set()

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
        # キャラクター生成開始
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        theme = data.get("theme", None)
        evaluators_override = data.get("evaluators_override", {})
        api_keys = data.get("api_keys", {})
        composition_preferences = data.get("composition_preferences", None)
        task = asyncio.create_task(run_character_generation(profile_name, theme, evaluators_override, api_keys, composition_preferences))
        ws_active_tasks[id(websocket)] = task
        task.add_done_callback(lambda t: ws_active_tasks.pop(id(websocket), None))
    
    elif action == "resume_generation":
        # チェックポイントから再開
        character_name = data.get("character_name", "")
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        evaluators_override = data.get("evaluators_override", {})
        api_keys = data.get("api_keys", {})
        task = asyncio.create_task(resume_character_generation(character_name, profile_name, evaluators_override, api_keys))
        ws_active_tasks[id(websocket)] = task
        task.add_done_callback(lambda t: ws_active_tasks.pop(id(websocket), None))
    
    elif action == "generate_diary":
        # 日記生成開始
        package_name = data.get("package_name", "")
        days = data.get("days", 7)
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        api_keys = data.get("api_keys", {})
        task = asyncio.create_task(run_diary_generation(package_name, days, profile_name, api_keys))
        ws_active_tasks[id(websocket)] = task
        
        # 完了時に辞書から削除
        task.add_done_callback(lambda t: ws_active_tasks.pop(id(websocket), None))
    
    elif action == "cancel_diary":
        # 現在実行中のタスクがあればキャンセル
        task_id = id(websocket)
        if task_id in ws_active_tasks:
            logger.info("Cancelling diary generation task per user request.")
            ws_active_tasks[task_id].cancel()
            ws_active_tasks.pop(task_id, None)
            
    elif action == "cancel_character_generation":
        # キャラクター生成の中断
        task_id = id(websocket)
        package_name = None
        
        if active_orchestrator:
            logger.info(f"Cancelling character generation per user request (Session: {getattr(active_orchestrator, 'session_id', 'unknown')})")
            
            # 中断前にチェックポイントを強制保存
            try:
                active_orchestrator._checkpoint()
                # パッケージ名を取得（キャラ名 or セッションID）
                pkg = active_orchestrator.package
                char_name = None
                if pkg and hasattr(pkg, 'macro_profile') and pkg.macro_profile:
                    bi = getattr(pkg.macro_profile, 'basic_info', None)
                    if bi:
                        char_name = getattr(bi, 'name', None)
                if char_name:
                    from backend.storage.md_storage import safe_name
                    package_name = safe_name(char_name)
                else:
                    package_name = getattr(active_orchestrator, 'session_id', None)
            except Exception as e:
                logger.error(f"Error saving checkpoint during cancel: {e}")
            
            active_orchestrator.cancel()
        
        if task_id in ws_active_tasks:
            ws_active_tasks[task_id].cancel()
            ws_active_tasks.pop(task_id, None)
        
        # フロントエンドに中断完了を通知（パーシャルデータの表示用）
        await websocket.send_json({
            "type": "generation_cancelled",
            "package_name": package_name,
            "message": "生成が中断されました。"
        })

    elif action == "regenerate_artifact":
        package_name = data.get("package_name", "")
        artifact_name = data.get("artifact_name", "")
        instructions = data.get("instructions", "")
        cascade = data.get("cascade", False)
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        api_keys = data.get("api_keys", {})
        asyncio.create_task(run_artifact_regeneration(package_name, artifact_name, instructions, cascade, profile_name, api_keys))

    elif action == "save_artifact_edit":
        package_name = data.get("package_name", "")
        artifact_name = data.get("artifact_name", "")
        edited_data = data.get("data", {})
        asyncio.create_task(save_manual_edit(package_name, artifact_name, edited_data))

    elif action == "approve_concept":
        # Human in the Loop: コンセプト承認
        if active_orchestrator:
            active_orchestrator.handle_review_response("approve")
        else:
            await websocket.send_json({"type": "error", "content": "アクティブな生成セッションがありません"})

    elif action == "revise_concept":
        # Human in the Loop: フィードバック付きコンセプト再生成
        if active_orchestrator:
            feedback = data.get("feedback", "")
            active_orchestrator.handle_review_response("revise", feedback=feedback)
        else:
            await websocket.send_json({"type": "error", "content": "アクティブな生成セッションがありません"})

    elif action == "edit_concept_direct":
        # Human in the Loop: コンセプト直接編集
        if active_orchestrator:
            edited_concept = data.get("concept_package", {})
            active_orchestrator.handle_review_response("edit", edited_concept=edited_concept)
        else:
            await websocket.send_json({"type": "error", "content": "アクティブな生成セッションがありません"})

    elif action == "get_status":
        await websocket.send_json({
            "type": "status",
            "cost": token_tracker.summary(),
        })

    else:
        await websocket.send_json({
            "type": "error",
            "content": f"Unknown action: {action}"
        })


async def run_character_generation(profile_name: str, theme: str = None, evaluators_override: dict = None, api_keys: dict = None, composition_preferences: dict = None):
    """キャラクター生成パイプライン全体を実行"""
    try:
        from backend.agents.master_orchestrator.orchestrator import MasterOrchestrator
        from backend.models.character import StoryCompositionPreferences
        import dataclasses
        from datetime import datetime

        base_profile = PROFILES.get(profile_name, PROFILES["draft"])
        target_profile = base_profile
        if evaluators_override:
            target_profile = dataclasses.replace(base_profile, **{
                k: v for k, v in evaluators_override.items()
                if hasattr(base_profile, k)
            })

        # 構成プリファレンスをPydanticモデルに変換
        prefs = None
        if composition_preferences:
            try:
                prefs = StoryCompositionPreferences(**composition_preferences)
            except Exception as e:
                logger.warning(f"Invalid composition_preferences: {e}")

        session_id = f"SID_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        await manager.send_progress("init", 0.0, "キャラクター生成を開始します...")
        # クライアントにセッションIDを通知（中断時の再開キーとして使用）
        await manager.send_agent_thought("System", f"Session ID: {session_id}", "info")

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
    """チェックポイントから再開"""
    try:
        from backend.agents.master_orchestrator.orchestrator import MasterOrchestrator
        from backend.storage.md_storage import load_checkpoint
        import dataclasses
        
        await manager.send_agent_thought("System", f"{character_name} の復旧を開始します...", "thinking")
        
        package = await load_checkpoint(character_name)
        if not package:
            await manager.send_error(f"チェックポイントが見つかりませんでした: {character_name}")
            return
            
        base_profile = PROFILES.get(profile_name, PROFILES["draft"])
        target_profile = base_profile
        if evaluators_override:
            target_profile = dataclasses.replace(base_profile, **{
                k: v for k, v in evaluators_override.items() 
                if hasattr(base_profile, k)
            })
            
        global active_orchestrator
        orchestrator = MasterOrchestrator(profile=target_profile, ws_manager=manager, existing_package=package, session_id=character_name, api_keys=api_keys) # character_name が事実上のSession ID
        active_orchestrator = orchestrator
        package = await orchestrator.run()
        await _finalize_character_generation(package)
    except Exception as e:
        logger.error(f"Resume failed: {e}", exc_info=True)
        await manager.send_error(f"再開エラー: {str(e)}")
    finally:
        active_orchestrator = None

async def _finalize_character_generation(package):
    """生成完了後の保存と通知（作業ディレクトリに統一保存）"""
    from backend.storage.md_storage import safe_name

    char_name = "unknown"
    if package.macro_profile and package.macro_profile.basic_info:
        char_name = package.macro_profile.basic_info.name

    # 作業ディレクトリと同一パスに保存（1キャラ=1ディレクトリ）
    save_dir = AppConfig.STORAGE_DIR / safe_name(char_name)
    save_dir.mkdir(parents=True, exist_ok=True)

    pkg_json = package.model_dump(mode="json")
    (save_dir / "package.json").write_text(
        json.dumps(pkg_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    await manager.send_progress("complete", 1.0, f"キャラクター「{char_name}」の生成が完了しました")
    await manager.send_phase_result("complete", {
        "package_name": save_dir.name,
        "character_name": char_name,
        "cost": token_tracker.summary(),
    })


async def run_diary_generation(package_name: str, days: int = 7, profile_name: str = None, api_keys: dict = None):
    """日記生成パイプライン全体を実行"""
    global _diary_generation_active

    # 同時実行防止ガード
    if package_name in _diary_generation_active:
        logger.warning(f"[run_diary_generation] 既に日記生成中: {package_name}。リクエストを拒否します。")
        await manager.send_error(f"「{package_name}」の日記生成は既に実行中です。完了をお待ちください。")
        return

    _diary_generation_active.add(package_name)
    session_id = f"diary_{package_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"[run_diary_generation] 開始: package={package_name}, session_id={session_id}")

    try:
        from backend.agents.daily_loop.orchestrator import DailyLoopOrchestrator
        from backend.models.character import CharacterPackage
        
        pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
        if not pkg_path.exists():
            await manager.send_error(f"パッケージが見つかりません: {package_name}")
            return
        
        pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
        package = CharacterPackage(**pkg_data)
        
        await manager.send_progress("diary_init", 0.0, f"日記生成を開始します... (session: {session_id})")
        
        target_profile = PROFILES.get(profile_name, PROFILES["draft"])
        orchestrator = DailyLoopOrchestrator(
            package=package,
            profile=target_profile,
            ws_manager=manager,
            api_keys=api_keys,
            session_id=session_id,
        )
        results = await orchestrator.run(days=days)

        # 日記を保存
        save_dir = AppConfig.STORAGE_DIR / package_name / "diaries"
        save_dir.mkdir(parents=True, exist_ok=True)

        for day_state in results:
            if day_state.diary:
                diary_path = save_dir / f"day_{day_state.day:02d}.md"
                diary_path.write_text(day_state.diary.content, encoding="utf-8")

        # protagonist_planイベントを含む最新パッケージをpackage.jsonに保存
        # （ループ内でも保存しているが、完了後に確実に最終状態を反映）
        pkg_path.write_text(
            json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        await manager.send_progress("diary_complete", 1.0, f"{len(results)}日分の日記生成が完了しました (session: {session_id})")
        
    except Exception as e:
        logger.error(f"Diary generation failed (session={session_id}): {e}", exc_info=True)
        await manager.send_error(f"日記生成エラー: {str(e)}")
    finally:
        _diary_generation_active.discard(package_name)
        logger.info(f"[run_diary_generation] 終了: package={package_name}, session_id={session_id}")

# ─── アーティファクト再生成・編集 ─────────────────────────────

async def run_artifact_regeneration(package_name: str, artifact_name: str, instructions: str, cascade: bool, profile_name: str, api_keys: dict = None):
    """特定アーティファクトを再生成する"""
    from backend.models.character import CharacterPackage
    from backend.regeneration import regenerate_artifact, get_downstream_artifacts, ARTIFACT_TO_PHASE, ARTIFACT_LABELS
    import dataclasses

    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    if not pkg_path.exists():
        await manager.send_error(f"パッケージが見つかりません: {package_name}")
        return

    if artifact_name not in ARTIFACT_TO_PHASE:
        await manager.send_error(f"不明なアーティファクト: {artifact_name}")
        return

    try:
        pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
        package = CharacterPackage(**pkg_data)

        base_profile = PROFILES.get(profile_name, PROFILES["draft"])

        label = ARTIFACT_LABELS.get(artifact_name, artifact_name)
        await manager.send_progress("regeneration", 0.0, f"「{label}」を再生成中...")

        # メインアーティファクトの再生成
        package = await regenerate_artifact(package, artifact_name, instructions, base_profile, manager, api_keys=api_keys)

        # カスケード再生成
        regenerated = [artifact_name]
        if cascade:
            downstream = get_downstream_artifacts(artifact_name)
            for i, ds_artifact in enumerate(downstream):
                ds_label = ARTIFACT_LABELS.get(ds_artifact, ds_artifact)
                await manager.send_progress("regeneration", (i + 1) / (len(downstream) + 1), f"カスケード再生成: {ds_label}")
                package = await regenerate_artifact(package, ds_artifact, "", base_profile, manager)
                regenerated.append(ds_artifact)

        # 保存
        save_dir = AppConfig.STORAGE_DIR / package_name
        save_dir.mkdir(parents=True, exist_ok=True)
        pkg_json = package.model_dump(mode="json")
        (save_dir / "package.json").write_text(
            json.dumps(pkg_json, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        await manager.send_progress("regeneration", 1.0, "再生成完了")
        await manager.send_phase_result("regenerate_complete", {
            "package_name": package_name,
            "regenerated": regenerated,
            "cost": token_tracker.summary(),
        })

    except Exception as e:
        logger.error(f"Artifact regeneration failed: {e}", exc_info=True)
        await manager.send_error(f"再生成エラー: {str(e)}")


async def save_manual_edit(package_name: str, artifact_name: str, edited_data: dict):
    """手動編集されたアーティファクトを保存する"""
    from backend.models.character import (
        CharacterPackage, ConceptPackage, MacroProfile, LinguisticExpression,
        MicroParameters, AutobiographicalEpisodes, WeeklyEventsStore,
    )
    from backend.regeneration import ARTIFACT_TO_PHASE, ARTIFACT_LABELS

    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    if not pkg_path.exists():
        await manager.send_error(f"パッケージが見つかりません: {package_name}")
        return

    if artifact_name not in ARTIFACT_TO_PHASE:
        await manager.send_error(f"不明なアーティファクト: {artifact_name}")
        return

    # アーティファクト名 → Pydanticモデルのマッピング
    model_map = {
        "concept_package": ConceptPackage,
        "macro_profile": MacroProfile,
        "linguistic_expression": LinguisticExpression,
        "micro_parameters": MicroParameters,
        "autobiographical_episodes": AutobiographicalEpisodes,
        "weekly_events_store": WeeklyEventsStore,
    }

    try:
        pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
        package = CharacterPackage(**pkg_data)

        # Pydanticモデルでバリデーション
        model_cls = model_map.get(artifact_name)
        if model_cls:
            validated = model_cls(**edited_data)
            setattr(package, artifact_name, validated)
        else:
            setattr(package, artifact_name, edited_data)

        # 保存
        pkg_json = package.model_dump(mode="json")
        pkg_path.write_text(
            json.dumps(pkg_json, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        label = ARTIFACT_LABELS.get(artifact_name, artifact_name)
        await manager.broadcast({
            "type": "edit_saved",
            "artifact": artifact_name,
            "package_name": package_name,
            "message": f"「{label}」の編集を保存しました",
        })

    except Exception as e:
        logger.error(f"Manual edit save failed: {e}", exc_info=True)
        await manager.send_error(f"編集保存エラー: {str(e)}")


# ─── 起動 ────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=AppConfig.HOST,
        port=AppConfig.PORT,
        reload=False,
        log_level=AppConfig.LOG_LEVEL.lower(),
    )
