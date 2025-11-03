"""
Three-Model Collaboration System
================================

Generates expert trajectories for SRL→RLVR training using three specialized models:
1. Lore Retriever (Model A): Retrieves and synthesizes knowledge
2. Teacher Planner (Model B): Generates expert step-by-step strategies
3. Verifier (Model C): Validates structure, enforces rules, produces rewards

All models collaborate dynamically to ensure training examples are NEVER static.
"""

from .base_http_client import BaseHttpClient
from .lore_retriever import LoreRetriever, LoreContext
from .teacher_planner import TeacherPlanner, ExpertTrajectory
from .verifier import Verifier, VerificationResult
from .collaboration_orchestrator import CollaborationOrchestrator, CollaborationResult
from .rules_engine_client import RulesEngineClient
from .lore_database_client import LoreDatabaseClient

__all__ = [
    "BaseHttpClient",
    "LoreRetriever",
    "LoreContext",
    "TeacherPlanner",
    "ExpertTrajectory",
    "Verifier",
    "VerificationResult",
    "CollaborationOrchestrator",
    "CollaborationResult",
    "RulesEngineClient",
    "LoreDatabaseClient",
]
