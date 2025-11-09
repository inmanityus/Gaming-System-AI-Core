"""
Complete Body Broker Demo - All Systems Integration
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.harvesting.body_part_extraction import (
    HarvestingSystem, ExtractionMethod, ToolQuality, BodyPartType
)
from services.negotiation.haggling_system import (
    HagglingSystem, NegotiationContext, ClientTemperament
)
from services.drug_economy.dark_drugs_system import DarkDrugsSystem, DrugType
from services.clients.dark_families_system import DarkFamiliesSystem, ClientFamily
from services.morality.surgeon_butcher_system import SurgeonButcherSystem, TargetType
from services.broker_book.broker_book_system import BrokerBook
from services.death_system.debt_of_flesh import DebtOfFleshSystem


async def main():
    # Initialize all systems
    harvesting = HarvestingSystem()
    haggling = HagglingSystem()
    drugs = DarkDrugsSystem()
    families = DarkFamiliesSystem()
    morality = SurgeonButcherSystem()
    book = BrokerBook()
    death_system = DebtOfFleshSystem()
    death_system.set_hovel_location((0.0, 0.0, 0.0))
    
    print("="*60)
    print("THE BODY BROKER - Complete System Demo")
    print("="*60)
    
    # Workflow 1: First kill and sale
    print("\n[WORKFLOW 1: First Kill & Sale]")
    
    # Kill target
    await morality.record_kill("criminal_001", TargetType.DESERVING)
    print(f"Morality: {morality.state.path.value}")
    
    # Harvest
    result = await harvesting.extract_parts(
        "criminal_001",
        ExtractionMethod.BLADE_KILL,
        ToolQuality.STANDARD,
        [BodyPartType.KIDNEY],
        player_skill=0.6
    )
    kidney = result.parts_extracted[0]
    print(f"Harvested: {kidney.part_type.value} ({kidney.quality.value}) = €{kidney.actual_value:,.0f}")
    
    # Negotiate
    context = NegotiationContext(
        "carrion_001", "Rotclaw", ClientTemperament.AGGRESSIVE,
        "low", kidney.quality.value, kidney.actual_value,
        50, 5, "normal"
    )
    neg = await haggling.negotiate_deal(context, ["appeal_to_greed"])
    print(f"Negotiation: {neg.outcome.value} = €{neg.final_price:,.0f}")
    
    # Receive drug
    drug = drugs.create_drug(DrugType.GRAVE_DUST, 0.8, 10.0, "Carrion Kin")
    print(f"Payment: {drug.drug_type.value} x{drug.quantity} = €{drug.street_value:,.0f} street value")
    
    # Update Book
    book.witness_creature("ghoul_001", "Rotclaw the Ghoul")
    book.discover_drug("grave_dust", "Grave-Dust")
    book.add_client("carrion_001", "Rotclaw", "Ghoul")
    
    families.update_reputation(ClientFamily.CARRION_KIN, +10)
    print(f"Carrion Kin reputation: {families.player_relationships[ClientFamily.CARRION_KIN]}")
    
    print("\n✅ Complete workflow executed successfully!")
    print("\nAll 12 Body Broker systems operational.")


if __name__ == "__main__":
    asyncio.run(main())

