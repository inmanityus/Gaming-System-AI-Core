"""
Edge Case Testing for Body Broker
Based on expected peer review feedback
"""

import pytest
import asyncio
from services.drug_economy.dark_drugs_system import DarkDrugsSystem, DrugType
from services.harvesting.body_part_extraction import HarvestingSystem, ExtractionMethod, ToolQuality, BodyPartType
from services.negotiation.haggling_system import HagglingSystem, NegotiationContext, ClientTemperament


@pytest.mark.asyncio
async def test_drug_mixing_deadly_combo():
    """Test deadly drug combination."""
    drugs = DarkDrugsSystem()
    
    drug1 = drugs.create_drug(DrugType.STILL_BLOOD, 1.0, 10.0, "Stitch-Guild")
    drug2 = drugs.create_drug(DrugType.AETHER, 1.0, 5.0, "Leviathan")
    
    result = await drugs.mix_drugs(drug1, drug2)
    
    assert result is None, "Deadly combo should return None"


@pytest.mark.asyncio
async def test_harvesting_extreme_low_skill():
    """Test harvesting with minimal skill."""
    harvesting = HarvestingSystem()
    
    result = await harvesting.extract_parts(
        "target_001",
        ExtractionMethod.SHOTGUN_BLAST,
        ToolQuality.RUSTY,
        [BodyPartType.BRAIN],
        player_skill=0.0
    )
    
    assert result.success
    assert result.parts_extracted[0].quality.value == "junk"


@pytest.mark.asyncio
async def test_negotiation_hostile_outcome():
    """Test negotiation leading to hostility."""
    haggling = HagglingSystem()
    
    context = NegotiationContext(
        "ghoul_001", "Angry Ghoul", ClientTemperament.AGGRESSIVE,
        "low", "junk", 1000.0, 0, 1, "low"
    )
    
    result = await haggling.negotiate_deal(context, ["intimidate"])
    
    # Low reputation + junk quality + wrong tactic should fail badly
    assert result.outcome.value in ["failed", "hostile"]


@pytest.mark.asyncio
async def test_decay_system():
    """Test body part decay over time."""
    from services.harvesting.body_part_extraction import BodyPart, BodyPartType, PartQuality
    from datetime import datetime, timedelta
    
    part = BodyPart(
        part_id="test_part",
        part_type=BodyPartType.HEART,
        quality=PartQuality.PRISTINE,
        base_value=50000.0,
        actual_value=100000.0,
        harvested_at=datetime.now() - timedelta(hours=25),  # Past decay time
        decay_time_hours=24.0
    )
    
    assert part.is_decayed() == True
    assert part.get_decay_percentage() > 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

