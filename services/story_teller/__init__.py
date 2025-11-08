"""
Story Teller Service - AI-powered narrative generation and management.

This service handles:
- Story node creation and management
- AI-powered narrative generation
- Player choice processing
- Dynamic story branching
- Real-time story updates
- Feature awareness (NEW)
- Cross-world consistency (NEW)
"""

from story_manager import StoryManager
from narrative_generator import NarrativeGenerator
from choice_processor import ChoiceProcessor
from story_branching import StoryBranching
from feature_awareness import FeatureAwareness
from cross_world_consistency import CrossWorldConsistency, AssetTemplate

__all__ = [
    "StoryManager",
    "NarrativeGenerator", 
    "ChoiceProcessor",
    "StoryBranching",
    "FeatureAwareness",
    "CrossWorldConsistency",
    "AssetTemplate",
]
