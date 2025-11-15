"""
Example: AI Integration Client using NATS SDK

Demonstrates how to call LLM inference service via NATS.
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
from google.protobuf.wrappers_pb2 import DoubleValue, UInt32Value, BoolValue
from google.protobuf.timestamp_pb2 import Timestamp
import time


async def main():
    """Example: LLM inference via NATS."""
    
    # Connect to NATS
    async with NATSClient("nats://localhost:4222") as client:
        print("Connected to NATS")
        
        # Create request
        request = ai_integration_pb2.LLMInferenceRequest()
        
        # Add meta
        request.meta.request_id = "req-123"
        request.meta.trace_id = "trace-456"
        request.meta.client_id = "example-client"
        request.meta.user_id = "user-789"
        request.meta.idempotency_key = "idem-unique-key"
        
        timestamp = Timestamp()
        timestamp.FromSeconds(int(time.time()))
        request.meta.timestamp.CopyFrom(timestamp)
        
        # Set model and input (using oneof field)
        request.model_id = "gpt-5-pro"
        request.prompt = "Tell me about NATS messaging"
        
        # Set generation parameters with presence detection
        request.params.temperature.CopyFrom(DoubleValue(value=0.7))
        request.params.max_tokens.CopyFrom(UInt32Value(value=100))
        request.params.stream.CopyFrom(BoolValue(value=False))
        
        print("Sending request to svc.ai.llm.v1.infer")
        
        # Send request and await response
        try:
            response = await client.request(
                subject="svc.ai.llm.v1.infer",
                request_data=request.SerializeToString(),
                response_type=ai_integration_pb2.LLMInferenceResponse,
                timeout=10.0
            )
            
            print(f"Generation ID: {response.generation_id}")
            print(f"Output: {response.output_text}")
            print(f"Tokens used: {response.usage.total_tokens}")
            print(f"Finish reason: {response.finish_reason}")
            
            if response.HasField("error"):
                print(f"Error: {response.error.message}")
        
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

