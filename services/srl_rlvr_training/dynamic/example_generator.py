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
        
        Args:
            model_type: Type of model being trained
        
        Returns:
            Best strategy name
        """
        # TODO: Implement strategy selection based on:
        # - Model type requirements
        # - Historical performance
        # - Current best practices
        # - Available resources
        
        return "collaboration"  # Default to three-model collaboration
    
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

