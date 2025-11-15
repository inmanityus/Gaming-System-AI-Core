"""Knowledge Base Service - NATS Binary Messaging Server
RAG system for game lore and documentation

Subjects: svc.kb.v1.query, svc.kb.v1.ingest, svc.kb.v1.update
Events: evt.kb.document.ingested.v1
"""
import asyncio, logging, os, sys, uuid
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import knowledge_base_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="knowledge-base-service"))
        self.documents = []
    
    async def handle_query(self, request: knowledge_base_pb2.QueryRequest) -> knowledge_base_pb2.QueryResponse:
        response = knowledge_base_pb2.QueryResponse()
        response.meta.CopyFrom(request.meta)
        try:
            # Mock search
            for doc in self.documents:
                if request.query_text.lower() in doc.content.lower():
                    result = response.documents.add()
                    result.CopyFrom(doc)
                    result.relevance_score = 0.85
            
            response.synthesized_answer = f"Based on {len(response.documents)} sources: {request.query_text}"
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Knowledge Base NATS Service running on svc.kb.v1.query")
            async for msg in self.client.subscribe_queue("svc.kb.v1.query", "q.kb"):
                try:
                    request = knowledge_base_pb2.QueryRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_query(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(KnowledgeBaseNATSService().run())

