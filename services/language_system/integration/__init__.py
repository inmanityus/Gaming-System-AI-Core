"""
Integration Module
==================

Provides integration with game engine, audio systems, and dialogue systems.
"""

from .tts_integration import TTSIntegration, TTSRequest, TTSResult

__all__ = [
    "TTSIntegration",
    "TTSRequest",
    "TTSResult",
]

