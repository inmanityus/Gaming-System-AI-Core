"""
The Broker's Book System

Living grimoire serving as player's interface with Dark World commerce.

From Story Teller design (Gemini 2.5 Pro):
- 4 sections: Terrors, Poisons, Accounts, Red Market
- Knowledge progression through action
- Auto-updating prices
- Can be lost/damaged
"""

__version__ = "1.0.0"

from .broker_book_system import (
    BrokerBook,
    KnowledgeTier,
    BestiaryEntry,
    DrugEntry,
    ClientEntry,
    PartsEntry,
)

__all__ = [
    "BrokerBook",
    "KnowledgeTier",
    "BestiaryEntry",
    "DrugEntry",
    "ClientEntry",
    "PartsEntry",
]

