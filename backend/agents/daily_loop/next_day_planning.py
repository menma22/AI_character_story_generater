"""
翌日予定追加エージェント（v10 §4.9.4 完全準拠）

Stage 1: 主人公AI側
  - 今日の日記を書いた後、「明日やりたいこと」を3つ出力
  - 主人公の能動的計画能力を表現

Stage 2: 裏方の整合性調整AI
  - 翌日のイベント列と衝突しないか確認
  - 整合性がある1個を選んで、source: "protagonist_plan" として翌日イベント列に挿入
  - この段階は主人公AIからは隠蔽される

v10 固有の差別化要素:
  Generative Agents (Park et al., 2023) にも存在しない、
  本アーキテクチャ固有の「主人公の能動的計画 → 翌日イベントへの反映」経路。
"""

import json
import logging
from typing import Optional

from backend.models.character import Event, WeeklyEventsStore
from backend.models.memory import (
    DiaryEntry, MoodState, NextDayPlan,
    IntrospectionMemo, DayProcessingState, EventPackage,
)
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


class NextDayPlanningAgent:
    """翌日予定追加エージェント（Stage 1 + Stage 2）"""
    
    def __init__(self, ws_manager=None, tier: str = "gemini"):
        self.ws = ws_manager
        self.tier = tier
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[翌日予定]", content, status)
    
    async def stage1_protagonist_plan(
        self,
        day: int,
        events: list[EventPackage],
        introspection: IntrospectionMemo,
        current_mood: MoodState,
        macro_context: str,
        voice_context: str,
    ) -> list[NextDayPlan]:
        """
        Stage 1: 主人公AIが「明日やりたいこと」を3つ出力

        日記生成の前に実行されるため、diary ではなく events を受け取る。

        Returns:
            list[NextDayPlan]（最大3つ）
        """
        await self._notify(f"Stage 1: Day {day}の主人公が明日の計画を考えています...")

        # イベント処理結果からサマリーを構築
        event_summaries = "\n".join([
            f"- [{ep.event_id}] {ep.integration_output.final_action[:120]} → {ep.scene_narration.aftermath[:80]}"
            for ep in events
        ]) if events else "(今日の出来事なし)"

        result = await call_llm(
            tier=self.tier,
            system_prompt=f"""あなたはキャラクター本人として、今日1日を振り返り
「明日やりたいこと」を考えるエージェントです。

【コンテキスト説明】
あなたはこのキャラクターとして毎日を過ごしており、今日の出来事と内省を踏まえて、
明日の行動を主体的に計画します。この計画は後の日記にも反映されます。

【ルール】
1. 今日の出来事と内省を踏まえて、明日したいことを3つ出す
2. 大きな計画ではなく、小さくて具体的な行動を出す
3. キャラクターの性格・価値観に基づいた自然な欲求であること
4. すべてが前向きである必要はない（回避行動でもよい）
5. {voice_context}

【出力形式】JSON:
{{
  "plans": [
    {{
      "action": "何をするか（1-2文）",
      "preferred_time": "いつ頃やりたいか（morning/afternoon/evening等）",
      "motivation": "なぜそれをしたいのか（1文、キャラ視点で）"
    }}
  ]
}}""",
            user_message=(
                f"【マクロプロフィール】\n{macro_context[:500]}\n\n"
                f"【Day {day}の出来事】\n{event_summaries}\n\n"
                f"【Day {day}の内省】\n{introspection.raw_text}\n\n"
                f"【現在のムード】V={current_mood.valence:.1f} A={current_mood.arousal:.1f} D={current_mood.dominance:.1f}\n\n"
                f"明日やりたいことを3つ考えてください。"
            ),
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        plans_raw = data.get("plans", [])
        
        plans = []
        for p in plans_raw[:3]:
            if isinstance(p, dict):
                plans.append(NextDayPlan(
                    action=p.get("action", ""),
                    preferred_time=p.get("preferred_time", "afternoon"),
                    motivation=p.get("motivation", ""),
                ))
        
        await self._notify(f"Stage 1完了: {len(plans)}個の計画を生成", "complete")
        return plans
    
    async def stage2_consistency_check(
        self,
        plans: list[NextDayPlan],
        next_day: int,
        events_store: WeeklyEventsStore,
    ) -> Optional[Event]:
        """
        Stage 2: 裏方の整合性調整AI
        
        翌日のイベント列と衝突しないか確認し、
        整合性がある1個を選んでイベントとして挿入する。
        
        Returns:
            Event（挿入するイベント）or None
        """
        if not plans or next_day > 7:
            return None
        
        await self._notify(f"Stage 2: Day {next_day}のイベント列との整合性チェック...")
        
        # 翌日の既存イベントを取得
        existing_events = [e for e in events_store.events if e.day == next_day]
        existing_summary = "\n".join([
            f"  [{e.time_slot}] {e.content[:60]}... (source:{e.source})"
            for e in existing_events
        ])
        
        plans_summary = "\n".join([
            f"  Plan {i+1}: {p.action} (preferred: {p.preferred_time}, motivation: {p.motivation})"
            for i, p in enumerate(plans)
        ])
        
        result = await call_llm(
            tier=self.tier,
            system_prompt="""あなたは翌日予定の整合性調整AIです
（裏方、主人公からは見えない）。

【タスク】
主人公が「明日やりたい」と言った3つの計画のうち、
翌日の既存イベント列と衝突しない1つを選んで、イベントとして挿入してください。

【ルール】
1. 既存イベントの時間帯と重複しない時間を選ぶ
2. 物語の流れに自然に組み込めるものを優先
3. 全てが不整合な場合、最も影響が少ないものを選ぶ
4. source は必ず "protagonist_plan" にすること
5. known_to_protagonist は true にすること

【出力形式】JSON:
{
  "selected_plan_index": 0,
  "event": {
    "id": "evt_plan_XXX",
    "day": 翌日番号,
    "time_slot": "afternoon",
    "known_to_protagonist": true,
    "source": "protagonist_plan",
    "expectedness": "high",
    "content": "主人公が計画した行動の記述（3-5文）",
    "involved_characters": [],
    "meaning_to_character": "なぜこれをしたいのか",
    "narrative_arc_role": "standalone_ripple",
    "conflict_type": null,
    "connected_episode_id": null,
    "connected_values": []
  },
  "insertion_reasoning": "この計画を選んだ理由"
}""",
            user_message=(
                f"【Day {next_day}の既存イベント】\n{existing_summary}\n\n"
                f"【主人公の計画（3つ）】\n{plans_summary}\n\n"
                f"1つを選んでイベントとして挿入してください。"
            ),
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        evt_data = data.get("event", {})
        
        if not evt_data:
            await self._notify("Stage 2: 挿入可能なイベントなし", "complete")
            return None
        
        try:
            # IDの生成
            existing_ids = [e.id for e in events_store.events]
            plan_count = sum(1 for e in events_store.events if e.source == "protagonist_plan")
            evt_id = evt_data.get("id", f"evt_plan_{plan_count + 1:03d}")
            
            event = Event(
                id=evt_id,
                day=next_day,
                time_slot=evt_data.get("time_slot", "afternoon"),
                known_to_protagonist=True,
                source="protagonist_plan",
                expectedness=evt_data.get("expectedness", "high"),
                content=evt_data.get("content", ""),
                involved_characters=evt_data.get("involved_characters", []),
                meaning_to_character=evt_data.get("meaning_to_character", ""),
                narrative_arc_role=evt_data.get("narrative_arc_role", "standalone_ripple"),
                conflict_type=evt_data.get("conflict_type"),
                connected_episode_id=evt_data.get("connected_episode_id"),
                connected_values=evt_data.get("connected_values", []),
            )
            
            # 選択された計画にマーク
            selected_idx = data.get("selected_plan_index", 0)
            if 0 <= selected_idx < len(plans):
                plans[selected_idx].inserted = True
            
            await self._notify(
                f"Stage 2完了: Plan {selected_idx + 1}を選択 → Day {next_day} [{event.time_slot}] に挿入",
                "complete"
            )
            
            return event
            
        except Exception as e:
            logger.warning(f"NextDayPlanning event creation error: {e}")
            await self._notify(f"Stage 2エラー: {str(e)}", "error")
            return None
