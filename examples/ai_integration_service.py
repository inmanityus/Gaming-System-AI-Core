"""
Example: AI Integration Service using NATS SDK

Demonstrates how to implement a NATS-based service that responds to requests.
"""

import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../generated"))

from sdk import NATSClient
import ai_integration_pb2
import common_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import time
import uuid


async def handle_llm_inference(request: ai_integration_pb2.LLMInferenceRequest) -> ai_integration_pb2.LLMInferenceResponse:
    """
    Process LLM inference request.
    
    In production, this would call actual LLM service.
    For demo, we just echo back.
    """
    response = ai_integration_pb2.LLMInferenceResponse()
    
    # Copy meta
    response.meta.CopyFrom(request.meta)
    
    # Generate response
    response.generation_id = f"gen-{uuid.uuid4().hex[:8]}"
    
    # Echo input as output (demo only)
    which_input = request.WhichOneof("input")
    if which_input == "prompt":
        response.output_text = f"Response to: {request.prompt}"
    elif which_input == "chat_messages":
        # Chat messages
        for msg in request.chat_messages.messages:
            response_msg = response.chat_messages.messages.add()
            response_msg.CopyFrom(msg)
        # Add assistant response
        assistant_msg = response.chat_messages.messages.add()
        assistant_msg.role = ai_integration_pb2.ChatMessage.ASSISTANT
        assistant_msg.content = "This is a demo response"
    else:
        response.output_text = "No input provided"
    
    response.finish_reason = "stop"
    
    # Set token usage
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 20
    response.usage.total_tokens = 30
    
    return response


async def main():
    """Run AI Integration service."""
    
    # Connect to NATS
    async with NATSClient("nats://localhost:4222") as client:
        print("AI Integration Service started")
        print("Listening on svc.ai.llm.v1.infer with queue group q.ai.llm.infer")
        
        # Subscribe to subject with queue group (load balanced)
        async for msg in client.subscribe_queue(
            subject="svc.ai.llm.v1.infer",
            queue="q.ai.llm.infer"
        ):
            try:
                # Deserialize request
                request = ai_integration_pb2.LLMInferenceRequest()
                request.ParseFromString(msg.data)
                
                print(f"Received request: {request.meta.request_id}")
                
                # Process request
                response = await handle_llm_inference(request)
                
                # Send response
                await msg.respond(response.SerializeToString())
                
                print(f"Sent response: {response.generation_id}")
            
            except Exception as e:
                print(f"Error processing request: {e}")
                
                # Send error response
                error_response = ai_integration_pb2.LLMInferenceResponse()
                error_response.meta.CopyFrom(request.meta)
                error_response.error.code = common_pb2.Error.INTERNAL
                error_response.error.message = str(e)
                
                await msg.respond(error_response.SerializeToString())


if __name__ == "__main__":
    asyncio.run(main())

