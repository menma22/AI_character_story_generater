"""
Phase A-3 Orchestrator
自伝的エピソード（5-8個）を生成する。
McAdamsカテゴリ強制 + redemption bias対策。
"""

import json
import asyncio
import logging

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, MicroParameters,
    AutobiographicalEpisodes, AutobiographicalEpisode, EpisodeMetadata,
)
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)

EPISODE_PLANNER_PROMPT = """あなたはキャラクターの自伝的エピソードを計画するPlannerです。
キャラクターの人格の根幹を形作った5-8個の決定的エピソードの構成を計画してください。

【McAdamsカテゴリ制約（必須）】
- redemption（良い方向への転換）: 最大2個
- contamination（良かったものが損なわれた）: 最低1個
- loss（喪失・別れ）: 最低1個
- ambivalent（評価が定まらない）: 最低1個
- dream_origin（夢の起源）: 1個

【redemption bias対策（厳守）】
- LLMは全てを成長・救済に向ける傾向がある。これを構造的に防止すること
- contamination/loss/ambivalent型のエピソードが、最後に救済で終わってはならない
- 全エピソードが「結果的によかった」になることは禁止

【各エピソードに必要な情報】
- 時期（childhood/adolescence/young_adult/adult）
- 関与する他者
- 現在のどの価値観・怖れ・夢と紐づくか

出力形式: JSON
{
  "episode_plan": [
    {"id": "ep_001", "category": "contamination", "period": "adolescence",
     "theme": "テーマの要約", "involved_others": ["中学時代の親友"],
     "connected_to": {"values": ["Benevolence-Dependability"], "fears": ["親密な関係の喪失"]}}
  ]
}
"""

EPISODE_WRITER_PROMPT = """あなたはキャラクターの自伝的エピソードを書くWriterです。
計画に基づいて、200-400字のnarrative（物語形式の記述）を1個書いてください。

【重要な設計思想】
- 個別のnarrativeの構造（結末が救済か悲劇か）は自由
- 問題なのは5-8個全体が特定パターンに偏ること
- 具体的な固有名詞、時期、場所、セリフを含めて書くこと
- 「何が起きたか」だけでなく「どう感じたか」「今どう思っているか」も含めること

出力形式: JSON
{
  "id": "ep_XXX",
  "narrative": "200-400字のnarrative",
  "metadata": {
    "life_period": "時期",
    "category": "カテゴリ",
    "involved_others": ["関与者"],
    "connected_to": {"values": [...], "fears": [...]},
    "unresolved": true/false
  }
}
"""


class PhaseA3Orchestrator:
    """Phase A-3 Orchestrator"""
    
    def __init__(
        self,
        concept: ConceptPackage,
        macro_profile: MacroProfile,
        micro_parameters: MicroParameters,
        profile: EvaluationProfile,
        ws_manager=None,
    ):
        self.concept = concept
        self.macro = macro_profile
        self.micro = micro_parameters
        self.profile = profile
        self.ws = ws_manager
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[A-3] Orchestrator", content, status)
    
    def _full_context(self) -> str:
        """全コンテキストを文字列化"""
        return (
            f"concept_package:\n{json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            f"macro_profile:\n{json.dumps(self.macro.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            f"主要気質パラメータ:\n{json.dumps([p.model_dump(mode='json') for p in self.micro.temperament[:9]], ensure_ascii=False, indent=2)}\n\n"
            f"価値観:\n{json.dumps(self.micro.schwartz_values, ensure_ascii=False, indent=2)}\n\n"
            f"理想自己: {self.micro.ideal_self}\n"
            f"義務自己: {self.micro.ought_self}"
        )
    
    async def run(self) -> AutobiographicalEpisodes:
        """Phase A-3を実行"""
        await self._notify("Phase A-3: 自伝的エピソード生成開始")
        context = self._full_context()
        
        # Step 1: EpisodePlanner
        await self._notify("Step 1: エピソード計画")
        plan_result = await call_llm(
            tier=self.profile.director_tier,
            system_prompt=EPISODE_PLANNER_PROMPT,
            user_message=context,
            max_tokens=3000,
            json_mode=True,
            cache_system=True,
        )
        
        plan_data = plan_result["content"] if isinstance(plan_result["content"], dict) else {}
        episode_plan = plan_data.get("episode_plan", [])
        
        await self._notify(f"計画完了: {len(episode_plan)}個のエピソード")
        
        # Step 2: 各エピソードを並列で書く
        await self._notify("Step 2: エピソード並列生成中...")
        
        async def write_episode(plan_entry: dict) -> dict:
            ep_id = plan_entry.get("id", "ep_unknown")
            if self.ws:
                await self.ws.send_agent_thought(f"[A-3] Writer ({ep_id})", "執筆中...", "thinking")
            
            result = await call_llm(
                tier=self.profile.worker_tier,
                system_prompt=EPISODE_WRITER_PROMPT,
                user_message=(
                    f"{context}\n\n"
                    f"【このエピソードの計画】\n{json.dumps(plan_entry, ensure_ascii=False, indent=2)}\n\n"
                    f"上記計画に基づいて、200-400字のnarrativeを書いてください。"
                ),
                max_tokens=2000,
                json_mode=True,
            )
            
            data = result["content"] if isinstance(result["content"], dict) else {}
            if self.ws:
                await self.ws.send_agent_thought(f"[A-3] Writer ({ep_id})", "完了 ✓", "complete")
            return data
        
        episode_results = await asyncio.gather(*[write_episode(ep) for ep in episode_plan])
        
        # AutobiographicalEpisodes組み立て
        episodes = []
        for i, ep_data in enumerate(episode_results):
            try:
                metadata = ep_data.get("metadata", {})
                episode = AutobiographicalEpisode(
                    id=ep_data.get("id", f"ep_{i+1:03d}"),
                    narrative=ep_data.get("narrative", ""),
                    metadata=EpisodeMetadata(
                        life_period=metadata.get("life_period", "unknown"),
                        category=metadata.get("category", "ambivalent"),
                        involved_others=metadata.get("involved_others", []),
                        connected_to=metadata.get("connected_to", {}),
                        unresolved=metadata.get("unresolved", False),
                    ),
                )
                episodes.append(episode)
            except Exception as e:
                logger.warning(f"Episode parse error: {e}")
        
        result = AutobiographicalEpisodes(episodes=episodes if len(episodes) >= 5 else episodes + [
            AutobiographicalEpisode(
                id=f"ep_{len(episodes)+j+1:03d}",
                narrative="（生成エラーにより空のエピソード）",
                metadata=EpisodeMetadata(life_period="unknown", category="ambivalent"),
            ) for j in range(max(0, 5 - len(episodes)))
        ])
        
        await self._notify(f"Phase A-3完了: {len(result.episodes)}個のエピソード生成", "complete")
        return result
