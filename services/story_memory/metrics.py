"""
Story Memory Metrics and Observability
======================================

Provides comprehensive metrics for the Story Memory System.
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any
from uuid import UUID

from loguru import logger
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, Summary


# Prometheus metrics
story_events_ingested = PrometheusCounter(
    "story_events_ingested_total",
    "Total number of story events ingested",
    ["event_type", "player_id"]
)

story_snapshot_latency = Histogram(
    "story_snapshot_latency_seconds",
    "Time taken to generate story snapshots",
    ["cache_hit"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

story_drift_alerts = PrometheusCounter(
    "story_drift_alerts_total",
    "Total number of narrative drift alerts",
    ["drift_type", "severity"]
)

story_conflicts_detected = PrometheusCounter(
    "story_conflicts_detected_total",
    "Total number of narrative conflicts detected",
    ["conflict_type", "severity"]
)

arc_progress_updates = PrometheusCounter(
    "arc_progress_updates_total",
    "Total number of arc progress updates",
    ["arc_role", "progress_state"]
)

moral_alignment_gauge = Gauge(
    "story_moral_alignment",
    "Player moral alignment score (-1 to 1)",
    ["player_id"]
)

cache_hit_rate = Gauge(
    "story_cache_hit_rate",
    "Story snapshot cache hit rate"
)

active_story_sessions = Gauge(
    "story_active_sessions",
    "Number of active story sessions"
)

drift_check_duration = Summary(
    "story_drift_check_duration_seconds",
    "Time taken to check for narrative drift"
)

event_processing_lag = Histogram(
    "story_event_processing_lag_seconds",
    "Lag between event creation and processing",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
)


class StoryMemoryMetrics:
    """
    Aggregates and tracks metrics for Story Memory System.
    """
    
    def __init__(self):
        # Event tracking
        self.event_counts: Dict[str, Counter] = defaultdict(Counter)
        self.event_lag_samples: List[float] = []
        
        # Drift analytics
        self.drift_distribution: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.conflict_trends: Dict[str, List[datetime]] = defaultdict(list)
        
        # Arc analytics
        self.arc_completion_times: Dict[str, List[float]] = defaultdict(list)
        self.arc_abandonment_rate: Dict[str, float] = defaultdict(float)
        
        # Performance tracking
        self.snapshot_times: List[float] = []
        self.cache_performance = {"hits": 0, "misses": 0}
        
        self._last_reset = datetime.utcnow()
    
    def record_event_ingested(
        self,
        event_type: str,
        player_id: UUID,
        lag_seconds: float = 0
    ) -> None:
        """Record ingestion of a story event."""
        story_events_ingested.labels(
            event_type=event_type,
            player_id=str(player_id)
        ).inc()
        
        self.event_counts[event_type][str(player_id)] += 1
        
        if lag_seconds > 0:
            event_processing_lag.observe(lag_seconds)
            self.event_lag_samples.append(lag_seconds)
            
            # Keep only recent samples
            if len(self.event_lag_samples) > 1000:
                self.event_lag_samples = self.event_lag_samples[-1000:]
    
    def record_snapshot_generation(
        self,
        duration_seconds: float,
        cache_hit: bool
    ) -> None:
        """Record snapshot generation performance."""
        story_snapshot_latency.labels(
            cache_hit=str(cache_hit).lower()
        ).observe(duration_seconds)
        
        self.snapshot_times.append(duration_seconds)
        
        if cache_hit:
            self.cache_performance["hits"] += 1
        else:
            self.cache_performance["misses"] += 1
        
        # Update cache hit rate gauge
        total = self.cache_performance["hits"] + self.cache_performance["misses"]
        if total > 0:
            hit_rate = self.cache_performance["hits"] / total
            cache_hit_rate.set(hit_rate)
    
    def record_drift_alert(
        self,
        drift_type: str,
        severity: str,
        player_id: UUID
    ) -> None:
        """Record a narrative drift alert."""
        story_drift_alerts.labels(
            drift_type=drift_type,
            severity=severity
        ).inc()
        
        self.drift_distribution[drift_type][severity] += 1
        
        logger.info(
            f"Drift alert: {drift_type} ({severity}) for player {player_id}"
        )
    
    def record_conflict(
        self,
        conflict_type: str,
        severity: str,
        player_id: UUID
    ) -> None:
        """Record a narrative conflict."""
        story_conflicts_detected.labels(
            conflict_type=conflict_type,
            severity=severity
        ).inc()
        
        self.conflict_trends[conflict_type].append(datetime.utcnow())
        
        # Keep only recent conflicts
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.conflict_trends[conflict_type] = [
            t for t in self.conflict_trends[conflict_type]
            if t > cutoff
        ]
    
    def record_arc_progress(
        self,
        arc_id: str,
        arc_role: str,
        progress_state: str,
        player_id: UUID
    ) -> None:
        """Record arc progress update."""
        arc_progress_updates.labels(
            arc_role=arc_role,
            progress_state=progress_state
        ).inc()
        
        # Track completion if applicable
        if progress_state == "completed":
            # This would calculate time from start to completion
            # For now, just log it
            logger.info(
                f"Arc completed: {arc_id} ({arc_role}) by player {player_id}"
            )
    
    def record_moral_alignment(
        self,
        player_id: UUID,
        alignment_score: float
    ) -> None:
        """Record player's moral alignment."""
        moral_alignment_gauge.labels(
            player_id=str(player_id)
        ).set(alignment_score)
    
    def record_drift_check(
        self,
        duration_seconds: float,
        drift_found: bool
    ) -> None:
        """Record drift check performance."""
        drift_check_duration.observe(duration_seconds)
    
    def update_active_sessions(self, count: int) -> None:
        """Update active sessions gauge."""
        active_story_sessions.set(count)
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        # Calculate event rate
        total_events = sum(
            sum(counter.values())
            for counter in self.event_counts.values()
        )
        time_span = (datetime.utcnow() - self._last_reset).total_seconds() / 3600
        event_rate = total_events / max(time_span, 1)
        
        # Top event types
        event_totals = Counter()
        for event_type, player_counts in self.event_counts.items():
            event_totals[event_type] = sum(player_counts.values())
        
        # Drift analytics
        total_drift_alerts = sum(
            sum(severities.values())
            for severities in self.drift_distribution.values()
        )
        
        # Conflict rate
        recent_conflicts = sum(
            len(times) for times in self.conflict_trends.values()
        )
        
        # Performance percentiles
        snapshot_p50 = self._percentile(self.snapshot_times, 50)
        snapshot_p95 = self._percentile(self.snapshot_times, 95)
        snapshot_p99 = self._percentile(self.snapshot_times, 99)
        
        lag_p50 = self._percentile(self.event_lag_samples, 50)
        lag_p95 = self._percentile(self.event_lag_samples, 95)
        
        return {
            "event_analytics": {
                "total_events": total_events,
                "events_per_hour": round(event_rate, 2),
                "top_event_types": event_totals.most_common(10),
                "unique_players": len(set(
                    player_id
                    for counter in self.event_counts.values()
                    for player_id in counter.keys()
                ))
            },
            "drift_analytics": {
                "total_alerts": total_drift_alerts,
                "by_type": dict(self.drift_distribution),
                "most_common_drift": max(
                    self.drift_distribution.items(),
                    key=lambda x: sum(x[1].values())
                )[0] if self.drift_distribution else None
            },
            "conflict_analytics": {
                "recent_conflicts_24h": recent_conflicts,
                "by_type": {
                    k: len(v) for k, v in self.conflict_trends.items()
                }
            },
            "performance": {
                "snapshot_latency_ms": {
                    "p50": round(snapshot_p50 * 1000, 2),
                    "p95": round(snapshot_p95 * 1000, 2),
                    "p99": round(snapshot_p99 * 1000, 2)
                },
                "event_lag_seconds": {
                    "p50": round(lag_p50, 2),
                    "p95": round(lag_p95, 2)
                },
                "cache_hit_rate": round(
                    self.cache_performance["hits"] / 
                    max(self.cache_performance["hits"] + self.cache_performance["misses"], 1),
                    3
                )
            },
            "uptime_hours": round(time_span, 2)
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
        """Reset in-memory analytics."""
        logger.info("Resetting story memory analytics")
        
        self.event_counts.clear()
        self.event_lag_samples.clear()
        self.drift_distribution.clear()
        self.conflict_trends.clear()
        self.arc_completion_times.clear()
        self.arc_abandonment_rate.clear()
        self.snapshot_times.clear()
        self.cache_performance = {"hits": 0, "misses": 0}
        
        self._last_reset = datetime.utcnow()


# Global metrics instance
story_metrics = StoryMemoryMetrics()


def track_snapshot_operation():
    """Decorator to track snapshot operation timing."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            cache_hit = kwargs.get("force_refresh", False) is False
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                story_metrics.record_snapshot_generation(
                    duration_seconds=duration,
                    cache_hit=cache_hit and duration < 0.01
                )
                
                return result
            
            except Exception as e:
                logger.error(f"Snapshot operation failed: {e}")
                raise
        
        return wrapper
    return decorator


def track_drift_check():
    """Decorator to track drift check timing."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                story_metrics.record_drift_check(
                    duration_seconds=duration,
                    drift_found=result is not None
                )
                
                return result
            
            except Exception as e:
                logger.error(f"Drift check failed: {e}")
                raise
        
        return wrapper
    return decorator
