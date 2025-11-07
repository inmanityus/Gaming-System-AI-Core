"""
Tests for Performance Budget Monitor.

Implements REQ-PERF-002: Performance Budget System.
"""

import pytest
import time
from services.performance_budget.budget_monitor import (
    PerformanceBudgetMonitor,
    PerformanceMode,
    SubsystemBudget,
    FrameMetrics,
    PerformanceBudgetContext,
)


def test_monitor_creation_competitive():
    """Test monitor creation in competitive mode."""
    monitor = PerformanceBudgetMonitor(PerformanceMode.COMPETITIVE)
    
    assert monitor.mode == PerformanceMode.COMPETITIVE
    assert monitor.frame_budget_ms == 3.33
    assert "ai_proxy" in monitor.subsystem_budgets
    assert monitor.subsystem_budgets["ai_proxy"].budget_ms == 0.1


def test_monitor_creation_immersive():
    """Test monitor creation in immersive mode."""
    monitor = PerformanceBudgetMonitor(PerformanceMode.IMMERSIVE)
    
    assert monitor.mode == PerformanceMode.IMMERSIVE
    assert monitor.frame_budget_ms == 16.67
    assert "ai_full" in monitor.subsystem_budgets
    assert monitor.subsystem_budgets["ai_full"].budget_ms == 1.0


def test_start_frame():
    """Test starting a new frame."""
    monitor = PerformanceBudgetMonitor()
    
    frame_num = monitor.start_frame()
    assert frame_num == 1
    assert monitor.total_frames == 1
    
    frame_num2 = monitor.start_frame()
    assert frame_num2 == 2
    assert monitor.total_frames == 2


def test_record_subsystem_time():
    """Test recording subsystem time."""
    monitor = PerformanceBudgetMonitor()
    
    monitor.record_subsystem_time("ai_proxy", 0.05)
    
    budget = monitor.subsystem_budgets["ai_proxy"]
    assert budget.current_ms == 0.05
    assert budget.max_ms == 0.05
    assert len(budget.recent_times) == 1


def test_record_subsystem_time_violation():
    """Test recording subsystem time that violates budget."""
    monitor = PerformanceBudgetMonitor()
    
    # Record time exceeding budget
    monitor.record_subsystem_time("ai_proxy", 0.15)  # Budget is 0.1ms
    
    budget = monitor.subsystem_budgets["ai_proxy"]
    assert budget.violations == 1
    assert monitor.budget_violations == 1


def test_record_subsystem_time_validation():
    """Test input validation for record_subsystem_time."""
    monitor = PerformanceBudgetMonitor()
    
    # Invalid subsystem name
    with pytest.raises(ValueError):
        monitor.record_subsystem_time("", 0.1)
    
    # Invalid time (negative)
    with pytest.raises(ValueError):
        monitor.record_subsystem_time("ai_proxy", -0.1)
    
    # Invalid time (too high)
    with pytest.raises(ValueError):
        monitor.record_subsystem_time("ai_proxy", 2000.0)


def test_end_frame():
    """Test ending a frame and getting metrics."""
    monitor = PerformanceBudgetMonitor()
    
    frame_num = monitor.start_frame()
    monitor.record_subsystem_time("ai_proxy", 0.05)
    monitor.record_subsystem_time("gameplay", 0.1)
    
    metrics = monitor.end_frame(frame_num)
    
    assert isinstance(metrics, FrameMetrics)
    assert metrics.frame_number == frame_num
    assert metrics.total_time_ms > 0
    assert "ai_proxy" in metrics.subsystems
    assert metrics.mode == PerformanceMode.COMPETITIVE


def test_end_frame_budget_violation():
    """Test frame budget violation."""
    monitor = PerformanceBudgetMonitor()
    
    frame_num = monitor.start_frame()
    # Record times that exceed total frame budget
    monitor.record_subsystem_time("cpu_total", 2.0)  # Budget is 1.1ms
    monitor.record_subsystem_time("gpu_total", 3.0)  # Budget is 2.0ms
    
    metrics = monitor.end_frame(frame_num)
    
    # Total exceeds 3.33ms budget
    assert metrics.total_time_ms > monitor.frame_budget_ms


def test_get_budget_status():
    """Test getting budget status."""
    monitor = PerformanceBudgetMonitor()
    
    monitor.start_frame()
    monitor.record_subsystem_time("ai_proxy", 0.05)
    monitor.end_frame(1)
    
    status = monitor.get_budget_status()
    
    assert status["mode"] == "competitive"
    assert status["total_frames"] == 1
    assert "subsystems" in status
    assert "ai_proxy" in status["subsystems"]


def test_get_statistics():
    """Test getting comprehensive statistics."""
    monitor = PerformanceBudgetMonitor()
    
    for i in range(10):
        frame_num = monitor.start_frame()
        monitor.record_subsystem_time("ai_proxy", 0.05)
        monitor.end_frame(frame_num)
    
    stats = monitor.get_statistics()
    
    assert stats["total_frames"] == 10
    assert "subsystems" in stats
    assert "ai_proxy" in stats["subsystems"]
    assert "avg_ms" in stats["subsystems"]["ai_proxy"]
    assert "p95_ms" in stats["subsystems"]["ai_proxy"]


def test_should_skip_work():
    """Test should_skip_work method."""
    monitor = PerformanceBudgetMonitor()
    
    # Initially should not skip
    assert monitor.should_skip_work("ai_proxy") is False
    
    # Record multiple violations
    for _ in range(15):
        monitor.record_subsystem_time("ai_proxy", 0.15)  # Over budget
    
    # Should now recommend skipping
    assert monitor.should_skip_work("ai_proxy") is True


def test_get_quality_scale():
    """Test get_quality_scale method."""
    monitor = PerformanceBudgetMonitor()
    
    # Under budget - should return 1.0
    monitor.record_subsystem_time("ai_proxy", 0.05)
    assert monitor.get_quality_scale("ai_proxy") == 1.0
    
    # Over budget - should return lower value
    for _ in range(15):
        monitor.record_subsystem_time("ai_proxy", 0.15)
    
    scale = monitor.get_quality_scale("ai_proxy")
    assert 0.0 <= scale <= 1.0
    assert scale < 1.0


def test_time_subsystem_context_manager():
    """Test time_subsystem context manager."""
    monitor = PerformanceBudgetMonitor()
    
    with monitor.time_subsystem("ai_proxy"):
        time.sleep(0.001)  # 1ms sleep
    
    budget = monitor.subsystem_budgets["ai_proxy"]
    assert len(budget.recent_times) == 1
    assert budget.recent_times[0] > 0


def test_reset_statistics():
    """Test resetting statistics."""
    monitor = PerformanceBudgetMonitor()
    
    # Add some data
    for i in range(10):
        frame_num = monitor.start_frame()
        monitor.record_subsystem_time("ai_proxy", 0.05)
        monitor.end_frame(frame_num)
    
    # Reset
    monitor.reset_statistics()
    
    assert monitor.total_frames == 0
    assert monitor.budget_violations == 0
    assert len(monitor.frame_history) == 0
    for budget in monitor.subsystem_budgets.values():
        assert len(budget.recent_times) == 0


def test_set_mode():
    """Test switching performance mode."""
    monitor = PerformanceBudgetMonitor(PerformanceMode.COMPETITIVE)
    
    assert monitor.mode == PerformanceMode.COMPETITIVE
    assert monitor.frame_budget_ms == 3.33
    
    monitor.set_mode(PerformanceMode.IMMERSIVE)
    
    assert monitor.mode == PerformanceMode.IMMERSIVE
    assert monitor.frame_budget_ms == 16.67


def test_subsystem_budget_average():
    """Test SubsystemBudget average calculation."""
    budget = SubsystemBudget("test", 1.0)
    
    budget.recent_times.append(0.5)
    budget.recent_times.append(0.6)
    budget.recent_times.append(0.7)
    
    assert budget.average_ms() == pytest.approx(0.6, abs=0.01)


def test_subsystem_budget_percentile():
    """Test SubsystemBudget percentile calculation."""
    budget = SubsystemBudget("test", 1.0)
    
    for i in range(10):
        budget.recent_times.append(i * 0.1)
    
    p95 = budget.percentile_ms(0.95)
    assert 0.8 <= p95 <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



