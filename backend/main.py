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
logging.basicConfig(
    level=getattr(logging, AppConfig.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
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
    """生成済み脚本パッケージ一覧"""
    storage = AppConfig.STORAGE_DIR
    packages = []
    if storage.exists():
        for d in sorted(storage.iterdir(), reverse=True):
            if d.is_dir():
                pkg_file = d / "package.json"
                if pkg_file.exists():
                    try:
                        data = json.loads(pkg_file.read_text(encoding="utf-8"))
                        packages.append({
                            "name": d.name,
                            "generated_at": data.get("metadata", {}).get("generated_at", ""),
                            "character_name": data.get("macro_profile", {}).get("basic_info", {}).get("name", "不明"),
                        })
                    except Exception:
                        packages.append({"name": d.name, "error": "読み込みエラー"})
    return {"packages": packages}


@app.get("/api/packages/{package_name}")
async def get_package(package_name: str):
    """特定の脚本パッケージを取得"""
    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    if pkg_path.exists():
        return json.loads(pkg_path.read_text(encoding="utf-8"))
    return {"error": "パッケージが見つかりません"}


# ─── WebSocket エンドポイント ─────────────────────────────────

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
    action = data.get("action", "")
    
    if action == "generate_character":
        # キャラクター生成開始
        profile_name = data.get("profile", AppConfig.DEFAULT_PROFILE)
        theme = data.get("theme", None)
        asyncio.create_task(run_character_generation(profile_name, theme))
    
    elif action == "generate_diary":
        # 日記生成開始
        package_name = data.get("package_name", "")
        days = data.get("days", 7)
        asyncio.create_task(run_diary_generation(package_name, days))
    
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


async def run_character_generation(profile_name: str, theme: str = None):
    """キャラクター生成パイプライン全体を実行"""
    from backend.agents.master_orchestrator.orchestrator import MasterOrchestrator
    
    profile = PROFILES.get(profile_name, PROFILES["draft"])
    
    await manager.send_progress("init", 0.0, "キャラクター生成を開始します...")
    
    try:
        orchestrator = MasterOrchestrator(profile=profile, ws_manager=manager)
        package = await orchestrator.run(theme=theme)
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        char_name = "unknown"
        if package.macro_profile and package.macro_profile.basic_info:
            char_name = package.macro_profile.basic_info.name
        
        save_dir = AppConfig.STORAGE_DIR / f"{char_name}_{timestamp}"
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
        
    except Exception as e:
        logger.error(f"Character generation failed: {e}", exc_info=True)
        await manager.send_error(f"キャラクター生成エラー: {str(e)}")


async def run_diary_generation(package_name: str, days: int = 7):
    """日記生成パイプライン全体を実行"""
    from backend.agents.daily_loop.orchestrator import DailyLoopOrchestrator
    
    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    if not pkg_path.exists():
        await manager.send_error(f"パッケージが見つかりません: {package_name}")
        return
    
    try:
        from backend.models.character import CharacterPackage
        pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
        package = CharacterPackage(**pkg_data)
        
        await manager.send_progress("diary_init", 0.0, "日記生成を開始します...")
        
        orchestrator = DailyLoopOrchestrator(package=package, ws_manager=manager)
        results = await orchestrator.run(days=days)
        
        # 日記を保存
        save_dir = AppConfig.STORAGE_DIR / package_name / "diaries"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        for day_state in results:
            if day_state.diary:
                diary_path = save_dir / f"day_{day_state.day:02d}.md"
                diary_path.write_text(day_state.diary.content, encoding="utf-8")
        
        await manager.send_progress("diary_complete", 1.0, f"{len(results)}日分の日記生成が完了しました")
        
    except Exception as e:
        logger.error(f"Diary generation failed: {e}", exc_info=True)
        await manager.send_error(f"日記生成エラー: {str(e)}")


# ─── 起動 ────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=AppConfig.HOST,
        port=AppConfig.PORT,
        reload=True,
        log_level=AppConfig.LOG_LEVEL.lower(),
    )
