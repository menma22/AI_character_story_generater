import asyncio
import json
from pathlib import Path
from backend.agents.master_orchestrator.orchestrator import MasterOrchestrator
from backend.agents.daily_loop.orchestrator import DailyLoopOrchestrator
from backend.config import PROFILES

async def run_e2e():
    profile = PROFILES["draft"]
    print(f"=== Starting E2E Test with {profile.name} profile ===")
    
    # 1. First run the Master Orchestrator (Phase A-1 to D)
    print("Running Master Orchestrator...")
    master = MasterOrchestrator(profile=profile, ws_manager=None)
    package = await master.run(theme="テスト用キャラクター")
    
    # 2. Then run the Daily Loop for 7 days
    print("\nRunning Daily Loop (7 days)...")
    daily = DailyLoopOrchestrator(package=package, ws_manager=None)
    day_states = await daily.run(days=7)
    
    print("\n=== Generation Complete ===")
    if package.macro_profile and package.macro_profile.basic_info:
        print(f"Character Name: {package.macro_profile.basic_info.name}")
    print(f"Days processed: {len(day_states)}")
    
    # Check if a diary entry exists for the last day
    if day_states and day_states[-1].diary:
        print(f"Day 7 Diary snippet: {day_states[-1].diary.content[:100]}...")
        
    print(f"Total Cost: ${package.metadata.total_cost_usd:.4f}")

if __name__ == "__main__":
    asyncio.run(run_e2e())
