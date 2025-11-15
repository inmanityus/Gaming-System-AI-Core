"""Performance Mode Service - NATS Binary Messaging Server
Adaptive quality and performance management

Subjects: svc.perf.v1.adjust_mode, svc.perf.v1.get_metrics, svc.perf.v1.set_budget
Events: evt.perf.mode.changed.v1
"""
import asyncio, logging, os, sys, random
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import performance_mode_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceModeNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="performance-mode-service"))
    
    async def handle_get_metrics(self, request: performance_mode_pb2.GetMetricsRequest) -> performance_mode_pb2.GetMetricsResponse:
        response = performance_mode_pb2.GetMetricsResponse()
        response.meta.CopyFrom(request.meta)
        try:
            response.metrics.avg_fps = random.uniform(45.0, 60.0)
            response.metrics.min_fps = random.uniform(30.0, 45.0)
            response.metrics.max_fps = 60.0
            response.metrics.avg_frame_time_ms = 1000.0 / response.metrics.avg_fps
            response.metrics.frame_drops = random.randint(0, 10)
            response.metrics.cpu_usage = random.uniform(0.4, 0.8)
            response.metrics.gpu_usage = random.uniform(0.6, 0.9)
            response.metrics.memory_mb = random.randint(2000, 4000)
            response.recommended_mode = "high" if response.metrics.avg_fps > 55 else "medium"
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Performance Mode NATS Service running on svc.perf.v1.get_metrics")
            async for msg in self.client.subscribe_queue("svc.perf.v1.get_metrics", "q.perf"):
                try:
                    request = performance_mode_pb2.GetMetricsRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_get_metrics(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(PerformanceModeNATSService().run())

