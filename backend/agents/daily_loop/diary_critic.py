"""
日記出力チェック（Self-Critic）エージェント（v10 §4.9.1 準拠）

シンプルな構造:
  1. 主エージェントが書いた日記ドラフトを受け取る
  2. チェック項目 + マクロプロフィール等の情報と照合（LLMに任せる）
  3. JSON形式で「OK」か「やり直し」を判定
  4. やり直しの場合、修正すべき箇所を明確に指摘して返す
"""

import json
import logging
from typing import Optional

from backend.models.character import MacroProfile, VoiceFingerprint
from backend.models.memory import DiaryEntry, MoodState
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


class DiarySelfCritic:
    """日記出力チェック（Self-Critic）— LLMベースのシンプルな検証"""

    def __init__(
        self,
        voice_fingerprint: VoiceFingerprint,
        macro_profile: Optional[MacroProfile] = None,
        ws_manager=None,
        tier: str = "gemini",
    ):
        self.voice = voice_fingerprint
        self.macro_profile = macro_profile
        self.ws = ws_manager
        self.tier = tier

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[日記Self-Critic]", content, status)

    def _build_check_context(self) -> str:
        """チェックに必要な情報をまとめたコンテキストを構築する"""
        sections = []

        # 言語的指紋（必須チェック項目）
        sections.append("## 言語的指紋（厳守ルール）")
        sections.append(f"- 一人称: {self.voice.first_person or '未指定'}")
        if self.voice.speech_patterns:
            sections.append(f"- 口癖: {', '.join(self.voice.speech_patterns)}")
        if self.voice.catchphrases:
            sections.append(f"- 口癖フレーズ: {', '.join(self.voice.catchphrases)}")
        if self.voice.sentence_endings:
            sections.append(f"- 文末表現: {', '.join(self.voice.sentence_endings)}")
        if self.voice.kanji_hiragana_tendency:
            sections.append(f"- 漢字/ひらがな傾向: {self.voice.kanji_hiragana_tendency}")
        if self.voice.emoji_usage:
            sections.append(f"- 絵文字・記号: {self.voice.emoji_usage}")
        if self.voice.avoided_words:
            sections.append(f"- 避ける語彙: {', '.join(self.voice.avoided_words)}")
        if self.voice.metaphor_irony_frequency:
            sections.append(f"- 比喩・反語: {self.voice.metaphor_irony_frequency}")

        # マクロプロフィール（キャラクター整合性の参照情報）
        if self.macro_profile:
            sections.append("\n## キャラクター情報（整合性チェック用）")
            bi = self.macro_profile.basic_info
            if bi.name:
                sections.append(f"- 名前: {bi.name}")
            if bi.age:
                sections.append(f"- 年齢: {bi.age}")
            if bi.occupation:
                sections.append(f"- 職業: {bi.occupation}")
            cl = self.macro_profile.current_life_outline
            if cl.hobbies_leisure:
                sections.append(f"- 趣味: {', '.join(cl.hobbies_leisure)}")
            if cl.daily_routine:
                sections.append(f"- 日常: {cl.daily_routine}")

        return "\n".join(sections)

    async def critique(self, diary: DiaryEntry, mood: MoodState) -> dict:
        """
        日記の品質チェック — LLMに全て任せるシンプルな検証

        Returns:
            {"passed": bool, "issues": list[str]}
        """
        await self._notify(f"Day {diary.day}の日記をチェック中...")

        check_context = self._build_check_context()

        result = await call_llm(
            tier=self.tier,
            system_prompt=f"""あなたは日記の品質チェッカーです。
以下のチェック項目とキャラクター情報に基づいて、日記ドラフトがルールを守れているか検証してください。

{check_context}

## 現在のムード（PAD値）
- 感情価(V): {mood.valence}, 覚醒度(A): {mood.arousal}, 支配感(D): {mood.dominance}

## チェック観点
1. 言語的指紋の遵守: 一人称、口癖、文末表現、漢字/ひらがな傾向が指定通りか
2. 避ける語彙の不使用: 避ける語彙リストに該当する語が含まれていないか
3. AI臭さの排除: 「成長」「気づき」「学び」「前向き」など、AIが書いた感じのする安直で綺麗事な語彙が使われていないか
4. 文量の適切さ: 200〜500字程度が目安（厳密でなくてよい）
5. ムードとの整合性: PAD値が示す感情状態と日記のトーンが矛盾していないか
6. キャラクター整合性: 年齢・職業・日常と矛盾する内容がないか

## 出力形式（JSON）
問題がなければ:
{{"passed": true, "issues": []}}

問題があれば:
{{"passed": false, "issues": ["具体的な問題点と修正指示1", "具体的な問題点と修正指示2"]}}

issuesには「何が問題で、どう直すべきか」を主エージェントが即座に修正できるよう明確に書いてください。""",
            user_message=f"【日記ドラフト（Day {diary.day}）】\n{diary.content}",
            json_mode=True,
        )

        # レスポンスのパース
        data = result["content"] if isinstance(result["content"], dict) else {}
        passed = data.get("passed", False)
        issues = data.get("issues", [])

        if passed:
            await self._notify("日記チェックOK", "complete")
        else:
            await self._notify(f"問題検出: {len(issues)}件", "complete")

        return {"passed": passed, "issues": issues}
