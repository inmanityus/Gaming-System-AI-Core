from __future__ import annotations

"""Language System Service - NATS Binary Messaging Server
Multi-language translation and localization

Subjects: svc.lang.v1.translate, svc.lang.v1.detect, svc.lang.v1.localize
Events: evt.lang.translation.completed.v1
"""
import asyncio, logging, os, sys
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
import language_system_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LanguageSystemNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="language-system-service"))
    
    async def handle_translate(self, request: language_system_pb2.TranslateRequest) -> language_system_pb2.TranslateResponse:
        response = language_system_pb2.TranslateResponse()
        response.meta.CopyFrom(request.meta)
        try:
            response.translated_text = f"[{request.target_language}] {request.text}"
            response.detected_source_language = request.source_language or "en"
            response.confidence = 0.95
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Language System NATS Service running on svc.lang.v1.translate")
            async for msg in self.client.subscribe_queue("svc.lang.v1.translate", "q.lang"):
                try:
                    request = language_system_pb2.TranslateRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_translate(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(LanguageSystemNATSService().run())


