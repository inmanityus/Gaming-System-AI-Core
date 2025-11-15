"""
NPC Behavior Service - NATS Binary Messaging Server
Plans NPC behavior and actions using AI

Subjects:
  svc.npc.behavior.v1.plan - Plan NPC behavior RPC
Events:
  evt.npc.behavior.planned.v1 - Behavior planned event
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import uuid
import random

# Add SDK and generated proto paths
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path))
sys.path.insert(0, str(generated_path))

from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import npc_behavior_pb2
import common_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NPCBehaviorNATSService:
    """NATS-based NPC Behavior service."""
    
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(
            servers=[self.nats_url],
            name="npc-behavior-service"
        ))
    
    async def handle_behavior_request(
        self,
        request: npc_behavior_pb2.BehaviorRequest
    ) -> npc_behavior_pb2.BehaviorResponse:
        """Plan NPC behavior based on situation and world state."""
        logger.info(f"Planning behavior for NPC {request.npc_id}: {request.meta.request_id}")
        
        response = npc_behavior_pb2.BehaviorResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Generate behavior plan (mock implementation)
            response.plan_id = f"plan-{uuid.uuid4().hex[:8]}"
            
            # Add actions based on NPC archetype
            num_actions = random.randint(1, 3)
            action_types = ["MOVE", "SPEAK", "INTERACT", "WAIT", "ATTACK", "FLEE"]
            
            for i in range(num_actions):
                action = response.actions.add()
                action.type = random.choice(action_types)
                action.params["priority"] = str(random.randint(1, 10))
                action.params["duration"] = str(random.uniform(1.0, 5.0))
                
                if action.type == "SPEAK":
                    action.params["dialogue"] = "I have goods to trade..."
                elif action.type == "MOVE":
                    action.params["target_x"] = str(random.randint(0, 100))
                    action.params["target_y"] = str(random.randint(0, 100))
            
            logger.info(f"Generated {len(response.actions)} actions for NPC")
            return response
        
        except Exception as e:
            logger.error(f"Error planning behavior: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        """Run NATS service worker."""
        logger.info("Starting NPC Behavior NATS Service")
        logger.info(f"Connecting to NATS at {self.nats_url}")
        
        async with self.client:
            logger.info("Connected to NATS successfully")
            logger.info("Subscribing to svc.npc.behavior.v1.plan with queue group q.npc.behavior")
            
            async for msg in self.client.subscribe_queue(
                subject="svc.npc.behavior.v1.plan",
                queue="q.npc.behavior"
            ):
                try:
                    request = npc_behavior_pb2.BehaviorRequest()
                    request.ParseFromString(msg.data)
                    
                    response = await self.handle_behavior_request(request)
                    
                    if msg.reply:
                        await msg.respond(response.SerializeToString())
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)


async def main():
    """Main entry point."""
    service = NPCBehaviorNATSService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

