"""
Base HTTP Client for Inter-Service Communication
Provides retry logic, circuit breaker, timeout handling
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation with async support."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
        self.lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker protection."""
        async with self.lock:
            if self.state == "open":
                if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                    self.state = "half-open"
                    self.failure_count = 0
                else:
                    raise CircuitBreakerOpen(f"Circuit breaker open, retry after {self.recovery_timeout}s")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise


class BaseHTTPClient:
    """
    Base HTTP client with:
    - Automatic retries with exponential backoff
    - Circuit breaker pattern
    - Timeout handling
    - Connection pooling
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 1.0
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.session: Optional[aiohttp.ClientSession] = None
        self.circuit_breaker = CircuitBreaker()
    
    async def __aenter__(self):
        """Context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def close(self):
        """Explicitly close the session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session."""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make HTTP request with automatic retries."""
        session = await self._get_session()
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return response
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
        
        raise last_exception
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """GET request with circuit breaker."""
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()
        
        async def _do_request():
            for attempt in range(self.max_retries):
                try:
                    async with session.get(url, params=params, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_backoff * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                    else:
                        raise
        
        return await self.circuit_breaker.call(_do_request)
    
    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """POST request with circuit breaker."""
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()
        
        async def _do_request():
            for attempt in range(self.max_retries):
                try:
                    async with session.post(url, json=json, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_backoff * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                    else:
                        raise
        
        return await self.circuit_breaker.call(_do_request)
    
    async def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """PUT request."""
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()
        
        async with session.put(url, json=json, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """DELETE request."""
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()
        
        async with session.delete(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception:
            return False

