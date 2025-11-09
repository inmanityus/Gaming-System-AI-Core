"""
AI Models Service - Core Model Management
Archetype Model Chain System implementation.

This service provides:
- Archetype chain registry (Redis-backed)
- Base model lifecycle management
- LoRA adapter orchestration
- Inference coordination with ai_integration service

Architecture:
- services/ai_models/ - Orchestration layer (this)
- services/ai_integration/ - vLLM HTTP service layer
- services/memory/ - 3-tier memory system

Multi-model collaboration:
- Claude Sonnet 4.5: Architecture integration
- Gemini 2.5 Pro: ML optimization (AWQ quantization requirement)
- Perplexity: Production best practices (vLLM multi-LoRA)
"""

__version__ = "1.0.0"
__author__ = "AI Core Team (Multi-Model Collaboration)"

from .archetype_chain_registry import (
    ArchetypeChainRegistry,
    ArchetypeType,
    AdapterTask,
    AdapterInfo,
    ArchetypeChainConfig,
)

__all__ = [
    "ArchetypeChainRegistry",
    "ArchetypeType",
    "AdapterTask", 
    "AdapterInfo",
    "ArchetypeChainConfig",
]

