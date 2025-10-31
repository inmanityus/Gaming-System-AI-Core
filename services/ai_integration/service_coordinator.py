"""
Service Coordinator - Inter-service communication and coordination.
Manages requests between AI Integration and other services.
Integrated with Model Management System for deployment coordination.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

import aiohttp
from aiohttp import ClientSession, ClientTimeout

# Add parent directory to path for model_management imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from services.model_management.deployment_manager import DeploymentManager


class ServiceCoordinator:
    """
    Coordinates communication between AI Integration and other services.
    Manages request routing, response aggregation, and error handling.
    Integrated with Model Management System for deployment coordination.
    """
    
    def __init__(self, deployment_manager: Optional[DeploymentManager] = None):
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=10.0)
        
        # Model Management System integration
        self.deployment_manager = deployment_manager or DeploymentManager()
        
        # Service endpoints
        self.services = {
            "state_manager": "http://localhost:8001",
            "settings": "http://localhost:8002", 
            "story_teller": "http://localhost:8005",
            "world_state": "http://localhost:8006",  # Future service
            "npc_behavior": "http://localhost:8007",  # Future service
        }
        
        # Request tracking
        self.request_counts = {name: 0 for name in self.services}
        self.error_counts = {name: 0 for name in self.services}
    
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(
        self, 
        service_name: str, 
        endpoint: str, 
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make request to a service."""
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        url = f"{self.services[service_name]}{endpoint}"
        session = await self._get_session()
        
        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    result = await response.json()
                    self.request_counts[service_name] += 1
                    return result
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    self.request_counts[service_name] += 1
                    return result
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
        except Exception as e:
            self.error_counts[service_name] += 1
            raise ServiceError(f"Request to {service_name} failed: {str(e)}")
    
    async def get_player_state(self, player_id: UUID) -> Dict[str, Any]:
        """Get player state from State Manager service."""
        try:
            result = await self._make_request(
                "state_manager",
                f"/game-states/player/{player_id}",
                "GET"
            )
            return result
        except ServiceError:
            # Fallback to direct database query
            return await self._get_player_state_fallback(player_id)
    
    async def _get_player_state_fallback(self, player_id: UUID) -> Dict[str, Any]:
        """Fallback method to get player state directly from database."""
        
        postgres = await get_postgres_pool()
        
        query = """
            SELECT gs.*, p.username, p.tier, p.level, p.reputation
            FROM game_states gs
            JOIN players p ON gs.player_id = p.id
            WHERE gs.player_id = $1 AND gs.is_active = TRUE
            ORDER BY gs.updated_at DESC
            LIMIT 1
        """
        
        result = await postgres.fetch(query, player_id)
        if not result:
            return {"error": "Player state not found"}
        
        return {
            "success": True,
            "state": dict(result),
            "source": "fallback"
        }
    
    async def get_player_settings(self, player_id: UUID) -> Dict[str, Any]:
        """Get player settings from Settings service."""
        try:
            result = await self._make_request(
                "settings",
                f"/players/{player_id}/preferences",
                "GET"
            )
            return result
        except ServiceError:
            return {"error": "Settings service unavailable"}
    
    async def get_story_context(self, player_id: UUID) -> Dict[str, Any]:
        """Get story context from Story Teller service."""
        try:
            result = await self._make_request(
                "story_teller",
                f"/players/{player_id}/nodes",
                "GET"
            )
            return result
        except ServiceError:
            return {"error": "Story Teller service unavailable"}
    
    async def update_player_state(
        self, 
        player_id: UUID, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update player state via State Manager service."""
        try:
            result = await self._make_request(
                "state_manager",
                f"/game-states/player/{player_id}",
                "POST",
                updates
            )
            return result
        except ServiceError:
            return {"error": "Failed to update player state"}
    
    async def create_story_node(
        self, 
        player_id: UUID, 
        story_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create story node via Story Teller service."""
        try:
            result = await self._make_request(
                "story_teller",
                f"/nodes",
                "POST",
                {"player_id": str(player_id), **story_data}
            )
            return result
        except ServiceError:
            return {"error": "Failed to create story node"}
    
    async def process_choice(
        self, 
        player_id: UUID, 
        node_id: UUID, 
        choice_id: str
    ) -> Dict[str, Any]:
        """Process player choice via Story Teller service."""
        try:
            result = await self._make_request(
                "story_teller",
                f"/nodes/{node_id}/choices/process",
                "POST",
                {"player_id": str(player_id), "choice_id": choice_id}
            )
            return result
        except ServiceError:
            return {"error": "Failed to process choice"}
    
    async def get_world_state(self) -> Dict[str, Any]:
        """Get world state from World State service."""
        try:
            result = await self._make_request(
                "world_state",
                "/world-state/current",
                "GET"
            )
            return result
        except ServiceError:
            return {"error": "World State service unavailable"}
    
    async def get_npc_behavior(
        self, 
        npc_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get NPC behavior from NPC Behavior service."""
        try:
            result = await self._make_request(
                "npc_behavior",
                f"/npcs/{npc_id}/behavior",
                "POST",
                context
            )
            return result
        except ServiceError:
            return {"error": "NPC Behavior service unavailable"}
    
    async def aggregate_context(
        self, 
        player_id: UUID, 
        context_types: List[str]
    ) -> Dict[str, Any]:
        """Aggregate context from multiple services."""
        tasks = []
        
        if "state" in context_types:
            tasks.append(self.get_player_state(player_id))
        
        if "settings" in context_types:
            tasks.append(self.get_player_settings(player_id))
        
        if "story" in context_types:
            tasks.append(self.get_story_context(player_id))
        
        if "world" in context_types:
            tasks.append(self.get_world_state())
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        aggregated = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                aggregated[f"error_{i}"] = str(result)
            else:
                context_type = context_types[i] if i < len(context_types) else f"unknown_{i}"
                aggregated[context_type] = result
        
        return aggregated
    
    async def broadcast_update(
        self, 
        update_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Broadcast update to all relevant services."""
        tasks = []
        
        # Determine which services need the update
        if update_type == "player_state":
            tasks.append(self._broadcast_to_service("state_manager", "/updates/player-state", data))
            tasks.append(self._broadcast_to_service("story_teller", "/updates/player-state", data))
        
        elif update_type == "story_progress":
            tasks.append(self._broadcast_to_service("state_manager", "/updates/story-progress", data))
            tasks.append(self._broadcast_to_service("world_state", "/updates/story-progress", data))
        
        elif update_type == "world_event":
            tasks.append(self._broadcast_to_service("story_teller", "/updates/world-event", data))
            tasks.append(self._broadcast_to_service("npc_behavior", "/updates/world-event", data))
        
        # Execute broadcasts concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "success": True,
            "update_type": update_type,
            "results": results,
            "timestamp": "2025-10-29T23:17:17Z"
        }
    
    async def _broadcast_to_service(
        self, 
        service_name: str, 
        endpoint: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Broadcast update to a specific service."""
        try:
            result = await self._make_request(service_name, endpoint, "POST", data)
            return {"service": service_name, "success": True, "result": result}
        except Exception as e:
            return {"service": service_name, "success": False, "error": str(e)}
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services."""
        health_status = {}
        
        for service_name in self.services:
            try:
                result = await self._make_request(service_name, "/health", "GET")
                health_status[service_name] = {
                    "status": "healthy",
                    "response": result
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "request_counts": self.request_counts,
            "error_counts": self.error_counts,
            "error_rates": {
                name: self.error_counts[name] / max(self.request_counts[name], 1)
                for name in self.services
            }
        }
    
    async def coordinate_model_deployment(
        self,
        new_model_id: str,
        current_model_id: str,
        use_case: str,
        strategy: str = "blue_green"
    ) -> Dict[str, Any]:
        """
        Coordinate model deployment during orchestration.
        
        This method integrates with DeploymentManager to handle model updates
        during service orchestration, ensuring smooth transitions.
        
        Args:
            new_model_id: ID of new model to deploy
            current_model_id: ID of current model to replace
            use_case: Use case identifier
            strategy: Deployment strategy (blue_green, canary, all_at_once)
        
        Returns:
            Deployment result with status and details
        """
        try:
            # Use DeploymentManager to handle deployment
            success = await self.deployment_manager.deploy_model(
                new_model_id=new_model_id,
                current_model_id=current_model_id,
                strategy=strategy
            )
            
            if success:
                # Notify services about model update
                await self.broadcast_update(
                    update_type="model_deployment",
                    data={
                        "use_case": use_case,
                        "new_model_id": new_model_id,
                        "current_model_id": current_model_id,
                        "strategy": strategy,
                        "status": "completed"
                    }
                )
            
            return {
                "success": success,
                "new_model_id": new_model_id,
                "current_model_id": current_model_id,
                "use_case": use_case,
                "strategy": strategy
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "new_model_id": new_model_id,
                "current_model_id": current_model_id,
                "use_case": use_case
            }


class ServiceError(Exception):
    """Raised when service communication fails."""
    pass
