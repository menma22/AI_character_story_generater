"""
言語表現バリデーター
キャラクターの言語的表現方法（LinguisticExpression）が日記で正しく守られているかを検証する
"""

import logging
from typing import Optional
from backend.models.character import LinguisticExpression
from backend.models.memory import DiaryEntry, MoodState
from backend.tools.llm_api import call_llm
from backend.agents.context_descriptions import wrap_context

logger = logging.getLogger(__name__)


class LinguisticExpressionValidator:
    """言語表現の守られ具合を検証するAI"""

    def __init__(self, linguistic_expression: LinguisticExpression, api_keys: Optional[dict] = None):
        self.le = linguistic_expression
        self.api_keys = api_keys

    async def validate(self, diary: DiaryEntry, mood: MoodState) -> dict:
        """
        日記がLinguisticExpressionを守っているかを検証

        Returns:
            {
                "passed": bool,
                "score": float (0.0-1.0),
                "issues": [list of issues found],
                "passed_items": [list of successfully validated items],
                "feedback": str (修正アドバイス)
            }
        """
        if not self.le:
            return {"passed": True, "score": 1.0, "issues": [], "passed_items": [], "feedback": ""}

        # 検証コンテキストの構築
        validation_context = self._build_validation_context()

        system_prompt = """あなたはキャラクターの言語表現バリデーターです。
与えられた日記がキャラクターの言語的特徴（喋り方、文体、語彙）を正しく守っているかを厳密に検証してください。

以下の項目について詳細にチェック：
1. 一人称の統一性
2. 避ける語彙の有無
3. 口癖の自然な出現
4. 文末表現のバリエーション
5. 漢字/ひらがなの傾向
6. 絵文字・記号の使用傾向
7. 自問形式の頻度
8. 比喩・反語の使用頻度
9. 日記のトーン・構成傾向
10. 内省の深さ

【出力形式】JSON:
{
  "passed": true|false,
  "score": 0.0-1.0（0が最悪、1が完璧）,
  "passed_items": ["守られていた項目1", "項目2", ...],
  "failed_items": [
    {
      "item": "チェック項目名",
      "issue": "具体的な問題（例：『避ける語彙「成長」が2回出現』）",
      "evidence": "日記からの引用（最大50字）"
    },
    ...
  ],
  "feedback": "修正アドバイス（3-5文、具体的に）"
}

【重要】
- 完璧を求めるな。自然な日記として読める範囲での良好な遵守を判定する。ただし、避ける語彙については厳密に。
- 避ける語彙は絶対に見落とすな。1つでも検出されたら failed_items に含める。
- 一人称の「揺らぎ」は一度だけなら許容する（疲れているなど文脈で説明可能）。複数回は問題。
- 「自問がない」という指摘は、自問頻度が「よく自問する」の場合のみ問題として扱う。
"""

        user_message = f"""{wrap_context('言語表現定義', validation_context)}

【検証対象の日記】
{diary.content}

【現在のムード】
V={mood.valence:.1f} A={mood.arousal:.1f} D={mood.dominance:.1f}

上記の日記が言語表現定義を守っているかを厳密に検証してください。"""

        result = await call_llm(
            tier="gemini",
            system_prompt=system_prompt,
            user_message=user_message,
            json_mode=True,
            api_keys=self.api_keys,
        )

        data = result["content"] if isinstance(result["content"], dict) else {}

        # レスポンスの正規化
        passed = data.get("passed", False)
        score = float(data.get("score", 0.0))
        passed_items = data.get("passed_items", [])
        failed_items = data.get("failed_items", [])
        feedback = data.get("feedback", "")

        # failed_items が存在する場合、passed は False
        if failed_items:
            passed = False

        return {
            "passed": passed,
            "score": score,
            "issues": [item["issue"] for item in failed_items],
            "failed_items": failed_items,
            "passed_items": passed_items,
            "feedback": feedback,
        }

    def _build_validation_context(self) -> str:
        """バリデーション用のLinguisticExpression定義を構築"""
        if not self.le:
            return ""

        parts = []
        vf = self.le.speech_characteristics.concrete_features

        # 具体的特徴
        parts.append("【具体的な言語特性】")
        parts.append(f"一人称: {vf.first_person}")

        # 二人称
        if vf.second_person_by_context:
            spc = vf.second_person_by_context
            parts.append("二人称の使い分け:")
            if spc.get("to_intimate"):
                parts.append(f"  - 親しい人へ: {spc.get('to_intimate')}")
            if spc.get("to_superior"):
                parts.append(f"  - 目上へ: {spc.get('to_superior')}")
            if spc.get("to_stranger"):
                parts.append(f"  - 知らない人へ: {spc.get('to_stranger')}")

        parts.append(f"口癖: {', '.join(vf.speech_patterns)}")
        parts.append(f"文末表現: {', '.join(vf.sentence_endings)}")
        parts.append(f"漢字/ひらがな傾向: {vf.kanji_hiragana_tendency}")
        parts.append(f"絵文字・記号の使用: {vf.emoji_usage}")
        parts.append(f"自問形式の頻度: {vf.self_questioning_frequency}")
        parts.append(f"比喩・反語の頻度: {vf.metaphor_irony_frequency}")
        parts.append(f"【絶対に避ける語彙（これらの語は厳禁）】: {', '.join(vf.avoided_words)}")

        # 抽象的な特徴
        if self.le.speech_characteristics.abstract_feel:
            parts.append(f"\n【喋り方の雰囲気】\n{self.le.speech_characteristics.abstract_feel}")

        if self.le.speech_characteristics.conversation_style:
            parts.append(f"\n【会話スタイル】\n{self.le.speech_characteristics.conversation_style}")

        if self.le.speech_characteristics.emotional_expression_tendency:
            parts.append(
                f"\n【感情表現の傾向】\n{self.le.speech_characteristics.emotional_expression_tendency}"
            )

        # 日記の書き方
        parts.append("\n【日記の書き方】")
        da = self.le.diary_writing_atmosphere
        if da.tone:
            parts.append(f"トーン: {da.tone}")
        if da.structure_tendency:
            parts.append(f"構成傾向: {da.structure_tendency}")
        if da.introspection_depth:
            parts.append(f"内省の深さ: {da.introspection_depth}")
        if da.what_gets_written:
            parts.append(f"書く内容: {da.what_gets_written}")
        if da.what_gets_omitted:
            parts.append(f"省略する内容: {da.what_gets_omitted}")
        if da.raw_atmosphere_description:
            parts.append(f"空気感: {da.raw_atmosphere_description}")

        return "\n".join(parts)
