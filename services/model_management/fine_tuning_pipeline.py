"""
Fine-Tuning Pipeline - Fine-tunes models using historical logs + initial training data.
Supports LoRA and full fine-tuning. Creates use-case specific models.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, PostgreSQLPool
from services.model_management.historical_log_processor import HistoricalLogProcessor


class FineTuningPipeline:
    """
    Fine-tunes models using historical logs and initial training data.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.log_processor = HistoricalLogProcessor()
        self.training_output_dir = "models/fine_tuned"
        os.makedirs(self.training_output_dir, exist_ok=True)
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def fine_tune_model(
        self,
        base_model_id: UUID,
        use_case: str,
        historical_logs_range: Dict[str, str] = None,
        initial_training_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune a model using historical logs + initial training data.
        
        Args:
            base_model_id: Base model to fine-tune
            use_case: Use case identifier
            historical_logs_range: {"start": "...", "end": "..."}
            initial_training_data: Initial training examples
        
        Returns:
            Fine-tuned model information
        """
        # 1. Get historical logs
        historical_logs = await self.log_processor.get_historical_logs(
            model_id=base_model_id,
            use_case=use_case,
            start_time=historical_logs_range.get("start") if historical_logs_range else None,
            end_time=historical_logs_range.get("end") if historical_logs_range else None,
            limit=10000
        )
        
        # 2. Process logs into training data
        processed_logs = await self.log_processor.process_logs_to_training_data(historical_logs)
        
        # 3. Filter high-quality examples
        quality_filtered = await self.log_processor.filter_high_quality_examples(
            processed_logs,
            min_quality_score=0.7
        )
        
        # 4. Combine with initial training data
        if initial_training_data is None:
            initial_training_data = []
        
        training_data = await self.log_processor.combine_with_initial_data(
            quality_filtered,
            initial_training_data
        )
        
        # 5. Prepare training dataset
        train_dataset, val_dataset = await self._prepare_datasets(training_data)
        
        # 6. Fine-tune model (prefer LoRA if supported)
        base_model = await self._get_model_info(base_model_id)
        
        if base_model.get("supports_lora", True):
            fine_tuned_model = await self._fine_tune_lora(
                base_model=base_model,
                train_dataset=train_dataset,
                val_dataset=val_dataset,
                use_case=use_case
            )
        else:
            fine_tuned_model = await self._fine_tune_full(
                base_model=base_model,
                train_dataset=train_dataset,
                val_dataset=val_dataset,
                use_case=use_case
            )
        
        # 7. Validate fine-tuned model
        validation_results = await self._validate_fine_tuned_model(
            fine_tuned_model,
            val_dataset
        )
        
        if not validation_results.get("passed", False):
            # Re-train with adjustments
            return await self._retrain_with_adjustments(
                base_model,
                training_data,
                validation_results,
                use_case
            )
        
        return fine_tuned_model
    
    async def _get_model_info(self, model_id: UUID) -> Dict[str, Any]:
        """Get model information from registry."""
        from services.model_management.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        model = await registry.get_model(model_id)
        
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        return model
    
    async def _prepare_datasets(
        self,
        training_data: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Prepare training and validation datasets.
        
        Split: 80% training, 20% validation
        """
        # Shuffle data
        import random
        shuffled = training_data.copy()
        random.shuffle(shuffled)
        
        # Split
        split_index = int(len(shuffled) * 0.8)
        train_dataset = shuffled[:split_index]
        val_dataset = shuffled[split_index:]
        
        return train_dataset, val_dataset
    
    async def _fine_tune_lora(
        self,
        base_model: Dict[str, Any],
        train_dataset: List[Dict[str, Any]],
        val_dataset: List[Dict[str, Any]],
        use_case: str
    ) -> Dict[str, Any]:
        """
        Fine-tune using LoRA (Low-Rank Adaptation).
        
        More efficient than full fine-tuning.
        """
        # This would call actual LoRA training code
        # For now, create placeholder structure
        
        model_name = base_model["model_name"]
        version = base_model["version"]
        
        fine_tuned_model = {
            "model_id": None,  # Will be assigned after training
            "base_model_id": base_model["model_id"],
            "model_name": f"{model_name}-{use_case}",
            "model_type": "self_hosted",
            "provider": base_model["provider"],
            "use_case": use_case,
            "version": f"{version}-{use_case}-lora",
            "fine_tuning_method": "lora",
            "training_samples": len(train_dataset),
            "validation_samples": len(val_dataset),
            "model_path": None,  # Will be set after training
            "status": "training",
            "training_config": {
                "lora_rank": 64,
                "lora_alpha": 32,
                "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
                "learning_rate": 2e-4,
                "batch_size": 4,
                "num_epochs": 3
            }
        }
        
        # TODO: Call actual LoRA training code
        # For now, mark as placeholder
        print(f"[PLACEHOLDER] LoRA fine-tuning for {fine_tuned_model['model_name']}")
        print(f"  Training samples: {len(train_dataset)}")
        print(f"  Validation samples: {len(val_dataset)}")
        
        return fine_tuned_model
    
    async def _fine_tune_full(
        self,
        base_model: Dict[str, Any],
        train_dataset: List[Dict[str, Any]],
        val_dataset: List[Dict[str, Any]],
        use_case: str
    ) -> Dict[str, Any]:
        """
        Full fine-tuning (not LoRA).
        
        More resource-intensive but can achieve better results.
        """
        model_name = base_model["model_name"]
        version = base_model["version"]
        
        fine_tuned_model = {
            "model_id": None,
            "base_model_id": base_model["model_id"],
            "model_name": f"{model_name}-{use_case}",
            "model_type": "self_hosted",
            "provider": base_model["provider"],
            "use_case": use_case,
            "version": f"{version}-{use_case}-full",
            "fine_tuning_method": "full",
            "training_samples": len(train_dataset),
            "validation_samples": len(val_dataset),
            "model_path": None,
            "status": "training",
            "training_config": {
                "learning_rate": 1e-5,
                "batch_size": 2,
                "num_epochs": 3,
                "gradient_accumulation_steps": 4
            }
        }
        
        # TODO: Call actual full fine-tuning code
        print(f"[PLACEHOLDER] Full fine-tuning for {fine_tuned_model['model_name']}")
        
        return fine_tuned_model
    
    async def _validate_fine_tuned_model(
        self,
        fine_tuned_model: Dict[str, Any],
        val_dataset: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate fine-tuned model.
        
        Returns validation results.
        """
        # TODO: Implement actual validation
        # For now, return placeholder results
        
        return {
            "passed": True,  # Placeholder - would actually validate
            "validation_samples": len(val_dataset),
            "metrics": {
                "loss": 0.5,  # Placeholder
                "accuracy": 0.85  # Placeholder
            }
        }
    
    async def _retrain_with_adjustments(
        self,
        base_model: Dict[str, Any],
        training_data: List[Dict[str, Any]],
        validation_results: Dict[str, Any],
        use_case: str
    ) -> Dict[str, Any]:
        """
        Re-train model with adjustments based on validation feedback.
        """
        # Adjust training parameters based on validation results
        # Re-train and validate again
        
        # TODO: Implement retraining logic
        print(f"[PLACEHOLDER] Retraining with adjustments for {use_case}")
        
        return await self.fine_tune_model(
            base_model_id=UUID(base_model["model_id"]),
            use_case=use_case,
            initial_training_data=training_data
        )


