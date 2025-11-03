"""
Intelligent Router - Routes requests to appropriate tier.
Implements tier selection, fallback strategies, and health checks.
"""

import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, List
import httpx


class Tier(Enum):
    """Model tiers."""
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"


class SLA(Enum):
    """Service Level Agreements."""
    REAL_TIME = "real-time"
    INTERACTIVE = "interactive"
    ASYNC = "async"


class TierHealth:
    """Health status for a tier."""
    
    def __init__(self):
        self.is_healthy = True
        self.failure_count = 0
        self.last_check = time.time()
        self.latency_p95 = 0.0
        self.failure_threshold = 5
        self.timeout = 60.0
    
    def record_success(self, latency: float):
        """Record successful request."""
        self.failure_count = 0
        self.last_check = time.time()
        # Simple latency tracking
        self.latency_p95 = latency
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_check = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_healthy = False
    
    def should_check_health(self) -> bool:
        """Check if health check is needed."""
        return time.time() - self.last_check > 30.0
    
    def can_retry(self) -> bool:
        """Check if tier can be retried."""
        if not self.is_healthy:
            # Allow retry after timeout
            if time.time() - self.last_check > self.timeout:
                return True
            return False
        return True


class IntelligentRouter:
    """Intelligent router for multi-tier architecture."""
    
    def __init__(self):
        """Initialize router with tier endpoints."""
        self.tier_endpoints = {
            Tier.GOLD: "http://localhost:8001",
            Tier.SILVER: "http://localhost:8002",
            Tier.BRONZE: "http://localhost:8003"
        }
        
        self.tier_health = {
            Tier.GOLD: TierHealth(),
            Tier.SILVER: TierHealth(),
            Tier.BRONZE: TierHealth()
        }
        
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def route(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route request to appropriate tier.
        
        Args:
            request: Request with prompt, SLA, latency_budget_ms, etc.
        
        Returns:
            Response with tier, endpoint, and routing metadata
        """
        # Select tier based on SLA
        sla = SLA(request.get("sla", "interactive"))
        tier = self._select_tier(sla, request)
        
        # Get routing information
        endpoint = self.tier_endpoints[tier]
        health = self.tier_health[tier]
        
        # Check health before routing
        if not health.can_retry():
            # Try fallback
            tier = self._get_fallback_tier(tier, request)
            endpoint = self.tier_endpoints[tier]
            health = self.tier_health[tier]
        
        response = {
            "tier": tier.value,
            "endpoint": endpoint,
            "sla": sla.value,
            "health": health.is_healthy
        }
        
        # Add async job info for Bronze tier
        if tier == Tier.BRONZE:
            response["async"] = True
            response["job_id"] = f"job_{time.time()}"
        
        return response
    
    def _select_tier(self, sla: SLA, request: Dict[str, Any]) -> Tier:
        """
        Select tier based on SLA and request characteristics.
        
        Args:
            sla: Service level agreement
            request: Request details
        
        Returns:
            Selected tier
        """
        # Route by SLA
        if sla == SLA.REAL_TIME:
            return Tier.GOLD
        elif sla == SLA.INTERACTIVE:
            return Tier.SILVER
        else:  # ASYNC
            return Tier.BRONZE
    
    def _get_fallback_tier(self, tier: Tier, request: Dict[str, Any]) -> Tier:
        """
        Get fallback tier when primary tier is unavailable.
        
        Args:
            tier: Primary tier
            request: Request details
        
        Returns:
            Fallback tier
        """
        # Fallback chain: Gold -> Silver -> Bronze
        if tier == Tier.GOLD:
            return Tier.SILVER
        elif tier == Tier.SILVER:
            return Tier.BRONZE
        else:
            # Bronze is final tier
            return tier
    
    async def check_health(self, tier: Tier) -> bool:
        """
        Check health of a specific tier.
        
        Args:
            tier: Tier to check
        
        Returns:
            True if healthy, False otherwise
        """
        endpoint = self.tier_endpoints[tier]
        health = self.tier_health[tier]
        
        try:
            start_time = time.time()
            response = await self.http_client.get(f"{endpoint}/health", timeout=5.0)
            latency = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                health.record_success(latency)
                return True
            else:
                health.record_failure()
                return False
        except Exception as e:
            health.record_failure()
            return False
    
    async def check_all_tiers_health(self) -> Dict[str, bool]:
        """
        Check health of all tiers.
        
        Returns:
            Dict mapping tier name to health status
        """
        results = {}
        for tier in Tier:
            results[tier.value] = await self.check_health(tier)
        return results
    
    async def get_tier_health_status(self) -> Dict[str, Any]:
        """
        Get health status for all tiers.
        
        Returns:
            Dict with health status for each tier
        """
        status = {}
        for tier in Tier:
            health = self.tier_health[tier]
            status[tier.value] = {
                "is_healthy": health.is_healthy,
                "failure_count": health.failure_count,
                "latency_p95_ms": health.latency_p95
            }
        return status
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

