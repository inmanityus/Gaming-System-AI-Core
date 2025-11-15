"""
Metrics and observability for 4D Vision Ingest service.
Part of T4D-12 implementation.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps
from typing import Callable, Any


# Ingest metrics
ingest_segments_total = Counter(
    'vision_ingest_segments_total',
    'Total number of segments ingested',
    ['build_id', 'level_name', 'scene_type']
)

ingest_duration_seconds = Histogram(
    'vision_ingest_duration_seconds',
    'Time taken to ingest a segment',
    ['status'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

ingest_errors_total = Counter(
    'vision_ingest_errors_total',
    'Total number of ingest errors',
    ['error_type', 'build_id']
)

segment_size_bytes = Histogram(
    'vision_segment_size_bytes',
    'Size of ingested segments in bytes',
    ['media_type'],
    buckets=[1e6, 10e6, 100e6, 500e6, 1e9]  # 1MB to 1GB
)

validation_failures_total = Counter(
    'vision_validation_failures_total',
    'Total number of segment validation failures',
    ['failure_reason']
)

# Current state gauges
active_ingestion_tasks = Gauge(
    'vision_active_ingestion_tasks',
    'Number of currently active ingestion tasks'
)

ingest_queue_size = Gauge(
    'vision_ingest_queue_size',
    'Current size of the ingestion queue'
)

# Performance metrics
segment_duration_summary = Summary(
    'vision_segment_duration_seconds',
    'Duration of segments being processed',
    ['level_name']
)

media_processing_latency = Histogram(
    'vision_media_processing_latency_seconds',
    'Latency of media processing operations',
    ['operation', 'media_type']
)


def track_ingest_metrics(func: Callable) -> Callable:
    """Decorator to track ingest metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        active_ingestion_tasks.inc()
        
        try:
            result = await func(*args, **kwargs)
            ingest_duration_seconds.labels(status='success').observe(time.time() - start_time)
            return result
        except Exception as e:
            ingest_duration_seconds.labels(status='error').observe(time.time() - start_time)
            error_type = type(e).__name__
            
            # Extract build_id if available
            build_id = 'unknown'
            if len(args) > 1 and hasattr(args[1], 'build_id'):
                build_id = args[1].build_id
            
            ingest_errors_total.labels(error_type=error_type, build_id=build_id).inc()
            raise
        finally:
            active_ingestion_tasks.dec()
    
    return wrapper


def track_validation_metrics(func: Callable) -> Callable:
    """Decorator to track validation metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            reason = str(e) if str(e) else 'unknown'
            validation_failures_total.labels(failure_reason=reason).inc()
            raise
    
    return wrapper


class IngestMetricsCollector:
    """Collects and exposes ingest-specific metrics."""
    
    def __init__(self):
        self._start_time = time.time()
    
    def record_segment_ingested(self, segment: dict):
        """Record successful segment ingestion."""
        ingest_segments_total.labels(
            build_id=segment.get('build_id', 'unknown'),
            level_name=segment.get('level_name', 'unknown'),
            scene_type=segment.get('scene_type', 'unknown')
        ).inc()
        
        # Record segment duration
        if 'duration_seconds' in segment:
            segment_duration_summary.labels(
                level_name=segment.get('level_name', 'unknown')
            ).observe(segment['duration_seconds'])
    
    def record_media_size(self, media_type: str, size_bytes: int):
        """Record media size metrics."""
        segment_size_bytes.labels(media_type=media_type).observe(size_bytes)
    
    def record_processing_latency(self, operation: str, media_type: str, latency: float):
        """Record media processing latency."""
        media_processing_latency.labels(
            operation=operation,
            media_type=media_type
        ).observe(latency)
    
    def update_queue_size(self, size: int):
        """Update current queue size."""
        ingest_queue_size.set(size)
    
    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self._start_time
