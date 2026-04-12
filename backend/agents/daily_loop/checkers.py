"""
4つの個別チェックAI（裏方エージェント）

出来事周辺情報統合エージェントと日記生成エージェントの出力を、
プロフィール・気質・性格パラメータ・価値観のそれぞれに沿っているかチェックする。

これらは裏方エージェントであり、隠蔽原則の制約を受けない（全パラメータ参照可能）。
"""

import json
import logging
from typing import Optional

from backend.models.memory import CheckResult
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


class BaseChecker:
    """チェッカー基底クラス"""

    def __init__(self, checker_type: str, ws_manager=None, tier: str = "gemini", api_keys: Optional[dict] = None):
        self.checker_type = checker_type
        self.ws = ws_manager
        self.tier = tier
        self.api_keys = api_keys

    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought(f"[{self.checker_type}チェック]", content, status)

    async def check(self, output_text: str, context: str) -> CheckResult:
        """出力がコンテキスト（パラメータ等）に沿っているかチェック"""
        raise NotImplementedError


class ProfileChecker(BaseChecker):
    """マクロプロフィール整合性チェック

    出力が以下と整合しているか検証:
    - 名前、年齢、性別、外見
    - 職業、社会的立場、経済状況
    - 家族構成、人間関係
    - 日常ルーティン、趣味、習慣
    """

    def __init__(self, ws_manager=None, tier: str = "gemini", api_keys: Optional[dict] = None):
        super().__init__("プロフィール", ws_manager, tier, api_keys)

    async def check(self, output_text: str, macro_profile_json: str) -> CheckResult:
        await self._notify("プロフィール整合性をチェック中...")

        result = await call_llm(
            tier=self.tier,
            system_prompt="""あなたはキャラクターのプロフィール整合性チェッカーです。
出力テキストがマクロプロフィール（名前・職業・生活様式・人間関係等）と矛盾していないかチェックしてください。

【チェック項目】
- 名前や一人称の一貫性
- 職業・社会的立場に合った行動や言動か
- 生活圏・経済状況と整合するか
- 人間関係の描写が設定と矛盾しないか

出力形式: JSON
{
  "passed": true/false,
  "issues": ["問題点1", "問題点2"],
  "severity": "none/minor/major",
  "suggestion": "修正の示唆（問題がある場合のみ）"
}""",
            user_message=(
                f"【マクロプロフィール】\n{macro_profile_json[:1500]}\n\n"
                f"【チェック対象テキスト】\n{output_text[:2000]}"
            ),
            json_mode=True,
            api_keys=self.api_keys,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        check_result = CheckResult(
            checker_type="profile",
            passed=data.get("passed", True),
            issues=data.get("issues", []),
            severity=data.get("severity", "none"),
            suggestion=data.get("suggestion", ""),
        )
        status_mark = "✓" if check_result.passed else f"✗ ({check_result.severity})"
        await self._notify(f"プロフィールチェック完了: {status_mark}", "complete")
        return check_result


class TemperamentChecker(BaseChecker):
    """気質パラメータ整合性チェック

    出力がCloningerモデルの気質パラメータ（#1-#23）に整合しているか検証。
    裏方エージェントのため、パラメータ名・値に直接アクセス可能。
    """

    def __init__(self, ws_manager=None, tier: str = "gemini", api_keys: Optional[dict] = None):
        super().__init__("気質", ws_manager, tier, api_keys)

    async def check(self, output_text: str, activated_temperament_text: str, memory_context: str = "") -> CheckResult:
        await self._notify("気質パラメータ整合性をチェック中...")

        result = await call_llm(
            tier=self.tier,
            system_prompt="""あなたはキャラクターの気質パラメータ整合性チェッカーです。
出力テキストの行動・反応が、活性化された気質パラメータ（Cloningerモデル: 新奇性追求・損害回避・報酬依存・固執性）
と整合しているかチェックしてください。

【判定ロジック（優先順位）】
1. 短期記憶（key memory・デイリーログ）のコンテキストを最優先で参照する
2. 出力が気質パラメータと乖離している場合:
   - 短期記憶の内容から妥当と判断できる → 合格（理由を記載）
   - 短期記憶からも説明できない → 不合格
3. 短期記憶からも気質パラメータからも説明できない行動 → 絶対不合格（severity: major）

【チェック例】
- 損害回避が高い(4-5)のに、危険を無視した行動 → ただし短期記憶に「リスクを取る決意をした」記録があれば合格
- 新奇性追求が低い(1-2)のに、突飛な冒険をしている → 短期記憶で説明できなければ不整合
- 報酬依存が高いのに、他者の反応を全く気にしない → 短期記憶で説明できなければ不整合

出力形式: JSON
{
  "passed": true/false,
  "issues": ["問題点1", "問題点2"],
  "severity": "none/minor/major",
  "suggestion": "修正の示唆（問題がある場合のみ）"
}""",
            user_message=(
                f"【短期記憶コンテキスト（最優先参照）】\n{memory_context[:1000]}\n\n"
                f"【活性化された気質パラメータ】\n{activated_temperament_text}\n\n"
                f"【チェック対象テキスト】\n{output_text[:2000]}"
            ),
            json_mode=True,
            api_keys=self.api_keys,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        check_result = CheckResult(
            checker_type="temperament",
            passed=data.get("passed", True),
            issues=data.get("issues", []),
            severity=data.get("severity", "none"),
            suggestion=data.get("suggestion", ""),
        )
        status_mark = "✓" if check_result.passed else f"✗ ({check_result.severity})"
        await self._notify(f"気質チェック完了: {status_mark}", "complete")
        return check_result


class PersonalityChecker(BaseChecker):
    """性格パラメータ整合性チェック

    出力がBig Five/HEXACOの性格パラメータ（#24-#50）に整合しているか検証。
    """

    def __init__(self, ws_manager=None, tier: str = "gemini", api_keys: Optional[dict] = None):
        super().__init__("性格", ws_manager, tier, api_keys)

    async def check(self, output_text: str, activated_personality_text: str, memory_context: str = "") -> CheckResult:
        await self._notify("性格パラメータ整合性をチェック中...")

        result = await call_llm(
            tier=self.tier,
            system_prompt="""あなたはキャラクターの性格パラメータ整合性チェッカーです。
出力テキストの行動・態度が、活性化された性格パラメータ（Big Five/HEXACO: 外向性・協調性・誠実性・神経症傾向・開放性等）
と整合しているかチェックしてください。

【判定ロジック（優先順位）】
1. 短期記憶（key memory・デイリーログ）のコンテキストを最優先で参照する
2. 出力が性格パラメータと乖離している場合:
   - 短期記憶の内容から妥当と判断できる → 合格（理由を記載）
   - 短期記憶からも説明できない → 不合格
3. 短期記憶からも性格パラメータからも説明できない行動 → 絶対不合格（severity: major）

【チェック例】
- 外向性が低い(1-2)のに、見知らぬ人に積極的に話しかけている → ただし短期記憶に「殻を破ろうとしている」記録があれば合格
- 協調性が高い(4-5)のに、対立的・攻撃的な言動ばかり → 短期記憶で説明できなければ不整合
- 誠実性が高いのに、約束を平気で破る描写 → 短期記憶で説明できなければ不整合

出力形式: JSON
{
  "passed": true/false,
  "issues": ["問題点1", "問題点2"],
  "severity": "none/minor/major",
  "suggestion": "修正の示唆（問題がある場合のみ）"
}""",
            user_message=(
                f"【短期記憶コンテキスト（最優先参照）】\n{memory_context[:1000]}\n\n"
                f"【活性化された性格パラメータ】\n{activated_personality_text}\n\n"
                f"【チェック対象テキスト】\n{output_text[:2000]}"
            ),
            json_mode=True,
            api_keys=self.api_keys,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        check_result = CheckResult(
            checker_type="personality",
            passed=data.get("passed", True),
            issues=data.get("issues", []),
            severity=data.get("severity", "none"),
            suggestion=data.get("suggestion", ""),
        )
        status_mark = "✓" if check_result.passed else f"✗ ({check_result.severity})"
        await self._notify(f"性格チェック完了: {status_mark}", "complete")
        return check_result


class ValuesChecker(BaseChecker):
    """価値観整合性チェック

    出力がSchwartz価値観、道徳基盤理論(MFT)、理想自己・義務自己と整合しているか検証。
    ※ 価値観違反チェック（§4.6c）とは別に、出力の全体的な価値観一貫性を検証する。
    """

    def __init__(self, ws_manager=None, tier: str = "gemini", api_keys: Optional[dict] = None):
        super().__init__("価値観", ws_manager, tier, api_keys)

    async def check(self, output_text: str, values_context: str) -> CheckResult:
        await self._notify("価値観整合性をチェック中...")

        result = await call_llm(
            tier=self.tier,
            system_prompt="""あなたはキャラクターの価値観整合性チェッカーです。
出力テキストの行動・判断が、Schwartz価値観・道徳基盤理論・理想自己・義務自己
と全体的に整合しているかチェックしてください。

【チェック項目】
- 行動がSchwartz価値観の「strong」項目に反していないか
- 理想自己・義務自己と大きく乖離する行動がないか
- 道徳的判断の方向性が一貫しているか

出力形式: JSON
{
  "passed": true/false,
  "issues": ["問題点1", "問題点2"],
  "severity": "none/minor/major",
  "suggestion": "修正の示唆（問題がある場合のみ）"
}""",
            user_message=(
                f"【価値観コンテキスト】\n{values_context}\n\n"
                f"【チェック対象テキスト】\n{output_text[:2000]}"
            ),
            json_mode=True,
            api_keys=self.api_keys,
        )
        data = result["content"] if isinstance(result["content"], dict) else {}
        check_result = CheckResult(
            checker_type="values",
            passed=data.get("passed", True),
            issues=data.get("issues", []),
            severity=data.get("severity", "none"),
            suggestion=data.get("suggestion", ""),
        )
        status_mark = "✓" if check_result.passed else f"✗ ({check_result.severity})"
        await self._notify(f"価値観チェック完了: {status_mark}", "complete")
        return check_result
