#!/usr/bin/env python3
"""
Storage Service
Handles S3 storage operations for reports
"""

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class S3StorageService:
    """Handle S3 storage operations"""
    
    def __init__(
        self, 
        bucket_name: str, 
        region: str = 'us-east-1',
        connect_timeout: int = 5,
        read_timeout: int = 30,
        max_attempts: int = 3
    ):
        self.bucket_name = bucket_name
        self.region = region
        
        # CRITICAL FIX (P1-4): Configure timeouts and retries
        # Prevents hanging on S3 operations
        config = Config(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries={'max_attempts': max_attempts, 'mode': 'adaptive'},
            signature_version='s3v4'
        )
        
        self.s3_client = boto3.client('s3', region_name=region, config=config)
        logger.info(f"S3 Storage Service initialized: bucket={bucket_name}, region={region}")
        logger.info(f"Timeouts: connect={connect_timeout}s, read={read_timeout}s, retries={max_attempts}")
    
    async def upload(
        self,
        key: str,
        content: bytes,
        content_type: str
    ) -> str:
        """Upload content to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )
            
            url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Uploaded to S3: {url} ({len(content)} bytes)")
            return url
            
        except ClientError as e:
            logger.error(f"S3 upload failed for key '{key}': {e}")
            raise
    
    async def download(self, key: str) -> bytes:
        """Download content from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            content = response['Body'].read()
            logger.info(f"Downloaded from S3: {key} ({len(content)} bytes)")
            return content
            
        except ClientError as e:
            logger.error(f"S3 download failed for key '{key}': {e}")
            raise
    
    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 300,  # Default 5 minutes (was 3600)
        max_expiration: int = 3600  # Max 1 hour
    ) -> str:
        """
        Generate presigned URL for download with security validation.
        
        CRITICAL FIX (P0-2): Adds security validation to prevent vulnerabilities:
        1. Validates expiration is within limits (prevent long-lived URLs)
        2. Verifies object exists before generating URL (prevent enumeration attacks)
        3. Validates key format (prevent path traversal)
        4. Forces download with Content-Disposition header
        """
        try:
            # Validate expiration
            if expiration > max_expiration:
                raise ValueError(f"ExpiresIn cannot exceed {max_expiration} seconds")
            
            if expiration < 60:
                logger.warning(f"Very short expiration ({expiration}s), may cause download issues")
            
            # Validate key format (prevent path traversal)
            if '..' in key or key.startswith('/'):
                raise ValueError(f"Invalid key format: {key}")
            
            # Verify object exists (prevent enumeration attacks)
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise FileNotFoundError(f"Object not found: {key}")
                raise
            
            # Generate presigned URL with security headers
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ResponseContentDisposition': 'attachment'  # Force download
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated secure presigned URL for key '{key}' (expires in {expiration}s)")
            return url
            
        except ClientError as e:
            logger.error(f"Presigned URL generation failed for key '{key}': {e}")
            raise
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Presigned URL validation failed for key '{key}': {e}")
            raise
    
    def check_object_exists(self, key: str) -> bool:
        """Check if object exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    async def delete(self, key: str) -> None:
        """Delete object from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"Deleted from S3: {key}")
            
        except ClientError as e:
            logger.error(f"S3 delete failed for key '{key}': {e}")
            raise


class FileSystemStorageService:
    """Handle filesystem storage operations"""
    
    def __init__(self, base_path: str = './storage/reports'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Filesystem Storage Service initialized: base_path={self.base_path}")
    
    async def upload(
        self,
        key: str,
        content: bytes,
        content_type: str
    ) -> str:
        """Save content to filesystem"""
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            if isinstance(content, bytes):
                f.write(content)
            else:
                f.write(content.encode('utf-8'))
        
        logger.info(f"Saved to filesystem: {file_path} ({len(content)} bytes)")
        return str(file_path)
    
    async def download(self, key: str) -> bytes:
        """Read content from filesystem"""
        file_path = self.base_path / key
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        logger.info(f"Read from filesystem: {file_path} ({len(content)} bytes)")
        return content
    
    def check_file_exists(self, key: str) -> bool:
        """Check if file exists"""
        file_path = self.base_path / key
        return file_path.exists()
    
    async def delete(self, key: str) -> None:
        """Delete file from filesystem"""
        file_path = self.base_path / key
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted from filesystem: {file_path}")

