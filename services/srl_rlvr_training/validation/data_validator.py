"""
Data Validator - Validates training data before training jobs.
Prevents training failures due to invalid data.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates training data before training jobs.
    
    Validations:
    - Data format and structure
    - Required fields present
    - Data quality checks
    - Size and count validation
    """
    
    def __init__(self, s3_bucket: Optional[str] = None):
        """
        Initialize Data Validator.
        
        Args:
            s3_bucket: S3 bucket for training data
        """
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket or os.getenv('SRL_TRAINING_DATA_S3_BUCKET', 'srl-training-data')
        
        logger.info(f"DataValidator initialized (bucket: {self.s3_bucket})")
    
    async def validate_training_data(
        self,
        data_s3_uri: str,
        tier: str,
        expected_format: str = "jsonl"
    ) -> Dict[str, Any]:
        """
        Validate training data before training job.
        
        Args:
            data_s3_uri: S3 URI to training data
            tier: Model tier (gold, silver, bronze)
            expected_format: Expected data format (jsonl, json, parquet)
        
        Returns:
            Validation result with issues list
        """
        logger.info(f"Validating training data: {data_s3_uri}")
        
        bucket, key = self._parse_s3_uri(data_s3_uri)
        
        try:
            # Download and validate data
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            data_content = response['Body'].read()
            
            # Parse based on format
            if expected_format == "jsonl":
                data = self._parse_jsonl(data_content)
            elif expected_format == "json":
                data = json.loads(data_content)
            else:
                raise ValueError(f"Unsupported format: {expected_format}")
            
            # Perform validations
            validation_result = {
                "valid": True,
                "issues": [],
                "data_count": len(data) if isinstance(data, list) else 1,
                "tier": tier
            }
            
            # Validate structure
            structure_issues = self._validate_structure(data, tier)
            validation_result["issues"].extend(structure_issues)
            
            # Validate required fields
            field_issues = self._validate_required_fields(data, tier)
            validation_result["issues"].extend(field_issues)
            
            # Validate data quality
            quality_issues = self._validate_data_quality(data, tier)
            validation_result["issues"].extend(quality_issues)
            
            # Determine if valid
            validation_result["valid"] = len(validation_result["issues"]) == 0
            
            logger.info(f"Validation complete: {'PASS' if validation_result['valid'] else 'FAIL'} ({len(validation_result['issues'])} issues)")
            
            return validation_result
            
        except ClientError as e:
            logger.error(f"Error accessing S3 data: {e}")
            return {
                "valid": False,
                "issues": [f"S3 access error: {str(e)}"],
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "error": str(e)
            }
    
    def _parse_jsonl(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse JSONL format data."""
        decoded = content.decode('utf-8').strip()
        if not decoded:
            return []
        lines = decoded.split('\n')
        data = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}")
        return data
    
    def _validate_structure(
        self,
        data: Any,
        tier: str
    ) -> List[str]:
        """Validate data structure."""
        issues = []
        
        if not isinstance(data, list):
            issues.append("Data must be a list of examples")
            return issues
        
        if len(data) == 0:
            issues.append("Data is empty")
        
        # Tier-specific minimum counts
        min_counts = {
            "gold": 100,
            "silver": 200,
            "bronze": 500
        }
        
        min_count = min_counts.get(tier, 100)
        if len(data) < min_count:
            issues.append(f"Data count ({len(data)}) below minimum for {tier} tier ({min_count})")
        
        return issues
    
    def _validate_required_fields(
        self,
        data: List[Dict[str, Any]],
        tier: str
    ) -> List[str]:
        """Validate required fields are present."""
        issues = []
        
        required_fields = ["prompt", "expected_output"]
        
        for idx, example in enumerate(data):
            for field in required_fields:
                if field not in example:
                    issues.append(f"Example {idx} missing required field: {field}")
        
        return issues
    
    def _validate_data_quality(
        self,
        data: List[Dict[str, Any]],
        tier: str
    ) -> List[str]:
        """Validate data quality."""
        issues = []
        
        for idx, example in enumerate(data):
            # Check for empty fields
            if "prompt" in example and not example["prompt"].strip():
                issues.append(f"Example {idx} has empty prompt")
            
            if "expected_output" in example and not example["expected_output"].strip():
                issues.append(f"Example {idx} has empty expected_output")
            
            # Check for reasonable length
            if "prompt" in example and len(example["prompt"]) > 10000:
                issues.append(f"Example {idx} prompt too long ({len(example['prompt'])} chars)")
        
        return issues
    
    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """Parse S3 URI into bucket and key."""
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        
        uri = s3_uri[5:]  # Remove "s3://"
        parts = uri.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        return bucket, key

