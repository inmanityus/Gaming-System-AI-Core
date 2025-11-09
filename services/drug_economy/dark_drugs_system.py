"""
Dark Drugs Economy System
Coder: Claude Sonnet 4.5

8 Dark World drug types from client families:
1. Grave-Dust (Carrion Kin) - Strength + pain resistance, paranoia
2. Hive-Nectar (Chatter-Swarm) - Telepathy with crew
3. Still-Blood (Stitch-Guild) - Regeneration
4. Moon-Wine (Moon-Clans) - Speed + senses, primal fury risk
5. Vitae (Vampires) - Hypnotic charm + influence
6. Logic-Spore (Obsidian Synod) - See data-streams, predict movements
7. Enchantments (Fae) - Reality-bending perks (ironic twists)
8. Aether (Leviathan) - Real spellcasting fuel

Effects, side effects, mixing, empire building.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class DrugType(str, Enum):
    """8 Dark World drug types."""
    GRAVE_DUST = "grave_dust"
    HIVE_NECTAR = "hive_nectar"
    STILL_BLOOD = "still_blood"
    MOON_WINE = "moon_wine"
    VITAE = "vitae"
    LOGIC_SPORE = "logic_spore"
    ENCHANTMENT = "enchantment"
    AETHER = "aether"


@dataclass
class DrugEffect:
    """Single drug effect."""
    effect_name: str
    magnitude: float  # 0.0 to 2.0
    duration_minutes: float
    positive: bool  # Benefit or drawback


@dataclass
class DarkDrug:
    """Dark World drug instance."""
    drug_id: str
    drug_type: DrugType
    quality: float  # 0.0 to 1.0
    quantity: float  # Units
    obtained_from: str  # Client family name
    primary_effects: List[DrugEffect] = field(default_factory=list)
    side_effects: List[DrugEffect] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    street_value: float = 0.0
    obtained_at: datetime = field(default_factory=datetime.now)


class DarkDrugsSystem:
    """
    Drug economy system for The Body Broker.
    
    Drugs are payment from Dark clients, used to build Human empire.
    """
    
    def __init__(self):
        """Initialize drug system."""
        # Define drug effects per type
        self.drug_definitions = self._initialize_drug_definitions()
        logger.info("Dark drugs system initialized (8 drug types)")
    
    def _initialize_drug_definitions(self) -> Dict[DrugType, Dict]:
        """Define all 8 Dark drug types."""
        return {
            DrugType.GRAVE_DUST: {
                'tier': 'low',
                'from': 'Carrion Kin (Ghouls)',
                'primary_effects': [
                    DrugEffect("strength_boost", 1.5, 30.0, True),
                    DrugEffect("pain_resistance", 1.3, 30.0, True)
                ],
                'side_effects': [
                    DrugEffect("aggressive_paranoia", 1.0, 60.0, False)
                ],
                'uses': ['Recruit street thugs', 'Basic muscle'],
                'street_value': 50.0
            },
            DrugType.HIVE_NECTAR: {
                'tier': 'low-mid',
                'from': 'Chatter-Swarm (Insects)',
                'primary_effects': [
                    DrugEffect("telepathy_short_range", 1.0, 60.0, True)
                ],
                'side_effects': [
                    DrugEffect("sensory_overload", 0.8, 60.0, False)
                ],
                'uses': ['Crew coordination', 'Gang communication'],
                'street_value': 200.0
            },
            DrugType.STILL_BLOOD: {
                'tier': 'mid',
                'from': 'Stitch-Guild (Flesh Golems)',
                'primary_effects': [
                    DrugEffect("regeneration", 2.0, 120.0, True)
                ],
                'side_effects': [
                    DrugEffect("necrotic_tissue_risk", 0.5, 240.0, False)
                ],
                'uses': ['Heal enforcers', 'Reduce downtime'],
                'street_value': 1000.0
            },
            DrugType.MOON_WINE: {
                'tier': 'mid',
                'from': 'Moon-Clans (Were-beasts)',
                'primary_effects': [
                    DrugEffect("inhuman_speed", 2.0, 45.0, True),
                    DrugEffect("heightened_senses", 1.8, 45.0, True)
                ],
                'side_effects': [
                    DrugEffect("primal_fury_risk", 1.5, 45.0, False)
                ],
                'uses': ['Berserker shock troops', 'High-risk assassinations'],
                'street_value': 1500.0
            },
            DrugType.VITAE: {
                'tier': 'mid-high',
                'from': 'Vampiric Houses',
                'primary_effects': [
                    DrugEffect("hypnotic_charm", 1.8, 180.0, True),
                    DrugEffect("social_influence", 1.6, 180.0, True)
                ],
                'side_effects': [
                    DrugEffect("light_sensitivity", 0.7, 240.0, False)
                ],
                'uses': ['Charm executives', 'Infiltrate high society', 'Manipulate politicians'],
                'street_value': 5000.0
            },
            DrugType.LOGIC_SPORE: {
                'tier': 'high',
                'from': 'Obsidian Synod (Golem-Minds)',
                'primary_effects': [
                    DrugEffect("see_datastreams", 2.0, 120.0, True),
                    DrugEffect("predict_movements", 1.9, 120.0, True),
                    DrugEffect("impossible_calculations", 2.0, 120.0, True)
                ],
                'side_effects': [
                    DrugEffect("reality_dissociation", 1.2, 180.0, False)
                ],
                'uses': ['Predict raids', 'Hack systems', 'Strategic advantage'],
                'street_value': 10000.0
            },
            DrugType.ENCHANTMENT: {
                'tier': 'high',
                'from': 'Silent Court (Fae)',
                'primary_effects': [
                    DrugEffect("reality_bending", 2.0, 0.0, True)  # Permanent perk
                ],
                'side_effects': [
                    DrugEffect("ironic_twist", 2.0, 0.0, False)  # Always has cost
                ],
                'uses': ['Unique abilities', 'Game-changing perks'],
                'street_value': 50000.0  # One-time
            },
            DrugType.AETHER: {
                'tier': 'top',
                'from': 'Leviathan Conclave (Abyssal)',
                'primary_effects': [
                    DrugEffect("true_spellcasting", 2.0, 0.0, True)  # Fuel, not duration
                ],
                'side_effects': [
                    DrugEffect("world_rejection_risk", 2.0, 0.0, False)  # Can fail catastrophically
                ],
                'uses': ['Warp reality', 'Godlike power', 'Unpredictable'],
                'street_value': 100000.0  # Per unit
            }
        }
    
    def create_drug(
        self,
        drug_type: DrugType,
        quality: float,
        quantity: float,
        obtained_from: str
    ) -> DarkDrug:
        """Create drug instance from client payment."""
        definition = self.drug_definitions[drug_type]
        
        drug = DarkDrug(
            drug_id=f"{drug_type.value}_{int(datetime.now().timestamp())}",
            drug_type=drug_type,
            quality=quality,
            quantity=quantity,
            obtained_from=obtained_from,
            primary_effects=definition['primary_effects'].copy(),
            side_effects=definition['side_effects'].copy(),
            street_value=definition['street_value'] * quality
        )
        
        logger.info(f"Drug created: {drug_type.value} (quality {quality*100:.0f}%, €{drug.street_value:,.0f})")
        return drug
    
    async def use_drug(
        self,
        drug: DarkDrug,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Use drug (apply effects).
        
        Returns:
            Effect results
        """
        active_effects = []
        
        for effect in drug.primary_effects:
            active_effects.append({
                'effect': effect.effect_name,
                'magnitude': effect.magnitude * drug.quality,
                'duration_minutes': effect.duration_minutes,
                'positive': True
            })
        
        for effect in drug.side_effects:
            active_effects.append({
                'effect': effect.effect_name,
                'magnitude': effect.magnitude,
                'duration_minutes': effect.duration_minutes,
                'positive': False
            })
        
        logger.info(f"Drug used: {drug.drug_type.value} by {user_id}, {len(active_effects)} effects")
        
        return {
            'drug_id': drug.drug_id,
            'drug_type': drug.drug_type.value,
            'user_id': user_id,
            'effects': active_effects,
            'timestamp': datetime.now().isoformat()
        }
    
    async def mix_drugs(
        self,
        drug1: DarkDrug,
        drug2: DarkDrug
    ) -> Optional[DarkDrug]:
        """
        Mix two drugs (advanced alchemy).
        
        Some combinations create new effects, some are deadly.
        """
        logger.info(f"Mixing: {drug1.drug_type.value} + {drug2.drug_type.value}")
        
        # Combination effects table
        combinations = {
            (DrugType.GRAVE_DUST, DrugType.MOON_WINE): {
                'result_type': DrugType.GRAVE_DUST,  # Enhanced version
                'effects_multiplier': 1.5,
                'new_side_effects': [DrugEffect("extreme_aggression", 2.0, 30.0, False)]
            },
            (DrugType.VITAE, DrugType.LOGIC_SPORE): {
                'result_type': DrugType.VITAE,
                'effects_multiplier': 1.3,
                'new_side_effects': [DrugEffect("cognitive_overload", 1.5, 60.0, False)]
            },
            # Deadly combo
            (DrugType.STILL_BLOOD, DrugType.AETHER): {
                'result_type': None,  # Deadly - no result
                'effects_multiplier': 0.0,
                'new_side_effects': [DrugEffect("cellular_disintegration", 10.0, 0.0, False)]
            }
        }
        
        # Check if combination exists (order doesn't matter)
        combo_key = (drug1.drug_type, drug2.drug_type)
        reverse_key = (drug2.drug_type, drug1.drug_type)
        
        combo = combinations.get(combo_key) or combinations.get(reverse_key)
        
        if not combo:
            logger.warning("Unknown drug combination - unpredictable effects")
            return None
        
        if combo['result_type'] is None:
            logger.error("DEADLY COMBINATION - both drugs destroyed")
            return None
        
        # Create mixed drug
        mixed = DarkDrug(
            drug_id=f"mixed_{drug1.drug_id}_{drug2.drug_id}",
            drug_type=combo['result_type'],
            quality=(drug1.quality + drug2.quality) / 2 * combo['effects_multiplier'],
            quantity=min(drug1.quantity, drug2.quantity),
            obtained_from=f"Mixed: {drug1.obtained_from} + {drug2.obtained_from}",
            primary_effects=drug1.primary_effects.copy(),
            side_effects=drug1.side_effects + combo['new_side_effects']
        )
        
        logger.info(f"Mixed drug created: {mixed.drug_type.value} (quality {mixed.quality:.2f})")
        return mixed

