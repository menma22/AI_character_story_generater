"""
第三者視点の日記検証AI（v10 §4.9.1 補完）

既存の DiarySelfCritic（言語的指紋の遵守チェック）とは異なり、
「初見の読者」として日記を評価する。

チェック観点:
  1. 理解可能性: 第三者が読んで内容を理解できるか
  2. 面白さ・人間味: 読みたいと思えるか、テクスチャがあるか
  3. 内部整合性: 日記内部に矛盾や論理破綻がないか
  4. 自然さ: 日記として不自然・奇妙な表現がないか
  5. 過去の日記との整合性: 過去の日記と矛盾していないか
"""

import logging
from typing import Optional

from backend.models.character import MacroProfile
from backend.models.memory import DiaryEntry, MoodState
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


class ThirdPartyReviewer:
    """第三者視点の日記検証AI — 読者としての品質チェック"""

    def __init__(
        self,
        macro_profile: Optional[MacroProfile] = None,
        ws_manager=None,
        tier: str = "gemini",
    ):
        self.macro_profile = macro_profile
        self.ws = ws_manager
        self.tier = tier

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[第三者レビュー]", content, status)

    def _build_character_summary(self) -> str:
        """チェックに必要な最低限のキャラクター情報を構築"""
        if not self.macro_profile:
            return "(キャラクター情報なし)"
        parts = []
        bi = self.macro_profile.basic_info
        if bi.name:
            parts.append(f"名前: {bi.name}")
        if bi.age:
            parts.append(f"年齢: {bi.age}")
        if bi.occupation:
            parts.append(f"職業: {bi.occupation}")
        cl = self.macro_profile.current_life_outline
        if cl and cl.hobbies_leisure:
            parts.append(f"趣味: {', '.join(cl.hobbies_leisure)}")
        if cl and cl.daily_routine:
            parts.append(f"日常: {cl.daily_routine[:100]}")
        vc = self.macro_profile.values_core
        if vc and vc.most_important:
            parts.append(f"大事にしていること: {vc.most_important}")
        return "\n".join(parts) if parts else "(��ャラクター情報なし)"

    async def review(
        self,
        diary: DiaryEntry,
        mood: MoodState,
        events_summary: str,
        past_diaries: str = "",
    ) -> dict:
        """
        第三者視点での日記品質チェック

        Args:
            diary: チェック対象の日記��ントリ
            mood: 執筆時のムード状態
            events_summary: その日に起きた出来事��要約
            past_diaries: その日までの過去の日記テキスト全文

        Returns:
            {"passed": bool, "issues": list[str]}
        """
        await self._notify(f"Day {diary.day}の日記を第三者視点でレビュー中...")

        character_summary = self._build_character_summary()

        # user_message構築: 過去の日記、キャラ概要、��日の出来事、ムード、チェック対象の日記を全て含める
        user_parts = []
        user_parts.append(f"## キャラクタ��概要\n{character_summary}")
        if past_diaries:
            user_parts.append(f"## 今までの日記（Day 1〜Day {diary.day - 1}）\n{past_diaries}")
        if events_summary:
            user_parts.append(f"## 今日の出来事（Day {diary.day}）\n{events_summary}")
        user_parts.append(f"## 現在のムード\nV={mood.valence:.1f} A={mood.arousal:.1f} D={mood.dominance:.1f}")
        user_parts.append(f"## 【チェック対象】日記ドラフト（Day {diary.day}）\n{diary.content}")
        user_message = "\n\n".join(user_parts)

        result = await call_llm(
            tier=self.tier,
            system_prompt=f"""あなたはこの日記を��めて読む「第���者の読者」です。
以下に提供される「今までの日記」「キ���ラクター概要」「今日��出来事」を参照しつつ、この日記を読者として評価して���ださい。


## チェック��点（5項目）

1. **理解可能性**: 日記の���容を第三者が読んで理解できるか？
   - 説���なく登場する固有名詞や出来事はないか
   - 文脈が飛びすぎて意味不明な箇所はないか
   - ただし日記なので、多少の省略は許容する

2. **面白さ・人間味**: この日記を読みたいと思えるか？
   - テンプレート的・機械的な記述になっていないか
   - キャラクターの個性���感性が感じられ���か
   - 出来事の羅列ではなく、主観的な体験として書かれているか

3. **内部整合性**: 日記の中で矛盾がないか？
   - 前半と後半で感情や態度が理由なく変わっていないか
   - 同じ出���事が異なる描写をされていないか

4. **自然さ**: 日記として不自然な点はないか？
   - 人間が日記に書かないような説明的・辞書的な記述はないか
   - 過度に文学的で日記らしさを失っていないか

5. **過去の日記との整合性**: 過去の日記で��べた事実・感情と矛盾していないか���
   - 以前の日記で語っ��出来事や人物への態度が急変していないか
   - 既出の固有名詞や設定が一貫しているか
   - ※ Day 1��場合はこの観点はスキップ

## 判定基準
- 5項目すべてが概���問題なければ合格（passed: true）
- 1項��でも明確な問題があれば不合格（passed: false）

## 出力形式（JSON）
問題がなければ:
{{"passed": true, "issues": []}}

問題が���れば:
{{"passed": false, "issues": ["【観点名】具体的な問題点と、どう修正す��きか", "..."]}}

issuesには「何が問題で、どう直すべきか」を日記執筆者が即座に修正できるよう具体的に書いてください。""",
            user_message=user_message,
            json_mode=True,
        )

        data = result["content"] if isinstance(result["content"], dict) else {}
        passed = data.get("passed", False)
        issues = data.get("issues", [])

        if passed:
            await self._notify("第三者レビュ���: 合格", "complete")
        else:
            await self._notify(f"第三者レビュー: 問題検出 {len(issues)}件", "complete")

        return {"passed": passed, "issues": issues}
