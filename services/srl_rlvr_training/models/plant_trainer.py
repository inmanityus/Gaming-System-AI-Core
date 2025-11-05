"""
Plant Model Trainer
==================

Trains plant models for flora generation.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_trainer import BaseModelTrainer

logger = logging.getLogger(__name__)


class PlantTrainer(BaseModelTrainer):
    """
    Trainer for plant models.
    
    Plant models handle:
    - Flora generation
    - Ecosystem integration
    - Seasonal variations
    - Growth patterns
    """
    
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Train plant model using SRL."""
        logger.info(f"SRL training plant model for {monster_species}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type="plants",
            num_examples=num_examples
        )
        
        # Plant-specific training data preparation
        # Focus on: flora characteristics, ecosystem integration, seasonal variations, growth patterns
        plant_training_data = []
        for traj in result.trajectories:
            # Extract plant-specific features from trajectory
            plant_data = {
                "flora": traj.get("flora", {}),
                "ecosystem": traj.get("ecosystem", {}),
                "seasonal": traj.get("seasonal", {}),
                "growth": traj.get("growth", {}),
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "quality_score": traj.get("quality_score", 0.8)
            }
            plant_training_data.append(plant_data)
        
        # Use base trainer's SRL training with plant-specific data
        if self.srl_trainer:
            training_result = self.srl_trainer.train(
                training_data=plant_training_data,
                model_type="plants",
                species=monster_species
            )
        else:
            training_result = {"status": "no_trainer", "examples": len(plant_training_data)}
        
        return {
            "status": "completed",
            "num_examples": len(result.trajectories),
            "model_type": "plants",
            "monster_species": monster_species,
            "training_result": training_result
        }
    
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Fine-tune plant model using RLVR with plant-specific outcome evaluation."""
        logger.info(f"RLVR fine-tuning plant model from {srl_model_path}")
        
        # Generate RLVR training examples with plant-specific outcomes
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species="plant_rlvr",
            model_type="plants",
            num_examples=num_examples
        )
        
        # Prepare RLVR training data with plant-specific outcome evaluation
        rlvr_training_data = []
        for traj in result.trajectories:
            # Compute plant-specific outcome rewards
            # Check: flora quality, ecosystem integration, seasonal variation, growth pattern accuracy
            flora_score = self._evaluate_flora_quality(traj.get("flora", {}))
            ecosystem_score = self._evaluate_ecosystem_integration(traj.get("ecosystem", {}))
            seasonal_score = self._evaluate_seasonal_variation(traj.get("seasonal", {}))
            growth_score = self._evaluate_growth_pattern(traj.get("growth", {}))
            
            # Combined outcome reward
            outcome_reward = (flora_score + ecosystem_score + seasonal_score + growth_score) / 4.0
            
            rlvr_data = {
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "outcome_reward": outcome_reward,
                "flora_score": flora_score,
                "ecosystem_score": ecosystem_score,
                "seasonal_score": seasonal_score,
                "growth_score": growth_score
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
            "model_type": "plants",
            "rlvr_result": rlvr_result,
            "num_examples": len(rlvr_training_data)
        }
    
    def _evaluate_flora_quality(self, flora: Dict[str, Any]) -> float:
        """Evaluate flora quality."""
        if not flora:
            return 0.5
        
        required_fields = ["species", "appearance", "habitat"]
        present_fields = sum(1 for field in required_fields if field in flora)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_ecosystem_integration(self, ecosystem: Dict[str, Any]) -> float:
        """Evaluate ecosystem integration."""
        if not ecosystem:
            return 0.5
        
        required_fields = ["niche", "interactions", "biodiversity"]
        present_fields = sum(1 for field in required_fields if field in ecosystem)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_seasonal_variation(self, seasonal: Dict[str, Any]) -> float:
        """Evaluate seasonal variation."""
        if not seasonal:
            return 0.5
        
        required_fields = ["spring", "summer", "fall", "winter"]
        present_fields = sum(1 for field in required_fields if field in seasonal)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_growth_pattern(self, growth: Dict[str, Any]) -> float:
        """Evaluate growth pattern accuracy."""
        if not growth:
            return 0.5
        
        required_fields = ["rate", "stages", "conditions"]
        present_fields = sum(1 for field in required_fields if field in growth)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate plant model with plant-specific metrics."""
        logger.info(f"Evaluating plant model: {model_path}")
        
        if not test_examples:
            return {
                "flora_quality": 0.0,
                "ecosystem_integration": 0.0,
                "seasonal_variation": 0.0,
                "growth_pattern_accuracy": 0.0
            }
        
        # Evaluate each example
        flora_scores = []
        ecosystem_scores = []
        seasonal_scores = []
        growth_scores = []
        
        for example in test_examples:
            flora = example.get("flora", {})
            ecosystem = example.get("ecosystem", {})
            seasonal = example.get("seasonal", {})
            growth = example.get("growth", {})
            
            flora_scores.append(self._evaluate_flora_quality(flora))
            ecosystem_scores.append(self._evaluate_ecosystem_integration(ecosystem))
            seasonal_scores.append(self._evaluate_seasonal_variation(seasonal))
            growth_scores.append(self._evaluate_growth_pattern(growth))
        
        # Compute averages
        return {
            "flora_quality": sum(flora_scores) / len(flora_scores) if flora_scores else 0.0,
            "ecosystem_integration": sum(ecosystem_scores) / len(ecosystem_scores) if ecosystem_scores else 0.0,
            "seasonal_variation": sum(seasonal_scores) / len(seasonal_scores) if seasonal_scores else 0.0,
            "growth_pattern_accuracy": sum(growth_scores) / len(growth_scores) if growth_scores else 0.0
        }

