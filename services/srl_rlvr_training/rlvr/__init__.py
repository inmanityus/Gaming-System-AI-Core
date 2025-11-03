"""
RLVR Fine-Tuning Pipeline
=========================

Reinforcement Learning with Verifiable Rewards (RLVR) for outcome-based fine-tuning.

Implements Google's RLVR approach:
- Outcome-based rewards (not step-wise)
- PPO (Proximal Policy Optimization) training
- Optional DPO (Direct Preference Optimization) alternative
- Reward model for verifiable outcomes
"""

from .rlvr_trainer import RLVRTrainer
from .ppo_trainer import PPOTrainer
from .dpo_trainer import DPOTrainer

__all__ = [
    "RLVRTrainer",
    "PPOTrainer",
    "DPOTrainer",
]

