# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Pairwise Tests for Failure Handler - Created by Tester and Reviewed by Reviewer.
Tests failure handling and recovery functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.recovery.failure_handler import FailureHandler


class TestFailureHandler:
    """Pairwise tests for FailureHandler."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Mock model registry."""
        registry = Mock()
        registry.get_model = AsyncMock(return_value=None)
        registry.get_current_model = AsyncMock(return_value=None)
        return registry
    
    @pytest.fixture
    def failure_handler(self, mock_model_registry):
        """Create FailureHandler instance."""
        with patch('services.srl_rlvr_training.recovery.failure_handler.boto3.client'):
            handler = FailureHandler(
                model_registry=mock_model_registry,
                s3_bucket="test-bucket",
                max_retries=3
            )
            return handler
    
    def test_failure_handler_initialization(self, failure_handler):
        """Test FailureHandler initialization."""
        assert failure_handler.model_registry is not None
        assert failure_handler.s3_bucket == "test-bucket"
        assert failure_handler.max_retries == 3
    
    def test_determine_recovery_strategy_spot_interruption(self, failure_handler):
        """Test recovery strategy for spot interruption."""
        strategy = failure_handler._determine_recovery_strategy(
            "Spot instance interrupted",
            "s3://bucket/checkpoint"
        )
        assert strategy == "resume_from_checkpoint"
    
    def test_determine_recovery_strategy_oom(self, failure_handler):
        """Test recovery strategy for out of memory."""
        strategy = failure_handler._determine_recovery_strategy(
            "Out of memory error",
            None
        )
        assert strategy == "retry_with_reduced_batch"
    
    def test_determine_recovery_strategy_validation_failure(self, failure_handler):
        """Test recovery strategy for validation failure."""
        strategy = failure_handler._determine_recovery_strategy(
            "Data validation failed",
            None
        )
        assert strategy == "retry_after_data_fix"
    
    def test_determine_recovery_strategy_unknown(self, failure_handler):
        """Test recovery strategy for unknown failure."""
        strategy = failure_handler._determine_recovery_strategy(
            "Unknown error",
            None
        )
        assert strategy == "retry_with_same_config"
    
    @pytest.mark.asyncio
    async def test_retry_with_reduced_batch(self, failure_handler):
        """Test retry with reduced batch size."""
        result = await failure_handler._retry_with_reduced_batch(
            "test-job",
            "gold"
        )
        
        assert result["success"] == True
        assert result["strategy"] == "retry_with_reduced_batch"
        assert "batch_size_reduction" in result
    
    @pytest.mark.asyncio
    async def test_retry_with_new_job(self, failure_handler):
        """Test retry with new job."""
        result = await failure_handler._retry_with_new_job(
            "test-job",
            "silver"
        )
        
        assert result["success"] == True
        assert result["strategy"] == "retry_with_new_job"
        assert result["retry_count"] == 1
    
    def test_parse_s3_uri(self, failure_handler):
        """Test S3 URI parsing."""
        bucket, key = failure_handler._parse_s3_uri("s3://test-bucket/path/file.json")
        assert bucket == "test-bucket"
        assert key == "path/file.json"
    
    def test_parse_s3_uri_invalid(self, failure_handler):
        """Test S3 URI parsing with invalid URI."""
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            failure_handler._parse_s3_uri("invalid-uri")










