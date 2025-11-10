"""
Performance Mode Service - Dual-Mode Performance Architecture

Implements REQ-PERF-001: Dual-Mode Performance Architecture.
Manages Immersive Mode (60-120 FPS) and Competitive Mode (300+ FPS).
"""

from services.performance_mode.mode_manager import (
    PerformanceMode,
    ModeManager,
    RenderingConfig,
    ModePreset,
)

__all__ = [
    "PerformanceMode",
    "ModeManager",
    "RenderingConfig",
    "ModePreset",
]



