import asyncio
import logging
from backend.agents.creative_director.director import CreativeDirector
from backend.config import PROFILES

logging.basicConfig(level=logging.INFO)

async def test_director():
    profile = PROFILES["draft"]
    director = CreativeDirector(profile)
    try:
        pkg = await director.run("サイバーパンクな世界観")
        import json
        print(json.dumps(pkg.model_dump(mode="json"), indent=2, ensure_ascii=False))
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Also print the last messages state if possible. 
        # But we can't easily access it from outside.

if __name__ == "__main__":
    asyncio.run(test_director())
