"""
Metrics and observability for 4D Vision Coverage job.
Part of T4D-12 implementation.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from typing import Dict, Any


# Coverage job metrics
coverage_runs_total = Counter(
    'vision_coverage_runs_total',
    'Total number of coverage analysis runs',
    ['status']
)

coverage_run_duration_seconds = Histogram(
    'vision_coverage_run_duration_seconds',
    'Time taken for a complete coverage run',
    buckets=[10, 30, 60, 120, 300, 600]
)

builds_analyzed_total = Counter(
    'vision_builds_analyzed_total',
    'Total number of builds analyzed'
)

coverage_events_emitted_total = Counter(
    'vision_coverage_events_emitted_total',
    'Total coverage events emitted',
    ['event_type']
)

# Coverage metrics
build_quality_score = Gauge(
    'vision_build_quality_score',
    'Quality score for a build (0-1)',
    ['build_id']
)

scene_coverage_ratio = Gauge(
    'vision_scene_coverage_ratio',
    'Scene coverage ratio',
    ['build_id']
)

issue_density = Gauge(
    'vision_issue_density',
    'Issues per minute of analyzed content',
    ['build_id', 'issue_type']
)

# Trend metrics
trend_delta_gauge = Gauge(
    'vision_trend_delta',
    'Change in metrics between builds',
    ['metric_type', 'direction']
)

coverage_job_errors_total = Counter(
    'vision_coverage_job_errors_total',
    'Total errors in coverage job',
    ['error_type']
)

# Job health
last_successful_run = Gauge(
    'vision_coverage_last_successful_run_timestamp',
    'Timestamp of last successful coverage run'
)


class CoverageMetricsCollector:
    """Collects and exposes coverage job metrics."""
    
    def __init__(self):
        self._start_time = time.time()
        self._run_start_time = None
    
    def start_coverage_run(self):
        """Mark the start of a coverage run."""
        self._run_start_time = time.time()
    
    def end_coverage_run(self, success: bool = True):
        """Mark the end of a coverage run."""
        if self._run_start_time:
            duration = time.time() - self._run_start_time
            coverage_run_duration_seconds.observe(duration)
            
        coverage_runs_total.labels(status='success' if success else 'error').inc()
        
        if success:
            last_successful_run.set(time.time())
        
        self._run_start_time = None
    
    def record_build_analyzed(self, build_id: str):
        """Record a build being analyzed."""
        builds_analyzed_total.inc()
    
    def record_coverage_event(self, event_type: str):
        """Record emission of a coverage event."""
        coverage_events_emitted_total.labels(event_type=event_type).inc()
    
    def record_build_metrics(self, build_id: str, metrics: Dict[str, Any]):
        """Record build-level metrics."""
        if 'quality_score' in metrics:
            build_quality_score.labels(build_id=build_id).set(
                metrics['quality_score']
            )
        
        if 'scene_coverage' in metrics:
            scene_coverage_ratio.labels(build_id=build_id).set(
                metrics['scene_coverage']
            )
        
        if 'issue_densities' in metrics:
            for issue_type, density in metrics['issue_densities'].items():
                issue_density.labels(
                    build_id=build_id,
                    issue_type=issue_type
                ).set(density)
    
    def record_trend_delta(self, metric_type: str, delta: float):
        """Record trend changes."""
        direction = 'improving' if delta < 0 else 'degrading' if delta > 0 else 'stable'
        trend_delta_gauge.labels(
            metric_type=metric_type,
            direction=direction
        ).set(abs(delta))
    
    def record_error(self, error_type: str):
        """Record a job error."""
        coverage_job_errors_total.labels(error_type=error_type).inc()
    
    def get_uptime_seconds(self) -> float:
        """Get job uptime in seconds."""
        return time.time() - self._start_time
