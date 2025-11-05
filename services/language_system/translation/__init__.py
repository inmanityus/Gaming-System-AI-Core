"""
Translation & Interpretation Module
===================================

Provides translation, interpretation, and language learning capabilities.
"""

from .translator import Translator, TranslationRequest, TranslationResult
from .interpreter import Interpreter, InterpretationRequest, InterpretationResult
from .language_learner import LanguageLearner, LearningProgress, LearningEvent

__all__ = [
    "Translator",
    "TranslationRequest",
    "TranslationResult",
    "Interpreter",
    "InterpretationRequest",
    "InterpretationResult",
    "LanguageLearner",
    "LearningProgress",
    "LearningEvent",
]

