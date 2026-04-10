"""
裏方出力検証エージェント（v10 §4.6b 準拠）

衝動ブランチ（Perceiver + Impulsive Agent）の出力に
気質・性格パラメータの名前や値が直接言及されていないかチェックする。

隠蔽原則: 主人公AIは自分の気質・性格パラメータを直接知ることができない。
Perceiver/Impulsiveの出力は「自然言語化された知覚・反応」であり、
「#5 感情安定性が低いので」のようなパラメータ直接言及は漏洩とみなす。
"""

import json
import logging
from typing import Optional

from backend.models.memory import PerceiverOutput, ImpulsiveOutput
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
]


class OutputVerificationAgent:
    """裏方出力検証エージェント"""
    
    def __init__(self, ws_manager=None, tier: str = "gemma"):
        self.ws = ws_manager
        self.tier = tier
    
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
        perceiver_output: PerceiverOutput,
        impulsive_output: ImpulsiveOutput,
    ) -> dict:
        """
        Perceiver/Impulsiveの出力に隠蔽原則違反がないかチェック
        
        Returns:
            {"passed": bool, "violations": list[str], "corrected_perceiver": PerceiverOutput|None, "corrected_impulsive": ImpulsiveOutput|None}
        """
        # Step 1: キーワードベース簡易チェック
        combined = (
            perceiver_output.phenomenal_description +
            perceiver_output.reflexive_emotion +
            perceiver_output.automatic_attention +
            impulsive_output.impulse_reaction +
            impulsive_output.bodily_sensation +
            impulsive_output.action_tendency
        )
        
        keyword_hits = self._quick_keyword_check(combined)
        
        if not keyword_hits:
            await self._notify("出力検証OK: 漏洩なし ✓", "complete")
            return {"passed": True, "violations": [], "corrected_perceiver": None, "corrected_impulsive": None}
        
        # Step 2: 漏洩検出 → LLMによる修正
        await self._notify(f"漏洩検出: {', '.join(keyword_hits[:5])} → 修正中...")
        
        result = await call_llm(
            tier=self.tier,
            system_prompt="""あなたは出力修正エージェントです。
以下のPerceiverとImpulsive Agentの出力から、気質・性格パラメータの名前、ID番号、
学術用語が含まれている場合、それらを自然言語の体験記述に置き換えてください。

【禁止すべき表現の例】
- 「#5 感情安定性が低いため」→ NG
- 「NS（新奇性追求）が高いキャラクターなので」→ NG
- 「外向性パラメータに基づき」→ NG

【あるべき表現の例】
- 「胸がざわつく」「手のひらに汗がにじむ」→ OK
- 「思わず身を乗り出す」「逃げ出したい衝動に駆られる」→ OK

出力形式: JSON
{
  "perceiver": {
    "phenomenal_description": "修正後の現象的記述",
    "reflexive_emotion": "修正後の反射感情",
    "automatic_attention": "修正後の自動注意"
  },
  "impulsive": {
    "impulse_reaction": "修正後の衝動反応",
    "bodily_sensation": "修正後の身体感覚",
    "action_tendency": "修正後の行動傾向"
  }
}""",
            user_message=(
                f"【Perceiver出力】\n"
                f"phenomenal_description: {perceiver_output.phenomenal_description}\n"
                f"reflexive_emotion: {perceiver_output.reflexive_emotion}\n"
                f"automatic_attention: {perceiver_output.automatic_attention}\n\n"
                f"【Impulsive出力】\n"
                f"impulse_reaction: {impulsive_output.impulse_reaction}\n"
                f"bodily_sensation: {impulsive_output.bodily_sensation}\n"
                f"action_tendency: {impulsive_output.action_tendency}\n\n"
                f"【検出された漏洩キーワード】{', '.join(keyword_hits)}\n\n"
                f"上記の出力を修正してください。"
            ),
            max_tokens=800,
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        
        corrected_perceiver = None
        corrected_impulsive = None
        
        if "perceiver" in data:
            p = data["perceiver"]
            corrected_perceiver = PerceiverOutput(
                phenomenal_description=p.get("phenomenal_description", perceiver_output.phenomenal_description),
                reflexive_emotion=p.get("reflexive_emotion", perceiver_output.reflexive_emotion),
                automatic_attention=p.get("automatic_attention", perceiver_output.automatic_attention),
            )
        
        if "impulsive" in data:
            i = data["impulsive"]
            corrected_impulsive = ImpulsiveOutput(
                impulse_reaction=i.get("impulse_reaction", impulsive_output.impulse_reaction),
                bodily_sensation=i.get("bodily_sensation", impulsive_output.bodily_sensation),
                action_tendency=i.get("action_tendency", impulsive_output.action_tendency),
            )
        
        await self._notify(f"出力修正完了: {len(keyword_hits)}件の漏洩を修正", "complete")
        
        return {
            "passed": False,
            "violations": keyword_hits,
            "corrected_perceiver": corrected_perceiver,
            "corrected_impulsive": corrected_impulsive,
        }
