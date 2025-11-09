"""
Debt of Flesh - Death Consequence System
Coder: Claude Sonnet 4.5
Awaiting Peer Review

From Story Teller design (Gemini 2.5 Pro):
- Soul-Echo on death (disembodied, watch Corpse-Tender take your body)
- Re-bodiment at Hovel (naked, no gear)
- Veil-Fray stacking debuff (-10%, -25%, etc.)
- Corpse Run OR Bribe with Flesh Tithe
- Gear remains at death location

Features:
- Death tracking
- Debuff management
- Corpse location tracking
- Bribe system
- Retrieval mechanics
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DeathState(str, Enum):
    """Player death states."""
    ALIVE = "alive"
    SOUL_ECHO = "soul_echo"
    RE_BODYING = "re_bodying"
    CORPSE_RUN = "corpse_run"


@dataclass
class CorpseLocation:
    """Player's corpse with gear."""
    corpse_id: str
    death_location: Tuple[float, float, float]  # x, y, z
    world: str  # "human" or "dark"
    death_time: datetime
    gear_items: List[str]
    killed_by: Optional[str] = None  # Creature/NPC that killed player
    corpse_tender_present: bool = True
    retrieved: bool = False


@dataclass
class VeilFrayDebuff:
    """Stacking debuff from repeated deaths."""
    level: int = 0
    health_penalty: float = 0.0
    stamina_penalty: float = 0.0
    active: bool = False
    
    def add_stack(self) -> None:
        """Add death stack."""
        self.level += 1
        self.active = True
        
        # Increasing penalty per stack
        if self.level == 1:
            self.health_penalty = 0.10  # -10%
            self.stamina_penalty = 0.10
        elif self.level == 2:
            self.health_penalty = 0.25  # -25%
            self.stamina_penalty = 0.25
        elif self.level >= 3:
            self.health_penalty = 0.40  # -40% (brutal)
            self.stamina_penalty = 0.40
        
        logger.warning(f"Veil-Fray level {self.level}: -{self.health_penalty*100:.0f}% max stats")
    
    def clear(self) -> None:
        """Clear debuff (successful corpse retrieval or major deal)."""
        self.level = 0
        self.health_penalty = 0.0
        self.stamina_penalty = 0.0
        self.active = False
        logger.info("Veil-Fray cleared")


@dataclass
class FleshTithe:
    """Bribe payment to Corpse-Tender."""
    item_id: str
    item_name: str
    value: int  # How much Corpse-Tender values it
    item_type: str  # "organ", "drug", "veil_component"


class DebtOfFleshSystem:
    """
    Death consequence system for The Body Broker.
    
    Story Teller Design:
    - Death is a transaction, not a reset
    - Corpse-Tender takes your body + gear
    - Must retrieve or bribe
    - Stacking penalties for repeated failure
    """
    
    def __init__(self):
        """Initialize death system."""
        self.current_state: DeathState = DeathState.ALIVE
        self.veil_fray: VeilFrayDebuff = VeilFrayDebuff()
        self.corpses: Dict[str, CorpseLocation] = {}  # corpse_id -> location
        self.death_count: int = 0
        self.retrieval_count: int = 0
        self.bribe_count: int = 0
        
        # Player's home base
        self.hovel_location: Optional[Tuple[float, float, float]] = None
        
        logger.info("Debt of Flesh system initialized")
    
    def set_hovel_location(self, location: Tuple[float, float, float]) -> None:
        """Set player's hovel (respawn point)."""
        self.hovel_location = location
        logger.info(f"Hovel location set: {location}")
    
    async def trigger_death(
        self,
        death_location: Tuple[float, float, float],
        world: str,
        gear_items: List[str],
        killed_by: Optional[str] = None
    ) -> str:
        """
        Trigger death sequence.
        
        Returns:
            corpse_id for tracking
        """
        self.death_count += 1
        self.current_state = DeathState.SOUL_ECHO
        
        # Create corpse
        corpse_id = f"corpse_{self.death_count}_{int(datetime.now().timestamp())}"
        corpse = CorpseLocation(
            corpse_id=corpse_id,
            death_location=death_location,
            world=world,
            death_time=datetime.now(),
            gear_items=gear_items,
            killed_by=killed_by,
            corpse_tender_present=True
        )
        
        self.corpses[corpse_id] = corpse
        
        logger.warning(
            f"Player death #{self.death_count}: {world} world at {death_location}, "
            f"{len(gear_items)} items lost"
        )
        
        # Add Veil-Fray stack
        self.veil_fray.add_stack()
        
        return corpse_id
    
    async def respawn_at_hovel(self) -> None:
        """
        Respawn player at hovel.
        
        Player is naked, has Veil-Fray debuff.
        """
        if not self.hovel_location:
            raise RuntimeError("Hovel location not set")
        
        self.current_state = DeathState.ALIVE
        
        logger.info(
            f"Respawned at hovel (naked): "
            f"Veil-Fray level {self.veil_fray.level} active"
        )
    
    async def attempt_corpse_retrieval(
        self,
        corpse_id: str,
        success: bool
    ) -> bool:
        """
        Player attempts naked run to retrieve corpse.
        
        Args:
            corpse_id: Which corpse
            success: Whether retrieval succeeded
        
        Returns:
            True if gear recovered
        """
        corpse = self.corpses.get(corpse_id)
        if not corpse:
            return False
        
        if success:
            corpse.retrieved = True
            self.retrieval_count += 1
            self.veil_fray.clear()  # Clear debuff on successful retrieval
            
            logger.info(f"✅ Corpse retrieved: {len(corpse.gear_items)} items recovered")
            return True
        else:
            logger.warning(f"❌ Retrieval failed for {corpse_id}")
            return False
    
    async def bribe_corpse_tender(
        self,
        corpse_id: str,
        tithe: FleshTithe
    ) -> bool:
        """
        Bribe Corpse-Tender with Flesh Tithe.
        
        Pacifies area, allows safe retrieval.
        
        Args:
            corpse_id: Which corpse
            tithe: What you're offering
        
        Returns:
            True if bribe accepted
        """
        corpse = self.corpses.get(corpse_id)
        if not corpse:
            return False
        
        # Determine if tithe is sufficient
        min_value = 10  # Base requirement
        
        if tithe.value >= min_value:
            # Bribe accepted
            corpse.corpse_tender_present = False
            self.bribe_count += 1
            
            logger.info(
                f"✅ Corpse-Tender bribed with {tithe.item_name} "
                f"(value: {tithe.value}), area pacified"
            )
            return True
        else:
            logger.warning(f"❌ Tithe insufficient: {tithe.item_name} (need {min_value}+)")
            return False
    
    async def complete_major_deal(self) -> None:
        """
        Complete major deal.
        
        Clears Veil-Fray debuff as reward.
        """
        self.veil_fray.clear()
        logger.info("Major deal complete: Veil-Fray cleared")
    
    async def get_active_corpses(self) -> List[CorpseLocation]:
        """Get list of unretrieved corpses."""
        return [c for c in self.corpses.values() if not c.retrieved]
    
    async def get_death_stats(self) -> Dict[str, Any]:
        """Get death statistics."""
        active_corpses = await self.get_active_corpses()
        
        return {
            'total_deaths': self.death_count,
            'successful_retrievals': self.retrieval_count,
            'bribes_paid': self.bribe_count,
            'active_corpses': len(active_corpses),
            'veil_fray_level': self.veil_fray.level,
            'veil_fray_active': self.veil_fray.active,
            'health_penalty': self.veil_fray.health_penalty,
            'stamina_penalty': self.veil_fray.stamina_penalty
        }

