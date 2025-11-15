"""
HTTP→NATS Gateway Service
Translates HTTP/JSON requests to NATS/Protobuf messages for gradual migration.

Purpose:
- Allows existing HTTP clients to communicate with NATS-based services
- Enables zero-downtime migration from HTTP to NATS
- Provides request/response translation and error mapping

Architecture:
- FastAPI HTTP server
- NATS client for backend communication
- Protobuf serialization/deserialization
- Idempotency key propagation
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import nats
from nats.aio.errors import ErrNoServers, ErrTimeout
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from google.protobuf import json_format
from google.protobuf.message import Message

# Request size limit (10MB)
MAX_REQUEST_SIZE = 10 * 1024 * 1024

# SSE concurrency limit per worker
MAX_SSE_CONCURRENT = 100
current_sse_count = 0

# Add generated proto path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../generated"))

# Import generated protobuf modules
import common_pb2
import ai_integration_pb2
import model_mgmt_pb2
import state_manager_pb2
import quest_pb2
import npc_behavior_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NATS connection
from typing import Any
nats_client: Any = None

# Route mapping: HTTP path -> NATS subject + protobuf types
ROUTE_MAP = {
    # AI Integration
    "/ai/llm/infer": {
        "subject": "svc.ai.llm.v1.infer",
        "request_type": ai_integration_pb2.LLMInferenceRequest,
        "response_type": ai_integration_pb2.LLMInferenceResponse,
        "stream_response_type": ai_integration_pb2.LLMStreamChunk,
    },
    
    # Model Management
    "/ai/models": {
        "subject": "svc.ai.model.v1.list",
        "request_type": model_mgmt_pb2.ListModelsRequest,
        "response_type": model_mgmt_pb2.ListModelsResponse,
    },
    "/ai/models/{model_id}": {
        "subject": "svc.ai.model.v1.get",
        "request_type": model_mgmt_pb2.GetModelRequest,
        "response_type": model_mgmt_pb2.GetModelResponse,
    },
    "/ai/models/{model_id}/select": {
        "subject": "svc.ai.model.v1.select",
        "request_type": model_mgmt_pb2.SelectModelRequest,
        "response_type": model_mgmt_pb2.SelectModelResponse,
    },
    
    # State Manager
    "/state/update": {
        "subject": "svc.state.manager.v1.update",
        "request_type": state_manager_pb2.GameStateUpdate,
        "response_type": state_manager_pb2.GameStateUpdateAck,
    },
    "/state/get": {
        "subject": "svc.state.manager.v1.get",
        "request_type": state_manager_pb2.GetStateRequest,
        "response_type": state_manager_pb2.GetStateResponse,
    },
    
    # Quest System
    "/quest/generate": {
        "subject": "svc.quest.v1.generate",
        "request_type": quest_pb2.QuestGenerationRequest,
        "response_type": quest_pb2.QuestGenerationResponse,
    },
    
    # NPC Behavior
    "/npc/behavior": {
        "subject": "svc.npc.behavior.v1.plan",
        "request_type": npc_behavior_pb2.BehaviorRequest,
        "response_type": npc_behavior_pb2.BehaviorResponse,
    },
}


def json_to_proto(json_data: Dict[str, Any], proto_class: type) -> Message:
    """Convert JSON to protobuf message."""
    try:
        message = proto_class()
        json_format.ParseDict(json_data, message, ignore_unknown_fields=True)
        return message
    except Exception as e:
        logger.error(f"Failed to parse JSON to protobuf: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")


def proto_to_json(proto_message: Message) -> Dict[str, Any]:
    """Convert protobuf message to JSON."""
    try:
        return json_format.MessageToDict(
            proto_message,
            preserving_proto_field_name=True,
            including_default_value_fields=False
        )
    except Exception as e:
        logger.error(f"Failed to convert protobuf to JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Response serialization error: {str(e)}")


def create_meta(request: Request, idempotency_key: Optional[str] = None) -> common_pb2.Meta:
    """Create Meta message from HTTP request."""
    import uuid
    from google.protobuf.timestamp_pb2 import Timestamp
    import time
    
    meta = common_pb2.Meta()
    meta.request_id = str(uuid.uuid4())
    meta.trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    meta.client_id = request.headers.get("X-Client-ID", "http-gateway")
    meta.user_id = request.headers.get("X-User-ID", "")
    meta.tenant_id = request.headers.get("X-Tenant-ID", "")
    
    timestamp = Timestamp()
    timestamp.FromSeconds(int(time.time()))
    meta.timestamp.CopyFrom(timestamp)
    
    if idempotency_key:
        meta.idempotency_key = idempotency_key
    
    # Copy custom headers as labels
    for key, value in request.headers.items():
        if key.startswith("X-Custom-"):
            label_key = key.replace("X-Custom-", "").lower()
            meta.labels[label_key] = value
    
    return meta


def map_proto_error_to_http(error: common_pb2.Error) -> int:
    """Map protobuf error code to HTTP status code."""
    error_map = {
        common_pb2.Error.UNKNOWN: 500,
        common_pb2.Error.INVALID_ARGUMENT: 400,
        common_pb2.Error.NOT_FOUND: 404,
        common_pb2.Error.PERMISSION_DENIED: 403,
        common_pb2.Error.UNAUTHENTICATED: 401,
        common_pb2.Error.CONFLICT: 409,
        common_pb2.Error.RESOURCE_EXHAUSTED: 429,
        common_pb2.Error.FAILED_PRECONDITION: 412,
        common_pb2.Error.ABORTED: 409,
        common_pb2.Error.OUT_OF_RANGE: 400,
        common_pb2.Error.UNIMPLEMENTED: 501,
        common_pb2.Error.INTERNAL: 500,
        common_pb2.Error.UNAVAILABLE: 503,
        common_pb2.Error.DEADLINE_EXCEEDED: 504,
    }
    return error_map.get(error.code, 500)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global nats_client
    
    # Startup: Connect to NATS
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    logger.info(f"Connecting to NATS at {nats_url}")
    
    # Connection callbacks for observability
    async def disconnected_cb():
        logger.warning("NATS disconnected - attempting reconnect")
    
    async def reconnected_cb():
        logger.info("NATS reconnected successfully")
    
    async def error_cb(e):
        logger.error(f"NATS error: {e}")
    
    async def closed_cb():
        logger.info("NATS connection closed")
    
    try:
        nats_client = await nats.connect(
            nats_url,
            max_reconnect_attempts=-1,  # Infinite reconnects
            reconnect_time_wait=2,
            ping_interval=20,
            max_outstanding_pings=3,
            disconnected_cb=disconnected_cb,
            reconnected_cb=reconnected_cb,
            error_cb=error_cb,
            closed_cb=closed_cb,
            # TLS if configured
            tls=None if not os.getenv("NATS_TLS_CERT") else {
                "cert": os.getenv("NATS_TLS_CERT"),
                "key": os.getenv("NATS_TLS_KEY"),
                "ca": os.getenv("NATS_TLS_CA"),
            }
        )
        logger.info("Connected to NATS successfully")
    except Exception as e:
        logger.error(f"Failed to connect to NATS: {e}")
        raise
    
    yield
    
    # Shutdown: Drain then close NATS connection
    if nats_client:
        try:
            await nats_client.drain()
            logger.info("NATS connection drained")
        except Exception as e:
            logger.error(f"Error draining NATS connection: {e}")
        
        await nats_client.close()
        logger.info("NATS connection closed")


app = FastAPI(
    title="HTTP→NATS Gateway",
    description="Translates HTTP/JSON to NATS/Protobuf for gradual migration",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Liveness check - process is running."""
    return {"status": "alive"}


@app.get("/ready")
async def readiness_check():
    """Readiness check - can serve traffic."""
    if not nats_client or not nats_client.is_connected:
        raise HTTPException(status_code=503, detail="NATS not connected")
    
    return {
        "status": "ready",
        "nats_connected": True,
        "routes": len(ROUTE_MAP)
    }


@app.post("/{full_path:path}")
async def proxy_request(full_path: str, request: Request):
    """
    Proxy HTTP request to NATS.
    
    1. Match HTTP path to NATS subject + protobuf types
    2. Convert JSON body to protobuf request
    3. Send to NATS and await response
    4. Convert protobuf response to JSON
    5. Map errors to HTTP status codes
    """
    if not nats_client or not nats_client.is_connected:
        raise HTTPException(status_code=503, detail="NATS not connected")
    
    # Find route mapping
    route_key = f"/{full_path}"
    route_config = ROUTE_MAP.get(route_key)
    
    if not route_config:
        raise HTTPException(status_code=404, detail=f"Route not found: {route_key}")
    
    try:
        # Parse HTTP JSON body
        body = await request.json()
        
        # Extract idempotency key if present
        idempotency_key = body.pop("idempotency_key", None)
        
        # Create Meta
        meta = create_meta(request, idempotency_key)
        
        # Add meta to request body
        body["meta"] = proto_to_json(meta)
        
        # Convert JSON to protobuf
        proto_request = json_to_proto(body, route_config["request_type"])
        
        # Serialize to bytes
        request_bytes = proto_request.SerializeToString()
        
        # Check if streaming is requested
        is_streaming = False
        if hasattr(proto_request, "params") and hasattr(proto_request.params, "stream"):
            if proto_request.params.HasField("stream"):
                is_streaming = proto_request.params.stream.value
        
        # Check SSE concurrency limit
        if is_streaming:
            global current_sse_count
            if current_sse_count >= MAX_SSE_CONCURRENT:
                raise HTTPException(
                    status_code=429,
                    detail="Too many concurrent streaming requests",
                    headers={"Retry-After": "10"}
                )
            current_sse_count += 1
        
        # Send to NATS
        subject = route_config["subject"]
        timeout_seconds = float(os.getenv("NATS_TIMEOUT_SECONDS", "30"))
        
        try:
            if is_streaming:
                # Streaming response
                return await handle_streaming_response(
                    subject,
                    request_bytes,
                    route_config["stream_response_type"],
                    timeout_seconds
                )
            else:
                # Single response
                logger.info(f"Sending request to {subject}")
                response_msg = await nats_client.request(
                    subject,
                    request_bytes,
                    timeout=timeout_seconds
                )
                
                # Deserialize protobuf response
                proto_response = route_config["response_type"]()
                proto_response.ParseFromString(response_msg.data)
                
                # Check for error in response
                if proto_response.HasField("error") and proto_response.error.code != common_pb2.Error.UNKNOWN:
                    http_status = map_proto_error_to_http(proto_response.error)
                    return JSONResponse(
                        status_code=http_status,
                        content={
                            "error": {
                                "code": common_pb2.Error.Code.Name(proto_response.error.code),
                                "message": proto_response.error.message,
                                "details": dict(proto_response.error.details)
                            }
                        }
                    )
                
                # Convert to JSON and return
                json_response = proto_to_json(proto_response)
                return JSONResponse(content=json_response)
        
        except ErrTimeout:
            logger.error(f"NATS timeout waiting for response from {subject}")
            raise HTTPException(status_code=504, detail="Gateway timeout")
        except ErrNoServers:
            logger.error(f"No NATS responders for subject {subject}")
            raise HTTPException(
                status_code=503,
                detail="Service unavailable",
                headers={"Retry-After": "5"}
            )
        finally:
            if is_streaming:
                current_sse_count -= 1
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout waiting for response from {subject}")
        raise HTTPException(status_code=504, detail="Gateway timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def handle_streaming_response(subject: str, request_bytes: bytes, chunk_type: type, timeout: float):
    """
    Handle streaming response from NATS.
    
    For LLM token streaming (production-grade):
    1. Create unique inbox and subscribe
    2. Flush to ensure subscription is registered server-side
    3. Send request to NATS with reply inbox
    4. Prime read: wait for first chunk before sending HTTP headers (enables proper error codes)
    5. Stream chunks with bounded queue and backpressure handling
    6. Clean up subscription on client disconnect or completion
    """
    async def generate_stream():
        # Create unique reply inbox
        reply_inbox = nats_client.new_inbox()
        
        # Subscribe to reply inbox with bounded pending limits
        sub = await nats_client.subscribe(
            reply_inbox,
            pending_msgs_limit=256,  # Prevent slow consumer OOM
            pending_bytes_limit=1024 * 1024  # 1MB max buffered
        )
        
        # Bounded queue for backpressure between NATS and HTTP
        queue = asyncio.Queue(maxsize=50)
        is_complete = asyncio.Event()
        error_holder = []
        
        async def nats_reader():
            """Read from NATS subscription and feed queue."""
            try:
                async for msg in sub.messages:
                    chunk = chunk_type()
                    chunk.ParseFromString(msg.data)
                    
                    # Check for error in chunk
                    if chunk.HasField("error") and chunk.error.code != common_pb2.Error.UNKNOWN:
                        error_holder.append(chunk.error)
                        is_complete.set()
                        break
                    
                    # Put in queue with timeout (handle slow client)
                    try:
                        await asyncio.wait_for(queue.put(chunk), timeout=5.0)
                    except asyncio.TimeoutError:
                        # Client too slow - terminate stream
                        logger.warning("SSE client too slow, terminating stream")
                        is_complete.set()
                        break
                    
                    # Check if final chunk
                    if chunk.is_final:
                        is_complete.set()
                        break
            except Exception as e:
                logger.error(f"NATS reader error: {e}")
                error_holder.append(e)
                is_complete.set()
            finally:
                # Signal completion
                await queue.put(None)
        
        try:
            # CRITICAL: Flush subscription before publishing to avoid race
            await nats_client.flush()
            
            # Send request with reply inbox
            await nats_client.publish(subject, request_bytes, reply=reply_inbox)
            
            # Start NATS reader task
            reader_task = asyncio.create_task(nats_reader())
            
            # Prime read: Get first chunk before sending HTTP headers
            try:
                first_chunk = await asyncio.wait_for(queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                reader_task.cancel()
                raise HTTPException(status_code=504, detail="Streaming request timeout")
            
            if first_chunk is None:
                # Stream ended before first chunk
                if error_holder:
                    error = error_holder[0]
                    if isinstance(error, Exception):
                        raise HTTPException(status_code=500, detail=str(error))
                    else:
                        http_status = map_proto_error_to_http(error)
                        raise HTTPException(status_code=http_status, detail=error.message)
                raise HTTPException(status_code=500, detail="Stream ended prematurely")
            
            # Check if first chunk is an error
            if first_chunk.HasField("error") and first_chunk.error.code != common_pb2.Error.UNKNOWN:
                http_status = map_proto_error_to_http(first_chunk.error)
                raise HTTPException(status_code=http_status, detail=first_chunk.error.message)
            
            # SUCCESS: First chunk is valid, start streaming
            # Send SSE comment as keepalive
            yield ":keepalive\n\n"
            
            # Send first chunk
            chunk_json = proto_to_json(first_chunk)
            yield f"data: {json.dumps(chunk_json)}\n\n"
            
            # Send remaining chunks
            last_keepalive = asyncio.get_event_loop().time()
            while not is_complete.is_set():
                try:
                    # Get next chunk with timeout for keepalive
                    chunk = await asyncio.wait_for(queue.get(), timeout=10.0)
                    
                    if chunk is None:
                        # Stream complete
                        break
                    
                    chunk_json = proto_to_json(chunk)
                    yield f"data: {json.dumps(chunk_json)}\n\n"
                    
                    last_keepalive = asyncio.get_event_loop().time()
                
                except asyncio.TimeoutError:
                    # Send keepalive
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_keepalive > 10.0:
                        yield ":keepalive\n\n"
                        last_keepalive = current_time
            
            # Wait for reader task to complete
            await reader_task
        
        finally:
            # CRITICAL: Always unsubscribe and cleanup
            try:
                await sub.unsubscribe()
            except Exception as e:
                logger.error(f"Error unsubscribing: {e}")
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "http_nats_gateway:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

