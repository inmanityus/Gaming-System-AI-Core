"""
Unit Tests for GPU Metrics Publisher
Tests metric collection and CloudWatch publishing logic.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from publisher import GPUMetricsPublisher


class TestGPUMetricsCollection:
    """Test GPU metrics collection."""
    
    @patch('publisher.pynvml')
    def test_init_with_gpu(self, mock_nvml):
        """Initialize with GPU available."""
        mock_nvml.nvmlInit.return_value = None
        mock_nvml.nvmlDeviceGetCount.return_value = 1
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = Mock()
        
        publisher = GPUMetricsPublisher()
        
        assert publisher.device_count == 1
        assert len(publisher.device_handles) == 1
        mock_nvml.nvmlInit.assert_called_once()
    
    @patch('publisher.pynvml')
    def test_init_without_gpu(self, mock_nvml):
        """Initialize on CPU instance (no GPU)."""
        mock_nvml.nvmlInit.side_effect = Exception("No GPU")
        
        publisher = GPUMetricsPublisher()
        
        assert publisher.device_count == 0
        assert len(publisher.device_handles) == 0
    
    @patch('publisher.pynvml')
    def test_get_metrics_success(self, mock_nvml):
        """Successfully collect GPU metrics."""
        # Setup mocks
        mock_handle = Mock()
        mock_util = Mock()
        mock_util.gpu = 75
        mock_util.memory = 80
        
        mock_memory = Mock()
        mock_memory.used = 20 * 1024 ** 3  # 20GB
        mock_memory.total = 24 * 1024 ** 3  # 24GB
        
        mock_nvml.nvmlDeviceGetUtilizationRates.return_value = mock_util
        mock_nvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory
        mock_nvml.nvmlDeviceGetTemperature.return_value = 65
        mock_nvml.nvmlDeviceGetPowerUsage.return_value = 250000  # 250W in mW
        
        publisher = GPUMetricsPublisher()
        publisher.device_handles = [mock_handle]
        publisher.device_count = 1
        
        metrics = publisher.get_gpu_metrics(0)
        
        assert metrics['gpu_utilization'] == 75
        assert 'memory_utilization' in metrics
        assert metrics['temperature_celsius'] == 65
        assert metrics['power_watts'] == 250.0
    
    @patch('publisher.pynvml')
    def test_get_metrics_partial_failure(self, mock_nvml):
        """Handles partial metric collection failure gracefully."""
        mock_handle = Mock()
        
        # GPU util succeeds
        mock_util = Mock()
        mock_util.gpu = 75
        mock_util.memory = 80
        mock_nvml.nvmlDeviceGetUtilizationRates.return_value = mock_util
        
        # Memory fails
        mock_nvml.nvmlDeviceGetMemoryInfo.side_effect = Exception("Memory query failed")
        
        # Temperature succeeds
        mock_nvml.nvmlDeviceGetTemperature.return_value = 65
        
        publisher = GPUMetricsPublisher()
        publisher.device_handles = [mock_handle]
        publisher.device_count = 1
        
        metrics = publisher.get_gpu_metrics(0)
        
        # Should have some metrics despite partial failure
        assert 'gpu_utilization' in metrics
        assert 'temperature_celsius' in metrics


class TestCloudWatchPublishing:
    """Test CloudWatch metric publishing."""
    
    @patch('publisher.boto3')
    @patch('publisher.pynvml')
    def test_publish_with_retry(self, mock_nvml, mock_boto3):
        """Publishing retries on failure."""
        mock_cloudwatch = Mock()
        mock_boto3.client.return_value = mock_cloudwatch
        
        # First attempt fails, second succeeds
        mock_cloudwatch.put_metric_data.side_effect = [
            Exception("Temporary failure"),
            None  # Success
        ]
        
        publisher = GPUMetricsPublisher()
        publisher.device_count = 0  # Skip GPU init
        
        metrics = {'gpu_utilization': 75}
        publisher.publish_metrics(metrics, 0)
        
        # Should have retried
        assert mock_cloudwatch.put_metric_data.call_count == 2
    
    @patch('publisher.boto3')
    @patch('publisher.pynvml')
    def test_publish_handles_empty_metrics(self, mock_nvml, mock_boto3):
        """Handles empty metrics gracefully."""
        mock_cloudwatch = Mock()
        mock_boto3.client.return_value = mock_cloudwatch
        
        publisher = GPUMetricsPublisher()
        publisher.device_count = 0
        
        # Should not crash
        publisher.publish_metrics({}, 0)
        publisher.publish_metrics(None, 0)
        
        # Should not call CloudWatch with empty data
        assert mock_cloudwatch.put_metric_data.call_count == 0

