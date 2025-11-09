"""
Morality System - Surgeon vs Butcher Paths
Coder: Claude Sonnet 4.5

Two moral paths with different consequences:

SURGEON PATH:
- Only kill deserving targets (criminals, abusers)
- Slower growth, limited supply
- Vigilante respect in Human World
- "Finicky" reputation in Dark

BUTCHER PATH:
- Kill anyone (hospitals, schools, civilians)
- Fast growth, fulfill any order
- Public Enemy #1 in Human World
- Best Dark reputation but universally reviled

Morality is economics and strategy, not good/evil meter.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MoralPath(str, Enum):
    """Player's moral alignment."""
    SURGEON = "surgeon"  # Selective, principled
    MIXED = "mixed"  # Some restraint
    BUTCHER = "butcher"  # Indiscriminate


class TargetType(str, Enum):
    """Types of targets."""
    DESERVING = "deserving"  # Criminals, abusers, traffickers
    NEUTRAL = "neutral"  # Average civilians
    INNOCENT = "innocent"  # Children, helping professions, victims


@dataclass
class KillRecord:
    """Record of a kill."""
    target_id: str
    target_type: TargetType
    timestamp: datetime
    justification: Optional[str] = None
    witnesses: int = 0
    collateral_damage: bool = False


@dataclass
class MoralityState:
    """Player's morality state."""
    path: MoralPath
    innocents_killed: int = 0
    deserving_killed: int = 0
    neutral_killed: int = 0
    total_kills: int = 0
    
    # Reputation effects
    human_world_notoriety: int = 0  # 0-100 (higher = more wanted)
    vigilante_respect: int = 0  # 0-100 (Surgeon path)
    dark_world_efficiency_rating: int = 50  # 0-100 (Butcher benefits)
    
    # Consequences
    surgeon_supply_penalty: float = 0.0  # Harder to find targets
    butcher_heat_level: int = 0  # Police/corp attention
    fae_amusement_level: int = 0  # Fae test Surgeon's rules


class SurgeonButcherSystem:
    """
    Morality system tracking Surgeon vs Butcher paths.
    
    Not a good/evil meter - it's strategic choice with consequences.
    """
    
    def __init__(self):
        """Initialize morality system."""
        self.state = MoralityState(path=MoralPath.MIXED)
        self.kill_history: List[KillRecord] = []
        
        logger.info("Morality system initialized (starting: Mixed)")
    
    async def record_kill(
        self,
        target_id: str,
        target_type: TargetType,
        justification: Optional[str] = None,
        witnesses: int = 0,
        collateral_damage: bool = False
    ) -> None:
        """
        Record a kill and update morality state.
        
        Args:
            target_id: Target identifier
            target_type: Deserving, neutral, or innocent
            justification: Player's justification
            witnesses: Number of witnesses
            collateral_damage: Did kill cause collateral damage
        """
        record = KillRecord(
            target_id=target_id,
            target_type=target_type,
            timestamp=datetime.now(),
            justification=justification,
            witnesses=witnesses,
            collateral_damage=collateral_damage
        )
        
        self.kill_history.append(record)
        self.state.total_kills += 1
        
        # Update counters
        if target_type == TargetType.DESERVING:
            self.state.deserving_killed += 1
        elif target_type == TargetType.INNOCENT:
            self.state.innocents_killed += 1
        else:
            self.state.neutral_killed += 1
        
        # Determine moral path
        await self._recalculate_path()
        
        # Apply consequences
        await self._apply_consequences(record)
        
        logger.info(
            f"Kill recorded: {target_type.value}, "
            f"path={self.state.path.value}, "
            f"total={self.state.total_kills}"
        )
    
    async def _recalculate_path(self) -> None:
        """Recalculate moral path based on kill history."""
        total = self.state.total_kills
        if total == 0:
            return
        
        innocents_pct = self.state.innocents_killed / total
        deserving_pct = self.state.deserving_killed / total
        
        # Determine path
        if innocents_pct >= 0.3:
            # 30%+ innocents = Butcher
            self.state.path = MoralPath.BUTCHER
        elif deserving_pct >= 0.70:
            # 70%+ deserving = Surgeon
            self.state.path = MoralPath.SURGEON
        else:
            # Mixed
            self.state.path = MoralPath.MIXED
    
    async def _apply_consequences(self, record: KillRecord) -> None:
        """Apply consequences based on kill type and path."""
        
        # Surgeon path consequences
        if self.state.path == MoralPath.SURGEON:
            # Supply penalty (harder to find deserving targets)
            self.state.surgeon_supply_penalty = min(0.5, self.state.total_kills * 0.01)
            
            # Vigilante respect (if killing deserving)
            if record.target_type == TargetType.DESERVING:
                self.state.vigilante_respect = min(100, self.state.vigilante_respect + 2)
            
            # Fae amusement (testing rules)
            if record.target_type == TargetType.INNOCENT:
                self.state.fae_amusement_level += 10  # Fae notice hypocrisy
        
        # Butcher path consequences
        elif self.state.path == MoralPath.BUTCHER:
            # Efficiency rating (Dark World values this)
            self.state.dark_world_efficiency_rating = min(100, 50 + self.state.total_kills)
            
            # Heat level (human world attention)
            if record.target_type == TargetType.INNOCENT:
                self.state.butcher_heat_level += 5
            
            # Notoriety
            self.state.human_world_notoriety = min(100, self.state.total_kills * 2)
    
    def get_path_description(self) -> str:
        """Get description of current moral path."""
        descriptions = {
            MoralPath.SURGEON: (
                "You only kill the deserving. It's slower, but you sleep... better. "
                "The Dark sees you as 'finicky,' but some humans see you as a dark hero."
            ),
            MoralPath.MIXED: (
                "You kill when needed. Pragmatic. The world is gray, and so are you. "
                "Neither hero nor monster—just a broker trying to survive."
            ),
            MoralPath.BUTCHER: (
                "Everyone is meat. You are efficient, ruthless, and wealthy. "
                "The Dark respects you. The human world hunts you. Your crew fears you."
            )
        }
        return descriptions[self.state.path]
    
    def get_consequences(self) -> Dict[str, Any]:
        """Get current consequences of moral choices."""
        return {
            'path': self.state.path.value,
            'description': self.get_path_description(),
            'kills': {
                'total': self.state.total_kills,
                'deserving': self.state.deserving_killed,
                'neutral': self.state.neutral_killed,
                'innocents': self.state.innocents_killed
            },
            'surgeon_effects': {
                'vigilante_respect': self.state.vigilante_respect,
                'supply_penalty': f"{self.state.surgeon_supply_penalty*100:.0f}%",
                'fae_testing': self.state.fae_amusement_level
            },
            'butcher_effects': {
                'dark_efficiency': self.state.dark_world_efficiency_rating,
                'human_notoriety': self.state.human_world_notoriety,
                'heat_level': self.state.butcher_heat_level
            }
        }

