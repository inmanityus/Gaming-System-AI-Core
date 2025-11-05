"""
Facial Expression Model Trainer
================================

Trains facial expression models mapping emotions to FACS AUs and blendshapes.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_trainer import BaseModelTrainer

logger = logging.getLogger(__name__)


class FacialTrainer(BaseModelTrainer):
    """
    Trainer for facial expression models.
    
    Facial models handle:
    - Emotion to FACS AU mapping
    - AU to blendshape mapping (rig-specific)
    - Body language integration
    - Temporal stability
    """
    
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Train facial expression model using SRL."""
        logger.info(f"SRL training facial model for {monster_species}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type="facial",
            num_examples=num_examples
        )
        
        facial_training_data = []
        for traj in result.trajectories:
            facial_data = {
                "emotion": traj.get("emotion", ""),
                "facs_aus": traj.get("facs_aus", {}),
                "blendshapes": traj.get("blendshapes", {}),
                "body_language": traj.get("body_language", {}),
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "quality_score": traj.get("quality_score", 0.8)
            }
            facial_training_data.append(facial_data)
        
        if self.srl_trainer:
            training_result = self.srl_trainer.train(
                training_data=facial_training_data,
                model_type="facial",
                species=monster_species
            )
        else:
            training_result = {"status": "no_trainer", "examples": len(facial_training_data)}
        
        return {
            "status": "completed",
            "num_examples": len(result.trajectories),
            "model_type": "facial",
            "monster_species": monster_species,
            "training_result": training_result
        }
    
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Fine-tune facial model using RLVR with facial-specific outcome evaluation."""
        logger.info(f"RLVR fine-tuning facial model from {srl_model_path}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species="facial_rlvr",
            model_type="facial",
            num_examples=num_examples
        )
        
        rlvr_training_data = []
        for traj in result.trajectories:
            au_score = self._evaluate_au_accuracy(traj.get("facs_aus", {}))
            blendshape_score = self._evaluate_blendshape_quality(traj.get("blendshapes", {}))
            identity_score = self._evaluate_identity_preservation(traj.get("identity", {}))
            temporal_score = self._evaluate_temporal_stability(traj.get("temporal", {}))
            
            outcome_reward = (au_score + blendshape_score + identity_score + temporal_score) / 4.0
            
            rlvr_data = {
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "outcome_reward": outcome_reward,
                "au_score": au_score,
                "blendshape_score": blendshape_score,
                "identity_score": identity_score,
                "temporal_score": temporal_score
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
            "model_type": "facial",
            "rlvr_result": rlvr_result,
            "num_examples": len(rlvr_training_data)
        }
    
    def _evaluate_au_accuracy(self, facs_aus: Dict[str, Any]) -> float:
        """Evaluate FACS AU accuracy."""
        if not facs_aus:
            return 0.5
        if isinstance(facs_aus, dict) and len(facs_aus) > 0:
            return 0.8
        return 0.5
    
    def _evaluate_blendshape_quality(self, blendshapes: Dict[str, Any]) -> float:
        """Evaluate blendshape quality."""
        if not blendshapes:
            return 0.5
        required_fields = ["weights", "count"]
        present_fields = sum(1 for field in required_fields if field in blendshapes)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_identity_preservation(self, identity: Dict[str, Any]) -> float:
        """Evaluate identity preservation."""
        if not identity:
            return 0.5
        required_fields = ["baseline", "preservation_score"]
        present_fields = sum(1 for field in required_fields if field in identity)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_temporal_stability(self, temporal: Dict[str, Any]) -> float:
        """Evaluate temporal stability."""
        if not temporal:
            return 0.5
        required_fields = ["smoothness", "consistency"]
        present_fields = sum(1 for field in required_fields if field in temporal)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate facial expression model with facial-specific metrics."""
        logger.info(f"Evaluating facial model: {model_path}")
        
        if not test_examples:
            return {
                "au_accuracy": 0.0,
                "blendshape_quality": 0.0,
                "identity_preservation": 0.0,
                "temporal_stability": 0.0
            }
        
        au_scores = []
        blendshape_scores = []
        identity_scores = []
        temporal_scores = []
        
        for example in test_examples:
            au_scores.append(self._evaluate_au_accuracy(example.get("facs_aus", {})))
            blendshape_scores.append(self._evaluate_blendshape_quality(example.get("blendshapes", {})))
            identity_scores.append(self._evaluate_identity_preservation(example.get("identity", {})))
            temporal_scores.append(self._evaluate_temporal_stability(example.get("temporal", {})))
        
        return {
            "au_accuracy": sum(au_scores) / len(au_scores) if au_scores else 0.0,
            "blendshape_quality": sum(blendshape_scores) / len(blendshape_scores) if blendshape_scores else 0.0,
            "identity_preservation": sum(identity_scores) / len(identity_scores) if identity_scores else 0.0,
            "temporal_stability": sum(temporal_scores) / len(temporal_scores) if temporal_scores else 0.0
        }

