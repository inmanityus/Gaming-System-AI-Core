"""
Body Broker Integration Tests
Coder: Claude Sonnet 4.5
Awaiting Pairwise Testing

Tests complete Body Broker workflow:
- Harvesting -> Negotiation -> Drug Payment -> Empire Building
"""

import asyncio
import pytest
from services.harvesting.body_part_extraction import (
    HarvestingSystem,
    ExtractionMethod,
    ToolQuality,
    BodyPartType
)
from services.negotiation.haggling_system import (
    HagglingSystem,
    NegotiationContext,
    ClientTemperament
)
from services.drug_economy.dark_drugs_system import DarkDrugsSystem, DrugType
from services.clients.dark_families_system import DarkFamiliesSystem, ClientFamily
from services.morality.surgeon_butcher_system import SurgeonButcherSystem, TargetType


@pytest.mark.asyncio
async def test_complete_broker_workflow():
    """Test full workflow: harvest -> negotiate -> receive drug."""
    
    # Initialize systems
    harvesting = HarvestingSystem()
    haggling = HagglingSystem()
    drugs = DarkDrugsSystem()
    families = DarkFamiliesSystem()
    morality = SurgeonButcherSystem()
    
    # Step 1: Harvest body parts
    result = await harvesting.extract_parts(
        target_id="target_001",
        kill_method=ExtractionMethod.BLADE_KILL,
        tool_quality=ToolQuality.SURGICAL,
        parts_to_extract=[BodyPartType.KIDNEY],
        player_skill=0.7
    )
    
    assert result.success
    assert len(result.parts_extracted) == 1
    kidney = result.parts_extracted[0]
    
    # Step 2: Negotiate with client
    context = NegotiationContext(
        client_id="carrion_kin_001",
        client_name="Rotclaw",
        client_temperament=ClientTemperament.AGGRESSIVE,
        client_tier="low",
        item_quality=kidney.quality.value,
        base_price=kidney.actual_value,
        player_reputation=50,
        player_charisma=5,
        market_demand="normal"
    )
    
    neg_result = await haggling.negotiate_deal(
        context=context,
        player_tactics=["appeal_to_greed"]
    )
    
    assert neg_result.final_price > 0
    
    # Step 3: Receive drug payment
    drug = drugs.create_drug(
        drug_type=DrugType.GRAVE_DUST,
        quality=0.8,
        quantity=10.0,
        obtained_from="Carrion Kin"
    )
    
    assert drug.drug_type == DrugType.GRAVE_DUST
    assert drug.street_value > 0
    
    # Step 4: Record morality
    await morality.record_kill(
        target_id="target_001",
        target_type=TargetType.DESERVING
    )
    
    consequences = morality.get_consequences()
    assert consequences['path'] in ['surgeon', 'mixed']
    
    print(f"✅ Complete workflow test passed!")
    print(f"   Harvested: {kidney.part_type.value} ({kidney.quality.value})")
    print(f"   Negotiated: €{neg_result.final_price:,.0f} ({neg_result.outcome.value})")
    print(f"   Received: {drug.drug_type.value} (€{drug.street_value:,.0f})")
    print(f"   Morality: {consequences['path']}")


@pytest.mark.asyncio
async def test_client_progression():
    """Test progression through client tiers."""
    families = DarkFamiliesSystem()
    
    # Start with LOW tier unlocked
    assert families.is_family_unlocked(ClientFamily.CARRION_KIN)
    assert families.is_family_unlocked(ClientFamily.CHATTER_SWARM)
    
    # MID/HIGH tier locked
    assert not families.is_family_unlocked(ClientFamily.STITCH_GUILD)
    assert not families.is_family_unlocked(ClientFamily.LEVIATHAN_CONCLAVE)
    
    # Unlock MID tier
    families.unlock_family(ClientFamily.STITCH_GUILD)
    assert families.is_family_unlocked(ClientFamily.STITCH_GUILD)
    
    # Update reputation
    rep = families.update_reputation(ClientFamily.CARRION_KIN, +20)
    assert rep == 20
    
    print("✅ Client progression test passed!")


@pytest.mark.asyncio
async def test_morality_paths():
    """Test Surgeon vs Butcher path divergence."""
    morality = SurgeonButcherSystem()
    
    # Kill 10 deserving targets
    for i in range(10):
        await morality.record_kill(
            target_id=f"criminal_{i}",
            target_type=TargetType.DESERVING
        )
    
    # Should be Surgeon path
    assert morality.state.path == "surgeon"
    assert morality.state.vigilante_respect > 0
    
    # Kill 5 innocents (shifts to Butcher)
    for i in range(5):
        await morality.record_kill(
            target_id=f"innocent_{i}",
            target_type=TargetType.INNOCENT
        )
    
    # Should shift to Butcher or Mixed
    assert morality.state.path in ["butcher", "mixed"]
    assert morality.state.innocents_killed == 5
    
    print("✅ Morality paths test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

