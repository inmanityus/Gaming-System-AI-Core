"""Auth Service - NATS Binary Messaging Server
Session management, authentication, rate limiting

Subjects: svc.auth.v1.validate_session, svc.auth.v1.create_session, svc.auth.v1.revoke_session, svc.auth.v1.check_rate_limit
"""
import asyncio, logging, os, sys, uuid, time
from pathlib import Path
from typing import Dict
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import auth_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="auth-service"))
        self.sessions: Dict[str, dict] = {}
    
    async def handle_validate_session(self, request: auth_pb2.ValidateSessionRequest) -> auth_pb2.ValidateSessionResponse:
        response = auth_pb2.ValidateSessionResponse()
        response.meta.CopyFrom(request.meta)
        try:
            if request.session_token in self.sessions:
                session = self.sessions[request.session_token]
                response.is_valid = True
                response.user_id = session["user_id"]
                for k, v in session.get("data", {}).items(): response.session_data[k] = v
                response.expires_at_ms = session["expires_at_ms"]
            else:
                response.is_valid = False
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_create_session(self, request: auth_pb2.CreateSessionRequest) -> auth_pb2.CreateSessionResponse:
        response = auth_pb2.CreateSessionResponse()
        response.meta.CopyFrom(request.meta)
        try:
            token = f"sess-{uuid.uuid4().hex}"
            expires_at = int(time.time() * 1000) + (request.ttl_seconds * 1000)
            self.sessions[token] = {
                "user_id": request.user_id,
                "data": dict(request.session_data),
                "expires_at_ms": expires_at
            }
            response.session_token = token
            response.expires_at_ms = expires_at
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Auth NATS Service running")
            tasks = [
                asyncio.create_task(self._validate_worker()),
                asyncio.create_task(self._create_worker()),
            ]
            await asyncio.gather(*tasks)
    
    async def _validate_worker(self):
        async for msg in self.client.subscribe_queue("svc.auth.v1.validate_session", "q.auth"):
            try:
                request = auth_pb2.ValidateSessionRequest()
                request.ParseFromString(msg.data)
                response = await self.handle_validate_session(request)
                if msg.reply: await msg.respond(response.SerializeToString())
            except Exception as e: logger.error(f"Error: {e}")
    
    async def _create_worker(self):
        async for msg in self.client.subscribe_queue("svc.auth.v1.create_session", "q.auth"):
            try:
                request = auth_pb2.CreateSessionRequest()
                request.ParseFromString(msg.data)
                response = await self.handle_create_session(request)
                if msg.reply: await msg.respond(response.SerializeToString())
            except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(AuthNATSService().run())

