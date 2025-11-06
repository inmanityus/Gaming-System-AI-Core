"""
Performance Budget Monitor - Enforces frame budgets for 300+ FPS.

Implements REQ-PERF-002: Performance Budget System.

Tracks and enforces performance budgets for all subsystems to ensure
300+ FPS in Competitive Mode and 60-120 FPS in Immersive Mode.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
from contextlib import contextmanager
import threading

_logger = logging.getLogger(__name__)


class PerformanceMode(Enum):
    """Performance mode."""
    COMPETITIVE = "competitive"  # 300+ FPS target
    IMMERSIVE = "immersive"      # 60-120 FPS target


@dataclass
class SubsystemBudget:
    """Budget allocation for a subsystem."""
    name: str
    budget_ms: float  # Milliseconds per frame
    parent: Optional[str] = None  # Parent subsystem for hierarchy
    current_ms: float = 0.0
    max_ms: float = 0.0
    # Rolling window statistics (last N frames) - prevents unbounded growth
    recent_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    violations: int = 0
    warnings: int = 0
    
    def average_ms(self) -> float:
        """Get average time over recent frames."""
        if not self.recent_times:
            return 0.0
        return sum(self.recent_times) / len(self.recent_times)
    
    def percentile_ms(self, p: float) -> float:
        """Get percentile time (e.g., p=0.95 for 95th percentile)."""
        if not self.recent_times:
            return 0.0
        sorted_times = sorted(self.recent_times)
        idx = int(len(sorted_times) * p)
        return sorted_times[min(idx, len(sorted_times) - 1)]


@dataclass
class FrameMetrics:
    """Frame performance metrics."""
    frame_number: int
    total_time_ms: float
    subsystems: Dict[str, float]  # subsystem_name -> time_ms
    mode: PerformanceMode
    timestamp: float = field(default_factory=time.time)


class PerformanceBudgetMonitor:
    """
    Monitors and enforces performance budgets.
    
    Tracks frame times for all subsystems and ensures budgets are met.
    """
    
    def __init__(self, mode: PerformanceMode = PerformanceMode.COMPETITIVE):
        self.mode = mode
        self._lock = threading.Lock()
        
        # Define budgets based on mode
        # NOTE: Budget hierarchy - child subsystems' budgets are included in parent budgets
        # e.g., ai_proxy + gameplay + physics + animation + other_cpu should sum to <= cpu_total
        if mode == PerformanceMode.COMPETITIVE:
            # 300+ FPS = 3.33ms total frame budget
            self.frame_budget_ms = 3.33
            self.subsystem_budgets = {
                "cpu_total": SubsystemBudget("cpu_total", 1.1, parent=None),
                "ai_proxy": SubsystemBudget("ai_proxy", 0.1, parent="cpu_total"),
                "gameplay": SubsystemBudget("gameplay", 0.2, parent="cpu_total"),
                "physics": SubsystemBudget("physics", 0.3, parent="cpu_total"),
                "animation": SubsystemBudget("animation", 0.3, parent="cpu_total"),
                "other_cpu": SubsystemBudget("other_cpu", 0.2, parent="cpu_total"),
                "gpu_total": SubsystemBudget("gpu_total", 2.0, parent=None),
                "base_pass": SubsystemBudget("base_pass", 0.6, parent="gpu_total"),
                "lighting": SubsystemBudget("lighting", 0.5, parent="gpu_total"),
                "post_process": SubsystemBudget("post_process", 0.3, parent="gpu_total"),
                "ui": SubsystemBudget("ui", 0.1, parent="gpu_total"),
                "gpu_overhead": SubsystemBudget("gpu_overhead", 0.5, parent="gpu_total"),
                "audio": SubsystemBudget("audio", 0.15, parent=None),
                "os_driver_network": SubsystemBudget("os_driver_network", 0.08, parent=None),
            }
        else:  # IMMERSIVE
            # 60-120 FPS = 8.33-16.67ms total frame budget
            self.frame_budget_ms = 16.67  # Conservative (60 FPS)
            self.subsystem_budgets = {
                "cpu_total": SubsystemBudget("cpu_total", 2.5, parent=None),
                "ai_full": SubsystemBudget("ai_full", 1.0, parent="cpu_total"),
                "gameplay": SubsystemBudget("gameplay", 0.5, parent="cpu_total"),
                "physics": SubsystemBudget("physics", 0.5, parent="cpu_total"),
                "animation": SubsystemBudget("animation", 0.3, parent="cpu_total"),
                "other_cpu": SubsystemBudget("other_cpu", 0.2, parent="cpu_total"),
                "gpu_total": SubsystemBudget("gpu_total", 5.0, parent=None),
                "base_pass": SubsystemBudget("base_pass", 1.5, parent="gpu_total"),
                "lighting_lumen": SubsystemBudget("lighting_lumen", 2.0, parent="gpu_total"),
                "post_process": SubsystemBudget("post_process", 0.8, parent="gpu_total"),
                "ui": SubsystemBudget("ui", 0.2, parent="gpu_total"),
                "gpu_overhead": SubsystemBudget("gpu_overhead", 0.5, parent="gpu_total"),
                "audio": SubsystemBudget("audio", 0.5, parent=None),
                "os_driver_network": SubsystemBudget("os_driver_network", 0.33, parent=None),
            }
        
        # Frame history (last 1000 frames)
        self.frame_history: deque = deque(maxlen=1000)
        self.frame_number = 0
        
        # Performance statistics
        self.total_frames = 0
        self.total_time_ms = 0.0
        self.max_frame_time_ms = 0.0
        self.budget_violations = 0
        
    def start_frame(self) -> int:
        """Start a new frame. Returns frame number."""
        with self._lock:
            self.frame_number += 1
            self.total_frames += 1
            return self.frame_number
    
    def record_subsystem_time(self, subsystem_name: str, time_ms: float):
        """
        Record time spent in a subsystem.
        
        Args:
            subsystem_name: Name of the subsystem
            time_ms: Time spent in milliseconds (must be non-negative)
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation (outside lock to avoid holding lock during validation errors)
        if not subsystem_name or not isinstance(subsystem_name, str):
            raise ValueError(f"Invalid subsystem_name: {subsystem_name}")
        
        if not isinstance(time_ms, (int, float)) or time_ms < 0:
            raise ValueError(f"Invalid time_ms: {time_ms} (must be non-negative number)")
        
        if time_ms > 1000.0:  # Sanity check: > 1 second is likely an error
            raise ValueError(f"Suspiciously high time_ms: {time_ms}ms for {subsystem_name}")
        
        violation_msg = None
        warning_msg = None
        
        with self._lock:
            if subsystem_name not in self.subsystem_budgets:
                # Create budget if doesn't exist
                self.subsystem_budgets[subsystem_name] = SubsystemBudget(
                    subsystem_name,
                    budget_ms=0.5,  # Default budget
                    parent=None
                )
            
            budget = self.subsystem_budgets[subsystem_name]
            budget.current_ms = time_ms
            budget.recent_times.append(time_ms)
            
            if time_ms > budget.max_ms:
                budget.max_ms = time_ms
            
            # Check for violations
            if time_ms > budget.budget_ms:
                budget.violations += 1
                self.budget_violations += 1
                violation_msg = (subsystem_name, time_ms, budget.budget_ms)
            elif time_ms > budget.budget_ms * 0.8:  # Warning at 80% of budget
                budget.warnings += 1
                warning_msg = (subsystem_name, time_ms, budget.budget_ms)
        
        # I/O outside lock to prevent deadlock risk
        if violation_msg:
            name, actual, expected = violation_msg
            _logger.warning(
                "BUDGET VIOLATION: %s took %.3fms (budget: %.3fms)",
                name, actual, expected
            )
        elif warning_msg and _logger.isEnabledFor(logging.DEBUG):
            name, actual, expected = warning_msg
            _logger.debug(
                "BUDGET WARNING: %s at %.3fms (budget: %.3fms)",
                name, actual, expected
            )
    
    def end_frame(self, frame_number: int) -> FrameMetrics:
        """End a frame and return metrics."""
        with self._lock:
            # Calculate total frame time
            total_time_ms = sum(
                budget.current_ms
                for budget in self.subsystem_budgets.values()
            )
            
            self.total_time_ms += total_time_ms
            if total_time_ms > self.max_frame_time_ms:
                self.max_frame_time_ms = total_time_ms
            
            # Check total budget violation
            frame_violation = None
            if total_time_ms > self.frame_budget_ms:
                self.budget_violations += 1
                frame_violation = (frame_number, total_time_ms, self.frame_budget_ms)
            
            # Create metrics
            subsystem_times = {
                name: budget.current_ms
                for name, budget in self.subsystem_budgets.items()
            }
            
            metrics = FrameMetrics(
                frame_number=frame_number,
                total_time_ms=total_time_ms,
                subsystems=subsystem_times,
                mode=self.mode
            )
            
            self.frame_history.append(metrics)
            
            # Reset current times
            for budget in self.subsystem_budgets.values():
                budget.current_ms = 0.0
        
        # I/O outside lock
        if frame_violation:
            frame_num, actual, expected = frame_violation
            _logger.warning(
                "FRAME BUDGET VIOLATION: Frame %d took %.3fms (budget: %.3fms)",
                frame_num, actual, expected
            )
        
        return metrics
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        with self._lock:
            avg_frame_time = (
                self.total_time_ms / self.total_frames
                if self.total_frames > 0
                else 0.0
            )
            
            estimated_fps = (
                1000.0 / avg_frame_time
                if avg_frame_time > 0
                else 0.0
            )
            
            subsystems_status = {}
            for name, budget in self.subsystem_budgets.items():
                avg_time = budget.average_ms()
                p95_time = budget.percentile_ms(0.95)
                
                subsystems_status[name] = {
                    "budget_ms": budget.budget_ms,
                    "avg_time_ms": avg_time,
                    "max_time_ms": budget.max_ms,
                    "p95_time_ms": p95_time,
                    "violations": budget.violations,
                    "warnings": budget.warnings,
                    "utilization_percent": (avg_time / budget.budget_ms * 100) if budget.budget_ms > 0 else 0.0,
                    "parent": budget.parent,
                }
            
            return {
                "mode": self.mode.value,
                "frame_budget_ms": self.frame_budget_ms,
                "total_frames": self.total_frames,
                "avg_frame_time_ms": avg_frame_time,
                "max_frame_time_ms": self.max_frame_time_ms,
                "estimated_fps": estimated_fps,
                "budget_violations": self.budget_violations,
                "violation_rate": (
                    self.budget_violations / self.total_frames * 100
                    if self.total_frames > 0
                    else 0.0
                ),
                "subsystems": subsystems_status,
            }
    
    def set_mode(self, mode: PerformanceMode):
        """Switch performance mode."""
        with self._lock:
            self.mode = mode
            
            # Reinitialize budgets for new mode
            if mode == PerformanceMode.COMPETITIVE:
                self.frame_budget_ms = 3.33
                # Reinitialize with competitive budgets
                # (keeping existing data, just updating budgets)
            else:  # IMMERSIVE
                self.frame_budget_ms = 16.67
                # Reinitialize with immersive budgets
    
    def get_recent_frames(self, count: int = 100) -> List[FrameMetrics]:
        """Get recent frame metrics."""
        with self._lock:
            return list(self.frame_history)[-count:]
    
    def should_skip_work(self, subsystem_name: str) -> bool:
        """
        Check if subsystem should skip non-critical work to stay in budget.
        
        Returns True if subsystem is over budget and should reduce work.
        """
        with self._lock:
            budget = self.subsystem_budgets.get(subsystem_name)
            if not budget:
                return False
            
            # If consistently over budget, signal to reduce work
            if len(budget.recent_times) >= 10:
                recent_avg = sum(list(budget.recent_times)[-10:]) / 10
                return recent_avg > budget.budget_ms * 1.2  # 20% over budget
            return False
    
    def get_quality_scale(self, subsystem_name: str) -> float:
        """
        Get quality scale factor (0.0-1.0) based on budget pressure.
        
        Returns lower values when over budget to reduce workload.
        """
        with self._lock:
            budget = self.subsystem_budgets.get(subsystem_name)
            if not budget or not budget.recent_times:
                return 1.0
            
            recent_avg = sum(list(budget.recent_times)[-10:]) / 10 if len(budget.recent_times) >= 10 else budget.average_ms()
            ratio = recent_avg / budget.budget_ms if budget.budget_ms > 0 else 1.0
            
            if ratio <= 0.8:
                return 1.0  # Under budget - max quality
            elif ratio >= 1.5:
                return 0.5  # Severely over budget - reduce quality
            else:
                # Linear interpolation between 0.8-1.5 ratio
                return 1.0 - ((ratio - 0.8) / 0.7) * 0.5
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        with self._lock:
            avg_frame_time = (
                sum(m.total_time_ms for m in self.frame_history) / len(self.frame_history)
                if self.frame_history else 0.0
            )
            
            return {
                "mode": self.mode.value,
                "total_frames": self.total_frames,
                "avg_frame_time_ms": avg_frame_time,
                "max_frame_time_ms": self.max_frame_time_ms,
                "target_frame_time_ms": self.frame_budget_ms,
                "budget_violations": self.budget_violations,
                "violation_rate": (
                    self.budget_violations / self.total_frames * 100
                    if self.total_frames > 0 else 0.0
                ),
                "subsystems": {
                    name: {
                        "budget_ms": budget.budget_ms,
                        "avg_ms": budget.average_ms(),
                        "max_ms": budget.max_ms,
                        "p95_ms": budget.percentile_ms(0.95),
                        "violations": budget.violations,
                        "warnings": budget.warnings,
                        "parent": budget.parent,
                    }
                    for name, budget in self.subsystem_budgets.items()
                }
            }
    
    def reset_statistics(self):
        """Reset all statistics."""
        with self._lock:
            self.total_frames = 0
            self.total_time_ms = 0.0
            self.max_frame_time_ms = 0.0
            self.budget_violations = 0
            self.frame_history.clear()
            
            for budget in self.subsystem_budgets.values():
                budget.current_ms = 0.0
                budget.max_ms = 0.0
                budget.recent_times.clear()
                budget.violations = 0
                budget.warnings = 0


    @contextmanager
    def time_subsystem(self, subsystem_name: str):
        """
        Context manager for timing a subsystem.
        
        Usage:
            with monitor.time_subsystem("physics"):
                run_physics_simulation()
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.record_subsystem_time(subsystem_name, elapsed_ms)


class PerformanceBudgetContext:
    """
    Context manager for tracking subsystem performance.
    
    Usage:
        with PerformanceBudgetContext(monitor, "ai_proxy"):
            # Code to measure
            pass
    """
    
    def __init__(self, monitor: PerformanceBudgetMonitor, subsystem_name: str):
        self.monitor = monitor
        self.subsystem_name = subsystem_name
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
            self.monitor.record_subsystem_time(self.subsystem_name, elapsed_ms)
        return False


# Global monitor instance
_global_monitor: Optional[PerformanceBudgetMonitor] = None


def get_budget_monitor(mode: PerformanceMode = PerformanceMode.COMPETITIVE) -> PerformanceBudgetMonitor:
    """Get global budget monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceBudgetMonitor(mode)
    return _global_monitor


def set_performance_mode(mode: PerformanceMode):
    """Set global performance mode."""
    monitor = get_budget_monitor()
    monitor.set_mode(mode)

