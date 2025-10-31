"""
Paid Model Manager - Manages paid models with auto-switching.
Always checks for better models and switches when found.
"""

import asyncio
from typing import Any, Dict, List, Optional

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.model_management.model_registry import ModelRegistry
from services.model_management.paid_model_scanner import PaidModelScanner
from services.model_management.model_ranker import ModelRanker


class PaidModelManager:
    """
    Manages paid models (Story Teller uses these).
    Automatically checks for better models and switches.
    """
    
    def __init__(self):
        self.registry = ModelRegistry()
        self.scanner = PaidModelScanner()
        self.ranker = ModelRanker()
        self.switch_history: List[Dict[str, Any]] = []
    
    async def check_for_better_models(
        self,
        use_case: str,
        current_model_id: str
    ) -> Optional[str]:
        """
        Check for better paid models available for use case.
        
        Returns:
            Better model ID if found, None otherwise
        """
        # Get current model
        current_model = await self.registry.get_model(current_model_id)
        if not current_model:
            return None
        
        # Scan for available models
        available_models = await self.scanner.scan_available_models(
            use_case=use_case,
            providers=["openrouter", "openai", "anthropic", "google"]
        )
        
        if not available_models:
            return None
        
        # Rank models
        ranked_models = self.ranker.rank_models(
            models=available_models,
            use_case=use_case
        )
        
        # Compare with current
        current_performance = self._get_model_performance(current_model)
        
        for ranked_model in ranked_models:
            model_score = ranked_model.get("rank_score", 0.0)
            
            if model_score > current_performance:
                return ranked_model.get("model_id")
        
        return None
    
    async def auto_switch_model(
        self,
        use_case: str,
        new_model_id: str,
        current_model_id: str
    ) -> bool:
        """
        Automatically switch to better model.
        
        Process:
        1. Validate new model
        2. Shadow deployment
        3. Gradual traffic shift
        4. Monitor and rollback if needed
        """
        # Validate new model
        validation = await self._validate_model(new_model_id, use_case)
        if not validation.get("passed", False):
            return False
        
        # Start shadow deployment (run both models in parallel)
        shadow_results = await self._run_shadow_deployment(
            new_model_id,
            current_model_id,
            duration_minutes=60
        )
        
        if shadow_results.get("success_rate", 0.0) >= 0.95:
            # Gradually shift traffic
            traffic_shifts = [10, 25, 50, 75, 100]
            
            for shift_percent in traffic_shifts:
                await self._shift_traffic(new_model_id, shift_percent)
                
                # Monitor for issues
                await asyncio.sleep(300)  # 5 minutes
                
                issues = await self._detect_issues(new_model_id)
                
                if issues:
                    # Rollback
                    await self._rollback_traffic_shift(current_model_id)
                    return False
            
            # Complete switch
            await self._complete_switch(new_model_id, current_model_id, use_case)
            return True
        
        return False
    
    def _get_model_performance(self, model: Dict[str, Any]) -> float:
        """Get overall performance score for model."""
        metrics = model.get("performance_metrics", {})
        return metrics.get("overall_score", 0.5)
    
    async def _validate_model(
        self,
        model_id: str,
        use_case: str
    ) -> Dict[str, Any]:
        """Validate model works for use case."""
        # TODO: Implement actual validation
        return {"passed": True}  # Placeholder
    
    async def _run_shadow_deployment(
        self,
        new_model_id: str,
        current_model_id: str,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """Run shadow deployment (both models in parallel)."""
        # TODO: Implement shadow deployment
        return {"success_rate": 0.98}  # Placeholder
    
    async def _shift_traffic(
        self,
        model_id: str,
        percent: int
    ):
        """Shift traffic percentage to model."""
        # TODO: Implement traffic shifting
        print(f"[PLACEHOLDER] Shifting {percent}% traffic to {model_id}")
    
    async def _detect_issues(self, model_id: str) -> bool:
        """Detect issues with deployed model."""
        # TODO: Implement issue detection
        return False  # Placeholder
    
    async def _rollback_traffic_shift(self, previous_model_id: str):
        """Rollback traffic to previous model."""
        # TODO: Implement rollback
        print(f"[PLACEHOLDER] Rolling back to {previous_model_id}")
    
    async def _complete_switch(
        self,
        new_model_id: str,
        current_model_id: str,
        use_case: str
    ):
        """Complete model switch."""
        # Update registry
        await self.registry.update_model_status(new_model_id, "current")
        await self.registry.update_model_status(current_model_id, "deprecated")
        
        # Record switch
        self.switch_history.append({
            "from_model": current_model_id,
            "to_model": new_model_id,
            "use_case": use_case,
            "timestamp": asyncio.get_event_loop().time()
        })


