import asyncio
from backend.models.character import CharacterPackage, MacroProfile, BasicInfo, ConceptPackage
from backend.models.memory import EventPackage
from pydantic import BaseModel
from backend.storage.md_storage import save_character_profile, save_daily_log

async def test_md():
    pkg = CharacterPackage(
        concept_package=ConceptPackage(
            character_concept="テストマン",
            story_outline="テスト用のストーリー。この男はすべてをテストする。",
            narrative_theme="自動テストの悲劇",
            interestingness_hooks=["几帳面", "パラノイア"],
            verdict="pass",
            iteration_count=1
        ),
        macro_profile=MacroProfile(
            basic_info=BasicInfo(
                name="テスト アルファ",
                age=25,
                gender="男",
                appearance="テストスペック",
                occupation="テスター"
            )
        )
    )

    class MockDiary:
        content: str = "今日の日記。"
    class MockDayState:
        day: int = 1
        event_packages: list = []
        introspection: str = ""
        diary: MockDiary = MockDiary()
        extracted_key_memories: list = []
        
    day_state = MockDayState()
    class MockEvent:
        content: str = "mock content"
    class MockEventPackage:
        event_id: str = "e1"
        event_content: str = "テストイベント"
        event: MockEvent = MockEvent()
        event_metadata: dict = {"expectedness": "low"}
        mood_before = None
        mood_after = None
        
    d = MockEventPackage()
    day_state.event_packages.append(d)
    
    await save_character_profile("テスト アルファ", pkg)
    await save_daily_log("テスト アルファ", 1, day_state)
    print("MD Files generated!")

if __name__ == "__main__":
    asyncio.run(test_md())
