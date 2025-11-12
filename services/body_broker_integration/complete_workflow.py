# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Body Broker Complete Workflow Orchestrator

Connects all 12 systems for gameplay.
"""

import asyncio
from typing import Dict, Any

from services.harvesting.body_part_extraction import HarvestingSystem
from services.negotiation.haggling_system import HagglingSystem
from services.drug_economy.dark_drugs_system import DarkDrugsSystem
from services.clients.dark_families_system import DarkFamiliesSystem
from services.morality.surgeon_butcher_system import SurgeonButcherSystem
from services.broker_book.broker_book_system import BrokerBook
from services.death_system.debt_of_flesh import DebtOfFleshSystem


class BodyBrokerOrchestrator:
    """Orchestrates all Body Broker systems."""
    
    def __init__(self):
        self.harvesting = HarvestingSystem()
        self.haggling = HagglingSystem()
        self.drugs = DarkDrugsSystem()
        self.families = DarkFamiliesSystem()
        self.morality = SurgeonButcherSystem()
        self.book = BrokerBook()
        self.death_system = DebtOfFleshSystem()
    
    async def initialize(self) -> None:
        """Initialize all systems."""
        self.death_system.set_hovel_location((0.0, 0.0, 0.0))
    
    async def execute_complete_transaction(
        self,
        target_id: str,
        target_type: Any,
        kill_method: Any,
        tool_quality: Any,
        parts: list,
        client_id: str,
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute complete broker transaction."""
        
        # Record kill
        await self.morality.record_kill(target_id, target_type)
        
        # Harvest
        harvest_result = await self.harvesting.extract_parts(
            target_id, kill_method, tool_quality, parts, 0.6
        )
        
        # Negotiate
        from services.negotiation.haggling_system import NegotiationContext
        context = NegotiationContext(**client_data)
        neg_result = await self.haggling.negotiate_deal(context, ["appeal_to_greed"])
        
        # Receive payment
        from services.drug_economy.dark_drugs_system import DrugType
        drug = self.drugs.create_drug(DrugType.GRAVE_DUST, 0.8, 10.0, "Client")
        
        return {
            'harvest': harvest_result,
            'negotiation': neg_result,
            'drug': drug
        }

