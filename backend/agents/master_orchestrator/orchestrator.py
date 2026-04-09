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
    
    def __init__(self, profile: EvaluationProfile, ws_manager=None):
        self.profile = profile
        self.ws = ws_manager
        self.package = CharacterPackage()
    
    async def _notify(self, content: str, status: str = "thinking"):
        if self.ws:
            await self.ws.send_agent_thought("Master Orchestrator", content, status)
    
    async def _progress(self, phase: str, progress: float, detail: str = ""):
        if self.ws:
            await self.ws.send_progress(phase, progress, detail)
    
    async def run(self, theme: Optional[str] = None) -> CharacterPackage:
        """
        キャラクター生成パイプライン全体を実行
        
        Args:
            theme: ユーザー指定のテーマ（省略時は完全自動）
        
        Returns:
            CharacterPackage
        """
        await self._notify("Master Orchestratorを起動します。全Phaseを順次実行します。")
        
        # ─── Tier -1: Creative Director ───────────────────────
        await self._progress("creative_director", 0.0, "Creative Director起動中...")
        
        director = CreativeDirector(profile=self.profile, ws_manager=self.ws)
        concept = await director.run(theme=theme)
        self.package.concept_package = concept
        
        await self._progress("creative_director", 1.0, "Creative Director完了")
        cc_preview = concept.character_concept[:60] if concept.character_concept else "(未定義)"
        await self._notify(f"concept_package確定: {cc_preview}...")
        
        # ─── Phase A-1: マクロプロフィール生成 ────────────────
        await self._progress("phase_a1", 0.0, "Phase A-1: マクロプロフィール生成開始")
        
        try:
            from backend.agents.phase_a1.orchestrator import PhaseA1Orchestrator
            a1_orch = PhaseA1Orchestrator(
                concept=concept,
                profile=self.profile,
                ws_manager=self.ws,
            )
            macro_profile = await a1_orch.run()
            self.package.macro_profile = macro_profile
            
            await self._progress("phase_a1", 1.0, "Phase A-1完了")
            await self._notify(f"macro_profile確定: {macro_profile.basic_info.name}")
        except Exception as e:
            logger.error(f"Phase A-1 failed: {e}", exc_info=True)
            await self._notify(f"Phase A-1エラー: {str(e)}", "error")
            raise
        
        # ─── Phase A-2: ミクロパラメータ生成 ──────────────────
        await self._progress("phase_a2", 0.0, "Phase A-2: ミクロパラメータ生成開始")
        
        try:
            from backend.agents.phase_a2.orchestrator import PhaseA2Orchestrator
            a2_orch = PhaseA2Orchestrator(
                concept=concept,
                macro_profile=macro_profile,
                profile=self.profile,
                ws_manager=self.ws,
            )
            micro_params = await a2_orch.run()
            self.package.micro_parameters = micro_params
            
            await self._progress("phase_a2", 1.0, "Phase A-2完了")
            await self._notify(f"micro_parameters確定: 気質{len(micro_params.temperament)}個 + 性格{len(micro_params.personality)}個")
        except Exception as e:
            logger.error(f"Phase A-2 failed: {e}", exc_info=True)
            await self._notify(f"Phase A-2エラー: {str(e)}", "error")
            raise
        
        # ─── Phase A-3: 自伝的エピソード生成 ──────────────────
        await self._progress("phase_a3", 0.0, "Phase A-3: 自伝的エピソード生成開始")
        
        try:
            from backend.agents.phase_a3.orchestrator import PhaseA3Orchestrator
            a3_orch = PhaseA3Orchestrator(
                concept=concept,
                macro_profile=macro_profile,
                micro_parameters=micro_params,
                profile=self.profile,
                ws_manager=self.ws,
            )
            episodes = await a3_orch.run()
            self.package.autobiographical_episodes = episodes
            
            await self._progress("phase_a3", 1.0, "Phase A-3完了")
            await self._notify(f"autobiographical_episodes確定: {len(episodes.episodes)}個のエピソード")
        except Exception as e:
            logger.error(f"Phase A-3 failed: {e}", exc_info=True)
            await self._notify(f"Phase A-3エラー: {str(e)}", "error")
            raise
        
        # ─── Phase D: イベント列生成 ──────────────────────────
        await self._progress("phase_d", 0.0, "Phase D: 7日分イベント列生成開始")
        
        try:
            from backend.agents.phase_d.orchestrator import PhaseDOrchestrator
            d_orch = PhaseDOrchestrator(
                concept=concept,
                macro_profile=macro_profile,
                micro_parameters=micro_params,
                episodes=episodes,
                profile=self.profile,
                ws_manager=self.ws,
            )
            events_store = await d_orch.run()
            self.package.weekly_events_store = events_store
            
            await self._progress("phase_d", 1.0, "Phase D完了")
            await self._notify(f"weekly_events_store確定: {len(events_store.events)}件のイベント")
        except Exception as e:
            logger.error(f"Phase D failed: {e}", exc_info=True)
            await self._notify(f"Phase Dエラー: {str(e)}", "error")
            raise
        
        # ─── メタデータ更新 ──────────────────────────────────
        cost = token_tracker.summary()
        self.package.metadata = PackageMetadata(
            total_llm_calls=cost["total_calls"],
            total_cost_usd=cost["estimated_cost_usd"],
        )
        
        await self._notify("全Phase完了。脚本パッケージが確定しました。", "complete")
        
        if self.ws:
            await self.ws.send_cost_update(cost)
        
        return self.package
