"""
AI Integration Service - NATS Binary Messaging Server
Production-grade NATS-based service for LLM inference

Dual-stack implementation:
- HTTP REST (existing, for backward compatibility)
- NATS Binary (new, for optimal performance)

Subjects:
  svc.ai.llm.v1.infer - LLM inference RPC (queue group: q.ai.llm.infer)
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
import ai_integration_pb2
import common_pb2

# Import from absolute path since running as script
try:
    from services.ai_integration.llm_client import LLMClient
    from services.ai_integration.context_manager import ContextManager
except ImportError:
    # Fallback for relative import
    from .llm_client import LLMClient
    from .context_manager import ContextManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIIntegrationNATSService:
    """NATS-based AI Integration service."""
    
    def __init__(self):
        self.nats_url = os.getenv(
            "NATS_URL",
            "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"
        )
        self.client = NATSClient(NATSConfig(
            servers=[self.nats_url],
            name="ai-integration-service"
        ))
        self.llm_client = LLMClient()
        self.context_manager = ContextManager()
    
    async def handle_llm_inference(
        self,
        request: ai_integration_pb2.LLMInferenceRequest
    ) -> ai_integration_pb2.LLMInferenceResponse:
        """
        Handle LLM inference request.
        
        Processes protobuf request and returns protobuf response.
        """
        logger.info(f"Processing LLM inference request: {request.meta.request_id}")
        
        response = ai_integration_pb2.LLMInferenceResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            # Extract parameters
            model_id = request.model_id
            
            # Get input (prompt or chat messages)
            if request.input.HasField("prompt"):
                prompt = request.input.prompt
                messages = None
            else:
                messages = []
                for msg in request.input.chat_messages.messages:
                    messages.append({
                        "role": ai_integration_pb2.ChatMessage.Role.Name(msg.role).lower(),
                        "content": msg.content,
                        "name": msg.name if msg.name else None
                    })
                prompt = None
            
            # Extract generation parameters (with presence detection)
            params = {}
            if request.params.HasField("temperature"):
                params["temperature"] = request.params.temperature.value
            if request.params.HasField("top_p"):
                params["top_p"] = request.params.top_p.value
            if request.params.HasField("max_tokens"):
                params["max_tokens"] = request.params.max_tokens.value
            if request.params.HasField("top_k"):
                params["top_k"] = request.params.top_k.value
            if request.params.HasField("presence_penalty"):
                params["presence_penalty"] = request.params.presence_penalty.value
            if request.params.HasField("frequency_penalty"):
                params["frequency_penalty"] = request.params.frequency_penalty.value
            if request.params.stop:
                params["stop"] = list(request.params.stop)
            
            # Check if streaming requested
            is_streaming = False
            if request.params.HasField("stream"):
                is_streaming = request.params.stream.value
            
            if is_streaming:
                # Streaming not supported in request/reply - return error
                response.error.code = common_pb2.Error.UNIMPLEMENTED
                response.error.message = "Streaming not supported via request/reply. Use pub/sub streaming pattern."
                return response
            
            # Call LLM service
            if prompt:
                result = await self.llm_client.generate(
                    model_id=model_id,
                    prompt=prompt,
                    **params
                )
            else:
                result = await self.llm_client.chat(
                    model_id=model_id,
                    messages=messages,
                    **params
                )
            
            # Build response
            response.generation_id = result.get("id", "gen-unknown")
            
            if "text" in result:
                response.output_text = result["text"]
            elif "messages" in result:
                # Convert messages to protobuf
                for msg in result["messages"]:
                    pb_msg = response.chat_messages.messages.add()
                    role_map = {
                        "system": ai_integration_pb2.ChatMessage.SYSTEM,
                        "user": ai_integration_pb2.ChatMessage.USER,
                        "assistant": ai_integration_pb2.ChatMessage.ASSISTANT,
                        "tool": ai_integration_pb2.ChatMessage.TOOL,
                    }
                    pb_msg.role = role_map.get(msg["role"], ai_integration_pb2.ChatMessage.ROLE_UNSPECIFIED)
                    pb_msg.content = msg["content"]
                    if "name" in msg:
                        pb_msg.name = msg["name"]
            
            response.finish_reason = result.get("finish_reason", "stop")
            
            # Set token usage
            usage = result.get("usage", {})
            response.usage.prompt_tokens = usage.get("prompt_tokens", 0)
            response.usage.completion_tokens = usage.get("completion_tokens", 0)
            response.usage.total_tokens = usage.get("total_tokens", 0)
            
            logger.info(f"Generated response: {response.generation_id}")
            return response
        
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        """Run NATS service worker."""
        logger.info("Starting AI Integration NATS Service")
        logger.info(f"Connecting to NATS at {self.nats_url}")
        
        async with self.client:
            logger.info("Connected to NATS successfully")
            logger.info("Subscribing to svc.ai.llm.v1.infer with queue group q.ai.llm.infer")
            
            # Subscribe as queue group worker (load balanced)
            async for msg in self.client.subscribe_queue(
                subject="svc.ai.llm.v1.infer",
                queue="q.ai.llm.infer"
            ):
                try:
                    # Deserialize request
                    request = ai_integration_pb2.LLMInferenceRequest()
                    request.ParseFromString(msg.data)
                    
                    logger.info(f"Received request: {request.meta.request_id}")
                    
                    # Process request
                    response = await self.handle_llm_inference(request)
                    
                    # Send response
                    if msg.reply:
                        await msg.respond(response.SerializeToString())
                        logger.info(f"Sent response: {response.generation_id}")
                    else:
                        logger.warning("No reply subject - cannot send response")
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    
                    # Send error response
                    if msg.reply:
                        error_response = ai_integration_pb2.LLMInferenceResponse()
                        if 'request' in locals():
                            error_response.meta.CopyFrom(request.meta)
                        error_response.error.code = common_pb2.Error.INTERNAL
                        error_response.error.message = str(e)
                        
                        try:
                            await msg.respond(error_response.SerializeToString())
                        except Exception as respond_error:
                            logger.error(f"Failed to send error response: {respond_error}")


async def main():
    """Main entry point."""
    service = AIIntegrationNATSService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

