"""
4-Layer Pipeline Implementation for Orchestration Service.
Each layer handles a specific aspect of content generation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import random

logger = logging.getLogger(__name__)


class FoundationLayer:
    """
    Layer 1: Foundation
    Generates base content using procedural generation and small LLMs.
    Mostly procedural with minimal LLM usage.
    """
    
    def __init__(self, inference_service=None):
        """Initialize Foundation Layer."""
        self.inference_service = inference_service
        logger.info("FoundationLayer initialized")
    
    async def generate_base(self, request) -> Dict[str, Any]:
        """
        Generate foundation content (monsters, terrain, rooms).
        
        Args:
            request: ContentRequest with generation parameters
            
        Returns:
            FoundationOutput with base content
        """
        try:
            # Generate monster base (procedural with optional LLM enhancement)
            monster = await self._generate_monster_base(
                seed=request.seed,
                monster_type=request.monster_type
            )
            
            # Generate terrain (procedural)
            terrain = await self._generate_terrain(
                biome=request.biome,
                size=request.size
            )
            
            # Generate room (procedural)
            room = await self._generate_room(
                dimensions=request.dimensions,
                seed=request.seed
            )
            
            return {
                "monster": monster,
                "terrain": terrain,
                "room": room
            }
        except Exception as e:
            logger.error(f"Error in FoundationLayer.generate_base: {e}")
            # Return fallback content
            return {
                "monster": {"type": "default", "health": 100},
                "terrain": {"biome": "default", "size": 100},
                "room": {"dimensions": {"width": 10, "height": 10}}
            }
    
    async def _generate_monster_base(self, seed: Optional[int], monster_type: Optional[str]) -> Dict[str, Any]:
        """Generate base monster using procedural generation."""
        if seed is not None:
            random.seed(seed)
        
        monster_types = ["vampire", "zombie", "ghost", "werewolf", "demon"]
        selected_type = monster_type or random.choice(monster_types)
        
        return {
            "type": selected_type,
            "health": random.randint(50, 200),
            "attack": random.randint(10, 50),
            "defense": random.randint(5, 30),
            "speed": random.randint(20, 80),
            "seed": seed or random.randint(0, 1000000)
        }
    
    async def _generate_terrain(self, biome: Optional[str], size: Optional[int]) -> Dict[str, Any]:
        """Generate terrain using procedural generation."""
        biomes = ["forest", "desert", "tundra", "swamp", "mountain"]
        selected_biome = biome or random.choice(biomes)
        
        return {
            "biome": selected_biome,
            "size": size or random.randint(50, 500),
            "features": self._generate_terrain_features(selected_biome)
        }
    
    def _generate_terrain_features(self, biome: str) -> List[str]:
        """Generate terrain features based on biome."""
        feature_map = {
            "forest": ["trees", "streams", "clearings"],
            "desert": ["dunes", "oases", "cacti"],
            "tundra": ["snow", "ice", "rocks"],
            "swamp": ["mud", "water", "moss"],
            "mountain": ["cliffs", "caves", "valleys"]
        }
        return feature_map.get(biome, ["default"])
    
    async def _generate_room(self, dimensions: Optional[Dict[str, int]], seed: Optional[int]) -> Dict[str, Any]:
        """Generate room using procedural generation."""
        if seed is not None:
            random.seed(seed)
        
        if dimensions:
            width = dimensions.get("width", random.randint(10, 50))
            height = dimensions.get("height", random.randint(10, 50))
        else:
            width = random.randint(10, 50)
            height = random.randint(10, 50)
        
        return {
            "dimensions": {"width": width, "height": height},
            "exits": random.randint(1, 4),
            "lighting": random.choice(["bright", "dim", "dark"])
        }


class CustomizationLayer:
    """
    Layer 2: Customization
    Enhances base content using specialized local LLMs with LoRA adapters.
    """
    
    def __init__(self, inference_service=None):
        """Initialize Customization Layer."""
        self.inference_service = inference_service
        logger.info("CustomizationLayer initialized")
    
    async def customize_monster(self, base_monster: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize monster with personality using specialized LoRA adapter.
        
        Args:
            base_monster: Base monster from Layer 1
            
        Returns:
            Customized monster with personality
        """
        try:
            if self.inference_service:
                # Use specialized LoRA adapter for monster type
                monster_type = base_monster.get("type", "default")
                model_name = f"llama3.1-8b+{monster_type}-lora"
                
                prompt = f"Add personality and unique traits to this {monster_type}: {base_monster}"
                
                response = await self.inference_service.generate(
                    model=model_name,
                    prompt=prompt,
                    stream=False
                )
                
                # Merge LLM enhancements with base monster
                customized = base_monster.copy()
                if isinstance(response, dict):
                    customized.update(response)
                elif isinstance(response, str):
                    # Parse response if it's a string
                    customized["personality"] = response[:200]  # Truncate for safety
                
                return customized
            else:
                # Fallback: Add basic personality without LLM
                customized = base_monster.copy()
                customized["personality"] = f"A fierce {base_monster.get('type', 'creature')}"
                return customized
        except Exception as e:
            logger.error(f"Error in CustomizationLayer.customize_monster: {e}")
            # Return base monster with fallback personality
            customized = base_monster.copy()
            customized["personality"] = "A mysterious creature"
            return customized
    
    async def enhance_terrain(self, terrain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance terrain with details.
        
        Args:
            terrain: Terrain from Layer 1
            
        Returns:
            Enhanced terrain
        """
        try:
            enhanced = terrain.copy()
            enhanced["details"] = f"Detailed {terrain.get('biome', 'area')} with various features"
            return enhanced
        except Exception as e:
            logger.error(f"Error in CustomizationLayer.enhance_terrain: {e}")
            return terrain
    
    async def detail_room(self, room: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add details to room.
        
        Args:
            room: Room from Layer 1
            
        Returns:
            Detailed room
        """
        try:
            detailed = room.copy()
            lighting = room.get("lighting", "dim")
            detailed["atmosphere"] = f"A {lighting} room with {room.get('exits', 1)} exit(s)"
            return detailed
        except Exception as e:
            logger.error(f"Error in CustomizationLayer.detail_room: {e}")
            return room


class InteractionLayer:
    """
    Layer 3: Interaction
    Generates NPC dialogue for active NPCs only.
    """
    
    def __init__(self, inference_service=None):
        """Initialize Interaction Layer."""
        self.inference_service = inference_service
        logger.info("InteractionLayer initialized")
    
    async def generate_dialogue(
        self,
        npcs: List[Dict[str, Any]],
        player_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate dialogue for active NPCs.
        
        Args:
            npcs: List of NPCs (monsters/characters)
            player_context: Player context for dialogue generation
            
        Returns:
            List of dialogue objects
        """
        try:
            # Filter to active NPCs only
            active_npcs = [npc for npc in npcs if npc.get("is_active", True)]
            
            if not active_npcs:
                return []
            
            # Generate dialogue for each active NPC in parallel
            dialogue_tasks = [
                self.generate_npc_dialogue(npc, player_context)
                for npc in active_npcs
            ]
            
            dialogues = await asyncio.gather(*dialogue_tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_dialogues = [
                d for d in dialogues
                if not isinstance(d, Exception)
            ]
            
            return valid_dialogues
        except Exception as e:
            logger.error(f"Error in InteractionLayer.generate_dialogue: {e}")
            return []
    
    async def generate_npc_dialogue(
        self,
        npc: Dict[str, Any],
        player_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate dialogue for a single NPC.
        
        Args:
            npc: NPC data
            player_context: Player context
            
        Returns:
            Dialogue object
        """
        try:
            if self.inference_service and player_context:
                npc_type = npc.get("type", "creature")
                prompt = f"Generate dialogue for a {npc_type} NPC interacting with the player: {player_context}"
                
                response = await self.inference_service.generate(
                    model="llama3.1-8b",
                    prompt=prompt,
                    stream=False
                )
                
                dialogue_text = response if isinstance(response, str) else str(response)
                return {
                    "npc_id": npc.get("id", "unknown"),
                    "npc_type": npc_type,
                    "dialogue": dialogue_text[:500],  # Truncate for safety
                    "tone": npc.get("personality", "neutral")
                }
            else:
                # Fallback dialogue
                return {
                    "npc_id": npc.get("id", "unknown"),
                    "npc_type": npc.get("type", "creature"),
                    "dialogue": f"Hello, traveler. I am a {npc.get('type', 'creature')}.",
                    "tone": "neutral"
                }
        except Exception as e:
            logger.error(f"Error in InteractionLayer.generate_npc_dialogue: {e}")
            return {
                "npc_id": npc.get("id", "unknown"),
                "npc_type": npc.get("type", "creature"),
                "dialogue": "...",
                "tone": "neutral"
            }


class CoordinationLayer:
    """
    Layer 4: Coordination
    Uses cloud LLMs for complex scenario orchestration (battles, environmental storytelling).
    """
    
    def __init__(self, cloud_llm_client=None):
        """Initialize Coordination Layer."""
        self.cloud_llm_client = cloud_llm_client
        logger.info("CoordinationLayer initialized")
    
    async def coordinate(
        self,
        content: Dict[str, Any],
        interactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate complex scenarios using cloud LLM.
        
        Args:
            content: Content from Layers 1-2
            interactions: Interactions from Layer 3
            
        Returns:
            Orchestration plan
        """
        try:
            if self.cloud_llm_client:
                orchestration_prompt = self._build_orchestration_prompt(content, interactions)
                
                response = await self.cloud_llm_client.generate(
                    model="gpt-5-pro",
                    prompt=orchestration_prompt,
                    max_tokens=1024
                )
                
                plan = self._parse_orchestration_plan(response)
                return plan
            else:
                # Fallback: Basic coordination plan
                return {
                    "scenario_type": "battle",
                    "plan": "Basic coordination plan",
                    "monsters": content.get("monsters", []),
                    "interactions": interactions or []
                }
        except Exception as e:
            logger.error(f"Error in CoordinationLayer.coordinate: {e}")
            return {
                "scenario_type": "default",
                "plan": "Fallback coordination plan",
                "error": str(e)
            }
    
    def _build_orchestration_prompt(
        self,
        content: Dict[str, Any],
        interactions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build orchestration prompt for cloud LLM."""
        prompt = f"""Coordinate this scenario:
- Monsters: {content.get('monsters', [])}
- Terrain: {content.get('terrain', {})}
- Interactions: {interactions or []}

Generate a battle coordination plan that ensures:
1. Group cohesion among monsters
2. Tactical positioning
3. Dynamic response to player actions
"""
        return prompt
    
    def _parse_orchestration_plan(self, response: Any) -> Dict[str, Any]:
        """Parse orchestration plan from LLM response."""
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            return {
                "scenario_type": "battle",
                "plan": response[:1000],  # Truncate for safety
                "tactics": "coordination"
            }
        else:
            return {
                "scenario_type": "default",
                "plan": "Parsed coordination plan"
            }
    
    async def coordinate_battle(
        self,
        monsters: List[Dict[str, Any]],
        player: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate battle with multiple NPCs.
        
        Args:
            monsters: List of monsters
            player: Player state
            
        Returns:
            Battle execution plan
        """
        try:
            # Each monster decides action (parallel)
            monster_action_tasks = [
                self._monster_decide_action(monster, player)
                for monster in monsters
            ]
            
            monster_actions = await asyncio.gather(*monster_action_tasks, return_exceptions=True)
            
            # Filter exceptions
            valid_actions = [
                action for action in monster_actions
                if not isinstance(action, Exception)
            ]
            
            # Coordinator ensures group cohesion
            if self.cloud_llm_client:
                coordinator_plan = await self.cloud_llm_client.generate(
                    model="gpt-5-pro",
                    prompt=f"Coordinate these monster actions: {valid_actions}. Ensure pack coordination.",
                    max_tokens=512
                )
            else:
                coordinator_plan = {"tactics": "pack_coordination", "plan": "Basic coordination"}
            
            return {
                "monster_actions": valid_actions,
                "coordinator_plan": coordinator_plan
            }
        except Exception as e:
            logger.error(f"Error in CoordinationLayer.coordinate_battle: {e}")
            return {
                "monster_actions": [],
                "coordinator_plan": {"error": str(e)}
            }
    
    async def _monster_decide_action(
        self,
        monster: Dict[str, Any],
        player: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Monster decides action based on context."""
        return {
            "monster_id": monster.get("id", "unknown"),
            "action": "attack",
            "target": "player",
            "priority": monster.get("attack", 10)
        }

