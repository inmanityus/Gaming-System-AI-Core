"""
Model Management Service - NATS Binary Messaging Server
Manages AI model registry, selection, and configuration

Subjects:
  svc.ai.model.v1.list - List available models
  svc.ai.model.v1.get - Get specific model info
  svc.ai.model.v1.select - Select/activate model
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add SDK and generated proto paths
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path))
sys.path.insert(0, str(generated_path))

from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import model_mgmt_pb2
import common_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mock model registry (in production, this would be a database)
MODELS = [
    {
        "model_id": "gpt-5-pro",
        "name": "GPT-5 Pro",
        "provider": "openai",
        "family": "gpt",
        "modality": "chat",
        "is_default": True,
        "metadata": {"context_length": "128000", "quality": "highest"}
    },
    {
        "model_id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "google",
        "family": "gemini",
        "modality": "chat",
        "is_default": False,
        "metadata": {"context_length": "1000000", "quality": "highest"}
    },
    {
        "model_id": "claude-4.5-sonnet",
        "name": "Claude 4.5 Sonnet",
        "provider": "anthropic",
        "family": "claude",
        "modality": "chat",
        "is_default": False,
        "metadata": {"context_length": "200000", "quality": "highest"}
    },
]


class ModelManagementNATSService:
    """NATS-based Model Management service."""
    
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(
            servers=[self.nats_url],
            name="model-management-service"
        ))
        self.selected_model = "gpt-5-pro"  # Default
    
    async def handle_list_models(
        self,
        request: model_mgmt_pb2.ListModelsRequest
    ) -> model_mgmt_pb2.ListModelsResponse:
        """List available models with optional filtering."""
        logger.info(f"Listing models: {request.meta.request_id}")
        
        response = model_mgmt_pb2.ListModelsResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Filter models
            filtered_models = MODELS
            
            if request.modality_filter:
                filtered_models = [
                    m for m in filtered_models
                    if m["modality"] == request.modality_filter
                ]
            
            if request.provider_filter:
                filtered_models = [
                    m for m in filtered_models
                    if m["provider"] == request.provider_filter
                ]
            
            # Build response
            for model in filtered_models:
                model_info = response.models.add()
                model_info.model_id = model["model_id"]
                model_info.name = model["name"]
                model_info.provider = model["provider"]
                model_info.family = model["family"]
                model_info.modality = model["modality"]
                model_info.is_default = model["is_default"]
                for k, v in model["metadata"].items():
                    model_info.metadata[k] = v
            
            logger.info(f"Returning {len(filtered_models)} models")
            return response
        
        except Exception as e:
            logger.error(f"Error listing models: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_get_model(
        self,
        request: model_mgmt_pb2.GetModelRequest
    ) -> model_mgmt_pb2.GetModelResponse:
        """Get specific model information."""
        logger.info(f"Getting model {request.model_id}: {request.meta.request_id}")
        
        response = model_mgmt_pb2.GetModelResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Find model
            model = next((m for m in MODELS if m["model_id"] == request.model_id), None)
            
            if not model:
                response.error.code = common_pb2.Error.NOT_FOUND
                response.error.message = f"Model not found: {request.model_id}"
                return response
            
            # Build response
            response.model.model_id = model["model_id"]
            response.model.name = model["name"]
            response.model.provider = model["provider"]
            response.model.family = model["family"]
            response.model.modality = model["modality"]
            response.model.is_default = model["is_default"]
            for k, v in model["metadata"].items():
                response.model.metadata[k] = v
            
            logger.info(f"Returning model: {model['name']}")
            return response
        
        except Exception as e:
            logger.error(f"Error getting model: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_select_model(
        self,
        request: model_mgmt_pb2.SelectModelRequest
    ) -> model_mgmt_pb2.SelectModelResponse:
        """Select/activate a model."""
        logger.info(f"Selecting model {request.model_id}: {request.meta.request_id}")
        
        response = model_mgmt_pb2.SelectModelResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Verify model exists
            model = next((m for m in MODELS if m["model_id"] == request.model_id), None)
            
            if not model:
                response.error.code = common_pb2.Error.NOT_FOUND
                response.error.message = f"Model not found: {request.model_id}"
                response.ok = False
                return response
            
            # Select model
            self.selected_model = request.model_id
            response.ok = True
            
            logger.info(f"Model selected: {model['name']}")
            return response
        
        except Exception as e:
            logger.error(f"Error selecting model: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            response.ok = False
            return response
    
    async def run(self):
        """Run NATS service workers for all operations."""
        logger.info("Starting Model Management NATS Service")
        logger.info(f"Connecting to NATS at {self.nats_url}")
        
        async with self.client:
            logger.info("Connected to NATS successfully")
            
            # Start worker tasks for each operation
            tasks = [
                asyncio.create_task(self._list_worker()),
                asyncio.create_task(self._get_worker()),
                asyncio.create_task(self._select_worker()),
            ]
            
            # Wait for all workers
            await asyncio.gather(*tasks)
    
    async def _list_worker(self):
        """Worker for list models operation."""
        logger.info("Starting list models worker on svc.ai.model.v1.list")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.ai.model.v1.list",
            queue="q.model"
        ):
            try:
                request = model_mgmt_pb2.ListModelsRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_list_models(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in list worker: {e}", exc_info=True)
    
    async def _get_worker(self):
        """Worker for get model operation."""
        logger.info("Starting get model worker on svc.ai.model.v1.get")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.ai.model.v1.get",
            queue="q.model"
        ):
            try:
                request = model_mgmt_pb2.GetModelRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_get_model(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in get worker: {e}", exc_info=True)
    
    async def _select_worker(self):
        """Worker for select model operation."""
        logger.info("Starting select model worker on svc.ai.model.v1.select")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.ai.model.v1.select",
            queue="q.model"
        ):
            try:
                request = model_mgmt_pb2.SelectModelRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_select_model(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in select worker: {e}", exc_info=True)


async def main():
    """Main entry point."""
    service = ModelManagementNATSService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

