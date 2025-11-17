"""
Checkpoint Manager - Manages training checkpoints for failure recovery.
Handles checkpoint creation, storage, and retrieval.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages training checkpoints for failure recovery.
    
    Features:
    - Frequent checkpointing (every 30 minutes)
    - S3 storage for durability
    - Checkpoint metadata tracking
    - Checkpoint validation
    """
    
    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        checkpoint_frequency_minutes: int = 30
    ):
        """
        Initialize Checkpoint Manager.
        
        Args:
            s3_bucket: S3 bucket for checkpoints
            checkpoint_frequency_minutes: Frequency of checkpointing (minutes)
        """
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket or os.getenv('SRL_CHECKPOINT_S3_BUCKET', 'srl-checkpoints')
        self.checkpoint_frequency = checkpoint_frequency_minutes * 60  # Convert to seconds
        
        logger.info(
            f"CheckpointManager initialized "
            f"(bucket: {self.s3_bucket}, frequency: {checkpoint_frequency_minutes}min)"
        )
    
    async def create_checkpoint(
        self,
        training_job_name: str,
        tier: str,
        checkpoint_path: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Create and upload checkpoint to S3.
        
        Args:
            training_job_name: Training job name
            tier: Model tier
            checkpoint_path: Local path to checkpoint
            metadata: Checkpoint metadata
        
        Returns:
            S3 URI of uploaded checkpoint
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        s3_key = f"checkpoints/{tier}/{training_job_name}/{timestamp}/"
        
        # Upload checkpoint files
        checkpoint_dir = Path(checkpoint_path)
        if not checkpoint_dir.exists():
            raise ValueError(f"Checkpoint path does not exist: {checkpoint_path}")
        
        uploaded_files = []
        for file_path in checkpoint_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(checkpoint_dir)
                s3_file_key = f"{s3_key}{str(relative_path).replace(chr(92), '/')}"
                
                self.s3_client.upload_file(
                    str(file_path),
                    self.s3_bucket,
                    s3_file_key
                )
                uploaded_files.append(s3_file_key)
        
        # Upload metadata
        metadata["uploaded_files"] = uploaded_files
        metadata["timestamp"] = timestamp
        metadata["training_job_name"] = training_job_name
        metadata["tier"] = tier
        
        metadata_key = f"{s3_key}metadata.json"
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType="application/json"
        )
        
        s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
        logger.info(f"Checkpoint created: {s3_uri}")
        
        return s3_uri
    
    async def get_latest_checkpoint(
        self,
        training_job_name: str,
        tier: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest checkpoint for a training job.
        
        Args:
            training_job_name: Training job name
            tier: Model tier
        
        Returns:
            Checkpoint information or None
        """
        prefix = f"checkpoints/{tier}/{training_job_name}/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix,
                Delimiter="/"
            )
            
            if 'CommonPrefixes' not in response:
                return None
            
            # Get all checkpoint directories
            checkpoint_dirs = [cp['Prefix'] for cp in response['CommonPrefixes']]
            checkpoint_dirs.sort(reverse=True)  # Latest first
            
            if not checkpoint_dirs:
                return None
            
            # Get metadata from latest checkpoint
            latest_prefix = checkpoint_dirs[0]
            metadata_key = f"{latest_prefix}metadata.json"
            
            try:
                metadata_response = self.s3_client.get_object(
                    Bucket=self.s3_bucket,
                    Key=metadata_key
                )
                metadata = json.loads(metadata_response['Body'].read())
                metadata["s3_uri"] = f"s3://{self.s3_bucket}/{latest_prefix}"
                return metadata
            except ClientError:
                logger.warning(f"Metadata not found for checkpoint: {latest_prefix}")
                return {
                    "s3_uri": f"s3://{self.s3_bucket}/{latest_prefix}",
                    "training_job_name": training_job_name,
                    "tier": tier
                }
                
        except ClientError as e:
            logger.error(f"Error getting latest checkpoint: {e}")
            return None
    
    async def validate_checkpoint(
        self,
        checkpoint_s3_uri: str
    ) -> Dict[str, Any]:
        """
        Validate checkpoint integrity.
        
        Args:
            checkpoint_s3_uri: S3 URI of checkpoint
        
        Returns:
            Validation result
        """
        bucket, key = self._parse_s3_uri(checkpoint_s3_uri)
        
        try:
            # Check if metadata exists
            metadata_key = f"{key}metadata.json"
            try:
                metadata_response = self.s3_client.get_object(
                    Bucket=bucket,
                    Key=metadata_key
                )
                metadata = json.loads(metadata_response['Body'].read())
            except ClientError:
                return {
                    "valid": False,
                    "error": "Metadata not found"
                }
            
            # Check if all files exist
            missing_files = []
            for file_key in metadata.get("uploaded_files", []):
                try:
                    self.s3_client.head_object(Bucket=bucket, Key=file_key)
                except ClientError:
                    missing_files.append(file_key)
            
            if missing_files:
                return {
                    "valid": False,
                    "error": "Missing checkpoint files",
                    "missing_files": missing_files
                }
            
            return {
                "valid": True,
                "metadata": metadata,
                "file_count": len(metadata.get("uploaded_files", []))
            }
            
        except Exception as e:
            logger.error(f"Error validating checkpoint: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """Parse S3 URI into bucket and key."""
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        
        uri = s3_uri[5:]  # Remove "s3://"
        parts = uri.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        return bucket, key










