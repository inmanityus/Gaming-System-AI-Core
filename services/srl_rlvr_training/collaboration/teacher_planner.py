"""
Teacher Planner (Model B)
==========================

Generates expert step-by-step strategies with reasoning for training examples.

Role: Creates expert trajectories that demonstrate the correct approach to solving
      problems specific to each model type (personality, facial, buildings, etc.).
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExpertTrajectory:
    """An expert trajectory with step-by-step reasoning."""
    problem: str
    steps: List[Dict[str, Any]]  # Each step: {"action": str, "reasoning": str, "reward": float}
    expected_outcome: Any
    metadata: Dict[str, Any]
    
    def to_training_example(self) -> Dict[str, Any]:
        """Convert trajectory to training example format."""
        return {
            "problem": self.problem,
            "steps": self.steps,
            "expected_outcome": self.expected_outcome,
            "metadata": self.metadata
        }


class TeacherPlanner:
    """
    Generates expert trajectories for SRL→RLVR training.
    
    This is Model B in the three-model collaboration system.
    """
    
    def __init__(self, cloud_llm_client):
        """
        Initialize Teacher Planner.
        
        Args:
            cloud_llm_client: Client for cloud LLM (GPT-5 Pro, Claude 4.5, etc.)
        """
        self.llm_client = cloud_llm_client
        logger.info("TeacherPlanner initialized")
    
    def generate_trajectory(
        self,
        lore_context: 'LoreContext',  # From LoreRetriever
        model_type: str,
        problem_description: str
    ) -> ExpertTrajectory:
        """
        Generate an expert trajectory for a given problem.
        
        Args:
            lore_context: Context from Lore Retriever
            model_type: Type of model being trained
            problem_description: Description of the problem to solve
        
        Returns:
            ExpertTrajectory: Complete expert trajectory with step-by-step reasoning
        """
        logger.info(f"Generating expert trajectory for {model_type}: {problem_description}")
        
        # TODO: Implement actual trajectory generation using cloud LLM
        # This will:
        # 1. Use lore_context to inform the expert strategy
        # 2. Generate step-by-step reasoning appropriate for model_type
        # 3. Create dense rewards for each step (SRL requirement)
        # 4. Ensure trajectory is specific to the game context
        
        # Placeholder trajectory
        trajectory = ExpertTrajectory(
            problem=problem_description,
            steps=[
                {
                    "action": "analyze_context",
                    "reasoning": "Understanding the problem context",
                    "reward": 0.2
                },
                {
                    "action": "apply_rules",
                    "reasoning": "Applying game-specific rules",
                    "reward": 0.3
                },
                {
                    "action": "generate_solution",
                    "reasoning": "Generating the solution",
                    "reward": 0.5
                }
            ],
            expected_outcome="Correct solution",
            metadata={
                "model_type": model_type,
                "monster_species": lore_context.monster_species if lore_context else None
            }
        )
        
        return trajectory
    
    def generate_batch(
        self,
        lore_contexts: List['LoreContext'],
        model_type: str,
        num_examples: int = 10
    ) -> List[ExpertTrajectory]:
        """
        Generate a batch of expert trajectories.
        
        Args:
            lore_contexts: List of lore contexts
            model_type: Type of model being trained
            num_examples: Number of trajectories to generate
        
        Returns:
            List[ExpertTrajectory]: Batch of expert trajectories
        """
        logger.info(f"Generating batch of {num_examples} trajectories for {model_type}")
        
        trajectories = []
        for i in range(num_examples):
            # TODO: Vary problem descriptions dynamically
            problem = f"Problem {i+1} for {model_type}"
            trajectory = self.generate_trajectory(
                lore_context=lore_contexts[i % len(lore_contexts)] if lore_contexts else None,
                model_type=model_type,
                problem_description=problem
            )
            trajectories.append(trajectory)
        
        return trajectories

