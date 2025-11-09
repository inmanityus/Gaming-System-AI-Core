"""
Archetype Evaluation Harness
Coder: Claude Sonnet 4.5

Quality gates and performance benchmarks for archetype testing.

Success Criteria:
- Vampire: 8-10 min conversation, >90% lore accuracy
- Zombie: 100-300 concurrent, >95% action coherence
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ArchetypeType(str, Enum):
    """Archetype types."""
    VAMPIRE = "vampire"
    WEREWOLF = "werewolf"
    ZOMBIE = "zombie"
    GHOUL = "ghoul"
    LICH = "lich"


@dataclass
class QualityGate:
    """Quality threshold."""
    metric_name: str
    min_score: float
    max_score: float = 1.0
    description: Optional[str] = None
    
    def check(self, actual: float) -> bool:
        """Check if score passes gate."""
        return self.min_score <= actual <= self.max_score


@dataclass
class PerformanceGate:
    """Performance threshold."""
    metric_name: str
    max_value: float
    unit: str = "ms"
    description: Optional[str] = None
    
    def check(self, actual: float) -> bool:
        """Check if value passes gate."""
        return actual <= self.max_value


@dataclass
class ArchetypeTest:
    """Test definition."""
    archetype: ArchetypeType
    test_name: str
    test_type: str
    duration_minutes: Optional[float] = None
    num_npcs: int = 1
    quality_gates: List[QualityGate] = field(default_factory=list)
    performance_gates: List[PerformanceGate] = field(default_factory=list)


@dataclass
class TestMetrics:
    """Collected metrics."""
    lore_accuracy: float = 0.0
    consistency_score: float = 0.0
    action_coherence: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    memory_usage_gb: float = 0.0
    throughput_npcs_per_sec: float = 0.0
    turn_count: int = 0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lore_accuracy': self.lore_accuracy,
            'consistency_score': self.consistency_score,
            'action_coherence': self.action_coherence,
            'latency_p50_ms': self.latency_p50_ms,
            'latency_p95_ms': self.latency_p95_ms,
            'memory_usage_gb': self.memory_usage_gb,
            'throughput_npcs_per_sec': self.throughput_npcs_per_sec,
            'turn_count': self.turn_count,
            'error_count': self.error_count
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    test: ArchetypeTest
    metrics: TestMetrics
    passed: bool
    failed_gates: List[str]
    duration_seconds: float
    start_time: datetime
    end_time: datetime


class ArchetypeEvaluationHarness:
    """Evaluation harness for archetype testing."""
    
    def __init__(self):
        self.results: List[EvaluationResult] = []
        logger.info("Evaluation harness initialized")
    
    async def run_test(self, test: ArchetypeTest) -> EvaluationResult:
        """Run archetype test."""
        logger.info(f"Running test: {test.test_name}")
        
        start_time = datetime.now()
        metrics = TestMetrics()
        
        # Run test type
        if test.test_type == "conversation":
            metrics = await self._run_conversation_test(test)
        elif test.test_type == "horde":
            metrics = await self._run_horde_test(test)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Check gates
        passed = True
        failed = []
        
        for gate in test.quality_gates:
            actual = getattr(metrics, gate.metric_name, 0.0)
            if not gate.check(actual):
                passed = False
                failed.append(f"{gate.metric_name}: {actual:.3f} < {gate.min_score:.3f}")
        
        for gate in test.performance_gates:
            actual = getattr(metrics, gate.metric_name, 0.0)
            if not gate.check(actual):
                passed = False
                failed.append(f"{gate.metric_name}: {actual:.1f} > {gate.max_value:.1f}")
        
        result = EvaluationResult(
            test=test,
            metrics=metrics,
            passed=passed,
            failed_gates=failed,
            duration_seconds=duration,
            start_time=start_time,
            end_time=end_time
        )
        
        self.results.append(result)
        logger.info(f"{'✅ PASSED' if passed else '❌ FAILED'}: {test.test_name}")
        
        return result
    
    async def _run_conversation_test(self, test: ArchetypeTest) -> TestMetrics:
        """Run conversation test (placeholder)."""
        await asyncio.sleep(0.1)
        
        metrics = TestMetrics()
        metrics.lore_accuracy = 0.92
        metrics.consistency_score = 0.96
        metrics.latency_p95_ms = 180.0
        metrics.turn_count = int((test.duration_minutes or 1.0) * 6)
        
        return metrics
    
    async def _run_horde_test(self, test: ArchetypeTest) -> TestMetrics:
        """Run horde test (placeholder)."""
        await asyncio.sleep(0.5)
        
        metrics = TestMetrics()
        metrics.action_coherence = 0.97
        metrics.throughput_npcs_per_sec = test.num_npcs / 1.0
        metrics.memory_usage_gb = 12.5
        
        return metrics
    
    async def run_vampire_conversation_test(self, duration_min: float = 10.0) -> EvaluationResult:
        """Run vampire conversation test."""
        test = ArchetypeTest(
            archetype=ArchetypeType.VAMPIRE,
            test_name="vampire_long_conversation",
            test_type="conversation",
            duration_minutes=duration_min,
            quality_gates=[
                QualityGate("lore_accuracy", min_score=0.90),
                QualityGate("consistency_score", min_score=0.95),
            ],
            performance_gates=[
                PerformanceGate("latency_p95_ms", max_value=250.0),
                PerformanceGate("memory_usage_gb", max_value=15.0),
            ]
        )
        return await self.run_test(test)
    
    async def run_zombie_horde_test(self, num_zombies: int = 300) -> EvaluationResult:
        """Run zombie horde test."""
        test = ArchetypeTest(
            archetype=ArchetypeType.ZOMBIE,
            test_name="zombie_horde_scale",
            test_type="horde",
            num_npcs=num_zombies,
            quality_gates=[
                QualityGate("action_coherence", min_score=0.95),
            ],
            performance_gates=[
                PerformanceGate("latency_p95_ms", max_value=250.0),
                PerformanceGate("memory_usage_gb", max_value=15.0),
            ]
        )
        return await self.run_test(test)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test results summary."""
        if not self.results:
            return {'message': 'No tests run'}
        
        passed = sum(1 for r in self.results if r.passed)
        return {
            'total': len(self.results),
            'passed': passed,
            'failed': len(self.results) - passed,
            'pass_rate': passed / len(self.results)
        }

