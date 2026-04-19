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

async def save_logs(character_name: str, logs: list[dict]):
    """思考ログをJSONとMarkdownで保存"""
    if not character_name or not logs:
        return
        
    char_dir = STORAGE_ROOT / safe_name(character_name)
    _ensure_dir(char_dir)
    
    # JSON保存
    json_path = char_dir / "agent_logs.json"
    json_path.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Markdown保存 (人間可読)
    md_path = char_dir / "agent_logs.md"
    md_content = f"# Agent Thought Logs: {character_name}\n\n"
    for log in logs:
        agent = log.get("agent", "Unknown")
        content = log.get("content", "")
        status = log.get("status", "thinking")
        model = log.get("model", "")
        model_str = f" [{model}]" if model else ""
        
        md_content += f"### {agent}{model_str} ({status})\n"
        md_content += f"{content}\n\n"
        md_content += "---\n\n"
        
    md_path.write_text(md_content, encoding="utf-8")
    return json_path

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
        if package.concept_package.raw_prose_markdown:
            md_content += "## 1. Concept Summary\n\n"
            md_content += f"{package.concept_package.raw_prose_markdown}\n\n"
        else:
            md_content += "## 1. Concept Package\n\n"
            md_content += f"**Concept:**\n{package.concept_package.character_concept}\n\n"
            md_content += f"**Story Outline:**\n{package.concept_package.story_outline}\n\n"
            md_content += f"**Interestingness Hooks:**\n"
            for feature in package.concept_package.interestingness_hooks:
                md_content += f"- {feature}\n"
            md_content += "\n"
    
    # 2. Macro Profile
    if package.macro_profile:
        if package.macro_profile.raw_prose_markdown:
            md_content += "## 2. Macro Profile\n\n"
            md_content += f"{package.macro_profile.raw_prose_markdown}\n\n"
        else:
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
    
    # 2.5. Linguistic Expression (言語的表現方法)
    if package.linguistic_expression:
        md_content += "## 2.5. 言語的表現方法\n\n"
        if package.linguistic_expression.raw_prose_markdown:
            md_content += f"{package.linguistic_expression.raw_prose_markdown}\n\n"
        else:
            le = package.linguistic_expression
            sc = le.speech_characteristics
            vf = sc.concrete_features
            md_content += "### 喋り方の特徴\n\n"
            if sc.abstract_feel:
                md_content += f"**雰囲気:** {sc.abstract_feel}\n\n"
            md_content += f"- **一人称:** {vf.first_person}\n"
            if vf.catchphrases:
                md_content += f"- **口癖:** {', '.join(vf.catchphrases)}\n"
            if vf.sentence_endings:
                md_content += f"- **文末表現:** {', '.join(vf.sentence_endings)}\n"
            md_content += f"- **漢字/ひらがな:** {vf.kanji_hiragana_tendency}\n"
            if vf.avoided_words:
                md_content += f"- **避ける語彙:** {', '.join(vf.avoided_words)}\n"
            if sc.conversation_style:
                md_content += f"- **会話スタイル:** {sc.conversation_style}\n"
            if sc.emotional_expression_tendency:
                md_content += f"- **感情表現:** {sc.emotional_expression_tendency}\n"
            md_content += "\n"
            da = le.diary_writing_atmosphere
            md_content += "### 日記の書き方の雰囲気\n\n"
            if da.raw_atmosphere_description:
                md_content += f"**空気感:** {da.raw_atmosphere_description}\n\n"
            if da.tone:
                md_content += f"- **トーン:** {da.tone}\n"
            if da.structure_tendency:
                md_content += f"- **構成傾向:** {da.structure_tendency}\n"
            if da.introspection_depth:
                md_content += f"- **内省の深さ:** {da.introspection_depth}\n"
            if da.what_gets_written:
                md_content += f"- **書く内容:** {da.what_gets_written}\n"
            if da.what_gets_omitted:
                md_content += f"- **省略する傾向:** {da.what_gets_omitted}\n"
            md_content += "\n"

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
            life_period = ep.metadata.life_period if ep.metadata else "unknown"
            category = ep.metadata.category if ep.metadata else "unknown"
            md_content += f"### Episode {idx+1}: {category} ({life_period})\n"
            md_content += f"- **Narrative:** {ep.narrative}\n"
            if ep.metadata and ep.metadata.connected_to:
                md_content += f"- **Connected to:** {', '.join(str(v) for v in ep.metadata.connected_to.values())}\n"
            md_content += "\n"

    # 4.5. Character Capabilities (所持品・能力・可能行動)
    if package.character_capabilities:
        caps = package.character_capabilities
        md_content += "## 4.5. 所持品・能力・可能行動\n\n"

        md_content += "### 所持品\n\n"
        if caps.possessions:
            for item in caps.possessions:
                carry = " ★常時携帯" if item.always_carried else ""
                md_content += f"- **{item.name}**{carry}: {item.description}\n"
                if item.emotional_significance:
                    md_content += f"  - 感情的意味: {item.emotional_significance}\n"
        else:
            md_content += "（未設定）\n"
        md_content += "\n"

        md_content += "### 能力・スキル\n\n"
        if caps.abilities:
            for ability in caps.abilities:
                md_content += f"- **{ability.name}** [{ability.proficiency}]: {ability.description}\n"
                if ability.origin:
                    md_content += f"  - 習得: {ability.origin}\n"
        else:
            md_content += "（未設定）\n"
        md_content += "\n"

        md_content += "### 取れる行動\n\n"
        if caps.available_actions:
            for act in caps.available_actions:
                md_content += f"- **{act.action}**: {act.context}\n"
                if act.prerequisites:
                    md_content += f"  - 前提: {act.prerequisites}\n"
        else:
            md_content += "（未設定）\n"
        md_content += "\n"

    # 5. Events Plan
    if package.weekly_events_store:
        md_content += "## 5. 7-Day Event Plan (Phase D)\n\n"
        for event in package.weekly_events_store.events:
            conflict_str = f"[{event.conflict_type}]" if event.conflict_type else ""
            md_content += f"- **Day {event.day}** {conflict_str} (Expectedness: {event.expectedness}): {event.content}\n"
        md_content += "\n"
        
    file_path = char_dir / "00_profile.md"
    file_path.write_text(md_content, encoding="utf-8")
    return file_path

async def save_daily_log(character_name: str, day: int, day_state):
    """
    1日の処理状態を完全にカバーするMarkdownログを保存する。
    イベント処理（Perceiver/Impulsive/Reflective/Integration/SceneNarration/ValuesViolation）、
    内省、日記、記憶、ムード変遷を全て記録する。
    """
    if not character_name:
        character_name = "Unknown_Character"

    char_dir = STORAGE_ROOT / safe_name(character_name)
    logs_dir = char_dir / "daily_logs"
    _ensure_dir(logs_dir)

    md_content = f"# Day {day} ログ — {character_name}\n\n"
    md_content += f"**日次集約ムード (Peak-End):** V={day_state.daily_mood.valence:.1f} / A={day_state.daily_mood.arousal:.1f} / D={day_state.daily_mood.dominance:.1f}\n\n"

    # ── 1. イベント処理詳細 ──
    md_content += "## 1. イベント処理\n\n"
    for i, ep in enumerate(day_state.events_processed):
        md_content += f"### イベント {i+1}: {ep.event_id}\n\n"
        md_content += f"**出来事:** {ep.event_content}\n\n"

        # メタデータ
        meta = ep.event_metadata or {}
        md_content += f"*既知/未知: {'既知' if meta.get('known_to_protagonist') else '未知'} | 予想外度: {meta.get('expectedness', '?')} | source: {meta.get('source', 'N/A')}*\n\n"

        # ムード変遷
        md_content += f"**ムード変遷:** V={ep.mood_before.valence:.1f}→{ep.mood_after.valence:.1f} / A={ep.mood_before.arousal:.1f}→{ep.mood_after.arousal:.1f} / D={ep.mood_before.dominance:.1f}→{ep.mood_after.dominance:.1f}\n\n"

        # 衝動反応（Impulsive）と理性分析（Reflective）は別ファイルに保存
        # → save_rim_outputs() を参照

        # Integration (行動決定)
        if ep.integration_output and ep.integration_output.final_action:
            md_content += "#### 行動決定（Integration）\n\n"
            md_content += f"**最終行動:** {ep.integration_output.final_action}\n\n"
            if ep.integration_output.higgins_ideal_gap:
                md_content += f"*Ideal不一致:* {ep.integration_output.higgins_ideal_gap}\n\n"
            if ep.integration_output.higgins_ought_gap:
                md_content += f"*Ought不一致:* {ep.integration_output.higgins_ought_gap}\n\n"
            if ep.integration_output.emotion_change:
                md_content += f"*気持ちの変化:* {ep.integration_output.emotion_change}\n\n"

        # 情景描写
        if ep.scene_narration and ep.scene_narration.scene_description:
            md_content += "#### 情景描写\n\n"
            md_content += f"{ep.scene_narration.scene_description}\n\n"
            if ep.scene_narration.aftermath:
                md_content += f"*後日譚:* {ep.scene_narration.aftermath}\n\n"

        # 価値観違反
        if ep.values_violation and ep.values_violation.violation_detected:
            md_content += "#### ⚠ 価値観違反検出\n\n"
            md_content += f"- **違反内容:** {ep.values_violation.violation_content}\n"
            md_content += f"- **種別:** {ep.values_violation.violation_type}\n"
            md_content += f"- **罪悪感:** {ep.values_violation.guilt_emotion}\n\n"

        md_content += "---\n\n"

    # ── 2. 内省 ──
    md_content += "## 2. 内省（Self-Perception & 記憶統合）\n\n"
    if day_state.introspection:
        intro = day_state.introspection
        if intro.raw_text:
            md_content += f"{intro.raw_text}\n\n"
    else:
        md_content += "*内省なし*\n\n"

    # ── 3. 日記 ──
    md_content += "## 3. 日記\n\n"
    if day_state.diary:
        md_content += f"> {day_state.diary.content}\n\n"
        md_content += f"*執筆時ムード: V={day_state.diary.mood_at_writing.valence:.1f} A={day_state.diary.mood_at_writing.arousal:.1f} D={day_state.diary.mood_at_writing.dominance:.1f}*\n\n"
    else:
        md_content += "*日記なし*\n\n"

    # ── 4. Key Memory ──
    md_content += "## 4. Key Memory\n\n"
    if day_state.key_memory:
        md_content += f"**Day {day_state.key_memory.day}の最も重要な瞬間:**\n\n{day_state.key_memory.content}\n\n"
    else:
        md_content += "*Key Memory未抽出*\n\n"

    # ── 5. 翌日予定 ──
    if day_state.next_day_plans:
        md_content += "## 5. 翌日予定（protagonist_plan）\n\n"
        for plan in day_state.next_day_plans:
            action = plan.get("action", "")
            time = plan.get("preferred_time", "")
            motivation = plan.get("motivation", "")
            inserted = "✓挿入済" if plan.get("inserted") else "未挿入"
            md_content += f"- [{inserted}] {action}（{time}）— {motivation}\n"
        md_content += "\n"

    # ── 6. コスト記録 ──
    if day_state.cost_records:
        md_content += "## 6. コスト記録\n\n"
        md_content += "| ステップ | 入力トークン | 出力トークン | 推定コスト |\n"
        md_content += "|---------|------------|------------|----------|\n"
        total_cost = 0
        total_input = 0
        total_output = 0
        for rec in day_state.cost_records:
            label = rec.get("label", "不明")
            inp = rec.get("input_tokens", 0)
            out = rec.get("output_tokens", 0)
            cost = rec.get("cost_usd", 0)
            md_content += f"| {label} | {inp:,} | {out:,} | ${cost:.4f} |\n"
            total_cost += cost
            total_input += inp
            total_output += out
        md_content += f"| **Day {day} 合計** | **{total_input:,}** | **{total_output:,}** | **${total_cost:.4f}** |\n\n"

    file_path = logs_dir / f"Day_{day}.md"
    file_path.write_text(md_content, encoding="utf-8")
    return file_path


async def save_rim_outputs(character_name: str, day: int, day_state):
    """
    衝動エージェント（Impulsive）と理性エージェント（Reflective）の出力を
    Dayログとは別ファイルに保存する。
    これらの出力は日記AIには渡さず、デバッグ・分析用途でのみ使用される。
    """
    if not character_name:
        character_name = "Unknown_Character"

    char_dir = STORAGE_ROOT / safe_name(character_name)
    logs_dir = char_dir / "daily_logs"
    _ensure_dir(logs_dir)

    md_content = f"# Day {day} RIM出力（衝動/理性エージェント） — {character_name}\n\n"
    md_content += "*このファイルは衝動エージェント（Impulsive）と理性エージェント（Reflective）の*\n"
    md_content += "*生出力を保存したものです。日記AIには渡されません。*\n\n"

    has_content = False
    for i, ep in enumerate(day_state.events_processed):
        event_header_written = False

        if ep.impulsive_output and ep.impulsive_output.raw_text:
            if not event_header_written:
                md_content += f"## イベント {i+1}: {ep.event_id}\n\n"
                md_content += f"**出来事:** {ep.event_content}\n\n"
                event_header_written = True
            md_content += "### 衝動反応（Impulsive）\n\n"
            md_content += f"{ep.impulsive_output.raw_text}\n\n"
            has_content = True

        if ep.reflective_output and ep.reflective_output.raw_text:
            if not event_header_written:
                md_content += f"## イベント {i+1}: {ep.event_id}\n\n"
                md_content += f"**出来事:** {ep.event_content}\n\n"
                event_header_written = True
            md_content += "### 内面分析（Reflective）\n\n"
            md_content += f"{ep.reflective_output.raw_text}\n\n"
            has_content = True

        if event_header_written:
            md_content += "---\n\n"

    if not has_content:
        md_content += "*このDayのRIM出力はありません*\n"

    file_path = logs_dir / f"Day_{day}_rim_outputs.md"
    file_path.write_text(md_content, encoding="utf-8")
    return file_path
