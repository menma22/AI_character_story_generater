"""
日記出力チェック（Self-Critic）エージェント（v10 §4.9.1 準拠）

日記生成後に品質チェックを実施:
- 言語的指紋（一人称、口癖、文末表現、漢字/ひらがな傾向）の整合性
- 避ける語彙の使用チェック
- AI臭い語彙（「成長」「気づき」「学び」等）の排除
- 日記の長さ・省略の自然さ
- mood PADとの整合性
"""

import json
import logging
from typing import Optional

from backend.models.character import VoiceFingerprint
from backend.models.memory import DiaryEntry, MoodState
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)

# AI臭い語彙のブラックリスト
AI_SMELL_WORDS = [
    "成長", "気づき", "学び", "視野が広がっ", "新たな発見",
    "自己成長", "大切なこと", "心の成長", "前向き", "ポジティブ",
    "チャレンジ", "ステップアップ", "自分を見つめ直", "大事にしたい",
]


class DiarySelfCritic:
    """日記出力チェック（Self-Critic）"""
    
    def __init__(self, voice_fingerprint: VoiceFingerprint, ws_manager=None, tier: str = "gemini"):
        self.voice = voice_fingerprint
        self.ws = ws_manager
        self.tier = tier
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[日記Self-Critic]", content, status)
    
    def _check_avoided_words(self, text: str) -> list[str]:
        """避ける語彙のチェック"""
        found = []
        for word in self.voice.avoided_words:
            if word in text:
                found.append(word)
        return found
    
    def _check_ai_smell(self, text: str) -> list[str]:
        """AI臭い語彙のチェック"""
        found = []
        for word in AI_SMELL_WORDS:
            if word in text:
                found.append(word)
        return found
    
    def _check_first_person(self, text: str) -> bool:
        """一人称の整合性チェック"""
        if not self.voice.first_person:
            return True
        
        # 指定された一人称が使われているか
        return self.voice.first_person in text
    
    async def critique(self, diary: DiaryEntry, mood: MoodState) -> dict:
        """
        日記の品質チェック
        
        Returns:
            {"passed": bool, "issues": list[str], "corrected_diary": str|None}
        """
        await self._notify(f"Day {diary.day}の日記をチェック中...")
        
        issues = []
        
        # Rule-based checks
        avoided = self._check_avoided_words(diary.content)
        if avoided:
            issues.append(f"避ける語彙の使用: {', '.join(avoided)}")
        
        ai_smell = self._check_ai_smell(diary.content)
        if ai_smell:
            issues.append(f"AI臭い語彙: {', '.join(ai_smell)}")
        
        if not self._check_first_person(diary.content):
            issues.append(f"一人称「{self.voice.first_person}」が使われていない")
        
        if len(diary.content) < 200:
            issues.append(f"日記が短すぎる ({len(diary.content)}字、最低200字推奨)")
        
        if len(diary.content) > 800:
            issues.append(f"日記が長すぎる ({len(diary.content)}字、最大600字推奨)")
        
        if not issues:
            await self._notify("日記チェックOK ✓", "complete")
            return {"passed": True, "issues": [], "corrected_diary": None}
        
        # Issues found → LLMで修正
        await self._notify(f"問題検出: {len(issues)}件 → 修正中...")
        
        result = await call_llm(
            tier=self.tier,
            system_prompt=f"""あなたは日記修正エージェントです。
以下の日記を修正してください。

【言語的指紋（厳守）】
一人称: {self.voice.first_person}
口癖: {', '.join(self.voice.speech_patterns)}
文末表現: {', '.join(self.voice.sentence_endings)}
漢字/ひらがな: {self.voice.kanji_hiragana_tendency}
避ける語彙: {', '.join(self.voice.avoided_words)}

【修正指示】
{chr(10).join(f'- {issue}' for issue in issues)}

修正後の日記のみを出力してください。JSON形式:
{{"corrected_diary": "修正後の日記本文"}}""",
            user_message=f"【元の日記】\n{diary.content}",
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        corrected = data.get("corrected_diary", diary.content)
        
        await self._notify(f"日記修正完了: {len(issues)}件の問題を修正", "complete")
        
        return {
            "passed": False,
            "issues": issues,
            "corrected_diary": corrected,
        }
