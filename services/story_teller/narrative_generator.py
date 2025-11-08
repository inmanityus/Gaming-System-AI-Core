"""
Narrative Generator - AI-powered story content generation.
Integrated with Model Management System for guardrails monitoring.
"""

import json
import sys
import os
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

from database_connection import get_postgres
import asyncpg

# Add parent directory to path for model_management imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from narrative_loader import NarrativeLoader
from feature_awareness import FeatureAwareness
from cross_world_consistency import CrossWorldConsistency

# HTTP clients for cross-service communication
import aiohttp
import logging

logger = logging.getLogger(__name__)


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
    
    def __init__(self, ai_integration_url: str = None):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        
        # AI Integration service URL for LLM calls
        self.ai_integration_url = ai_integration_url or os.getenv(
            "AI_INTEGRATION_URL",
            "http://ai-integration:8080"
        )
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Narrative Loader - loads world history from docs/narrative/
        self.narrative_loader = NarrativeLoader()
        logger.info(f"Loaded {len(self.narrative_loader.get_all_narratives())} narrative files")
        
        # Feature Awareness - makes story teller aware of all available features
        self.feature_awareness = FeatureAwareness()
        
        # Cross-World Consistency - ensures consistent asset generation
        self.cross_world_consistency = CrossWorldConsistency()
    
    async def _get_postgres(self) -> asyncpg.Pool:
        """Get PostgreSQL pool instance."""
        if self.postgres_pool is None:
            self.postgres_pool = await get_postgres()
        return self.postgres_pool
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30.0))
        return self.session
    
    async def _get_model_id_for_logging(self) -> Optional[str]:
        """Get current model ID for story generation use case via HTTP."""
        try:
            session = await self._get_session()
            model_mgmt_url = os.getenv("MODEL_MANAGEMENT_URL", "http://model-management:8080")
            url = f"{model_mgmt_url}/api/models/current/story_generation"
            
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("model_id")
        except Exception as e:
            logger.error(f"Error getting model ID: {e}")
        return None
    
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
        player_result = await postgres.fetchrow(player_query, player_id)
        
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
        history_results = await postgres.fetch(history_query, player_id)
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
        world_result = await postgres.fetchrow(world_query)
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
                FROM (
                    SELECT territory_control
                    FROM world_states
                    ORDER BY created_at DESC
                    LIMIT 1
                ) latest_state
            )
            LIMIT 20
        """
        npc_results = await postgres.fetch(npc_query)
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
            
            # Generate content using appropriate LLM layer with real LLM Client
            narrative_content = await self._call_llm_service(
                node_type=node_type,
                prompt=prompt,
                context=context.to_dict()
            )
            
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
                    return self._generate_fallback_content_dict(node_type, title, description)
            
            # Log to historical logs for model management
            try:
                # Get current model ID for story generation use case
                model_id = await self._get_model_id_for_logging()
                
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
            return self._generate_fallback_content_dict(node_type, title, description)
    
    def _build_narrative_prompt(
        self,
        node_type: str,
        title: str,
        description: str,
        context: NarrativeContext,
        context_hints: Dict[str, Any],
    ) -> str:
        """Build a comprehensive prompt for narrative generation."""
        
        # Get narrative context from loaded files
        narrative_context = self.narrative_loader.get_full_context()
        
        # Get feature awareness context for story teller
        feature_context = await self.feature_awareness.build_story_teller_prompt_context(
            world_type=context.current_world,
            location_type=context_hints.get("location_type"),
        )
        
        prompt = f"""
Generate a {node_type} story node for "The Body Broker" game.

=== WORLD HISTORY & NARRATIVE FOUNDATION ===
{narrative_context}

=== AVAILABLE SYSTEM FEATURES ===
{feature_context}

=== CURRENT NODE DETAILS ===
- Title: {title}
- Description: {description}
- Type: {node_type}

=== PLAYER CONTEXT ===
- Player ID: {context.player_id}
- Current World: {context.current_world}
- Location: {context.location}
- Player Stats: {json.dumps(context.player_stats, indent=2)}

=== STORY HISTORY (Last 5 nodes) ===
{json.dumps(context.story_history[:5], indent=2)}

=== WORLD STATE ===
- Global Events: {json.dumps(context.world_state.get('global_events', {}), indent=2)}
- Faction Power: {json.dumps(context.world_state.get('faction_power', {}), indent=2)}
- Economic State: {json.dumps(context.world_state.get('economic_state', {}), indent=2)}

=== NPC RELATIONSHIPS ===
{json.dumps(context.npc_relationships, indent=2)}

=== CONTEXT HINTS ===
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
    
    def _get_llm_layer(self, node_type: str) -> str:
        """Map node type to LLM layer name for hierarchical LLM system."""
        layer_mapping = {
            "dialogue": "interaction",
            "action": "customization", 
            "choice": "interaction",
            "cutscene": "foundation",
            "combat": "customization",
            "exploration": "interaction",
            "story": "coordination",
        }
        return layer_mapping.get(node_type, "interaction")
    
    async def _call_llm_service(self, node_type: str, prompt: str, context: Dict[str, Any]) -> str:
        """
        Call LLM service to generate content using real LLM Client.
        
        This replaces the previous mock implementation with actual HTTP calls
        to inference services via LLMClient.
        
        Args:
            node_type: Type of story node (maps to LLM layer)
            prompt: The prompt for narrative generation
            context: Context dictionary with player state, world state, etc.
        
        Returns:
            JSON string with narrative content and choices
        """
        try:
            # Get appropriate LLM layer for this node type
            layer = self._get_llm_layer(node_type)
            
            # Call real LLM service via LLMClient (makes actual HTTP requests)
            result = await self.llm_client.generate_text(
                layer=layer,
                prompt=prompt,
                context=context,
                max_tokens=2000,  # Sufficient for narrative content + choices
                temperature=0.8,  # Creative but controlled
            )
            
            # Check if request was successful
            if not result.get("success", False):
                # If LLM service unavailable, log error but continue with fallback
                error_msg = result.get("error", "Unknown error")
                print(f"Warning: LLM service returned error: {error_msg}")
                # Use fallback response but format it as expected JSON
                return self._generate_fallback_content(node_type, prompt)
            
            # Extract generated text from LLM response
            generated_text = result.get("text", "")
            
            # Try to parse as JSON if it's already JSON
            try:
                parsed = json.loads(generated_text)
                # If it's already in the expected format, return as-is
                if "narrative_content" in parsed and "choices" in parsed:
                    return generated_text
            except json.JSONDecodeError:
                # If not JSON, wrap it in the expected format
                pass
            
            # If LLM returned plain text, structure it as expected format
            # Note: In production, the LLM should be prompted to return structured JSON
            # This is a temporary adapter to handle text-only responses
            structured_response = {
                "narrative_content": generated_text,
                "choices": [
                    {
                        "id": "continue",
                        "text": "Continue",
                        "consequences": {},
                        "prerequisites": {}
                    }
                ],
                "atmosphere": "default",
                "mood": "neutral",
                "difficulty": "medium"
            }
            
            return json.dumps(structured_response)
            
        except Exception as e:
            # Log error and return fallback
            print(f"Error calling LLM service: {e}")
            return self._generate_fallback_content(node_type, prompt)
    
    def _generate_fallback_content(self, node_type: str, prompt: str) -> str:
        """
        Generate fallback content when LLM service is unavailable.
        This is a safety mechanism for when inference services are down,
        NOT mock data for production use. The system should always try
        to call real LLM services first.
        """
        fallback_narratives = {
            "dialogue": "You find yourself in conversation with a mysterious figure. The exchange is tense, and every word matters.",
            "action": "Action is required. The situation demands your immediate attention and careful decision-making.",
            "choice": "A critical choice presents itself. Your decision will shape what comes next.",
            "cutscene": "The scene unfolds before you, revealing important details about the world around you.",
            "combat": "Conflict is imminent. Prepare yourself for what's to come.",
            "exploration": "You explore your surroundings, discovering new information and opportunities.",
            "story": "The story continues to unfold, with new developments changing the landscape of possibilities.",
        }
        
        narrative_text = fallback_narratives.get(node_type, "The narrative continues, with new developments shaping your journey.")
        
        return json.dumps({
            "narrative_content": narrative_text,
            "choices": [
                {
                    "id": "continue_story",
                    "text": "Continue the story",
                    "consequences": {},
                    "prerequisites": {}
                }
            ],
            "atmosphere": "default",
            "mood": "neutral",
            "difficulty": "medium",
            "fallback_used": True  # Flag to indicate this is a fallback, not real generation
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
    
    def _generate_fallback_content_dict(
        self, 
        node_type: str, 
        title: str, 
        description: str
    ) -> Dict[str, Any]:
        """
        Generate fallback content when AI generation fails.
        Returns a Dict (used when called from generate_narrative).
        """
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
            "difficulty": "easy",
            "fallback_used": True  # Flag to indicate fallback was used
        }
