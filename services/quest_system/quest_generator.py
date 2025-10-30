"""
Quest Generation Engine - AI-driven quest creation.
Generates dynamic, contextually relevant quests using AI integration.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.ai_integration.llm_client import LLMClient
from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class QuestGenerationEngine:
    """
    AI-driven quest generation engine.
    Creates dynamic, contextually relevant quests based on world state and narrative context.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self.llm_client: Optional[LLMClient] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = await get_redis_pool()
        return self.redis
    
    async def _get_llm_client(self) -> LLMClient:
        """Get LLM client instance."""
        if self.llm_client is None:
            self.llm_client = LLMClient()
        return self.llm_client
    
    async def generate_quest(
        self,
        player_id: UUID,
        quest_type: str = "main",
        context: Optional[Dict[str, Any]] = None,
        quest_giver_npc_id: Optional[UUID] = None,
        world_state_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Generate a new quest using AI.
        
        Args:
            player_id: Player UUID
            quest_type: Type of quest (main, side, daily, event)
            context: Optional context for quest generation
            quest_giver_npc_id: Optional NPC that gives the quest
            world_state_id: Optional world state ID for context
        
        Returns:
            Generated quest data
        """
        # Gather context for quest generation
        quest_context = await self._gather_context(player_id, quest_giver_npc_id, world_state_id)
        
        # Merge provided context
        if context:
            quest_context.update(context)
        
        # Build prompt for quest generation
        prompt = self._build_quest_prompt(quest_type, quest_context)
        
        # Generate quest using LLM (fallback to template if LLM unavailable)
        try:
            llm_client = await self._get_llm_client()
            response = await llm_client.generate(
                prompt=prompt,
                context=quest_context,
                max_tokens=1500,
                temperature=0.8
            )
            quest_data = self._parse_quest_response(response)
        except Exception as e:
            print(f"LLM quest generation failed, using template: {e}")
            quest_data = self._generate_template_quest(quest_type, quest_context)
        
        # Generate unique quest ID
        quest_id = uuid4()
        
        # Structure quest data
        quest = {
            "quest_id": str(quest_id),
            "player_id": str(player_id),
            "quest_type": quest_type,
            "title": quest_data.get("title", "Untitled Quest"),
            "description": quest_data.get("description", ""),
            "objectives": quest_data.get("objectives", []),
            "rewards": quest_data.get("rewards", {}),
            "status": "active",
            "prerequisites": quest_data.get("prerequisites", []),
            "quest_giver_npc_id": str(quest_giver_npc_id) if quest_giver_npc_id else None,
            "world_state_id": str(world_state_id) if world_state_id else None,
            "meta_data": {
                "generated_at": quest_context.get("timestamp"),
                "generation_context": quest_context,
            }
        }
        
        return quest
    
    async def _gather_context(
        self,
        player_id: UUID,
        quest_giver_npc_id: Optional[UUID],
        world_state_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Gather context for quest generation."""
        context = {
            "timestamp": "2025-01-29T00:00:00Z",  # Would use actual timestamp
            "player_id": str(player_id),
        }
        
        postgres = await self._get_postgres()
        
        # Get player data
        player_row = await postgres.fetch(
            """
            SELECT id, level, stats, money, reputation
            FROM players
            WHERE id = $1
            """,
            player_id
        )
        if player_row:
            context["player"] = {
                "level": player_row["level"],
                "stats": player_row["stats"],
                "money": float(player_row["money"]),
                "reputation": player_row["reputation"],
            }
        
        # Get quest giver NPC data if provided
        if quest_giver_npc_id:
            npc_row = await postgres.fetch(
                """
                SELECT id, name, npc_type, personality_vector, current_location
                FROM npcs
                WHERE id = $1
                """,
                quest_giver_npc_id
            )
            if npc_row:
                context["quest_giver"] = {
                    "name": npc_row["name"],
                    "type": npc_row["npc_type"],
                    "location": npc_row["current_location"],
                }
        
        # Get world state data if provided
        if world_state_id:
            world_row = await postgres.fetch(
                """
                SELECT day_phase, faction_power, global_events
                FROM world_states
                WHERE id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                world_state_id
            )
            if world_row:
                context["world_state"] = {
                    "day_phase": world_row["day_phase"],
                    "faction_power": world_row["faction_power"],
                    "events": world_row["global_events"],
                }
        
        return context
    
    def _build_quest_prompt(self, quest_type: str, context: Dict[str, Any]) -> str:
        """Build prompt for quest generation."""
        prompt = f"""Generate a {quest_type} quest for "The Body Broker" game.

Game Context:
- Player Level: {context.get('player', {}).get('level', 1)}
- World Phase: {context.get('world_state', {}).get('day_phase', 'day')}
"""
        
        if "quest_giver" in context:
            prompt += f"- Quest Giver: {context['quest_giver']['name']} ({context['quest_giver']['type']}) at {context['quest_giver']['location']}\n"
        
        prompt += """
Generate a quest with:
1. A compelling title
2. A detailed description
3. 2-4 objectives (specific, measurable tasks)
4. Rewards (money, items, reputation, experience)
5. Any prerequisites

Return JSON format:
{
  "title": "Quest Title",
  "description": "Quest description...",
  "objectives": [
    {"id": "obj1", "description": "Objective 1", "type": "kill|collect|talk|go", "target": "...", "count": 1},
    ...
  ],
  "rewards": {
    "money": 100,
    "experience": 50,
    "reputation": 10,
    "items": []
  },
  "prerequisites": []
}
"""
        return prompt
    
    def _parse_quest_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into quest data."""
        try:
            # Extract text from response
            text = response.get("text", "") or response.get("response", "")
            
            # Try to extract JSON from response
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            
            # Parse JSON
            quest_data = json.loads(text)
            
            # Validate and normalize
            return {
                "title": quest_data.get("title", "Untitled Quest"),
                "description": quest_data.get("description", ""),
                "objectives": quest_data.get("objectives", []),
                "rewards": quest_data.get("rewards", {}),
                "prerequisites": quest_data.get("prerequisites", []),
            }
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return self._generate_template_quest("side", {})
    
    def _generate_template_quest(self, quest_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a template quest as fallback."""
        templates = {
            "main": {
                "title": "The Body Broker's First Client",
                "description": "A mysterious client needs your services. Investigate their request and fulfill their needs.",
                "objectives": [
                    {"id": "obj1", "description": "Meet with the client", "type": "talk", "target": "client_npc", "count": 1},
                    {"id": "obj2", "description": "Complete the client's request", "type": "collect", "target": "item", "count": 1},
                ],
                "rewards": {"money": 500, "experience": 100, "reputation": 25, "items": []},
                "prerequisites": [],
            },
            "side": {
                "title": "A Simple Errand",
                "description": "Someone needs help with a small task. Complete it for a reward.",
                "objectives": [
                    {"id": "obj1", "description": "Collect required items", "type": "collect", "target": "item", "count": 3},
                ],
                "rewards": {"money": 100, "experience": 50, "reputation": 10, "items": []},
                "prerequisites": [],
            },
        }
        
        return templates.get(quest_type, templates["side"])
