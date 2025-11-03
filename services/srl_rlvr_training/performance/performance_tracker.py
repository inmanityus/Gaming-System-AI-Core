"""
Performance Tracker
==================

Tracks model performance over time to detect weaknesses and regressions.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """A performance metric entry."""
    timestamp: datetime
    model_id: str
    model_type: str
    metric_name: str
    metric_value: float
    benchmark_name: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PerformanceTracker:
    """
    Tracks model performance over time.
    
    Maintains history of:
    - Benchmark scores
    - Inference latency
    - Quality metrics
    - Cost metrics
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize Performance Tracker.
        
        Args:
            db_url: Database URL for persistent storage (optional)
        """
        self.db_url = db_url
        self.metrics_history: List[PerformanceMetric] = []
        logger.info("PerformanceTracker initialized")
    
    def record_metric(
        self,
        model_id: str,
        model_type: str,
        metric_name: str,
        metric_value: float,
        benchmark_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a performance metric.
        
        Args:
            model_id: Model identifier
            model_type: Type of model
            metric_name: Name of metric (e.g., "accuracy", "latency_ms")
            metric_value: Metric value
            benchmark_name: Benchmark name (optional)
            metadata: Additional metadata (optional)
        """
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            model_id=model_id,
            model_type=model_type,
            metric_name=metric_name,
            metric_value=metric_value,
            benchmark_name=benchmark_name,
            metadata=metadata or {}
        )
        
        self.metrics_history.append(metric)
        
        # TODO: Persist to database if db_url is provided
        
        logger.debug(f"Recorded metric: {model_id}/{metric_name} = {metric_value}")
    
    def get_performance_trend(
        self,
        model_id: str,
        metric_name: str,
        days: int = 30
    ) -> List[PerformanceMetric]:
        """
        Get performance trend for a model.
        
        Args:
            model_id: Model identifier
            metric_name: Metric name
            days: Number of days to look back
        
        Returns:
            List of performance metrics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        trend = [
            m for m in self.metrics_history
            if m.model_id == model_id
            and m.metric_name == metric_name
            and m.timestamp >= cutoff
        ]
        
        # Sort by timestamp
        trend.sort(key=lambda x: x.timestamp)
        
        return trend
    
    def detect_regression(
        self,
        model_id: str,
        metric_name: str,
        threshold: float = 0.05
    ) -> Optional[Dict[str, Any]]:
        """
        Detect performance regression.
        
        Args:
            model_id: Model identifier
            metric_name: Metric name
            threshold: Regression threshold (relative change)
        
        Returns:
            Regression info if detected, None otherwise
        """
        trend = self.get_performance_trend(model_id, metric_name, days=30)
        
        if len(trend) < 2:
            return None
        
        # Compare recent vs baseline (first week)
        recent = trend[-7:]
        baseline = trend[:7] if len(trend) >= 7 else trend[:len(trend)//2]
        
        if not recent or not baseline:
            return None
        
        recent_avg = sum(m.metric_value for m in recent) / len(recent)
        baseline_avg = sum(m.metric_value for m in baseline) / len(baseline)
        
        change = (recent_avg - baseline_avg) / baseline_avg if baseline_avg != 0 else 0
        
        if change < -threshold:  # Negative change = regression
            logger.warning(f"Regression detected: {model_id}/{metric_name} ({change:.2%})")
            return {
                "model_id": model_id,
                "metric_name": metric_name,
                "baseline_avg": baseline_avg,
                "recent_avg": recent_avg,
                "change_percent": change * 100,
                "regression": True
            }
        
        return None

