"""
OpenTelemetry Integration for NATS SDK
Peer Reviewed: GPT-5 Pro (designed), Pending pairwise validation
"""

from __future__ import annotations

import os
from typing import Optional
from opentelemetry import trace, propagators
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_tracing(
    service_name: str,
    otlp_endpoint: Optional[str] = None,
    environment: Optional[str] = None
) -> None:
    """
    Initialize OpenTelemetry tracing for a service.
    
    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP exporter endpoint (default: env var or localhost:4317)
        environment: Deployment environment (default: env var or "dev")
    """
    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": environment or os.getenv("ENV", "dev"),
    })
    
    provider = TracerProvider(resource=resource)
    
    exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True
    )
    
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def get_tracer(name: str):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def inject_headers(headers: dict) -> None:
    """Inject trace context into headers."""
    try:
        propagator = propagators.get_global_textmap()
        if propagator:
            propagator.inject(headers)
    except Exception:
        # Silently ignore if propagator not configured
        pass


def extract_context(headers: dict):
    """Extract trace context from headers."""
    try:
        propagator = propagators.get_global_textmap()
        if propagator:
            return propagator.extract(headers)
    except Exception:
        # Silently ignore if propagator not configured
        pass
    return None

