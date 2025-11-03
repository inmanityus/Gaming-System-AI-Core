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
import asyncio
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
    
    async def generate_training_examples(
        self,
        monster_species: str,
        model_type: str,
        num_examples: int = 10,
        rules: Optional[Dict[str, Any]] = None,
        max_regeneration_attempts: int = 3
    ) -> CollaborationResult:
        """
        Generate validated training examples via three-model collaboration.
        
        Args:
            monster_species: Species identifier
            model_type: Type of model being trained
            num_examples: Number of examples to generate
            rules: Dynamic rules to enforce (optional, fetched if None)
            max_regeneration_attempts: Maximum times to regenerate invalid trajectories
        
        Returns:
            CollaborationResult: Validated trajectories and metadata
        """
        logger.info(f"Generating {num_examples} training examples for {monster_species} ({model_type})")
        
        # Step 1: Retrieve lore context
        lore_context = await self.lore_retriever.retrieve_lore(monster_species, model_type)
        
        # Step 2: Generate expert trajectories
        trajectories = await self.teacher_planner.generate_batch(
            lore_contexts=[lore_context] if lore_context else [],
            model_type=model_type,
            num_examples=num_examples
        )
        
        # Step 3: Verify trajectories
        validation_results = await self.verifier.verify_batch(
            trajectories=trajectories,
            model_type=model_type,
            rules=rules,
            monster_species=monster_species
        )
        
        # Filter to only valid trajectories
        valid_trajectories = []
        invalid_count = 0
        
        for trajectory, result in validation_results:
            if result.is_valid:
                valid_trajectories.append(trajectory)
            else:
                invalid_count += 1
                logger.warning(f"Invalid trajectory (score={result.score:.2f}): {len(result.issues)} issues")
        
        # If we need more valid examples, regenerate with feedback
        regeneration_attempt = 0
        while len(valid_trajectories) < num_examples and regeneration_attempt < max_regeneration_attempts:
            needed = num_examples - len(valid_trajectories)
            logger.info(
                f"Regenerating {needed} examples "
                f"(have {len(valid_trajectories)}, need {num_examples}, attempt {regeneration_attempt + 1})"
            )
            
            # Generate additional trajectories
            additional_trajectories = await self.teacher_planner.generate_batch(
                lore_contexts=[lore_context] if lore_context else [],
                model_type=model_type,
                num_examples=needed * 2  # Generate extra to account for invalid ones
            )
            
            # Verify additional trajectories
            additional_results = await self.verifier.verify_batch(
                trajectories=additional_trajectories,
                model_type=model_type,
                rules=rules,
                monster_species=monster_species
            )
            
            # Add valid ones
            for trajectory, result in additional_results:
                if result.is_valid and len(valid_trajectories) < num_examples:
                    valid_trajectories.append(trajectory)
                else:
                    invalid_count += 1
            
            regeneration_attempt += 1
        
        # Final result
        result = CollaborationResult(
            trajectories=valid_trajectories[:num_examples],
            validated_count=len(valid_trajectories),
            invalid_count=invalid_count,
            metadata={
                "monster_species": monster_species,
                "model_type": model_type,
                "lore_context_used": lore_context is not None,
                "regeneration_attempts": regeneration_attempt,
                "lore_entries": len(lore_context.related_lore) if lore_context else 0,
                "rules_count": len(lore_context.game_rules) if lore_context and lore_context.game_rules else 0
            }
        )
        
        logger.info(
            f"Generated {result.validated_count}/{num_examples} valid trajectories "
            f"(invalid: {result.invalid_count})"
        )
        return result
    
    async def close(self) -> None:
        """Close all component connections."""
        logger.info("Closing collaboration orchestrator components")
        await asyncio.gather(
            self.lore_retriever.close(),
            self.verifier.close(),
            return_exceptions=True
        )
        logger.info("All components closed")

