"""
Shared models for Orchestration Service
"""

from typing import Any, Dict
from pydantic import BaseModel


class ContentRequest(BaseModel):
    """Request for content generation."""
    prompt: str
    context: Dict[str, Any] = {}


class ContentResponse(BaseModel):
    """Response from content generation."""
    content: str
    metadata: Dict[str, Any] = {}

