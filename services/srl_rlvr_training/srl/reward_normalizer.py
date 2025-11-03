"""
Reward Normalizer
=================

Normalizes step-wise rewards for stable SRL training.

Reward normalization ensures that:
- Rewards are on a consistent scale
- Training is stable across different trajectory types
- Outliers don't dominate the loss function
"""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class RewardNormalizer:
    """
    Normalizes rewards for stable SRL training.
    """
    
    def __init__(self, method: str = "z_score"):
        """
        Initialize Reward Normalizer.
        
        Args:
            method: Normalization method ("z_score", "min_max", "robust")
        """
        self.method = method
        self.reward_history: List[float] = []
        logger.info(f"RewardNormalizer initialized with method: {method}")
    
    def normalize(self, rewards: List[float]) -> List[float]:
        """
        Normalize a list of rewards.
        
        Args:
            rewards: List of raw reward values
        
        Returns:
            List of normalized reward values
        """
        if not rewards:
            return []
        
        # Update history
        self.reward_history.extend(rewards)
        
        if self.method == "z_score":
            mean = np.mean(self.reward_history)
            std = np.std(self.reward_history)
            if std == 0:
                return rewards
            normalized = [(r - mean) / std for r in rewards]
        
        elif self.method == "min_max":
            min_reward = min(self.reward_history)
            max_reward = max(self.reward_history)
            if max_reward == min_reward:
                return rewards
            normalized = [(r - min_reward) / (max_reward - min_reward) for r in rewards]
        
        elif self.method == "robust":
            median = np.median(self.reward_history)
            mad = np.median([abs(r - median) for r in self.reward_history])
            if mad == 0:
                return rewards
            normalized = [(r - median) / mad for r in rewards]
        
        else:
            logger.warning(f"Unknown normalization method: {self.method}, returning raw rewards")
            normalized = rewards
        
        return normalized
    
    def normalize_trajectory(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize rewards in an expert trajectory.
        
        Args:
            trajectory: Expert trajectory with steps containing rewards
        
        Returns:
            Trajectory with normalized rewards
        """
        if "steps" not in trajectory:
            return trajectory
        
        # Extract rewards
        rewards = [step.get("reward", 0.0) for step in trajectory["steps"]]
        
        # Normalize
        normalized_rewards = self.normalize(rewards)
        
        # Update trajectory
        normalized_trajectory = trajectory.copy()
        for i, step in enumerate(normalized_trajectory["steps"]):
            step["reward"] = normalized_rewards[i]
            step["reward_normalized"] = True
        
        return normalized_trajectory

