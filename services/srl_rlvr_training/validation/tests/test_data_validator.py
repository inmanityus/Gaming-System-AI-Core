"""
Pairwise Tests for Data Validator - Created by Tester and Reviewed by Reviewer.
Tests data validation functionality.
"""

import pytest
from unittest.mock import Mock, patch
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.validation.data_validator import DataValidator


class TestDataValidator:
    """Pairwise tests for DataValidator."""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client."""
        with patch('services.srl_rlvr_training.validation.data_validator.boto3.client') as mock_client:
            mock_s3 = Mock()
            mock_client.return_value = mock_s3
            yield mock_s3
    
    @pytest.fixture
    def validator(self, mock_s3_client):
        """Create DataValidator instance."""
        return DataValidator(s3_bucket="test-bucket")
    
    @pytest.mark.asyncio
    async def test_validate_jsonl_format(self, validator, mock_s3_client):
        """Test validation of JSONL format data."""
        # Mock S3 response - create 100 examples to meet minimum for gold tier
        jsonl_content = '\n'.join([f'{{"prompt": "test{i}", "expected_output": "output{i}"}}' for i in range(100)])
        mock_s3_client.get_object.return_value = {
            'Body': Mock(read=lambda: jsonl_content.encode('utf-8'))
        }
        
        result = await validator.validate_training_data(
            data_s3_uri="s3://test-bucket/data.jsonl",
            tier="gold",
            expected_format="jsonl"
        )
        
        assert result["valid"] == True
        assert result["data_count"] == 100
        assert len(result["issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_missing_required_fields(self, validator, mock_s3_client):
        """Test validation detects missing required fields."""
        jsonl_content = '{"prompt": "test1"}\n{"expected_output": "output2"}'
        mock_s3_client.get_object.return_value = {
            'Body': Mock(read=lambda: jsonl_content.encode('utf-8'))
        }
        
        result = await validator.validate_training_data(
            data_s3_uri="s3://test-bucket/data.jsonl",
            tier="gold",
            expected_format="jsonl"
        )
        
        assert result["valid"] == False
        assert len(result["issues"]) > 0
        assert any("missing required field" in issue.lower() for issue in result["issues"])
    
    @pytest.mark.asyncio
    async def test_validate_minimum_count(self, validator, mock_s3_client):
        """Test validation enforces minimum data count per tier."""
        # Create data with less than minimum for gold tier (100)
        jsonl_content = '\n'.join([f'{{"prompt": "test{i}", "expected_output": "output{i}"}}' for i in range(50)])
        mock_s3_client.get_object.return_value = {
            'Body': Mock(read=lambda: jsonl_content.encode('utf-8'))
        }
        
        result = await validator.validate_training_data(
            data_s3_uri="s3://test-bucket/data.jsonl",
            tier="gold",
            expected_format="jsonl"
        )
        
        assert result["valid"] == False
        assert any("below minimum" in issue.lower() for issue in result["issues"])
    
    @pytest.mark.asyncio
    async def test_validate_empty_data(self, validator, mock_s3_client):
        """Test validation detects empty data."""
        mock_s3_client.get_object.return_value = {
            'Body': Mock(read=lambda: b'')
        }
        
        result = await validator.validate_training_data(
            data_s3_uri="s3://test-bucket/data.jsonl",
            tier="gold",
            expected_format="jsonl"
        )
        
        assert result["valid"] == False
        # Check for empty data or data count issues
        assert any("empty" in issue.lower() or "count" in issue.lower() or "below minimum" in issue.lower() for issue in result["issues"])
    
    @pytest.mark.asyncio
    async def test_validate_data_quality_empty_fields(self, validator, mock_s3_client):
        """Test validation detects empty prompt/expected_output fields."""
        jsonl_content = '{"prompt": "", "expected_output": "output1"}\n{"prompt": "test2", "expected_output": ""}'
        mock_s3_client.get_object.return_value = {
            'Body': Mock(read=lambda: jsonl_content.encode('utf-8'))
        }
        
        result = await validator.validate_training_data(
            data_s3_uri="s3://test-bucket/data.jsonl",
            tier="gold",
            expected_format="jsonl"
        )
        
        assert result["valid"] == False
        assert any("empty" in issue.lower() for issue in result["issues"])

