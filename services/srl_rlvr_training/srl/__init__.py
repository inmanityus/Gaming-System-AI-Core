"""
SRL Training Pipeline
=====================

Supervised Reinforcement Learning (SRL) with step-wise supervised rewards.

Implements Google's SRL approach:
- Step-wise dense rewards from expert trajectories
- KL divergence penalty to prevent catastrophic forgetting
- Reward normalization for stable training
"""

from .srl_trainer import SRLTrainer
from .reward_normalizer import RewardNormalizer
from .kl_controller import KLController

__all__ = [
    "SRLTrainer",
    "RewardNormalizer",
    "KLController",
]

