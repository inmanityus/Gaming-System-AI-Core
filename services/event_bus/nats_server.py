"""Event Bus Service - NATS Binary Messaging Server
Central event distribution using JetStream

Subjects: svc.events.v1.publish, evt.*.*.*
"""
import asyncio, logging, os, sys, uuid
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import event_bus_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventBusNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="event-bus-service"))
    
    async def handle_publish(self, request: event_bus_pb2.PublishRequest) -> event_bus_pb2.PublishResponse:
        response = event_bus_pb2.PublishResponse()
        response.meta.CopyFrom(request.meta)
        try:
            event = event_bus_pb2.GameEvent()
            event.event_id = request.event_id
            event.event_type = request.event_type
            event.timestamp_ms = int(asyncio.get_event_loop().time() * 1000)
            event.payload = request.payload
            for k, v in request.metadata.items(): event.metadata[k] = v
            event.priority = request.priority
            
            # Publish to JetStream
            subject = f"evt.{request.event_type}.v1"
            await self.client.publish_event(subject, event)
            
            response.success = True
            response.event_id = request.event_id
            response.subscriber_count = 1  # Mock
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Event Bus NATS Service running on svc.events.v1.publish")
            async for msg in self.client.subscribe_queue("svc.events.v1.publish", "q.events"):
                try:
                    request = event_bus_pb2.PublishRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_publish(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(EventBusNATSService().run())

