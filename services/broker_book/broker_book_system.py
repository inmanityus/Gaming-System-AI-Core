"""
The Broker's Book System
Coder: Claude Sonnet 4.5
Awaiting Peer Review

Living grimoire that serves as player's interface with Dark World commerce.

Features (from Story Teller design):
- 4 sections: Terrors (bestiary), Poisons (drugs), Accounts (clients), Red Market (parts)
- Knowledge tiers: Whispers -> Awareness -> Familiarity -> Expertise -> Mastery
- Auto-updating prices based on world events
- Earned through action (see creature, harvest it, deal with it)
- Can be lost/damaged
- Personality in tone, margin notes from dead Brokers
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class KnowledgeTier(str, Enum):
    """Knowledge progression tiers."""
    WHISPERS = "whispers"  # Locked, vague
    AWARENESS = "awareness"  # Name, basic description
    FAMILIARITY = "familiarity"  # Functional knowledge
    EXPERTISE = "expertise"  # Advanced intel
    MASTERY = "mastery"  # Secret knowledge


@dataclass
class BestiaryEntry:
    """Entry in The Terrors section."""
    creature_id: str
    name: str
    tier: KnowledgeTier
    sketch_unlocked: bool = False
    weaknesses: List[str] = field(default_factory=list)
    habitat: Optional[str] = None
    desires: Optional[str] = None
    valuable_parts: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    dissection_count: int = 0
    
    def unlock_sketch(self) -> None:
        """Unlock charcoal sketch (see creature once)."""
        self.sketch_unlocked = True
    
    def add_observation(self, observation: str) -> None:
        """Add observation from witnessing behavior."""
        self.observations.append(observation)
    
    def add_dissection(self) -> None:
        """Record dissection (unlocks anatomy details)."""
        self.dissection_count += 1


@dataclass
class DrugEntry:
    """Entry in The Poisons section."""
    drug_id: str
    name: str
    tier: KnowledgeTier
    street_price_min: float = 0.0
    street_price_max: float = 0.0
    bulk_price: float = 0.0
    price_trend: str = "stable"  # up, down, stable
    effects_known: float = 0.0  # 0.0 to 1.0
    effects: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    combinations: Dict[str, str] = field(default_factory=dict)  # drug_id -> effect
    buyers: List[str] = field(default_factory=list)
    use_count: int = 0
    witness_od_count: int = 0
    sale_count: int = 0


@dataclass
class ClientEntry:
    """Entry in The Accounts section."""
    client_id: str
    name: str
    species: str
    tier: KnowledgeTier
    reliability_stars: int = 0  # 0-5
    payment_history: str = "Unknown"
    preferences: List[str] = field(default_factory=list)
    hates: List[str] = field(default_factory=list)
    secrets_unlocked: int = 0
    secrets_total: int = 8
    last_contact: Optional[datetime] = None
    next_expected: Optional[datetime] = None
    satisfaction_level: int = 50  # 0-100
    transaction_count: int = 0


@dataclass
class PartsEntry:
    """Entry in The Red Market section."""
    part_id: str
    name: str
    category: str  # organ, blood, tissue, bone, etc.
    current_price_min: float = 0.0
    current_price_max: float = 0.0
    demand_level: str = "medium"  # low, medium, high, critical
    supply_level: str = "medium"
    quality_factors: List[str] = field(default_factory=list)
    quality_factors_unlocked: int = 0
    buyers: List[str] = field(default_factory=list)
    price_history: List[float] = field(default_factory=list)  # Last 30 days


class BrokerBook:
    """
    The Broker's Book - Living grimoire system.
    
    Story Teller Design:
    - Connected to 'Collective Desperation' (psychic web)
    - Updates when deals happen anywhere
    - Earned knowledge through action
    - Can be lost/damaged
    """
    
    def __init__(self):
        """Initialize empty book."""
        # The four sections
        self.terrors: Dict[str, BestiaryEntry] = {}  # creature_id -> entry
        self.poisons: Dict[str, DrugEntry] = {}  # drug_id -> entry
        self.accounts: Dict[str, ClientEntry] = {}  # client_id -> entry
        self.red_market: Dict[str, PartsEntry] = {}  # part_id -> entry
        
        # Book state
        self.is_damaged: bool = False
        self.damage_level: float = 0.0  # 0.0 to 1.0
        self.corruption_level: float = 0.0  # 0.0 to 1.0 (from dirty dealings)
        
        # Margin notes from dead Brokers
        self.margin_notes: List[str] = []
        
        logger.info("The Broker's Book initialized (empty)")
    
    # ========== BESTIARY (The Terrors) ==========
    
    def witness_creature(self, creature_id: str, name: str) -> None:
        """
        Player sees creature for first time.
        
        Unlocks charcoal sketch, basic entry at Whispers tier.
        """
        if creature_id not in self.terrors:
            entry = BestiaryEntry(
                creature_id=creature_id,
                name=name,
                tier=KnowledgeTier.WHISPERS
            )
            entry.unlock_sketch()
            self.terrors[creature_id] = entry
            
            logger.info(f"New creature witnessed: {name} (Whispers)")
    
    def observe_creature_behavior(
        self,
        creature_id: str,
        observation: str
    ) -> None:
        """
        Player observes creature behavior.
        
        Advances to Awareness tier, adds observations.
        """
        entry = self.terrors.get(creature_id)
        if not entry:
            return
        
        entry.add_observation(observation)
        
        if entry.tier == KnowledgeTier.WHISPERS and len(entry.observations) >= 1:
            entry.tier = KnowledgeTier.AWARENESS
            logger.info(f"Creature advanced to Awareness: {entry.name}")
    
    def dissect_creature(self, creature_id: str, parts_found: List[str]) -> None:
        """
        Player dissects creature at hovel table.
        
        Advances to Familiarity tier, unlocks anatomy details.
        """
        entry = self.terrors.get(creature_id)
        if not entry:
            return
        
        entry.add_dissection()
        entry.valuable_parts.extend(parts_found)
        
        if entry.tier in [KnowledgeTier.WHISPERS, KnowledgeTier.AWARENESS]:
            entry.tier = KnowledgeTier.FAMILIARITY
            logger.info(f"Creature advanced to Familiarity: {entry.name}")
    
    # ========== PHARMACOPOEIA (The Poisons) ==========
    
    def discover_drug(self, drug_id: str, name: str) -> None:
        """
        Player discovers drug exists.
        
        Creates Whispers tier entry.
        """
        if drug_id not in self.poisons:
            entry = DrugEntry(
                drug_id=drug_id,
                name=name,
                tier=KnowledgeTier.WHISPERS
            )
            self.poisons[drug_id] = entry
            logger.info(f"New drug discovered: {name} (Whispers)")
    
    def use_drug(self, drug_id: str, effects_experienced: List[str]) -> None:
        """
        Player uses drug themselves.
        
        Advances tier, unlocks full effects.
        """
        entry = self.poisons.get(drug_id)
        if not entry:
            return
        
        entry.use_count += 1
        entry.effects.extend(effects_experienced)
        entry.effects_known = min(1.0, entry.use_count * 0.1)  # 10% per use
        
        if entry.tier == KnowledgeTier.WHISPERS and entry.use_count >= 1:
            entry.tier = KnowledgeTier.AWARENESS
        elif entry.tier == KnowledgeTier.AWARENESS and entry.use_count >= 5:
            entry.tier = KnowledgeTier.FAMILIARITY
        
        logger.info(f"Drug knowledge increased: {entry.name} ({entry.effects_known*100:.0f}%)")
    
    def witness_overdose(self, drug_id: str, symptoms: List[str]) -> None:
        """Player witnesses someone OD."""
        entry = self.poisons.get(drug_id)
        if not entry:
            return
        
        entry.witness_od_count += 1
        entry.side_effects.extend(symptoms)
        logger.info(f"Overdose witnessed: {entry.name}")
    
    def complete_drug_sale(self, drug_id: str, buyer_id: str) -> None:
        """Player completes drug sale."""
        entry = self.poisons.get(drug_id)
        if not entry:
            return
        
        entry.sale_count += 1
        if buyer_id not in entry.buyers:
            entry.buyers.append(buyer_id)
        
        # Advance to Expertise after 10 sales
        if entry.tier == KnowledgeTier.FAMILIARITY and entry.sale_count >= 10:
            entry.tier = KnowledgeTier.EXPERTISE
            logger.info(f"Drug advanced to Expertise: {entry.name}")
    
    # ========== CLIENT LEDGER (The Accounts) ==========
    
    def add_client(
        self,
        client_id: str,
        name: str,
        species: str
    ) -> None:
        """Add new client after first deal."""
        if client_id not in self.accounts:
            entry = ClientEntry(
                client_id=client_id,
                name=name,
                species=species,
                tier=KnowledgeTier.AWARENESS
            )
            self.accounts[client_id] = entry
            logger.info(f"New client added: {name}")
    
    def update_client_satisfaction(
        self,
        client_id: str,
        delta: int
    ) -> None:
        """Update client satisfaction after deal."""
        entry = self.accounts.get(client_id)
        if not entry:
            return
        
        entry.satisfaction_level = max(0, min(100, entry.satisfaction_level + delta))
        entry.transaction_count += 1
        entry.last_contact = datetime.now()
        
        # Advance tier based on transactions
        if entry.tier == KnowledgeTier.AWARENESS and entry.transaction_count >= 3:
            entry.tier = KnowledgeTier.FAMILIARITY
        elif entry.tier == KnowledgeTier.FAMILIARITY and entry.transaction_count >= 10:
            entry.tier = KnowledgeTier.EXPERTISE
    
    # ========== RED MARKET (Human Parts) ==========
    
    def update_market_prices(
        self,
        part_id: str,
        new_price_min: float,
        new_price_max: float,
        event_reason: Optional[str] = None
    ) -> None:
        """
        Auto-update prices based on world events.
        
        This is the 'magic' - prices update from dynamic economy.
        """
        entry = self.red_market.get(part_id)
        if not entry:
            # Create entry if doesn't exist
            entry = PartsEntry(
                part_id=part_id,
                name=part_id.replace("_", " ").title(),
                category="organ"
            )
            self.red_market[part_id] = entry
        
        # Update prices
        entry.current_price_min = new_price_min
        entry.current_price_max = new_price_max
        entry.price_history.append((new_price_min + new_price_max) / 2)
        
        # Keep last 30 entries
        if len(entry.price_history) > 30:
            entry.price_history = entry.price_history[-30:]
        
        if event_reason:
            logger.info(f"Price updated: {entry.name} -> €{new_price_min}-{new_price_max} ({event_reason})")
    
    # ========== BOOK STATE ==========
    
    def damage_book(self, damage_amount: float, damage_type: str) -> None:
        """
        Damage the book (blood, water, fire).
        
        Corrupts entries, makes some illegible.
        """
        self.is_damaged = True
        self.damage_level = min(1.0, self.damage_level + damage_amount)
        
        logger.warning(f"Book damaged: {damage_type} (level: {self.damage_level*100:.0f}%)")
    
    def repair_book(self, repair_amount: float) -> None:
        """Repair book (expensive, requires materials)."""
        self.damage_level = max(0.0, self.damage_level - repair_amount)
        
        if self.damage_level == 0.0:
            self.is_damaged = False
            logger.info("Book fully repaired")
    
    def increase_corruption(self, amount: float) -> None:
        """
        Increase corruption from dirty dealings.
        
        Affects book's tone, appearance.
        """
        self.corruption_level = min(1.0, self.corruption_level + amount)
    
    # ========== QUERY METHODS ==========
    
    def get_creature_info(self, creature_id: str) -> Optional[BestiaryEntry]:
        """Get creature entry."""
        return self.terrors.get(creature_id)
    
    def get_drug_price(self, drug_id: str) -> Optional[tuple]:
        """Get current drug price range."""
        entry = self.poisons.get(drug_id)
        if not entry or entry.tier == KnowledgeTier.WHISPERS:
            return None
        return (entry.street_price_min, entry.street_price_max)
    
    def get_client_preferences(self, client_id: str) -> Optional[ClientEntry]:
        """Get client preferences for negotiation."""
        return self.accounts.get(client_id)
    
    def get_part_price(self, part_id: str) -> Optional[tuple]:
        """Get current part price range."""
        entry = self.red_market.get(part_id)
        if not entry:
            return None
        return (entry.current_price_min, entry.current_price_max)
    
    def get_market_alerts(self) -> List[str]:
        """Get time-sensitive market alerts."""
        alerts = []
        
        # Check for significant price changes
        for entry in self.red_market.values():
            if len(entry.price_history) >= 2:
                recent = entry.price_history[-1]
                previous = entry.price_history[-2]
                change_pct = ((recent - previous) / previous) * 100 if previous > 0 else 0
                
                if abs(change_pct) >= 20:
                    direction = "↑↑" if change_pct > 0 else "↓↓"
                    alerts.append(f"{direction} {entry.name} ({change_pct:+.0f}%)")
        
        return alerts
    
    def save_to_file(self, filepath: str) -> None:
        """Save book state to file."""
        data = {
            'terrors': {k: v.__dict__ for k, v in self.terrors.items()},
            'poisons': {k: v.__dict__ for k, v in self.poisons.items()},
            'accounts': {k: v.__dict__ for k, v in self.accounts.items()},
            'red_market': {k: v.__dict__ for k, v in self.red_market.items()},
            'is_damaged': self.is_damaged,
            'damage_level': self.damage_level,
            'corruption_level': self.corruption_level
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Book saved to {filepath}")
    
    def load_from_file(self, filepath: str) -> None:
        """Load book state from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct entries (simplified - would need proper deserialization)
        self.is_damaged = data.get('is_damaged', False)
        self.damage_level = data.get('damage_level', 0.0)
        self.corruption_level = data.get('corruption_level', 0.0)
        
        logger.info(f"Book loaded from {filepath}")

