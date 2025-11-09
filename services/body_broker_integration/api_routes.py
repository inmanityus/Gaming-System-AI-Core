"""API routes for Body Broker systems - COMPLETE"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .complete_workflow import BodyBrokerOrchestrator
import asyncpg

router = APIRouter(prefix="/body-broker", tags=["body-broker"])
orchestrator = BodyBrokerOrchestrator()
db_pool = None


async def get_db():
    """Get database connection."""
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(
            host="localhost",
            port=5443,
            database="gaming_system_ai_core",
            user="postgres"
        )
    return db_pool


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


@router.post("/kill")
async def record_kill(target_id: str, target_type: str, justification: str = None):
    """Record a kill for morality tracking."""
    from services.morality.surgeon_butcher_system import TargetType
    await orchestrator.morality.record_kill(target_id, TargetType(target_type), justification)
    
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO kill_records (player_id, target_id, target_type, justification) VALUES ($1, $2, $3, $4)",
            "player_001", target_id, target_type, justification
        )
    
    return {"status": "recorded", "path": orchestrator.morality.state.path.value}


@router.get("/morality")
async def get_morality_status():
    """Get player's morality status."""
    return orchestrator.morality.get_consequences()


@router.post("/death")
async def trigger_death(location: List[float], world: str, gear_items: List[str], killed_by: str = None):
    """Trigger death and create corpse."""
    corpse_id = await orchestrator.death_system.trigger_death(
        tuple(location), world, gear_items, killed_by
    )
    
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO death_records (player_id, corpse_id, death_location, world, gear_items, killed_by, veil_fray_level) VALUES ($1, $2, point($3,$4), $5, $6, $7, $8)",
            "player_001", corpse_id, location[0], location[1], world, gear_items, killed_by, orchestrator.death_system.veil_fray.level
        )
    
    return {"corpse_id": corpse_id, "veil_fray_level": orchestrator.death_system.veil_fray.level}


@router.post("/book/witness")
async def witness_creature(creature_id: str, name: str):
    """Record creature sighting in Book."""
    orchestrator.book.witness_creature(creature_id, name)
    return {"status": "recorded"}


@router.get("/stats")
async def get_all_stats():
    """Get comprehensive stats across all systems."""
    return {
        "morality": orchestrator.morality.get_consequences(),
        "families": {"unlocked": [f.value for f in orchestrator.families.get_unlocked_families()]},
        "deaths": await orchestrator.death_system.get_death_stats(),
        "book_sections": {
            "creatures": len(orchestrator.book.terrors),
            "drugs": len(orchestrator.book.poisons),
            "clients": len(orchestrator.book.accounts),
            "parts": len(orchestrator.book.red_market)
        }
    }

