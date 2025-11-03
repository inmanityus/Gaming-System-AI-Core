"""
Base Trainer
============

Base class for all model-specific trainers.
"""

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseModelTrainer(ABC):
    """
    Base class for model-specific trainers.
    
    All model trainers inherit from this class and implement:
    - SRL training logic specific to model type
    - RLVR fine-tuning logic specific to model type
    - Model-specific evaluation metrics
    """
    
    def __init__(
        self,
        model_type: str,
        base_model_name: str,
        srl_trainer,
        rlvr_trainer,
        collaboration_orchestrator
    ):
        """
        Initialize base trainer.
        
        Args:
            model_type: Type of model (e.g., "personality", "facial")
            base_model_name: Base model name (e.g., "qwen-7b-instruct")
            srl_trainer: SRL trainer instance
            rlvr_trainer: RLVR trainer instance
            collaboration_orchestrator: Three-model collaboration orchestrator
        """
        self.model_type = model_type
        self.base_model_name = base_model_name
        self.srl_trainer = srl_trainer
        self.rlvr_trainer = rlvr_trainer
        self.collaboration_orchestrator = collaboration_orchestrator
        logger.info(f"{self.__class__.__name__} initialized for {model_type}")
    
    @abstractmethod
    def train_srl(
        self,
        monster_species: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """
        Train model using SRL approach.
        
        Args:
            monster_species: Species identifier
            num_examples: Number of training examples
        
        Returns:
            Training metrics and results
        """
        pass
    
    @abstractmethod
    def train_rlvr(
        self,
        srl_model_path: str,
        num_examples: int = 10
    ) -> Dict[str, Any]:
        """
        Fine-tune model using RLVR approach.
        
        Args:
            srl_model_path: Path to SRL-trained model
            num_examples: Number of training examples
        
        Returns:
            Fine-tuning metrics and results
        """
        pass
    
    @abstractmethod
    def evaluate(
        self,
        model_path: str,
        test_examples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            model_path: Path to trained model
            test_examples: Test examples
        
        Returns:
            Evaluation metrics
        """
        pass

