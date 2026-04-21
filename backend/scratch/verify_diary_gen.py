import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# プロジェクトルート（backendフォルダがある場所）をパスに追加
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.append(str(project_root))

from backend.agents.daily_loop.orchestrator import DailyLoopOrchestrator
from backend.models.character import CharacterPackage
from backend.config import AppConfig

from backend.config import AppConfig, PROFILES

import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("verify_fix")

async def verify():
    package_name = "神宮寺 誠"
    pkg_path = AppConfig.STORAGE_DIR / package_name / "package.json"
    
    if not pkg_path.exists():
        print(f"Error: {pkg_path} not found")
        return

    # APIキーの取得
    google_key = os.getenv("GOOGLE_AI_API_KEY")
    if not google_key:
        print("Warning: GOOGLE_AI_API_KEY not found in environment.")
    
    api_keys = {"GOOGLE_AI": google_key}

    # パッケージの読み込み
    pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
    package = CharacterPackage(**pkg_data)
    
    # プロファイル
    profile = PROFILES["draft"]
    
    # セッションID（実行ごとにユニークにする）
    session_id = f"test_verify_{datetime.now().strftime('%H%M%S')}"
    
    print(f"Starting diary generation for {package_name} Day 1 (Session: {session_id})...")
    
    try:
        # オーケストレーターの初期化
        orchestrator = DailyLoopOrchestrator(
            package=package,
            profile=profile,
            ws_manager=None,
            api_keys=api_keys,
            session_id=session_id
        )
        
        # Day 1 のみ実行
        results = await orchestrator.run(days=1)
        
        if results:
            print(f"Received results for {len(results)} days.")
            day_state = results[0]
            if day_state.diary:
                content = day_state.diary.content
                print("\n=== Generated Diary Content ===")
                print(content)
                print("===============================\n")
                
                if "失敗" in content or "気になれなかった" in content:
                    print("STATUS: Falls back to error text.")
                else:
                    print("SUCCESS: Diary generated successfully!")
            else:
                print("FAILED: day_state.diary is None")
        else:
            print("FAILED: results list is empty")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())

if __name__ == "__main__":
    asyncio.run(verify())
