"""
Metrics and observability for 4D Vision Analyzer service.
Part of T4D-12 implementation.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps
from typing import Callable, Any, Dict, List


# Analysis metrics
segments_analyzed_total = Counter(
    'vision_segments_analyzed_total',
    'Total number of segments analyzed',
    ['detector_type', 'status']
)

analysis_duration_seconds = Histogram(
    'vision_analysis_duration_seconds',
    'Time taken to analyze a segment',
    ['detector_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

issues_detected_total = Counter(
    'vision_issues_detected_total',
    'Total number of issues detected',
    ['issue_type', 'severity_category', 'detector_type']
)

analysis_errors_total = Counter(
    'vision_analysis_errors_total',
    'Total number of analysis errors',
    ['error_type', 'detector_type']
)

# Detector-specific metrics
detector_confidence_summary = Summary(
    'vision_detector_confidence',
    'Confidence scores from detectors',
    ['detector_type', 'issue_type']
)

detector_finding_rate = Histogram(
    'vision_detector_finding_rate',
    'Rate of findings per segment',
    ['detector_type'],
    buckets=[0, 1, 2, 5, 10, 20, 50]
)

# Performance metrics
frame_processing_rate = Gauge(
    'vision_frame_processing_rate_fps',
    'Current frame processing rate',
    ['detector_type']
)

active_analysis_tasks = Gauge(
    'vision_active_analysis_tasks',
    'Number of currently active analysis tasks',
    ['detector_type']
)

# Goal impact tracking
goal_impact_counter = Counter(
    'vision_goal_impacts_total',
    'Issues impacting specific goals',
    ['goal', 'severity_category']
)

# SLO metrics
slo_analysis_latency = Histogram(
    'vision_slo_analysis_latency_seconds',
    'Analysis latency for SLO tracking',
    buckets=[1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

slo_coverage_ratio = Gauge(
    'vision_slo_coverage_ratio',
    'Coverage ratio for SLO tracking',
    ['build_id']
)


def severity_to_category(severity: float) -> str:
    """Convert severity float to category."""
    if severity < 0.3:
        return "low"
    elif severity < 0.6:
        return "medium"
    elif severity < 0.8:
        return "high"
    else:
        return "critical"


def track_analysis_metrics(detector_type: str):
    """Decorator to track analysis metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            active_analysis_tasks.labels(detector_type=detector_type).inc()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                segments_analyzed_total.labels(
                    detector_type=detector_type,
                    status='success'
                ).inc()
                
                analysis_duration_seconds.labels(
                    detector_type=detector_type
                ).observe(duration)
                
                # Track SLO latency
                slo_analysis_latency.observe(duration)
                
                return result
            except Exception as e:
                segments_analyzed_total.labels(
                    detector_type=detector_type,
                    status='error'
                ).inc()
                
                analysis_errors_total.labels(
                    error_type=type(e).__name__,
                    detector_type=detector_type
                ).inc()
                raise
            finally:
                active_analysis_tasks.labels(detector_type=detector_type).dec()
        
        return wrapper
    return decorator


class AnalyzerMetricsCollector:
    """Collects and exposes analyzer-specific metrics."""
    
    def __init__(self):
        self._start_time = time.time()
        self._frame_counters: Dict[str, int] = {}
        self._frame_timers: Dict[str, float] = {}
    
    def record_findings(self, findings: List[Dict[str, Any]], detector_type: str):
        """Record findings from a detector."""
        # Record finding rate
        detector_finding_rate.labels(detector_type=detector_type).observe(len(findings))
        
        # Record each finding
        for finding in findings:
            issue_type = finding.get('issue_type', 'unknown')
            severity = finding.get('severity', 0.5)
            confidence = finding.get('confidence', 0.5)
            
            # Track issue
            issues_detected_total.labels(
                issue_type=issue_type,
                severity_category=severity_to_category(severity),
                detector_type=detector_type
            ).inc()
            
            # Track confidence
            detector_confidence_summary.labels(
                detector_type=detector_type,
                issue_type=issue_type
            ).observe(confidence)
            
            # Track goal impacts
            affected_goals = finding.get('affected_goals', [])
            for goal in affected_goals:
                goal_impact_counter.labels(
                    goal=goal,
                    severity_category=severity_to_category(severity)
                ).inc()
    
    def start_frame_timing(self, detector_type: str):
        """Start timing frame processing."""
        self._frame_timers[detector_type] = time.time()
        if detector_type not in self._frame_counters:
            self._frame_counters[detector_type] = 0
    
    def record_frame_processed(self, detector_type: str):
        """Record a processed frame."""
        self._frame_counters[detector_type] = self._frame_counters.get(detector_type, 0) + 1
        
        # Update FPS gauge every second
        if detector_type in self._frame_timers:
            elapsed = time.time() - self._frame_timers[detector_type]
            if elapsed >= 1.0:
                fps = self._frame_counters[detector_type] / elapsed
                frame_processing_rate.labels(detector_type=detector_type).set(fps)
                
                # Reset counters
                self._frame_counters[detector_type] = 0
                self._frame_timers[detector_type] = time.time()
    
    def update_coverage_ratio(self, build_id: str, ratio: float):
        """Update coverage ratio for SLO tracking."""
        slo_coverage_ratio.labels(build_id=build_id).set(ratio)
    
    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self._start_time
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get current analysis statistics."""
        # This would aggregate from Prometheus in production
        return {
            "uptime_seconds": self.get_uptime_seconds(),
            "active_tasks": sum(
                active_analysis_tasks.labels(detector_type=dt)._value.get()
                for dt in ["animation", "physics", "rendering", "lighting", "performance", "flow"]
            )
        }

