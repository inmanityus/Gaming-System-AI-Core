"""
Quest System Service - NATS Binary Messaging Server
Generates quests dynamically using AI

Subjects:
  svc.quest.v1.generate - Generate quest RPC
Events:
  evt.quest.generated.v1 - Quest generated event
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
import quest_pb2
import common_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestSystemNATSService:
    """NATS-based Quest System service."""
    
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(
            servers=[self.nats_url],
            name="quest-system-service"
        ))
    
    async def handle_generate_quest(
        self,
        request: quest_pb2.QuestGenerationRequest
    ) -> quest_pb2.QuestGenerationResponse:
        """Generate a quest based on player context."""
        logger.info(f"Generating quest for player {request.player_id}: {request.meta.request_id}")
        
        response = quest_pb2.QuestGenerationResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Generate quest (mock implementation)
            quest = response.quest
            quest.quest_id = f"quest-{uuid.uuid4().hex[:8]}"
            quest.title = f"The {random.choice(['Dark', 'Bloody', 'Corrupt'])} {random.choice(['Hunt', 'Trade', 'Contract'])}"
            quest.description = f"A dangerous opportunity in the body broker trade..."
            quest.difficulty = request.difficulty or "NORMAL"
            
            # Add objectives
            num_objectives = random.randint(2, 4)
            for i in range(num_objectives):
                objective = quest.objectives.add()
                objective.objective_id = f"obj-{i+1}"
                objective.description = f"Objective {i+1}: {random.choice(['Harvest', 'Deliver', 'Negotiate', 'Eliminate'])}"
                objective.type = random.choice(['harvest', 'delivery', 'negotiation', 'combat'])
                objective.params["target_count"] = str(random.randint(1, 5))
            
            # Add tags
            quest.tags["theme"] = random.choice(['horror', 'corruption', 'survival'])
            quest.tags["location"] = random.choice(['urban', 'warehouse', 'underground'])
            
            logger.info(f"Generated quest: {quest.title}")
            return response
        
        except Exception as e:
            logger.error(f"Error generating quest: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        """Run NATS service worker."""
        logger.info("Starting Quest System NATS Service")
        logger.info(f"Connecting to NATS at {self.nats_url}")
        
        async with self.client:
            logger.info("Connected to NATS successfully")
            logger.info("Subscribing to svc.quest.v1.generate with queue group q.quest")
            
            async for msg in self.client.subscribe_queue(
                subject="svc.quest.v1.generate",
                queue="q.quest"
            ):
                try:
                    request = quest_pb2.QuestGenerationRequest()
                    request.ParseFromString(msg.data)
                    
                    response = await self.handle_generate_quest(request)
                    
                    if msg.reply:
                        await msg.respond(response.SerializeToString())
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)


async def main():
    """Main entry point."""
    service = QuestSystemNATSService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

