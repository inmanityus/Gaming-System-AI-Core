"""
KL Divergence Controller
========================

Controls KL divergence between current policy and reference policy
to prevent catastrophic forgetting during SRL training.

Key requirement: KL divergence must stay below max_kl threshold.
"""

import logging
from typing import Dict, Any, Optional
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class KLController:
    """
    Controls KL divergence to prevent catastrophic forgetting.
    """
    
    def __init__(self, max_kl: float = 0.1, kl_weight: float = 0.1):
        """
        Initialize KL Controller.
        
        Args:
            max_kl: Maximum allowed KL divergence
            kl_weight: Weight for KL penalty in loss
        """
        self.max_kl = max_kl
        self.kl_weight = kl_weight
        self.reference_policy: Optional[nn.Module] = None
        logger.info(f"KLController initialized (max_kl={max_kl}, weight={kl_weight})")
    
    def set_reference_policy(self, model: nn.Module):
        """
        Set reference policy (typically initial model state).
        
        Args:
            model: Reference model to compare against
        """
        self.reference_policy = model
        logger.info("Reference policy set")
    
    def compute_kl_divergence(
        self,
        current_policy_logits: torch.Tensor,
        reference_policy_logits: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute KL divergence between current and reference policies.
        
        Args:
            current_policy_logits: Logits from current policy
            reference_policy_logits: Logits from reference policy
        
        Returns:
            KL divergence tensor
        """
        # TODO: Implement actual KL divergence computation
        # This will:
        # 1. Convert logits to probabilities (softmax)
        # 2. Compute KL(P_current || P_reference)
        # 3. Return KL divergence value
        
        logger.debug("Computing KL divergence")
        
        # Placeholder
        kl_div = torch.tensor(0.0)
        
        return kl_div
    
    def compute_kl_penalty(
        self,
        current_policy_logits: torch.Tensor,
        reference_policy_logits: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute KL penalty for loss function.
        
        Args:
            current_policy_logits: Logits from current policy
            reference_policy_logits: Logits from reference policy
        
        Returns:
            KL penalty tensor (scaled by kl_weight)
        """
        kl_div = self.compute_kl_divergence(current_policy_logits, reference_policy_logits)
        penalty = self.kl_weight * kl_div
        
        # Check if KL exceeds threshold
        if kl_div.item() > self.max_kl:
            logger.warning(f"KL divergence ({kl_div.item():.4f}) exceeds max_kl ({self.max_kl})")
        
        return penalty
    
    def should_stop_training(self, current_kl: float) -> bool:
        """
        Check if training should stop due to excessive KL divergence.
        
        Args:
            current_kl: Current KL divergence value
        
        Returns:
            True if training should stop
        """
        if current_kl > self.max_kl * 2:  # Allow some buffer
            logger.error(f"KL divergence ({current_kl:.4f}) exceeds safety threshold")
            return True
        return False

