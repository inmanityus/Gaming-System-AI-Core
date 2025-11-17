# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Lambda function for collecting Bronze tier traces for distillation.
"""

import json
import os
import logging
from typing import Dict, Any

import boto3

# Add parent directory to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.distillation.trace_collector import TraceCollector

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_bucket = os.getenv('SRL_DISTILLATION_S3_BUCKET', 'srl-distillation-traces')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for collecting Bronze tier traces.
    
    Args:
        event: Lambda event with tier and collection_window
        context: Lambda context
    
    Returns:
        Result with trace S3 URI
    """
    try:
        tier = event.get('tier', 'bronze')
        collection_window = event.get('collection_window', '24h')
        
        logger.info(f"Collecting {tier} tier traces (window: {collection_window})")
        
        # Initialize trace collector
        collector = TraceCollector(s3_bucket=s3_bucket)
        
        # Collect traces (async operation in Lambda)
        # In actual implementation, this would use async/await
        trace_s3_uri = collector.collect_traces(
            tier=tier,
            collection_window_hours=24 if collection_window == '24h' else 12
        )
        
        return {
            'statusCode': 200,
            'trace_s3_uri': trace_s3_uri,
            'tier': tier,
            'collection_window': collection_window
        }
        
    except Exception as e:
        logger.error(f"Error collecting traces: {e}")
        return {
            'statusCode': 500,
            'error': str(e)
        }










