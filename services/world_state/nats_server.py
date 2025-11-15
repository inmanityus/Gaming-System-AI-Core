"""
World State Service - NATS Binary Messaging Server
Manages persistent world state with pub/sub for real-time updates

Subjects:
  svc.world.v1.get_state - Get world state
  svc.world.v1.update_state - Update world state
  svc.world.v1.subscribe - Subscribe to state changes
Events:
  evt.world.state.changed.v1 - World state changed
  evt.world.entity.updated.v1 - Entity updated
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List
import uuid

sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path))
sys.path.insert(0, str(generated_path))

from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import world_state_pb2
import common_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorldStateNATSService:
    """NATS-based World State service."""
    
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(
            servers=[self.nats_url],
            name="world-state-service"
        ))
        self.worlds: Dict[str, world_state_pb2.WorldState] = {}
    
    async def handle_get_state(
        self,
        request: world_state_pb2.GetStateRequest
    ) -> world_state_pb2.GetStateResponse:
        """Get current world state."""
        logger.info(f"Get world state {request.world_id}: {request.meta.request_id}")
        
        response = world_state_pb2.GetStateResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            if request.world_id not in self.worlds:
                # Initialize world
                world = world_state_pb2.WorldState()
                world.world_id = request.world_id
                world.timestamp_ms = int(asyncio.get_event_loop().time() * 1000)
                world.total_entities = 0
                self.worlds[request.world_id] = world
            
            world = self.worlds[request.world_id]
            response.world_state.CopyFrom(world)
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting world state: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_update_state(
        self,
        request: world_state_pb2.UpdateStateRequest
    ) -> world_state_pb2.UpdateStateResponse:
        """Update world state."""
        logger.info(f"Update world state {request.world_id}: {request.meta.request_id}")
        
        response = world_state_pb2.UpdateStateResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            if request.world_id not in self.worlds:
                world = world_state_pb2.WorldState()
                world.world_id = request.world_id
                self.worlds[request.world_id] = world
            
            world = self.worlds[request.world_id]
            
            # Update entities
            if request.merge:
                # Merge entities
                for req_entity in request.entities_to_update:
                    # Find existing or add new
                    found = False
                    for entity in world.entities:
                        if entity.entity_id == req_entity.entity_id:
                            entity.CopyFrom(req_entity)
                            found = True
                            break
                    if not found:
                        new_entity = world.entities.add()
                        new_entity.CopyFrom(req_entity)
            else:
                # Replace all entities
                del world.entities[:]
                for req_entity in request.entities_to_update:
                    new_entity = world.entities.add()
                    new_entity.CopyFrom(req_entity)
            
            # Update global flags
            if request.merge:
                world.global_flags.update(request.global_flags_to_update)
            else:
                world.global_flags.clear()
                world.global_flags.update(request.global_flags_to_update)
            
            world.timestamp_ms = int(asyncio.get_event_loop().time() * 1000)
            world.total_entities = len(world.entities)
            
            response.entities_updated = len(request.entities_to_update)
            response.flags_updated = len(request.global_flags_to_update)
            response.new_timestamp_ms = world.timestamp_ms
            
            return response
        
        except Exception as e:
            logger.error(f"Error updating world state: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        """Run NATS service workers."""
        logger.info("Starting World State NATS Service")
        logger.info(f"Connecting to NATS at {self.nats_url}")
        
        async with self.client:
            logger.info("Connected to NATS successfully")
            
            tasks = [
                asyncio.create_task(self._get_worker()),
                asyncio.create_task(self._update_worker()),
            ]
            
            await asyncio.gather(*tasks)
    
    async def _get_worker(self):
        """Worker for get state."""
        logger.info("Starting get state worker on svc.world.v1.get_state")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.world.v1.get_state",
            queue="q.world"
        ):
            try:
                request = world_state_pb2.GetStateRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_get_state(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in get worker: {e}", exc_info=True)
    
    async def _update_worker(self):
        """Worker for update state."""
        logger.info("Starting update state worker on svc.world.v1.update_state")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.world.v1.update_state",
            queue="q.world"
        ):
            try:
                request = world_state_pb2.UpdateStateRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_update_state(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in update worker: {e}", exc_info=True)


async def main():
    """Main entry point."""
    service = WorldStateNATSService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

