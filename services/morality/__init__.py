"""
Morality System

Surgeon vs Butcher path tracking with strategic consequences.
"""

__version__ = "1.0.0"

from .surgeon_butcher_system import (
    SurgeonButcherSystem,
    MoralPath,
    TargetType,
    KillRecord,
    MoralityState,
)

__all__ = [
    "SurgeonButcherSystem",
    "MoralPath",
    "TargetType",
    "KillRecord",
    "MoralityState",
]

