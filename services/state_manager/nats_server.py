"""
State Manager Service - NATS Binary Messaging Server
Manages game state with optimistic concurrency control

Subjects:
  svc.state.manager.v1.update - Update game state (CAS)
  svc.state.manager.v1.get - Get game state
Events:
  evt.state.entity.updated.v1 - Entity state updated
  evt.state.player.updated.v1 - Player state updated
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict
import time

# Add SDK and generated proto paths
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path))
sys.path.insert(0, str(generated_path))

from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import state_manager_pb2
import common_pb2
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import ParseDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateStore:
    """In-memory state store with versioning."""
    
    def __init__(self):
        self.player_states: Dict[str, tuple[dict, int]] = {}  # player_id -> (state, version)
        self.entity_states: Dict[str, tuple[dict, int]] = {}  # entity_id -> (state, version)
    
    def get_player_state(self, player_id: str) -> tuple[dict, int]:
        """Get player state and version."""
        return self.player_states.get(player_id, ({}, 0))
    
    def update_player_state(
        self,
        player_id: str,
        state: dict,
        expected_version: int = None
    ) -> tuple[bool, int, str]:
        """
        Update player state with CAS.
        
        Returns: (success, new_version, error_message)
        """
        current_state, current_version = self.player_states.get(player_id, ({}, 0))
        
        # Check CAS if expected_version provided
        if expected_version is not None and expected_version != current_version:
            return False, current_version, f"Version conflict: expected {expected_version}, got {current_version}"
        
        # Update state
        new_version = current_version + 1
        self.player_states[player_id] = (state, new_version)
        return True, new_version, ""
    
    def delete_player_state(
        self,
        player_id: str,
        expected_version: int = None
    ) -> tuple[bool, str]:
        """
        Delete player state with CAS.
        
        Returns: (success, error_message)
        """
        if player_id not in self.player_states:
            return False, f"Player not found: {player_id}"
        
        _, current_version = self.player_states[player_id]
        
        # Check CAS if expected_version provided
        if expected_version is not None and expected_version != current_version:
            return False, f"Version conflict: expected {expected_version}, got {current_version}"
        
        del self.player_states[player_id]
        return True, ""
    
    def get_entity_state(self, entity_id: str) -> tuple[dict, int]:
        """Get entity state and version."""
        return self.entity_states.get(entity_id, ({}, 0))
    
    def update_entity_state(
        self,
        entity_id: str,
        state: dict,
        expected_version: int = None
    ) -> tuple[bool, int, str]:
        """Update entity state with CAS."""
        current_state, current_version = self.entity_states.get(entity_id, ({}, 0))
        
        if expected_version is not None and expected_version != current_version:
            return False, current_version, f"Version conflict: expected {expected_version}, got {current_version}"
        
        new_version = current_version + 1
        self.entity_states[entity_id] = (state, new_version)
        return True, new_version, ""
    
    def delete_entity_state(
        self,
        entity_id: str,
        expected_version: int = None
    ) -> tuple[bool, str]:
        """Delete entity state with CAS."""
        if entity_id not in self.entity_states:
            return False, f"Entity not found: {entity_id}"
        
        _, current_version = self.entity_states[entity_id]
        
        if expected_version is not None and expected_version != current_version:
            return False, f"Version conflict: expected {expected_version}, got {current_version}"
        
        del self.entity_states[entity_id]
        return True, ""


class StateManagerNATSService:
    """NATS-based State Manager service."""
    
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(
            servers=[self.nats_url],
            name="state-manager-service"
        ))
        self.store = StateStore()
    
    async def handle_update_state(
        self,
        request: state_manager_pb2.GameStateUpdate
    ) -> state_manager_pb2.GameStateUpdateAck:
        """Handle state update with optimistic concurrency control."""
        logger.info(f"State update request: {request.meta.request_id}")
        
        response = state_manager_pb2.GameStateUpdateAck()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Validate operation
            if request.op == state_manager_pb2.GameStateUpdate.OPERATION_UNSPECIFIED:
                response.ok = False
                response.error.code = common_pb2.Error.INVALID_ARGUMENT
                response.error.message = "Operation must be specified (UPSERT or DELETE)"
                return response
            
            # Get expected version (0 means no CAS check)
            expected_version = request.expected_version if request.expected_version > 0 else None
            
            # Handle based on target type
            if request.target.HasField("player"):
                player = request.target.player
                player_id = player.player_id
                
                if request.op == state_manager_pb2.GameStateUpdate.UPSERT:
                    # Convert Struct to dict
                    state_dict = {}
                    if player.state.fields:
                        for key, value in player.state.fields.items():
                            state_dict[key] = self._struct_value_to_python(value)
                    
                    success, new_version, error_msg = self.store.update_player_state(
                        player_id,
                        state_dict,
                        expected_version
                    )
                    
                    if not success:
                        response.ok = False
                        response.error.code = common_pb2.Error.FAILED_PRECONDITION
                        response.error.message = error_msg
                        response.new_version = new_version  # Return current version for retry
                        return response
                    
                    response.ok = True
                    response.new_version = new_version
                    
                    # Publish event
                    await self._publish_player_updated_event(player_id, new_version)
                
                elif request.op == state_manager_pb2.GameStateUpdate.DELETE:
                    success, error_msg = self.store.delete_player_state(player_id, expected_version)
                    
                    if not success:
                        response.ok = False
                        response.error.code = common_pb2.Error.FAILED_PRECONDITION
                        response.error.message = error_msg
                        return response
                    
                    response.ok = True
                    response.new_version = 0  # Deleted
            
            elif request.target.HasField("entity"):
                entity = request.target.entity
                entity_id = entity.entity_id
                
                if request.op == state_manager_pb2.GameStateUpdate.UPSERT:
                    state_dict = {}
                    if entity.state.fields:
                        for key, value in entity.state.fields.items():
                            state_dict[key] = self._struct_value_to_python(value)
                    
                    success, new_version, error_msg = self.store.update_entity_state(
                        entity_id,
                        state_dict,
                        expected_version
                    )
                    
                    if not success:
                        response.ok = False
                        response.error.code = common_pb2.Error.FAILED_PRECONDITION
                        response.error.message = error_msg
                        response.new_version = new_version
                        return response
                    
                    response.ok = True
                    response.new_version = new_version
                    
                    # Publish event
                    await self._publish_entity_updated_event(entity_id, new_version)
                
                elif request.op == state_manager_pb2.GameStateUpdate.DELETE:
                    success, error_msg = self.store.delete_entity_state(entity_id, expected_version)
                    
                    if not success:
                        response.ok = False
                        response.error.code = common_pb2.Error.FAILED_PRECONDITION
                        response.error.message = error_msg
                        return response
                    
                    response.ok = True
                    response.new_version = 0
            
            return response
        
        except Exception as e:
            logger.error(f"Error updating state: {e}", exc_info=True)
            response.ok = False
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_get_state(
        self,
        request: state_manager_pb2.GetStateRequest
    ) -> state_manager_pb2.GetStateResponse:
        """Get current state."""
        logger.info(f"Get state request: {request.meta.request_id}")
        
        response = state_manager_pb2.GetStateResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Get state based on target
            if request.target.HasField("player_id"):
                player_id = request.target.player_id
                state_dict, version = self.store.get_player_state(player_id)
                
                if not state_dict:
                    response.error.code = common_pb2.Error.NOT_FOUND
                    response.error.message = f"Player state not found: {player_id}"
                    return response
                
                # Convert dict to Struct
                ParseDict(state_dict, response.state)
                response.version = version
            
            elif request.target.HasField("entity_id"):
                entity_id = request.target.entity_id
                state_dict, version = self.store.get_entity_state(entity_id)
                
                if not state_dict:
                    response.error.code = common_pb2.Error.NOT_FOUND
                    response.error.message = f"Entity state not found: {entity_id}"
                    return response
                
                ParseDict(state_dict, response.state)
                response.version = version
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting state: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    def _struct_value_to_python(self, value):
        """Convert protobuf Value to Python type."""
        which = value.WhichOneof("kind")
        if which == "null_value":
            return None
        elif which == "number_value":
            return value.number_value
        elif which == "string_value":
            return value.string_value
        elif which == "bool_value":
            return value.bool_value
        elif which == "struct_value":
            return {k: self._struct_value_to_python(v) for k, v in value.struct_value.fields.items()}
        elif which == "list_value":
            return [self._struct_value_to_python(v) for v in value.list_value.values]
        return None
    
    async def _publish_player_updated_event(self, player_id: str, version: int):
        """Publish player updated event."""
        try:
            # TODO: Create proper event message and publish via JetStream
            logger.info(f"Player updated event: {player_id} v{version}")
        except Exception as e:
            logger.error(f"Error publishing player event: {e}")
    
    async def _publish_entity_updated_event(self, entity_id: str, version: int):
        """Publish entity updated event."""
        try:
            # TODO: Create proper event message and publish via JetStream
            logger.info(f"Entity updated event: {entity_id} v{version}")
        except Exception as e:
            logger.error(f"Error publishing entity event: {e}")
    
    async def run(self):
        """Run NATS service workers."""
        logger.info("Starting State Manager NATS Service")
        logger.info(f"Connecting to NATS at {self.nats_url}")
        
        async with self.client:
            logger.info("Connected to NATS successfully")
            
            # Start worker tasks
            tasks = [
                asyncio.create_task(self._update_worker()),
                asyncio.create_task(self._get_worker()),
            ]
            
            await asyncio.gather(*tasks)
    
    async def _update_worker(self):
        """Worker for state updates."""
        logger.info("Starting update state worker on svc.state.manager.v1.update")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.state.manager.v1.update",
            queue="q.state"
        ):
            try:
                request = state_manager_pb2.GameStateUpdate()
                request.ParseFromString(msg.data)
                
                response = await self.handle_update_state(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in update worker: {e}", exc_info=True)
    
    async def _get_worker(self):
        """Worker for state retrieval."""
        logger.info("Starting get state worker on svc.state.manager.v1.get")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.state.manager.v1.get",
            queue="q.state"
        ):
            try:
                request = state_manager_pb2.GetStateRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_get_state(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in get worker: {e}", exc_info=True)


async def main():
    """Main entry point."""
    service = StateManagerNATSService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

