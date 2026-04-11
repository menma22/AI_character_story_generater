"""
第三者視点の日記検証AI（v10 §4.9.1 補完）

既存の DiarySelfCritic（言語的指紋の遵守チェック）とは異なり、
「初見の読者」として日記を評価する。

チェック観点:
  1. 理解可能性: 第三者が読んで内容を理解できるか
  2. 面白さ・人間味: 読みたいと思えるか、テクスチャがあるか
  3. 内部整合性: 日記内部に矛盾や論理破綻がないか
  4. 自然さ: 日記として不自然・奇妙な表現がないか
  5. イベントとの整合: その日の出来事と日記の内容が合っているか
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
        return "\n".join(parts) if parts else "(キャラクター情報なし)"

    async def review(
        self,
        diary: DiaryEntry,
        mood: MoodState,
        events_summary: str,
    ) -> dict:
        """
        第三者視点での日記品質チェック

        Args:
            diary: チェック対象の日記エントリ
            mood: 執筆時のムード状態
            events_summary: その日に起きた出来事の要約

        Returns:
            {"passed": bool, "issues": list[str]}
        """
        await self._notify(f"Day {diary.day}の日記を第三者視点でレビュー中...")

        character_summary = self._build_character_summary()

        result = await call_llm(
            tier=self.tier,
            system_prompt=f"""あなたはこの日記を初めて読む「第三者の読者」です。
キャラクターの設定や物語の背景は以下の情報だけを知っています。
この日記を読者として評価してください。

## あなたが知っているキャラクター情報
{character_summary}

## その日に起きた出来事（あらすじ）
{events_summary}

## 執筆時のムード
感情価(V): {mood.valence:.1f}, 覚醒度(A): {mood.arousal:.1f}, 支配感(D): {mood.dominance:.1f}

## チェック観点（5項目）

1. **理解可能性**: 日記の内容を第三者が読んで理解できるか？
   - 説明なく登場する固有名詞や出来事はないか
   - 文脈が飛びすぎて意味不明な箇所はないか
   - ただし日記なので、多少の省略は許容する

2. **面白さ・人間味**: この日記を読みたいと思えるか？
   - テンプレート的・機械的な記述になっていないか
   - キャラクターの個性や感性が感じられるか
   - 出来事の羅列ではなく、主観的な体験として書かれているか

3. **内部整合性**: 日記の中で矛盾がないか？
   - 前半と後半で感情や態度が理由なく変わっていないか
   - 同じ出来事が異なる描写をされていないか

4. **自然さ**: 日記として不自然な点はないか？
   - 人間が日記に書かないような説明的・辞書的な記述はないか
   - 「成長」「気づき」「学び」などのAI臭い締めくくりはないか
   - 過度に文学的で日記らしさを失っていないか

5. **イベントとの整合**: その日の出来事と日記の内容が合っているか？
   - あらすじに含まれる出来事と日記の記述に大きな齟齬はないか
   - ムード（PAD値）と日記のトーンが矛盾していないか

## 判定基準
- 5項目すべてが概ね問題なければ合格（passed: true）
- 1項目でも明確な問題があれば不合格（passed: false）
- 軽微な違和感は許容し、明らかに問題がある場合のみissueとして報告

## 出力形式（JSON）
問題がなければ:
{{"passed": true, "issues": []}}

問題があれば:
{{"passed": false, "issues": ["【観点名】具体的な問題点と、どう修正すべきか", "..."]}}

issuesには「何が問題で、どう直すべきか」を日記執筆者が即座に修正できるよう具体的に書いてください。""",
            user_message=f"【日記ドラフト（Day {diary.day}）】\n{diary.content}",
            json_mode=True,
        )

        data = result["content"] if isinstance(result["content"], dict) else {}
        passed = data.get("passed", False)
        issues = data.get("issues", [])

        if passed:
            await self._notify("第三者レビュー: 合格", "complete")
        else:
            await self._notify(f"第三者レビュー: 問題検出 {len(issues)}件", "complete")

        return {"passed": passed, "issues": issues}
