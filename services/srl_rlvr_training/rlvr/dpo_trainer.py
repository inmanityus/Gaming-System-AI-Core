"""
DPO Trainer
===========

Direct Preference Optimization for RLVR fine-tuning.

DPO is an alternative to PPO that directly optimizes preferences
without requiring a separate reward model.
"""

import logging
from typing import Dict, Any
import torch

logger = logging.getLogger(__name__)


class DPOTrainer:
    """
    Direct Preference Optimization trainer for RLVR.
    """
    
    def __init__(self, beta: float = 0.1):
        """
        Initialize DPO Trainer.
        
        Args:
            beta: DPO temperature parameter
        """
        self.beta = beta
        logger.info("DPOTrainer initialized")
    
    def compute_dpo_loss(
        self,
        policy_log_probs: torch.Tensor,
        reference_log_probs: torch.Tensor,
        preferences: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Compute DPO loss using Direct Preference Optimization.
        
        DPO loss formula:
        L = -log(σ(β * (log π_θ(y_w|x) - log π_ref(y_w|x)) - β * (log π_θ(y_l|x) - log π_ref(y_l|x))))
        
        For preference-based (not paired) format:
        L = -log(σ(β * (log π_θ - log π_ref) * preferences))
        
        Args:
            policy_log_probs: Log probabilities from current policy [batch_size]
            reference_log_probs: Log probabilities from reference policy [batch_size]
            preferences: Preference scores (higher = better) [batch_size]
        
        Returns:
            Dict with DPO loss and total loss
        """
        logger.debug("Computing DPO loss")
        
        # Ensure tensors are on same device
        device = policy_log_probs.device
        reference_log_probs = reference_log_probs.to(device)
        preferences = preferences.to(device)
        
        # Compute log ratios: log(π_θ / π_ref) = log π_θ - log π_ref
        log_ratios = policy_log_probs - reference_log_probs
        
        # Apply beta temperature scaling
        scaled_log_ratios = self.beta * log_ratios
        
        # Weight by preferences (higher preference = stronger signal)
        # For positive preferences, we want to maximize the log ratio
        # For negative preferences, we want to minimize the log ratio
        preference_weighted = scaled_log_ratios * preferences
        
        # Apply sigmoid and compute negative log likelihood
        # DPO loss: -log(σ(β * log_ratio * preference))
        sigmoid_probs = torch.sigmoid(preference_weighted)
        
        # Avoid log(0) by clamping
        sigmoid_probs = torch.clamp(sigmoid_probs, min=1e-8, max=1.0 - 1e-8)
        dpo_loss = -torch.log(sigmoid_probs)
        
        # Average over batch
        dpo_loss = dpo_loss.mean()
        
        # Total loss is DPO loss (can add regularization terms here if needed)
        total_loss = dpo_loss
        
        return {
            "dpo_loss": dpo_loss,
            "total_loss": total_loss,
            "log_ratios_mean": log_ratios.mean().item(),
            "preference_mean": preferences.mean().item()
        }

