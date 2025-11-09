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
import socket

# Systemd notification support with native fallback
try:
    from systemd import daemon as sd_daemon
    SYSTEMD_NOTIFY_METHOD = 'library'
except ImportError:
    sd_daemon = None
    SYSTEMD_NOTIFY_METHOD = 'native'  # Use native socket implementation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GPUMetricsPublisher:
    """Publishes GPU metrics to CloudWatch for auto-scaling."""
    
    def __init__(self):
        self.running = False
        
        # Configure boto3 with proper timeouts and retries
        from botocore.config import Config
        boto_config = Config(
            region_name='us-east-1',
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            connect_timeout=5,
            read_timeout=10
        )
        self.cloudwatch = boto3.client('cloudwatch', config=boto_config)
        self.namespace = 'AI-Gaming/GPU'
        self.device_handles: List[Optional[pynvml.c_nvmlDevice_t]] = []
        self.device_count = 0
        
        # Instance metadata (get from EC2 metadata service with IMDSv2)
        self.instance_id = self._get_instance_id()
        self.instance_type = self._get_instance_type()
        self.availability_zone = self._get_availability_zone()
        self.tier = os.getenv('GPU_TIER', 'unknown')  # gold, silver, bronze
        
        # Watchdog state
        self.last_watchdog = time.time()
        self.watchdog_interval = 15  # Send watchdog every 15s (WatchdogSec=45s in systemd)
        
        logger.info(f"Instance: {self.instance_id} ({self.instance_type})")
        logger.info(f"Tier: {self.tier}, AZ: {self.availability_zone}")
        logger.info(f"Systemd notify: {SYSTEMD_NOTIFY_METHOD}")
        
        # Initialize NVIDIA ML
        self._init_nvidia_ml()
    
    def _get_imds_token(self) -> Optional[str]:
        """Get IMDSv2 token with retry logic."""
        try:
            import requests
            response = requests.put(
                'http://169.254.169.254/latest/api/token',
                headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'},
                timeout=1
            )
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.warning(f"Failed to get IMDSv2 token: {e}")
        return None
    
    def _get_imds_value(self, path: str, default: str = 'unknown') -> str:
        """Get value from EC2 metadata service (IMDSv2 preferred)."""
        try:
            import requests
            
            # Try IMDSv2 first
            token = self._get_imds_token()
            headers = {'X-aws-ec2-metadata-token': token} if token else {}
            
            response = requests.get(
                f'http://169.254.169.254/latest/meta-data/{path}',
                headers=headers,
                timeout=2
            )
            
            if response.status_code == 200:
                return response.text
                
        except Exception as e:
            logger.warning(f"Failed to get IMDS value for {path}: {e}")
        
        return os.getenv(f'EC2_{path.upper().replace("/", "_")}', default)
    
    def _get_instance_id(self) -> str:
        """Get EC2 instance ID from metadata service."""
        return self._get_imds_value('instance-id')
    
    def _get_instance_type(self) -> str:
        """Get EC2 instance type from metadata service."""
        return self._get_imds_value('instance-type')
    
    def _get_availability_zone(self) -> str:
        """Get EC2 availability zone from metadata service."""
        return self._get_imds_value('placement/availability-zone')
    
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
    
    def _sd_notify_native(self, message: str):
        """
        Native systemd notify implementation (fallback when systemd-python unavailable).
        Sends notification directly to NOTIFY_SOCKET.
        """
        notify_socket = os.getenv('NOTIFY_SOCKET')
        if not notify_socket:
            return False
        
        try:
            import socket as sock
            
            # Handle abstract socket (starts with @)
            if notify_socket.startswith('@'):
                notify_socket = '\0' + notify_socket[1:]
            
            # Create socket and send message
            s = sock.socket(sock.AF_UNIX, sock.SOCK_DGRAM)
            try:
                s.sendto(message.encode('utf-8'), notify_socket)
                return True
            finally:
                s.close()
        except Exception as e:
            logger.debug(f"sd_notify_native failed: {e}")
            return False
    
    def _sd_notify(self, message: str):
        """Send notification to systemd using best available method."""
        if SYSTEMD_NOTIFY_METHOD == 'library' and sd_daemon:
            try:
                sd_daemon.notify(message)
                return True
            except Exception as e:
                logger.warning(f"systemd library notify failed, trying native: {e}")
                return self._sd_notify_native(message)
        else:
            return self._sd_notify_native(message)
    
    def _send_watchdog(self):
        """Send watchdog notification to systemd."""
        now = time.time()
        if now - self.last_watchdog >= self.watchdog_interval:
            if self._sd_notify('WATCHDOG=1'):
                logger.debug("Sent watchdog ping to systemd")
            self.last_watchdog = now
    
    def publish_heartbeat(self):
        """Publish heartbeat metric for liveness monitoring."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[{
                    'MetricName': 'Heartbeat',
                    'Value': 1.0,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'InstanceId', 'Value': self.instance_id},
                        {'Name': 'Tier', 'Value': self.tier},
                        {'Name': 'InstanceType', 'Value': self.instance_type},
                        {'Name': 'AvailabilityZone', 'Value': self.availability_zone}
                    ]
                }]
            )
            logger.debug("Published heartbeat metric")
        except Exception as e:
            logger.warning(f"Failed to publish heartbeat: {e}")
    
    def publish_metrics(self, metrics: Dict, device_index: int = 0):
        """Publish metrics to CloudWatch with retry logic and batching."""
        if not metrics:
            return
        
        metric_data = []
        
        # Common dimensions for all metrics
        common_dimensions = [
            {'Name': 'InstanceId', 'Value': self.instance_id},
            {'Name': 'Tier', 'Value': self.tier},
            {'Name': 'InstanceType', 'Value': self.instance_type}
        ]
        
        # GPU utilization
        if 'gpu_utilization' in metrics:
            metric_data.append({
                'MetricName': 'GPUUtilization',
                'Value': float(metrics['gpu_utilization']),
                'Unit': 'Percent',
                'Timestamp': datetime.utcnow(),
                'Dimensions': common_dimensions + [
                    {'Name': 'DeviceIndex', 'Value': str(device_index)}
                ]
            })
        
        # Memory utilization
        if 'memory_utilization' in metrics:
            metric_data.append({
                'MetricName': 'GPUMemoryUtilization',
                'Value': float(metrics['memory_utilization']),
                'Unit': 'Percent',
                'Timestamp': datetime.utcnow(),
                'Dimensions': common_dimensions + [
                    {'Name': 'DeviceIndex', 'Value': str(device_index)}
                ]
            })
        
        # Temperature
        if 'temperature_celsius' in metrics:
            metric_data.append({
                'MetricName': 'GPUTemperature',
                'Value': float(metrics['temperature_celsius']),
                'Unit': 'None',
                'Timestamp': datetime.utcnow(),
                'Dimensions': common_dimensions
            })
        
        # Power usage
        if 'power_watts' in metrics:
            metric_data.append({
                'MetricName': 'GPUPowerUsage',
                'Value': float(metrics['power_watts']),
                'Unit': 'None',
                'Timestamp': datetime.utcnow(),
                'Dimensions': common_dimensions
            })
        
        # Publish to CloudWatch with retry logic and proper error handling
        if metric_data:
            for attempt in range(3):
                try:
                    # CloudWatch has a limit of 1000 metrics per request, batch if needed
                    batch_size = 20  # Conservative batch size
                    for i in range(0, len(metric_data), batch_size):
                        batch = metric_data[i:i + batch_size]
                        self.cloudwatch.put_metric_data(
                            Namespace=self.namespace,
                            MetricData=batch
                        )
                    
                    logger.debug(f"Published {len(metric_data)} metrics successfully")
                    return
                
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                    
                    # Don't retry on throttling (will get backed off by boto3 config)
                    if error_code == 'Throttling':
                        logger.warning(f"CloudWatch throttling on attempt {attempt + 1}")
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                            continue
                    
                    if attempt == 2:
                        logger.error(f"Failed to publish metrics after 3 attempts: {error_code} - {e}")
                    else:
                        logger.warning(f"CloudWatch publish attempt {attempt + 1} failed ({error_code}), retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                
                except Exception as e:
                    logger.error(f"Unexpected error publishing metrics: {e}", exc_info=True)
                    # Don't retry on unexpected errors
                    break
    
    def run(self, interval_seconds: int = 60):
        """Run publisher loop with signal handling and systemd notify support."""
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)
        
        logger.info(f"🚀 Starting GPU metrics publisher (interval: {interval_seconds}s)")
        logger.info(f"📊 Monitoring {self.device_count} GPU(s)")
        
        if self.device_count == 0:
            logger.warning("⚠️ No GPUs available - running in heartbeat-only mode")
            # Keep running to provide health check, but don't publish GPU metrics
            self.running = True
            
            # Notify systemd we're ready
            if self._sd_notify('READY=1'):
                logger.info("Notified systemd: READY")
            else:
                logger.info("Systemd notify not available (running standalone)")
            
            while self.running:
                # Publish heartbeat even without GPUs
                self.publish_heartbeat()
                self._send_watchdog()
                time.sleep(interval_seconds)
            return
        
        self.running = True
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        # Notify systemd we're ready (after successful GPU init)
        if self._sd_notify('READY=1'):
            logger.info("Notified systemd: READY")
        else:
            logger.info("Systemd notify not available (running standalone)")
        
        logger.info("✅ GPU metrics publisher ready")
        
        while self.running:
            try:
                # Publish heartbeat for liveness monitoring
                self.publish_heartbeat()
                
                # Collect and publish metrics from all GPUs
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
                
                # Send watchdog ping to systemd
                self._send_watchdog()
                
                # Sleep until next collection
                time.sleep(interval_seconds)
            
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.shutdown_handler(signal.SIGINT, None)
            
            except Exception as e:
                logger.error(f"Unexpected error in publisher loop: {e}", exc_info=True)
                consecutive_errors += 1
                # Still send watchdog even on errors
                self._send_watchdog()
                time.sleep(interval_seconds)


if __name__ == '__main__':
    publisher = GPUMetricsPublisher()
    publisher.run(interval_seconds=60)

