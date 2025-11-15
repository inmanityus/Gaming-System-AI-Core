# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Trace Collector - Collects Bronze tier model outputs for distillation.
Stores expert traces from Bronze tier models to distill to Silver and Gold tiers.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class TraceCollector:
    """
    Collects Bronze tier model outputs (traces) for knowledge distillation.
    
    Strategy:
    - Collects outputs from Bronze tier models (671B MoE)
    - Stores in S3 for nightly distillation pipeline
    - Distillation reduces dependency on expensive Bronze tier
    """
    
    def __init__(
        self,
        model_registry: Optional[ModelRegistry] = None,
        historical_log_processor: Optional[HistoricalLogProcessor] = None,
        s3_bucket: Optional[str] = None
    ):
        """
        Initialize Trace Collector.
        
        Args:
            model_registry: Model registry instance
            historical_log_processor: Historical log processor
            s3_bucket: S3 bucket for storing traces
        """
        self.model_registry = model_registry or ModelRegistry()
        self.historical_log_processor = historical_log_processor or HistoricalLogProcessor()
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket or os.getenv('SRL_DISTILLATION_S3_BUCKET', 'srl-distillation-traces')
        
        # Bronze tier use cases
        self.bronze_use_cases = [
            "srl_bronze_tier",
            "coordination_layer",
            "coordination"
        ]
        
        logger.info(f"TraceCollector initialized (S3 bucket: {self.s3_bucket})")
    
    async def collect_bronze_traces(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_traces: int = 10000
    ) -> Dict[str, Any]:
        """
        Collect Bronze tier model traces from historical logs.
        
        Args:
            start_time: Start time for trace collection (default: 24 hours ago)
            end_time: End time for trace collection (default: now)
            max_traces: Maximum number of traces to collect
        
        Returns:
            Collection summary with trace count and S3 location
        """
        logger.info("Collecting Bronze tier traces for distillation")
        
        # Default to last 24 hours
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        if start_time is None:
            start_time = end_time - timedelta(hours=24)
        
        # Collect traces from all Bronze tier use cases
        all_traces = []
        
        for use_case in self.bronze_use_cases:
            try:
                # Get Bronze tier models for this use case
                bronze_model = await self.model_registry.get_current_model(use_case)
                
                if not bronze_model:
                    logger.debug(f"No Bronze tier model found for use case: {use_case}")
                    continue
                
                model_id = bronze_model.get("model_id")
                if not model_id:
                    continue
                
                # Get historical logs for this model
                logs = await self.historical_log_processor.get_historical_logs(
                    model_id=UUID(model_id) if isinstance(model_id, str) else model_id,
                    use_case=use_case,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                    limit=max_traces // len(self.bronze_use_cases)
                )
                
                # Convert logs to traces
                for log in logs:
                    trace = self._log_to_trace(log)
                    if trace:
                        all_traces.append(trace)
                
                logger.info(f"Collected {len(logs)} traces from {use_case}")
                
            except Exception as e:
                logger.error(f"Error collecting traces from {use_case}: {e}")
                continue
        
        # Limit total traces
        if len(all_traces) > max_traces:
            all_traces = all_traces[:max_traces]
        
        # Store traces in S3
        s3_key = await self._store_traces_in_s3(all_traces, start_time, end_time)
        
        summary = {
            "trace_count": len(all_traces),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "s3_bucket": self.s3_bucket,
            "s3_key": s3_key,
            "s3_uri": f"s3://{self.s3_bucket}/{s3_key}"
        }
        
        logger.info(f"Collected {len(all_traces)} Bronze tier traces, stored in {summary['s3_uri']}")
        
        return summary
    
    def _log_to_trace(self, log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert historical log entry to distillation trace.
        
        Args:
            log: Historical log entry
        
        Returns:
            Trace dictionary or None if invalid
        """
        try:
            # Extract trace data
            trace = {
                "prompt": log.get("prompt", ""),
                "context": log.get("context", {}),
                "expert_output": log.get("generated_output", ""),
                "corrected_output": log.get("corrected_output"),
                "user_feedback": log.get("user_feedback", {}),
                "performance_metrics": log.get("performance_metrics", {}),
                "timestamp": log.get("timestamp"),
                "model_id": log.get("model_id"),
                "use_case": log.get("use_case")
            }
            
            # Validate trace has required fields
            if not trace["prompt"] or not trace["expert_output"]:
                return None
            
            return trace
            
        except Exception as e:
            logger.error(f"Error converting log to trace: {e}")
            return None
    
    async def _store_traces_in_s3(
        self,
        traces: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """
        Store traces in S3 for distillation pipeline.
        
        Args:
            traces: List of trace dictionaries
            start_time: Start time for this collection
            end_time: End time for this collection
        
        Returns:
            S3 key where traces were stored
        """
        # Generate S3 key with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        s3_key = f"traces/{timestamp}/bronze-traces.json"
        
        # Prepare data for S3
        data = {
            "collection_metadata": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "trace_count": len(traces),
                "collected_at": datetime.now(timezone.utc).isoformat()
            },
            "traces": traces
        }
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json.dumps(data, indent=2),
                ContentType="application/json"
            )
            logger.info(f"Stored {len(traces)} traces in S3: s3://{self.s3_bucket}/{s3_key}")
        except ClientError as e:
            logger.error(f"Error storing traces in S3: {e}")
            raise
        
        return s3_key
    
    async def get_trace_stats(self) -> Dict[str, Any]:
        """
        Get statistics about collected traces.
        
        Returns:
            Statistics dictionary
        """
        try:
            # List objects in S3 traces prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix="traces/"
            )
            
            total_traces = 0
            collection_count = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('bronze-traces.json'):
                        collection_count += 1
                        # Download and count traces in this file
                        try:
                            obj_response = self.s3_client.get_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            data = json.loads(obj_response['Body'].read())
                            total_traces += data.get('collection_metadata', {}).get('trace_count', 0)
                        except Exception as e:
                            logger.warning(f"Error reading trace file {obj['Key']}: {e}")
            
            return {
                "total_traces": total_traces,
                "collection_count": collection_count,
                "s3_bucket": self.s3_bucket
            }
            
        except ClientError as e:
            logger.error(f"Error getting trace stats: {e}")
            return {
                "total_traces": 0,
                "collection_count": 0,
                "s3_bucket": self.s3_bucket,
                "error": str(e)
            }









