"""
Collaboration Orchestrator
===========================

Orchestrates the three-model collaboration system to generate expert trajectories.

Coordinates:
- Lore Retriever (Model A)
- Teacher Planner (Model B)
- Verifier (Model C)
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .lore_retriever import LoreRetriever, LoreContext
from .teacher_planner import TeacherPlanner, ExpertTrajectory
from .verifier import Verifier, VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class CollaborationResult:
    """Result of three-model collaboration."""
    trajectories: List[ExpertTrajectory]
    validated_count: int
    invalid_count: int
    metadata: Dict[str, Any]


class CollaborationOrchestrator:
    """
    Orchestrates three-model collaboration to generate validated expert trajectories.
    
    Process:
    1. Lore Retriever gathers context
    2. Teacher Planner generates trajectories
    3. Verifier validates trajectories
    4. Returns validated trajectories for training
    """
    
    def __init__(
        self,
        lore_retriever: LoreRetriever,
        teacher_planner: TeacherPlanner,
        verifier: Verifier
    ):
        """
        Initialize Collaboration Orchestrator.
        
        Args:
            lore_retriever: Lore Retriever instance
            teacher_planner: Teacher Planner instance
            verifier: Verifier instance
        """
        self.lore_retriever = lore_retriever
        self.teacher_planner = teacher_planner
        self.verifier = verifier
        logger.info("CollaborationOrchestrator initialized")
    
    def generate_training_examples(
        self,
        monster_species: str,
        model_type: str,
        num_examples: int = 10,
        rules: Optional[Dict[str, Any]] = None
    ) -> CollaborationResult:
        """
        Generate validated training examples via three-model collaboration.
        
        Args:
            monster_species: Species identifier
            model_type: Type of model being trained
            num_examples: Number of examples to generate
            rules: Dynamic rules to enforce (optional)
        
        Returns:
            CollaborationResult: Validated trajectories and metadata
        """
        logger.info(f"Generating {num_examples} training examples for {monster_species} ({model_type})")
        
        # Step 1: Retrieve lore context
        lore_context = self.lore_retriever.retrieve_lore(monster_species, model_type)
        
        # Step 2: Generate expert trajectories
        trajectories = self.teacher_planner.generate_batch(
            lore_contexts=[lore_context],
            model_type=model_type,
            num_examples=num_examples
        )
        
        # Step 3: Verify trajectories
        if rules is None:
            rules = {}  # TODO: Fetch from rules engine
        
        validation_results = self.verifier.verify_batch(
            trajectories=trajectories,
            model_type=model_type,
            rules=rules
        )
        
        # Filter to only valid trajectories
        valid_trajectories = []
        invalid_count = 0
        
        for trajectory, result in validation_results:
            if result.is_valid:
                valid_trajectories.append(trajectory)
            else:
                invalid_count += 1
                logger.warning(f"Invalid trajectory: {result.issues}")
        
        # If we need more valid examples, regenerate
        while len(valid_trajectories) < num_examples and invalid_count < num_examples * 3:
            logger.info(f"Regenerating examples (have {len(valid_trajectories)}, need {num_examples})")
            additional_trajectories = self.teacher_planner.generate_batch(
                lore_contexts=[lore_context],
                model_type=model_type,
                num_examples=num_examples - len(valid_trajectories)
            )
            
            additional_results = self.verifier.verify_batch(
                trajectories=additional_trajectories,
                model_type=model_type,
                rules=rules
            )
            
            for trajectory, result in additional_results:
                if result.is_valid:
                    valid_trajectories.append(trajectory)
                else:
                    invalid_count += 1
        
        result = CollaborationResult(
            trajectories=valid_trajectories[:num_examples],
            validated_count=len(valid_trajectories),
            invalid_count=invalid_count,
            metadata={
                "monster_species": monster_species,
                "model_type": model_type,
                "lore_context_used": lore_context is not None
            }
        )
        
        logger.info(f"Generated {result.validated_count} valid trajectories")
        return result

