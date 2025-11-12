#!/usr/bin/env python3
"""
Database Configuration
Pydantic settings for PostgreSQL connection.

P0-5: Configuration management for database connection.
"""

from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional
import os


class DatabaseSettings(BaseSettings):
    """
    Database configuration with environment variable support.
    
    P0-5: Secure configuration management.
    """
    
    # PostgreSQL connection
    db_host: str = 'localhost'
    db_port: int = 5443
    db_name: str = 'body_broker_qa'
    db_user: str = 'postgres'
    db_password: Optional[str] = None
    
    # Connection pool settings
    db_pool_min_size: int = 2
    db_pool_max_size: int = 10
    db_command_timeout: int = 30
    
    # S3 configuration
    s3_bucket_reports: str = 'body-broker-qa-reports'
    s3_bucket_captures: str = 'body-broker-qa-captures'
    s3_region: str = 'us-east-1'
    
    # Rate limiting
    rate_limit_reports_per_minute: int = 10
    
    # Cache configuration
    cache_max_size: int = 1000
    cache_ttl_hours: int = 24
    
    # PDF generation
    pdf_max_workers: int = 2
    pdf_generation_timeout: int = 120  # seconds
    
    # Report limits
    max_report_size_mb: int = 100
    max_issues_per_report: int = 10000
    
    class Config:
        env_file = '.env'
        case_sensitive = False
    
    @validator('db_password', pre=True, always=True)
    def get_password_from_env(cls, v):
        """Get password from environment or use default."""
        if v is None:
            # Try to get from environment
            return os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD'))
        return v
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL."""
        password_part = f":{self.db_password}" if self.db_password else ""
        return f"postgresql://{self.db_user}{password_part}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def dict_safe(self) -> dict:
        """Get config dict without sensitive fields."""
        config = self.dict()
        if 'db_password' in config:
            config['db_password'] = '***' if config['db_password'] else None
        return config


# Global settings instance
settings = DatabaseSettings()

