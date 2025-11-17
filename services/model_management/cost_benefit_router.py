"""
Cost-Benefit Router - Dynamic model selection based on cost-benefit analysis.
Routes requests to optimal models considering performance, cost, latency, and hardware.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

# Add parent directory to path for model_management imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Metrics for a model used in cost-benefit analysis."""
    model_id: str
    model_name: str
    performance_score: float  # 0.0 to 1.0
    cost_per_1k_tokens: float  # USD
    latency_ms: float  # Average latency in milliseconds
    hardware_requirements: Dict[str, Any]  # GPU memory, VRAM, etc.
    availability: float  # 0.0 to 1.0 (uptime/reliability)
    use_case: str
    tier: str  # gold, silver, bronze


@dataclass
class RoutingDecision:
    """Result of cost-benefit analysis."""
    selected_model_id: str
    selected_model_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    alternative_models: List[Dict[str, Any]]  # Other viable options
    cost_estimate: float  # Estimated cost for this request
    latency_estimate: float  # Estimated latency in ms


class CostBenefitRouter:
    """
    Routes requests to optimal models based on cost-benefit analysis.
    
    Considers:
    - Performance benchmarks
    - Cost per token
    - Inference latency
    - Hardware requirements
    - Model availability
    - Task-specific requirements
    """
    
    def __init__(self, model_registry: Optional[ModelRegistry] = None):
        """
        Initialize Cost-Benefit Router.
        
        Args:
            model_registry: Model registry instance
        """
        self.model_registry = model_registry or ModelRegistry()
        
        # Responsibility mapping: task type -> preferred model types
        self.responsibility_mapping = {
            "interaction": ["srl_gold_tier", "interaction_layer"],
            "customization": ["srl_silver_tier", "customization_layer"],
            "coordination": ["srl_bronze_tier", "coordination_layer"],
            "foundation": ["foundation_layer"],
            "sentiment_analysis": ["srl_gold_tier", "interaction_layer"],
            "code_generation": ["srl_silver_tier", "customization_layer"],
            "content_moderation": ["srl_bronze_tier", "coordination_layer"],
        }
        
        # Weight factors for cost-benefit calculation
        self.weights = {
            "performance": 0.4,
            "cost": 0.25,
            "latency": 0.2,
            "availability": 0.15
        }
        
        # Latency thresholds (ms) by layer
        self.latency_thresholds = {
            "interaction": 200,  # Gold tier: <200ms
            "customization": 500,  # Silver tier: <500ms
            "coordination": 2000,  # Bronze tier: <2000ms
            "foundation": 100  # Foundation: <100ms
        }
        
        # Cost thresholds (USD per 1k tokens) by layer
        self.cost_thresholds = {
            "interaction": 0.001,  # Gold tier: very low cost
            "customization": 0.005,  # Silver tier: low cost
            "coordination": 0.01,  # Bronze tier: moderate cost
            "foundation": 0.0001  # Foundation: minimal cost
        }
    
    async def select_optimal_model(
        self,
        task_type: str,
        context: Dict[str, Any],
        priority: str = "balanced"  # "performance", "cost", "latency", "balanced"
    ) -> RoutingDecision:
        """
        Select optimal model for a given task using cost-benefit analysis.
        
        Args:
            task_type: Type of task (e.g., "interaction", "customization")
            context: Request context (layer, prompt, etc.)
            priority: Optimization priority
        
        Returns:
            RoutingDecision with selected model and reasoning
        """
        logger.info(f"Selecting optimal model for task: {task_type} (priority: {priority})")
        
        # Get candidate models for this task type
        candidate_models = await self._get_candidate_models(task_type)
        
        if not candidate_models:
            raise ValueError(f"No models available for task type: {task_type}")
        
        # Adjust weights based on priority
        adjusted_weights = self._adjust_weights_for_priority(priority)
        
        # Score each candidate model
        scored_models = []
        for model_metrics in candidate_models:
            score = self._calculate_cost_benefit_score(
                model_metrics,
                task_type,
                adjusted_weights,
                context
            )
            scored_models.append((score, model_metrics))
        
        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[0], reverse=True)
        
        # Select best model
        best_score, best_model = scored_models[0]
        
        # Prepare alternatives (top 3)
        alternatives = [
            {
                "model_id": model.model_id,
                "model_name": model.model_name,
                "score": score,
                "reasoning": self._generate_reasoning(model, task_type, score)
            }
            for score, model in scored_models[:3]
        ]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(best_model, task_type, best_score)
        
        # Estimate cost and latency
        cost_estimate = self._estimate_cost(best_model, context)
        latency_estimate = best_model.latency_ms
        
        return RoutingDecision(
            selected_model_id=best_model.model_id,
            selected_model_name=best_model.model_name,
            confidence=min(best_score, 1.0),
            reasoning=reasoning,
            alternative_models=alternatives[1:],  # Exclude best (already selected)
            cost_estimate=cost_estimate,
            latency_estimate=latency_estimate
        )
    
    async def _get_candidate_models(self, task_type: str) -> List[ModelMetrics]:
        """
        Get candidate models for a given task type.
        
        Args:
            task_type: Type of task
        
        Returns:
            List of ModelMetrics for candidate models
        """
        # Get responsibility mappings
        use_cases = self.responsibility_mapping.get(task_type, [task_type])
        
        candidate_models = []
        
        # Fetch models from registry for each use case
        for use_case in use_cases:
            try:
                model = await self.model_registry.get_current_model(use_case)
                if model:
                    metrics = await self._fetch_model_metrics(model)
                    if metrics:
                        candidate_models.append(metrics)
            except Exception as e:
                logger.warning(f"Error fetching model for use case {use_case}: {e}")
        
        # If no models found, try fallback
        if not candidate_models:
            logger.warning(f"No models found for task type {task_type}, using fallback")
            # Return default/fallback model metrics
            candidate_models.append(self._create_fallback_metrics(task_type))
        
        return candidate_models
    
    async def _fetch_model_metrics(self, model: Dict[str, Any]) -> Optional[ModelMetrics]:
        """
        Fetch metrics for a model from registry.
        
        Args:
            model: Model dictionary from registry
        
        Returns:
            ModelMetrics or None
        """
        try:
            model_id = str(model.get("model_id", ""))
            model_name = model.get("model_name", "unknown")
            use_case = model.get("use_case", "unknown")
            configuration = model.get("configuration", {})
            tier = configuration.get("tier", "unknown")
            
            # Get performance metrics from historical logs
            performance_score = await self._calculate_performance_score(model_id, use_case)
            
            # Get cost from configuration or use defaults
            cost_per_1k_tokens = configuration.get("cost_per_1k_tokens", self._get_default_cost(tier))
            
            # Get latency from configuration or use defaults
            latency_ms = configuration.get("avg_latency_ms", self._get_default_latency(tier))
            
            # Get hardware requirements
            resource_requirements = model.get("resource_requirements", {})
            hardware_requirements = {
                "gpu_memory_gb": resource_requirements.get("gpu_memory_gb", 8),
                "vram_required": resource_requirements.get("vram_required", True)
            }
            
            # Get availability (default to 0.95 if not available)
            availability = configuration.get("availability", 0.95)
            
            return ModelMetrics(
                model_id=model_id,
                model_name=model_name,
                performance_score=performance_score,
                cost_per_1k_tokens=cost_per_1k_tokens,
                latency_ms=latency_ms,
                hardware_requirements=hardware_requirements,
                availability=availability,
                use_case=use_case,
                tier=tier
            )
        except Exception as e:
            logger.error(f"Error fetching model metrics: {e}")
            return None
    
    async def _calculate_performance_score(
        self,
        model_id: str,
        use_case: str
    ) -> float:
        """
        Calculate performance score based on historical data.
        
        Args:
            model_id: Model ID
            use_case: Use case
        
        Returns:
            Performance score (0.0 to 1.0)
        """
        # TODO: Query historical logs to calculate actual performance
        # For now, return default scores based on tier
        tier_scores = {
            "gold": 0.85,
            "silver": 0.90,
            "bronze": 0.95
        }
        
        # Try to determine tier from use case
        if "gold" in use_case.lower():
            return tier_scores["gold"]
        elif "silver" in use_case.lower():
            return tier_scores["silver"]
        elif "bronze" in use_case.lower():
            return tier_scores["bronze"]
        
        return 0.80  # Default score
    
    def _calculate_cost_benefit_score(
        self,
        model_metrics: ModelMetrics,
        task_type: str,
        weights: Dict[str, float],
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate cost-benefit score for a model.
        
        Args:
            model_metrics: Model metrics
            task_type: Task type
            weights: Weight factors
            context: Request context
        
        Returns:
            Cost-benefit score (higher is better)
        """
        # Normalize metrics to 0-1 scale
        
        # Performance score (already 0-1)
        perf_score = model_metrics.performance_score
        
        # Cost score (lower cost = higher score)
        cost_threshold = self.cost_thresholds.get(task_type, 0.01)
        cost_score = max(0.0, 1.0 - (model_metrics.cost_per_1k_tokens / cost_threshold))
        cost_score = min(1.0, cost_score)  # Cap at 1.0
        
        # Latency score (lower latency = higher score)
        latency_threshold = self.latency_thresholds.get(task_type, 1000)
        latency_score = max(0.0, 1.0 - (model_metrics.latency_ms / latency_threshold))
        latency_score = min(1.0, latency_score)  # Cap at 1.0
        
        # Availability score (already 0-1)
        availability_score = model_metrics.availability
        
        # Weighted combination
        total_score = (
            weights["performance"] * perf_score +
            weights["cost"] * cost_score +
            weights["latency"] * latency_score +
            weights["availability"] * availability_score
        )
        
        return total_score
    
    def _adjust_weights_for_priority(self, priority: str) -> Dict[str, float]:
        """
        Adjust weight factors based on priority.
        
        Args:
            priority: Optimization priority
        
        Returns:
            Adjusted weights
        """
        base_weights = self.weights.copy()
        
        if priority == "performance":
            base_weights["performance"] = 0.6
            base_weights["cost"] = 0.15
            base_weights["latency"] = 0.15
            base_weights["availability"] = 0.10
        elif priority == "cost":
            base_weights["performance"] = 0.25
            base_weights["cost"] = 0.50
            base_weights["latency"] = 0.15
            base_weights["availability"] = 0.10
        elif priority == "latency":
            base_weights["performance"] = 0.25
            base_weights["cost"] = 0.15
            base_weights["latency"] = 0.50
            base_weights["availability"] = 0.10
        # "balanced" uses default weights
        
        return base_weights
    
    def _generate_reasoning(
        self,
        model_metrics: ModelMetrics,
        task_type: str,
        score: float
    ) -> str:
        """
        Generate human-readable reasoning for model selection.
        
        Args:
            model_metrics: Selected model metrics
            task_type: Task type
            score: Cost-benefit score
        
        Returns:
            Reasoning string
        """
        reasoning_parts = [
            f"Selected {model_metrics.model_name} (tier: {model_metrics.tier})",
            f"Performance: {model_metrics.performance_score:.2f}",
            f"Cost: ${model_metrics.cost_per_1k_tokens:.4f}/1k tokens",
            f"Latency: {model_metrics.latency_ms:.0f}ms",
            f"Availability: {model_metrics.availability:.2f}",
            f"Score: {score:.3f}"
        ]
        
        return "; ".join(reasoning_parts)
    
    def _estimate_cost(
        self,
        model_metrics: ModelMetrics,
        context: Dict[str, Any]
    ) -> float:
        """
        Estimate cost for a request.
        
        Args:
            model_metrics: Model metrics
            context: Request context
        
        Returns:
            Estimated cost in USD
        """
        # Estimate token count (rough approximation)
        prompt = context.get("prompt", "")
        estimated_tokens = len(prompt.split()) * 1.3  # Rough token estimate
        
        # Calculate cost
        cost = (estimated_tokens / 1000.0) * model_metrics.cost_per_1k_tokens
        
        return cost
    
    def _get_default_cost(self, tier: str) -> float:
        """Get default cost per 1k tokens for a tier."""
        defaults = {
            "gold": 0.0005,  # Very low cost for local models
            "silver": 0.002,  # Low cost
            "bronze": 0.008   # Moderate cost
        }
        return defaults.get(tier, 0.001)
    
    def _get_default_latency(self, tier: str) -> float:
        """Get default latency in ms for a tier."""
        defaults = {
            "gold": 150,    # 150ms for 3B-8B models
            "silver": 400,  # 400ms for 7B-13B models
            "bronze": 1500  # 1500ms for 671B MoE (distributed)
        }
        return defaults.get(tier, 500)
    
    def _create_fallback_metrics(self, task_type: str) -> ModelMetrics:
        """Create fallback model metrics when no models are available."""
        return ModelMetrics(
            model_id="fallback",
            model_name="fallback_model",
            performance_score=0.70,
            cost_per_1k_tokens=0.001,
            latency_ms=500,
            hardware_requirements={"gpu_memory_gb": 8, "vram_required": True},
            availability=0.95,
            use_case=task_type,
            tier="gold"
        )
    
    async def update_metrics(
        self,
        model_id: str,
        performance_data: Dict[str, Any]
    ) -> bool:
        """
        Update model metrics based on performance data.
        
        Args:
            model_id: Model ID
            performance_data: Performance metrics
        
        Returns:
            True if successful
        """
        # TODO: Update model metrics in registry based on performance data
        logger.info(f"Updating metrics for model {model_id}")
        return True










