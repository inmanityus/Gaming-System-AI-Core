from __future__ import annotations

# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Language Learner Module
=======================

Manages player language learning progression and skill levels.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


logger = logging.getLogger(__name__)


@dataclass
class LearningProgress:
    """Player's learning progress for a language."""
    language: str
    skill_level: float = 0.0  # 0.0 to 1.0
    words_known: int = 0
    phrases_known: int = 0
    grammar_understood: bool = False
    fragments_unlocked: List[str] = field(default_factory=list)
    artifacts_found: List[str] = field(default_factory=list)
    interactions_count: int = 0
    last_improvement: Optional[str] = None


@dataclass
class LearningEvent:
    """Event that contributes to language learning."""
    language: str
    event_type: str  # "artifact", "interaction", "translation", "study"
    fragment: Optional[str] = None
    artifact_id: Optional[str] = None
    interaction_id: Optional[str] = None
    quality_score: float = 1.0  # 0.0 to 1.0, how well player did


class LanguageLearner:
    """
    Manages player language learning progression.
    
    Tracks:
    - Skill levels per language
    - Words and phrases learned
    - Grammar understanding
    - Artifact discoveries
    - Interaction history
    """
    
    def __init__(self):
        """Initialize Language Learner."""
        self.progress: Dict[str, LearningProgress] = {}
        
        # Learning rates (skill points per event)
        self.learning_rates = {
            "artifact": 0.1,  # Finding artifact unlocks fragment
            "interaction": 0.02,  # Each interaction improves slightly
            "translation": 0.05,  # Successfully translating improves
            "study": 0.03,  # Studying improves understanding
        }
        
        logger.info("LanguageLearner initialized")
    
    def get_progress(self, language: str) -> LearningProgress:
        """
        Get player's learning progress for a language.
        
        Args:
            language: Language name
            
        Returns:
            LearningProgress for the language
        """
        if language not in self.progress:
            self.progress[language] = LearningProgress(language=language)
        
        return self.progress[language]
    
    def record_learning_event(self, event: LearningEvent) -> LearningProgress:
        """
        Record a learning event and update progress.
        
        Args:
            event: Learning event
            
        Returns:
            Updated LearningProgress
        """
        progress = self.get_progress(event.language)
        
        # Update based on event type
        if event.event_type == "artifact":
            if event.artifact_id and event.artifact_id not in progress.artifacts_found:
                progress.artifacts_found.append(event.artifact_id)
                progress.skill_level += self.learning_rates["artifact"] * event.quality_score
                progress.last_improvement = f"Found artifact: {event.artifact_id}"
        
        elif event.event_type == "interaction":
            progress.interactions_count += 1
            progress.skill_level += self.learning_rates["interaction"] * event.quality_score
            progress.last_improvement = "Interaction with native speaker"
        
        elif event.event_type == "translation":
            progress.skill_level += self.learning_rates["translation"] * event.quality_score
            progress.last_improvement = "Successful translation"
        
        elif event.event_type == "study":
            progress.skill_level += self.learning_rates["study"] * event.quality_score
            progress.last_improvement = "Studied language"
        
        # Unlock fragment if provided
        if event.fragment and event.fragment not in progress.fragments_unlocked:
            progress.fragments_unlocked.append(event.fragment)
            progress.skill_level += 0.05  # Bonus for fragment
        
        # Cap skill level at 1.0
        progress.skill_level = min(1.0, progress.skill_level)
        
        # Update word/phrase counts (simplified)
        if progress.skill_level >= 0.3:
            progress.words_known = int(progress.skill_level * 100)
        if progress.skill_level >= 0.6:
            progress.phrases_known = int((progress.skill_level - 0.6) * 50)
        if progress.skill_level >= 0.8:
            progress.grammar_understood = True
        
        logger.info(
            f"Learning event recorded: {event.language} - {event.event_type}, "
            f"skill_level now: {progress.skill_level:.2f}"
        )
        
        return progress
    
    def get_skill_level(self, language: str) -> float:
        """
        Get current skill level for a language.
        
        Args:
            language: Language name
            
        Returns:
            Skill level (0.0 to 1.0)
        """
        progress = self.get_progress(language)
        return progress.skill_level
    
    def can_understand(self, language: str, complexity: int = 1) -> bool:
        """
        Check if player can understand language at given complexity.
        
        Args:
            language: Language name
            complexity: Complexity level (1-5)
            
        Returns:
            True if player can understand
        """
        skill = self.get_skill_level(language)
        
        # Complexity thresholds
        thresholds = {
            1: 0.1,  # Very basic
            2: 0.3,  # Basic
            3: 0.5,  # Intermediate
            4: 0.7,  # Advanced
            5: 0.9,  # Expert
        }
        
        return skill >= thresholds.get(complexity, 1.0)
    
    def get_translation_quality(self, language: str) -> float:
        """
        Get translation quality factor based on skill level.
        
        Args:
            language: Language name
            
        Returns:
            Quality factor (0.0 to 1.0)
        """
        skill = self.get_skill_level(language)
        
        # Quality scales with skill, but has minimum baseline
        return max(0.3, skill)  # Minimum 30% quality even at skill 0
    
    def get_all_progress(self) -> Dict[str, LearningProgress]:
        """Get all language learning progress."""
        return self.progress.copy()


