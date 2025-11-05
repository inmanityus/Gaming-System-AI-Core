"""
OpenAI Fine-Tuner
================

Fine-tuning support for OpenAI ChatGPT models.
"""

import logging
import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class OpenAIFineTuner:
    """
    Fine-tunes OpenAI ChatGPT models.
    
    Supports:
    - OpenAI fine-tuning API
    - Model versioning
    - Cost tracking
    """
    
    def __init__(self, api_key_env: str = "OPENAI_API_KEY", org_id: Optional[str] = None):
        """
        Initialize OpenAI Fine-Tuner.
        
        Args:
            api_key_env: Environment variable name for API key
            org_id: OpenAI organization ID (optional)
        """
        self.api_key_env = api_key_env
        self.org_id = org_id
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required for OpenAIFineTuner")
        
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {api_key_env}")
        
        self.client = openai.OpenAI(api_key=api_key, organization=org_id)
        logger.info("OpenAIFineTuner initialized")
    
    def fine_tune(
        self,
        model_name: str,
        training_data: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune OpenAI model.
        
        Args:
            model_name: Base model name (e.g., "gpt-4o", "gpt-4o-mini")
            training_data: Training examples in OpenAI format
            config: Fine-tuning configuration
        
        Returns:
            Fine-tuning job information
        """
        logger.info(f"Fine-tuning OpenAI model: {model_name}")
        
        config = config or {}
        
        # Prepare training data in OpenAI format (JSONL)
        import tempfile
        
        # Convert training data to OpenAI format
        openai_format_data = []
        for item in training_data:
            if isinstance(item, dict):
                # Handle different input formats
                if 'messages' in item:
                    messages = item['messages']
                elif 'prompt' in item and 'completion' in item:
                    messages = [
                        {"role": "system", "content": item.get('system', '')},
                        {"role": "user", "content": item['prompt']},
                        {"role": "assistant", "content": item['completion']}
                    ]
                elif 'instruction' in item:
                    messages = [
                        {"role": "user", "content": item['instruction']},
                        {"role": "assistant", "content": item.get('output', '')}
                    ]
                else:
                    logger.warning(f"Skipping invalid training example: {item}")
                    continue
                
                openai_format_data.append({"messages": messages})
        
        if not openai_format_data:
            raise ValueError("No valid training data provided")
        
        # Write to temporary JSONL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for item in openai_format_data:
                f.write(json.dumps(item) + '\n')
            training_file_path = f.name
        
        try:
            # Upload training file
            logger.info("Uploading training file to OpenAI")
            with open(training_file_path, 'rb') as f:
                training_file = self.client.files.create(
                    file=f,
                    purpose='fine-tune'
                )
            
            logger.info(f"Training file uploaded: {training_file.id}")
            
            # Create fine-tuning job
            hyperparameters = config.get('hyperparameters', {})
            
            fine_tune_job = self.client.fine_tuning.jobs.create(
                training_file=training_file.id,
                model=model_name,
                hyperparameters=hyperparameters if hyperparameters else None,
                suffix=config.get('suffix', f"ft-{datetime.now().strftime('%Y%m%d')}")
            )
            
            logger.info(f"Fine-tuning job created: {fine_tune_job.id}")
            
            return {
                "status": "started",
                "model_name": model_name,
                "job_id": fine_tune_job.id,
                "training_file_id": training_file.id,
                "created_at": fine_tune_job.created_at
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(training_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")
    
    def get_fine_tuned_model(self, job_id: str) -> Dict[str, Any]:
        """Get fine-tuned model information."""
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
            
            result = {
                "job_id": job.id,
                "status": job.status,
                "model": job.model if hasattr(job, 'model') else None,
                "fine_tuned_model": job.fine_tuned_model if hasattr(job, 'fine_tuned_model') and job.fine_tuned_model else None,
                "created_at": job.created_at,
                "trained_tokens": job.trained_tokens if hasattr(job, 'trained_tokens') else None,
                "error": job.error if hasattr(job, 'error') and job.error else None
            }
            
            if job.status == 'succeeded' and job.fine_tuned_model:
                result["model_id"] = job.fine_tuned_model
                result["status"] = "completed"
            elif job.status == 'failed':
                result["status"] = "failed"
            else:
                result["status"] = job.status
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving fine-tuning job {job_id}: {e}")
            raise

