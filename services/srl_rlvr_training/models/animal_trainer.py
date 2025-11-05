"""
Animal Model Trainer
===================

Trains animal models for creature generation.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_trainer import BaseModelTrainer

logger = logging.getLogger(__name__)


class AnimalTrainer(BaseModelTrainer):
    """
    Trainer for animal models.
    
    Animal models handle:
    - Creature anatomy
    - Movement patterns
    - Behavior generation
    - Ecosystem integration
    """
    
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Train animal model using SRL with animal-specific features."""
        logger.info(f"SRL training animal model for {monster_species}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type="animals",
            num_examples=num_examples
        )
        
        # Animal-specific training data preparation
        # Focus on: anatomy, movement, behavior, ecosystem integration
        animal_training_data = []
        for traj in result.trajectories:
            # Extract animal-specific features from trajectory
            animal_data = {
                "anatomy": traj.get("anatomy", {}),
                "movement": traj.get("movement", {}),
                "behavior": traj.get("behavior", {}),
                "ecosystem": traj.get("ecosystem", {}),
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "quality_score": traj.get("quality_score", 0.8)
            }
            animal_training_data.append(animal_data)
        
        # Use base trainer's SRL training with animal-specific data
        if self.srl_trainer:
            training_result = self.srl_trainer.train(
                training_data=animal_training_data,
                model_type="animals",
                species=monster_species
            )
        else:
            training_result = {"status": "no_trainer", "examples": len(animal_training_data)}
        
        return {
            "status": "completed",
            "num_examples": len(result.trajectories),
            "model_type": "animals",
            "monster_species": monster_species,
            "training_result": training_result
        }
    
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Fine-tune animal model using RLVR with animal-specific outcome evaluation."""
        logger.info(f"RLVR fine-tuning animal model from {srl_model_path}")
        
        # Generate RLVR training examples with animal-specific outcomes
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species="animal_rlvr",
            model_type="animals",
            num_examples=num_examples
        )
        
        # Prepare RLVR training data with animal-specific outcome evaluation
        rlvr_training_data = []
        for traj in result.trajectories:
            # Compute animal-specific outcome rewards
            # Check: anatomy accuracy, movement quality, behavior realism, ecosystem fit
            anatomy_score = self._evaluate_anatomy(traj.get("output", ""), traj.get("anatomy", {}))
            movement_score = self._evaluate_movement(traj.get("movement", {}))
            behavior_score = self._evaluate_behavior(traj.get("behavior", {}))
            ecosystem_score = self._evaluate_ecosystem(traj.get("ecosystem", {}))
            
            # Combined outcome reward
            outcome_reward = (anatomy_score + movement_score + behavior_score + ecosystem_score) / 4.0
            
            rlvr_data = {
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "outcome_reward": outcome_reward,
                "anatomy_score": anatomy_score,
                "movement_score": movement_score,
                "behavior_score": behavior_score,
                "ecosystem_score": ecosystem_score
            }
            rlvr_training_data.append(rlvr_data)
        
        # Use base trainer's RLVR training
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
            "model_type": "animals",
            "rlvr_result": rlvr_result,
            "num_examples": len(rlvr_training_data)
        }
    
    def _evaluate_anatomy(self, output: str, anatomy: Dict[str, Any]) -> float:
        """Evaluate anatomy accuracy."""
        # Simple check: if anatomy fields are present and consistent
        if not anatomy:
            return 0.5
        
        required_fields = ["body_type", "limbs", "sensory_organs"]
        present_fields = sum(1 for field in required_fields if field in anatomy)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_movement(self, movement: Dict[str, Any]) -> float:
        """Evaluate movement quality."""
        if not movement:
            return 0.5
        
        required_fields = ["gait", "speed", "terrain_adaptation"]
        present_fields = sum(1 for field in required_fields if field in movement)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_behavior(self, behavior: Dict[str, Any]) -> float:
        """Evaluate behavior quality."""
        if not behavior:
            return 0.5
        
        required_fields = ["social", "feeding", "defense"]
        present_fields = sum(1 for field in required_fields if field in behavior)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_ecosystem(self, ecosystem: Dict[str, Any]) -> float:
        """Evaluate ecosystem integration."""
        if not ecosystem:
            return 0.5
        
        required_fields = ["habitat", "niche", "interactions"]
        present_fields = sum(1 for field in required_fields if field in ecosystem)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate animal model with animal-specific metrics."""
        logger.info(f"Evaluating animal model: {model_path}")
        
        if not test_examples:
            return {
                "anatomy_accuracy": 0.0,
                "movement_quality": 0.0,
                "behavior_quality": 0.0,
                "ecosystem_integration": 0.0
            }
        
        # Evaluate each example
        anatomy_scores = []
        movement_scores = []
        behavior_scores = []
        ecosystem_scores = []
        
        for example in test_examples:
            output = example.get("output", "")
            anatomy = example.get("anatomy", {})
            movement = example.get("movement", {})
            behavior = example.get("behavior", {})
            ecosystem = example.get("ecosystem", {})
            
            anatomy_scores.append(self._evaluate_anatomy(output, anatomy))
            movement_scores.append(self._evaluate_movement(movement))
            behavior_scores.append(self._evaluate_behavior(behavior))
            ecosystem_scores.append(self._evaluate_ecosystem(ecosystem))
        
        # Compute averages
        return {
            "anatomy_accuracy": sum(anatomy_scores) / len(anatomy_scores) if anatomy_scores else 0.0,
            "movement_quality": sum(movement_scores) / len(movement_scores) if movement_scores else 0.0,
            "behavior_quality": sum(behavior_scores) / len(behavior_scores) if behavior_scores else 0.0,
            "ecosystem_integration": sum(ecosystem_scores) / len(ecosystem_scores) if ecosystem_scores else 0.0
        }

