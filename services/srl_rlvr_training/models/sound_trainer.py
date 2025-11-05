"""
Sound Model Trainer
===================

Trains sound models for noise and soundtrack generation.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_trainer import BaseModelTrainer

logger = logging.getLogger(__name__)


class SoundTrainer(BaseModelTrainer):
    """
    Trainer for sound models.
    
    Sound models handle:
    - Noise generation (ambient, environmental)
    - Soundtrack generation
    - Audio quality
    - Contextual appropriateness
    """
    
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Train sound model using SRL."""
        logger.info(f"SRL training sound model for {monster_species}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species=monster_species,
            model_type="sounds",
            num_examples=num_examples
        )
        
        sound_training_data = []
        for traj in result.trajectories:
            sound_data = {
                "noise": traj.get("noise", {}),
                "soundtrack": traj.get("soundtrack", {}),
                "audio_quality": traj.get("audio_quality", {}),
                "context": traj.get("context", {}),
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "quality_score": traj.get("quality_score", 0.8)
            }
            sound_training_data.append(sound_data)
        
        if self.srl_trainer:
            training_result = self.srl_trainer.train(
                training_data=sound_training_data,
                model_type="sounds",
                species=monster_species
            )
        else:
            training_result = {"status": "no_trainer", "examples": len(sound_training_data)}
        
        return {
            "status": "completed",
            "num_examples": len(result.trajectories),
            "model_type": "sounds",
            "monster_species": monster_species,
            "training_result": training_result
        }
    
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """Fine-tune sound model using RLVR with sound-specific outcome evaluation."""
        logger.info(f"RLVR fine-tuning sound model from {srl_model_path}")
        
        result = self.collaboration_orchestrator.generate_training_examples(
            monster_species="sound_rlvr",
            model_type="sounds",
            num_examples=num_examples
        )
        
        rlvr_training_data = []
        for traj in result.trajectories:
            audio_score = self._evaluate_audio_quality(traj.get("audio_quality", {}))
            context_score = self._evaluate_contextual_appropriateness(traj.get("context", {}))
            noise_score = self._evaluate_noise_generation(traj.get("noise", {}))
            soundtrack_score = self._evaluate_soundtrack_quality(traj.get("soundtrack", {}))
            
            outcome_reward = (audio_score + context_score + noise_score + soundtrack_score) / 4.0
            
            rlvr_data = {
                "input": traj.get("input", ""),
                "output": traj.get("output", ""),
                "outcome_reward": outcome_reward,
                "audio_score": audio_score,
                "context_score": context_score,
                "noise_score": noise_score,
                "soundtrack_score": soundtrack_score
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
            "model_type": "sounds",
            "rlvr_result": rlvr_result,
            "num_examples": len(rlvr_training_data)
        }
    
    def _evaluate_audio_quality(self, audio_quality: Dict[str, Any]) -> float:
        """Evaluate audio quality."""
        if not audio_quality:
            return 0.5
        required_fields = ["sample_rate", "bit_depth", "clarity"]
        present_fields = sum(1 for field in required_fields if field in audio_quality)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_contextual_appropriateness(self, context: Dict[str, Any]) -> float:
        """Evaluate contextual appropriateness."""
        if not context:
            return 0.5
        required_fields = ["scene", "mood", "timing"]
        present_fields = sum(1 for field in required_fields if field in context)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_noise_generation(self, noise: Dict[str, Any]) -> float:
        """Evaluate noise generation quality."""
        if not noise:
            return 0.5
        required_fields = ["type", "intensity", "realism"]
        present_fields = sum(1 for field in required_fields if field in noise)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def _evaluate_soundtrack_quality(self, soundtrack: Dict[str, Any]) -> float:
        """Evaluate soundtrack quality."""
        if not soundtrack:
            return 0.5
        required_fields = ["composition", "mixing", "emotional_impact"]
        present_fields = sum(1 for field in required_fields if field in soundtrack)
        return present_fields / len(required_fields) if required_fields else 0.5
    
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate sound model with sound-specific metrics."""
        logger.info(f"Evaluating sound model: {model_path}")
        
        if not test_examples:
            return {
                "audio_quality": 0.0,
                "contextual_appropriateness": 0.0,
                "noise_generation_quality": 0.0,
                "soundtrack_quality": 0.0
            }
        
        audio_scores = []
        context_scores = []
        noise_scores = []
        soundtrack_scores = []
        
        for example in test_examples:
            audio_scores.append(self._evaluate_audio_quality(example.get("audio_quality", {})))
            context_scores.append(self._evaluate_contextual_appropriateness(example.get("context", {})))
            noise_scores.append(self._evaluate_noise_generation(example.get("noise", {})))
            soundtrack_scores.append(self._evaluate_soundtrack_quality(example.get("soundtrack", {})))
        
        return {
            "audio_quality": sum(audio_scores) / len(audio_scores) if audio_scores else 0.0,
            "contextual_appropriateness": sum(context_scores) / len(context_scores) if context_scores else 0.0,
            "noise_generation_quality": sum(noise_scores) / len(noise_scores) if noise_scores else 0.0,
            "soundtrack_quality": sum(soundtrack_scores) / len(soundtrack_scores) if soundtrack_scores else 0.0
        }

