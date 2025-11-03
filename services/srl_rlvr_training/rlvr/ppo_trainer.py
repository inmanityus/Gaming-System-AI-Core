"""
PPO Trainer
===========

Proximal Policy Optimization for RLVR fine-tuning.
"""

import logging
from typing import Dict, Any
import torch

logger = logging.getLogger(__name__)


class PPOTrainer:
    """
    Proximal Policy Optimization trainer for RLVR.
    """
    
    def __init__(
        self,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01
    ):
        """
        Initialize PPO Trainer.
        
        Args:
            clip_epsilon: PPO clip parameter
            value_coef: Value loss coefficient
            entropy_coef: Entropy bonus coefficient
        """
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        logger.info("PPOTrainer initialized")
    
    def compute_ppo_loss(
        self,
        old_log_probs: torch.Tensor,
        new_log_probs: torch.Tensor,
        advantages: torch.Tensor,
        returns: torch.Tensor,
        values: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Compute PPO loss.
        
        PPO objective: L^CLIP(θ) = E[min(r(θ) * A, clip(r(θ), 1-ε, 1+ε) * A)]
        where r(θ) = π_θ(a|s) / π_θ_old(a|s) = exp(new_log_probs - old_log_probs)
        
        Args:
            old_log_probs: Log probabilities from old policy [batch, seq_len]
            new_log_probs: Log probabilities from new policy [batch, seq_len]
            advantages: Advantage estimates [batch, seq_len]
            returns: Target returns [batch, seq_len]
            values: Value estimates [batch, seq_len]
        
        Returns:
            Dict with policy loss, value loss, entropy, and total loss
        """
        logger.debug("Computing PPO loss")
        
        # Compute importance sampling ratio
        ratio = torch.exp(new_log_probs - old_log_probs)
        
        # Clipped objective
        clipped_ratio = torch.clamp(ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon)
        
        # PPO clipped objective: min(r * A, clip(r) * A)
        policy_objective_1 = ratio * advantages
        policy_objective_2 = clipped_ratio * advantages
        policy_loss = -torch.min(policy_objective_1, policy_objective_2).mean()
        
        # Value loss (MSE between predicted and actual returns)
        value_loss = torch.nn.functional.mse_loss(values, returns)
        
        # Entropy bonus (encourages exploration)
        # Compute entropy from log_probs: H = -sum(p * log(p))
        # Approximate using log_probs: entropy ≈ -mean(exp(log_prob) * log_prob)
        probs = torch.exp(new_log_probs)
        entropy = -(probs * new_log_probs).sum(dim=-1).mean()
        
        # Total loss: policy loss + value loss - entropy bonus
        total_loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy
        
        return {
            "policy_loss": policy_loss,
            "value_loss": value_loss,
            "entropy": entropy,
            "total_loss": total_loss,
            "ratio": ratio.mean()
        }

