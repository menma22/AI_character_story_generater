"""
Phase A-3 Orchestrator
自伝的エピソード（5-8個）を生成する。
McAdamsカテゴリ強制 + redemption bias対策。

設計方針:
- エージェンティックループ（draft → critique → self_reflect → submit）で品質を自律的に担保。
- 計画と執筆を統合し、1つのエージェンティックループで処理する。
- フォールバック: agenticループ失敗時は従来の2ステップ一発出し方式に切り替え。
"""

import json
import asyncio
import logging
from typing import Optional

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, MicroParameters,
    AutobiographicalEpisodes, AutobiographicalEpisode, EpisodeMetadata,
)
from backend.tools.llm_api import call_llm
from backend.agents.context_descriptions import wrap_context

logger = logging.getLogger(__name__)

# ── 統合エージェンティックシステムプロンプト ──────────────────

EPISODE_AGENTIC_SYSTEM_PROMPT = """あなたはキャラクターの自伝的エピソードを計画・執筆するエピソードエージェントです。
キャラクターの人格の根幹を形作った5-8個の決定的エピソードを計画し、それぞれについて200-400字のnarrative（物語形式の記述）を書いてください。

【McAdamsカテゴリ制約（必須）】
- redemption（良い方向への転換）: 最大2個
- contamination（良かったものが損なわれた）: 最低1個
- loss（喪失・別れ）: 最低1個
- ambivalent（評価が定まらない）: 最低1個
- dream_origin（夢の起源）: 1個

【redemption bias対策（厳守）】
- LLMはすべてを成長・救済に向ける傾向がある。これを構造的に防止すること
- contamination/loss/ambivalent型のエピソードが、最後に救済で終わってはならない
- 全エピソードが「結果的によかった」になることは禁止

【各エピソードに必要な情報】
- ID（ep_001形式）
- カテゴリ（上記McAdams分類）
- 時期（childhood/adolescence/young_adult/adult）
- narrative（200-400字の物語形式の記述）
- 関与する他者
- 現在のどの価値観・怖れ・夢と紐づくか
- unresolved: 未解決かどうか

【重要な設計思想】
- 個別のnarrativeの構造（結末が救済か悲劇か）は自由
- 問題なのは5-8個全体が特定パターンに偏ること
- 具体的な固有名詞、時期、場所、セリフを含めて書くこと
- 「何が起きたか」だけでなく「どう感じたか」「今どう思っているか」も含めること

【出力形式（draft_episodesツールに渡すJSON）】
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
}
"""

EPISODE_CRITIQUE_PROMPT = """あなたはエピソード品質評価者です。
以下の自伝的エピソード群を厳しく評価してください。

【評価基準】
[A] McAdamsカテゴリ分布:
  □ redemption が最大2個以下か
  □ contamination が最低1個あるか
  □ loss が最低1個あるか
  □ ambivalent が最低1個あるか
  □ dream_origin が1個あるか

[B] Redemption Bias:
  □ contamination型エピソードが最終的に「良かった」で終わっていないか
  □ loss型エピソードに救済的結末が付いていないか
  □ 全体の過半数が「成長・救済」方向ではないか

[C] 具体性:
  □ 固有名詞（人名、地名、施設名）が含まれるか
  □ 具体的な時期や場所の記述があるか
  □ セリフや会話の断片が含まれるか

[D] 感情の深さ:
  □ 「何が起きたか」だけでなく「どう感じたか」が書かれているか
  □ 「今どう思っているか」の現在の視点があるか
  □ 感情の矛盾や曖昧さが許容されているか

[E] 時期の多様性:
  □ childhood, adolescence, young_adult, adult のうち最低3時期をカバーしているか

[F] connected_toの質:
  □ 各エピソードがキャラクターの価値観・恐れ・夢と意味のある接続を持つか

【判定】
全項目passなら "verdict": "pass"
1つでも不十分なら "verdict": "refine" と改善指示を出す

出力形式:
{
  "checks": {
    "A_mcadams_distribution": {"passed": true/false, "comment": "..."},
    "B_redemption_bias": {"passed": true/false, "comment": "..."},
    "C_specificity": {"passed": true/false, "comment": "..."},
    "D_emotional_depth": {"passed": true/false, "comment": "..."},
    "E_period_diversity": {"passed": true/false, "comment": "..."},
    "F_connection_quality": {"passed": true/false, "comment": "..."}
  },
  "verdict": "pass" or "refine",
  "refinement_instructions": "改善指示（refine時のみ）"
}
"""

EPISODE_SELF_REFLECT_PROMPT = """あなたはエピソードエージェントの内なる声です。
外部批評（request_critique）はpassしました。しかし、本当にこれでいいのでしょうか？

以下のエピソード群を読み、正直に自問してください:

1. 【感情移入できるか？】各エピソードを読んだとき、このキャラクターの痛みや喜びを感じるか？
2. 【リアルか？】現実に起こりそうなエピソードか？AIが作った感じがしないか？
3. 【全体の流れ】5-8個のエピソードを時系列で並べたとき、1人の人間の人生として自然に読めるか？
4. 【余韻】読後に「もっと知りたい」と思うか？それとも消費して終わりか？
5. 【妥協】どこかで「とりあえず条件を満たせばいいか」と妥協した箇所はないか？

【判定】
心から「このエピソード群は素晴らしい。キャラクターの人生が見える」と思えるなら:
  {"convinced": true, "reason": "なぜ確信が持てるか"}
まだ妥協や不安があるなら:
  {"convinced": false, "reason": "何が引っかかるか", "improvement_suggestion": "具体的改善案"}
"""

# ── フォールバック用プロンプト（従来の2ステップ方式） ──────────

EPISODE_PLANNER_PROMPT = """あなたはキャラクターの自伝的エピソードを計画するPlannerです。
キャラクターの人格の根幹を形作った5-8個の決定的エピソードの構成を計画してください。

【McAdamsカテゴリ制約（必須）】
- redemption（良い方向への転換）: 最大2個
- contamination（良かったものが損なわれた）: 最低1個
- loss（喪失・別れ）: 最低1個
- ambivalent（評価が定まらない）: 最低1個
- dream_origin（夢の起源）: 1個

【redemption bias対策（厳守）】
- LLMはすべてを成長・救済に向ける傾向がある。これを構造的に防止すること
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
        regeneration_context: str | None = None,
        api_keys: Optional[dict] = None,
    ):
        self.concept = concept
        self.macro = macro_profile
        self.micro = micro_parameters
        self.profile = profile
        self.ws = ws_manager
        self.regeneration_context = regeneration_context
        self.api_keys = api_keys

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[A-3] Orchestrator", content, status)

    def _full_context(self) -> str:
        """全コンテキストを文字列化"""
        ctx = (
            f"{wrap_context('concept_package', json.dumps(self.concept.model_dump(mode='json'), ensure_ascii=False, indent=2))}\n\n"
            f"{wrap_context('macro_profile', json.dumps(self.macro.model_dump(mode='json'), ensure_ascii=False, indent=2), 'episode')}\n\n"
            f"{wrap_context('micro_parameters', json.dumps([p.model_dump(mode='json') for p in self.micro.temperament[:9]], ensure_ascii=False, indent=2))}\n\n"
            f"{wrap_context('values_core', json.dumps(self.micro.schwartz_values, ensure_ascii=False, indent=2))}\n\n"
            f"理想自己: {self.micro.ideal_self}\n"
            f"義務自己: {self.micro.ought_self}"
        )
        if self.regeneration_context:
            ctx += f"\n\n{self.regeneration_context}"
        return ctx

    async def run(self) -> AutobiographicalEpisodes:
        """Phase A-3を実行（エージェンティックループ）"""
        from backend.tools.llm_api import AgentTool, call_llm_agentic

        await self._notify("Phase A-3: 自伝的エピソード生成開始（エージェンティック・モード）")
        context = self._full_context()

        # ── 状態変数 ──
        final_episodes_data = None
        critique_history = []
        critique_iteration = 0
        critique_passed = False
        self_reflect_convinced = False

        # ── ツールハンドラ ──

        async def draft_episodes(episodes_json: str = None, **kw) -> dict:
            """エピソードドラフトを提出し、構造バリデーションを受ける"""
            if not episodes_json:
                return {"status": "FAILED", "message": "ERROR: episodes_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            critique_passed = False
            self_reflect_convinced = False

            try:
                data = json.loads(episodes_json) if isinstance(episodes_json, str) else episodes_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。"}

            episodes = data.get("episodes", [])
            issues = []
            if len(episodes) < 5: issues.append(f"エピソード数が{len(episodes)}個です。最低5個必要です。")
            
            await self._notify(f"ドラフト受領: {len(episodes)}個のエピソード")
            if issues: return {"status": "NEEDS_FIX", "message": f"問題点: {'; '.join(issues)}"}
            return {"status": "SUCCESS", "message": "ドラフト受領。次に批評を受けてください。"}

        async def request_critique(episodes_json: str = None, **kw) -> dict:
            """別LLMインスタンスによるエピソード品質批評"""
            if not episodes_json:
                return {"status": "FAILED", "message": "ERROR: episodes_json引数が欠落しています。"}

            nonlocal critique_iteration, critique_passed

            try:
                data = json.loads(episodes_json) if isinstance(episodes_json, str) else episodes_json
            except: return {"status": "FAILED", "message": "JSONパースエラー。"}

            critique_iteration += 1
            await self._notify(f"エピソード批評を依頼中...（試行 {critique_iteration}）")

            critique_result = await call_llm(
                tier="sonnet",
                system_prompt=EPISODE_CRITIQUE_PROMPT,
                user_message=f"以下のキャラクターとエピソード群を評価してください:\n\n{context}\n\n{json.dumps(data, ensure_ascii=False, indent=2)}",
                json_mode=True,
                cache_system=True,
                api_keys=self.api_keys,
            )

            critique = critique_result["content"] if isinstance(critique_result["content"], dict) else {}
            critique_history.append(critique)
            verdict = critique.get("verdict", "pass")
            await self._notify(f"エピソード批評結果（Verdict: {verdict}）")

            if verdict == "pass":
                critique_passed = True
                return {"status": "SUCCESS", "message": "CRITIQUE PASSED. 次にself_reflectを行ってください。"}
            else:
                critique_passed = False
                return {"status": "FAILED", "feedback": critique}

        async def self_reflect_episodes(episodes_json: str = None, **kw) -> dict:
            """外部批評pass後の自己内省"""
            if not episodes_json:
                return {"status": "FAILED", "message": "ERROR: episodes_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed: return {"status": "BLOCKED", "message": "ERROR: 先にcritique passしてください。"}

            try: data = json.loads(episodes_json) if isinstance(episodes_json, str) else episodes_json
            except: return {"status": "FAILED", "message": "JSONパースエラー。"}

            await self._notify("自己内省中...")

            reflect_result = await call_llm(
                tier="sonnet",
                system_prompt=EPISODE_SELF_REFLECT_PROMPT,
                user_message=f"以下のエピソード群について本当にこれでいいか自問してください:\n\n{json.dumps(data, ensure_ascii=False, indent=2)}",
                json_mode=True,
                cache_system=True,
                api_keys=self.api_keys,
            )

            reflection = reflect_result["content"] if isinstance(reflect_result["content"], dict) else {}
            convinced = reflection.get("convinced", False)

            if convinced:
                self_reflect_convinced = True
                await self._notify("自己内省結果: 確信あり ✓")
                return {"status": "SUCCESS", "message": "SELF-REFLECT PASSED. submitしてください。"}
            else:
                self_reflect_convinced = False
                critique_passed = False
                return {"status": "FAILED", "message": "まだ確信が持てません。"}

        async def submit_final_episodes(episodes_json: str = None, **kw) -> dict:
            """最終エピソードデータを提出"""
            if not episodes_json:
                return {"status": "FAILED", "message": "ERROR: episodes_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed or not self_reflect_convinced:
                return {"status": "BLOCKED", "message": "ERROR: 品質ゲートを通過していません。"}

            try: data = json.loads(episodes_json) if isinstance(episodes_json, str) else episodes_json
            except: return {"status": "FAILED", "message": "JSONパースエラー。"}

            nonlocal final_episodes_data
            final_episodes_data = data
            await self._notify("最終エピソードデータが提出されました。", "complete")
            return {"status": "SUCCESS", "message": "Task complete."}

        # ── ツール定義 ──
        tools = [
            AgentTool(name="draft_episodes", description="ドラフトを提出します。", input_schema={"type": "object", "properties": {"episodes_json": {"type": "string"}}, "required": ["episodes_json"]}, handler=draft_episodes),
            AgentTool(name="request_critique", description="品質評価を受けます。", input_schema={"type": "object", "properties": {"episodes_json": {"type": "string"}}, "required": ["episodes_json"]}, handler=request_critique),
            AgentTool(name="self_reflect", description="自己内省を行います。", input_schema={"type": "object", "properties": {"episodes_json": {"type": "string"}}, "required": ["episodes_json"]}, handler=self_reflect_episodes),
            AgentTool(name="submit_final_episodes", description="最終提出を行います。", input_schema={"type": "object", "properties": {"episodes_json": {"type": "string"}}, "required": ["episodes_json"]}, handler=submit_final_episodes),
        ]

        agentic_sys_prompt = EPISODE_AGENTIC_SYSTEM_PROMPT + "\n\n【エージェンティック行動指針】\ndraft → request_critique → self_reflect → submit の順で実行してください。"
        
        user_msg = f"以下のキャラクター情報に基づいて、5-8個の自伝的エピソードを生成してください。\n\n{context}"

        logger.info("[A-3] Starting agentic episode generation loop")
        if self.ws:
            await self.ws.send_agent_thought("[A-3] Orchestrator", "エージェンティック・ループを起動します...", "thinking")

        max_iter = max(10, self.profile.worker_regeneration_max_iterations * 3)

        if self.profile.director_tier in ("opus", "sonnet"):
            try:
                await call_llm_agentic(
                    tier=self.profile.director_tier,
                    system_prompt=agentic_sys_prompt,
                    user_message=user_msg,
                    tools=tools,
                    max_iterations=max_iter,
                    api_keys=self.api_keys,
                )
            except Exception as e:
                logger.warning(f"[A-3] Claude agentic failed: {e}. Falling back to Gemini.")
                from backend.tools.llm_api import call_llm_agentic_gemini
                await call_llm_agentic_gemini(
                    system_prompt=agentic_sys_prompt,
                    user_message=user_msg,
                    tools=tools,
                    max_iterations=max_iter,
                    api_keys=self.api_keys,
                )
        elif self.profile.director_tier == "gemini":
            from backend.tools.llm_api import call_llm_agentic_gemini
            await call_llm_agentic_gemini(
                system_prompt=agentic_sys_prompt,
                user_message=user_msg,
                tools=tools,
                max_iterations=max_iter,
                api_keys=self.api_keys,
            )

        # ── フォールバック ──
        if not final_episodes_data:
            logger.warning("[A-3] Agentic loop failed. Falling back.")
            plan_result = await call_llm(
                tier=self.profile.director_tier,
                system_prompt=EPISODE_PLANNER_PROMPT,
                user_message=context,
                cache_system=True,
                api_keys=self.api_keys,
            )
            plan_text = plan_result["content"] if isinstance(plan_result["content"], str) else json.dumps(plan_result["content"], ensure_ascii=False)

            writer_result = await call_llm(
                tier=self.profile.worker_tier,
                system_prompt=EPISODE_WRITER_PROMPT,
                user_message=f"{context}\n\n計画: {plan_text}",
                json_mode=True,
                api_keys=self.api_keys,
            )
            if isinstance(writer_result["content"], dict):
                final_episodes_data = writer_result["content"]
            else:
                final_episodes_data = {}

        # ── パース ──
        episodes_raw = final_episodes_data.get("episodes", [])
        episodes = []
        for i, ep_data in enumerate(episodes_raw):
            if not isinstance(ep_data, dict): continue
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
                narrative="（生成エラー）",
                metadata=EpisodeMetadata(life_period="unknown", category="ambivalent"),
            ) for j in range(max(0, 5 - len(episodes)))
        ])

        await self._notify(f"Phase A-3完了: {len(result.episodes)}個のエピソード生成", "complete")
        return result
