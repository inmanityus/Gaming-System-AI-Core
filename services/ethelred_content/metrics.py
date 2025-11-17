"""
Content Governance Metrics and Observability
============================================

Provides metrics collection and monitoring for the Content Governance system.
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from loguru import logger
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, Summary


# Prometheus metrics
policy_snapshots_created = PrometheusCounter(
    "content_policy_snapshots_created_total",
    "Total number of session content policy snapshots created",
    ["profile_name", "has_overrides"]
)

policy_lookup_duration = Histogram(
    "content_policy_lookup_duration_seconds",
    "Time taken to look up content policies",
    ["cache_hit", "source"]
)

content_violations_total = PrometheusCounter(
    "content_violations_total",
    "Total number of content violations detected",
    ["category", "severity", "content_type"]
)

violation_levels_gauge = Gauge(
    "content_violation_level_difference",
    "Difference between observed and allowed content levels",
    ["category"]
)

active_policies_gauge = Gauge(
    "content_active_policies",
    "Number of active content policies in the system",
    ["profile_name"]
)

moderation_requests = PrometheusCounter(
    "content_moderation_requests_total",
    "Total number of content moderation requests",
    ["content_type", "allowed"]
)

moderation_latency = Summary(
    "content_moderation_latency_seconds",
    "Latency of content moderation operations"
)


class ContentGovernanceMetrics:
    """
    Aggregates and tracks metrics for Content Governance.
    
    Provides both Prometheus metrics and custom analytics for dashboards.
    """
    
    def __init__(self):
        # In-memory analytics (reset periodically)
        self.violation_trends: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.policy_coverage: Dict[str, int] = defaultdict(int)
        self.violation_heatmap: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Track unique sessions/players
        self.active_sessions: set[UUID] = set()
        self.active_players: set[UUID] = set()
        
        # Performance tracking
        self.lookup_times: List[float] = []
        self.moderation_times: List[float] = []
        
        self._last_reset = datetime.utcnow()
    
    def record_policy_snapshot(
        self,
        session_id: UUID,
        player_id: UUID,
        profile_name: str,
        has_overrides: bool,
    ) -> None:
        """Record creation of a policy snapshot."""
        policy_snapshots_created.labels(
            profile_name=profile_name,
            has_overrides=str(has_overrides).lower()
        ).inc()
        
        self.active_sessions.add(session_id)
        self.active_players.add(player_id)
        self.policy_coverage[profile_name] += 1
        
        # Update active policies gauge
        for profile, count in self.policy_coverage.items():
            active_policies_gauge.labels(profile_name=profile).set(count)
    
    def record_policy_lookup(
        self,
        duration_seconds: float,
        cache_hit: bool,
        source: str = "unknown",
    ) -> None:
        """Record a policy lookup operation."""
        policy_lookup_duration.labels(
            cache_hit=str(cache_hit).lower(),
            source=source
        ).observe(duration_seconds)
        
        self.lookup_times.append(duration_seconds)
        
        # Keep only recent times for percentile calculations
        if len(self.lookup_times) > 1000:
            self.lookup_times = self.lookup_times[-1000:]
    
    def record_violation(
        self,
        category: str,
        severity: str,
        content_type: str,
        observed_level: int,
        allowed_level: int,
        session_id: Optional[UUID] = None,
        player_id: Optional[UUID] = None,
    ) -> None:
        """Record a content violation."""
        content_violations_total.labels(
            category=category,
            severity=severity,
            content_type=content_type
        ).inc()
        
        # Track level difference
        level_diff = observed_level - allowed_level
        violation_levels_gauge.labels(category=category).set(level_diff)
        
        # Store for trend analysis
        self.violation_trends[category].append({
            "timestamp": datetime.utcnow(),
            "severity": severity,
            "content_type": content_type,
            "level_diff": level_diff,
            "session_id": session_id,
            "player_id": player_id,
        })
        
        # Update heatmap
        self.violation_heatmap[category][severity] += 1
        
        # Cleanup old trends (keep 1 hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.violation_trends[category] = [
            v for v in self.violation_trends[category]
            if v["timestamp"] > cutoff
        ]
    
    def record_moderation_request(
        self,
        content_type: str,
        allowed: bool,
        duration_seconds: float,
    ) -> None:
        """Record a content moderation request."""
        moderation_requests.labels(
            content_type=content_type,
            allowed=str(allowed).lower()
        ).inc()
        
        moderation_latency.observe(duration_seconds)
        self.moderation_times.append(duration_seconds)
        
        # Keep only recent times
        if len(self.moderation_times) > 1000:
            self.moderation_times = self.moderation_times[-1000:]
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary for dashboards."""
        # Calculate percentiles
        lookup_p50 = self._percentile(self.lookup_times, 50)
        lookup_p95 = self._percentile(self.lookup_times, 95)
        lookup_p99 = self._percentile(self.lookup_times, 99)
        
        mod_p50 = self._percentile(self.moderation_times, 50)
        mod_p95 = self._percentile(self.moderation_times, 95)
        mod_p99 = self._percentile(self.moderation_times, 99)
        
        # Violation rate by category
        violation_rates = {}
        for category, violations in self.violation_trends.items():
            if violations:
                # Violations per minute
                time_span = (violations[-1]["timestamp"] - violations[0]["timestamp"]).total_seconds() / 60
                rate = len(violations) / max(time_span, 1)
                violation_rates[category] = round(rate, 2)
        
        # Top violating categories
        top_categories = Counter()
        for category, severities in self.violation_heatmap.items():
            top_categories[category] = sum(severities.values())
        
        return {
            "active_sessions": len(self.active_sessions),
            "active_players": len(self.active_players),
            "policy_coverage": dict(self.policy_coverage),
            "policy_lookup_latency": {
                "p50_ms": round(lookup_p50 * 1000, 2),
                "p95_ms": round(lookup_p95 * 1000, 2),
                "p99_ms": round(lookup_p99 * 1000, 2),
            },
            "moderation_latency": {
                "p50_ms": round(mod_p50 * 1000, 2),
                "p95_ms": round(mod_p95 * 1000, 2),
                "p99_ms": round(mod_p99 * 1000, 2),
            },
            "violation_rates_per_min": violation_rates,
            "top_violation_categories": top_categories.most_common(5),
            "violation_heatmap": {
                cat: dict(severities)
                for cat, severities in self.violation_heatmap.items()
            },
            "uptime_hours": (datetime.utcnow() - self._last_reset).total_seconds() / 3600,
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def reset_analytics(self) -> None:
        """Reset in-memory analytics (called periodically)."""
        logger.info("Resetting content governance analytics")
        
        self.violation_trends.clear()
        self.policy_coverage.clear()
        self.violation_heatmap.clear()
        self.active_sessions.clear()
        self.active_players.clear()
        self.lookup_times.clear()
        self.moderation_times.clear()
        
        self._last_reset = datetime.utcnow()


# Global metrics instance
content_metrics = ContentGovernanceMetrics()


def track_policy_operation(operation: str):
    """Decorator to track policy operation timing."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            cache_hit = False
            
            try:
                result = await func(*args, **kwargs)
                
                # Check if it was a cache hit (heuristic based on timing)
                duration = time.time() - start
                cache_hit = duration < 0.001  # Sub-millisecond likely cache hit
                
                content_metrics.record_policy_lookup(
                    duration_seconds=duration,
                    cache_hit=cache_hit,
                    source=operation
                )
                
                return result
            
            except Exception as e:
                logger.error(f"Policy operation {operation} failed: {e}")
                raise
        
        return wrapper
    return decorator


def track_moderation():
    """Decorator to track moderation request timing."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                # Extract request info from args
                if args and hasattr(args[1], 'content_type'):
                    request = args[1]
                    content_metrics.record_moderation_request(
                        content_type=request.content_type,
                        allowed=result.allowed,
                        duration_seconds=duration
                    )
                
                return result
            
            except Exception as e:
                logger.error(f"Moderation request failed: {e}")
                raise
        
        return wrapper
    return decorator

