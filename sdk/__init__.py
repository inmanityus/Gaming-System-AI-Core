"""
NATS Binary Messaging SDK for Gaming System AI Core

Production-ready Python SDK for NATS-based microservices communication.

Usage:
    from sdk import NATSClient
    
    async with NATSClient("nats://localhost:4222") as client:
        # Request/reply
        response = await client.request(
            "svc.ai.llm.v1.infer",
            request_proto,
            response_type=LLMInferenceResponse,
            timeout=5.0
        )
        
        # Pub/sub
        await client.publish(
            "evt.quest.generated.v1",
            event_proto
        )
        
        # Queue group worker
        async for msg in client.subscribe_queue(
            "svc.quest.v1.generate",
            queue="q.quest"
        ):
            # Process request
            response = process_request(msg)
            await msg.respond(response)
"""

from .nats_client import NATSClient, NATSConfig
from .errors import (
    ServiceTimeoutError,
    ServiceUnavailableError,
    RetryExhaustedError,
    CircuitOpenError
)
from .circuit_breaker import AsyncCircuitBreaker
from .codecs import encode_protobuf, decode_protobuf
from .otel import get_tracer, inject_headers, extract_context

__version__ = "1.0.0"

__all__ = [
    "NATSClient",
    "NATSConfig",
    "ServiceTimeoutError",
    "ServiceUnavailableError",
    "RetryExhaustedError",
    "CircuitOpenError",
    "AsyncCircuitBreaker",
    "encode_protobuf",
    "decode_protobuf",
    "get_tracer",
    "inject_headers",
    "extract_context",
]
