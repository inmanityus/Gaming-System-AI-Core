"""
AI-003: LoRA Adapter API Routes
FastAPI routes for LoRA adapter management.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, validator

from lora_manager import LoRAManager, LoRAAdapter

router = APIRouter(prefix="/api/v1/lora", tags=["LoRA Adapters"])

# SECURITY: Base directory for LoRA adapters - MUST be absolute path
BASE_ADAPTER_DIRECTORY = os.path.abspath(os.getenv('LORA_ADAPTER_BASE_DIR', '/models/adapters/'))

# SECURITY: API Keys for authentication
API_KEYS = set(os.getenv('LORA_API_KEYS', '').split(',')) if os.getenv('LORA_API_KEYS') else set()

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for protected endpoints (REQUIRED FOR PRODUCTION)."""
    if not API_KEYS:
        # Development mode warning
        import logging
        logging.warning("LORA_API_KEYS not configured - allowing unauthenticated access (INSECURE!)")
        return True
    
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

def validate_adapter_path(path: str) -> str:
    """
    SECURITY: Validate adapter path to prevent path traversal attacks.
    
    Returns absolute path within BASE_ADAPTER_DIRECTORY.
    Raises HTTPException if path is invalid or outside allowed directory.
    """
    # Reject obviously malicious patterns
    if '..' in path or path.startswith('/') or path.startswith('\\'):
        raise HTTPException(status_code=400, detail="Invalid path: path traversal detected")
    
    # Build absolute path within base directory
    try:
        # Join with base directory
        full_path = os.path.join(BASE_ADAPTER_DIRECTORY, path)
        # Resolve to absolute path (follows symlinks)
        resolved_path = os.path.realpath(full_path)
        # Ensure resolved path is within base directory
        if not resolved_path.startswith(os.path.realpath(BASE_ADAPTER_DIRECTORY)):
            raise HTTPException(status_code=400, detail="Invalid path: outside allowed directory")
        return resolved_path
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {str(e)}")

# Pydantic models
class LoRAAdapterRequest(BaseModel):
    name: str
    base_model: str
    path: str
    rank: int = 64
    alpha: float = 16.0
    
    @validator('path')
    def validate_path(cls, v):
        """Validate path format (additional validation done in endpoint)."""
        if not v or not isinstance(v, str):
            raise ValueError("path must be a non-empty string")
        if len(v) > 500:
            raise ValueError("path too long (max 500 characters)")
        return v


class LoRAAdapterResponse(BaseModel):
    name: str
    base_model: str
    path: str
    rank: int
    alpha: float
    loaded: bool
    loaded_at: Optional[str] = None
    memory_mb: int = 0


class LoRAHotSwapRequest(BaseModel):
    old_name: str
    new_name: str


# Dependency
_lora_manager: Optional[LoRAManager] = None

def get_lora_manager() -> LoRAManager:
    """Get or create LoRA manager instance."""
    global _lora_manager
    if _lora_manager is None:
        _lora_manager = LoRAManager()
    return _lora_manager


@router.post("/register", response_model=LoRAAdapterResponse)
async def register_adapter(
    request: LoRAAdapterRequest,
    manager: LoRAManager = Depends(get_lora_manager),
    _auth: bool = Depends(verify_api_key)  # SECURITY: Require authentication
):
    """
    Register a LoRA adapter.
    
    SECURITY: Requires API key authentication. Path is validated to prevent traversal.
    """
    # SECURITY: Validate and sanitize path
    validated_path = validate_adapter_path(request.path)
    
    try:
        await manager.register_adapter(
            name=request.name,
            base_model=request.base_model,
            path=validated_path,  # Use validated path
            rank=request.rank,
            alpha=request.alpha
        )
        
        status = await manager.get_adapter_status(request.name)
        return LoRAAdapterResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/load/{adapter_name}")
async def load_adapter(
    adapter_name: str,
    manager: LoRAManager = Depends(get_lora_manager),
    _auth: bool = Depends(verify_api_key)  # SECURITY: Require authentication
):
    """Load a LoRA adapter into vLLM server. Requires API key authentication."""
    try:
        success = await manager.load_adapter(adapter_name)
        if success:
            return {"success": True, "message": f"Adapter {adapter_name} loaded"}
        else:
            raise HTTPException(status_code=500, detail="Failed to load adapter")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unload/{adapter_name}")
async def unload_adapter(
    adapter_name: str,
    manager: LoRAManager = Depends(get_lora_manager),
    _auth: bool = Depends(verify_api_key)  # SECURITY: Require authentication
):
    """Unload a LoRA adapter from vLLM server. Requires API key authentication."""
    try:
        success = await manager.unload_adapter(adapter_name)
        if success:
            return {"success": True, "message": f"Adapter {adapter_name} unloaded"}
        else:
            raise HTTPException(status_code=500, detail="Failed to unload adapter")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hot-swap", response_model=dict)
async def hot_swap_adapter(
    request: LoRAHotSwapRequest,
    manager: LoRAManager = Depends(get_lora_manager),
    _auth: bool = Depends(verify_api_key)  # SECURITY: Require authentication
):
    """Hot-swap adapters (unload old, load new) without downtime. Requires API key authentication."""
    try:
        success = await manager.hot_swap_adapter(request.old_name, request.new_name)
        if success:
            return {
                "success": True,
                "message": f"Swapped from {request.old_name} to {request.new_name}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to hot-swap adapters")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[LoRAAdapterResponse])
async def list_adapters(
    loaded_only: bool = False,
    manager: LoRAManager = Depends(get_lora_manager)
):
    """List all registered adapters."""
    try:
        adapters = await manager.list_adapters(loaded_only=loaded_only)
        return [LoRAAdapterResponse(**adapter) for adapter in adapters]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{adapter_name}", response_model=LoRAAdapterResponse)
async def get_adapter_status(
    adapter_name: str,
    manager: LoRAManager = Depends(get_lora_manager)
):
    """Get status of a specific adapter."""
    try:
        status = await manager.get_adapter_status(adapter_name)
        if status:
            return LoRAAdapterResponse(**status)
        else:
            raise HTTPException(status_code=404, detail=f"Adapter {adapter_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory", response_model=dict)
async def get_memory_usage(
    manager: LoRAManager = Depends(get_lora_manager)
):
    """Get memory usage statistics for loaded adapters."""
    try:
        memory_stats = await manager.get_memory_usage()
        return memory_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

