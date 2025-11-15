"""Capability Registry Service - NATS Binary Messaging Server
Tracks service capabilities and availability for dynamic routing

Subjects: svc.capability.v1.register, svc.capability.v1.query, svc.capability.v1.heartbeat
Events: evt.capability.registered.v1, evt.capability.removed.v1
"""
import asyncio, logging, os, sys, uuid, time
from pathlib import Path
from typing import Dict, List
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import capability_registry_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CapabilityRegistryNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="capability-registry-service"))
        self.registrations: Dict[str, capability_registry_pb2.ServiceCapability] = {}
    
    async def handle_register(self, request: capability_registry_pb2.RegisterRequest) -> capability_registry_pb2.RegisterResponse:
        response = capability_registry_pb2.RegisterResponse()
        response.meta.CopyFrom(request.meta)
        try:
            reg_id = f"reg-{uuid.uuid4().hex[:12]}"
            
            # Store registration
            svc_cap = capability_registry_pb2.ServiceCapability()
            svc_cap.service_id = request.service_id
            svc_cap.registration_id = reg_id
            svc_cap.capabilities.extend(request.capabilities)
            svc_cap.is_online = True
            svc_cap.last_heartbeat_ms = int(time.time() * 1000)
            for k, v in request.metadata.items(): svc_cap.metadata[k] = v
            
            self.registrations[reg_id] = svc_cap
            
            response.success = True
            response.registration_id = reg_id
            response.expires_at_ms = int(time.time() * 1000) + 300000  # 5 minutes
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_query(self, request: capability_registry_pb2.QueryRequest) -> capability_registry_pb2.QueryResponse:
        response = capability_registry_pb2.QueryResponse()
        response.meta.CopyFrom(request.meta)
        try:
            for svc_cap in self.registrations.values():
                if request.capability_type:
                    # Filter by capability type
                    has_cap = any(c.capability_type == request.capability_type for c in svc_cap.capabilities)
                    if not has_cap: continue
                
                if not request.include_offline and not svc_cap.is_online:
                    continue
                
                result = response.services.add()
                result.CopyFrom(svc_cap)
            
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Capability Registry NATS Service running")
            tasks = [
                asyncio.create_task(self._register_worker()),
                asyncio.create_task(self._query_worker()),
            ]
            await asyncio.gather(*tasks)
    
    async def _register_worker(self):
        async for msg in self.client.subscribe_queue("svc.capability.v1.register", "q.capability"):
            try:
                request = capability_registry_pb2.RegisterRequest()
                request.ParseFromString(msg.data)
                response = await self.handle_register(request)
                if msg.reply: await msg.respond(response.SerializeToString())
            except Exception as e: logger.error(f"Error: {e}")
    
    async def _query_worker(self):
        async for msg in self.client.subscribe_queue("svc.capability.v1.query", "q.capability"):
            try:
                request = capability_registry_pb2.QueryRequest()
                request.ParseFromString(msg.data)
                response = await self.handle_query(request)
                if msg.reply: await msg.respond(response.SerializeToString())
            except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(CapabilityRegistryNATSService().run())

