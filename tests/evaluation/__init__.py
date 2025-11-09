"""
Evaluation Harness for Archetype Model Chain System

Provides:
- Acceptance tests per archetype
- Quality gates (consistency, lore accuracy, sentiment tracking)
- Performance benchmarks (latency, memory, throughput)
- Regression testing for adapter updates

Test Archetypes:
1. Vampire: Rich dialogue, 8-10 min conversations, >90% lore accuracy
2. Zombie: Horde behaviors, 100-300 concurrent, >95% action coherence

Multi-model collaboration:
- GPT-5 Codex: Test implementation
- Gemini 2.5 Pro: Performance validation
- Claude Sonnet 4.5: Quality metrics
"""

__version__ = "1.0.0"
__author__ = "AI Core Team (Multi-Model Collaboration)"

from .archetype_eval_harness import (
    ArchetypeEvaluationHarness,
    ArchetypeTest,
    QualityGate,
    EvaluationResult,
)

__all__ = [
    "ArchetypeEvaluationHarness",
    "ArchetypeTest",
    "QualityGate",
    "EvaluationResult",
]

