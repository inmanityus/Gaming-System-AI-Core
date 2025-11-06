"""
LoRA Adapter System - AI-003
Hot-swappable LoRA adapter management for vLLM.
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from aiohttp import ClientSession, ClientTimeout


@dataclass
class LoRAAdapter:
    """LoRA adapter metadata."""
    name: str
    base_model: str
    path: str
    rank: int = 64
    alpha: float = 16.0
    loaded: bool = False
    loaded_at: Optional[datetime] = None
    memory_mb: int = 0


class LoRAManager:
    """
    Manages LoRA adapter loading, unloading, and hot-swapping.
    Integrates with vLLM server for runtime adapter management.
    """
    
    def __init__(self, vllm_base_url: Optional[str] = None):
        self.vllm_base_url = vllm_base_url or os.getenv("VLLM_BASE_URL", "http://localhost:8000")
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=30.0)
        self._adapters: Dict[str, LoRAAdapter] = {}
        self._max_adapters = int(os.getenv("MAX_LORA_ADAPTERS", "20"))
        
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def register_adapter(
        self,
        name: str,
        base_model: str,
        path: str,
        rank: int = 64,
        alpha: float = 16.0
    ) -> bool:
        """
        Register a LoRA adapter (does not load it).
        
        Args:
            name: Adapter name
            base_model: Base model name
            path: Path to adapter files
            rank: LoRA rank
            alpha: LoRA alpha
        
        Returns:
            True if registered successfully
        """
        adapter = LoRAAdapter(
            name=name,
            base_model=base_model,
            path=path,
            rank=rank,
            alpha=alpha
        )
        self._adapters[name] = adapter
        return True
    
    async def load_adapter(self, name: str) -> bool:
        """
        Load a LoRA adapter into vLLM server.
        
        Args:
            name: Adapter name
        
        Returns:
            True if loaded successfully
        """
        if name not in self._adapters:
            raise ValueError(f"Adapter {name} not registered")
        
        adapter = self._adapters[name]
        
        if adapter.loaded:
            return True
        
        # Check if we're at max adapters
        loaded_count = sum(1 for a in self._adapters.values() if a.loaded)
        if loaded_count >= self._max_adapters:
            raise RuntimeError(f"Maximum adapters ({self._max_adapters}) already loaded")
        
        try:
            session = await self._get_session()
            
            # vLLM LoRA loading endpoint
            payload = {
                "name": name,
                "path": adapter.path,
                "rank": adapter.rank,
                "alpha": adapter.alpha,
            }
            
            async with session.post(
                f"{self.vllm_base_url}/v1/loras",
                json=payload
            ) as response:
                if response.status == 200:
                    adapter.loaded = True
                    adapter.loaded_at = datetime.now()
                    result = await response.json()
                    adapter.memory_mb = result.get("memory_mb", 0)
                    return True
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to load adapter: {error_text}")
        except Exception as e:
            raise RuntimeError(f"Error loading adapter {name}: {e}")
    
    async def unload_adapter(self, name: str) -> bool:
        """
        Unload a LoRA adapter from vLLM server.
        
        Args:
            name: Adapter name
        
        Returns:
            True if unloaded successfully
        """
        if name not in self._adapters:
            raise ValueError(f"Adapter {name} not registered")
        
        adapter = self._adapters[name]
        
        if not adapter.loaded:
            return True
        
        try:
            session = await self._get_session()
            
            async with session.delete(
                f"{self.vllm_base_url}/v1/loras/{name}"
            ) as response:
                if response.status == 200:
                    adapter.loaded = False
                    adapter.loaded_at = None
                    adapter.memory_mb = 0
                    return True
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to unload adapter: {error_text}")
        except Exception as e:
            raise RuntimeError(f"Error unloading adapter {name}: {e}")
    
    async def hot_swap_adapter(self, old_name: str, new_name: str) -> bool:
        """
        Hot-swap adapters (unload old, load new) without downtime.
        
        Args:
            old_name: Adapter to unload
            new_name: Adapter to load
        
        Returns:
            True if swap successful
        """
        try:
            # Load new adapter first (if not already loaded)
            if new_name in self._adapters and not self._adapters[new_name].loaded:
                await self.load_adapter(new_name)
            
            # Unload old adapter
            if old_name in self._adapters and self._adapters[old_name].loaded:
                await self.unload_adapter(old_name)
            
            return True
        except Exception as e:
            raise RuntimeError(f"Error hot-swapping adapters: {e}")
    
    async def list_adapters(self, loaded_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all registered adapters.
        
        Args:
            loaded_only: If True, only return loaded adapters
        
        Returns:
            List of adapter metadata
        """
        adapters = []
        for adapter in self._adapters.values():
            if loaded_only and not adapter.loaded:
                continue
            
            adapters.append({
                "name": adapter.name,
                "base_model": adapter.base_model,
                "path": adapter.path,
                "rank": adapter.rank,
                "alpha": adapter.alpha,
                "loaded": adapter.loaded,
                "loaded_at": adapter.loaded_at.isoformat() if adapter.loaded_at else None,
                "memory_mb": adapter.memory_mb,
            })
        
        return adapters
    
    async def get_adapter_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific adapter.
        
        Args:
            name: Adapter name
        
        Returns:
            Adapter status or None if not found
        """
        if name not in self._adapters:
            return None
        
        adapter = self._adapters[name]
        return {
            "name": adapter.name,
            "base_model": adapter.base_model,
            "loaded": adapter.loaded,
            "loaded_at": adapter.loaded_at.isoformat() if adapter.loaded_at else None,
            "memory_mb": adapter.memory_mb,
        }
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get total memory usage of loaded adapters.
        
        Returns:
            Memory usage statistics
        """
        total_memory = sum(
            adapter.memory_mb
            for adapter in self._adapters.values()
            if adapter.loaded
        )
        
        loaded_count = sum(1 for a in self._adapters.values() if a.loaded)
        
        return {
            "total_memory_mb": total_memory,
            "loaded_adapters": loaded_count,
            "max_adapters": self._max_adapters,
            "available_slots": self._max_adapters - loaded_count,
        }

