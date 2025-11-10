"""
Model Ranker - Ranks models by performance, cost, resources.
Used for both paid and self-hosted models.
"""

from typing import Any, Dict, List


class ModelRanker:
    """
    Ranks models by various criteria.
    """
    
    def __init__(self):
        self.default_criteria_weights = {
            "performance_score": 0.3,
            "cost_efficiency": 0.2,
            "latency": 0.2,
            "quality_metrics": 0.3
        }
    
    def rank_models(
        self,
        models: List[Dict[str, Any]],
        criteria_weights: Dict[str, float] = None,
        use_case: str = None
    ) -> List[Dict[str, Any]]:
        """
        Rank models by criteria.
        
        Args:
            models: List of models to rank
            criteria_weights: Weights for ranking criteria
            use_case: Use case identifier (affects criteria)
        
        Returns:
            Ranked list of models (sorted by score, descending)
        """
        if criteria_weights is None:
            criteria_weights = self.default_criteria_weights.copy()
        
        # Adjust weights based on use case
        if use_case:
            criteria_weights = self._adjust_weights_for_use_case(criteria_weights, use_case)
        
        ranked = []
        
        for model in models:
            score = self._calculate_model_score(model, criteria_weights)
            model["rank_score"] = score
            model["ranking_criteria"] = criteria_weights
            ranked.append(model)
        
        # Sort by score (descending)
        ranked.sort(key=lambda x: x.get("rank_score", 0), reverse=True)
        
        return ranked
    
    def _calculate_model_score(
        self,
        model: Dict[str, Any],
        criteria_weights: Dict[str, float]
    ) -> float:
        """Calculate overall score for a model."""
        score = 0.0
        
        # Performance score
        performance = self._get_performance_score(model)
        score += performance * criteria_weights.get("performance_score", 0.3)
        
        # Cost efficiency
        cost_efficiency = self._get_cost_efficiency_score(model)
        score += cost_efficiency * criteria_weights.get("cost_efficiency", 0.2)
        
        # Latency (lower is better, so invert)
        latency = self._get_latency_score(model)
        score += latency * criteria_weights.get("latency", 0.2)
        
        # Quality metrics
        quality = self._get_quality_score(model)
        score += quality * criteria_weights.get("quality_metrics", 0.3)
        
        return score
    
    def _get_performance_score(self, model: Dict[str, Any]) -> float:
        """Get performance score (0-1)."""
        # Use benchmark scores if available
        benchmark_score = model.get("benchmark_score", 0.5)
        performance_metrics = model.get("performance_metrics", {})
        
        # Combine benchmark with actual performance if available
        if performance_metrics:
            accuracy = performance_metrics.get("accuracy", 0.5)
            return (benchmark_score + accuracy) / 2
        
        return benchmark_score
    
    def _get_cost_efficiency_score(self, model: Dict[str, Any]) -> float:
        """Get cost efficiency score (0-1, higher is better)."""
        pricing = model.get("pricing", {})
        
        if not pricing:
            # Self-hosted models have no cost
            if model.get("model_type") == "self_hosted":
                return 1.0
            return 0.5  # Unknown pricing
        
        # Calculate cost per token or per request
        prompt_price = pricing.get("prompt", 0.0)
        completion_price = pricing.get("completion", 0.0)
        
        if prompt_price == 0 and completion_price == 0:
            return 1.0  # Free
        
        # Lower price = higher score
        # Normalize: assume $0.001/1K tokens is good baseline
        total_price = (prompt_price + completion_price) / 1000
        efficiency = max(0, 1.0 - (total_price / 0.001))
        
        return min(efficiency, 1.0)
    
    def _get_latency_score(self, model: Dict[str, Any]) -> float:
        """Get latency score (0-1, lower latency = higher score)."""
        latency_ms = model.get("latency_ms", 500)  # Default 500ms
        
        # Score: <100ms = 1.0, <200ms = 0.8, <500ms = 0.6, <1000ms = 0.4, >1000ms = 0.2
        if latency_ms < 100:
            return 1.0
        elif latency_ms < 200:
            return 0.8
        elif latency_ms < 500:
            return 0.6
        elif latency_ms < 1000:
            return 0.4
        else:
            return 0.2
    
    def _get_quality_score(self, model: Dict[str, Any]) -> float:
        """Get quality score (0-1)."""
        quality_metrics = model.get("quality_metrics", {})
        
        if not quality_metrics:
            return 0.5  # Default
        
        # Combine multiple quality metrics
        coherence = quality_metrics.get("coherence", 0.5)
        relevance = quality_metrics.get("relevance", 0.5)
        creativity = quality_metrics.get("creativity", 0.5)
        
        return (coherence + relevance + creativity) / 3
    
    def _adjust_weights_for_use_case(
        self,
        weights: Dict[str, float],
        use_case: str
    ) -> Dict[str, float]:
        """Adjust weights based on use case priorities."""
        adjusted = weights.copy()
        
        if use_case == "story_generation":
            # Prioritize quality and performance
            adjusted["quality_metrics"] = 0.4
            adjusted["performance_score"] = 0.3
            adjusted["cost_efficiency"] = 0.15
            adjusted["latency"] = 0.15
        
        elif use_case == "npc_dialogue":
            # Prioritize latency and quality
            adjusted["latency"] = 0.3
            adjusted["quality_metrics"] = 0.3
            adjusted["performance_score"] = 0.25
            adjusted["cost_efficiency"] = 0.15
        
        elif use_case == "faction_decision":
            # Prioritize performance and quality
            adjusted["performance_score"] = 0.35
            adjusted["quality_metrics"] = 0.3
            adjusted["latency"] = 0.2
            adjusted["cost_efficiency"] = 0.15
        
        # Normalize weights to sum to 1.0
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted








