"""
Orchestration Service - Main service coordinating the 4-layer pipeline.
Manages parallel execution, conflict resolution, and state synchronization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from services.orchestration.models import ContentRequest, ContentResponse, FoundationOutput
from services.orchestration.layers import (
    FoundationLayer,
    CustomizationLayer,
    InteractionLayer,
    CoordinationLayer
)
from services.ai_integration.llm_client import LLMClient
from services.state_manager.connection_pool import get_postgres_pool

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Main orchestration service coordinating the 4-layer hierarchical LLM pipeline.
    """
    
    def __init__(
        self,
        inference_service=None,
        cloud_llm_client=None,
        state_manager=None
    ):
        """
        Initialize Orchestration Service.
        
        Args:
            inference_service: Service for local LLM inference
            cloud_llm_client: Client for cloud LLM calls
            state_manager: State manager for shared state
        """
        # Initialize layers
        self.layer1 = FoundationLayer(inference_service=inference_service)
        self.layer2 = CustomizationLayer(inference_service=inference_service)
        self.layer3 = InteractionLayer(inference_service=inference_service)
        self.layer4 = CoordinationLayer(cloud_llm_client=cloud_llm_client)
        
        # State management
        self.state_manager = state_manager
        self.postgres = None
        self.redis = None
        
        # LLM client for cloud operations
        self.cloud_llm_client = cloud_llm_client or LLMClient()
        
        logger.info("OrchestrationService initialized with 4-layer pipeline")
    
    async def _get_postgres(self):
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def _get_redis(self):
        """Get Redis cluster instance."""
        # Redis connection will be handled by state_manager if provided
        # For now, return None if not available
        return self.redis
    
    async def generate_content(
        self,
        request: ContentRequest,
        user_id: Optional[str] = None
    ) -> ContentResponse:
        """
        Generate content using the 4-layer pipeline.
        
        Args:
            request: Content generation request
            user_id: User ID for tier checking and rate limiting
            
        Returns:
            Complete content response
        """
        try:
            # Layer 1: Foundation (procedural + small LLMs)
            foundation_data = await self.layer1.generate_base(request)
            foundation = FoundationOutput(**foundation_data)
            
            # Layer 2: Customization (parallel)
            customization_tasks = []
            
            if foundation.monster:
                customization_tasks.append(
                    self.layer2.customize_monster(foundation.monster)
                )
            if foundation.terrain:
                customization_tasks.append(
                    self.layer2.enhance_terrain(foundation.terrain)
                )
            if foundation.room:
                customization_tasks.append(
                    self.layer2.detail_room(foundation.room)
                )
            
            customized_results = await asyncio.gather(
                *customization_tasks,
                return_exceptions=True
            )
            
            # Process customization results
            customized = {}
            result_index = 0
            if foundation.monster:
                if not isinstance(customized_results[result_index], Exception):
                    customized["monster"] = customized_results[result_index]
                result_index += 1
            if foundation.terrain:
                if not isinstance(customized_results[result_index], Exception):
                    customized["terrain"] = customized_results[result_index]
                result_index += 1
            if foundation.room:
                if not isinstance(customized_results[result_index], Exception):
                    customized["room"] = customized_results[result_index]
            
            # Layer 3: Interactions (only for active NPCs)
            interactions = None
            if request.activate_npcs:
                # Convert monsters to NPCs for dialogue generation
                npcs = []
                if customized.get("monster"):
                    npcs.append({
                        "id": "monster_1",
                        "type": customized["monster"].get("type", "creature"),
                        "is_active": True,
                        **customized["monster"]
                    })
                
                interactions = await self.layer3.generate_dialogue(
                    npcs=npcs,
                    player_context=request.player_context
                )
            
            # Layer 4: Coordination (if needed)
            orchestration = None
            if request.requires_coordination:
                orchestration = await self.layer4.coordinate(
                    content=customized,
                    interactions=interactions
                )
            
            # Resolve any conflicts
            resolved_content = await self.resolve_conflicts({
                "foundation": foundation_data,
                "customized": customized,
                "interactions": interactions,
                "orchestration": orchestration
            })
            
            return ContentResponse(
                foundation=foundation,
                customized=resolved_content.get("customized", customized),
                interactions=resolved_content.get("interactions", interactions),
                orchestration=resolved_content.get("orchestration", orchestration)
            )
            
        except Exception as e:
            logger.error(f"Error in OrchestrationService.generate_content: {e}")
            # Return fallback response
            return ContentResponse(
                foundation=FoundationOutput(),
                customized=None,
                interactions=None,
                orchestration=None
            )
    
    async def resolve_conflicts(self, layer_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflicts between layer outputs.
        
        Args:
            layer_outputs: Outputs from all layers
            
        Returns:
            Resolved outputs
        """
        try:
            conflicts = self._detect_conflicts(layer_outputs)
            
            if conflicts:
                logger.warning(f"Detected conflicts: {conflicts}")
                
                # Use cloud LLM to resolve conflicts if available
                if self.cloud_llm_client:
                    context = await self._get_state_context()
                    resolution = await self._resolve_with_llm(conflicts, context)
                    return self._apply_resolution(layer_outputs, resolution)
            
            return layer_outputs
        except Exception as e:
            logger.error(f"Error in OrchestrationService.resolve_conflicts: {e}")
            return layer_outputs
    
    def _detect_conflicts(self, layer_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts in layer outputs."""
        conflicts = []
        
        # Check for inconsistencies
        foundation = layer_outputs.get("foundation", {})
        customized = layer_outputs.get("customized", {})
        
        # Example: Check if monster type changed unexpectedly
        if foundation.get("monster", {}).get("type") != customized.get("monster", {}).get("type"):
            conflicts.append({
                "type": "monster_type_mismatch",
                "foundation": foundation.get("monster", {}).get("type"),
                "customized": customized.get("monster", {}).get("type")
            })
        
        return conflicts
    
    async def _get_state_context(self) -> Dict[str, Any]:
        """Get context from state manager."""
        try:
            if self.state_manager:
                return await self.state_manager.get_context("default")
            else:
                # Get basic context (Redis connection handled separately if needed)
                return {"entities": [], "history": [], "world": {}}
        except Exception as e:
            logger.error(f"Error getting state context: {e}")
        return {"entities": [], "history": [], "world": {}}
    
    async def _resolve_with_llm(
        self,
        conflicts: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve conflicts using cloud LLM."""
        try:
            prompt = f"""Resolve these conflicts in game content generation:
{conflicts}

Context: {context}

Provide a resolution that maintains consistency."""
            
            response = await self.cloud_llm_client.generate(
                model="gpt-5-pro",
                prompt=prompt,
                max_tokens=512
            )
            
            # Parse resolution
            if isinstance(response, dict):
                return response
            elif isinstance(response, str):
                return {"resolution": response, "conflicts": conflicts}
            else:
                return {"resolution": "default", "conflicts": conflicts}
        except Exception as e:
            logger.error(f"Error resolving conflicts with LLM: {e}")
            return {"resolution": "default", "conflicts": conflicts}
    
    def _apply_resolution(
        self,
        layer_outputs: Dict[str, Any],
        resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply resolution to layer outputs."""
        resolved = layer_outputs.copy()
        
        # Apply resolution based on conflict type
        resolution_plan = resolution.get("resolution", "default")
        
        if "monster_type_mismatch" in str(resolution.get("conflicts", [])):
            # Use foundation type as source of truth
            if "customized" in resolved and "monster" in resolved["customized"]:
                foundation_type = resolved["foundation"].get("monster", {}).get("type")
                if foundation_type:
                    resolved["customized"]["monster"]["type"] = foundation_type
        
        return resolved
    
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
            return await self.layer4.coordinate_battle(monsters, player)
        except Exception as e:
            logger.error(f"Error in OrchestrationService.coordinate_battle: {e}")
            return {
                "monster_actions": [],
                "coordinator_plan": {"error": str(e)}
            }
    
    async def close(self):
        """Close connections and cleanup."""
        try:
            if self.postgres:
                await self.postgres.close()
            if self.redis:
                await self.redis.aclose()
        except Exception as e:
            logger.error(f"Error closing orchestration service: {e}")

