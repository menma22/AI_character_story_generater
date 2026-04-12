"""
CharacterCapabilitiesAgent
所持品・能力・可能行動をエージェンティックループで生成する。

設計方針:
- 必ず2回以上のWeb検索でキャラクターの職業・世界観・背景に関する具体的情報を収集してからドラフトを作成する。
- draft → request_critique → self_reflect → submit の品質ゲート付きループで品質を担保する。
- Creative Director と同様のエージェントアーキテクチャ。
"""

import json
import logging
from typing import Optional

from backend.config import EvaluationProfile, LLMModels
from backend.models.character import (
    ConceptPackage, MacroProfile,
    CharacterCapabilities, PossessedItem, CharacterAbility, AvailableAction,
)
from backend.tools.llm_api import call_llm, AgentTool, call_llm_agentic

logger = logging.getLogger(__name__)

# ── システムプロンプト ─────────────────────────────────────────────

CAPABILITIES_AGENT_SYSTEM_PROMPT = """あなたはキャラクターの所持品・能力・可能行動を設計するエージェントです。
Creative Directorの意向（concept_package）とキャラクターのマクロプロフィールに基づき、
キャラクターが実際に持っているもの、できること、能力などの情報を「濃密に」設計してください。

【最重要】concept_package の capabilities_hints（key_possessions_hint / core_abilities_hint / signature_actions_hint）が存在する場合、
それを具体化の起点・方向性として必ず反映してください。hintsが示した方向性に沿って、各アイテム・能力・行動を具体化すること。

【設計原則】
2. 能力はキャラクターの歴史・背景から自然に導かれるものにすること（突然の異能は不可）
3. 可能行動はイベント生成時に実際に「この人物ならこう動く」と使えるレベルの具体性を持たせること
4. AI臭い無難なアイテム・能力リストは失格。「このキャラクター以外には持てないもの」を目指すこと

【出力形式（submit_final_capabilitiesに渡すJSON）】
{
  "possessions": [
    {
      "name": "アイテム名",
      "description": "見た目・用途の説明（2-4文、具体的に）",
      "always_carried": true/false,
      "emotional_significance": "このキャラクターにとっての感情的意味（必ず記述。1-3文）"
    }
  ],
  "abilities": [
    {
      "name": "能力名",
      "description": "能力の説明（何ができるか、どの程度か、2-4文）",
      "proficiency": "novice/medium/expert",
      "origin": "どこで・いつ・どうやって身につけたか（1-3文）"
    }
  ],
  "available_actions": [
    {
      "action": "行動名（動詞+目的語の形式）",
      "context": "どんな場面・状況で使えるか（具体的なシーン描写）",
      "prerequisites": "この行動を取るために必要な前提条件"
    }
  ]
}

【数量制約】
- possessions: 5-10個（常時携帯品を少なくとも2個含む）
- abilities: 3-5個（職業・背景から自然に導かれるもの）
- available_actions: 3-5個（イベント対応で実際に使えるもの）
"""

# ── 批評プロンプト ────────────────────────────────────────────────

CAPABILITIES_CRITIQUE_PROMPT = """あなたはキャラクター所持品・能力・可能行動の品質評価者です。
以下の設計を厳しく評価してください。

【評価基準】

[A] 所持品の密度:
  □ possessionsが5個以上あるか
  □ 各アイテムにemotional_significanceが具体的に記述されているか（「大事なもの」等の抽象語はNG）
  □ always_carried=trueのアイテムが少なくとも2個あるか
  □ キャラクターの職業・価値観・背景と整合するか
  □ 「誰でも持ちそうな汎用アイテム」が大半を占めていないか

[B] 能力の整合性:
  □ abilitiesが3個以上あるか
  □ 各能力のoriginがキャラクターの人生史と具体的に接続されているか
  □ proficiencyの分布が現実的か（全てexpertは不自然）
  □ capabilities_hintsのcore_abilities_hintが反映されているか

[C] 可能行動の物語的有用性:
  □ available_actionsが3個以上あるか
  □ 各行動がイベント生成時に実際に使える具体性を持つか
  □ contextが「どんな場面で使えるか」を具体的なシーン描写で示しているか
  □ signature_actionsとして「このキャラクターにしかできない行動」が含まれるか

[D] キャラクター固有性:
  □ この設計全体が、他のキャラクターには当てはまらないユニークさを持つか
  □ concept_packageのcapabilities_hintsの方向性が反映されているか
  □ AI臭い無難さ・汎用性が出ていないか

[E] 具体性:
  □ 固有名詞・具体的な描写・感情的背景が含まれるか
  □ 抽象的・曖昧な記述で誤魔化されていないか

【判定】
全項目passなら "verdict": "pass"
1つでも不十分なら "verdict": "refine" と改善指示を出す

出力形式:
{
  "checks": {
    "A_possession_density": {"passed": true/false, "comment": "..."},
    "B_ability_consistency": {"passed": true/false, "comment": "..."},
    "C_action_utility": {"passed": true/false, "comment": "..."},
    "D_character_uniqueness": {"passed": true/false, "comment": "..."},
    "E_specificity": {"passed": true/false, "comment": "..."}
  },
  "verdict": "pass" or "refine",
  "refinement_instructions": "改善指示（refine時のみ）"
}
"""

# ── 内省プロンプト ────────────────────────────────────────────────

CAPABILITIES_SELF_REFLECT_PROMPT = """あなたはキャラクター所持品・能力エージェントの内なる声です。
外部批評（request_critique）はpassしました。しかし、本当にこれでいいのでしょうか？

以下の設計を読み、正直に自問してください:

1. 【固有性】この所持品リストを見ただけで、「このキャラクターだ」とわかるか？
   誰にでも当てはまるような汎用品が大半を占めていないか？
3. 【能力の根拠】abilitiesのoriginを読んで、「なるほど、この人が持つのは自然だ」と思えるか？
   唐突に付け足した感のある能力はないか？
4. 【行動の実用性】available_actionsは、主人公がイベント生成時に実際に使えるか？
   あまりにも限定的すぎたり、逆に汎用的すぎたりしないか？
5. 【妥協】数を合わせるために適当に追加したアイテムや能力はないか？

【判定】
心から「この設計は濃密で、このキャラクターの全てが表れている」と思えるなら:
  {"convinced": true, "reason": "なぜ確信が持てるか"}
まだ妥協や不安があるなら:
  {"convinced": false, "reason": "何が引っかかるか", "improvement_suggestion": "具体的改善案"}

正直に。甘い判定は下流イベント生成の質を損なう。
"""

MIN_SEARCHES = 2


class CharacterCapabilitiesAgent:
    """
    CharacterCapabilitiesAgent

    所持品・能力・可能行動をエージェンティックループで生成する。
    必ず2回以上のWeb検索を行ってからドラフトを作成し、
    批評・内省の品質ゲートを通過したもののみを提出する。
    """

    def __init__(
        self,
        concept: ConceptPackage,
        macro_profile: MacroProfile,
        context: str,
        profile: EvaluationProfile,
        ws_manager=None,
        api_keys: Optional[dict] = None,
    ):
        self.concept = concept
        self.macro = macro_profile
        self.context = context  # 上流コンテキスト（full_context文字列）
        self.profile = profile
        self.ws = ws_manager
        self.api_keys = api_keys

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("[CapabilitiesAgent]", content, status)

    async def run(self) -> CharacterCapabilities:
        """エージェンティックループで所持品・能力・可能行動を生成する"""
        await self._notify("CharacterCapabilitiesAgent 起動（エージェンティック・モード）")

        # ── 状態変数 ──
        final_caps_data: Optional[dict] = None
        search_count = 0
        critique_passed = False
        self_reflect_convinced = False
        critique_history = []

        # ── ツールハンドラ ──

        async def search_web(query: str = None, max_results: int = 3) -> dict:
            """キャラクターの職業・背景・世界観に関するWeb検索"""
            if not query:
                return {"status": "FAILED", "message": "ERROR: query引数が欠落しています。"}

            nonlocal search_count
            search_count += 1
            await self._notify(f"Web検索中 ({search_count}回目): {query}")
            try:
                from duckduckgo_search import DDGS
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(r)
                if results:
                    return {"status": "SUCCESS", "search_count": search_count, "results": results}
                else:
                    return {"status": "SUCCESS", "search_count": search_count, "message": "No results found."}
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                return {"status": "FAILED", "message": f"検索失敗: {e}"}

        async def draft_capabilities(capabilities_json: str = None, **kw) -> dict:
            """所持品・能力・可能行動のドラフトを提出して構造バリデーションを受ける"""
            if not capabilities_json:
                return {"status": "FAILED", "message": "ERROR: capabilities_json引数が欠落しています。"}

            if search_count < MIN_SEARCHES:
                return {
                    "status": "BLOCKED",
                    "message": f"ERROR: Web検索が{search_count}回しか実行されていません。最低{MIN_SEARCHES}回のsearch_webを実行してからdraft_capabilitiesを呼び出してください。",
                }

            nonlocal critique_passed, self_reflect_convinced
            critique_passed = False
            self_reflect_convinced = False

            try:
                data = json.loads(capabilities_json) if isinstance(capabilities_json, str) else capabilities_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。有効なJSON文字列を渡してください。"}

            issues = []
            possessions = data.get("possessions", [])
            abilities = data.get("abilities", [])
            actions = data.get("available_actions", [])

            if len(possessions) < 5:
                issues.append(f"possessionsが{len(possessions)}個です。最低5個必要です。")
            if len(abilities) < 3:
                issues.append(f"abilitiesが{len(abilities)}個です。最低3個必要です。")
            if len(actions) < 3:
                issues.append(f"available_actionsが{len(actions)}個です。最低3個必要です。")

            await self._notify(f"ドラフト受領: 所持品{len(possessions)}個・能力{len(abilities)}個・行動{len(actions)}個")

            if issues:
                return {"status": "NEEDS_FIX", "message": f"問題点: {'; '.join(issues)}"}

            return {"status": "SUCCESS", "message": "ドラフト受領。次にrequest_critiqueで品質評価を受けてください。"}

        async def request_critique(capabilities_json: str = None, **kw) -> dict:
            """別LLMによる所持品・能力設計の品質批評"""
            if not capabilities_json:
                return {"status": "FAILED", "message": "ERROR: capabilities_json引数が欠落しています。"}

            nonlocal critique_passed

            try:
                data = json.loads(capabilities_json) if isinstance(capabilities_json, str) else capabilities_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。"}

            iteration = len(critique_history) + 1
            await self._notify(f"品質批評を依頼中...（試行 {iteration}）")

            critique_result = await call_llm(
                tier="sonnet",
                system_prompt=CAPABILITIES_CRITIQUE_PROMPT,
                user_message=(
                    f"以下のキャラクター情報と所持品・能力設計を評価してください:\n\n"
                    f"{self.context}\n\n"
                    f"【評価対象】\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                ),
                json_mode=True,
                cache_system=True,
                api_keys=self.api_keys,
            )

            critique = critique_result["content"] if isinstance(critique_result["content"], dict) else {}
            critique_history.append(critique)

            checks = critique.get("checks", {})
            check_summary = []
            for key, val in checks.items():
                status_symbol = "✓" if val.get("passed", False) else "✗"
                check_summary.append(f"  [{status_symbol}] {key}: {val.get('comment', '')[:70]}")

            verdict = critique.get("verdict", "pass")
            await self._notify(f"批評結果（Verdict: {verdict}）:\n" + "\n".join(check_summary))

            if verdict == "pass":
                critique_passed = True
                return {"status": "SUCCESS", "message": "CRITIQUE PASSED. 次にself_reflectで自己内省を行ってください。"}
            else:
                critique_passed = False
                return {"status": "FAILED", "feedback": critique}

        async def self_reflect(capabilities_json: str = None, **kw) -> dict:
            """批評pass後の自己内省 — 本当にこれでいいか問う"""
            if not capabilities_json:
                return {"status": "FAILED", "message": "ERROR: capabilities_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed:
                return {"status": "BLOCKED", "message": "ERROR: 先にrequest_critiqueでpassを得てください。"}

            try:
                data = json.loads(capabilities_json) if isinstance(capabilities_json, str) else capabilities_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。"}

            await self._notify("自己内省中...「本当にこの設計で十分か？」")

            reflect_result = await call_llm(
                tier="sonnet",
                system_prompt=CAPABILITIES_SELF_REFLECT_PROMPT,
                user_message=(
                    f"以下の所持品・能力設計について、本当にこれでいいか正直に自問してください:\n\n"
                    f"{json.dumps(data, ensure_ascii=False, indent=2)}"
                ),
                json_mode=True,
                cache_system=True,
                api_keys=self.api_keys,
            )

            reflection = reflect_result["content"] if isinstance(reflect_result["content"], dict) else {}
            convinced = reflection.get("convinced", False)

            if convinced:
                self_reflect_convinced = True
                await self._notify(f"自己内省結果: 確信あり ✓ — {reflection.get('reason', '')[:80]}")
                return {"status": "SUCCESS", "message": "SELF-REFLECT PASSED. submit_final_capabilitiesで提出してください。"}
            else:
                self_reflect_convinced = False
                critique_passed = False
                reason = reflection.get("reason", "不明")
                suggestion = reflection.get("improvement_suggestion", "")
                await self._notify(f"自己内省結果: まだ妥協あり ✗ — {reason[:80]}")
                return {"status": "FAILED", "message": f"まだ確信が持てません。理由: {reason}。改善案: {suggestion}"}

        async def submit_final_capabilities(capabilities_json: str = None, **kw) -> dict:
            """品質ゲート通過後の最終提出"""
            if not capabilities_json:
                return {"status": "FAILED", "message": "ERROR: capabilities_json引数が欠落しています。"}

            nonlocal critique_passed, self_reflect_convinced
            if not critique_passed or not self_reflect_convinced:
                blocked_reasons = []
                if not critique_passed:
                    blocked_reasons.append("request_critiqueでpassを得ていない")
                if not self_reflect_convinced:
                    blocked_reasons.append("self_reflectで確信を得ていない")
                return {"status": "BLOCKED", "message": f"ERROR: 提出がブロックされました。理由: {', '.join(blocked_reasons)}"}

            try:
                data = json.loads(capabilities_json) if isinstance(capabilities_json, str) else capabilities_json
            except json.JSONDecodeError:
                return {"status": "FAILED", "message": "JSONパースエラー。"}

            nonlocal final_caps_data
            final_caps_data = data
            await self._notify("最終所持品・能力設計が提出されました。", "complete")
            return {"status": "SUCCESS", "message": "Task complete. Thank you."}

        # ── ツール登録 ──
        tools = [
            AgentTool(
                name="search_web",
                description=f"キャラクターの職業・背景・世界観に関するWeb検索。最低{MIN_SEARCHES}回必須。",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "検索クエリ"},
                        "max_results": {"type": "integer", "description": "最大取得件数（デフォルト3）"},
                    },
                    "required": ["query"],
                },
                handler=search_web,
            ),
            AgentTool(
                name="draft_capabilities",
                description=f"所持品・能力・可能行動のドラフトを提出する。search_webを{MIN_SEARCHES}回以上実行後に使用可能。",
                input_schema={
                    "type": "object",
                    "properties": {"capabilities_json": {"type": "string", "description": "所持品・能力・行動のJSONデータ（文字列）"}},
                    "required": ["capabilities_json"],
                },
                handler=draft_capabilities,
            ),
            AgentTool(
                name="request_critique",
                description="設計の品質を別LLMに批評させる。draft_capabilities後に使用可能。",
                input_schema={
                    "type": "object",
                    "properties": {"capabilities_json": {"type": "string"}},
                    "required": ["capabilities_json"],
                },
                handler=request_critique,
            ),
            AgentTool(
                name="self_reflect",
                description="批評passの後、自分自身に本当にこれでいいか問う内省。request_critiqueのpass後のみ使用可能。",
                input_schema={
                    "type": "object",
                    "properties": {"capabilities_json": {"type": "string"}},
                    "required": ["capabilities_json"],
                },
                handler=self_reflect,
            ),
            AgentTool(
                name="submit_final_capabilities",
                description="最終確定版を提出。critique + self_reflect の両方がpassした後のみ使用可能。",
                input_schema={
                    "type": "object",
                    "properties": {"capabilities_json": {"type": "string"}},
                    "required": ["capabilities_json"],
                },
                handler=submit_final_capabilities,
            ),
        ]

        # ── エージェンティックループ起動 ──
        agentic_sys_prompt = (
            CAPABILITIES_AGENT_SYSTEM_PROMPT
            + f"\n\n【エージェンティック行動指針 — 5フェーズ厳守】\n"
            f"(1) リサーチ: search_web を最低{MIN_SEARCHES}回実行し、キャラクターの職業・生活圏・背景に関連する具体的な情報を収集する。\n"
            f"    検索例: キャラの職業名+「道具」「必需品」、キャラの趣味+「用具」「スキル」、世界観+「生活様式」等。\n"
            f"(2) ドラフト: 収集した情報を踏まえてdraft_capabilitiesで提出。{MIN_SEARCHES}回未満の検索ではブロックされる。\n"
            f"(3) 批評: request_critiqueで品質評価を受ける。\n"
            f"(4) 内省: self_reflectで「本当にこれでいいか」を問う。\n"
            f"(5) 提出: submit_final_capabilitiesで最終提出。critique + self_reflect 両方passが必須。\n"
        )

        occupation = self.macro.basic_info.occupation if self.macro.basic_info else "不明"
        char_name = self.macro.basic_info.name if self.macro.basic_info else "キャラクター"

        user_msg = (
            f"以下のキャラクター情報に基づき、{char_name}（職業: {occupation}）の"
            f"所持品・能力・可能行動を設計してください。\n"
            f"まず必ずsearch_webを{MIN_SEARCHES}回以上使って、この職業や背景に関連する具体的な情報を調査してください。\n\n"
            f"{self.context}"
        )

        logger.info(f"[CapabilitiesAgent] Starting agentic loop for {char_name}")
        if self.ws:
            await self.ws.send_agent_thought(
                "[CapabilitiesAgent]",
                f"'{char_name}' の所持品・能力設計を開始します。エージェンティック・ループを起動します...",
                "thinking",
            )

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
                logger.warning(f"[CapabilitiesAgent] Claude agentic failed: {e}. Falling back to Gemini.")
                from backend.tools.llm_api import call_llm_agentic_gemini
                await call_llm_agentic_gemini(
                    system_prompt=agentic_sys_prompt,
                    user_message=user_msg,
                    tools=tools,
                    max_iterations=max_iter,
                    api_keys=self.api_keys,
                )
        elif self.profile.director_tier in ("gemini", "gemini_pro"):
            from backend.tools.llm_api import call_llm_agentic_gemini
            gemini_model = LLMModels.GEMINI_3_1_PRO if self.profile.director_tier == "gemini_pro" else None
            await call_llm_agentic_gemini(
                system_prompt=agentic_sys_prompt,
                user_message=user_msg,
                tools=tools,
                max_iterations=max_iter,
                api_keys=self.api_keys,
                model=gemini_model,
            )
        else:
            raise ValueError(f"Unsupported director tier: {self.profile.director_tier}")

        # ── フォールバック（エージェンティックループが失敗した場合） ──
        if not final_caps_data:
            logger.warning("[CapabilitiesAgent] Agentic loop failed to submit. Falling back to one-shot.")
            fallback_result = await call_llm(
                tier=self.profile.worker_tier,
                system_prompt=CAPABILITIES_AGENT_SYSTEM_PROMPT,
                user_message=f"{self.context}\n\n所持品・能力・可能行動をJSONで出力してください。",
                json_mode=True,
                api_keys=self.api_keys,
            )
            if isinstance(fallback_result["content"], dict):
                final_caps_data = fallback_result["content"]
            else:
                final_caps_data = {}

        # ── パース ──
        caps_text = json.dumps(final_caps_data, ensure_ascii=False)
        try:
            capabilities = CharacterCapabilities(
                possessions=[
                    PossessedItem(**p)
                    for p in final_caps_data.get("possessions", [])
                    if isinstance(p, dict)
                ],
                abilities=[
                    CharacterAbility(**a)
                    for a in final_caps_data.get("abilities", [])
                    if isinstance(a, dict)
                ],
                available_actions=[
                    AvailableAction(**act)
                    for act in final_caps_data.get("available_actions", [])
                    if isinstance(act, dict)
                ],
                raw_text=caps_text,
            )
        except Exception as e:
            logger.warning(f"[CapabilitiesAgent] CharacterCapabilities parse error: {e}")
            capabilities = CharacterCapabilities(raw_text=caps_text)

        await self._notify(
            f"CharacterCapabilitiesAgent 完了: "
            f"所持品{len(capabilities.possessions)}個・"
            f"能力{len(capabilities.abilities)}個・"
            f"行動{len(capabilities.available_actions)}個",
            "complete",
        )
        return capabilities
