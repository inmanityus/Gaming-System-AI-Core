"""Environmental Narrative Service - NATS Binary Messaging Server
Generates environmental storytelling elements

Subjects: svc.narrative.v1.generate, svc.narrative.v1.update_context
Events: evt.narrative.generated.v1
"""
import asyncio, logging, os, sys, uuid, random
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import environmental_narrative_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentalNarrativeNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="environmental-narrative-service"))
    
    async def handle_generate(self, request: environmental_narrative_pb2.GenerateRequest) -> environmental_narrative_pb2.GenerateResponse:
        response = environmental_narrative_pb2.GenerateResponse()
        response.meta.CopyFrom(request.meta)
        try:
            element = response.elements.add()
            element.element_id = f"elem-{uuid.uuid4().hex[:8]}"
            element.element_type = random.choice(["description", "sound", "visual"])
            element.content = f"A dark and foreboding {request.scene_type} scene..."
            element.intensity = random.uniform(0.5, 0.9)
            element.duration_seconds = random.randint(30, 120)
            response.atmosphere = random.choice(["tense", "mysterious", "ominous"])
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Environmental Narrative NATS Service running on svc.narrative.v1.generate")
            async for msg in self.client.subscribe_queue("svc.narrative.v1.generate", "q.narrative"):
                try:
                    request = environmental_narrative_pb2.GenerateRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_generate(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(EnvironmentalNarrativeNATSService().run())

