"""
Tier 0: Master Orchestrator
Phase A-1 → A-2 → A-3 → D を順次実行し、
各Phaseの出力をEvaluatorでチェックした上で次のPhaseに引き継ぐ。
"""

import json
import logging
from typing import Optional

from backend.config import EvaluationProfile
from backend.models.character import CharacterPackage, ConceptPackage, PackageMetadata
from backend.agents.creative_director.director import CreativeDirector
from backend.tools.llm_api import token_tracker

logger = logging.getLogger(__name__)


class MasterOrchestrator:
    """Tier 0: Master Orchestrator"""
    
    def __init__(self, profile: EvaluationProfile, ws_manager=None, existing_package: Optional[CharacterPackage] = None, session_id: Optional[str] = None):
        self.profile = profile
        self.ws = ws_manager
        self.package = existing_package or CharacterPackage()
        from datetime import datetime
        self.session_id = session_id or f"SID_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("Master Orchestrator", content, status)
    
    async def _progress(self, phase: str, progress: float, detail: str = ""):
        if self.ws:
            await self.ws.send_progress(phase, progress, detail)

    async def _checkpoint(self):
        try:
            from backend.storage.md_storage import save_checkpoint, save_character_profile, save_logs
            # 名前が未定義の場合はSession IDを使用
            cname = self.session_id
            if self.package.macro_profile and self.package.macro_profile.basic_info:
                if self.package.macro_profile.basic_info.name:
                    cname = self.package.macro_profile.basic_info.name
            
            await save_checkpoint(cname, self.package)
            await save_character_profile(cname, self.package)
            
            # 思考ログの保存
            if self.ws and hasattr(self.ws, "thought_history"):
                await save_logs(cname, self.ws.thought_history)
        except Exception as e:
            logger.warning(f"Checkpoint save failed: {e}")
    
    async def run(self, theme: Optional[str] = None) -> CharacterPackage:
        """
        キャラクター生成パイプライン全体を実行
        
        Args:
            theme: ユーザー指定のテーマ（省略時は完全自動）
        
        Returns:
            CharacterPackage
        """
        await self._notify("Master Orchestratorを起動します。全Phaseを順次実行します。")
        await self._checkpoint()  # セッション開始時にディレクトリと基本パッケージを保存
        
        from backend.agents.evaluators.pipeline import EvaluatorPipeline
        evaluator = EvaluatorPipeline(profile=self.profile, ws_manager=self.ws)
        
        # 評価結果の集計用
        all_eval_results = []
        
        async def _execute_phase_with_retry(phase_name: str, orch_class, orch_kwargs: dict, eval_func):
            max_iter = self.profile.worker_regeneration_max_iterations
            if max_iter < 1:
                max_iter = 1
                
            best_result = None
            best_evals = []
            best_passed_count = -1
            
            for iteration in range(1, max_iter + 1):
                try:
                    if iteration > 1:
                        await self._notify(f"{phase_name}: 再生成ループ {iteration}/{max_iter} を開始", "warning")
                    
                    # Phase実行
                    orch = orch_class(**orch_kwargs)
                    result = await orch.run()
                    
                    # Evaluator実行
                    evals = await eval_func(result)
                    
                    passed_count = sum(1 for e in evals if e.passed)
                    is_passed = all(e.passed for e in evals)
                    
                    # 暫定ベスト更新
                    if passed_count > best_passed_count:
                        best_passed_count = passed_count
                        best_result = result
                        best_evals = evals
                    
                    if is_passed:
                        all_eval_results.extend(best_evals)
                        return best_result
                    else:
                        errors = [e.error for e in evals if not e.passed]
                        await self._notify(f"{phase_name} 評価Fail: {errors[0]}", "warning")
                except Exception as e:
                    logger.error(f"Error in {phase_name} (iter {iteration}): {e}", exc_info=True)
                    await self._notify(f"{phase_name} コード実行エラー: {str(e)}", "error")
                    if iteration == max_iter:
                        raise
                    
            await self._notify(f"{phase_name}: 評価上限到達。暫定ベスト結果を採用します", "warning")
            all_eval_results.extend(best_evals)
            return best_result
        
            return best_result
        
        # ─── Tier -1: Creative Director ───────────────────────
        await self._checkpoint() # 直前に保存
        if not self.package.concept_package:
            await self._progress("creative_director", 0.0, "Creative Director起動中...")
            director = CreativeDirector(profile=self.profile, ws_manager=self.ws)
            concept = await director.run(theme=theme)
            self.package.concept_package = concept
            await self._checkpoint()
            await self._progress("creative_director", 1.0, "Creative Director完了")
        else:
            await self._notify("Creative Director: 既存のコンセプトを読み込み完了 (Skip)")
            concept = self.package.concept_package
            await self._progress("creative_director", 1.0)
            
        cc_preview = concept.character_concept[:60] if concept.character_concept else "(未定義)"
        await self._notify(f"concept_package確定: {cc_preview}...")
        
        # ─── Phase A-1: マクロプロフィール + 言語的表現方法 生成 ────────────────
        if not self.package.macro_profile:
            await self._progress("phase_a1", 0.0, "Phase A-1: マクロプロフィール + 言語的表現方法 生成開始")
            try:
                from backend.agents.phase_a1.orchestrator import PhaseA1Orchestrator
                phase_a1_result = await _execute_phase_with_retry(
                    "Phase A-1",
                    PhaseA1Orchestrator,
                    {"concept": concept, "profile": self.profile, "ws_manager": self.ws},
                    lambda res: evaluator.evaluate_phase_a1(res)
                )
                self.package.macro_profile = phase_a1_result.macro_profile
                self.package.linguistic_expression = phase_a1_result.linguistic_expression
                macro_profile = phase_a1_result.macro_profile
                await self._checkpoint()
                await self._progress("phase_a1", 1.0, "Phase A-1完了")
                await self._notify(f"macro_profile + linguistic_expression 確定: {macro_profile.basic_info.name}")
            except Exception as e:
                logger.error(f"Phase A-1 failed: {e}", exc_info=True)
                await self._notify(f"Phase A-1エラー: {str(e)}", "error")
                raise
        else:
            await self._notify("Phase A-1: 既存のマクロプロフィールを読み込み完了 (Skip)")
            macro_profile = self.package.macro_profile
            await self._progress("phase_a1", 1.0)
        
        # ─── Phase A-2: ミクロパラメータ生成 ──────────────────
        if not self.package.micro_parameters:
            await self._progress("phase_a2", 0.0, "Phase A-2: ミクロパラメータ生成開始")
            try:
                from backend.agents.phase_a2.orchestrator import PhaseA2Orchestrator
                micro_params = await _execute_phase_with_retry(
                    "Phase A-2",
                    PhaseA2Orchestrator,
                    {"concept": concept, "macro_profile": macro_profile, "profile": self.profile, "ws_manager": self.ws},
                    lambda res: evaluator.evaluate_phase_a2(res)
                )
                self.package.micro_parameters = micro_params
                await self._checkpoint()
                await self._progress("phase_a2", 1.0, "Phase A-2完了")
                await self._notify(f"micro_parameters確定: 気質{len(micro_params.temperament)}個 + 性格{len(micro_params.personality)}個")
            except Exception as e:
                logger.error(f"Phase A-2 failed: {e}", exc_info=True)
                await self._notify(f"Phase A-2エラー: {str(e)}", "error")
                raise
        else:
            await self._notify("Phase A-2: 既存のミクロパラメータを読み込み完了 (Skip)")
            micro_params = self.package.micro_parameters
            await self._progress("phase_a2", 1.0)
        
        # ─── Phase A-3: 自伝的エピソード生成 ──────────────────
        if not self.package.autobiographical_episodes:
            await self._progress("phase_a3", 0.0, "Phase A-3: 自伝的エピソード生成開始")
            try:
                from backend.agents.phase_a3.orchestrator import PhaseA3Orchestrator
                episodes = await _execute_phase_with_retry(
                    "Phase A-3",
                    PhaseA3Orchestrator,
                    {"concept": concept, "macro_profile": macro_profile, "micro_parameters": micro_params, "profile": self.profile, "ws_manager": self.ws},
                    lambda res: evaluator.evaluate_phase_a3(res, concept, macro_profile)
                )
                self.package.autobiographical_episodes = episodes
                await self._checkpoint()
                await self._progress("phase_a3", 1.0, "Phase A-3完了")
                await self._notify(f"autobiographical_episodes確定: {len(episodes.episodes)}個のエピソード")
            except Exception as e:
                logger.error(f"Phase A-3 failed: {e}", exc_info=True)
                await self._notify(f"Phase A-3エラー: {str(e)}", "error")
                raise
        else:
            await self._notify("Phase A-3: 既存の自伝的エピソードを読み込み完了 (Skip)")
            episodes = self.package.autobiographical_episodes
            await self._progress("phase_a3", 1.0)
        
        # ─── Phase D: イベント列生成 ──────────────────────────
        if not self.package.weekly_events_store:
            await self._progress("phase_d", 0.0, "Phase D: 7日分イベント列生成開始")
            try:
                from backend.agents.phase_d.orchestrator import PhaseDOrchestrator
                events_store = await _execute_phase_with_retry(
                    "Phase D",
                    PhaseDOrchestrator,
                    {"concept": concept, "macro_profile": macro_profile, "micro_parameters": micro_params, "episodes": episodes, "profile": self.profile, "ws_manager": self.ws},
                    lambda res: evaluator.evaluate_phase_d(res, episodes)
                )
                self.package.weekly_events_store = events_store
                await self._checkpoint()
                await self._progress("phase_d", 1.0, "Phase D完了")
                await self._notify(f"weekly_events_store確定: {len(events_store.events)}件のイベント")
            except Exception as e:
                logger.error(f"Phase D failed: {e}", exc_info=True)
                await self._notify(f"Phase Dエラー: {str(e)}", "error")
                raise
        else:
            await self._notify("Phase D: 既存のイベント列を読み込み完了 (Skip)")
            events_store = self.package.weekly_events_store
            await self._progress("phase_d", 1.0)
        
        # ─── Tier 3: 最終クロス構成チェック (Consistency / Interestingness) ──
        await self._notify("最終フェーズ横断Evaluatorを実行中...")
        
        try:
            # 各Phaseの評価は既に all_eval_results に入っている
            from backend.agents.evaluators.pipeline import ConsistencyChecker, InterestingnessEvaluator
            
            if self.profile.consistency_checker_enabled:
                all_eval_results.append(await ConsistencyChecker.check(concept, macro_profile, micro_params, self.ws))
            
            if self.profile.interestingness_evaluator_enabled:
                all_eval_results.append(await InterestingnessEvaluator.evaluate(concept, macro_profile, self.ws))
            
            passed = sum(1 for e in all_eval_results if e.passed)
            total = len(all_eval_results)
            
            self.package.audit_report = {
                "overall_passed": all(e.passed for e in all_eval_results),
                "passed_count": passed,
                "total_count": total,
                "results": [r.model_dump() for r in all_eval_results],
            }
            
            await self._notify(f"全評価完了: {passed}/{total} passed", "complete")
        except Exception as e:
            logger.warning(f"最終Evaluator error: {e}")
            await self._notify(f"Evaluator警告: {str(e)}", "error")
        
        # ─── メタデータ更新 ──────────────────────────────────
        cost = token_tracker.summary()
        self.package.metadata = PackageMetadata(
            total_llm_calls=cost["total_calls"],
            total_cost_usd=cost["estimated_cost_usd"],
        )
        
        await self._notify("全Phase完了。脚本パッケージが確定しました。", "complete")
        
        if self.ws:
            await self.ws.send_cost_update(cost)
            
        try:
            from backend.storage.md_storage import save_character_profile
            cname = self.package.macro_profile.basic_info.name if (self.package.macro_profile and self.package.macro_profile.basic_info) else "Unknown_Character"
            await save_character_profile(cname, self.package)
        except Exception as e:
            logger.error(f"MD保存失敗: {e}")
        
        return self.package
