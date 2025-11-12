"""
Language Generation Module
==========================

Provides sentence generation capabilities using both procedural and AI-based methods.
"""

from language_system.generation.sentence_generator import SentenceGenerator, SentenceRequest
from language_system.generation.ai_language_generator import (
    AILanguageGenerator,
    LanguageGenerator,
    LanguageRequest,
    LanguageGenerationResult
)
from language_system.generation.training_integration import (
    LanguageTrainingPipeline,
    LanguageTrainingData
)

__all__ = [
    "SentenceGenerator",
    "SentenceRequest",
    "AILanguageGenerator",
    "LanguageGenerator",
    "LanguageRequest",
    "LanguageGenerationResult",
    "LanguageTrainingPipeline",
    "LanguageTrainingData",
]
