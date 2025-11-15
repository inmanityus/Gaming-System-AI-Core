"""Time Manager Service - NATS Binary Messaging Server
Game time, day/night cycles, event scheduling

Subjects: svc.time.v1.get_time, svc.time.v1.set_time, svc.time.v1.schedule_event
Events: evt.time.hour.changed.v1, evt.time.day.changed.v1
"""
import asyncio, logging, os, sys, uuid
from pathlib import Path
import time as pytime
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
import time_manager_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeManagerNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="time-manager-service"))
        self.game_time_offset = 0  # Offset from real time
    
    async def handle_get_time(self, request: time_manager_pb2.GetTimeRequest) -> time_manager_pb2.GetTimeResponse:
        response = time_manager_pb2.GetTimeResponse()
        response.meta.CopyFrom(request.meta)
        try:
            # Mock game time
            response.game_time.year = 2025
            response.game_time.month = 11
            response.game_time.day = 13
            response.game_time.hour = 23
            response.game_time.minute = 30
            response.game_time.second = 0
            response.game_time.time_of_day = "night"
            response.game_time.moon_phase = "full"
            response.game_time.season = "fall"
            response.real_time_ms = int(pytime.time() * 1000)
            response.time_scale = 1.0
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Time Manager NATS Service running on svc.time.v1.get_time")
            async for msg in self.client.subscribe_queue("svc.time.v1.get_time", "q.time"):
                try:
                    request = time_manager_pb2.GetTimeRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_get_time(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(TimeManagerNATSService().run())

