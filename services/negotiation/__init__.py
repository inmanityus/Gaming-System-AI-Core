"""
Negotiation System

Haggling and dialogue-based deal-making with Dark World clients.
"""

__version__ = "1.0.0"

from .haggling_system import (
    HagglingSystem,
    NegotiationOutcome,
    ClientTemperament,
    NegotiationContext,
    NegotiationResult,
)

__all__ = [
    "HagglingSystem",
    "NegotiationOutcome",
    "ClientTemperament",
    "NegotiationContext",
    "NegotiationResult",
]

