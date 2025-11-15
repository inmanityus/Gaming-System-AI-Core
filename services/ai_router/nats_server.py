"""AI Router Service - NATS Binary Messaging Server
Routes AI requests to optimal services based on capabilities

Subjects: svc.ai.router.v1.route, svc.ai.router.v1.health_check
"""
import asyncio, logging, os, sys, random
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import ai_router_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIRouterNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="ai-router-service"))
    
    async def handle_route(self, request: ai_router_pb2.RouteRequest) -> ai_router_pb2.RouteResponse:
        response = ai_router_pb2.RouteResponse()
        response.meta.CopyFrom(request.meta)
        try:
            # Route to appropriate service based on request type
            service_map = {
                "inference": "ai-integration",
                "generation": "quest-system",
                "behavior": "npc-behavior",
                "state": "state-manager"
            }
            response.target_service = service_map.get(request.request_type, "ai-integration")
            response.target_subject = f"svc.{response.target_service}.v1.process"
            response.metadata["latency_estimate"] = str(random.uniform(1.0, 3.0))
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("AI Router NATS Service running on svc.ai.router.v1.route")
            async for msg in self.client.subscribe_queue("svc.ai.router.v1.route", "q.ai.router"):
                try:
                    request = ai_router_pb2.RouteRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_route(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(AIRouterNATSService().run())

