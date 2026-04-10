import pathlib
import json
from typing import Optional
from backend.models.character import CharacterPackage
from backend.models.memory import EventPackage

STORAGE_ROOT = pathlib.Path(__file__).parent / "character_packages"

def _ensure_dir(path: pathlib.Path):
    path.mkdir(parents=True, exist_ok=True)

def safe_name(name: str) -> str:
    """Sanitizes character name for filesystem usage"""
    return "".join([c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name]).strip()

async def save_checkpoint(character_name: str, package: CharacterPackage):
    """Saves the current character package for potential resumption"""
    if not character_name:
        character_name = "Incomplete_Character"
    
    char_dir = STORAGE_ROOT / safe_name(character_name)
    _ensure_dir(char_dir)
    
    checkpoint_path = char_dir / "checkpoint.json"
    data = package.model_dump(mode="json")
    checkpoint_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return checkpoint_path

async def load_checkpoint(character_name: str) -> Optional[CharacterPackage]:
    """Loads a previously saved checkpoint"""
    char_dir = STORAGE_ROOT / safe_name(character_name)
    checkpoint_path = char_dir / "checkpoint.json"
    
    if not checkpoint_path.exists():
        return None
        
    try:
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        return CharacterPackage(**data)
    except Exception as e:
        print(f"Failed to load checkpoint: {e}")
        return None

async def save_character_profile(character_name: str, package: CharacterPackage):
    """
    Saves the entire character package as a beautiful Markdown profile.
    """
    if not character_name:
        character_name = "Unknown_Character"
    
    char_dir = STORAGE_ROOT / safe_name(character_name)
    _ensure_dir(char_dir)
    
    md_content = f"# Character Profile: {character_name}\n\n"
    
    # 1. Concept
    if package.concept_package:
        md_content += "## 1. Concept Package\n\n"
        md_content += f"**Concept:**\n{package.concept_package.character_concept}\n\n"
        md_content += f"**Story Outline:**\n{package.concept_package.story_outline}\n\n"
        md_content += f"**Interestingness Hooks:**\n"
        for feature in package.concept_package.interestingness_hooks:
            md_content += f"- {feature}\n"
        md_content += "\n"
    
    # 2. Macro Profile
    if package.macro_profile:
        md_content += "## 2. Macro Profile\n\n"
        basic = getattr(package.macro_profile, "basic_info", None)
        if basic:
            md_content += f"- **Name:** {getattr(basic, 'name', '')}\n"
            md_content += f"- **Age:** {getattr(basic, 'age', '')}\n"
            md_content += f"- **Gender:** {getattr(basic, 'gender', '')}\n"
            md_content += f"- **Occupation:** {getattr(basic, 'occupation', '')}\n\n"
        
        md_content += f"### Psychological Features\n"
        psy = getattr(package.macro_profile, "psychological_features", None)
        if psy:
            md_content += f"- **Core Desire:** {getattr(psy, 'core_desire', '')}\n"
            md_content += f"- **Core Fear:** {getattr(psy, 'core_fear', '')}\n"
            md_content += f"- **Life Goal:** {getattr(psy, 'life_goal', '')}\n\n"
    
    # 3. Micro Parameters (Dump as JSON block for exact parameters)
    if package.micro_parameters:
        md_content += "## 3. Micro Parameters (Esoteric Psychology)\n\n"
        md_content += "```json\n"
        md_content += json.dumps(package.micro_parameters.model_dump(), ensure_ascii=False, indent=2)
        md_content += "\n```\n\n"
        
    # 4. Autobiographical Episodes
    if package.autobiographical_episodes:
        md_content += "## 4. Autobiographical Episodes\n\n"
        for idx, ep in enumerate(package.autobiographical_episodes.episodes):
            md_content += f"### Episode {idx+1}: {ep.title} ({ep.life_stage})\n"
            md_content += f"- **Core Memory:** {ep.core_memory}\n"
            md_content += f"- **Impact:** {ep.impact_on_personality}\n\n"

    # 5. Events Plan
    if package.weekly_events_store:
        md_content += "## 5. 7-Day Event Plan (Phase D)\n\n"
        for event in package.weekly_events_store.events:
            md_content += f"- **Day {event.day}** [{event.type}] (Unexpectedness: {event.unexpectedness}): {event.content}\n"
        md_content += "\n"
        
    file_path = char_dir / "00_profile.md"
    file_path.write_text(md_content, encoding="utf-8")
    return file_path

async def save_daily_log(character_name: str, day: int, day_state):
    """
    Saves a specific day's logs completely covering events, introspection, memory and diary to Markdown.
    """
    if not character_name:
        character_name = "Unknown_Character"
    
    char_dir = STORAGE_ROOT / safe_name(character_name)
    logs_dir = char_dir / "daily_logs"
    _ensure_dir(logs_dir)
    
    md_content = f"# Day {day} Log for {character_name}\n\n"
    
    # Event Packages (What happened today)
    md_content += "## 1. Events & Agent Reactions\n\n"
    for i, ep in enumerate(day_state.event_packages):
        md_content += f"### Event {i+1}\n"
        md_content += f"**Event Statement:** {ep.event.content}\n\n"
        if getattr(ep, 'action_output', None):
             action_str = ep.action_output if isinstance(ep.action_output, str) else json.dumps(ep.action_output, ensure_ascii=False)
             md_content += f"**Action Output:**\n{action_str}\n\n"
        md_content += "---\n\n"
        
    # Introspection
    md_content += "## 2. Introspection (Self-Perception & Cognitive Dissonance)\n\n"
    if day_state.introspection:
        md_content += f"{day_state.introspection}\n\n"
    else:
        md_content += "*No introspection available.*\n\n"
        
    # Diary
    md_content += "## 3. Written Diary\n\n"
    if day_state.diary:
        md_content += f"> {day_state.diary.content}\n\n"
    else:
        md_content += "*No diary written.*\n\n"
        
    # Extracted Short-Term Memory
    md_content += "## 4. Key Memories & Short Term DB\n\n"
    if day_state.extracted_key_memories:
        for mem in day_state.extracted_key_memories:
            md_content += f"- {mem}\n"
    else:
        md_content += "*No key memories extracted.*\n"
    md_content += "\n"
        
    file_path = logs_dir / f"Day_{day}.md"
    file_path.write_text(md_content, encoding="utf-8")
    return file_path
