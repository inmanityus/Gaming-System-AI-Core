"""
Dynamic Model Selector
======================

Responsibility-based model selection with cost-benefit analysis.

Key Principle: Model selection is NOT arbitrary - it's based on:
1. Task responsibilities
2. Model capabilities
3. Cost-benefit analysis
4. Performance benchmarks
"""

import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

logger = logging.getLogger(__name__)


@dataclass
class ModelCandidate:
    """A candidate model for selection."""
    model_id: str
    model_type: str
    capability_score: float  # 0.0 to 1.0
    cost_per_token: float
    latency_ms: float
    responsibility_match: float  # How well it matches task requirements
    benchmark_scores: Dict[str, float]
    
    @property
    def cost_benefit_score(self) -> float:
        """Compute cost-benefit score."""
        benefit = (self.capability_score + self.responsibility_match) / 2
        cost_penalty = min(self.cost_per_token * 1000, 1.0)  # Normalize cost
        return benefit - cost_penalty


class DynamicModelSelector:
    """
    Selects models dynamically based on responsibilities and cost-benefit analysis.
    
    This ensures:
    - Models are selected based on task requirements (not arbitrary)
    - Cost-benefit analysis is performed
    - New models are evaluated when released
    - Performance is tracked over time
    """
    
    def __init__(self, benchmark_db_url: str, model_registry_url: Optional[str] = None):
        """
        Initialize Dynamic Model Selector.
        
        Args:
            benchmark_db_url: URL to benchmark database
            model_registry_url: URL to model registry API (optional, uses benchmark_db_url if not provided)
        """
        self.benchmark_db_url = benchmark_db_url.rstrip('/')
        self.model_registry_url = model_registry_url or self.benchmark_db_url
        self.model_registry: Dict[str, ModelCandidate] = {}
        self.selection_history: List[Dict[str, Any]] = []
        
        # Initialize HTTP client if available
        if HTTPX_AVAILABLE:
            self.http_client = httpx.Client(timeout=30.0)
        else:
            self.http_client = None
            logger.warning("httpx not available, model selection will use cached registry only")
        
        logger.info(f"DynamicModelSelector initialized (benchmark_db: {self.benchmark_db_url})")
    
    def select_model(
        self,
        task_responsibilities: Dict[str, Any],
        model_type: str,
        budget_constraints: Optional[Dict[str, float]] = None
    ) -> Optional[str]:
        """
        Select best model for given task responsibilities.
        
        Args:
            task_responsibilities: Requirements for the task
            model_type: Type of model needed (e.g., "personality", "facial")
            budget_constraints: Budget constraints (optional)
        
        Returns:
            Selected model ID (None if no suitable model)
        """
        logger.info(f"Selecting model for {model_type} with responsibilities: {task_responsibilities}")
        
        # Get candidates
        candidates = self._get_candidates(model_type, task_responsibilities)
        
        if not candidates:
            logger.warning(f"No candidates found for {model_type}")
            return None
        
        # Apply budget constraints
        if budget_constraints:
            candidates = self._filter_by_budget(candidates, budget_constraints)
        
        # Score candidates
        scored_candidates = [
            (candidate, candidate.cost_benefit_score)
            for candidate in candidates
        ]
        
        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select best
        best_candidate, best_score = scored_candidates[0]
        
        logger.info(f"Selected model: {best_candidate.model_id} (score: {best_score:.4f})")
        
        # Log selection
        self._log_selection(
            selected_model=best_candidate.model_id,
            score=best_score,
            task_responsibilities=task_responsibilities,
            model_type=model_type
        )
        
        return best_candidate.model_id
    
    def _get_candidates(
        self,
        model_type: str,
        task_responsibilities: Dict[str, Any]
    ) -> List[ModelCandidate]:
        """
        Get candidate models matching requirements.
        
        Retrieves candidates by:
        1. Querying model registry
        2. Filtering by model_type
        3. Matching against task_responsibilities
        4. Computing responsibility_match scores
        """
        candidates = []
        
        try:
            # Query model registry for candidates
            if self.http_client:
                # Try API endpoint first
                try:
                    response = self.http_client.get(
                        f"{self.model_registry_url}/api/models",
                        params={
                            "model_type": model_type,
                            "available": True
                        }
                    )
                    response.raise_for_status()
                    models_data = response.json()
                    
                    # Query benchmarks for each model
                    for model_data in models_data.get("models", []):
                        model_id = model_data.get("model_id")
                        benchmark_scores = self._get_benchmark_scores(model_id)
                        
                        # Calculate responsibility match
                        responsibility_match = self._calculate_responsibility_match(
                            model_data, task_responsibilities
                        )
                        
                        candidate = ModelCandidate(
                            model_id=model_id,
                            model_type=model_data.get("model_type", model_type),
                            capability_score=model_data.get("capability_score", 0.5),
                            cost_per_token=model_data.get("cost_per_token", 0.001),
                            latency_ms=model_data.get("latency_ms", 100.0),
                            responsibility_match=responsibility_match,
                            benchmark_scores=benchmark_scores
                        )
                        candidates.append(candidate)
                        
                except Exception as e:
                    logger.warning(f"Error querying model registry API: {e}, using cached registry")
            
            # Fallback: Use cached registry
            if not candidates and self.model_registry:
                for model_id, candidate in self.model_registry.items():
                    if candidate.model_type == model_type:
                        # Recalculate responsibility match
                        candidate.responsibility_match = self._calculate_responsibility_match(
                            {"model_id": model_id, "model_type": model_type},
                            task_responsibilities
                        )
                        candidates.append(candidate)
            
            # If still no candidates, try to load default models from environment
            if not candidates:
                default_models = self._load_default_models(model_type)
                for model_data in default_models:
                    responsibility_match = self._calculate_responsibility_match(
                        model_data, task_responsibilities
                    )
                    candidate = ModelCandidate(
                        model_id=model_data.get("model_id", f"default_{model_type}"),
                        model_type=model_type,
                        capability_score=model_data.get("capability_score", 0.5),
                        cost_per_token=model_data.get("cost_per_token", 0.001),
                        latency_ms=model_data.get("latency_ms", 100.0),
                        responsibility_match=responsibility_match,
                        benchmark_scores=model_data.get("benchmark_scores", {})
                    )
                    candidates.append(candidate)
            
            logger.info(f"Found {len(candidates)} candidates for {model_type}")
            
        except Exception as e:
            logger.error(f"Error getting candidates: {e}")
        
        return candidates
    
    def _get_benchmark_scores(self, model_id: str) -> Dict[str, float]:
        """Get benchmark scores for a model."""
        try:
            if self.http_client:
                response = self.http_client.get(
                    f"{self.benchmark_db_url}/api/benchmarks/{model_id}"
                )
                response.raise_for_status()
                data = response.json()
                return data.get("scores", {})
        except Exception as e:
            logger.debug(f"Error getting benchmark scores for {model_id}: {e}")
        
        return {}
    
    def _calculate_responsibility_match(
        self,
        model_data: Dict[str, Any],
        task_responsibilities: Dict[str, Any]
    ) -> float:
        """
        Calculate how well model matches task responsibilities.
        
        Returns score from 0.0 to 1.0.
        """
        # Extract model capabilities
        model_capabilities = model_data.get("capabilities", {})
        required_capabilities = task_responsibilities.get("required_capabilities", {})
        
        if not required_capabilities:
            # No specific requirements, use default match
            return 0.7
        
        # Calculate match score
        matches = 0
        total_requirements = len(required_capabilities)
        
        for capability, required_level in required_capabilities.items():
            model_level = model_capabilities.get(capability, 0.0)
            if model_level >= required_level * 0.8:  # 80% threshold
                matches += 1
        
        match_score = matches / total_requirements if total_requirements > 0 else 0.5
        
        # Factor in model_type match
        model_type_match = 1.0 if model_data.get("model_type") == task_responsibilities.get("model_type") else 0.5
        
        # Combine scores
        final_score = (match_score * 0.7) + (model_type_match * 0.3)
        
        return min(1.0, max(0.0, final_score))
    
    def _load_default_models(self, model_type: str) -> List[Dict[str, Any]]:
        """Load default models from environment or configuration."""
        # Try environment variable first
        env_key = f"DEFAULT_MODELS_{model_type.upper()}"
        default_models_json = os.getenv(env_key)
        
        if default_models_json:
            try:
                import json
                return json.loads(default_models_json)
            except Exception as e:
                logger.warning(f"Error parsing default models from env: {e}")
        
        # Return minimal default
        return [{
            "model_id": f"default_{model_type}",
            "model_type": model_type,
            "capability_score": 0.5,
            "cost_per_token": 0.001,
            "latency_ms": 100.0,
            "benchmark_scores": {}
        }]
    
    def _filter_by_budget(
        self,
        candidates: List[ModelCandidate],
        budget_constraints: Dict[str, float]
    ) -> List[ModelCandidate]:
        """Filter candidates by budget constraints."""
        filtered = []
        for candidate in candidates:
            if "max_cost_per_token" in budget_constraints:
                if candidate.cost_per_token > budget_constraints["max_cost_per_token"]:
                    continue
            if "max_latency_ms" in budget_constraints:
                if candidate.latency_ms > budget_constraints["max_latency_ms"]:
                    continue
            filtered.append(candidate)
        
        return filtered
    
    def _log_selection(
        self,
        selected_model: str,
        score: float,
        task_responsibilities: Dict[str, Any],
        model_type: str
    ):
        """Log selection for tracking and analysis."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "selected_model": selected_model,
            "score": score,
            "task_responsibilities": task_responsibilities,
            "model_type": model_type
        }
        self.selection_history.append(log_entry)

