"""
Death System - Debt of Flesh

Death consequence system where death is a transaction.

From Story Teller design:
- Soul-Echo state (watch Corpse-Tender take your body)
- Re-bodiment at Hovel (naked)
- Veil-Fray stacking debuff
- Corpse runs or bribes for retrieval
"""

__version__ = "1.0.0"

from .debt_of_flesh import (
    DebtOfFleshSystem,
    DeathState,
    CorpseLocation,
    VeilFrayDebuff,
    FleshTithe,
)

__all__ = [
    "DebtOfFleshSystem",
    "DeathState",
    "CorpseLocation",
    "VeilFrayDebuff",
    "FleshTithe",
]

