"""
NATS SDK Custom Exceptions
Peer Reviewed: GPT-5 Pro (designed), Pending pairwise validation
"""

from __future__ import annotations


class NATSBaseError(Exception):
    """Base exception for all NATS SDK errors."""
    pass


class SerializationError(NATSBaseError):
    """Raised when protobuf serialization fails."""
    pass


class DeserializationError(NATSBaseError):
    """Raised when protobuf deserialization fails."""
    pass


class ServiceTimeoutError(NATSBaseError):
    """Raised when service request times out."""
    pass


class ServiceUnavailableError(NATSBaseError):
    """Raised when service is unavailable (no responders)."""
    pass


class CircuitOpenError(NATSBaseError):
    """Raised when circuit breaker is open."""
    pass


class RetryExhaustedError(NATSBaseError):
    """Raised when all retry attempts exhausted."""
    pass

