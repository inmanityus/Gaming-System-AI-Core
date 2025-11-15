"""Weather Manager Service - NATS Binary Messaging Server
Dynamic weather and environmental effects

Subjects: svc.weather.v1.get_weather, svc.weather.v1.set_weather, svc.weather.v1.forecast
Events: evt.weather.changed.v1
"""
import asyncio, logging, os, sys, uuid, random
from pathlib import Path
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import weather_manager_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherManagerNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="weather-manager-service"))
    
    async def handle_get_weather(self, request: weather_manager_pb2.GetWeatherRequest) -> weather_manager_pb2.GetWeatherResponse:
        response = weather_manager_pb2.GetWeatherResponse()
        response.meta.CopyFrom(request.meta)
        try:
            response.current_weather.condition_type = random.choice(["clear", "cloudy", "rain", "fog", "storm"])
            response.current_weather.intensity = random.uniform(0.3, 0.8)
            response.current_weather.temperature_celsius = random.uniform(-5.0, 25.0)
            response.current_weather.wind_speed_kmh = random.uniform(0.0, 30.0)
            response.current_weather.visibility_meters = random.uniform(100.0, 10000.0)
            response.current_weather.duration_minutes = random.randint(30, 180)
            response.last_change_ms = int(asyncio.get_event_loop().time() * 1000) - 3600000
            response.next_change_ms = int(asyncio.get_event_loop().time() * 1000) + 3600000
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Weather Manager NATS Service running on svc.weather.v1.get_weather")
            async for msg in self.client.subscribe_queue("svc.weather.v1.get_weather", "q.weather"):
                try:
                    request = weather_manager_pb2.GetWeatherRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_get_weather(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(WeatherManagerNATSService().run())

