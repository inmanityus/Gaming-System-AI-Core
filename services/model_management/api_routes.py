"""
Model Management API Routes - FastAPI routes for model management.
"""

import os
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, validator
from typing import Any, Dict, List, Optional
from uuid import UUID

from services.model_management.model_registry import ModelRegistry
from services.model_management.paid_model_manager import PaidModelManager
from services.model_management.self_hosted_scanner import SelfHostedScanner
from services.model_management.fine_tuning_pipeline import FineTuningPipeline

router = APIRouter(prefix="/api/v1/model-management", tags=["model-management"])

# SECURITY: Admin API Keys for model management operations
MODEL_ADMIN_KEYS = set(os.getenv('MODEL_ADMIN_KEYS', '').split(',')) if os.getenv('MODEL_ADMIN_KEYS') else set()

async def verify_model_admin(x_api_key: str = Header(None)):
    """
    SECURITY: Verify admin API key for model management operations.
    
    Required for: model registration, model switching, fine-tuning.
    These operations can cause security breaches and cost attacks.
    """
    if not MODEL_ADMIN_KEYS:
        raise HTTPException(
            status_code=503,
            detail="Model management disabled: MODEL_ADMIN_KEYS not configured"
        )
    if not x_api_key or x_api_key not in MODEL_ADMIN_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized: Model admin access required")
    return True

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
    
    @validator('model_path')
    def validate_model_path(cls, v):
        """SECURITY: Validate model_path to prevent path traversal."""
        if v is None:
            return v
        if '..' in v or v.startswith('/') or v.startswith('\\'):
            raise ValueError("Invalid model_path: path traversal detected")
        if len(v) > 500:
            raise ValueError("model_path too long (max 500 characters)")
        return v


class FineTuneRequest(BaseModel):
    base_model_id: str
    use_case: str
    historical_logs_range: Optional[Dict[str, str]] = None
    initial_training_data: Optional[List[Dict[str, Any]]] = None


@router.post("/register")
async def register_model(
    request: ModelRegisterRequest,
    _admin: bool = Depends(verify_model_admin)  # SECURITY: Admin only
):
    """Register a new model in the registry. REQUIRES ADMIN API KEY."""
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
    current_model_id: str,
    _admin: bool = Depends(verify_model_admin)  # SECURITY: Admin only - COST PROTECTION
):
    """Switch to a new paid model. REQUIRES ADMIN API KEY (prevents cost attacks)."""
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
async def fine_tune_model(
    request: FineTuneRequest,
    _admin: bool = Depends(verify_model_admin)  # SECURITY: Admin only
):
    """Fine-tune a model using historical logs. REQUIRES ADMIN API KEY."""
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








