"""
Weakness Detector
================

Detects weaknesses in model performance before they become game issues.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class WeaknessDetector:
    """
    Detects weaknesses in model performance.
    
    Monitors:
    - Performance degradation
    - Accuracy drops
    - Latency increases
    - Cost increases
    - Quality issues
    """
    
    def __init__(self, performance_tracker):
        """
        Initialize Weakness Detector.
        
        Args:
            performance_tracker: PerformanceTracker instance
        """
        self.performance_tracker = performance_tracker
        self.detected_weaknesses: List[Dict[str, Any]] = []
        logger.info("WeaknessDetector initialized")
    
    def detect_weaknesses(
        self,
        model_id: str,
        model_type: str
    ) -> List[Dict[str, Any]]:
        """
        Detect weaknesses for a model.
        
        Args:
            model_id: Model identifier
            model_type: Type of model
        
        Returns:
            List of detected weaknesses
        """
        logger.info(f"Detecting weaknesses for {model_id}")
        
        weaknesses = []
        
        # Check for regressions in key metrics
        key_metrics = ["accuracy", "latency_ms", "quality_score"]
        
        for metric_name in key_metrics:
            regression = self.performance_tracker.detect_regression(
                model_id=model_id,
                metric_name=metric_name,
                threshold=0.05
            )
            
            if regression:
                weaknesses.append({
                    "type": "regression",
                    "metric": metric_name,
                    "details": regression
                })
        
        # Check for absolute thresholds
        weaknesses.extend(self._check_absolute_thresholds(model_id, model_type))
        
        # Store detected weaknesses
        if weaknesses:
            self.detected_weaknesses.extend(weaknesses)
            logger.warning(f"Detected {len(weaknesses)} weaknesses for {model_id}")
        
        return weaknesses
    
    def _check_absolute_thresholds(
        self,
        model_id: str,
        model_type: str
    ) -> List[Dict[str, Any]]:
        """
        Check absolute performance thresholds.
        
        Checks:
        - Latency > max_latency_ms
        - Accuracy < min_accuracy
        - Quality score < min_quality
        """
        weaknesses = []
        
        # Get current performance metrics
        current_metrics = self.performance_tracker.get_latest_metrics(model_id)
        
        if not current_metrics:
            return weaknesses
        
        # Define thresholds based on model type
        thresholds = self._get_thresholds_for_model_type(model_type)
        
        # Check latency
        latency_ms = current_metrics.get("latency_ms", 0.0)
        max_latency_ms = thresholds.get("max_latency_ms", 1000.0)
        if latency_ms > max_latency_ms:
            weaknesses.append({
                "type": "threshold_exceeded",
                "metric": "latency_ms",
                "value": latency_ms,
                "threshold": max_latency_ms,
                "severity": "high" if latency_ms > max_latency_ms * 2 else "medium"
            })
        
        # Check accuracy
        accuracy = current_metrics.get("accuracy", 1.0)
        min_accuracy = thresholds.get("min_accuracy", 0.7)
        if accuracy < min_accuracy:
            weaknesses.append({
                "type": "threshold_below",
                "metric": "accuracy",
                "value": accuracy,
                "threshold": min_accuracy,
                "severity": "high" if accuracy < min_accuracy * 0.8 else "medium"
            })
        
        # Check quality score
        quality_score = current_metrics.get("quality_score", 1.0)
        min_quality = thresholds.get("min_quality", 0.75)
        if quality_score < min_quality:
            weaknesses.append({
                "type": "threshold_below",
                "metric": "quality_score",
                "value": quality_score,
                "threshold": min_quality,
                "severity": "high" if quality_score < min_quality * 0.8 else "medium"
            })
        
        # Check cost per token if available
        cost_per_token = current_metrics.get("cost_per_token", 0.0)
        max_cost_per_token = thresholds.get("max_cost_per_token", 0.01)
        if cost_per_token > max_cost_per_token:
            weaknesses.append({
                "type": "threshold_exceeded",
                "metric": "cost_per_token",
                "value": cost_per_token,
                "threshold": max_cost_per_token,
                "severity": "medium"
            })
        
        return weaknesses
    
    def _get_thresholds_for_model_type(self, model_type: str) -> Dict[str, float]:
        """Get performance thresholds for a model type."""
        # Default thresholds
        default_thresholds = {
            "max_latency_ms": 1000.0,
            "min_accuracy": 0.7,
            "min_quality": 0.75,
            "max_cost_per_token": 0.01
        }
        
        # Model-type specific thresholds
        type_thresholds = {
            "personality": {
                "max_latency_ms": 500.0,
                "min_accuracy": 0.8,
                "min_quality": 0.8
            },
            "facial": {
                "max_latency_ms": 800.0,
                "min_accuracy": 0.75,
                "min_quality": 0.78
            },
            "animals": {
                "max_latency_ms": 600.0,
                "min_accuracy": 0.75,
                "min_quality": 0.77
            },
            "building": {
                "max_latency_ms": 700.0,
                "min_accuracy": 0.72,
                "min_quality": 0.75
            }
        }
        
        # Merge type-specific with defaults
        thresholds = default_thresholds.copy()
        if model_type in type_thresholds:
            thresholds.update(type_thresholds[model_type])
        
        return thresholds
    
    def get_detected_weaknesses(
        self,
        model_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get detected weaknesses.
        
        Args:
            model_id: Filter by model ID (optional)
        
        Returns:
            List of weaknesses
        """
        if model_id:
            return [w for w in self.detected_weaknesses if w.get("model_id") == model_id]
        return self.detected_weaknesses

