"""
Model Management API Routes - FastAPI routes for model management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import UUID

from services.model_management.model_registry import ModelRegistry
from services.model_management.paid_model_manager import PaidModelManager
from services.model_management.self_hosted_scanner import SelfHostedScanner
from services.model_management.fine_tuning_pipeline import FineTuningPipeline

router = APIRouter(prefix="/api/v1/model-management", tags=["model-management"])

# Initialize components
registry = ModelRegistry()
paid_manager = PaidModelManager()
self_hosted_scanner = SelfHostedScanner()
fine_tuning_pipeline = FineTuningPipeline()


class ModelRegisterRequest(BaseModel):
    model_name: str
    model_type: str  # "paid" or "self_hosted"
    provider: str
    use_case: str
    version: str
    model_path: Optional[str] = None
    configuration: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    resource_requirements: Dict[str, Any] = {}


class FineTuneRequest(BaseModel):
    base_model_id: str
    use_case: str
    historical_logs_range: Optional[Dict[str, str]] = None
    initial_training_data: Optional[List[Dict[str, Any]]] = None


@router.post("/register")
async def register_model(request: ModelRegisterRequest):
    """Register a new model in the registry."""
    try:
        model_id = await registry.register_model(
            model_name=request.model_name,
            model_type=request.model_type,
            provider=request.provider,
            use_case=request.use_case,
            version=request.version,
            model_path=request.model_path,
            configuration=request.configuration,
            performance_metrics=request.performance_metrics,
            resource_requirements=request.resource_requirements
        )
        
        return {
            "model_id": str(model_id),
            "status": "registered"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover")
async def discover_models(use_case: str):
    """Discover available models for a use case."""
    try:
        # Scan paid models
        paid_models = await paid_manager.scanner.scan_available_models(use_case)
        
        # Scan self-hosted models
        self_hosted_models = await self_hosted_scanner.scan_and_rank_models(use_case)
        
        return {
            "paid_models": paid_models,
            "self_hosted_models": self_hosted_models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current/{use_case}")
async def get_current_model(use_case: str):
    """Get current model for a use case."""
    try:
        model = await registry.get_current_model(use_case)
        
        if not model:
            raise HTTPException(status_code=404, detail="No current model found")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-better-paid")
async def check_better_paid_model(use_case: str, current_model_id: str):
    """Check for better paid model."""
    try:
        better_model = await paid_manager.check_for_better_models(
            use_case=use_case,
            current_model_id=current_model_id
        )
        
        return {
            "better_model_found": better_model is not None,
            "better_model_id": better_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch-paid-model")
async def switch_paid_model(
    use_case: str,
    new_model_id: str,
    current_model_id: str
):
    """Switch to a new paid model."""
    try:
        success = await paid_manager.auto_switch_model(
            use_case=use_case,
            new_model_id=new_model_id,
            current_model_id=current_model_id
        )
        
        return {
            "success": success,
            "new_model_id": new_model_id if success else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fine-tune")
async def fine_tune_model(request: FineTuneRequest):
    """Fine-tune a model using historical logs."""
    try:
        result = await fine_tuning_pipeline.fine_tune_model(
            base_model_id=UUID(request.base_model_id),
            use_case=request.use_case,
            historical_logs_range=request.historical_logs_range,
            initial_training_data=request.initial_training_data
        )
        
        return {
            "status": "training",
            "fine_tuned_model": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get model information."""
    try:
        model = await registry.get_model(UUID(model_id))
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







