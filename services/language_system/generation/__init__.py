"""
Language Generation Module
==========================

Provides sentence generation capabilities using both procedural and AI-based methods.
"""

from .sentence_generator import SentenceGenerator, SentenceRequest
from .ai_language_generator import (
    AILanguageGenerator,
    LanguageGenerator,
    LanguageRequest,
    LanguageGenerationResult
)
from .training_integration import (
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
