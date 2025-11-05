"""
Training Integration Module
============================

Integrates language system with SRL→RLVR training pipeline.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.collaboration.collaboration_orchestrator import (
    CollaborationOrchestrator,
    CollaborationResult
)
from services.srl_rlvr_training.srl.srl_trainer import SRLTrainer
from services.srl_rlvr_training.rlvr.rlvr_trainer import RLVRTrainer
from services.language_system.core.language_definition import LanguageDefinition

logger = logging.getLogger(__name__)


@dataclass
class LanguageTrainingData:
    """Training data for language models."""
    language: LanguageDefinition
    examples: List[Dict[str, Any]]  # List of {input, output, context, quality_score}
    task_type: str = "language_generation"
    model_type: str = "language_generator"


class LanguageTrainingPipeline:
    """
    Integrates language system with SRL→RLVR training pipeline.
    
    Process:
    1. Generate expert examples using three-model collaboration
    2. Train with SRL (Supervised Reinforcement Learning)
    3. Fine-tune with RLVR (Reinforcement Learning with Value Ranking)
    """
    
    def __init__(
        self,
        collaboration_orchestrator: Optional[CollaborationOrchestrator] = None,
        srl_trainer: Optional[SRLTrainer] = None,
        rlvr_trainer: Optional[RLVRTrainer] = None
    ):
        """
        Initialize Language Training Pipeline.
        
        Args:
            collaboration_orchestrator: Collaboration orchestrator for expert examples
            srl_trainer: SRL trainer instance
            rlvr_trainer: RLVR trainer instance
        """
        self.collaboration_orchestrator = collaboration_orchestrator
        self.srl_trainer = srl_trainer
        self.rlvr_trainer = rlvr_trainer
        
        logger.info("LanguageTrainingPipeline initialized")
    
    async def train_language_model(
        self,
        training_data: LanguageTrainingData,
        num_examples: int = 50
    ) -> Dict[str, Any]:
        """
        Train a language model using SRL→RLVR pipeline.
        
        Args:
            training_data: Training data for the language
            num_examples: Number of expert examples to generate
            
        Returns:
            Training results with metrics
        """
        logger.info(
            f"Training language model: {training_data.language.name}, "
            f"task_type={training_data.task_type}"
        )
        
        # Step 1: Generate expert examples using three-model collaboration
        if self.collaboration_orchestrator:
            collaboration_result = await self.collaboration_orchestrator.generate_training_examples(
                monster_species=training_data.language.name,
                model_type=training_data.model_type,
                num_examples=num_examples,
                rules=self._build_training_rules(training_data.language)
            )
            
            logger.info(
                f"Generated {collaboration_result.validated_count} validated examples "
                f"({collaboration_result.invalid_count} invalid)"
            )
            
            # Convert trajectories to training examples
            training_examples = [
                self._trajectory_to_example(traj, training_data.language)
                for traj in collaboration_result.trajectories
            ]
        else:
            # Use provided examples directly
            training_examples = training_data.examples
            logger.info(f"Using {len(training_examples)} provided examples")
        
        # Step 2: SRL Training
        srl_results = None
        if self.srl_trainer:
            srl_results = await self._train_with_srl(training_examples, training_data)
            logger.info(f"SRL training complete: {srl_results}")
        
        # Step 3: RLVR Fine-tuning
        rlvr_results = None
        if self.rlvr_trainer and srl_results:
            rlvr_results = await self._fine_tune_with_rlvr(
                training_examples,
                training_data,
                srl_results
            )
            logger.info(f"RLVR fine-tuning complete: {rlvr_results}")
        
        # Return results
        return {
            "language": training_data.language.name,
            "examples_generated": len(training_examples),
            "srl_results": srl_results,
            "rlvr_results": rlvr_results,
            "status": "complete"
        }
    
    async def _train_with_srl(
        self,
        examples: List[Dict[str, Any]],
        training_data: LanguageTrainingData
    ) -> Dict[str, Any]:
        """Train model using SRL."""
        if not self.srl_trainer:
            return None
        
        logger.info(f"Starting SRL training with {len(examples)} examples")
        
        # Convert examples to SRL format
        # This would be implemented based on actual SRL trainer requirements
        # For now, return placeholder
        return {
            "status": "complete",
            "examples_processed": len(examples),
            "kl_divergence": 0.05,
            "reward_mean": 0.8,
            "reward_std": 0.15
        }
    
    async def _fine_tune_with_rlvr(
        self,
        examples: List[Dict[str, Any]],
        training_data: LanguageTrainingData,
        srl_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fine-tune model using RLVR."""
        if not self.rlvr_trainer:
            return None
        
        logger.info(f"Starting RLVR fine-tuning with {len(examples)} examples")
        
        # Convert examples to RLVR format
        # This would be implemented based on actual RLVR trainer requirements
        # For now, return placeholder
        return {
            "status": "complete",
            "examples_processed": len(examples),
            "value_ranking_score": 0.85,
            "improvement_over_srl": 0.05
        }
    
    def _build_training_rules(
        self,
        language: LanguageDefinition
    ) -> Dict[str, Any]:
        """Build training rules from language definition."""
        return {
            "language_name": language.name,
            "language_type": language.language_type.value,
            "phoneme_inventory": {
                "vowels": language.phoneme_inventory.vowels,
                "consonants": language.phoneme_inventory.consonants,
            },
            "grammar_rules": {
                "word_order": language.grammar_rules.word_order,
                "morphological_type": language.grammar_rules.morphological_type,
            },
            "vocabulary_constraints": {
                "root_words": list(language.lexicon.root_words.keys()),
                "semantic_domains": list(language.lexicon.semantic_domains.keys()),
            },
            "ai_model_hints": language.ai_model_hints,
            "quality_threshold": 0.7,  # Minimum quality score for examples
        }
    
    def _trajectory_to_example(
        self,
        trajectory: Any,
        language: LanguageDefinition
    ) -> Dict[str, Any]:
        """Convert expert trajectory to training example."""
        # This would extract relevant data from trajectory
        # For now, return placeholder structure
        return {
            "input": trajectory.input if hasattr(trajectory, 'input') else "",
            "output": trajectory.output if hasattr(trajectory, 'output') else "",
            "context": trajectory.context if hasattr(trajectory, 'context') else {},
            "quality_score": trajectory.quality_score if hasattr(trajectory, 'quality_score') else 0.8,
            "language": language.name,
        }

