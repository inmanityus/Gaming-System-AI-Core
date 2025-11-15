"""Settings Service - NATS Binary Messaging Server
Player settings and preferences management

Subjects: svc.settings.v1.get, svc.settings.v1.update, svc.settings.v1.reset
Events: evt.settings.changed.v1
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
import settings_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SettingsNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="settings-service"))
        self.player_settings: Dict[str, Dict[str, settings_pb2.Setting]] = {}
    
    async def handle_get(self, request: settings_pb2.GetRequest) -> settings_pb2.GetResponse:
        response = settings_pb2.GetResponse()
        response.meta.CopyFrom(request.meta)
        try:
            settings = self.player_settings.get(request.player_id, {})
            if request.setting_keys:
                for key in request.setting_keys:
                    if key in settings:
                        setting = response.settings.add()
                        setting.CopyFrom(settings[key])
            else:
                for setting in settings.values():
                    new_setting = response.settings.add()
                    new_setting.CopyFrom(setting)
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_update(self, request: settings_pb2.UpdateRequest) -> settings_pb2.UpdateResponse:
        response = settings_pb2.UpdateResponse()
        response.meta.CopyFrom(request.meta)
        try:
            if request.player_id not in self.player_settings:
                self.player_settings[request.player_id] = {}
            
            player_settings = self.player_settings[request.player_id]
            
            if request.merge:
                for setting in request.settings:
                    player_settings[setting.key] = setting
            else:
                player_settings.clear()
                for setting in request.settings:
                    player_settings[setting.key] = setting
            
            response.updated_count = len(request.settings)
            response.updated_keys.extend([s.key for s in request.settings])
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Settings NATS Service running")
            tasks = [
                asyncio.create_task(self._get_worker()),
                asyncio.create_task(self._update_worker()),
            ]
            await asyncio.gather(*tasks)
    
    async def _get_worker(self):
        async for msg in self.client.subscribe_queue("svc.settings.v1.get", "q.settings"):
            try:
                request = settings_pb2.GetRequest()
                request.ParseFromString(msg.data)
                response = await self.handle_get(request)
                if msg.reply: await msg.respond(response.SerializeToString())
            except Exception as e: logger.error(f"Error: {e}")
    
    async def _update_worker(self):
        async for msg in self.client.subscribe_queue("svc.settings.v1.update", "q.settings"):
            try:
                request = settings_pb2.UpdateRequest()
                request.ParseFromString(msg.data)
                response = await self.handle_update(request)
                if msg.reply: await msg.respond(response.SerializeToString())
            except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(SettingsNATSService().run())

