"""Router Service - NATS Binary Messaging Server
Main request routing and load balancing

Subjects: svc.router.v1.route, svc.router.v1.health
"""
import asyncio, logging, os, sys, uuid, random
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import router_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RouterNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="router-service"))
    
    async def handle_route(self, request: router_pb2.RouteRequest) -> router_pb2.RouteResponse:
        response = router_pb2.RouteResponse()
        response.meta.CopyFrom(request.meta)
        try:
            response.routed_to = f"instance-{random.randint(1,5)}"
            response.latency_ms = random.randint(1, 3)
            response.response_payload = b"routed response"
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Router NATS Service running on svc.router.v1.route")
            async for msg in self.client.subscribe_queue("svc.router.v1.route", "q.router"):
                try:
                    request = router_pb2.RouteRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_route(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(RouterNATSService().run())

