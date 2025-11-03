"""
SRL Trainer
===========

Implements Supervised Reinforcement Learning with step-wise rewards.

Based on Google's SRL paper:
- Dense step-wise rewards from expert trajectories
- Supervised learning on expert demonstrations
- KL divergence penalty to prevent overfitting
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import PreTrainedModel, PreTrainedTokenizer

from .reward_normalizer import RewardNormalizer
from .kl_controller import KLController

logger = logging.getLogger(__name__)


class SRLTrainer:
    """
    Trains models using Supervised Reinforcement Learning (SRL).
    
    SRL uses step-wise dense rewards from expert trajectories to guide
    model learning while maintaining stability via KL divergence penalties.
    """
    
    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        learning_rate: float = 1e-5,
        kl_penalty_weight: float = 0.1,
        max_kl: float = 0.1,
        reward_norm_method: str = "z_score"
    ):
        """
        Initialize SRL Trainer.
        
        Args:
            model: Model to train (e.g., Qwen 7B Instruct)
            tokenizer: Tokenizer for the model
            learning_rate: Learning rate for optimizer
            kl_penalty_weight: Weight for KL divergence penalty
            max_kl: Maximum allowed KL divergence
            reward_norm_method: Reward normalization method
        """
        self.model = model
        self.tokenizer = tokenizer
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
        
        # Store configuration
        self.learning_rate = learning_rate
        self.kl_penalty_weight = kl_penalty_weight
        self.max_kl = max_kl
        
        # Initialize components
        self.reward_normalizer = RewardNormalizer(method=reward_norm_method)
        self.kl_controller = KLController(max_kl=max_kl, kl_weight=kl_penalty_weight)
        
        # Set reference policy (initial model state for KL computation)
        self.reference_policy_state = None
        self._save_reference_policy()
        
        # Training state
        self.current_kl = 0.0
        self.training_step_count = 0
        
        logger.info(
            f"SRLTrainer initialized (lr={learning_rate}, "
            f"kl_weight={kl_penalty_weight}, max_kl={max_kl})"
        )
    
    def _save_reference_policy(self):
        """Save reference policy state for KL divergence computation."""
        # Save model state dict as reference
        self.reference_policy_state = {
            k: v.clone() for k, v in self.model.state_dict().items()
        }
        logger.debug("Reference policy state saved")
    
    def train_step(
        self,
        expert_trajectory: Dict[str, Any],
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor
    ) -> Dict[str, float]:
        """
        Perform one training step using expert trajectory.
        
        Args:
            expert_trajectory: Expert trajectory with steps and rewards
            input_ids: Tokenized input sequence
            attention_mask: Attention mask for input
        
        Returns:
            Dict with training metrics (loss, kl_divergence, reward, kl_penalty)
        """
        self.model.train()
        self.optimizer.zero_grad()
        
        # Extract step-wise rewards from expert trajectory
        steps = expert_trajectory.get("steps", [])
        if not steps:
            logger.warning("Expert trajectory has no steps")
            return {
                "loss": 0.0,
                "kl_divergence": 0.0,
                "reward": 0.0,
                "kl_penalty": 0.0
            }
        
        rewards = [step.get("reward", 0.0) for step in steps]
        
        # Normalize rewards
        normalized_rewards = self.reward_normalizer.normalize(rewards)
        
        # Get model predictions (logits)
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
        current_logits = outputs.logits
        
        # Get reference policy logits (from saved reference policy)
        # Note: In practice, we'd run reference policy forward pass, but for efficiency
        # we approximate using initial model state or use a cached reference model
        # For now, we'll compute KL from current logits distribution
        with torch.no_grad():
            # Load reference policy state temporarily
            reference_state = self.model.state_dict()
            self.model.load_state_dict(self.reference_policy_state)
            ref_outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            reference_logits = ref_outputs.logits
            # Restore current state
            self.model.load_state_dict(reference_state)
        
        # Compute KL divergence penalty
        kl_penalty = self.kl_controller.compute_kl_penalty(
            current_policy_logits=current_logits,
            reference_policy_logits=reference_logits
        )
        
        # Compute supervised loss on expert steps
        # For SRL, we want to maximize likelihood of expert actions weighted by rewards
        # Convert expert trajectory steps to target tokens
        # For simplicity, we'll use the expected outcome as the target
        target_text = expert_trajectory.get("expected_outcome", "")
        if not target_text:
            # Fallback: use problem statement as target
            target_text = expert_trajectory.get("problem", "")
        
        # Tokenize target
        target_tokens = self.tokenizer(
            target_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=input_ids.size(1)
        )
        target_ids = target_tokens["input_ids"].to(self.model.device)
        
        # Compute cross-entropy loss (supervised learning component)
        # Shift for language modeling
        shift_logits = current_logits[..., :-1, :].contiguous()
        shift_labels = target_ids[..., 1:].contiguous()
        
        # Flatten for loss computation
        loss_fct = nn.CrossEntropyLoss(reduction="none")
        token_losses = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1)
        )
        
        # Reshape to sequence length
        token_losses = token_losses.view(shift_labels.size())
        
        # Weight by normalized step rewards
        # Map rewards to sequence positions (simple uniform distribution for now)
        # In practice, you'd align rewards with specific token positions
        num_tokens = token_losses.size(-1)
        num_steps = len(normalized_rewards)
        
        # Create reward weights per token
        if num_steps > 0:
            # Distribute rewards across tokens
            tokens_per_step = max(1, num_tokens // num_steps)
            reward_weights = torch.ones_like(token_losses)
            
            for i, reward in enumerate(normalized_rewards):
                start_idx = i * tokens_per_step
                end_idx = min((i + 1) * tokens_per_step, num_tokens)
                if start_idx < num_tokens:
                    # Scale reward to be positive (add 1.0 to ensure positive weights)
                    reward_weights[:, start_idx:end_idx] = 1.0 + reward
        else:
            reward_weights = torch.ones_like(token_losses)
        
        # Weighted supervised loss
        weighted_loss = (token_losses * reward_weights).mean()
        
        # Total loss: supervised loss + KL penalty
        total_loss = weighted_loss + kl_penalty
        
        # Backward pass
        total_loss.backward()
        
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        
        # Optimizer step
        self.optimizer.step()
        
        # Update KL tracking
        with torch.no_grad():
            kl_div = self.kl_controller.compute_kl_divergence(
                current_policy_logits=current_logits,
                reference_policy_logits=reference_logits
            )
            self.current_kl = kl_div.item()
        
        # Update training step count
        self.training_step_count += 1
        
        # Metrics
        metrics = {
            "loss": total_loss.item(),
            "supervised_loss": weighted_loss.item(),
            "kl_divergence": self.current_kl,
            "kl_penalty": kl_penalty.item(),
            "mean_reward": sum(normalized_rewards) / len(normalized_rewards) if normalized_rewards else 0.0,
            "total_reward": sum(normalized_rewards)
        }
        
        # Check if training should stop due to KL divergence
        if self.kl_controller.should_stop_training(self.current_kl):
            logger.error(f"Training stopped due to excessive KL divergence: {self.current_kl:.4f}")
            metrics["training_stopped"] = True
        
        logger.debug(
            f"SRL step {self.training_step_count}: "
            f"loss={metrics['loss']:.4f}, kl={metrics['kl_divergence']:.4f}"
        )
        
        return metrics
    
    def train_epoch(
        self,
        expert_trajectories: List[Dict[str, Any]],
        batch_size: int = 32,
        device: Optional[torch.device] = None
    ) -> Dict[str, float]:
        """
        Train for one epoch on expert trajectories.
        
        Args:
            expert_trajectories: List of expert trajectories
            batch_size: Batch size for training
            device: Device to run training on
        
        Returns:
            Dict with epoch metrics
        """
        if device is None:
            device = next(self.model.parameters()).device
        
        logger.info(f"Training epoch on {len(expert_trajectories)} trajectories (batch_size={batch_size})")
        
        self.model.to(device)
        self.model.train()
        
        # Aggregate metrics
        total_loss = 0.0
        total_supervised_loss = 0.0
        total_kl = 0.0
        total_kl_penalty = 0.0
        total_reward = 0.0
        num_steps = 0
        
        # Process trajectories in batches
        for batch_start in range(0, len(expert_trajectories), batch_size):
            batch_end = min(batch_start + batch_size, len(expert_trajectories))
            batch_trajectories = expert_trajectories[batch_start:batch_end]
            
            # Process each trajectory in the batch
            for trajectory in batch_trajectories:
                # Tokenize input (problem statement)
                problem_text = trajectory.get("problem", "")
                if not problem_text:
                    logger.warning("Skipping trajectory with no problem statement")
                    continue
                
                # Tokenize input
                input_tokens = self.tokenizer(
                    problem_text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512  # Reasonable max length
                )
                input_ids = input_tokens["input_ids"].to(device)
                attention_mask = input_tokens["attention_mask"].to(device)
                
                # Train step
                try:
                    step_metrics = self.train_step(
                        expert_trajectory=trajectory,
                        input_ids=input_ids,
                        attention_mask=attention_mask
                    )
                    
                    # Accumulate metrics
                    total_loss += step_metrics.get("loss", 0.0)
                    total_supervised_loss += step_metrics.get("supervised_loss", 0.0)
                    total_kl += step_metrics.get("kl_divergence", 0.0)
                    total_kl_penalty += step_metrics.get("kl_penalty", 0.0)
                    total_reward += step_metrics.get("mean_reward", 0.0)
                    num_steps += 1
                    
                    # Check if training stopped
                    if step_metrics.get("training_stopped", False):
                        logger.error("Training stopped due to KL divergence - ending epoch early")
                        break
                
                except Exception as e:
                    logger.error(f"Error in training step: {e}", exc_info=True)
                    continue
            
            # Early stop if KL divergence too high
            if num_steps > 0 and self.current_kl > self.kl_controller.max_kl * 2:
                logger.warning("Stopping epoch early due to excessive KL divergence")
                break
        
        # Compute epoch averages
        if num_steps == 0:
            logger.warning("No training steps completed in epoch")
            return {
                "epoch_loss": 0.0,
                "epoch_supervised_loss": 0.0,
                "epoch_kl_divergence": 0.0,
                "epoch_kl_penalty": 0.0,
                "epoch_reward": 0.0,
                "num_steps": 0
            }
        
        metrics = {
            "epoch_loss": total_loss / num_steps,
            "epoch_supervised_loss": total_supervised_loss / num_steps,
            "epoch_kl_divergence": total_kl / num_steps,
            "epoch_kl_penalty": total_kl_penalty / num_steps,
            "epoch_reward": total_reward / num_steps,
            "num_steps": num_steps,
            "final_kl": self.current_kl
        }
        
        logger.info(
            f"Epoch complete: loss={metrics['epoch_loss']:.4f}, "
            f"kl={metrics['epoch_kl_divergence']:.4f}, "
            f"steps={num_steps}"
        )
        
        return metrics

