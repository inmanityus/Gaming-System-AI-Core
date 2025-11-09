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
from botocore.exceptions import ClientError
import time
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional
import pynvml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GPUMetricsPublisher:
    """Publishes GPU metrics to CloudWatch for auto-scaling."""
    
    def __init__(self):
        self.running = False
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        self.namespace = 'AI-Gaming/GPU'
        self.device_handles: List[Optional[pynvml.c_nvmlDevice_t]] = []
        self.device_count = 0
        
        # Instance metadata (get from EC2 metadata service)
        self.instance_id = self._get_instance_id()
        self.tier = os.getenv('GPU_TIER', 'unknown')  # gold, silver, bronze
        
        logger.info(f"Instance: {self.instance_id}, Tier: {self.tier}")
        
        # Initialize NVIDIA ML
        self._init_nvidia_ml()
    
    def _get_instance_id(self) -> str:
        """Get EC2 instance ID from metadata service."""
        try:
            import requests
            response = requests.get(
                'http://169.254.169.254/latest/meta-data/instance-id',
                timeout=1
            )
            return response.text
        except Exception:
            return os.getenv('EC2_INSTANCE_ID', 'unknown')
    
    def _init_nvidia_ml(self):
        """Initialize NVIDIA ML with proper error handling."""
        try:
            pynvml.nvmlInit()
            self.device_count = pynvml.nvmlDeviceGetCount()
            
            # Get handles for all devices
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                self.device_handles.append(handle)
            
            logger.info(f"✅ Initialized NVIDIA ML - {self.device_count} GPU(s) detected")
        
        except pynvml.NVMLError_LibraryNotFound:
            logger.warning("⚠️ NVIDIA ML library not found - no GPU metrics available")
            self.device_count = 0
        except pynvml.NVMLError_DriverNotLoaded:
            logger.warning("⚠️ NVIDIA driver not loaded - no GPU metrics available")
            self.device_count = 0
        except Exception as e:
            logger.error(f"Failed to initialize NVIDIA ML: {e}")
            self.device_count = 0
    
    def shutdown_handler(self, signum, frame):
        """Handle graceful shutdown on SIGTERM/SIGINT."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
        # Cleanup NVIDIA ML
        if self.device_count > 0:
            try:
                pynvml.nvmlShutdown()
                logger.info("✅ NVIDIA ML shutdown complete")
            except Exception as e:
                logger.error(f"Error during NVIDIA ML shutdown: {e}")
        
        sys.exit(0)
    
    def get_gpu_metrics(self, device_index: int = 0) -> Dict:
        """Get metrics for single GPU with comprehensive error handling."""
        if device_index >= len(self.device_handles):
            logger.error(f"Invalid device index: {device_index}")
            return {}
        
        handle = self.device_handles[device_index]
        if not handle:
            return {}
        
        metrics = {}
        
        try:
            # GPU utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            metrics['gpu_utilization'] = utilization.gpu
            metrics['memory_utilization_percent'] = utilization.memory
        except pynvml.NVMLError as e:
            logger.warning(f"Failed to get GPU utilization: {e}")
        
        try:
            # Memory info
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            metrics['memory_used_mb'] = memory_info.used / (1024 ** 2)
            metrics['memory_total_mb'] = memory_info.total / (1024 ** 2)
            metrics['memory_utilization'] = (memory_info.used / memory_info.total) * 100
        except pynvml.NVMLError as e:
            logger.warning(f"Failed to get memory info: {e}")
        
        try:
            # Temperature
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            metrics['temperature_celsius'] = temperature
        except pynvml.NVMLError as e:
            logger.warning(f"Failed to get temperature: {e}")
        
        try:
            # Power
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # mW to W
            metrics['power_watts'] = power_usage
        except pynvml.NVMLError as e:
            logger.warning(f"Failed to get power usage: {e}")
        
        return metrics
    
    def publish_metrics(self, metrics: Dict, device_index: int = 0):
        """Publish metrics to CloudWatch with retry logic."""
        if not metrics:
            return
        
        metric_data = []
        
        # GPU utilization
        if 'gpu_utilization' in metrics:
            metric_data.append({
                'MetricName': 'GPUUtilization',
                'Value': float(metrics['gpu_utilization']),
                'Unit': 'Percent',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'InstanceId', 'Value': self.instance_id},
                    {'Name': 'Tier', 'Value': self.tier},
                    {'Name': 'DeviceIndex', 'Value': str(device_index)}
                ]
            })
        
        # Memory utilization
        if 'memory_utilization' in metrics:
            metric_data.append({
                'MetricName': 'GPUMemoryUtilization',
                'Value': float(metrics['memory_utilization']),
                'Unit': 'Percent',
                'Dimensions': [
                    {'Name': 'InstanceId', 'Value': self.instance_id},
                    {'Name': 'Tier', 'Value': self.tier},
                    {'Name': 'DeviceIndex', 'Value': str(device_index)}
                ]
            })
        
        # Temperature
        if 'temperature_celsius' in metrics:
            metric_data.append({
                'MetricName': 'GPUTemperature',
                'Value': float(metrics['temperature_celsius']),
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
                'Value': float(metrics['power_watts']),
                'Unit': 'None',
                'Dimensions': [
                    {'Name': 'InstanceId', 'Value': self.instance_id},
                    {'Name': 'Tier', 'Value': self.tier}
                ]
            })
        
        # Publish to CloudWatch with retry logic
        if metric_data:
            for attempt in range(3):
                try:
                    self.cloudwatch.put_metric_data(
                        Namespace=self.namespace,
                        MetricData=metric_data
                    )
                    logger.info(f"✅ Published {len(metric_data)} metrics (attempt {attempt + 1})")
                    return
                
                except ClientError as e:
                    if attempt == 2:
                        logger.error(f"Failed to publish metrics after 3 attempts: {e}")
                    else:
                        logger.warning(f"CloudWatch publish attempt {attempt + 1} failed, retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                
                except Exception as e:
                    logger.error(f"Unexpected error publishing metrics: {e}")
                    break
    
    def run(self, interval_seconds: int = 60):
        """Run publisher loop with signal handling."""
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)
        
        logger.info(f"🚀 Starting GPU metrics publisher (interval: {interval_seconds}s)")
        logger.info(f"📊 Monitoring {self.device_count} GPU(s)")
        
        if self.device_count == 0:
            logger.warning("⚠️ No GPUs available - running in monitoring-only mode")
            # Keep running to provide health check, but don't publish metrics
            self.running = True
            while self.running:
                time.sleep(interval_seconds)
            return
        
        self.running = True
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                # Collect metrics from all GPUs
                success = False
                for device_idx in range(self.device_count):
                    metrics = self.get_gpu_metrics(device_idx)
                    if metrics:
                        self.publish_metrics(metrics, device_idx)
                        success = True
                
                if success:
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    logger.warning(f"Failed to collect metrics (error count: {consecutive_errors})")
                
                # If too many consecutive errors, alert but keep running
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"⚠️ {consecutive_errors} consecutive failures - metrics collection degraded")
                    consecutive_errors = 0  # Reset to avoid spam
                
                # Sleep until next collection
                time.sleep(interval_seconds)
            
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.shutdown_handler(signal.SIGINT, None)
            
            except Exception as e:
                logger.error(f"Unexpected error in publisher loop: {e}", exc_info=True)
                consecutive_errors += 1
                time.sleep(interval_seconds)


if __name__ == '__main__':
    publisher = GPUMetricsPublisher()
    publisher.run(interval_seconds=60)

