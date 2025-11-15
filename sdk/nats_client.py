"""
NATS Client Wrapper with Circuit Breaker, Retries, and Observability
Peer Reviewed: GPT-5 Pro (designed), Pending pairwise validation
Production-ready implementation for AI-to-AI binary messaging
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Type, TypeVar

import nats
from nats.errors import TimeoutError as NATSTimeoutError
from nats.errors import NoRespondersError
from nats.js.api import StreamConfig, StorageType, RetentionPolicy

from google.protobuf.message import Message

from .codecs import encode_protobuf, decode_protobuf, CONTENT_TYPE_PROTO, HEADER_MSG_TYPE
from .errors import (
    ServiceTimeoutError,
    ServiceUnavailableError,
    RetryExhaustedError,
    CircuitOpenError,
)
from .otel import get_tracer, inject_headers, extract_context
from .circuit_breaker import AsyncCircuitBreaker

T = TypeVar("T", bound=Message)

logger = logging.getLogger("sdk.nats_client")


@dataclass
class NATSConfig:
    """Configuration for NATS client."""
    servers: list[str]
    name: str
    connect_timeout: float = 2.0
    ping_interval: float = 10.0
    max_reconnect_attempts: int = -1  # infinite
    reconnect_time_wait: float = 2.0
    inbox_prefix: str = "_INBOX"
    request_timeout: float = 2.0
    request_retries: int = 2
    retry_backoff_min: float = 0.05
    retry_backoff_max: float = 0.5
    headers_enabled: bool = True
    enable_jetstream: bool = True
    trace: bool = True


class NATSClient:
    """
    Production NATS client wrapper with:
    - Circuit breaker per-subject
    - Exponential backoff retries
    - OpenTelemetry tracing
    - Protobuf serialization
    - Request/reply pattern
    - Pub/sub events
    - Queue group workers
    """
    
    def __init__(self, config: NATSConfig | str):
        # Allow simple string URL for convenience
        if isinstance(config, str):
            self._cfg = NATSConfig(
                servers=[config],
                name="nats-client"
            )
        else:
            self._cfg = config
        
        self._nc: Optional[nats.NATS] = None
        self._js = None
        self._tracer = get_tracer(self._cfg.name)
        self._cbreakers: Dict[str, AsyncCircuitBreaker] = {}
    
    async def connect(self) -> None:
        """Connect to NATS server with automatic reconnection."""
        
        # Async callbacks required by nats-py
        async def error_cb(e):
            logger.error("NATS error: %s", e)
        
        async def disconnected_cb():
            logger.warning("NATS disconnected")
        
        async def reconnected_cb():
            logger.info("NATS reconnected")
        
        async def closed_cb():
            logger.warning("NATS connection closed")
        
        self._nc = await nats.connect(
            servers=self._cfg.servers,
            name=self._cfg.name,
            connect_timeout=self._cfg.connect_timeout,
            ping_interval=self._cfg.ping_interval,
            max_reconnect_attempts=self._cfg.max_reconnect_attempts,
            reconnect_time_wait=self._cfg.reconnect_time_wait,
            error_cb=error_cb,
            disconnected_cb=disconnected_cb,
            reconnected_cb=reconnected_cb,
            closed_cb=closed_cb,
        )
        
        if self._cfg.enable_jetstream:
            self._js = self._nc.jetstream()
        
        logger.info("Connected to NATS: %s", self._cfg.servers)
    
    async def close(self) -> None:
        """Close NATS connection gracefully."""
        if self._nc and not self._nc.is_closed:
            await self._nc.drain()
            await self._nc.close()
    
    async def ensure_event_stream(self) -> None:
        """Ensure core event stream exists for JetStream events."""
        if not self._js:
            return
        
        try:
            await self._js.add_stream(
                StreamConfig(
                    name="EVT_CORE",
                    subjects=["evt.>"],
                    storage=StorageType.FILE,
                    retention=RetentionPolicy.Limits,
                    max_age=0,  # unlimited; configure per use case
                )
            )
        except Exception:
            # Already exists or race; safe to ignore if idempotent
            pass
    
    def _get_cb(self, subject: str) -> AsyncCircuitBreaker:
        """Get or create circuit breaker for subject."""
        if subject not in self._cbreakers:
            self._cbreakers[subject] = AsyncCircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30
            )
        return self._cbreakers[subject]
    
    async def request(
        self,
        subject: str,
        request_msg: Message | bytes = None,
        response_cls: Type[T] = None,
        request_data: bytes = None,
        response_type: Type[T] = None,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        idempotency_key: Optional[str] = None,
    ) -> T:
        """
        Send request and wait for response (RPC pattern).
        
        Args:
            subject: NATS subject to send to
            request_msg: Protobuf request message
            response_cls: Protobuf response class
            timeout: Request timeout in seconds
            headers: Additional headers
            idempotency_key: Idempotency key for at-least-once
            
        Returns:
            Protobuf response message
            
        Raises:
            CircuitOpenError: Circuit breaker is open
            ServiceTimeoutError: Request timed out
            ServiceUnavailableError: No responders available
            RetryExhaustedError: All retries failed
        """
        if not self._nc:
            raise RuntimeError("NATSClient not connected")
        
        # Support both Message objects and raw bytes
        if request_data:
            data = request_data
            resp_cls = response_type or response_cls
        elif request_msg:
            data = encode_protobuf(request_msg) if isinstance(request_msg, Message) else request_msg
            resp_cls = response_type or response_cls
        else:
            raise ValueError("Must provide either request_msg or request_data")
        
        hdrs = headers.copy() if headers else {}
        if self._cfg.headers_enabled:
            hdrs["content-type"] = CONTENT_TYPE_PROTO
            if isinstance(request_msg, Message):
                hdrs[HEADER_MSG_TYPE] = request_msg.DESCRIPTOR.full_name
            if idempotency_key:
                hdrs["Nats-Msg-Id"] = idempotency_key
            if self._cfg.trace:
                inject_headers(hdrs)
        
        if not resp_cls:
            raise ValueError("Must provide response_cls or response_type")
        cbreaker = self._get_cb(subject)
        
        if not await cbreaker.allow():
            raise CircuitOpenError(f"Circuit open for subject {subject}")
        
        to = timeout or self._cfg.request_timeout
        attempts = self._cfg.request_retries + 1
        backoff = self._cfg.retry_backoff_min
        
        last_exc: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            with self._tracer.start_as_current_span(
                "nats.request",
                attributes={"nats.subject": subject}
            ):
                try:
                    resp = await self._nc.request(
                        subject,
                        payload=data,
                        timeout=to,
                        headers=hdrs
                    )
                    await cbreaker.on_success()
                    return decode_protobuf(resp.data, resp_cls)
                    
                except NATSTimeoutError as e:
                    last_exc = e
                    await cbreaker.on_failure()
                    if attempt >= attempts:
                        raise ServiceTimeoutError(
                            f"Timeout after {attempt} attempts"
                        ) from e
                        
                except NoRespondersError as e:
                    last_exc = e
                    await cbreaker.on_failure()
                    raise ServiceUnavailableError(
                        f"No responders for {subject}"
                    ) from e
                    
                except Exception as e:
                    last_exc = e
                    await cbreaker.on_failure()
                    if attempt >= attempts:
                        raise RetryExhaustedError(str(e)) from e
            
            # Exponential backoff with jitter cap
            await asyncio.sleep(min(backoff, self._cfg.retry_backoff_max))
            backoff = min(backoff * 2, self._cfg.retry_backoff_max)
        
        assert last_exc
        raise RetryExhaustedError(str(last_exc))
    
    async def publish_event(
        self,
        subject: str,
        msg: Message,
        msg_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Publish event to NATS (pub/sub pattern).
        
        Args:
            subject: NATS subject to publish to
            msg: Protobuf message to publish
            msg_id: Message ID for deduplication
            headers: Additional headers
        """
        if not self._nc:
            raise RuntimeError("NATSClient not connected")
        
        hdrs = headers.copy() if headers else {}
        if self._cfg.headers_enabled:
            hdrs["content-type"] = CONTENT_TYPE_PROTO
            hdrs[HEADER_MSG_TYPE] = msg.DESCRIPTOR.full_name
            if self._cfg.trace:
                inject_headers(hdrs)
        
        payload = encode_protobuf(msg)
        
        if self._js:
            # Use JetStream for durable events
            await self._js.publish(
                subject,
                payload=payload,
                headers=hdrs,
                msg_id=msg_id or str(uuid.uuid4())
            )
        else:
            # Core NATS (fire-and-forget)
            await self._nc.publish(subject, payload, headers=hdrs)
    
    async def subscribe(
        self,
        subject: str,
        message_cls: Type[T],
        handler: Callable[[T, Dict[str, str], str], Awaitable[None]],
    ) -> None:
        """
        Subscribe to NATS subject (pub/sub pattern).
        
        Args:
            subject: NATS subject to subscribe to
            message_cls: Protobuf message class
            handler: Async callback (message, headers, reply_subject)
        """
        if not self._nc:
            raise RuntimeError("NATSClient not connected")
        
        async def _cb(msg):
            ctx = extract_context(msg.headers or {})
            with self._tracer.start_as_current_span(
                "nats.subscribe",
                context=ctx,
                attributes={"nats.subject": msg.subject}
            ):
                body = decode_protobuf(msg.data, message_cls)
                await handler(body, msg.headers or {}, msg.reply or "")
        
        await self._nc.subscribe(subject, cb=_cb)
    
    async def queue_worker(
        self,
        subject: str,
        queue: str,
        request_cls: Type[T],
        response_builder: Callable[[T], Awaitable[Message]],
    ) -> None:
        """
        Subscribe as queue group worker (load-balanced RPC pattern).
        
        Args:
            subject: NATS subject to subscribe to
            queue: Queue group name for load balancing
            request_cls: Protobuf request class
            response_builder: Async function to build response from request
        """
        if not self._nc:
            raise RuntimeError("NATSClient not connected")
        
        async def _cb(msg):
            ctx = extract_context(msg.headers or {})
            with self._tracer.start_as_current_span(
                "nats.queue_worker",
                context=ctx,
                attributes={"nats.subject": msg.subject, "nats.queue": queue}
            ):
                req = decode_protobuf(msg.data, request_cls)
                try:
                    resp_msg = await response_builder(req)
                except Exception as e:
                    logger.exception("Worker error for %s: %s", subject, e)
                    # Re-raise to trigger timeout on requester side
                    raise
                
                if msg.reply:
                    hdrs = {}
                    if self._cfg.headers_enabled:
                        hdrs["content-type"] = CONTENT_TYPE_PROTO
                        hdrs[HEADER_MSG_TYPE] = resp_msg.DESCRIPTOR.full_name
                        if self._cfg.trace:
                            inject_headers(hdrs)
                    
                    await self._nc.publish(
                        msg.reply,
                        payload=encode_protobuf(resp_msg),
                        headers=hdrs
                    )
        
        await self._nc.subscribe(subject, queue=queue, cb=_cb)
    
    async def request_stream(
        self,
        subject: str,
        request_data: bytes,
        chunk_type: Type[T],
        timeout: float = 30.0
    ):
        """
        Send request and stream response chunks (for LLM token streaming).
        
        Args:
            subject: NATS subject to send to
            request_data: Serialized protobuf request
            chunk_type: Protobuf chunk class (e.g., LLMStreamChunk)
            timeout: Total timeout for stream
            
        Yields:
            Protobuf chunk messages until is_final=true
        """
        if not self._nc:
            raise RuntimeError("NATSClient not connected")
        
        # Create unique inbox and subscribe
        inbox = self._nc.new_inbox()
        sub = await self._nc.subscribe(inbox, max_msgs=1000)
        
        try:
            # CRITICAL: Flush to ensure subscription is registered
            await self._nc.flush()
            
            # Send request with reply inbox
            await self._nc.publish(subject, request_data, reply=inbox)
            
            # Stream chunks until final
            start_time = asyncio.get_event_loop().time()
            async for msg in sub.messages:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    raise ServiceTimeoutError(f"Stream timeout after {elapsed}s")
                
                # Parse chunk
                chunk = chunk_type()
                chunk.ParseFromString(msg.data)
                
                yield chunk
                
                # Check if final chunk
                if chunk.is_final:
                    break
        
        finally:
            # Always unsubscribe
            await sub.unsubscribe()
    
    async def subscribe_queue(
        self,
        subject: str,
        queue: str
    ):
        """
        Subscribe to subject with queue group (load balanced).
        
        Yields messages for processing. Call msg.respond() to reply.
        
        Args:
            subject: NATS subject to subscribe to
            queue: Queue group name for load balancing
            
        Yields:
            NATS messages
        """
        if not self._nc:
            raise RuntimeError("NATSClient not connected")
        
        sub = await self._nc.subscribe(subject, queue=queue)
        
        try:
            async for msg in sub.messages:
                yield msg
        finally:
            await sub.unsubscribe()
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

