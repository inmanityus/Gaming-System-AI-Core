"""
Dark World Clients System

8 client families with progression ladder.
"""

__version__ = "1.0.0"

from .dark_families_system import (
    DarkFamiliesSystem,
    ClientTier,
    ClientFamily,
    ClientFamilyProfile,
)

__all__ = [
    "DarkFamiliesSystem",
    "ClientTier",
    "ClientFamily",
    "ClientFamilyProfile",
]

