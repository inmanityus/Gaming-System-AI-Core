"""
CloudWatch Metrics Publisher - Publishes custom metrics for SRL-RLVR training system.
"""

import boto3
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

cloudwatch = boto3.client('cloudwatch')


class CloudWatchMetricsPublisher:
    """Publishes custom metrics to CloudWatch for monitoring."""
    
    def __init__(self, namespace: str = "Custom/SRL-RLVR"):
        """
        Initialize CloudWatch Metrics Publisher.
        
        Args:
            namespace: CloudWatch namespace for metrics
        """
        self.namespace = namespace
        self.cloudwatch = cloudwatch
    
    def publish_model_performance(
        self,
        tier: str,
        performance_score: float,
        model_id: Optional[str] = None
    ) -> None:
        """
        Publish model performance metric.
        
        Args:
            tier: Model tier (gold, silver, bronze)
            performance_score: Performance score (0.0 to 1.0)
            model_id: Optional model ID
        """
        dimensions = [
            {"Name": "Tier", "Value": tier}
        ]
        
        if model_id:
            dimensions.append({"Name": "ModelId", "Value": model_id})
        
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    "MetricName": "ModelPerformance",
                    "Dimensions": dimensions,
                    "Value": performance_score,
                    "Unit": "Percent",
                    "Timestamp": datetime.now(timezone.utc)
                }
            ]
        )
    
    def publish_inference_latency(
        self,
        tier: str,
        latency_ms: float,
        model_id: Optional[str] = None
    ) -> None:
        """
        Publish inference latency metric.
        
        Args:
            tier: Model tier (gold, silver, bronze)
            latency_ms: Latency in milliseconds
            model_id: Optional model ID
        """
        dimensions = [
            {"Name": "Tier", "Value": tier}
        ]
        
        if model_id:
            dimensions.append({"Name": "ModelId", "Value": model_id})
        
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    "MetricName": "InferenceLatency",
                    "Dimensions": dimensions,
                    "Value": latency_ms,
                    "Unit": "Milliseconds",
                    "Timestamp": datetime.now(timezone.utc)
                }
            ]
        )
    
    def publish_model_drift(
        self,
        tier: str,
        drift_score: float,
        model_id: Optional[str] = None
    ) -> None:
        """
        Publish model drift metric.
        
        Args:
            tier: Model tier (gold, silver, bronze)
            drift_score: Drift score (0.0 to 1.0)
            model_id: Optional model ID
        """
        dimensions = [
            {"Name": "Tier", "Value": tier}
        ]
        
        if model_id:
            dimensions.append({"Name": "ModelId", "Value": model_id})
        
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    "MetricName": "ModelDrift",
                    "Dimensions": dimensions,
                    "Value": drift_score,
                    "Unit": "Percent",
                    "Timestamp": datetime.now(timezone.utc)
                }
            ]
        )
    
    def publish_training_metrics(
        self,
        tier: str,
        loss: float,
        learning_rate: float,
        kl_divergence: float,
        training_job_name: str
    ) -> None:
        """
        Publish training metrics.
        
        Args:
            tier: Model tier (gold, silver, bronze)
            loss: Training loss
            learning_rate: Current learning rate
            kl_divergence: KL divergence value
            training_job_name: SageMaker training job name
        """
        dimensions = [
            {"Name": "Tier", "Value": tier},
            {"Name": "TrainingJobName", "Value": training_job_name}
        ]
        
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    "MetricName": "TrainingLoss",
                    "Dimensions": dimensions,
                    "Value": loss,
                    "Unit": "None",
                    "Timestamp": datetime.now(timezone.utc)
                },
                {
                    "MetricName": "LearningRate",
                    "Dimensions": dimensions,
                    "Value": learning_rate,
                    "Unit": "None",
                    "Timestamp": datetime.now(timezone.utc)
                },
                {
                    "MetricName": "KLDivergence",
                    "Dimensions": dimensions,
                    "Value": kl_divergence,
                    "Unit": "None",
                    "Timestamp": datetime.now(timezone.utc)
                }
            ]
        )






