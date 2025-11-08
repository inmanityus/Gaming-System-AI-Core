"""
GPU Metrics Publisher
Publishes NVIDIA GPU metrics to CloudWatch for auto-scaling decisions.

Metrics published:
- GPU utilization (%)
- GPU memory utilization (%)
- GPU temperature (C)
- GPU power usage (W)
- Queue depth (from application)
- Inference latency P95 (from application)
"""

import boto3
import time
import logging
import os
from datetime import datetime
from typing import Dict, List
import pynvml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPUMetricsPublisher:
    """Publishes GPU metrics to CloudWatch for auto-scaling."""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        self.namespace = 'AI-Gaming/GPU'
        
        # Initialize NVIDIA ML
        try:
            pynvml.nvmlInit()
            self.device_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"✅ Initialized NVIDIA ML - {self.device_count} GPU(s) detected")
        except Exception as e:
            logger.error(f"Failed to initialize NVIDIA ML: {e}")
            self.device_count = 0
        
        # Instance metadata
        self.instance_id = os.getenv('EC2_INSTANCE_ID', 'unknown')
        self.tier = os.getenv('GPU_TIER', 'unknown')  # gold, silver, bronze
        
        logger.info(f"Instance: {self.instance_id}, Tier: {self.tier}")
    
    def get_gpu_metrics(self, device_index: int = 0) -> Dict:
        """Get metrics for single GPU."""
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            
            # GPU utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = utilization.gpu
            memory_util = utilization.memory
            
            # Memory info
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_used_mb = memory_info.used / (1024 ** 2)
            memory_total_mb = memory_info.total / (1024 ** 2)
            memory_percent = (memory_info.used / memory_info.total) * 100
            
            # Temperature
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # Power
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # mW to W
            
            return {
                'gpu_utilization': gpu_util,
                'memory_utilization': memory_percent,
                'memory_used_mb': memory_used_mb,
                'memory_total_mb': memory_total_mb,
                'temperature_celsius': temperature,
                'power_watts': power_usage
            }
        
        except Exception as e:
            logger.error(f"Error getting GPU metrics: {e}")
            return {}
    
    def publish_metrics(self, metrics: Dict):
        """Publish metrics to CloudWatch."""
        try:
            metric_data = []
            
            # GPU utilization
            if 'gpu_utilization' in metrics:
                metric_data.append({
                    'MetricName': 'GPUUtilization',
                    'Value': metrics['gpu_utilization'],
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'InstanceId', 'Value': self.instance_id},
                        {'Name': 'Tier', 'Value': self.tier}
                    ]
                })
            
            # Memory utilization
            if 'memory_utilization' in metrics:
                metric_data.append({
                    'MetricName': 'GPUMemoryUtilization',
                    'Value': metrics['memory_utilization'],
                    'Unit': 'Percent',
                    'Dimensions': [
                        {'Name': 'InstanceId', 'Value': self.instance_id},
                        {'Name': 'Tier', 'Value': self.tier}
                    ]
                })
            
            # Temperature
            if 'temperature_celsius' in metrics:
                metric_data.append({
                    'MetricName': 'GPUTemperature',
                    'Value': metrics['temperature_celsius'],
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'InstanceId', 'Value': self.instance_id},
                        {'Name': 'Tier', 'Value': self.tier}
                    ]
                })
            
            # Power usage
            if 'power_watts' in metrics:
                metric_data.append({
                    'MetricName': 'GPUPowerUsage',
                    'Value': metrics['power_watts'],
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'InstanceId', 'Value': self.instance_id},
                        {'Name': 'Tier', 'Value': self.tier}
                    ]
                })
            
            # Publish to CloudWatch
            if metric_data:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data
                )
                
                logger.info(f"✅ Published {len(metric_data)} metrics to CloudWatch")
        
        except Exception as e:
            logger.error(f"Error publishing metrics: {e}")
    
    def run(self, interval_seconds: int = 60):
        """Run publisher loop."""
        logger.info(f"🚀 Starting GPU metrics publisher (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Collect metrics from all GPUs
                for device_idx in range(self.device_count):
                    metrics = self.get_gpu_metrics(device_idx)
                    if metrics:
                        self.publish_metrics(metrics)
                
                # Sleep until next collection
                time.sleep(interval_seconds)
            
            except KeyboardInterrupt:
                logger.info("Shutting down GPU metrics publisher")
                break
            except Exception as e:
                logger.error(f"Error in publisher loop: {e}")
                time.sleep(interval_seconds)


if __name__ == '__main__':
    publisher = GPUMetricsPublisher()
    publisher.run(interval_seconds=60)

