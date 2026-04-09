"""
Evaluator群（v2 §8 完全準拠）

Tier 3 品質評価レイヤー。
各Phaseの出力品質をチェックし、不合格時は再生成を指示する。

構成:
1. SchemaValidator（ルールベース、全プロファイルON）
2. ConsistencyChecker（LLM、Standard以上）
3. BiasAuditor（LLM、Phase A-3用、Fast以上）
4. InterestingnessEvaluator（LLM、High Quality）
5. EventMetadataAuditor（ルール+LLM、Phase D用、Fast以上）
6. DistributionValidator（ルールベース、全プロファイルON）
7. NarrativeConnectionAuditor（LLM、Standard以上）
"""

import json
import logging
from typing import Optional
from pydantic import BaseModel

from backend.config import EvaluationProfile
from backend.models.character import (
    ConceptPackage, MacroProfile, MicroParameters,
    AutobiographicalEpisodes, WeeklyEventsStore,
)
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """評価結果"""
    evaluator: str
    passed: bool
    error: str = ""
    details: list[str] = []


# ═══════════════════════════════════════════════════════════════
# 1. SchemaValidator（ルールベース）
# ═══════════════════════════════════════════════════════════════

class SchemaValidator:
    """JSON schema準拠チェック（ルールベース、コストゼロ）"""
    
    @staticmethod
    def validate_macro_profile(profile: MacroProfile) -> ValidationResult:
        errors = []
        bi = profile.basic_info
        if not bi.name:
            errors.append("basic_info.name が空です")
        if not bi.age or bi.age <= 0:
            errors.append("basic_info.age が無効です")
        if not bi.gender:
            errors.append("basic_info.gender が空です")
        if not profile.voice_fingerprint.first_person:
            errors.append("voice_fingerprint.first_person が空です")
        if len(profile.voice_fingerprint.avoided_words) == 0:
            errors.append("voice_fingerprint.avoided_words が空です（最低2個必要）")
        if not profile.values_core.most_important:
            errors.append("values_core.most_important が空です")
        
        return ValidationResult(
            evaluator="SchemaValidator",
            passed=len(errors) == 0,
            error="; ".join(errors),
            details=errors,
        )
    
    @staticmethod
    def validate_micro_parameters(params: MicroParameters) -> ValidationResult:
        errors = []
        if len(params.temperament) < 20:
            errors.append(f"気質パラメータが{len(params.temperament)}個しかない（23個必要）")
        if len(params.personality) < 20:
            errors.append(f"性格パラメータが{len(params.personality)}個しかない（27個必要）")
        
        # 値域チェック
        for p in params.temperament + params.personality + params.other_cognition:
            if p.value < 1.0 or p.value > 5.0:
                errors.append(f"#{p.id} {p.name} の値 {p.value} が範囲外（1.0-5.0）")
            if not p.natural_language:
                errors.append(f"#{p.id} {p.name} のnatural_language が空です")
        
        if not params.schwartz_values:
            errors.append("schwartz_values が空です")
        if not params.ideal_self:
            errors.append("ideal_self が空です")
        
        return ValidationResult(
            evaluator="SchemaValidator",
            passed=len(errors) == 0,
            error="; ".join(errors),
            details=errors,
        )
    
    @staticmethod
    def validate_episodes(episodes: AutobiographicalEpisodes) -> ValidationResult:
        errors = []
        if len(episodes.episodes) < 5:
            errors.append(f"エピソードが{len(episodes.episodes)}個しかない（最低5個必要）")
        
        for ep in episodes.episodes:
            if not ep.narrative or len(ep.narrative) < 100:
                errors.append(f"{ep.id} のnarrative が短すぎる（{len(ep.narrative or '')}字、最低200字）")
            if not ep.metadata.life_period:
                errors.append(f"{ep.id} のlife_period が空です")
            if not ep.metadata.category:
                errors.append(f"{ep.id} のcategory が空です")
        
        return ValidationResult(
            evaluator="SchemaValidator",
            passed=len(errors) == 0,
            error="; ".join(errors),
            details=errors,
        )
    
    @staticmethod
    def validate_events_store(store: WeeklyEventsStore) -> ValidationResult:
        errors = []
        if len(store.events) < 28:
            errors.append(f"イベント数が{len(store.events)}件（最低28件必要）")
        
        for evt in store.events:
            if not evt.content:
                errors.append(f"{evt.id} のcontent が空です")
            if not evt.meaning_to_character:
                errors.append(f"{evt.id} のmeaning_to_character が空です")
            if evt.day < 1 or evt.day > 7:
                errors.append(f"{evt.id} のday {evt.day} が範囲外")
        
        return ValidationResult(
            evaluator="SchemaValidator",
            passed=len(errors) == 0,
            error="; ".join(errors[:10]),
            details=errors[:10],
        )


# ═══════════════════════════════════════════════════════════════
# 6. DistributionValidator（ルールベース）
# ═══════════════════════════════════════════════════════════════

class DistributionValidator:
    """予想外度分布・メタデータ分布チェック（ルールベース、コストゼロ）"""
    
    @staticmethod
    def validate(store: WeeklyEventsStore) -> ValidationResult:
        errors = []
        
        for day in range(1, 8):
            day_events = [e for e in store.events if e.day == day]
            
            if len(day_events) < 4:
                errors.append(f"Day {day}: イベント数が{len(day_events)}件（最低4件必要）")
            
            # 予想外度分布: high が半分以上
            high_count = sum(1 for e in day_events if e.expectedness == "high")
            if day_events and high_count < len(day_events) / 2:
                errors.append(f"Day {day}: expectedness=high が{high_count}/{len(day_events)}、半分以上必要")
            
            # low は Day 5 以外で各日最大1件
            low_count = sum(1 for e in day_events if e.expectedness == "low")
            if day != 5 and low_count > 1:
                errors.append(f"Day {day}: expectedness=low が{low_count}件（Day5以外は最大1件）")
            
            # Phase D で protagonist_plan は禁止
            plan_count = sum(1 for e in day_events 
                          if e.source == "protagonist_plan" and not hasattr(e, '_dynamically_added'))
            # protagonist_planは日次ループで動的に追加されるもので、Phase D時点では0件のはず
        
        # Day 5 には必ず高強度のイベントが存在すべき
        day5_events = [e for e in store.events if e.day == 5]
        if day5_events:
            has_climax = any(e.narrative_arc_role in ("day5_foreshadowing", "standalone_ripple") 
                          and e.expectedness in ("low", "medium") for e in day5_events)
            low_in_day5 = sum(1 for e in day5_events if e.expectedness == "low")
            if low_in_day5 == 0:
                errors.append("Day 5にexpectedness=lowのイベントがありません（山場として最低1件必要）")
        
        return ValidationResult(
            evaluator="DistributionValidator",
            passed=len(errors) == 0,
            error="; ".join(errors[:5]),
            details=errors,
        )


# ═══════════════════════════════════════════════════════════════
# 2. ConsistencyChecker（LLM）
# ═══════════════════════════════════════════════════════════════

class ConsistencyChecker:
    """Phase内・Phase間の整合性チェック（LLM）"""
    
    @staticmethod
    async def check(concept: ConceptPackage, macro: MacroProfile, 
                    micro: MicroParameters, ws_manager=None) -> ValidationResult:
        if ws_manager:
            await ws_manager.send_agent_thought("[ConsistencyChecker]", "整合性チェック中...", "thinking")
        
        result = await call_llm(
            tier="sonnet",
            system_prompt="""あなたは整合性チェッカーです。
concept_package、macro_profile、micro_parametersの間に矛盾がないかチェックしてください。

チェック項目:
1. concept_packageの方向性とmacro_profileの設定が矛盾しないか
2. psychological_hintsとmicro_parametersの値が整合するか
3. voice_fingerprintとキャラクターの属性が整合するか
4. values_coreとschwartz_valuesが整合するか

出力: JSON
{"passed": true/false, "issues": ["矛盾点1", "矛盾点2"]}""",
            user_message=(
                f"concept_package:\n{concept.character_concept[:300]}\n\n"
                f"macro_profile.basic_info:\n{json.dumps(macro.basic_info.model_dump(), ensure_ascii=False)}\n\n"
                f"values_core:\n{json.dumps(macro.values_core.model_dump(), ensure_ascii=False)}\n\n"
                f"schwartz_values:\n{json.dumps(micro.schwartz_values, ensure_ascii=False)}\n\n"
                f"ideal_self: {micro.ideal_self}\nought_self: {micro.ought_self}"
            ),
            max_tokens=800,
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        issues = data.get("issues", [])
        passed = data.get("passed", True)
        
        if ws_manager:
            status = "complete" if passed else "error"
            await ws_manager.send_agent_thought("[ConsistencyChecker]", 
                f"{'OK ✓' if passed else f'問題検出: {len(issues)}件'}", status)
        
        return ValidationResult(
            evaluator="ConsistencyChecker",
            passed=passed,
            error="; ".join(issues[:3]),
            details=issues,
        )


# ═══════════════════════════════════════════════════════════════
# 3. BiasAuditor（LLM、Phase A-3用）
# ═══════════════════════════════════════════════════════════════

class BiasAuditor:
    """Redemption bias検出（LLM、Phase A-3向け）"""
    
    @staticmethod
    async def audit(episodes: AutobiographicalEpisodes, ws_manager=None) -> ValidationResult:
        if ws_manager:
            await ws_manager.send_agent_thought("[BiasAuditor]", "Redemption bias検出中...", "thinking")
        
        ep_summary = "\n".join([
            f"[{ep.id}] category={ep.metadata.category}: {ep.narrative[:80]}..."
            for ep in episodes.episodes
        ])
        
        result = await call_llm(
            tier="sonnet",
            system_prompt="""あなたはBiasAuditorです。
自伝的エピソード群にRedemption biasがないかチェックしてください。

【Redemption bias (McAdams)】
全てのネガティブ体験が「でもそのおかげで成長できた」に帰着する傾向。
これは非リアリスティックであり、人間は必ずしも全ての困難から学ばない。

【チェック基準】
1. redemption カテゴリのエピソードが過半数を占めていないか
2. contamination（いい思い出が台無しになった体験）が最低1個はあるか
3. ambivalent（混合感情、未解決）が最低1個はあるか
4. unresolved=true のエピソードが1個以上あるか

出力: JSON
{"passed": true/false, "bias_issues": ["問題点1"], "category_distribution": {"redemption": 0, "contamination": 0, "ambivalent": 0, "other": 0}}""",
            user_message=f"エピソード群:\n{ep_summary}",
            max_tokens=600,
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        passed = data.get("passed", True)
        issues = data.get("bias_issues", [])
        
        if ws_manager:
            await ws_manager.send_agent_thought("[BiasAuditor]",
                f"{'OK ✓' if passed else f'Bias検出: {len(issues)}件'}", "complete")
        
        return ValidationResult(
            evaluator="BiasAuditor",
            passed=passed,
            error="; ".join(issues[:3]),
            details=issues,
        )


# ═══════════════════════════════════════════════════════════════
# 5. EventMetadataAuditor（ルール+LLM、Phase D用）
# ═══════════════════════════════════════════════════════════════

class EventMetadataAuditor:
    """イベントメタデータ品質チェック（Phase D用）"""
    
    @staticmethod
    async def audit(store: WeeklyEventsStore, ws_manager=None) -> ValidationResult:
        if ws_manager:
            await ws_manager.send_agent_thought("[EventMetadataAuditor]", "メタデータ品質チェック中...", "thinking")
        
        errors = []
        
        for evt in store.events:
            # meaning_to_characterの品質チェック
            if evt.meaning_to_character and len(evt.meaning_to_character) < 10:
                errors.append(f"{evt.id}: meaning_to_character が短すぎる")
            
            # content の品質チェック
            if evt.content and len(evt.content) < 30:
                errors.append(f"{evt.id}: content が短すぎる（3-5文必要）")
            
            # 曖昧な meaning_to_character を検出
            vague_words = ["面白い", "大変", "普通", "特にない"]
            for vw in vague_words:
                if evt.meaning_to_character and vw in evt.meaning_to_character:
                    errors.append(f"{evt.id}: meaning_to_character に曖昧語「{vw}」を使用")
        
        passed = len(errors) == 0
        
        if ws_manager:
            await ws_manager.send_agent_thought("[EventMetadataAuditor]",
                f"{'OK ✓' if passed else f'問題: {len(errors)}件'}", "complete")
        
        return ValidationResult(
            evaluator="EventMetadataAuditor",
            passed=passed,
            error="; ".join(errors[:5]),
            details=errors[:10],
        )


# ═══════════════════════════════════════════════════════════════
# 4. InterestingnessEvaluator（LLM、High Qualityのみ）
# ═══════════════════════════════════════════════════════════════

class InterestingnessEvaluator:
    """面白さ評価（LLM、High Qualityプロファイルのみ）"""
    
    @staticmethod
    async def evaluate(concept: ConceptPackage, macro: MacroProfile,
                       ws_manager=None) -> ValidationResult:
        if ws_manager:
            await ws_manager.send_agent_thought("[InterestingnessEvaluator]", "面白さ評価中...", "thinking")
        
        result = await call_llm(
            tier="sonnet",
            system_prompt="""あなたは面白さ評価者です。
このキャラクターの7日間の日記を読みたいと思うかどうか、厳しく評価してください。

【評価基準】
1. 最初の一文で引き込まれるか？
2. 内部矛盾は物語を生む力があるか？
3. 「次の日はどうなるんだろう」と思わせるか？
4. 既視感がないか？AI生成にありがちなパターンに陥っていないか？

出力: JSON
{"passed": true/false, "score": 1-10, "feedback": "フィードバック"}""",
            user_message=(
                f"character_concept:\n{concept.character_concept[:500]}\n\n"
                f"story_outline:\n{concept.story_outline[:500]}\n\n"
                f"name: {macro.basic_info.name}, age: {macro.basic_info.age}\n"
                f"occupation: {macro.basic_info.occupation}"
            ),
            max_tokens=500,
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        passed = data.get("passed", True) or data.get("score", 7) >= 6
        
        if ws_manager:
            score = data.get("score", "?")
            await ws_manager.send_agent_thought("[InterestingnessEvaluator]",
                f"スコア: {score}/10 {'✓' if passed else '✗'}", "complete")
        
        return ValidationResult(
            evaluator="InterestingnessEvaluator",
            passed=passed,
            error=data.get("feedback", ""),
            details=[f"Score: {data.get('score', '?')}/10", data.get("feedback", "")],
        )


# ═══════════════════════════════════════════════════════════════
# 7. NarrativeConnectionAuditor（LLM、Standard以上）
# ═══════════════════════════════════════════════════════════════

class NarrativeConnectionAuditor:
    """物語的接続・伏線チェック（LLM、Phase D用）"""
    
    @staticmethod
    async def audit(store: WeeklyEventsStore, episodes: AutobiographicalEpisodes,
                    ws_manager=None) -> ValidationResult:
        if ws_manager:
            await ws_manager.send_agent_thought("[NarrativeConnectionAuditor]", "物語的接続チェック中...", "thinking")
        
        # 伏線チェック
        foreshadowing_events = [e for e in store.events 
                               if e.narrative_arc_role == "day5_foreshadowing"]
        callback_events = [e for e in store.events 
                          if e.narrative_arc_role == "previous_day_callback"]
        
        issues = []
        
        if len(foreshadowing_events) < 2:
            issues.append(f"day5_foreshadowingイベントが{len(foreshadowing_events)}件しかない（最低2件推奨）")
        
        if len(callback_events) < 2:
            issues.append(f"previous_day_callbackイベントが{len(callback_events)}件しかない（最低2件推奨）")
        
        # エピソード接続チェック
        connected = [e for e in store.events if e.connected_episode_id]
        if len(connected) < 2:
            issues.append(f"自伝的エピソードに接続するイベントが{len(connected)}件しかない（最低2件推奨）")
        
        # recurring_motifs の存在チェック
        if not store.narrative_arc.recurring_motifs:
            issues.append("recurring_motifs（繰り返しのモチーフ）が定義されていません")
        
        passed = len(issues) == 0
        
        if ws_manager:
            await ws_manager.send_agent_thought("[NarrativeConnectionAuditor]",
                f"{'OK ✓' if passed else f'接続問題: {len(issues)}件'}", "complete")
        
        return ValidationResult(
            evaluator="NarrativeConnectionAuditor",
            passed=passed,
            error="; ".join(issues[:3]),
            details=issues,
        )


# ═══════════════════════════════════════════════════════════════
# 統合: EvaluatorPipeline
# ═══════════════════════════════════════════════════════════════

class EvaluatorPipeline:
    """プロファイルに基づいてEvaluatorを実行するパイプライン"""
    
    def __init__(self, profile: EvaluationProfile, ws_manager=None):
        self.profile = profile
        self.ws = ws_manager
    
    async def evaluate_phase_a1(self, macro: MacroProfile) -> list[ValidationResult]:
        results = []
        # SchemaValidator（常時ON）
        results.append(SchemaValidator.validate_macro_profile(macro))
        return results
    
    async def evaluate_phase_a2(self, micro: MicroParameters) -> list[ValidationResult]:
        results = []
        results.append(SchemaValidator.validate_micro_parameters(micro))
        return results
    
    async def evaluate_phase_a3(self, episodes: AutobiographicalEpisodes,
                                 concept: ConceptPackage = None,
                                 macro: MacroProfile = None) -> list[ValidationResult]:
        results = []
        results.append(SchemaValidator.validate_episodes(episodes))
        
        # BiasAuditor（Fast以上）
        if self.profile.bias_auditor_enabled:
            results.append(await BiasAuditor.audit(episodes, self.ws))
        
        return results
    
    async def evaluate_phase_d(self, store: WeeklyEventsStore,
                                episodes: AutobiographicalEpisodes = None) -> list[ValidationResult]:
        results = []
        
        # SchemaValidator
        results.append(SchemaValidator.validate_events_store(store))
        
        # DistributionValidator（常時ON）
        results.append(DistributionValidator.validate(store))
        
        # EventMetadataAuditor（Fast以上）
        if self.profile.event_metadata_auditor_enabled:
            results.append(await EventMetadataAuditor.audit(store, self.ws))
        
        # NarrativeConnectionAuditor（Standard以上）
        if self.profile.narrative_connection_auditor_enabled and episodes:
            results.append(await NarrativeConnectionAuditor.audit(store, episodes, self.ws))
        
        return results
    
    async def evaluate_full(self, concept: ConceptPackage, macro: MacroProfile,
                             micro: MicroParameters, episodes: AutobiographicalEpisodes,
                             store: WeeklyEventsStore) -> dict:
        """全Phaseの評価を実行"""
        all_results = []
        
        all_results.extend(await self.evaluate_phase_a1(macro))
        all_results.extend(await self.evaluate_phase_a2(micro))
        all_results.extend(await self.evaluate_phase_a3(episodes, concept, macro))
        all_results.extend(await self.evaluate_phase_d(store, episodes))
        
        # ConsistencyChecker（Standard以上）
        if self.profile.consistency_checker_enabled:
            all_results.append(await ConsistencyChecker.check(concept, macro, micro, self.ws))
        
        # InterestingnessEvaluator（High Quality）
        if self.profile.interestingness_evaluator_enabled:
            all_results.append(await InterestingnessEvaluator.evaluate(concept, macro, self.ws))
        
        passed_count = sum(1 for r in all_results if r.passed)
        total = len(all_results)
        
        return {
            "overall_passed": all(r.passed for r in all_results),
            "passed_count": passed_count,
            "total_count": total,
            "results": [r.model_dump() for r in all_results],
        }
