"""
Body Part Extraction System
Coder: Claude Sonnet 4.5
Awaiting Peer Review: GPT-5 Pro

From Body Broker design:
- Skill-based mini-game (precision matters)
- Quality grading: Junk → Good → Prime → Pristine
- Tool quality affects outcome
- Decay timer (parts have shelf life)
- Method matters: shotgun ruins organs, blade preserves, live extraction best
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ExtractionMethod(str, Enum):
    """Extraction methods."""
    SHOTGUN_BLAST = "shotgun_blast"  # Fast, ruins organs
    BLADE_KILL = "blade_kill"  # Preserves parts
    POISON_KILL = "poison_kill"  # Preserves most parts
    LIVE_EXTRACTION = "live_extraction"  # Best quality, hardest


class PartQuality(str, Enum):
    """Part quality grades."""
    JUNK = "junk"  # 25% base value
    DAMAGED = "damaged"  # 50% base value
    GOOD = "good"  # 100% base value
    PRIME = "prime"  # 150% base value
    PRISTINE = "pristine"  # 200% base value


class BodyPartType(str, Enum):
    """Human body part types."""
    HEART = "heart"
    LIVER = "liver"
    KIDNEY = "kidney"
    LUNG = "lung"
    BRAIN = "brain"
    EYES = "eyes"
    BLOOD = "blood"
    SKIN = "skin"
    BONE = "bone"
    SPINAL_CORD = "spinal_cord"


class ToolQuality(str, Enum):
    """Extraction tool quality."""
    RUSTY = "rusty"  # -20% quality
    STANDARD = "standard"  # 0% modifier
    SURGICAL = "surgical"  # +20% quality
    ADVANCED = "advanced"  # +40% quality


@dataclass
class BodyPart:
    """Harvested body part."""
    part_id: str
    part_type: BodyPartType
    quality: PartQuality
    base_value: float
    actual_value: float
    harvested_at: datetime
    decay_time_hours: float = 24.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_decayed(self) -> bool:
        """Check if part has decayed."""
        elapsed = datetime.now() - self.harvested_at
        return elapsed > timedelta(hours=self.decay_time_hours)
    
    def get_decay_percentage(self) -> float:
        """Get decay percentage (0.0 to 1.0)."""
        elapsed = datetime.now() - self.harvested_at
        return min(1.0, elapsed.total_seconds() / (self.decay_time_hours * 3600))


@dataclass
class ExtractionResult:
    """Result of extraction attempt."""
    success: bool
    parts_extracted: List[BodyPart]
    quality_achieved: PartQuality
    skill_rating: float  # 0.0 to 1.0
    time_taken_seconds: float
    complications: List[str] = field(default_factory=list)


class HarvestingSystem:
    """
    Body part extraction system for The Body Broker.
    
    Mechanics:
    - Kill method affects part quality
    - Tool quality matters
    - Player skill affects outcome
    - Decay timer creates urgency
    - Mini-game for precision
    """
    
    def __init__(self):
        """Initialize harvesting system."""
        # Quality multipliers by extraction method
        self.method_multipliers = {
            ExtractionMethod.SHOTGUN_BLAST: 0.25,  # Ruins organs
            ExtractionMethod.BLADE_KILL: 0.75,  # Decent
            ExtractionMethod.POISON_KILL: 0.90,  # Good
            ExtractionMethod.LIVE_EXTRACTION: 1.20,  # Best (bonus)
        }
        
        # Tool quality modifiers
        self.tool_modifiers = {
            ToolQuality.RUSTY: -0.20,
            ToolQuality.STANDARD: 0.0,
            ToolQuality.SURGICAL: +0.20,
            ToolQuality.ADVANCED: +0.40,
        }
        
        # Base values per part type (in credits/euros)
        self.base_values = {
            BodyPartType.HEART: 50000.0,
            BodyPartType.LIVER: 45000.0,
            BodyPartType.KIDNEY: 20000.0,
            BodyPartType.LUNG: 15000.0,
            BodyPartType.BRAIN: 80000.0,
            BodyPartType.EYES: 10000.0,
            BodyPartType.BLOOD: 500.0,  # Per liter
            BodyPartType.SKIN: 100.0,  # Per sq meter
            BodyPartType.BONE: 5000.0,
            BodyPartType.SPINAL_CORD: 60000.0,
        }
        
        logger.info("Harvesting system initialized")
    
    async def extract_parts(
        self,
        target_id: str,
        kill_method: ExtractionMethod,
        tool_quality: ToolQuality,
        parts_to_extract: List[BodyPartType],
        player_skill: float = 0.5,  # 0.0 to 1.0
        time_pressure: bool = False
    ) -> ExtractionResult:
        """
        Extract body parts from target.
        
        Args:
            target_id: Target human ID
            kill_method: How they were killed
            tool_quality: Quality of extraction tool
            parts_to_extract: Which parts to harvest
            player_skill: Player's skill level (0.0 to 1.0)
            time_pressure: Is player under time pressure (guards coming, etc.)
        
        Returns:
            Extraction result
        """
        import time
        start_time = time.time()
        
        parts_extracted = []
        complications = []
        
        # Base quality from kill method
        method_mult = self.method_multipliers[kill_method]
        tool_mod = self.tool_modifiers[tool_quality]
        
        # Calculate final quality modifier
        quality_modifier = method_mult + tool_mod + (player_skill * 0.3)
        
        # Time pressure penalty
        if time_pressure:
            quality_modifier -= 0.15
            complications.append("Time pressure reduced precision")
        
        # Extract each part
        for part_type in parts_to_extract:
            # Determine quality tier
            if quality_modifier >= 1.0:
                quality = PartQuality.PRISTINE
            elif quality_modifier >= 0.75:
                quality = PartQuality.PRIME
            elif quality_modifier >= 0.50:
                quality = PartQuality.GOOD
            elif quality_modifier >= 0.30:
                quality = PartQuality.DAMAGED
            else:
                quality = PartQuality.JUNK
            
            # Calculate value
            base_value = self.base_values[part_type]
            
            quality_multipliers = {
                PartQuality.JUNK: 0.25,
                PartQuality.DAMAGED: 0.50,
                PartQuality.GOOD: 1.0,
                PartQuality.PRIME: 1.5,
                PartQuality.PRISTINE: 2.0,
            }
            
            actual_value = base_value * quality_multipliers[quality]
            
            # Create part
            part_id = f"{target_id}_{part_type.value}_{int(datetime.now().timestamp())}"
            part = BodyPart(
                part_id=part_id,
                part_type=part_type,
                quality=quality,
                base_value=base_value,
                actual_value=actual_value,
                harvested_at=datetime.now(),
                metadata={
                    'target_id': target_id,
                    'extraction_method': kill_method.value,
                    'tool_quality': tool_quality.value,
                    'player_skill': player_skill
                }
            )
            
            parts_extracted.append(part)
            
            logger.info(
                f"Extracted {part_type.value}: {quality.value} quality, "
                f"€{actual_value:,.0f}"
            )
        
        time_taken = time.time() - start_time
        
        # Overall skill rating
        skill_rating = min(1.0, quality_modifier)
        
        result = ExtractionResult(
            success=len(parts_extracted) > 0,
            parts_extracted=parts_extracted,
            quality_achieved=parts_extracted[0].quality if parts_extracted else PartQuality.JUNK,
            skill_rating=skill_rating,
            time_taken_seconds=time_taken,
            complications=complications
        )
        
        return result
    
    async def check_decay(self, part: BodyPart) -> Tuple[bool, float]:
        """
        Check if part has decayed.
        
        Returns:
            (is_decayed, decay_percentage)
        """
        is_decayed = part.is_decayed()
        decay_pct = part.get_decay_percentage()
        
        if decay_pct > 0.75:
            logger.warning(f"Part {part.part_type.value} critically decayed: {decay_pct*100:.0f}%")
        
        return is_decayed, decay_pct
    
    async def apply_preservation(
        self,
        part: BodyPart,
        preservation_type: str = "formaldehyde"
    ) -> None:
        """
        Apply preservation to extend decay time.
        
        Args:
            part: Body part to preserve
            preservation_type: Type of preservation
        """
        if preservation_type == "formaldehyde":
            part.decay_time_hours += 24.0  # +1 day
        elif preservation_type == "cryogenic":
            part.decay_time_hours += 168.0  # +1 week
        
        logger.info(f"Preservation applied: {part.part_type.value} (+{part.decay_time_hours:.0f}h)")

