"""
Three-Model Collaboration System
================================

Generates expert trajectories for SRL→RLVR training using three specialized models:
1. Lore Retriever (Model A): Retrieves and synthesizes knowledge
2. Teacher Planner (Model B): Generates expert step-by-step strategies
3. Verifier (Model C): Validates structure, enforces rules, produces rewards

All models collaborate dynamically to ensure training examples are NEVER static.
"""

from .lore_retriever import LoreRetriever
from .teacher_planner import TeacherPlanner
from .verifier import Verifier
from .collaboration_orchestrator import CollaborationOrchestrator

__all__ = [
    "LoreRetriever",
    "TeacherPlanner",
    "Verifier",
    "CollaborationOrchestrator",
]

