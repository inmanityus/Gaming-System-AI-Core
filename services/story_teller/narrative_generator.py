"""
Narrative Generator - AI-powered story content generation.
Integrated with Model Management System for guardrails monitoring.
"""

import json
import sys
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from services.state_manager.connection_pool import get_postgres_pool, PostgreSQLPool

# Add parent directory to path for model_management imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from services.model_management.guardrails_monitor import GuardrailsMonitor
from services.model_management.historical_log_processor import HistoricalLogProcessor


class NarrativeContext:
    """Represents the context for narrative generation."""
    
    def __init__(
        self,
        player_id: UUID,
        current_world: str,
        location: str,
        player_stats: Dict[str, Any],
        story_history: List[Dict[str, Any]],
        world_state: Dict[str, Any],
        npc_relationships: Dict[str, Any],
    ):
        self.player_id = player_id
        self.current_world = current_world
        self.location = location
        self.player_stats = player_stats
        self.story_history = story_history
        self.world_state = world_state
        self.npc_relationships = npc_relationships
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "player_id": str(self.player_id),
            "current_world": self.current_world,
            "location": self.location,
            "player_stats": self.player_stats,
            "story_history": self.story_history,
            "world_state": self.world_state,
            "npc_relationships": self.npc_relationships,
        }


class NarrativeGenerator:
    """
    Generates narrative content using AI services.
    Integrates with the hierarchical LLM system.
    Integrated with Model Management System for guardrails monitoring.
    """
    
    def __init__(self, guardrails_monitor: Optional[GuardrailsMonitor] = None):
        self.postgres: Optional[PostgreSQLPool] = None
        self._llm_endpoints = {
            "foundation": "http://localhost:8001/generate",
            "customization": "http://localhost:8002/generate", 
            "interaction": "http://localhost:8003/generate",
            "coordination": "http://localhost:8004/generate",
        }
        
        # Model Management System integration
        self.guardrails_monitor = guardrails_monitor or GuardrailsMonitor()
        self.historical_log_processor = HistoricalLogProcessor()
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def _get_player_context(self, player_id: UUID) -> NarrativeContext:
        """Get comprehensive player context for narrative generation."""
        postgres = await self._get_postgres()
        
        # Get player data
        player_query = """
            SELECT stats, current_world, location
            FROM players p
            LEFT JOIN game_states gs ON p.id = gs.player_id AND gs.is_active = TRUE
            WHERE p.id = $1
        """
        player_result = await postgres.fetch(player_query, player_id)
        
        if not player_result:
            raise ValueError(f"Player {player_id} not found")
        
        player_stats = json.loads(player_result["stats"]) if isinstance(player_result["stats"], str) else player_result["stats"]
        current_world = player_result["current_world"] or "day"
        location = player_result["location"] or "unknown"
        
        # Get story history
        history_query = """
            SELECT node_type, title, narrative_content, choices, created_at
            FROM story_nodes
            WHERE player_id = $1 AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 10
        """
        history_results = await postgres.fetch_all(history_query, player_id)
        story_history = []
        for result in history_results:
            story_history.append({
                "node_type": result["node_type"],
                "title": result["title"],
                "narrative_content": result["narrative_content"],
                "choices": json.loads(result["choices"]) if isinstance(result["choices"], str) else result["choices"],
                "created_at": result["created_at"].isoformat() if result["created_at"] else None,
            })
        
        # Get world state
        world_query = """
            SELECT global_events, faction_power, economic_state, npc_population, territory_control
            FROM world_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        world_result = await postgres.fetch(world_query)
        world_state = {}
        if world_result:
            world_state = {
                "global_events": json.loads(world_result["global_events"]) if isinstance(world_result["global_events"], str) else world_result["global_events"],
                "faction_power": json.loads(world_result["faction_power"]) if isinstance(world_result["faction_power"], str) else world_result["faction_power"],
                "economic_state": json.loads(world_result["economic_state"]) if isinstance(world_result["economic_state"], str) else world_result["economic_state"],
                "npc_population": json.loads(world_result["npc_population"]) if isinstance(world_result["npc_population"], str) else world_result["npc_population"],
                "territory_control": json.loads(world_result["territory_control"]) if isinstance(world_result["territory_control"], str) else world_result["territory_control"],
            }
        
        # Get NPC relationships
        npc_query = """
            SELECT n.name, n.npc_type, n.relationships
            FROM npcs n
            JOIN factions f ON n.faction_id = f.id
            WHERE f.name IN (
                SELECT DISTINCT jsonb_object_keys(territory_control)
                FROM world_states
                ORDER BY created_at DESC
                LIMIT 1
            )
            LIMIT 20
        """
        npc_results = await postgres.fetch_all(npc_query)
        npc_relationships = {}
        for result in npc_results:
            relationships = json.loads(result["relationships"]) if isinstance(result["relationships"], str) else result["relationships"]
            npc_relationships[result["name"]] = {
                "type": result["npc_type"],
                "relationships": relationships,
            }
        
        return NarrativeContext(
            player_id=player_id,
            current_world=current_world,
            location=location,
            player_stats=player_stats,
            story_history=story_history,
            world_state=world_state,
            npc_relationships=npc_relationships,
        )
    
    async def generate_narrative(
        self,
        player_id: UUID,
        node_type: str,
        title: str,
        description: str,
        context_hints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate narrative content for a story node.
        
        Args:
            player_id: Player UUID
            node_type: Type of story node
            title: Node title
            description: Node description
            context_hints: Additional context hints
        
        Returns:
            Generated narrative content with choices
        """
        try:
            # Get player context
            context = await self._get_player_context(player_id)
            
            # Prepare prompt for AI generation
            prompt = self._build_narrative_prompt(
                node_type=node_type,
                title=title,
                description=description,
                context=context,
                context_hints=context_hints or {},
            )
            
            # Generate content using appropriate LLM layer
            llm_endpoint = self._select_llm_layer(node_type)
            narrative_content = await self._call_llm_service(llm_endpoint, prompt)
            
            # Parse and validate generated content
            parsed_content = self._parse_narrative_response(narrative_content)
            
            # Monitor generated content with guardrails
            narrative_text = parsed_content.get("narrative_content", "")
            choices_text = [choice.get("text", "") for choice in parsed_content.get("choices", [])]
            all_outputs = [narrative_text] + choices_text
            
            # Check guardrails compliance
            monitoring_results = await self.guardrails_monitor.monitor_outputs(
                model_id="story_generation",  # Use case identifier
                outputs=all_outputs
            )
            
            # If guardrails violation detected, generate fallback content
            if not monitoring_results.get("compliant", True):
                violations = monitoring_results.get("violations", [])
                # Log violation for model management system
                print(f"Guardrails violation detected: {violations}")
                # For critical violations, return fallback content
                if any(v.get("severity") in ["critical", "high"] for v in violations):
                    return self._generate_fallback_content(node_type, title, description)
            
            # Log to historical logs for model management
            try:
                # Get current model ID for story generation use case
                from services.model_management.model_registry import ModelRegistry
                registry = ModelRegistry()
                current_model = await registry.get_current_model("story_generation")
                model_id = current_model.get("model_id") if current_model else None
                
                if model_id:
                    await self.historical_log_processor.log_inference(
                        model_id=UUID(model_id) if isinstance(model_id, str) else model_id,
                        use_case="story_generation",
                        prompt=prompt,
                        context=context.to_dict(),
                        generated_output=narrative_text,
                        performance_metrics={
                            "node_type": node_type,
                            "choices_count": len(parsed_content.get("choices", [])),
                            "guardrails_compliant": monitoring_results.get("compliant", True),
                        }
                    )
            except Exception as log_error:
                print(f"Error logging narrative generation: {log_error}")
            
            return parsed_content
            
        except Exception as e:
            # Fallback to default content
            return self._generate_fallback_content(node_type, title, description)
    
    def _build_narrative_prompt(
        self,
        node_type: str,
        title: str,
        description: str,
        context: NarrativeContext,
        context_hints: Dict[str, Any],
    ) -> str:
        """Build a comprehensive prompt for narrative generation."""
        
        prompt = f"""
Generate a {node_type} story node for "The Body Broker" game.

NODE DETAILS:
- Title: {title}
- Description: {description}
- Type: {node_type}

PLAYER CONTEXT:
- Player ID: {context.player_id}
- Current World: {context.current_world}
- Location: {context.location}
- Player Stats: {json.dumps(context.player_stats, indent=2)}

STORY HISTORY (Last 5 nodes):
{json.dumps(context.story_history[:5], indent=2)}

WORLD STATE:
- Global Events: {json.dumps(context.world_state.get('global_events', {}), indent=2)}
- Faction Power: {json.dumps(context.world_state.get('faction_power', {}), indent=2)}
- Economic State: {json.dumps(context.world_state.get('economic_state', {}), indent=2)}

NPC RELATIONSHIPS:
{json.dumps(context.npc_relationships, indent=2)}

CONTEXT HINTS:
{json.dumps(context_hints, indent=2)}

REQUIREMENTS:
1. Generate engaging narrative content that fits the cyberpunk noir theme
2. Create 2-4 meaningful choices for the player
3. Each choice should have consequences and impact the story
4. Maintain consistency with previous story elements
5. Consider the player's current world state and relationships
6. Make the content immersive and atmospheric

OUTPUT FORMAT (JSON):
{{
    "narrative_content": "The main story text...",
    "choices": [
        {{
            "id": "choice_1",
            "text": "Choice description",
            "consequences": {{
                "reputation": 5,
                "money": -100,
                "relationships": {{"npc_name": 10}}
            }},
            "prerequisites": {{"level": 5, "items": ["item_name"]}}
        }}
    ],
    "atmosphere": "dark_cyberpunk",
    "mood": "tense",
    "difficulty": "medium"
}}

Generate the content now:
"""
        return prompt
    
    def _select_llm_layer(self, node_type: str) -> str:
        """Select appropriate LLM layer based on node type."""
        layer_mapping = {
            "dialogue": "interaction",
            "action": "customization", 
            "choice": "interaction",
            "cutscene": "foundation",
            "combat": "customization",
            "exploration": "interaction",
            "story": "coordination",
        }
        return self._llm_endpoints.get(layer_mapping.get(node_type, "interaction"))
    
    async def _call_llm_service(self, endpoint: str, prompt: str) -> str:
        """Call LLM service to generate content."""
        # TODO: Implement actual LLM service calls
        # For now, return mock content
        return self._generate_mock_content(prompt)
    
    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock content for testing."""
        return json.dumps({
            "narrative_content": "The neon lights flicker as you step into the dimly lit alley. The air is thick with the scent of rain and something more sinister. A figure emerges from the shadows, their cybernetic implants glinting in the artificial light.",
            "choices": [
                {
                    "id": "approach_cautiously",
                    "text": "Approach cautiously and try to communicate",
                    "consequences": {
                        "reputation": 5,
                        "money": 0,
                        "relationships": {"mysterious_figure": 10}
                    },
                    "prerequisites": {}
                },
                {
                    "id": "back_away",
                    "text": "Back away slowly and look for another route",
                    "consequences": {
                        "reputation": -2,
                        "money": 0,
                        "relationships": {"mysterious_figure": -5}
                    },
                    "prerequisites": {}
                },
                {
                    "id": "activate_combat_mode",
                    "text": "Activate combat mode and prepare for a fight",
                    "consequences": {
                        "reputation": -10,
                        "money": 50,
                        "relationships": {"mysterious_figure": -20}
                    },
                    "prerequisites": {"level": 3}
                }
            ],
            "atmosphere": "dark_cyberpunk",
            "mood": "tense",
            "difficulty": "medium"
        })
    
    def _parse_narrative_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate the LLM response."""
        try:
            parsed = json.loads(response)
            
            # Validate required fields
            required_fields = ["narrative_content", "choices"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate choices structure
            if not isinstance(parsed["choices"], list):
                raise ValueError("Choices must be a list")
            
            for choice in parsed["choices"]:
                if not isinstance(choice, dict):
                    raise ValueError("Each choice must be a dictionary")
                if "id" not in choice or "text" not in choice:
                    raise ValueError("Each choice must have 'id' and 'text' fields")
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing narrative response: {e}")
    
    def _generate_fallback_content(
        self, 
        node_type: str, 
        title: str, 
        description: str
    ) -> Dict[str, Any]:
        """Generate fallback content when AI generation fails."""
        return {
            "narrative_content": f"You find yourself in a {node_type} situation. {description}",
            "choices": [
                {
                    "id": "continue",
                    "text": "Continue forward",
                    "consequences": {},
                    "prerequisites": {}
                },
                {
                    "id": "wait",
                    "text": "Wait and observe",
                    "consequences": {},
                    "prerequisites": {}
                }
            ],
            "atmosphere": "neutral",
            "mood": "calm",
            "difficulty": "easy"
        }
