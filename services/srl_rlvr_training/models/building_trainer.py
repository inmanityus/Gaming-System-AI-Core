"""
Building Model Trainer
=====================

Trains building models for exterior and interior generation.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_trainer import BaseModelTrainer

logger = logging.getLogger(__name__)


class BuildingTrainer(BaseModelTrainer):
    """
    Trainer for building models.
    
    Building models handle:
    - Exterior generation (architectural styles, materials)
    - Interior generation (layout, furnishings, atmosphere)
    - Style consistency
    - Scale accuracy
    """
    
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Train building model using SRL."""
        logger.info(f"SRL training building model for {monster_species}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type="buildings",
            num_examples=num_examples
        )
        
        # Building-specific training data preparation
        # Focus on: exterior styles, interior layouts, materials, scale
        building_training_data = []
        for traj in result.trajectories:
            # Extract building-specific features from trajectory
            building_data = {
                "exterior": traj.get("exterior", {}),
                "interior": traj.get("interior", {}),
                "materials": traj.get("materials", {}),
                "scale": traj.get("scale", {}),
                "style": traj.get("style", ""),
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "quality_score": traj.get("quality_score", 0.8)
            }
            building_training_data.append(building_data)
        
        # Use base trainer's SRL training with building-specific data
        if self.srl_trainer:
            training_result = self.srl_trainer.train(
                training_data=building_training_data,
                model_type="buildings",
                species=monster_species
            )
        else:
            training_result = {"status": "no_trainer", "examples": len(building_training_data)}
        
        return {
            "status": "completed",
            "num_examples": len(result.trajectories),
            "model_type": "buildings",
            "monster_species": monster_species,
            "training_result": training_result
        }
    
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Fine-tune building model using RLVR with building-specific outcome evaluation."""
        logger.info(f"RLVR fine-tuning building model from {srl_model_path}")
        
        # Generate RLVR training examples with building-specific outcomes
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species="building_rlvr",
            model_type="buildings",
            num_examples=num_examples
        )
        
        # Prepare RLVR training data with building-specific outcome evaluation
        rlvr_training_data = []
        for traj in result.trajectories:
            # Compute building-specific outcome rewards
            # Check: style consistency, scale accuracy, interior quality, exterior quality
            style_score = self._evaluate_style_consistency(traj.get("style", ""), traj.get("exterior", {}), traj.get("interior", {}))
            scale_score = self._evaluate_scale_accuracy(traj.get("scale", {}))
            interior_score = self._evaluate_interior_quality(traj.get("interior", {}))
            exterior_score = self._evaluate_exterior_quality(traj.get("exterior", {}))
            
            # Combined outcome reward
            outcome_reward = (style_score + scale_score + interior_score + exterior_score) / 4.0
            
            rlvr_data = {
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "outcome_reward": outcome_reward,
                "style_score": style_score,
                "scale_score": scale_score,
                "interior_score": interior_score,
                "exterior_score": exterior_score
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
            "model_type": "buildings",
            "rlvr_result": rlvr_result,
            "num_examples": len(rlvr_training_data)
        }
    
    def _evaluate_style_consistency(self, style: str, exterior: Dict[str, Any], interior: Dict[str, Any]) -> float:
        """Evaluate style consistency between exterior and interior."""
        if not style or not exterior or not interior:
            return 0.5
        
        # Check if style is mentioned in both exterior and interior
        style_mentioned = (
            style.lower() in str(exterior).lower() and
            style.lower() in str(interior).lower()
        )
        return 0.9 if style_mentioned else 0.5
    
    def _evaluate_scale_accuracy(self, scale: Dict[str, Any]) -> float:
        """Evaluate scale accuracy."""
        if not scale:
            return 0.5
        
        required_fields = ["width", "height", "depth", "units"]
        present_fields = sum(1 for field in required_fields if field in scale)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_interior_quality(self, interior: Dict[str, Any]) -> float:
        """Evaluate interior quality."""
        if not interior:
            return 0.5
        
        required_fields = ["layout", "furnishings", "atmosphere"]
        present_fields = sum(1 for field in required_fields if field in interior)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_exterior_quality(self, exterior: Dict[str, Any]) -> float:
        """Evaluate exterior quality."""
        if not exterior:
            return 0.5
        
        required_fields = ["architectural_style", "materials", "features"]
        present_fields = sum(1 for field in required_fields if field in exterior)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate building model with building-specific metrics."""
        logger.info(f"Evaluating building model: {model_path}")
        
        if not test_examples:
            return {
                "style_consistency": 0.0,
                "scale_accuracy": 0.0,
                "interior_quality": 0.0,
                "exterior_quality": 0.0
            }
        
        # Evaluate each example
        style_scores = []
        scale_scores = []
        interior_scores = []
        exterior_scores = []
        
        for example in test_examples:
            style = example.get("style", "")
            exterior = example.get("exterior", {})
            interior = example.get("interior", {})
            scale = example.get("scale", {})
            
            style_scores.append(self._evaluate_style_consistency(style, exterior, interior))
            scale_scores.append(self._evaluate_scale_accuracy(scale))
            interior_scores.append(self._evaluate_interior_quality(interior))
            exterior_scores.append(self._evaluate_exterior_quality(exterior))
        
        # Compute averages
        return {
            "style_consistency": sum(style_scores) / len(style_scores) if style_scores else 0.0,
            "scale_accuracy": sum(scale_scores) / len(scale_scores) if scale_scores else 0.0,
            "interior_quality": sum(interior_scores) / len(interior_scores) if interior_scores else 0.0,
            "exterior_quality": sum(exterior_scores) / len(exterior_scores) if exterior_scores else 0.0
        }

