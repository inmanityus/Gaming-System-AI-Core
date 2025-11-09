"""API routes for Body Broker systems"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from .complete_workflow import BodyBrokerOrchestrator

router = APIRouter(prefix="/body-broker", tags=["body-broker"])
orchestrator = BodyBrokerOrchestrator()


class HarvestRequest(BaseModel):
    target_id: str
    kill_method: str
    tool_quality: str
    parts: List[str]


class NegotiationRequest(BaseModel):
    client_id: str
    client_name: str
    item_quality: str
    base_price: float
    tactics: List[str]


@router.post("/harvest")
async def harvest_parts(request: HarvestRequest):
    """Harvest body parts from target."""
    from services.harvesting.body_part_extraction import ExtractionMethod, ToolQuality, BodyPartType
    
    result = await orchestrator.harvesting.extract_parts(
        target_id=request.target_id,
        kill_method=ExtractionMethod(request.kill_method),
        tool_quality=ToolQuality(request.tool_quality),
        parts_to_extract=[BodyPartType(p) for p in request.parts],
        player_skill=0.6
    )
    
    return {
        "success": result.success,
        "parts": [{"type": p.part_type.value, "quality": p.quality.value, "value": p.actual_value} for p in result.parts_extracted]
    }


@router.post("/negotiate")
async def negotiate_deal(request: NegotiationRequest):
    """Negotiate with Dark World client."""
    from services.negotiation.haggling_system import NegotiationContext, ClientTemperament
    
    context = NegotiationContext(
        client_id=request.client_id,
        client_name=request.client_name,
        client_temperament=ClientTemperament.AGGRESSIVE,
        client_tier="low",
        item_quality=request.item_quality,
        base_price=request.base_price,
        player_reputation=50,
        player_charisma=5,
        market_demand="normal"
    )
    
    result = await orchestrator.haggling.negotiate_deal(context, request.tactics)
    
    return {
        "outcome": result.outcome.value,
        "final_price": result.final_price,
        "reputation_change": result.reputation_change
    }


@router.get("/families")
async def list_families():
    """List available Dark World families."""
    unlocked = orchestrator.families.get_unlocked_families()
    return {"unlocked_families": [f.value for f in unlocked]}


@router.get("/book/drugs/{drug_id}")
async def get_drug_info(drug_id: str):
    """Get drug information from Broker's Book."""
    entry = orchestrator.book.poisons.get(drug_id)
    if not entry:
        raise HTTPException(404, "Drug not found in Book")
    
    return {
        "name": entry.name,
        "tier": entry.tier.value,
        "price_range": (entry.street_price_min, entry.street_price_max),
        "effects_known": entry.effects_known
    }

