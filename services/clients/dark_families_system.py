"""
Dark Families System - 8 Client Families
Coder: Claude Sonnet 4.5

8 tiers of Dark World clients from Story Teller design:
LOW: Carrion Kin, Chatter-Swarm
MID: Stitch-Guild, Moon-Clans, Vampiric Houses
HIGH: Obsidian Synod, Silent Court (Fae), Leviathan Conclave

Each family has: needs, payment type, risk level, advancement path.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ClientTier(str, Enum):
    """Client tier levels."""
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class ClientFamily(str, Enum):
    """8 Dark World client families."""
    CARRION_KIN = "carrion_kin"
    CHATTER_SWARM = "chatter_swarm"
    STITCH_GUILD = "stitch_guild"
    MOON_CLANS = "moon_clans"
    VAMPIRIC_HOUSES = "vampiric_houses"
    OBSIDIAN_SYNOD = "obsidian_synod"
    SILENT_COURT = "silent_court"
    LEVIATHAN_CONCLAVE = "leviathan_conclave"


@dataclass
class ClientFamilyProfile:
    """Complete profile for client family."""
    family: ClientFamily
    tier: ClientTier
    full_name: str
    description: str
    what_they_buy: List[str]
    payment_type: str  # Drug they pay with
    risk_description: str
    advancement_requirement: str  # How to access next tier
    territory: str
    communication_style: str


class DarkFamiliesSystem:
    """
    8 Dark World client families system.
    
    Player progression: LOW -> MID -> HIGH
    Each family has specific needs, risks, rewards.
    """
    
    def __init__(self):
        """Initialize client families."""
        self.families = self._initialize_families()
        
        # Player relationships (family -> reputation 0-100)
        self.player_relationships: Dict[ClientFamily, int] = {
            family: 0 for family in ClientFamily
        }
        
        # Unlock status (family -> unlocked)
        self.unlocked_families: Dict[ClientFamily, bool] = {
            ClientFamily.CARRION_KIN: True,  # Start unlocked
            ClientFamily.CHATTER_SWARM: True,  # Start unlocked
        }
        
        logger.info("Dark families system initialized (8 families)")
    
    def _initialize_families(self) -> Dict[ClientFamily, ClientFamilyProfile]:
        """Define all 8 client families."""
        return {
            ClientFamily.CARRION_KIN: ClientFamilyProfile(
                family=ClientFamily.CARRION_KIN,
                tier=ClientTier.LOW,
                full_name="The Carrion Kin",
                description="Ghouls & scavengers, slum-dwellers",
                what_they_buy=["Bulk flesh", "Broken bones", "Coagulated blood", "Any quality"],
                payment_type="Grave-Dust",
                risk_description="Might eat you if hungry",
                advancement_requirement="Complete 10 bulk orders",
                territory="Dark World slums",
                communication_style="Guttural, aggressive, simple"
            ),
            ClientFamily.CHATTER_SWARM: ClientFamilyProfile(
                family=ClientFamily.CHATTER_SWARM,
                tier=ClientTier.LOW,
                full_name="The Chatter-Swarm",
                description="Insectoid hives, stolen speech",
                what_they_buy=["Eyes", "Tongues", "Vocal cords"],
                payment_type="Hive-Nectar",
                risk_description="Hive-mind can overwhelm",
                advancement_requirement="Supply 50 sensory organs",
                territory="Underground warrens",
                communication_style="Clicks + stolen whispers"
            ),
            ClientFamily.STITCH_GUILD: ClientFamilyProfile(
                family=ClientFamily.STITCH_GUILD,
                tier=ClientTier.MID,
                full_name="The Stitch-Guild",
                description="Flesh golems, necro-artisans",
                what_they_buy=["Pristine skin", "Long bones", "Complete nervous systems"],
                payment_type="Still-Blood",
                risk_description="Guild politics, rival artisans",
                advancement_requirement="Deliver 5 pristine quality parts",
                territory="Workshop district",
                communication_style="Meticulous, demanding, artistic"
            ),
            ClientFamily.MOON_CLANS: ClientFamilyProfile(
                family=ClientFamily.MOON_CLANS,
                tier=ClientTier.MID,
                full_name="The Moon-Clans",
                description="Were-beasts, shamanistic",
                what_they_buy=["Brave hearts", "Drinker livers", "Runner lungs", "Ritual-specific"],
                payment_type="Moon-Wine",
                risk_description="Pack mentality, territorial",
                advancement_requirement="Complete 3 ritual orders perfectly",
                territory="Forest edges, abandoned industrial",
                communication_style="Honor-bound, pack hierarchy"
            ),
            ClientFamily.VAMPIRIC_HOUSES: ClientFamilyProfile(
                family=ClientFamily.VAMPIRIC_HOUSES,
                tier=ClientTier.MID,
                full_name="The Vampiric Houses",
                description="Blood connoisseurs, aristocrats",
                what_they_buy=["Blood by type/purity", "Lifestyle matters (CEO vs athlete)"],
                payment_type="Vitae",
                risk_description="House politics, social hierarchy",
                advancement_requirement="Supply rare blood vintage (O-neg athlete, or genius scientist)",
                territory="Gothic estates",
                communication_style="Formal, hierarchical, refined"
            ),
            ClientFamily.OBSIDIAN_SYNOD: ClientFamilyProfile(
                family=ClientFamily.OBSIDIAN_SYNOD,
                tier=ClientTier.HIGH,
                full_name="The Obsidian Synod",
                description="Ancient golem-minds, neural network",
                what_they_buy=["Genius brains", "Spinal columns", "Neural maps"],
                payment_type="Logic-Spore",
                risk_description="Don't value your life, only utility",
                advancement_requirement="Deliver brain of verified genius (IQ 140+, doctorate, or master hacker)",
                territory="Obsidian towers",
                communication_style="Cold, logical, precise"
            ),
            ClientFamily.SILENT_COURT: ClientFamilyProfile(
                family=ClientFamily.SILENT_COURT,
                tier=ClientTier.HIGH,
                full_name="The Silent Court (Fae)",
                description="Fae nobility, concept traders",
                what_they_buy=["Concepts not parts", "Child's laughter", "Hero's dying breath", "Traitor's guilt"],
                payment_type="Enchantments",
                risk_description="Fae wordplay, binding promises, eternal debts",
                advancement_requirement="Complete impossible Fae bargain without being tricked",
                territory="Between-spaces, thin Veil locations",
                communication_style="Riddling, never lie but always mislead"
            ),
            ClientFamily.LEVIATHAN_CONCLAVE: ClientFamilyProfile(
                family=ClientFamily.LEVIATHAN_CONCLAVE,
                tier=ClientTier.HIGH,
                full_name="The Leviathan Conclave",
                description="Abyssal entities, soul consumers",
                what_they_buy=["Souls (live delivery)", "The pure, corrupt, or powerful"],
                payment_type="Aether",
                risk_description="Empire-level danger, might unleash horror",
                advancement_requirement="Deliver first live soul without dying",
                territory="Abyssal rifts",
                communication_style="Incomprehensible, terrifying, alien"
            )
        }
    
    def get_family_profile(self, family: ClientFamily) -> ClientFamilyProfile:
        """Get complete family profile."""
        return self.families[family]
    
    def is_family_unlocked(self, family: ClientFamily) -> bool:
        """Check if player has access to family."""
        return self.unlocked_families.get(family, False)
    
    def unlock_family(self, family: ClientFamily) -> None:
        """Unlock family (met advancement requirement)."""
        if not self.unlocked_families.get(family, False):
            self.unlocked_families[family] = True
            logger.info(f"✅ Family unlocked: {self.families[family].full_name}")
    
    def update_reputation(
        self,
        family: ClientFamily,
        delta: int
    ) -> int:
        """Update reputation with family."""
        current = self.player_relationships.get(family, 0)
        new_rep = max(0, min(100, current + delta))
        self.player_relationships[family] = new_rep
        
        logger.info(f"Reputation with {family.value}: {current} -> {new_rep} ({delta:+d})")
        return new_rep
    
    def get_unlocked_families(self) -> List[ClientFamily]:
        """Get list of unlocked families."""
        return [f for f, unlocked in self.unlocked_families.items() if unlocked]

