"""
Phase A-3 Orchestrator
自伝的エピソード（5-8個）を生成する。
McAdamsカテゴリ強制 + redemption bias対策。

設計方針:
- Plannerはプロンプトコンテキストとしてのみ使用されるため自然言語テキスト出力。
- Writerは各エピソードの計画を受け取り、JSON出力で機械的にパースする。
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
- ID（ep_001形式）
- カテゴリ（上記McAdams分類）
- 時期（childhood/adolescence/young_adult/adult）
- テーマの要約
- 関与する他者
- 現在のどの価値観・怖れ・夢と紐づくか

自然な文章で計画を記述してください。各エピソードを明確に区切って記述すること。"""

EPISODE_WRITER_PROMPT = """あなたはキャラクターの自伝的エピソードを書くWriterです。
計画に基づいて、5-8個のエピソードそれぞれについて200-400字のnarrative（物語形式の記述）を書いてください。

【重要な設計思想】
- 個別のnarrativeの構造（結末が救済か悲劇か）は自由
- 問題なのは5-8個全体が特定パターンに偏ること
- 具体的な固有名詞、時期、場所、セリフを含めて書くこと
- 「何が起きたか」だけでなく「どう感じたか」「今どう思っているか」も含めること

出力形式: JSON
{
  "episodes": [
    {
      "id": "ep_001",
      "narrative": "200-400字のnarrative",
      "metadata": {
        "life_period": "時期（childhood/adolescence/young_adult/adult）",
        "category": "カテゴリ（redemption/contamination/ambivalent/loss/dream_origin）",
        "involved_others": ["関与者"],
        "connected_to": {"values": [...], "fears": [...]},
        "unresolved": true/false
      }
    }
  ]
}"""


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

        # Step 1: EpisodePlanner（自然言語テキスト出力 — JSON不要）
        await self._notify("Step 1: エピソード計画（自然言語）")
        plan_result = await call_llm(
            tier=self.profile.director_tier,
            system_prompt=EPISODE_PLANNER_PROMPT,
            user_message=context,
            cache_system=True,
        )

        plan_text = plan_result["content"] if isinstance(plan_result["content"], str) else json.dumps(plan_result["content"], ensure_ascii=False, indent=2)
        logger.info(f"[A-3] Episode plan text length: {len(plan_text)}")
        await self._notify(f"計画完了 ({len(plan_text)}字)")

        # Step 2: 計画全体をWriterに渡し、全エピソードを一括生成（JSON出力）
        await self._notify("Step 2: 全エピソード一括生成中...")
        if self.ws:
            await self.ws.send_agent_thought("[A-3] Writer", "全エピソード執筆中...", "thinking")

        writer_result = await call_llm(
            tier=self.profile.worker_tier,
            system_prompt=EPISODE_WRITER_PROMPT,
            user_message=(
                f"{context}\n\n"
                f"--- エピソード計画 ---\n{plan_text}\n\n"
                f"上記計画に基づいて、全エピソードのnarrativeをJSON形式で書いてください。"
            ),
            json_mode=True,
        )

        if self.ws:
            await self.ws.send_agent_thought("[A-3] Writer", "完了 ✓", "complete")

        # JSONパース
        if isinstance(writer_result["content"], dict):
            writer_data = writer_result["content"]
        else:
            logger.error(
                f"[A-3] Episode writer returned non-dict "
                f"(type={type(writer_result['content']).__name__}, "
                f"len={len(str(writer_result['content']))}). "
                f"Raw preview: {str(writer_result.get('raw', ''))[:300]}"
            )
            await self._notify("Episode writer JSON解析失敗", "error")
            writer_data = {}

        episodes_raw = writer_data.get("episodes", [])

        # AutobiographicalEpisodes組み立て
        episodes = []
        for i, ep_data in enumerate(episodes_raw):
            if not isinstance(ep_data, dict):
                logger.warning(f"[A-3] Episode {i} is not a dict: {type(ep_data)}")
                continue
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
                logger.warning(f"Episode parse error (index {i}): {e}")

        if len(episodes) < 5:
            logger.error(
                f"[A-3] Only {len(episodes)} valid episodes generated "
                f"(episodes_raw had {len(episodes_raw)} items). "
                f"Padding with placeholders — evaluator will likely reject."
            )
            await self._notify(
                f"WARNING: {len(episodes)}個のエピソードのみ成功。プレースホルダーで補填。", "error"
            )

        result = AutobiographicalEpisodes(episodes=episodes if len(episodes) >= 5 else episodes + [
            AutobiographicalEpisode(
                id=f"ep_{len(episodes)+j+1:03d}",
                narrative="（生成エラーにより空のエピソード）",
                metadata=EpisodeMetadata(life_period="unknown", category="ambivalent"),
            ) for j in range(max(0, 5 - len(episodes)))
        ])

        await self._notify(f"Phase A-3完了: {len(result.episodes)}個のエピソード生成", "complete")
        return result
