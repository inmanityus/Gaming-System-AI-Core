"""
Pairwise Tests for Distillation Pipeline - Created by Tester and Reviewed by Reviewer.
Tests knowledge distillation functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.distillation.distillation_pipeline import DistillationPipeline
from services.srl_rlvr_training.distillation.trace_collector import TraceCollector


class TestDistillationPipeline:
    """Pairwise tests for DistillationPipeline."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Mock model registry."""
        registry = Mock()
        registry.get_model = AsyncMock(return_value=None)
        return registry
    
    @pytest.fixture
    def mock_trace_collector(self):
        """Mock trace collector."""
        collector = Mock(spec=TraceCollector)
        collector.collect_traces = Mock(return_value="s3://bucket/traces.json")
        return collector
    
    @pytest.fixture
    def distillation_pipeline(self, mock_model_registry, mock_trace_collector):
        """Create DistillationPipeline instance."""
        with patch('services.srl_rlvr_training.distillation.distillation_pipeline.boto3.client'):
            pipeline = DistillationPipeline(
                model_registry=mock_model_registry,
                trace_collector=mock_trace_collector,
                s3_bucket="test-bucket"
            )
            return pipeline
    
    @pytest.mark.asyncio
    async def test_distill_bronze_to_silver_initialization(self, distillation_pipeline):
        """Test Bronze to Silver distillation initialization."""
        # Verify pipeline is initialized correctly
        assert distillation_pipeline.model_registry is not None
        assert distillation_pipeline.trace_collector is not None
        assert distillation_pipeline.s3_bucket == "test-bucket"
    
    @pytest.mark.asyncio
    async def test_distill_silver_to_gold_initialization(self, distillation_pipeline):
        """Test Silver to Gold distillation initialization."""
        # Verify pipeline supports Silver to Gold distillation
        assert distillation_pipeline is not None
        # Test that the method exists
        assert hasattr(distillation_pipeline, 'distill_silver_to_gold')
    
    def test_parse_s3_uri(self, distillation_pipeline):
        """Test S3 URI parsing."""
        bucket, key = distillation_pipeline._parse_s3_uri("s3://test-bucket/path/to/file.json")
        assert bucket == "test-bucket"
        assert key == "path/to/file.json"
    
    def test_parse_s3_uri_invalid(self, distillation_pipeline):
        """Test S3 URI parsing with invalid URI."""
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            distillation_pipeline._parse_s3_uri("invalid-uri")
    
    @pytest.mark.asyncio
    async def test_prepare_distillation_data(self, distillation_pipeline):
        """Test preparation of distillation data from traces."""
        traces = [
            {
                "prompt": "test prompt",
                "expert_output": "expert response",
                "context": {"tier": "bronze"}
            }
        ]
        
        # Mock tokenizer
        mock_tokenizer = Mock()
        
        train_data = distillation_pipeline._prepare_distillation_data(traces, mock_tokenizer)
        
        assert len(train_data) == 1
        assert train_data[0]["input"] == "test prompt"
        assert train_data[0]["output"] == "expert response"
    
    @pytest.mark.asyncio
    async def test_prepare_distillation_data_empty_traces(self, distillation_pipeline):
        """Test preparation with empty traces."""
        traces = []
        mock_tokenizer = Mock()
        
        train_data = distillation_pipeline._prepare_distillation_data(traces, mock_tokenizer)
        
        assert len(train_data) == 0
    
    @pytest.mark.asyncio
    async def test_prepare_distillation_data_missing_fields(self, distillation_pipeline):
        """Test preparation with traces missing required fields."""
        traces = [
            {"prompt": "test"},  # Missing expert_output
            {"expert_output": "output"}  # Missing prompt
        ]
        mock_tokenizer = Mock()
        
        train_data = distillation_pipeline._prepare_distillation_data(traces, mock_tokenizer)
        
        # Should skip invalid traces
        assert len(train_data) == 0


