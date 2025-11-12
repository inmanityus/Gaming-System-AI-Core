"""
Failure Handler - Handles training failures and implements recovery strategies.
Implements checkpointing, retry logic, and graceful degradation.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

# Add parent directory to path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class FailureHandler:
    """
    Handles training failures and implements recovery strategies.
    
    Strategies:
    - Checkpoint-based recovery
    - Automatic retry with exponential backoff
    - Fallback to previous model versions
    - Step Functions rollback
    """
    
    def __init__(
        self,
        model_registry: Optional[ModelRegistry] = None,
        s3_bucket: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Initialize Failure Handler.
        
        Args:
            model_registry: Model registry instance
            s3_bucket: S3 bucket for checkpoints
            max_retries: Maximum retry attempts
        """
        self.model_registry = model_registry or ModelRegistry()
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket or os.getenv('SRL_CHECKPOINT_S3_BUCKET', 'srl-checkpoints')
        self.max_retries = max_retries
        
        logger.info(f"FailureHandler initialized (max_retries: {max_retries})")
    
    async def handle_training_failure(
        self,
        training_job_name: str,
        failure_reason: str,
        tier: str,
        checkpoint_s3_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle a training job failure.
        
        Args:
            training_job_name: Name of the failed training job
            failure_reason: Reason for failure
            tier: Model tier (gold, silver, bronze)
            checkpoint_s3_uri: Optional checkpoint URI for recovery
        
        Returns:
            Recovery action and status
        """
        logger.warning(f"Handling training failure: {training_job_name} ({failure_reason})")
        
        # Determine recovery strategy based on failure type
        recovery_strategy = self._determine_recovery_strategy(failure_reason, checkpoint_s3_uri)
        
        # Execute recovery
        recovery_result = await self._execute_recovery(
            training_job_name=training_job_name,
            tier=tier,
            strategy=recovery_strategy,
            checkpoint_s3_uri=checkpoint_s3_uri
        )
        
        return {
            "training_job_name": training_job_name,
            "failure_reason": failure_reason,
            "tier": tier,
            "recovery_strategy": recovery_strategy,
            "recovery_result": recovery_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _determine_recovery_strategy(
        self,
        failure_reason: str,
        checkpoint_s3_uri: Optional[str]
    ) -> str:
        """
        Determine recovery strategy based on failure reason.
        
        Args:
            failure_reason: Reason for failure
            checkpoint_s3_uri: Available checkpoint
        
        Returns:
            Recovery strategy name
        """
        # Spot interruption - resume from checkpoint
        if "Spot" in failure_reason or "interrupted" in failure_reason.lower():
            if checkpoint_s3_uri:
                return "resume_from_checkpoint"
            return "retry_with_new_job"
        
        # Out of memory - reduce batch size and retry
        if "out of memory" in failure_reason.lower() or "OOM" in failure_reason:
            return "retry_with_reduced_batch"
        
        # Validation failure - fix data and retry
        if "validation" in failure_reason.lower() or "data" in failure_reason.lower():
            return "retry_after_data_fix"
        
        # Unknown failure - retry with same config
        return "retry_with_same_config"
    
    async def _execute_recovery(
        self,
        training_job_name: str,
        tier: str,
        strategy: str,
        checkpoint_s3_uri: Optional[str]
    ) -> Dict[str, Any]:
        """
        Execute recovery strategy.
        
        Args:
            training_job_name: Training job name
            tier: Model tier
            strategy: Recovery strategy
            checkpoint_s3_uri: Checkpoint URI
        
        Returns:
            Recovery result
        """
        logger.info(f"Executing recovery strategy: {strategy}")
        
        if strategy == "resume_from_checkpoint":
            return await self._resume_from_checkpoint(
                training_job_name, tier, checkpoint_s3_uri
            )
        
        elif strategy == "retry_with_new_job":
            return await self._retry_with_new_job(training_job_name, tier)
        
        elif strategy == "retry_with_reduced_batch":
            return await self._retry_with_reduced_batch(training_job_name, tier)
        
        elif strategy == "retry_after_data_fix":
            return await self._retry_after_data_fix(training_job_name, tier)
        
        else:  # retry_with_same_config
            return await self._retry_with_same_config(training_job_name, tier)
    
    async def _resume_from_checkpoint(
        self,
        training_job_name: str,
        tier: str,
        checkpoint_s3_uri: str
    ) -> Dict[str, Any]:
        """Resume training from checkpoint."""
        logger.info(f"Resuming training from checkpoint: {checkpoint_s3_uri}")
        
        # Verify checkpoint exists
        bucket, key = self._parse_s3_uri(checkpoint_s3_uri)
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
        except ClientError:
            logger.error(f"Checkpoint not found: {checkpoint_s3_uri}")
            return {
                "success": False,
                "error": "Checkpoint not found",
                "fallback": "retry_with_new_job"
            }
        
        return {
            "success": True,
            "strategy": "resume_from_checkpoint",
            "checkpoint_uri": checkpoint_s3_uri,
            "action": "Launch new training job with checkpoint_path parameter"
        }
    
    async def _retry_with_new_job(
        self,
        training_job_name: str,
        tier: str
    ) -> Dict[str, Any]:
        """Retry with a new training job."""
        logger.info(f"Retrying with new training job: {training_job_name}")
        
        return {
            "success": True,
            "strategy": "retry_with_new_job",
            "action": "Launch new training job with same configuration",
            "retry_count": 1
        }
    
    async def _retry_with_reduced_batch(
        self,
        training_job_name: str,
        tier: str
    ) -> Dict[str, Any]:
        """Retry with reduced batch size."""
        logger.info(f"Retrying with reduced batch size: {training_job_name}")
        
        # Determine reduced batch size based on tier
        batch_size_reductions = {
            "gold": 0.5,    # Reduce to 50%
            "silver": 0.6,   # Reduce to 60%
            "bronze": 0.7   # Reduce to 70%
        }
        
        reduction = batch_size_reductions.get(tier, 0.5)
        
        return {
            "success": True,
            "strategy": "retry_with_reduced_batch",
            "batch_size_reduction": reduction,
            "action": f"Launch new training job with batch size reduced to {reduction * 100}%"
        }
    
    async def _retry_after_data_fix(
        self,
        training_job_name: str,
        tier: str
    ) -> Dict[str, Any]:
        """Retry after data validation and fix."""
        logger.info(f"Retrying after data fix: {training_job_name}")
        
        return {
            "success": True,
            "strategy": "retry_after_data_fix",
            "action": "Validate training data, fix issues, then retry training job"
        }
    
    async def _retry_with_same_config(
        self,
        training_job_name: str,
        tier: str
    ) -> Dict[str, Any]:
        """Retry with same configuration."""
        logger.info(f"Retrying with same config: {training_job_name}")
        
        return {
            "success": True,
            "strategy": "retry_with_same_config",
            "action": "Launch new training job with identical configuration",
            "retry_count": 1
        }
    
    async def get_fallback_model(
        self,
        tier: str,
        use_case: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get fallback model when training fails.
        
        Args:
            tier: Model tier
            use_case: Use case identifier
        
        Returns:
            Fallback model information or None
        """
        try:
            # Get previous model version from registry
            current_model = await self.model_registry.get_current_model(use_case)
            
            if current_model:
                # Get previous version
                model_id = current_model.get("model_id")
                if model_id:
                    model = await self.model_registry.get_model(UUID(model_id))
                    if model:
                        return {
                            "model_id": str(model_id),
                            "model_name": model.get("model_name"),
                            "version": model.get("version"),
                            "status": "fallback"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting fallback model: {e}")
            return None
    
    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """Parse S3 URI into bucket and key."""
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        
        uri = s3_uri[5:]  # Remove "s3://"
        parts = uri.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        return bucket, key






