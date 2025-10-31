"""
Historical Log Processor - Processes model historical logs into training data.
Converts logs into training examples for fine-tuning.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, PostgreSQLPool


class HistoricalLogProcessor:
    """
    Processes historical logs into training data format.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def get_historical_logs(
        self,
        model_id: UUID = None,
        use_case: str = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical logs from database.
        
        Args:
            model_id: Filter by model ID
            use_case: Filter by use case
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
            limit: Maximum number of logs to retrieve
        
        Returns:
            List of historical log entries
        """
        postgres = await self._get_postgres()
        
        query = "SELECT * FROM model_historical_logs WHERE 1=1"
        params = []
        param_index = 1
        
        if model_id:
            query += f" AND model_id = ${param_index}"
            params.append(model_id)
            param_index += 1
        
        if use_case:
            query += f" AND use_case = ${param_index}"
            params.append(use_case)
            param_index += 1
        
        if start_time:
            query += f" AND timestamp >= ${param_index}::timestamp"
            params.append(start_time)
            param_index += 1
        
        if end_time:
            query += f" AND timestamp <= ${param_index}::timestamp"
            params.append(end_time)
            param_index += 1
        
        query += f" ORDER BY timestamp DESC LIMIT ${param_index}"
        params.append(limit)
        
        rows = await postgres.fetch_all(query, *params)
        
        logs = []
        for row in rows:
            logs.append({
                "log_id": str(row["log_id"]),
                "model_id": str(row["model_id"]),
                "use_case": row["use_case"],
                "prompt": row["prompt"],
                "context": json.loads(row["context"]) if isinstance(row["context"], str) else row["context"],
                "generated_output": row["generated_output"],
                "user_feedback": json.loads(row["user_feedback"]) if isinstance(row["user_feedback"], str) else row["user_feedback"],
                "corrected_output": row["corrected_output"],
                "performance_metrics": json.loads(row["performance_metrics"]) if isinstance(row["performance_metrics"], str) else row["performance_metrics"],
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None
            })
        
        return logs
    
    async def process_logs_to_training_data(
        self,
        logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process historical logs into training examples.
        
        Converts logs into format suitable for fine-tuning:
        - Input: prompt + context
        - Output: generated_output (or corrected_output if feedback available)
        
        Args:
            logs: List of historical log entries
        
        Returns:
            List of training examples
        """
        training_examples = []
        
        for log in logs:
            # Build input from prompt and context
            context_str = self._format_context(log.get("context", {}))
            input_text = f"{log['prompt']}\n{context_str}".strip()
            
            # Use corrected_output if feedback provided, otherwise generated_output
            if log.get("corrected_output"):
                output_text = log["corrected_output"]
                quality_score = 1.0  # Corrected outputs are high quality
            else:
                output_text = log["generated_output"]
                # Quality score based on performance metrics
                quality_score = self._calculate_quality_score(log.get("performance_metrics", {}))
            
            example = {
                "input": input_text,
                "output": output_text,
                "quality_score": quality_score,
                "metadata": {
                    "log_id": log["log_id"],
                    "use_case": log["use_case"],
                    "timestamp": log["timestamp"],
                    "performance_metrics": log.get("performance_metrics", {})
                }
            }
            
            training_examples.append(example)
        
        return training_examples
    
    async def filter_high_quality_examples(
        self,
        examples: List[Dict[str, Any]],
        min_quality_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Filter examples by quality score.
        
        Args:
            examples: List of training examples
            min_quality_score: Minimum quality score threshold
        
        Returns:
            Filtered list of high-quality examples
        """
        filtered = [
            ex for ex in examples
            if ex.get("quality_score", 0.0) >= min_quality_score
        ]
        
        return filtered
    
    async def combine_with_initial_data(
        self,
        historical_examples: List[Dict[str, Any]],
        initial_examples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Combine historical log examples with initial training data.
        
        Args:
            historical_examples: Examples from historical logs
            initial_examples: Initial training data examples
        
        Returns:
            Combined list of training examples
        """
        # Combine both sources
        combined = initial_examples + historical_examples
        
        # Remove duplicates (based on input text)
        seen_inputs = set()
        unique_examples = []
        
        for example in combined:
            input_hash = hash(example["input"])
            if input_hash not in seen_inputs:
                seen_inputs.add(input_hash)
                unique_examples.append(example)
        
        return unique_examples
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into text string."""
        if not context:
            return ""
        
        context_parts = []
        
        for key, value in context.items():
            if isinstance(value, dict):
                value = json.dumps(value, indent=2)
            context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts)
    
    def _calculate_quality_score(self, performance_metrics: Dict[str, Any]) -> float:
        """Calculate quality score from performance metrics."""
        if not performance_metrics:
            return 0.5  # Default
        
        # Combine various metrics
        accuracy = performance_metrics.get("accuracy", 0.5)
        coherence = performance_metrics.get("coherence", 0.5)
        relevance = performance_metrics.get("relevance", 0.5)
        user_rating = performance_metrics.get("user_rating", 0.5)
        
        # Weighted average
        score = (accuracy * 0.3 + coherence * 0.3 + relevance * 0.2 + user_rating * 0.2)
        
        return score


