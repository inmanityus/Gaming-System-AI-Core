"""
Performance Budget System - Enforces frame budgets for target FPS.

Implements REQ-PERF-002: Performance Budget System.
"""

from .budget_monitor import (
    PerformanceBudgetMonitor,
    PerformanceBudgetContext,
    PerformanceMode,
    SubsystemBudget,
    FrameMetrics,
    get_budget_monitor,
    set_performance_mode,
)

__all__ = [
    "PerformanceBudgetMonitor",
    "PerformanceBudgetContext",
    "PerformanceMode",
    "SubsystemBudget",
    "FrameMetrics",
    "get_budget_monitor",
    "set_performance_mode",
]








