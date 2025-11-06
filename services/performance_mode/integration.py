"""
Integration with Budget Monitor for mode-aware budget enforcement.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from services.performance_mode.mode_manager import ModeManager, PerformanceMode
try:
    from services.performance_budget.budget_monitor import BudgetMonitor, PerformanceMode as BudgetMode
except ImportError:
    # Fallback if budget_monitor not available
    BudgetMonitor = None
    BudgetMode = None

_logger = logging.getLogger(__name__)


class ModeBudgetIntegrator:
    """Integrates ModeManager with BudgetMonitor for mode-aware budgets."""
    
    def __init__(
        self,
        mode_manager: ModeManager,
        budget_monitor: Optional[BudgetMonitor] = None
    ):
        self.mode_manager = mode_manager
        self.budget_monitor = budget_monitor
    
    def sync_budgets_for_mode(self, mode: PerformanceMode) -> None:
        """
        Sync budget monitor with current performance mode.
        
        Args:
            mode: Performance mode to sync
            
        Raises:
            RuntimeError: If sync fails after retries
        """
        if not self.budget_monitor:
            return
        
        if BudgetMode is None:
            _logger.warning("BudgetMonitor not available")
            return
        
        try:
            # Convert PerformanceMode to BudgetMonitor's PerformanceMode
            budget_mode = BudgetMode.COMPETITIVE if mode == PerformanceMode.COMPETITIVE else BudgetMode.IMMERSIVE
            
            # Update budget monitor mode with timeout
            if hasattr(self.budget_monitor, 'set_mode'):
                try:
                    # Use asyncio if async method exists
                    if asyncio.iscoroutinefunction(self.budget_monitor.set_mode):
                        # Run async method with timeout
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(
                            asyncio.wait_for(
                                self.budget_monitor.set_mode(budget_mode),
                                timeout=5.0
                            )
                        )
                    else:
                        # Sync method
                        self.budget_monitor.set_mode(budget_mode)
                    _logger.info(f"Budget monitor synced to mode: {budget_mode.value}")
                except asyncio.TimeoutError:
                    _logger.error(f"Budget monitor sync timeout for mode {mode}")
                    raise RuntimeError(f"Budget monitor sync timeout")
                except Exception as e:
                    _logger.error(f"Budget monitor sync failed: {e}", exc_info=True)
                    raise RuntimeError(f"Budget monitor sync failed: {e}") from e
            else:
                _logger.warning("BudgetMonitor does not have set_mode method")
        except Exception as e:
            _logger.error(f"Error syncing budgets for mode {mode}: {e}", exc_info=True)
            raise
    
    def get_budget_for_current_mode(self) -> Dict[str, float]:
        """
        Get budget allocations for current mode.
        
        Returns:
            Dictionary of subsystem budgets in milliseconds
        """
        mode = self.mode_manager.get_current_mode()
        
        if mode == PerformanceMode.COMPETITIVE:
            # 300 FPS = 3.33ms total per frame
            return {
                "cpu_total": 1.1,
                "ai_gameplay": 0.3,
                "physics": 0.3,
                "animation": 0.3,
                "other_cpu": 0.2,
                "gpu_total": 2.0,
                "base_pass": 0.6,
                "lighting": 0.5,
                "post_process": 0.3,
                "ui": 0.1,
                "gpu_overhead": 0.5,
                "audio": 0.15,
                "os_driver_network": 0.08,
            }
        else:
            # Immersive Mode: 60-120 FPS = 8.33-16.67ms total per frame
            # Use 12ms as middle ground
            return {
                "cpu_total": 2.5,
                "ai_full": 1.0,
                "gameplay": 0.5,
                "physics": 0.5,
                "animation": 0.3,
                "other_cpu": 0.2,
                "gpu_total": 8.0,
                "base_pass": 2.0,
                "lighting_lumen": 4.0,
                "post_process": 1.0,
                "ui": 0.2,
                "gpu_overhead": 0.8,
                "audio": 0.5,
                "os_driver_network": 0.5,
            }
