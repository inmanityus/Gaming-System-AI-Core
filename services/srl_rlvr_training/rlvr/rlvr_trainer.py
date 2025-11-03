"""
RLVR Trainer
===========

Implements Reinforcement Learning with Verifiable Rewards (RLVR).

RLVR focuses on outcome-based rewards rather than step-wise rewards,
making it ideal for fine-tuning after SRL pretraining.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import PreTrainedModel, PreTrainedTokenizer

from .ppo_trainer import PPOTrainer
from ..srl.kl_controller import KLController

logger = logging.getLogger(__name__)


class RLVRTrainer:
    """
    Trains models using RLVR (Reinforcement Learning with Verifiable Rewards).
    
    RLVR uses outcome-based rewards to fine-tune models after SRL pretraining.
    This approach is particularly effective for gaming scenarios where the
    final outcome (e.g., generated content quality) is what matters.
    """
    
    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        reward_model: Optional[nn.Module] = None,
        use_ppo: bool = True,
        use_dpo: bool = False,
        learning_rate: float = 1e-6,
        kl_penalty_weight: float = 0.1,
        max_kl: float = 0.1,
        gamma: float = 0.99  # Discount factor for returns
    ):
        """
        Initialize RLVR Trainer.
        
        Args:
            model: Model to fine-tune (pretrained via SRL)
            tokenizer: Tokenizer for the model
            reward_model: Reward model for outcome verification
            use_ppo: Use PPO training algorithm
            use_dpo: Use DPO training algorithm (alternative to PPO)
            learning_rate: Learning rate for optimizer
            kl_penalty_weight: Weight for KL divergence penalty
            max_kl: Maximum allowed KL divergence
            gamma: Discount factor for computing returns
        """
        self.model = model
        self.tokenizer = tokenizer
        self.reward_model = reward_model
        self.use_ppo = use_ppo
        self.use_dpo = use_dpo
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
        self.gamma = gamma
        
        # Initialize PPO trainer if using PPO
        if self.use_ppo:
            self.ppo_trainer = PPOTrainer(clip_epsilon=0.2, value_coef=0.5, entropy_coef=0.01)
        
        # Initialize KL controller for stability
        self.kl_controller = KLController(max_kl=max_kl, kl_weight=kl_penalty_weight)
        
        # Save reference policy (SRL-pretrained model state)
        self.reference_policy_state = {
            k: v.clone() for k, v in self.model.state_dict().items()
        }
        
        # Training state
        self.training_step_count = 0
        
        logger.info(f"RLVRTrainer initialized (ppo={use_ppo}, dpo={use_dpo}, lr={learning_rate})")
    
    def compute_outcome_reward(
        self,
        generated_output: str,
        expected_outcome: str
    ) -> float:
        """
        Compute outcome-based reward for RLVR.
        
        Uses reward model if available, otherwise uses similarity metrics.
        
        Args:
            generated_output: Generated text/output from model
            expected_outcome: Expected outcome (from expert trajectory)
        
        Returns:
            Reward score (0.0 to 1.0)
        """
        logger.debug("Computing outcome reward")
        
        # Use reward model if available
        if self.reward_model is not None:
            try:
                # Tokenize both outputs
                gen_tokens = self.tokenizer(
                    generated_output,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                ).to(self.model.device)
                
                exp_tokens = self.tokenizer(
                    expected_outcome,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                ).to(self.model.device)
                
                # Get reward from reward model
                with torch.no_grad():
                    reward = self.reward_model(gen_tokens["input_ids"], exp_tokens["input_ids"])
                    reward_score = torch.sigmoid(reward).item()
                
                return max(0.0, min(1.0, reward_score))
            
            except Exception as e:
                logger.warning(f"Reward model computation failed: {e}, falling back to similarity")
        
        # Fallback: Use text similarity (simple overlap-based metric)
        # In production, this would use more sophisticated metrics like BLEU, ROUGE, or semantic similarity
        gen_words = set(generated_output.lower().split())
        exp_words = set(expected_outcome.lower().split())
        
        if len(exp_words) == 0:
            return 0.0
        
        # Simple Jaccard similarity
        intersection = len(gen_words & exp_words)
        union = len(gen_words | exp_words)
        similarity = intersection / union if union > 0 else 0.0
        
        # Scale to [0, 1] range
        reward_score = similarity
        
        logger.debug(f"Outcome reward computed: {reward_score:.4f}")
        return max(0.0, min(1.0, reward_score))
    
    def train_step(
        self,
        srl_pretrained_output: Dict[str, Any],
        outcome_reward: float
    ) -> Dict[str, float]:
        """
        Perform one RLVR training step.
        
        Args:
            srl_pretrained_output: Output from SRL-pretrained model
            outcome_reward: Outcome-based reward score
        
        Returns:
            Dict with training metrics
        """
        # TODO: Implement actual RLVR training step
        # This will use either PPO or DPO algorithm
        
        if self.use_ppo:
            metrics = self._ppo_step(srl_pretrained_output, outcome_reward)
        elif self.use_dpo:
            metrics = self._dpo_step(srl_pretrained_output, outcome_reward)
        else:
            raise ValueError("Must use either PPO or DPO")
        
        return metrics
    
    def _ppo_step(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        generated_text: str,
        expected_outcome: str,
        old_log_probs: torch.Tensor
    ) -> Dict[str, float]:
        """
        PPO training step for RLVR.
        
        Args:
            input_ids: Tokenized input [batch, seq_len]
            attention_mask: Attention mask [batch, seq_len]
            generated_text: Generated output text
            expected_outcome: Expected outcome text
            old_log_probs: Log probabilities from old policy [batch, seq_len]
        
        Returns:
            Dict with training metrics
        """
        self.model.train()
        self.optimizer.zero_grad()
        
        # Get current policy output
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
        current_logits = outputs.logits
        
        # Compute new log probabilities
        log_probs = F.log_softmax(current_logits, dim=-1)
        # Get log prob of selected tokens (simplified - in practice would track action distribution)
        new_log_probs = log_probs.mean(dim=-1)  # Average across vocab for simplicity
        
        # Compute outcome reward
        outcome_reward = self.compute_outcome_reward(generated_text, expected_outcome)
        
        # Compute advantages and returns from outcome reward
        # For RLVR, reward is outcome-based (single scalar)
        # We need to distribute it across sequence
        seq_len = input_ids.size(1)
        returns = torch.full((seq_len,), outcome_reward, device=self.model.device)
        advantages = returns  # For simplicity, advantages = returns (no value function baseline)
        
        # Value estimates (would come from value head in full implementation)
        # For now, use simple approximation
        values = torch.full_like(returns, outcome_reward)
        
        # Compute PPO loss
        ppo_losses = self.ppo_trainer.compute_ppo_loss(
            old_log_probs=old_log_probs.squeeze(0) if old_log_probs.dim() > 1 else old_log_probs,
            new_log_probs=new_log_probs.squeeze(0) if new_log_probs.dim() > 1 else new_log_probs,
            advantages=advantages,
            returns=returns,
            values=values
        )
        
        # Compute KL divergence penalty
        with torch.no_grad():
            # Get reference policy logits
            ref_state = self.model.state_dict()
            self.model.load_state_dict(self.reference_policy_state)
            ref_outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            reference_logits = ref_outputs.logits
            self.model.load_state_dict(ref_state)
        
        kl_penalty = self.kl_controller.compute_kl_penalty(
            current_policy_logits=current_logits,
            reference_policy_logits=reference_logits
        )
        
        # Total loss
        total_loss = ppo_losses["total_loss"] + kl_penalty
        
        # Backward pass
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # Compute KL divergence
        with torch.no_grad():
            kl_div = self.kl_controller.compute_kl_divergence(
                current_policy_logits=current_logits,
                reference_policy_logits=reference_logits
            )
        
        self.training_step_count += 1
        
        metrics = {
            "loss": total_loss.item(),
            "policy_loss": ppo_losses["policy_loss"].item(),
            "value_loss": ppo_losses["value_loss"].item(),
            "entropy": ppo_losses["entropy"].item(),
            "kl_divergence": kl_div.item(),
            "kl_penalty": kl_penalty.item(),
            "outcome_reward": outcome_reward,
            "ratio": ppo_losses.get("ratio", torch.tensor(1.0)).item()
        }
        
        logger.debug(
            f"RLVR PPO step {self.training_step_count}: "
            f"loss={metrics['loss']:.4f}, reward={metrics['outcome_reward']:.4f}, "
            f"kl={metrics['kl_divergence']:.4f}"
        )
        
        return metrics
    
    def _dpo_step(
        self,
        srl_pretrained_output: Dict[str, Any],
        outcome_reward: float
    ) -> Dict[str, float]:
        """DPO training step."""
        # TODO: Implement DPO algorithm
        logger.debug("DPO training step")
        return {"loss": 0.0, "reward": outcome_reward}

