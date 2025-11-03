"""
Base HTTP Client
================

Base class for HTTP clients with circuit breaker, retry logic, and error handling.
Reduces code duplication between RulesEngineClient and LoreDatabaseClient.
"""

import logging
import asyncio
import time
from typing import Optional, Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from aiohttp import ClientError

logger = logging.getLogger(__name__)


class BaseHttpClient:
    """
    Base HTTP client with circuit breaker, retry logic, and error handling.
    
    Provides:
    - Circuit breaker pattern with thread-safe state management
    - Retry logic with exponential backoff
    - Proper error handling for different HTTP status codes
    - Monotonic clock for reliable time measurements
    """
    
    def __init__(self, base_url: str, timeout: float = 5.0):
        """
        Initialize Base HTTP Client.
        
        Args:
            base_url: Base URL for the service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = ClientTimeout(total=timeout)
        self.session: Optional[ClientSession] = None
        
        # Circuit breaker state (protected by lock)
        self._circuit_breaker_lock = asyncio.Lock()
        self._failure_count = 0
        self._circuit_breaker_threshold = 5
        self._last_failure_time: Optional[float] = None
        self._circuit_open_until: Optional[float] = None
        self._circuit_timeout_seconds = 60.0
        
        logger.info(f"{self.__class__.__name__} initialized for {base_url}")
    
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _can_execute(self) -> bool:
        """
        Check if circuit breaker allows execution.
        
        Uses monotonic clock and asyncio.Lock for thread-safe access.
        """
        async with self._circuit_breaker_lock:
            if self._circuit_open_until is None:
                return True
            
            current_time = time.monotonic()
            if current_time > self._circuit_open_until:
                # Circuit breaker timeout expired, reset
                self._circuit_open_until = None
                self._failure_count = 0
                logger.info("Circuit breaker reset - attempting request")
                return True
            
            return False
    
    async def _record_success(self) -> None:
        """Record successful request."""
        async with self._circuit_breaker_lock:
            self._failure_count = 0
            self._circuit_open_until = None
    
    async def _record_failure(self) -> None:
        """Record failed request."""
        async with self._circuit_breaker_lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            
            if self._failure_count >= self._circuit_breaker_threshold:
                # Open circuit breaker
                self._circuit_open_until = self._last_failure_time + self._circuit_timeout_seconds
                logger.warning(f"Circuit breaker opened after {self._failure_count} failures")
    
    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        max_retries: int = 3
    ) -> Optional[aiohttp.ClientResponse]:
        """
        Make HTTP request with retry logic and circuit breaker.
        
        Args:
            method: HTTP method ('GET', 'POST', etc.)
            url: Full URL to request
            params: Query parameters
            max_retries: Maximum number of retry attempts
        
        Returns:
            Response object if successful, None otherwise
        """
        if not await self._can_execute():
            logger.warning("Circuit breaker is open - request rejected")
            return None
        
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Session creation inside try block for error handling
                session = await self._get_session()
                
                async with session.request(method, url, params=params) as response:
                    # Success
                    if response.status == 200:
                        await self._record_success()
                        return response
                    
                    # Not found - not a service failure
                    elif response.status == 404:
                        await self._record_success()  # 404 is not a service failure
                        return response
                    
                    # Client errors (4xx) - don't retry
                    elif 400 <= response.status < 500:
                        logger.error(f"Client error {response.status}, not retrying")
                        await self._record_success()  # Not a service failure
                        return None  # Fail fast
                    
                    # Server errors (5xx) or other - retry
                    else:
                        logger.warning(f"Server returned status {response.status}")
                        await self._record_failure()
                        retry_count += 1
                        
            except asyncio.TimeoutError:
                logger.warning(f"Request timed out (attempt {retry_count + 1})")
                await self._record_failure()
                retry_count += 1
                
            except ClientError as e:
                logger.error(f"Client error: {e}")
                await self._record_failure()
                retry_count += 1
                
            except Exception as e:
                # Log unexpected errors but don't retry (e.g., KeyboardInterrupt, CancelledError)
                logger.error(f"Unexpected error: {e}")
                raise  # Propagate unexpected exceptions
            
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed after {max_retries} attempts")
        return None

