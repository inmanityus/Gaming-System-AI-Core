"""
Tree Model Trainer
=================

Trains tree models for tree generation.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_trainer import BaseModelTrainer

logger = logging.getLogger(__name__)


class TreeTrainer(BaseModelTrainer):
    """
    Trainer for tree models.
    
    Tree models handle:
    - Tree generation
    - Species variety
    - Age variations
    - Environmental adaptation
    """
    
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Train tree model using SRL."""
        logger.info(f"SRL training tree model for {monster_species}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type="trees",
            num_examples=num_examples
        )
        
        tree_training_data = []
        for traj in result.trajectories:
            tree_data = {
                "species": traj.get("species", {}),
                "age": traj.get("age", {}),
                "environment": traj.get("environment", {}),
                "structure": traj.get("structure", {}),
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "quality_score": traj.get("quality_score", 0.8)
            }
            tree_training_data.append(tree_data)
        
        if self.srl_trainer:
            training_result = self.srl_trainer.train(
                training_data=tree_training_data,
                model_type="trees",
                species=monster_species
            )
        else:
            training_result = {"status": "no_trainer", "examples": len(tree_training_data)}
        
        return {
            "status": "completed",
            "num_examples": len(result.trajectories),
            "model_type": "trees",
            "monster_species": monster_species,
            "training_result": training_result
        }
    
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Fine-tune tree model using RLVR with tree-specific outcome evaluation."""
        logger.info(f"RLVR fine-tuning tree model from {srl_model_path}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species="tree_rlvr",
            model_type="trees",
            num_examples=num_examples
        )
        
        rlvr_training_data = []
        for traj in result.trajectories:
            quality_score = self._evaluate_tree_quality(traj.get("structure", {}))
            variety_score = self._evaluate_species_variety(traj.get("species", {}))
            age_score = self._evaluate_age_variation(traj.get("age", {}))
            env_score = self._evaluate_environmental_adaptation(traj.get("environment", {}))
            
            outcome_reward = (quality_score + variety_score + age_score + env_score) / 4.0
            
            rlvr_data = {
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "outcome_reward": outcome_reward,
                "quality_score": quality_score,
                "variety_score": variety_score,
                "age_score": age_score,
                "env_score": env_score
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
            "model_type": "trees",
            "rlvr_result": rlvr_result,
            "num_examples": len(rlvr_training_data)
        }
    
    def _evaluate_tree_quality(self, structure: Dict[str, Any]) -> float:
        """Evaluate tree quality."""
        if not structure:
            return 0.5
        required_fields = ["trunk", "branches", "leaves", "roots"]
        present_fields = sum(1 for field in required_fields if field in structure)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_species_variety(self, species: Dict[str, Any]) -> float:
        """Evaluate species variety."""
        if not species:
            return 0.5
        if isinstance(species, dict) and len(species) > 0:
            return 0.8
        return 0.5
    
    def _evaluate_age_variation(self, age: Dict[str, Any]) -> float:
        """Evaluate age variation."""
        if not age:
            return 0.5
        required_fields = ["young", "mature", "old"]
        present_fields = sum(1 for field in required_fields if field in age)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_environmental_adaptation(self, environment: Dict[str, Any]) -> float:
        """Evaluate environmental adaptation."""
        if not environment:
            return 0.5
        required_fields = ["climate", "soil", "terrain"]
        present_fields = sum(1 for field in required_fields if field in environment)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate tree model with tree-specific metrics."""
        logger.info(f"Evaluating tree model: {model_path}")
        
        if not test_examples:
            return {
                "tree_quality": 0.0,
                "species_variety": 0.0,
                "age_variation": 0.0,
                "environmental_adaptation": 0.0
            }
        
        quality_scores = []
        variety_scores = []
        age_scores = []
        env_scores = []
        
        for example in test_examples:
            quality_scores.append(self._evaluate_tree_quality(example.get("structure", {})))
            variety_scores.append(self._evaluate_species_variety(example.get("species", {})))
            age_scores.append(self._evaluate_age_variation(example.get("age", {})))
            env_scores.append(self._evaluate_environmental_adaptation(example.get("environment", {})))
        
        return {
            "tree_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
            "species_variety": sum(variety_scores) / len(variety_scores) if variety_scores else 0.0,
            "age_variation": sum(age_scores) / len(age_scores) if age_scores else 0.0,
            "environmental_adaptation": sum(env_scores) / len(env_scores) if env_scores else 0.0
        }

