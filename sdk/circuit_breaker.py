"""
Circuit Breaker for NATS Service Calls
Prevents cascade failures by detecting and handling service degradation
"""

import time
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    timeout_seconds: float = 60.0  # Time to wait before trying again
    success_threshold: int = 2  # Successes in half-open before closing
    
    
class AsyncCircuitBreaker:
    """
    Circuit breaker implementation for service calls.
    
    States:
    - CLOSED: Normal operation, all requests go through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing recovery, allow limited requests
    
    Usage:
        breaker = AsyncCircuitBreaker(name="my-service")
        
        async def make_call():
            result = await breaker.call(async_function, arg1, arg2)
            return result
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name for logging/identification
            config: Configuration (uses defaults if None)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.last_attempt_time = 0.0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if call fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if time.time() - self.last_failure_time >= self.config.timeout_seconds:
                # Try half-open
                logger.info(f"Circuit breaker {self.name}: Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                # Still open, reject request
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
        
        # Record attempt
        self.last_attempt_time = time.time()
        
        try:
            # Make the call
            result = await func(*args, **kwargs)
            
            # Success
            self._on_success()
            return result
            
        except Exception as e:
            # Failure
            self._on_failure(e)
            raise
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.config.success_threshold:
                # Recovered!
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN → CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"Circuit breaker {self.name}: Failure {self.failure_count}/{self.config.failure_threshold} - {exception}")
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed while testing recovery, go back to open
            logger.warning(f"Circuit breaker {self.name}: HALF_OPEN → OPEN (recovery failed)")
            self.state = CircuitState.OPEN
            self.success_count = 0
        
        elif self.state == CircuitState.CLOSED:
            # Check if threshold reached
            if self.failure_count >= self.config.failure_threshold:
                logger.error(f"Circuit breaker {self.name}: CLOSED → OPEN (threshold reached)")
                self.state = CircuitState.OPEN
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED."""
        logger.info(f"Circuit breaker {self.name}: Manual reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Global registry of circuit breakers
_breakers: dict[str, AsyncCircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> AsyncCircuitBreaker:
    """
    Get or create circuit breaker for a service.
    
    Args:
        name: Service name
        config: Optional configuration
        
    Returns:
        AsyncCircuitBreaker instance
    """
    if name not in _breakers:
        _breakers[name] = AsyncCircuitBreaker(name, config)
    return _breakers[name]

# Backward compatibility alias
CircuitBreaker = AsyncCircuitBreaker
