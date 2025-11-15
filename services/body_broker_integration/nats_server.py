"""Body Broker Integration Service - NATS Binary Messaging Server
Game-specific body part trading mechanics

Subjects: svc.broker.v1.harvest, svc.broker.v1.negotiate, svc.broker.v1.complete_deal
Events: evt.broker.harvest.completed.v1, evt.broker.deal.completed.v1
"""
import asyncio, logging, os, sys, uuid, random
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import body_broker_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BodyBrokerNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="body-broker-service"))
    
    async def handle_harvest(self, request: body_broker_pb2.HarvestRequest) -> body_broker_pb2.HarvestResponse:
        response = body_broker_pb2.HarvestResponse()
        response.meta.CopyFrom(request.meta)
        try:
            for part_name in request.body_parts:
                part = response.harvested_parts.add()
                part.part_type = part_name
                part.quality = random.choice(["pristine", "good", "damaged"])
                part.freshness = random.uniform(0.6, 1.0)
            response.skill_xp_gained = random.uniform(10.0, 50.0)
            response.morality_impact = random.choice(["surgeon", "butcher"])
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Body Broker NATS Service running on svc.broker.v1.harvest")
            async for msg in self.client.subscribe_queue("svc.broker.v1.harvest", "q.broker"):
                try:
                    request = body_broker_pb2.HarvestRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_harvest(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(BodyBrokerNATSService().run())

