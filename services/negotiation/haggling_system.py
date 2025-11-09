"""
Haggling System - Negotiation with Dark Clients
Coder: Claude Sonnet 4.5
Awaiting Peer Review

Dialogue-based negotiation where:
- Reputation affects starting price
- Client personality affects tactics
- Quality affects leverage
- Can fail (client attacks or blacklists)

From Body Broker design - Face/Diplomat is S-tier skill.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NegotiationOutcome(str, Enum):
    """Negotiation results."""
    EXCELLENT = "excellent"  # 150% of asking price
    GOOD = "good"  # 120% of asking price
    FAIR = "fair"  # 100% of asking price
    POOR = "poor"  # 80% of asking price
    FAILED = "failed"  # No deal
    HOSTILE = "hostile"  # Client attacks


class ClientTemperament(str, Enum):
    """Client personality types."""
    AGGRESSIVE = "aggressive"  # Ghouls, low-tier
    CALCULATED = "calculated"  # Vampires, Synod
    WHIMSICAL = "whimsical"  # Fae
    DESPERATE = "desperate"  # High demand situations
    COLD = "cold"  # Golems, emotionless


@dataclass
class NegotiationContext:
    """Context for negotiation."""
    client_id: str
    client_name: str
    client_temperament: ClientTemperament
    client_tier: str  # "low", "mid", "high"
    item_quality: str  # From PartQuality
    base_price: float
    player_reputation: int  # 0-100 with this client
    player_charisma: int  # 1-10
    market_demand: str  # "low", "normal", "high", "critical"
    

@dataclass
class NegotiationResult:
    """Result of negotiation."""
    outcome: NegotiationOutcome
    final_price: float
    reputation_change: int
    client_response: str
    player_gained_insight: bool = False


class HagglingSystem:
    """
    Negotiation system for Dark World deals.
    
    S-tier skill per Body Broker design.
    Low charisma = eaten, betrayed, or broke.
    """
    
    def __init__(self):
        """Initialize haggling system."""
        # Temperament modifiers
        self.temperament_aggression = {
            ClientTemperament.AGGRESSIVE: 0.8,  # Easy to anger
            ClientTemperament.CALCULATED: 0.3,  # Hard to anger
            ClientTemperament.WHIMSICAL: 0.5,  # Unpredictable
            ClientTemperament.DESPERATE: 0.2,  # Won't risk deal
            ClientTemperament.COLD: 0.1,  # Emotionless
        }
        
        logger.info("Haggling system initialized")
    
    async def negotiate_deal(
        self,
        context: NegotiationContext,
        player_tactics: List[str]
    ) -> NegotiationResult:
        """
        Negotiate price with Dark World client.
        
        Args:
            context: Negotiation context
            player_tactics: Tactics player uses (intimidate, charm, logic, etc.)
        
        Returns:
            Negotiation result
        """
        # Calculate starting position
        reputation_mod = (context.player_reputation - 50) / 100  # -0.5 to +0.5
        charisma_mod = (context.player_charisma - 5) / 10  # -0.4 to +0.5
        
        # Market demand affects leverage
        demand_mods = {
            "low": -0.2,
            "normal": 0.0,
            "high": +0.2,
            "critical": +0.5
        }
        demand_mod = demand_mods.get(context.market_demand, 0.0)
        
        # Quality affects leverage
        quality_mods = {
            "junk": -0.3,
            "damaged": -0.15,
            "good": 0.0,
            "prime": +0.2,
            "pristine": +0.4
        }
        quality_mod = quality_mods.get(context.item_quality, 0.0)
        
        # Calculate leverage
        total_leverage = reputation_mod + charisma_mod + demand_mod + quality_mod
        
        # Evaluate tactics against temperament
        tactic_success = await self._evaluate_tactics(
            tactics=player_tactics,
            temperament=context.client_temperament,
            client_tier=context.client_tier
        )
        
        # Final leverage
        final_leverage = total_leverage + tactic_success
        
        # Determine outcome
        if final_leverage >= 0.6:
            outcome = NegotiationOutcome.EXCELLENT
            price_mult = 1.5
            rep_change = +10
        elif final_leverage >= 0.3:
            outcome = NegotiationOutcome.GOOD
            price_mult = 1.2
            rep_change = +5
        elif final_leverage >= -0.1:
            outcome = NegotiationOutcome.FAIR
            price_mult = 1.0
            rep_change = 0
        elif final_leverage >= -0.4:
            outcome = NegotiationOutcome.POOR
            price_mult = 0.8
            rep_change = -5
        else:
            # Deal fails
            aggression = self.temperament_aggression[context.client_temperament]
            if final_leverage < -0.6 and aggression > 0.5:
                outcome = NegotiationOutcome.HOSTILE
                price_mult = 0.0
                rep_change = -50
            else:
                outcome = NegotiationOutcome.FAILED
                price_mult = 0.0
                rep_change = -10
        
        final_price = context.base_price * price_mult
        
        # Generate client response
        response = await self._generate_client_response(
            outcome=outcome,
            temperament=context.client_temperament,
            client_name=context.client_name
        )
        
        result = NegotiationResult(
            outcome=outcome,
            final_price=final_price,
            reputation_change=rep_change,
            client_response=response,
            player_gained_insight=(outcome in [NegotiationOutcome.EXCELLENT, NegotiationOutcome.GOOD])
        )
        
        logger.info(
            f"Negotiation result: {outcome.value}, "
            f"€{final_price:,.0f} ({price_mult*100:.0f}%), "
            f"rep {rep_change:+d}"
        )
        
        return result
    
    async def _evaluate_tactics(
        self,
        tactics: List[str],
        temperament: ClientTemperament,
        client_tier: str
    ) -> float:
        """
        Evaluate player tactics against client temperament.
        
        Returns:
            Tactic success modifier (-0.3 to +0.3)
        """
        # Tactic effectiveness by temperament
        effectiveness = {
            ClientTemperament.AGGRESSIVE: {
                "intimidate": +0.2,
                "charm": -0.1,
                "logic": -0.2,
                "appeal_to_greed": +0.15
            },
            ClientTemperament.CALCULATED: {
                "intimidate": -0.2,
                "charm": +0.1,
                "logic": +0.3,
                "appeal_to_greed": +0.2
            },
            ClientTemperament.WHIMSICAL: {
                "intimidate": -0.3,
                "charm": +0.2,
                "logic": -0.1,
                "riddle": +0.4  # Fae love wordplay
            },
            ClientTemperament.DESPERATE: {
                "intimidate": +0.3,
                "charm": +0.1,
                "logic": 0.0,
                "exploit_desperation": +0.4
            },
            ClientTemperament.COLD: {
                "intimidate": 0.0,
                "charm": 0.0,
                "logic": +0.3,
                "data_driven_argument": +0.3
            }
        }
        
        client_effectiveness = effectiveness.get(temperament, {})
        
        total_modifier = 0.0
        for tactic in tactics:
            modifier = client_effectiveness.get(tactic, -0.1)  # Unknown tactic = slight penalty
            total_modifier += modifier
        
        # Cap at +/- 0.3
        return max(-0.3, min(0.3, total_modifier))
    
    async def _generate_client_response(
        self,
        outcome: NegotiationOutcome,
        temperament: ClientTemperament,
        client_name: str
    ) -> str:
        """Generate client response dialogue."""
        responses = {
            NegotiationOutcome.EXCELLENT: [
                f"{client_name} grins, revealing teeth. 'You drive a hard bargain, Broker. I respect that. Here's your payment—and a little extra for your... efficiency.'",
                f"A satisfied hum emanates from {client_name}. 'Quality and fair dealing. We shall meet again, Broker.'",
            ],
            NegotiationOutcome.GOOD: [
                f"{client_name} nods slowly. 'Acceptable. The quality justifies your price. Here.'",
                f"'{client_name} examines the goods. 'Mmm. Yes. This will do nicely. Your payment, as agreed.'"
            ],
            NegotiationOutcome.FAIR: [
                f"{client_name} shrugs. 'Standard rates. Nothing more, nothing less. Here's your due.'",
                f"A brief transaction. {client_name} hands over the payment without comment."
            ],
            NegotiationOutcome.POOR: [
                f"{client_name} scowls. 'You test my patience, Broker. Take this pittance and be grateful I'm paying at all.'",
                f"'Disappointing,' {client_name} mutters, tossing a smaller pouch at your feet. 'Don't waste my time again.'"
            ],
            NegotiationOutcome.FAILED: [
                f"{client_name} turns away. 'No deal. Find me when you have something worth my time.'",
                f"'Leave. Now.' {client_name}'s eyes narrow dangerously. The transaction is over."
            ],
            NegotiationOutcome.HOSTILE: [
                f"{client_name} snarls, lunging at you! 'You insult me with this trash? I'll EAT you instead!'",
                f"'WORTHLESS!' {client_name} shrieks, shifting into attack posture. You've crossed the line."
            ]
        }
        
        response_list = responses.get(outcome, ["No response."])
        return response_list[0]  # Return first response (could randomize)

