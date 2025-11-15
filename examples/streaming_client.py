"""
Example: Streaming LLM client using NATS SDK

Demonstrates how to handle streaming token responses.
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
    """Example: Streaming LLM inference via NATS."""
    
    # Connect to NATS
    async with NATSClient("nats://localhost:4222") as client:
        print("Connected to NATS")
        
        # Create request
        request = ai_integration_pb2.LLMInferenceRequest()
        
        # Add meta
        request.meta.request_id = "req-stream-123"
        request.meta.trace_id = "trace-456"
        timestamp = Timestamp()
        timestamp.FromSeconds(int(time.time()))
        request.meta.timestamp.CopyFrom(timestamp)
        
        # Set model and input
        request.model_id = "gpt-5-pro"
        request.input.prompt = "Tell me a story about NATS"
        
        # Enable streaming
        request.params.temperature.CopyFrom(DoubleValue(value=0.8))
        request.params.max_tokens.CopyFrom(UInt32Value(value=200))
        request.params.stream.CopyFrom(BoolValue(value=True))  # ENABLE STREAMING
        
        print("Sending streaming request to svc.ai.llm.v1.infer")
        
        # Stream response chunks
        try:
            async for chunk in client.request_stream(
                subject="svc.ai.llm.v1.infer",
                request_data=request.SerializeToString(),
                chunk_type=ai_integration_pb2.LLMStreamChunk,
                timeout=30.0
            ):
                # Check for error
                if chunk.HasField("error"):
                    print(f"Error: {chunk.error.message}")
                    break
                
                # Print token delta
                if chunk.delta.HasField("output_text_delta"):
                    print(chunk.delta.output_text_delta, end="", flush=True)
                
                # Check if final chunk
                if chunk.is_final:
                    print(f"\n\nGeneration complete")
                    print(f"Generation ID: {chunk.generation_id}")
                    print(f"Finish reason: {chunk.finish_reason}")
                    print(f"Total tokens: {chunk.usage.total_tokens}")
                    break
        
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

