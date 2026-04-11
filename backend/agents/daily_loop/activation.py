"""
パラメータ動的活性化エージェント（v10 §3.5, §4.4 完全準拠）

核心原則: 全52パラメータ + 規範層全要素は保持しつつ、
シーンごとに関連する5-10個だけを抽出して発火させる。

- 人間も全ての性格特性を常時意識しているわけじゃない（自己複雑性理論 Linville 1985）
- プロンプトサイズ問題が解決する
- 活性化ログが残るので、内省フェーズでの自己参照に使える
"""

import json
import logging
from typing import Optional

from backend.models.character import MicroParameters
from backend.models.memory import MoodState, ActivationLog
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


ACTIVATION_SYSTEM_PROMPT = """あなたは「パラメータ動的活性化エージェント」です。
与えられたシーン（出来事）に対して、52個の気質・性格パラメータ + 規範層の中から、
このシーンへの反応に最も関わってきそうなパラメータ・価値観・理想を抽出してください。

【理論的根拠】
- Linville (1985) 自己複雑性理論: 自己概念は複数の自己側面で構成されるが、状況がすべてを活性化するわけではない
- 状況-特性相互作用（Mischel 1973、CAPS 2004）: 特性は状況的手がかりにより選択的に活性化される

【抽出ルール】
1. 気質パラメータ(#1-#23)から2-4個を選択
2. 性格パラメータ(#24-#50)から2-4個を選択  
3. 対他者認知(#51-#52)は対人場面の場合のみ選択
4. 規範層（Schwartz価値、理想自己/義務自己）から関連するものを1-3個選択
5. 合計5-10個程度

【出力形式】JSON:
{
  "activated_temperament_ids": [1, 5, 10],
  "activated_personality_ids": [24, 30, 45],
  "activated_cognition_ids": [],
  "activated_values": ["Achievement", "Self-Direction"],
  "activated_ideal_self": true,
  "activated_ought_self": false,
  "activation_reasoning": "このシーンでは〇〇が関わるため、NS(#2)とHA(#4)が発火。対人葛藤があるため、信頼(#40)も活性化..."
}

【重要】
- 結果のJSON以外を出力しないこと
- パラメータIDは必ず実在のIDを使うこと
"""


class DynamicActivationAgent:
    """パラメータ動的活性化エージェント"""
    
    def __init__(self, micro_parameters: MicroParameters, ws_manager=None, tier: str = "gemma"):
        self.micro = micro_parameters
        self.ws = ws_manager
        self.tier = tier
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[活性化]", content, status)
    
    def _build_param_catalog(self) -> str:
        """全パラメータのカタログをコンパクトに生成"""
        lines = ["【気質パラメータ（23個）】"]
        for p in self.micro.temperament:
            lines.append(f"  #{p.id} {p.name}: {p.value:.1f}/5.0 | {p.natural_language[:40]}")
        
        lines.append("\n【性格パラメータ（27個）】")
        for p in self.micro.personality:
            lines.append(f"  #{p.id} {p.name}: {p.value:.1f}/5.0 | {p.natural_language[:40]}")
        
        lines.append("\n【対他者認知（2個）】")
        for p in self.micro.other_cognition:
            lines.append(f"  #{p.id} {p.name}: {p.value:.1f}/5.0 | {p.natural_language[:40]}")
        
        lines.append("\n【規範層】")
        if self.micro.schwartz_values:
            lines.append(f"  Schwartz: {json.dumps(self.micro.schwartz_values, ensure_ascii=False)}")
        if self.micro.ideal_self:
            lines.append(f"  理想自己: {self.micro.ideal_self}")
        if self.micro.ought_self:
            lines.append(f"  義務自己: {self.micro.ought_self}")
        if self.micro.goals:
            lines.append(f"  目標: {', '.join(self.micro.goals)}")
        
        return "\n".join(lines)
    
    async def activate(self, scene_description: str, current_mood: MoodState) -> ActivationLog:
        """
        シーンに対して動的活性化を実行
        
        Args:
            scene_description: イベントの自然言語記述
            current_mood: 現在のPADムード
        
        Returns:
            ActivationLog（活性化されたパラメータIDとログ）
        """
        await self._notify(f"動的活性化: {scene_description[:40]}...")
        
        param_catalog = self._build_param_catalog()
        
        result = await call_llm(
            tier=self.tier,
            system_prompt=ACTIVATION_SYSTEM_PROMPT,
            user_message=(
                f"【全パラメータカタログ】\n{param_catalog}\n\n"
                f"【現在ムード】V={current_mood.valence:.1f} A={current_mood.arousal:.1f} D={current_mood.dominance:.1f}\n\n"
                f"【シーン】\n{scene_description}\n\n"
                f"このシーンに関連する5-10個のパラメータ・価値観を抽出してください。"
            ),
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        
        # 活性化されたIDを収集
        temp_ids = [int(i) for i in data.get("activated_temperament_ids", []) if isinstance(i, (int, float))]
        pers_ids = [int(i) for i in data.get("activated_personality_ids", []) if isinstance(i, (int, float))]
        cog_ids = [int(i) for i in data.get("activated_cognition_ids", []) if isinstance(i, (int, float))]
        values = data.get("activated_values", [])
        reasoning = data.get("activation_reasoning", "")
        
        # 全パラメータIDを結合
        all_activated_ids = temp_ids + pers_ids + cog_ids
        
        log = ActivationLog(
            activated_temperament_ids=temp_ids,
            activated_personality_ids=pers_ids,
            activated_cognition_ids=cog_ids,
            activated_values=values if isinstance(values, list) else [],
            activation_reasoning=reasoning,
        )
        
        await self._notify(f"活性化完了: 気質{len(temp_ids)}個 + 性格{len(pers_ids)}個 + 価値{len(values)}個", "complete")
        return log
    
    def get_activated_params_text(self, log: ActivationLog) -> str:
        """
        活性化されたパラメータの自然言語記述を取得。
        Perceiver/Impulsive/Reflectiveのプロンプトに渡すためのもの。
        """
        lines = []
        
        # 気質
        for p in self.micro.temperament:
            if p.id in log.activated_temperament_ids:
                lines.append(f"[気質] #{p.id} {p.name} ({p.value:.1f}/5.0): {p.natural_language}")
        
        # 性格
        for p in self.micro.personality:
            if p.id in log.activated_personality_ids:
                lines.append(f"[性格] #{p.id} {p.name} ({p.value:.1f}/5.0): {p.natural_language}")
        
        # 対他者認知
        for p in self.micro.other_cognition:
            if p.id in (log.activated_cognition_ids or []):
                lines.append(f"[対他者認知] #{p.id} {p.name} ({p.value:.1f}/5.0): {p.natural_language}")
        
        # 規範層
        if log.activated_values:
            for v in log.activated_values:
                strength = self.micro.schwartz_values.get(v, "")
                if strength:
                    lines.append(f"[価値観] {v}: {strength}")
                else:
                    lines.append(f"[価値観] {v}")
        
        return "\n".join(lines) if lines else "(活性化パラメータなし)"
    
    def get_activated_normative_text(self, log: ActivationLog) -> str:
        """
        活性化された規範層の記述を取得。
        Reflective Agent用（気質・性格は含まない）。
        """
        lines = []
        
        if log.activated_values:
            for v in log.activated_values:
                strength = self.micro.schwartz_values.get(v, "")
                if strength:
                    lines.append(f"[Schwartz] {v}: {strength}")
        
        if self.micro.ideal_self:
            lines.append(f"[理想自己] {self.micro.ideal_self}")
        if self.micro.ought_self:
            lines.append(f"[義務自己] {self.micro.ought_self}")
        if self.micro.goals:
            lines.append(f"[目標] {', '.join(self.micro.goals)}")
        
        return "\n".join(lines) if lines else "(規範層情報なし)"
