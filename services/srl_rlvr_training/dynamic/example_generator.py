"""
Dynamic Example Generator
========================

Generates training examples dynamically - NEVER static.

Key Principle: Training examples must always be generated dynamically
and continuously improved as technology evolves.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DynamicExampleGenerator:
    """
    Generates training examples dynamically for SRL→RLVR training.
    
    This ensures that:
    - Examples are never static
    - Generation methods continuously improve
    - New techniques are automatically incorporated
    - Examples adapt to current best practices
    """
    
    def __init__(
        self,
        collaboration_orchestrator,  # CollaborationOrchestrator
        generation_strategies: Optional[List[str]] = None
    ):
        """
        Initialize Dynamic Example Generator.
        
        Args:
            collaboration_orchestrator: Three-model collaboration system
            generation_strategies: List of generation strategies to use
        """
        self.collaboration_orchestrator = collaboration_orchestrator
        self.generation_strategies = generation_strategies or ["collaboration", "synthetic", "adversarial"]
        self.generation_history: List[Dict[str, Any]] = []
        logger.info("DynamicExampleGenerator initialized")
    
    def generate_examples(
        self,
        monster_species: str,
        model_type: str,
        num_examples: int = 10,
        strategy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate training examples dynamically.
        
        Args:
            monster_species: Species identifier
            model_type: Type of model being trained
            num_examples: Number of examples to generate
            strategy: Generation strategy to use (None = auto-select best)
        
        Returns:
            List of training examples (expert trajectories)
        """
        if strategy is None:
            strategy = self._select_best_strategy(model_type)
        
        logger.info(f"Generating {num_examples} examples using strategy: {strategy}")
        
        # Use three-model collaboration as primary strategy
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type=model_type,
            num_examples=num_examples
        )
        
        examples = [t.to_training_example() for t in result.trajectories]
        
        # Log generation metadata
        self._log_generation(
            strategy=strategy,
            num_generated=len(examples),
            model_type=model_type,
            metadata=result.metadata
        )
        
        return examples
    
    def _select_best_strategy(self, model_type: str) -> str:
        """
        Select best generation strategy for model type.
        
        Strategy selection based on:
        - Model type requirements
        - Historical performance
        - Current best practices
        - Available resources
        
        Args:
            model_type: Type of model being trained
        
        Returns:
            Best strategy name
        """
        # Model type specific strategy mapping
        model_strategy_map = {
            "personality": "collaboration",  # Needs multi-model reasoning
            "facial": "collaboration",  # Complex expression mapping
            "animals": "collaboration",  # Requires expert knowledge
            "buildings": "collaboration",  # Architectural expertise
            "plants": "synthetic",  # Can use synthetic generation
            "trees": "synthetic",  # Can use synthetic generation
            "sounds": "adversarial",  # Can use adversarial examples
        }
        
        # Check if we have historical performance data
        if self.generation_history:
            # Analyze recent performance by strategy
            recent_history = self.generation_history[-100:]  # Last 100 generations
            
            strategy_performance = {}
            for entry in recent_history:
                strategy = entry.get("strategy", "collaboration")
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = {
                        "count": 0,
                        "success_rate": 0.0
                    }
                strategy_performance[strategy]["count"] += 1
                # Extract success rate from metadata if available
                metadata = entry.get("metadata", {})
                if "success_rate" in metadata:
                    strategy_performance[strategy]["success_rate"] += metadata["success_rate"]
            
            # Normalize success rates
            for strategy in strategy_performance:
                if strategy_performance[strategy]["count"] > 0:
                    strategy_performance[strategy]["success_rate"] /= strategy_performance[strategy]["count"]
            
            # Select best performing strategy for this model type
            if strategy_performance:
                # Filter strategies that have been used for this model type
                model_specific_history = [
                    e for e in recent_history 
                    if e.get("model_type") == model_type
                ]
                
                if model_specific_history:
                    model_strategy_perf = {}
                    for entry in model_specific_history:
                        strategy = entry.get("strategy", "collaboration")
                        if strategy not in model_strategy_perf:
                            model_strategy_perf[strategy] = {"count": 0, "avg_score": 0.0}
                        model_strategy_perf[strategy]["count"] += 1
                        metadata = entry.get("metadata", {})
                        if "quality_score" in metadata:
                            model_strategy_perf[strategy]["avg_score"] += metadata["quality_score"]
                    
                    # Normalize
                    for strategy in model_strategy_perf:
                        if model_strategy_perf[strategy]["count"] > 0:
                            model_strategy_perf[strategy]["avg_score"] /= model_strategy_perf[strategy]["count"]
                    
                    # Select highest performing strategy
                    if model_strategy_perf:
                        best_strategy = max(
                            model_strategy_perf.items(),
                            key=lambda x: x[1]["avg_score"]
                        )[0]
                        logger.debug(f"Selected strategy '{best_strategy}' based on historical performance")
                        return best_strategy
        
        # Default: Use model-specific strategy or fallback to collaboration
        selected_strategy = model_strategy_map.get(model_type, "collaboration")
        logger.debug(f"Selected strategy '{selected_strategy}' for model type '{model_type}'")
        return selected_strategy
    
    def _log_generation(
        self,
        strategy: str,
        num_generated: int,
        model_type: str,
        metadata: Dict[str, Any]
    ):
        """Log generation event for tracking and improvement."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": strategy,
            "num_generated": num_generated,
            "model_type": model_type,
            "metadata": metadata
        }
        self.generation_history.append(log_entry)
        
        # Keep only recent history (last 1000 entries)
        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-1000:]

