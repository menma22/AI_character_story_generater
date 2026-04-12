"""
裏方出力検証エージェント（v10 §4.6b 準拠）

衝動系エージェント（Perceiver + Impulsive 統合）の出力に
気質・性格パラメータの名前や値が直接言及されていないかチェックする。

隠蔽原則: 主人公AIは自分の気質・性格パラメータを直接知ることができない。
衝動系エージェントの出力は「自然言語化された知覚・反応」であり、
「#5 感情安定性が低いので」のようなパラメータ直接言及は漏洩とみなす。
"""

import json
import logging
from typing import Optional

from backend.models.memory import ImpulsiveOutput
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)

# チェック対象のキーワード（パラメータ名の日英）
LEAK_KEYWORDS = [
    # 気質パラメータ
    "新奇性追求", "NS", "損害回避", "HA", "報酬依存", "RD", "固執性", "Persistence",
    "パラメータ", "気質", "性格層", "性格パラメータ",
    # BigFive/HEXACO
    "外向性", "神経症", "開放性", "協調性", "誠実性",
    "Extraversion", "Neuroticism", "Openness", "Agreeableness", "Conscientiousness",
    # その他
    "衝動性パラメータ", "嫉妬気質", "社会的比較傾向",
    "#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9",
    "#10", "#11", "#12", "#13", "#14", "#15", "#16", "#17", "#18", "#19",
    "#20", "#21", "#22", "#23", "#24", "#25", "#26",
    "#27", "#28", "#29", "#30", "#31", "#32", "#33", "#34", "#35", "#36",
    "#37", "#38", "#39", "#40", "#41", "#42", "#43", "#44", "#45", "#46",
    "#47", "#48", "#49", "#50", "#51", "#52",
]


class OutputVerificationAgent:
    """裏方出力検証エージェント"""

    def __init__(self, ws_manager=None, tier: str = "gemini", api_keys: Optional[dict] = None):
        self.ws = ws_manager
        self.tier = tier
        self.api_keys = api_keys

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[出力検証]", content, status)

    def _quick_keyword_check(self, text: str) -> list[str]:
        """キーワードベースの簡易チェック"""
        found = []
        for kw in LEAK_KEYWORDS:
            if kw in text:
                found.append(kw)
        return found

    async def verify(
        self,
        impulsive_output: ImpulsiveOutput,
    ) -> dict:
        """
        衝動系エージェントの出力に隠蔽原則違反がないかチェック

        Returns:
            {"passed": bool, "violations": list[str], "corrected_impulsive": ImpulsiveOutput|None}
        """
        # Step 1: キーワードベース簡易チェック
        combined = impulsive_output.raw_text

        keyword_hits = self._quick_keyword_check(combined)

        if not keyword_hits:
            await self._notify("出力検証OK: 漏洩なし ✓", "complete")
            return {"passed": True, "violations": [], "corrected_impulsive": None}

        # Step 2: 漏洩検出 → LLMによる修正
        await self._notify(f"漏洩検出: {', '.join(keyword_hits[:5])} → 修正中...")

        result = await call_llm(
            tier=self.tier,
            system_prompt="""あなたは出力修正エージェントです。
衝動系エージェントの出力から、気質・性格パラメータの名前、ID番号、
学術用語が含まれている場合、それらを自然言語の体験記述に置き換えてください。

【禁止すべき表現の例】
- 「#5 感情安定性が低いため」→ NG
- 「NS（新奇性追求）が高いキャラクターなので」→ NG
- 「外向性パラメータに基づき」→ NG

【あるべき表現の例】
- 「胸がざわつく」「手のひらに汗がにじむ」→ OK
- 「思わず身を乗り出す」「逃げ出したい衝動に駆られる」→ OK

修正後の全文をそのまま出力してください。マークダウンのセクション構造は維持してください。""",
            user_message=(
                f"【衝動系エージェントの出力】\n{impulsive_output.raw_text}\n\n"
                f"【検出された漏洩キーワード】{', '.join(keyword_hits)}\n\n"
                f"上記の出力を修正してください。"
            ),
            json_mode=False,
            api_keys=self.api_keys,
        )

        corrected_text = result["content"] if isinstance(result["content"], str) else str(result["content"])
        corrected_impulsive = ImpulsiveOutput(raw_text=corrected_text)

        await self._notify(f"出力修正完了: {len(keyword_hits)}件の漏洩を修正", "complete")

        return {
            "passed": False,
            "violations": keyword_hits,
            "corrected_impulsive": corrected_impulsive,
        }
