from __future__ import annotations

"""
Translation & Interpretation Module
===================================

Provides translation, interpretation, and language learning capabilities.
"""

from services.language_system.translation.translator import Translator, TranslationRequest, TranslationResult
from services.language_system.translation.interpreter import Interpreter, InterpretationRequest, InterpretationResult
from services.language_system.translation.language_learner import LanguageLearner, LearningProgress, LearningEvent

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


