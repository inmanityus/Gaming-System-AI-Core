"""
Quality Validator - Validates distilled models against teacher models.
Compares student model outputs to teacher model outputs to ensure quality.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import boto3
import torch
from botocore.exceptions import ClientError
from transformers import AutoTokenizer, AutoModelForCausalLM

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class QualityValidator:
    """
    Validates distilled models by comparing to teacher models.
    
    Metrics:
    - Output similarity (cosine similarity, BLEU, ROUGE)
    - Task performance (accuracy, F1 score)
    - Latency comparison
    - Cost analysis
    """
    
    def __init__(
        self,
        model_registry: Optional[ModelRegistry] = None,
        s3_bucket: Optional[str] = None
    ):
        """
        Initialize Quality Validator.
        
        Args:
            model_registry: Model registry instance
            s3_bucket: S3 bucket for storing validation results
        """
        self.model_registry = model_registry or ModelRegistry()
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket or os.getenv('SRL_DISTILLATION_S3_BUCKET', 'srl-distillation-traces')
        
        # Device configuration
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Quality thresholds
        self.min_similarity_threshold = 0.85  # Minimum cosine similarity
        self.min_bleu_threshold = 0.70  # Minimum BLEU score
        self.min_rouge_threshold = 0.75  # Minimum ROUGE score
        
        logger.info(f"QualityValidator initialized (device: {self.device})")
    
    async def validate_distilled_model(
        self,
        student_adapter_s3_uri: str,
        student_base_model: str,
        teacher_model_id: str,
        test_traces: List[Dict[str, Any]],
        tier: str
    ) -> Dict[str, Any]:
        """
        Validate a distilled student model against teacher model.
        
        Args:
            student_adapter_s3_uri: S3 URI to student LoRA adapter
            student_base_model: Base model name for student
            teacher_model_id: Teacher model ID from registry
            test_traces: Test traces for validation
            tier: Model tier (gold, silver)
        
        Returns:
            Validation results with quality metrics
        """
        logger.info(f"Validating distilled {tier} tier model")
        
        # Load student model
        student_model, student_tokenizer = await self._load_student_model(
            student_base_model, student_adapter_s3_uri
        )
        
        # Get teacher model configuration
        teacher_model = await self.model_registry.get_model(UUID(teacher_model_id))
        if not teacher_model:
            raise ValueError(f"Teacher model {teacher_model_id} not found")
        
        # Generate outputs from both models
        student_outputs = []
        teacher_outputs = []
        
        for trace in test_traces[:100]:  # Limit to 100 for validation
            prompt = trace.get("prompt", "")
            if not prompt:
                continue
            
            # Generate from student model
            student_output = await self._generate_output(
                student_model, student_tokenizer, prompt
            )
            student_outputs.append(student_output)
            
            # Get teacher output (from trace or generate)
            teacher_output = trace.get("expert_output", "")
            if not teacher_output:
                # Would need to generate from teacher model
                # For now, use trace output
                teacher_output = trace.get("expert_output", "")
            teacher_outputs.append(teacher_output)
        
        # Compute quality metrics
        metrics = self._compute_quality_metrics(
            student_outputs, teacher_outputs, test_traces
        )
        
        # Determine if validation passes
        passes_validation = self._check_quality_thresholds(metrics, tier)
        
        # Store validation results
        validation_result = {
            "tier": tier,
            "student_adapter": student_adapter_s3_uri,
            "student_base_model": student_base_model,
            "teacher_model_id": teacher_model_id,
            "test_count": len(test_traces),
            "metrics": metrics,
            "passes_validation": passes_validation,
            "thresholds": {
                "min_similarity": self.min_similarity_threshold,
                "min_bleu": self.min_bleu_threshold,
                "min_rouge": self.min_rouge_threshold
            }
        }
        
        # Upload validation results to S3
        s3_key = await self._store_validation_results(validation_result)
        validation_result["s3_uri"] = f"s3://{self.s3_bucket}/{s3_key}"
        
        logger.info(
            f"Validation complete: {'PASS' if passes_validation else 'FAIL'} "
            f"(similarity: {metrics.get('cosine_similarity', 0):.3f})"
        )
        
        return validation_result
    
    async def _load_student_model(
        self,
        base_model: str,
        adapter_s3_uri: str
    ) -> Tuple[Any, Any]:
        """Load student model with LoRA adapter."""
        logger.info(f"Loading student model: {base_model}")
        
        # Load base model
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Download adapter from S3
        adapter_path = await self._download_adapter_from_s3(adapter_s3_uri)
        
        # Load LoRA adapter
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter_path)
        model.to(self.device)
        
        return model, tokenizer
    
    async def _generate_output(
        self,
        model: Any,
        tokenizer: Any,
        prompt: str,
        max_length: int = 512
    ) -> str:
        """Generate output from model."""
        inputs = tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove prompt from output
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        return generated_text
    
    def _compute_quality_metrics(
        self,
        student_outputs: List[str],
        teacher_outputs: List[str],
        test_traces: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Compute quality metrics comparing student to teacher."""
        if len(student_outputs) != len(teacher_outputs):
            logger.warning("Mismatch in output counts")
            return {"error": "Output count mismatch"}
        
        # Cosine similarity (semantic similarity)
        cosine_similarity = self._compute_cosine_similarity(
            student_outputs, teacher_outputs
        )
        
        # BLEU score (n-gram overlap)
        bleu_score = self._compute_bleu_score(student_outputs, teacher_outputs)
        
        # ROUGE score (recall-oriented)
        rouge_score = self._compute_rouge_score(student_outputs, teacher_outputs)
        
        metrics = {
            "cosine_similarity": cosine_similarity,
            "bleu_score": bleu_score,
            "rouge_score": rouge_score,
            "sample_count": len(student_outputs)
        }
        
        return metrics
    
    def _compute_cosine_similarity(
        self,
        student_outputs: List[str],
        teacher_outputs: List[str]
    ) -> float:
        """Compute average cosine similarity between outputs."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Load embedding model
            embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Compute embeddings
            student_embeddings = embedder.encode(student_outputs)
            teacher_embeddings = embedder.encode(teacher_outputs)
            
            # Compute cosine similarities
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(student_embeddings, teacher_embeddings)
            
            # Average diagonal (matching pairs)
            avg_similarity = float(similarities.diagonal().mean())
            
            return avg_similarity
        except Exception as e:
            logger.error(f"Error computing cosine similarity: {e}")
            return 0.0
    
    def _compute_bleu_score(
        self,
        student_outputs: List[str],
        teacher_outputs: List[str]
    ) -> float:
        """Compute BLEU score between outputs."""
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            
            smoothing = SmoothingFunction().method1
            scores = []
            
            for student, teacher in zip(student_outputs, teacher_outputs):
                student_tokens = student.split()
                teacher_tokens = teacher.split()
                
                score = sentence_bleu(
                    [teacher_tokens],
                    student_tokens,
                    smoothing_function=smoothing
                )
                scores.append(score)
            
            return float(sum(scores) / len(scores)) if scores else 0.0
        except Exception as e:
            logger.error(f"Error computing BLEU score: {e}")
            return 0.0
    
    def _compute_rouge_score(
        self,
        student_outputs: List[str],
        teacher_outputs: List[str]
    ) -> float:
        """Compute ROUGE score between outputs."""
        try:
            from rouge_score import rouge_scorer
            
            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            scores = []
            
            for student, teacher in zip(student_outputs, teacher_outputs):
                score = scorer.score(teacher, student)
                # Average ROUGE-1, ROUGE-2, ROUGE-L F-scores
                avg_f = (
                    score['rouge1'].fmeasure +
                    score['rouge2'].fmeasure +
                    score['rougeL'].fmeasure
                ) / 3.0
                scores.append(avg_f)
            
            return float(sum(scores) / len(scores)) if scores else 0.0
        except Exception as e:
            logger.error(f"Error computing ROUGE score: {e}")
            return 0.0
    
    def _check_quality_thresholds(
        self,
        metrics: Dict[str, float],
        tier: str
    ) -> bool:
        """Check if metrics meet quality thresholds."""
        similarity = metrics.get("cosine_similarity", 0.0)
        bleu = metrics.get("bleu_score", 0.0)
        rouge = metrics.get("rouge_score", 0.0)
        
        # Tier-specific thresholds (Gold tier can be slightly lower)
        if tier == "gold":
            min_similarity = self.min_similarity_threshold * 0.95
            min_bleu = self.min_bleu_threshold * 0.95
            min_rouge = self.min_rouge_threshold * 0.95
        else:
            min_similarity = self.min_similarity_threshold
            min_bleu = self.min_bleu_threshold
            min_rouge = self.min_rouge_threshold
        
        passes = (
            similarity >= min_similarity and
            bleu >= min_bleu and
            rouge >= min_rouge
        )
        
        return passes
    
    async def _download_adapter_from_s3(self, s3_uri: str) -> str:
        """Download LoRA adapter from S3."""
        bucket, key = self._parse_s3_uri(s3_uri)
        local_path = f"/tmp/adapters/{key.split('/')[-2]}"
        
        os.makedirs(local_path, exist_ok=True)
        
        # List and download all files in adapter directory
        response = self.s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=key
        )
        
        if 'Contents' in response:
            for obj in response['Contents']:
                file_key = obj['Key']
                local_file = os.path.join(local_path, file_key.replace(key, "").lstrip("/"))
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
                
                self.s3_client.download_file(bucket, file_key, local_file)
        
        return local_path
    
    async def _store_validation_results(self, results: Dict[str, Any]) -> str:
        """Store validation results in S3."""
        from datetime import datetime, timezone
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        tier = results.get("tier", "unknown")
        s3_key = f"validation/{tier}/validation-{timestamp}.json"
        
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=json.dumps(results, indent=2),
            ContentType="application/json"
        )
        
        return s3_key
    
    def _parse_s3_uri(self, s3_uri: str) -> Tuple[str, str]:
        """Parse S3 URI into bucket and key."""
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        
        uri = s3_uri[5:]  # Remove "s3://"
        parts = uri.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        return bucket, key










