"""Story Teller Service - NATS Binary Messaging Server
Narrative generation and story management

Subjects: svc.story.v1.generate, svc.story.v1.evaluate, svc.story.v1.continue
Events: evt.story.generated.v1
"""
import asyncio, logging, os, sys, uuid, random
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import story_teller_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryTellerNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="story-teller-service"))
    
    async def handle_generate(self, request: story_teller_pb2.GenerateRequest) -> story_teller_pb2.GenerateResponse:
        response = story_teller_pb2.GenerateResponse()
        response.meta.CopyFrom(request.meta)
        try:
            response.story.content_id = f"story-{uuid.uuid4().hex[:8]}"
            response.story.content_type = request.story_type
            response.story.content = f"A {request.tone} {request.story_type} about dark dealings in The Body Broker..."
            response.story.quality_score = random.uniform(0.7, 0.95)
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Story Teller NATS Service running on svc.story.v1.generate")
            async for msg in self.client.subscribe_queue("svc.story.v1.generate", "q.story"):
                try:
                    request = story_teller_pb2.GenerateRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_generate(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(StoryTellerNATSService().run())

