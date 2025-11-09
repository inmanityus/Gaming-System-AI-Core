"""
Archetype LoRA Coordinator - Production Implementation
Coder: Claude Sonnet 4.5
Awaiting Review: GPT-5 Pro

Orchestrates LoRA adapter management for archetypes.

Integrates:
- ArchetypeChainRegistry (metadata)
- services/ai_integration/lora_manager.py (vLLM HTTP API)

Features:
- Register all 7 adapters per archetype
- Load/unload adapters with LRU eviction
- Hot-swap adapters (<5ms target)
- Track usage for optimization
- Health monitoring
"""

import asyncio
import logging
import sys
import os
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Import registry components
from .archetype_chain_registry import (
    ArchetypeChainRegistry,
    ArchetypeType,
    AdapterTask,
    AdapterInfo
)

# Import existing LoRA manager
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_integration'))
try:
    from lora_manager import LoRAManager
except ImportError:
    LoRAManager = None

logger = logging.getLogger(__name__)


@dataclass
class AdapterLoadStatus:
    """
    Track adapter loading status and usage metrics.
    """
    adapter_name: str
    archetype: ArchetypeType
    task: AdapterTask
    path: str
    loaded: bool = False
    registered: bool = False
    last_used: Optional[datetime] = None
    load_count: int = 0
    usage_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    load_latency_ms: Optional[float] = None
    unload_latency_ms: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def mark_used(self) -> None:
        """Mark adapter as recently used (for LRU)."""
        self.last_used = datetime.now()
        self.usage_count += 1
    
    def mark_loaded(self, latency_ms: float = 0.0) -> None:
        """Mark adapter as loaded."""
        self.loaded = True
        self.load_count += 1
        self.load_latency_ms = latency_ms
        self.last_used = datetime.now()
        self.last_error = None
    
    def mark_unloaded(self, latency_ms: float = 0.0) -> None:
        """Mark adapter as unloaded."""
        self.loaded = False
        self.unload_latency_ms = latency_ms
    
    def mark_error(self, error: str) -> None:
        """Mark adapter error."""
        self.error_count += 1
        self.last_error = error


class ArchetypeLoRACoordinator:
    """
    Coordinates LoRA adapter management for archetypes.
    
    Responsibilities:
    - Register adapters with vLLM LoRA manager
    - Load/unload adapters with LRU eviction
    - Track usage for optimization
    - Provide health monitoring
    
    Design:
    - Per-adapter locks for thread safety
    - LRU eviction based on last_used timestamp
    - Integration with ArchetypeChainRegistry
    - Graceful error handling
    """
    
    def __init__(
        self,
        registry: ArchetypeChainRegistry,
        lora_manager: Any,  # LoRAManager from ai_integration
        max_loaded_adapters: int = 35
    ):
        """
        Initialize coordinator.
        
        Args:
            registry: Archetype chain registry
            lora_manager: vLLM LoRA manager
            max_loaded_adapters: Maximum adapters in GPU (default: 35 = 5×7)
        """
        if max_loaded_adapters <= 0:
            raise ValueError("max_loaded_adapters must be > 0")
        
        self.registry = registry
        self.lora_manager = lora_manager
        self.max_loaded_adapters = max_loaded_adapters
        
        # State tracking
        self._adapter_status: Dict[str, AdapterLoadStatus] = {}
        self._loaded_adapters: Set[str] = set()
        self._lock = asyncio.Lock()
        self._adapter_locks: Dict[str, asyncio.Lock] = {}
        
        # Metrics
        self._total_loads = 0
        self._total_unloads = 0
        self._total_evictions = 0
        
        logger.info(f"ArchetypeLoRACoordinator initialized: max_adapters={max_loaded_adapters}")
    
    def _adapter_name(self, archetype: ArchetypeType, task: AdapterTask) -> str:
        """Generate adapter name: {archetype}_{task}"""
        return f"{archetype.value}_{task.value}"
    
    def _get_adapter_lock(self, adapter_name: str) -> asyncio.Lock:
        """Get or create lock for specific adapter."""
        if adapter_name not in self._adapter_locks:
            self._adapter_locks[adapter_name] = asyncio.Lock()
        return self._adapter_locks[adapter_name]
    
    async def register_archetype_adapters(
        self,
        archetype: ArchetypeType
    ) -> Dict[AdapterTask, str]:
        """
        Register all 7 adapters for archetype with vLLM.
        
        Does NOT load into GPU yet - just registers.
        
        Returns:
            Mapping of task -> adapter_name
        """
        # Get chain config from registry
        chain = await self.registry.get_chain(archetype)
        if not chain:
            raise ValueError(f"No chain config for archetype: {archetype.value}")
        
        registered = {}
        
        for task, adapter_info in chain.adapters.items():
            adapter_name = self._adapter_name(archetype, task)
            
            # Get or create status
            if adapter_name not in self._adapter_status:
                async with self._lock:
                    self._adapter_status[adapter_name] = AdapterLoadStatus(
                        adapter_name=adapter_name,
                        archetype=archetype,
                        task=task,
                        path=adapter_info.path
                    )
            
            status = self._adapter_status[adapter_name]
            
            # Register if not already registered
            if not status.registered:
                async with self._get_adapter_lock(adapter_name):
                    try:
                        import time
                        start = time.time()
                        
                        await self.lora_manager.register_adapter(
                            name=adapter_name,
                            base_model=adapter_info.base_model,
                            path=adapter_info.path,
                            rank=adapter_info.rank,
                            alpha=adapter_info.alpha
                        )
                        
                        latency = (time.time() - start) * 1000
                        status.registered = True
                        status.load_latency_ms = latency
                        
                        logger.info(f"✅ Registered adapter: {adapter_name} ({latency:.1f}ms)")
                    
                    except Exception as e:
                        error_msg = f"Failed to register {adapter_name}: {e}"
                        status.mark_error(error_msg)
                        logger.error(error_msg)
                        raise
            
            registered[task] = adapter_name
        
        logger.info(f"Registered {len(registered)}/7 adapters for {archetype.value}")
        return registered
    
    async def load_archetype(
        self,
        archetype: ArchetypeType,
        tasks: Optional[List[AdapterTask]] = None
    ) -> Dict[AdapterTask, str]:
        """
        Load adapters for archetype into GPU.
        
        Applies LRU eviction if capacity exceeded.
        
        Args:
            archetype: Archetype type
            tasks: Specific tasks to load (default: all 7)
        
        Returns:
            Mapping of task -> adapter_name loaded
        """
        # Register first (idempotent)
        all_adapters = await self.register_archetype_adapters(archetype)
        
        # Determine which to load
        tasks_to_load = tasks or list(AdapterTask)
        loaded = {}
        
        for task in tasks_to_load:
            adapter_name = all_adapters[task]
            status = self._adapter_status[adapter_name]
            
            # Skip if already loaded
            if status.loaded:
                status.mark_used()
                loaded[task] = adapter_name
                continue
            
            # Ensure capacity for new adapter
            await self._ensure_capacity_for_one()
            
            # Load adapter
            async with self._get_adapter_lock(adapter_name):
                try:
                    import time
                    start = time.time()
                    
                    await self.lora_manager.load_adapter(adapter_name)
                    
                    latency = (time.time() - start) * 1000
                    status.mark_loaded(latency)
                    
                    async with self._lock:
                        self._loaded_adapters.add(adapter_name)
                        self._total_loads += 1
                    
                    logger.info(f"✅ Loaded adapter: {adapter_name} ({latency:.1f}ms)")
                    loaded[task] = adapter_name
                
                except Exception as e:
                    error_msg = f"Failed to load {adapter_name}: {e}"
                    status.mark_error(error_msg)
                    logger.error(error_msg)
        
        logger.info(f"Loaded {len(loaded)}/{len(tasks_to_load)} adapters for {archetype.value}")
        return loaded
    
    async def _ensure_capacity_for_one(self) -> None:
        """
        Ensure capacity for one more adapter.
        
        Evicts LRU adapter if at max capacity.
        """
        async with self._lock:
            if len(self._loaded_adapters) >= self.max_loaded_adapters:
                await self._evict_lru()
    
    async def _evict_lru(self) -> None:
        """
        Evict least recently used adapter.
        
        Must be called with self._lock held.
        """
        if not self._loaded_adapters:
            return
        
        # Find LRU adapter
        lru_adapter = None
        lru_time = None
        
        for adapter_name in self._loaded_adapters:
            status = self._adapter_status.get(adapter_name)
            if not status or not status.loaded:
                continue
            
            last_used = status.last_used
            if lru_time is None or (last_used and last_used < lru_time):
                lru_time = last_used
                lru_adapter = adapter_name
        
        if lru_adapter:
            logger.info(f"Evicting LRU adapter: {lru_adapter}")
            
            # Unload (without lock to avoid deadlock)
            self._lock.release()
            try:
                await self._unload_adapter(lru_adapter)
                self._total_evictions += 1
            finally:
                await self._lock.acquire()
    
    async def _unload_adapter(self, adapter_name: str) -> None:
        """Unload specific adapter."""
        status = self._adapter_status.get(adapter_name)
        if not status:
            return
        
        async with self._get_adapter_lock(adapter_name):
            if not status.loaded:
                return
            
            try:
                import time
                start = time.time()
                
                await self.lora_manager.unload_adapter(adapter_name)
                
                latency = (time.time() - start) * 1000
                status.mark_unloaded(latency)
                
                async with self._lock:
                    self._loaded_adapters.discard(adapter_name)
                    self._total_unloads += 1
                
                logger.info(f"Unloaded adapter: {adapter_name} ({latency:.1f}ms)")
            
            except Exception as e:
                error_msg = f"Failed to unload {adapter_name}: {e}"
                status.mark_error(error_msg)
                logger.error(error_msg)
    
    async def ensure_adapter_loaded(
        self,
        archetype: ArchetypeType,
        task: AdapterTask
    ) -> str:
        """
        Ensure adapter is loaded, loading if necessary.
        
        Returns:
            Adapter name
        """
        adapter_name = self._adapter_name(archetype, task)
        
        # Check if already loaded
        status = self._adapter_status.get(adapter_name)
        if status and status.loaded:
            status.mark_used()
            return adapter_name
        
        # Load the adapter
        await self.load_archetype(archetype, tasks=[task])
        
        return adapter_name
    
    async def get_adapter_name(
        self,
        archetype: ArchetypeType,
        task: AdapterTask
    ) -> str:
        """Get adapter name and mark as used."""
        adapter_name = self._adapter_name(archetype, task)
        
        status = self._adapter_status.get(adapter_name)
        if status:
            status.mark_used()
        
        return adapter_name
    
    async def get_loaded_adapters(self) -> List[str]:
        """Get list of currently loaded adapters."""
        async with self._lock:
            return sorted(list(self._loaded_adapters))
    
    async def get_adapter_stats(self) -> Dict[str, Any]:
        """Get comprehensive adapter statistics."""
        async with self._lock:
            loaded_count = len(self._loaded_adapters)
            
            by_archetype = {}
            for status in self._adapter_status.values():
                arch = status.archetype.value
                if arch not in by_archetype:
                    by_archetype[arch] = {
                        'total': 0,
                        'loaded': 0,
                        'registered': 0,
                        'total_usage': 0,
                        'errors': 0
                    }
                
                by_archetype[arch]['total'] += 1
                if status.loaded:
                    by_archetype[arch]['loaded'] += 1
                if status.registered:
                    by_archetype[arch]['registered'] += 1
                by_archetype[arch]['total_usage'] += status.usage_count
                by_archetype[arch]['errors'] += status.error_count
            
            return {
                'total_registered': len(self._adapter_status),
                'total_loaded': loaded_count,
                'max_loaded': self.max_loaded_adapters,
                'available_slots': self.max_loaded_adapters - loaded_count,
                'total_loads': self._total_loads,
                'total_unloads': self._total_unloads,
                'total_evictions': self._total_evictions,
                'by_archetype': by_archetype
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check coordinator health."""
        stats = await self.get_adapter_stats()
        
        # Check LoRA manager health if available
        lora_health = {}
        try:
            if hasattr(self.lora_manager, 'get_memory_usage'):
                lora_health = await self.lora_manager.get_memory_usage()
        except Exception as e:
            logger.warning(f"LoRA manager health check failed: {e}")
        
        # Determine status
        status = "healthy"
        issues = []
        
        # Check for high error rates
        for arch, data in stats['by_archetype'].items():
            if data['errors'] > 5:
                status = "degraded"
                issues.append(f"High error count for {arch}: {data['errors']}")
        
        # Check capacity
        if stats['available_slots'] == 0:
            status = "degraded"
            issues.append("At maximum adapter capacity")
        
        return {
            'status': status,
            'issues': issues,
            'coordinator_stats': stats,
            'lora_manager_health': lora_health
        }

