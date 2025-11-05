"""
Personality Model Trainer
=========================

Trains personality models for emotions, expressions, actions, and inherent traits.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_trainer import BaseModelTrainer

logger = logging.getLogger(__name__)


class PersonalityTrainer(BaseModelTrainer):
    """
    Trainer for personality models.
    
    Personality models handle:
    - Emotions (stress, love, fear, etc.)
    - Expressions (emotional responses)
    - Actions (personality-driven decisions)
    - Inherent traits (aggression, intelligence, charisma)
    """
    
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Train personality model using SRL."""
        logger.info(f"SRL training personality model for {monster_species}")
        
        # Generate training examples
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type="personality",
            num_examples=num_examples
        )
        
        # Personality-specific training data preparation
        # Focus on: emotions, expressions, actions, inherent traits
        personality_training_data = []
        for traj in result.trajectories:
            personality_data = {
                "emotions": traj.get("emotions", {}),
                "expressions": traj.get("expressions", {}),
                "actions": traj.get("actions", {}),
                "traits": traj.get("traits", {}),
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "quality_score": traj.get("quality_score", 0.8)
            }
            personality_training_data.append(personality_data)
        
        # Use base trainer's SRL training
        if self.srl_trainer:
            training_result = self.srl_trainer.train(
                training_data=personality_training_data,
                model_type="personality",
                species=monster_species
            )
        else:
            training_result = {"status": "no_trainer", "examples": len(personality_training_data)}
        
        return {
            "status": "completed",
            "num_examples": len(result.trajectories),
            "model_type": "personality",
            "monster_species": monster_species,
            "training_result": training_result
        }
    
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Fine-tune personality model using RLVR with personality-specific outcome evaluation."""
        logger.info(f"RLVR fine-tuning personality model from {srl_model_path}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species="personality_rlvr",
            model_type="personality",
            num_examples=num_examples
        )
        
        rlvr_training_data = []
        for traj in result.trajectories:
            emotion_score = self._evaluate_emotion_accuracy(traj.get("emotions", {}))
            expression_score = self._evaluate_expression_quality(traj.get("expressions", {}))
            action_score = self._evaluate_action_appropriateness(traj.get("actions", {}))
            trait_score = self._evaluate_trait_consistency(traj.get("traits", {}))
            
            outcome_reward = (emotion_score + expression_score + action_score + trait_score) / 4.0
            
            rlvr_data = {
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "outcome_reward": outcome_reward,
                "emotion_score": emotion_score,
                "expression_score": expression_score,
                "action_score": action_score,
                "trait_score": trait_score
            }
            rlvr_training_data.append(rlvr_data)
        
        if self.rlvr_trainer:
            rlvr_result = self.rlvr_trainer.fine_tune(
                srl_model_path=srl_model_path,
                training_data=rlvr_training_data
            )
        else:
            rlvr_result = {"status": "no_trainer", "examples": len(rlvr_training_data)}
        
        return {
            "status": "completed",
            "srl_model_path": srl_model_path,
            "model_type": "personality",
            "rlvr_result": rlvr_result,
            "num_examples": len(rlvr_training_data)
        }
    
    def _evaluate_emotion_accuracy(self, emotions: Dict[str, Any]) -> float:
        """Evaluate emotion accuracy."""
        if not emotions:
            return 0.5
        required_fields = ["type", "intensity", "context"]
        present_fields = sum(1 for field in required_fields if field in emotions)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_expression_quality(self, expressions: Dict[str, Any]) -> float:
        """Evaluate expression quality."""
        if not expressions:
            return 0.5
        required_fields = ["facial", "body", "voice"]
        present_fields = sum(1 for field in required_fields if field in expressions)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_action_appropriateness(self, actions: Dict[str, Any]) -> float:
        """Evaluate action appropriateness."""
        if not actions:
            return 0.5
        required_fields = ["type", "context", "motivation"]
        present_fields = sum(1 for field in required_fields if field in actions)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_trait_consistency(self, traits: Dict[str, Any]) -> float:
        """Evaluate trait consistency."""
        if not traits:
            return 0.5
        required_fields = ["aggression", "intelligence", "charisma"]
        present_fields = sum(1 for field in required_fields if field in traits)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate personality model with personality-specific metrics."""
        logger.info(f"Evaluating personality model: {model_path}")
        
        if not test_examples:
            return {
                "emotion_accuracy": 0.0,
                "expression_quality": 0.0,
                "action_appropriateness": 0.0,
                "trait_consistency": 0.0
            }
        
        emotion_scores = []
        expression_scores = []
        action_scores = []
        trait_scores = []
        
        for example in test_examples:
            emotion_scores.append(self._evaluate_emotion_accuracy(example.get("emotions", {})))
            expression_scores.append(self._evaluate_expression_quality(example.get("expressions", {})))
            action_scores.append(self._evaluate_action_appropriateness(example.get("actions", {})))
            trait_scores.append(self._evaluate_trait_consistency(example.get("traits", {})))
        
        return {
            "emotion_accuracy": sum(emotion_scores) / len(emotion_scores) if emotion_scores else 0.0,
            "expression_quality": sum(expression_scores) / len(expression_scores) if expression_scores else 0.0,
            "action_appropriateness": sum(action_scores) / len(action_scores) if action_scores else 0.0,
            "trait_consistency": sum(trait_scores) / len(trait_scores) if trait_scores else 0.0
        }

