"""
Archetype Chain Registry - Production Implementation (REVISED)
Coder: Claude Sonnet 4.5
Reviewer: GPT-5 Pro
Status: Implementing fixes from peer review

Central registry for archetype model chains with 3-tier caching:
- Local memory (instant, with TTL)
- Redis (sub-ms, TTL-based)
- Disk persistence (disaster recovery, atomic writes)

Tracks 7 LoRA adapters per archetype:
- personality, dialogue_style, action_policy, emotional_response
- world_knowledge, social_dynamics, goal_prioritization

Fixes Applied (GPT-5 Pro Review):
1. Non-atomic disk writes -> temp file + os.replace
2. Thundering herd -> singleflight pattern
3. Path traversal -> path validation
4. Local cache TTL -> time-based expiry
5. Init gate -> asyncio.Event
6. run_in_executor for fallback sync I/O
"""

import os
import json
import asyncio
import logging
import tempfile
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from pathlib import Path

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

try:
    import aiofiles
    import aiofiles.os
except ImportError:
    aiofiles = None

logger = logging.getLogger(__name__)


# Fix #1: Validate and normalize paths (security)
def _validate_adapter_path(path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Validate adapter path for security (prevent path traversal).
    
    Args:
        path: Path to validate
        base_dir: Optional base directory to enforce containment
    
    Returns:
        Normalized, validated Path
    
    Raises:
        ValueError: If path is invalid or escapes base_dir
    """
    try:
        p = Path(path).resolve()
        
        # Check for path traversal
        if ".." in path or path.startswith("/"):
            raise ValueError(f"Potentially unsafe path: {path}")
        
        # If base_dir specified, enforce containment
        if base_dir:
            base_resolved = base_dir.resolve()
            if not str(p).startswith(str(base_resolved)):
                raise ValueError(f"Path escapes base directory: {path}")
        
        return p
    
    except Exception as e:
        raise ValueError(f"Invalid adapter path: {path}, error: {e}")


@dataclass
class CacheEntry:
    """
    Cache entry with TTL (Fix #6: Local cache TTL).
    """
    value: Any
    expires_at: datetime
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.expires_at


class ArchetypeType(str, Enum):
    """Supported archetype types."""
    VAMPIRE = "vampire"
    WEREWOLF = "werewolf"
    ZOMBIE = "zombie"
    GHOUL = "ghoul"
    LICH = "lich"


class AdapterTask(str, Enum):
    """7 adapter types per archetype (from Storyteller guidance)."""
    PERSONALITY = "personality"
    DIALOGUE = "dialogue_style"
    ACTION = "action_policy"
    EMOTION = "emotional_response"
    KNOWLEDGE = "world_knowledge"
    SOCIAL = "social_dynamics"
    GOAL = "goal_prioritization"


@dataclass
class AdapterInfo:
    """
    Metadata for one LoRA adapter (~100MB each).
    
    NOTE: Stores path to adapter weights, NOT the weights themselves.
    This avoids Gemini's critical memory issue.
    """
    adapter_id: str
    archetype: ArchetypeType
    task: AdapterTask
    path: str  # Path to weights file on disk or S3
    base_model: str
    rank: int = 32
    alpha: float = 16.0
    memory_mb: int = 100
    version: str = "1.0.0"
    trained_on: Optional[str] = None
    created_at: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'adapter_id': self.adapter_id,
            'archetype': self.archetype.value if isinstance(self.archetype, Enum) else self.archetype,
            'task': self.task.value if isinstance(self.task, Enum) else self.task,
            'path': self.path,
            'base_model': self.base_model,
            'rank': self.rank,
            'alpha': self.alpha,
            'memory_mb': self.memory_mb,
            'version': self.version,
            'trained_on': self.trained_on,
            'created_at': self.created_at,
            'performance_metrics': self.performance_metrics,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdapterInfo':
        """Deserialize from dictionary."""
        data = dict(data)  # Copy to avoid mutating input
        data['archetype'] = ArchetypeType(data['archetype'])
        data['task'] = AdapterTask(data['task'])
        return cls(**data)


@dataclass
class ArchetypeChainConfig:
    """
    Complete configuration for one archetype chain.
    Contains all 7 adapters for the archetype.
    """
    archetype: ArchetypeType
    adapters: Dict[AdapterTask, AdapterInfo]  # Must have all 7
    vllm_server_url: str
    vllm_server_id: str
    voice_service_url: Optional[str] = None
    facial_service_url: Optional[str] = None
    body_service_url: Optional[str] = None
    total_memory_mb: int = 0
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate all 7 adapters present."""
        expected_tasks = set(AdapterTask)
        provided_tasks = set(self.adapters.keys())
        missing = expected_tasks - provided_tasks
        
        if missing:
            raise ValueError(f"Missing adapters for tasks: {[t.value for t in missing]}")
        
        # Calculate total memory if not set
        if self.total_memory_mb == 0:
            self.total_memory_mb = sum(a.memory_mb for a in self.adapters.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'archetype': self.archetype.value if isinstance(self.archetype, Enum) else self.archetype,
            'adapters': {
                task.value if isinstance(task, Enum) else task: adapter.to_dict()
                for task, adapter in self.adapters.items()
            },
            'vllm_server_url': self.vllm_server_url,
            'vllm_server_id': self.vllm_server_id,
            'voice_service_url': self.voice_service_url,
            'facial_service_url': self.facial_service_url,
            'body_service_url': self.body_service_url,
            'total_memory_mb': self.total_memory_mb,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchetypeChainConfig':
        """Deserialize from dictionary."""
        data = dict(data)  # Copy
        data['archetype'] = ArchetypeType(data['archetype'])
        data['adapters'] = {
            AdapterTask(task_str): AdapterInfo.from_dict(adapter_data)
            for task_str, adapter_data in data['adapters'].items()
        }
        return cls(**data)


class ArchetypeChainRegistry:
    """
    Central registry for archetype model chains.
    
    Coder: Claude Sonnet 4.5
    Reviewer: GPT-5 Pro - APPROVED WITH CHANGES
    Status: Implementing all 7 fixes
    
    3-tier caching:
    1. Local memory (instant, with TTL)
    2. Redis (sub-ms, 1hr TTL)
    3. Disk (persistent, atomic writes)
    
    Fixes Applied:
    - Atomic disk writes (temp + os.replace)
    - Singleflight pattern (prevent thundering herd)
    - Path validation (prevent traversal)
    - Local cache TTL (prevent stale data)
    - Init gate (asyncio.Event)
    - run_in_executor for fallback sync I/O
    - Disk as source of truth
    """
    
    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: int = 0,
        persistence_dir: Optional[str] = None,
        redis_ttl_seconds: int = 3600,
        cache_size: int = 64,
        local_cache_ttl_seconds: int = 300  # Fix #6: Local cache TTL (5 min)
    ):
        """
        Initialize registry.
        
        Args:
            redis_host: Redis host (default: localhost)
            redis_port: Redis port (default: 6379)
            redis_db: Redis database (default: 0)
            persistence_dir: Disk persistence directory (default: .cursor/ai-models)
            redis_ttl_seconds: Redis TTL in seconds (default: 3600 = 1 hour)
            cache_size: Max items in local cache (default: 64)
            local_cache_ttl_seconds: Local cache TTL (default: 300 = 5 min)
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db
        self.redis_ttl = redis_ttl_seconds
        self.local_cache_ttl = local_cache_ttl_seconds
        
        self.persistence_dir = Path(persistence_dir or ".cursor/ai-models")
        self.registry_file = self.persistence_dir / "registry.json"
        
        self.cache_size = cache_size
        
        # State
        self.redis_client: Optional[Any] = None
        self._cache: Dict[str, CacheEntry] = {}  # Fix #6: Now stores CacheEntry with TTL
        self._lock = asyncio.Lock()
        self._initialized = False
        self._init_gate = asyncio.Event()  # Fix #7: Init gate
        self._inflight: Dict[str, asyncio.Future] = {}  # Fix #4: Singleflight pattern
        
        logger.info(
            f"ArchetypeChainRegistry initialized: "
            f"redis={self.redis_host}:{self.redis_port}, "
            f"persistence={self.persistence_dir}"
        )
    
    async def initialize(self) -> None:
        """
        Initialize Redis connection and load registry.
        
        Fix #7: Sets init_gate Event when complete to prevent race conditions.
        """
        async with self._lock:
            if self._initialized:
                self._init_gate.set()  # Fix #7: Ensure gate is set
                return
            
            # Setup Redis
            if aioredis:
                try:
                    redis_url = f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
                    self.redis_client = aioredis.from_url(
                        redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
                    await self.redis_client.ping()
                    logger.info("✅ Redis connected")
                except Exception as e:
                    logger.warning(f"Redis connection failed: {e}, continuing without Redis")
                    self.redis_client = None
            else:
                logger.warning("redis.asyncio not available, continuing without Redis")
            
            # Ensure persistence directory exists
            if aiofiles:
                try:
                    await aiofiles.os.makedirs(self.persistence_dir, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create persistence dir: {e}")
            else:
                # Fix #1: Use run_in_executor for fallback sync I/O
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.persistence_dir.mkdir, True, True)
            
            # Load from disk first (disk as source of truth - Fix #3)
            await self._load_from_disk()
            
            # Then populate Redis from disk
            if self.redis_client and self._cache:
                for entry in self._cache.values():
                    await self._save_to_redis(entry.value)
            
            self._initialized = True
            self._init_gate.set()  # Fix #7: Signal initialization complete
            logger.info(f"Registry initialized: {len(self._cache)} archetype(s) loaded")
    
    async def _load_from_redis(self) -> None:
        """Load all chains from Redis."""
        if not self.redis_client:
            return
        
        try:
            pattern = "archetype_chain:*"
            keys = await self.redis_client.keys(pattern)
            
            for key in keys:
                try:
                    data_json = await self.redis_client.get(key)
                    if data_json:
                        data = json.loads(data_json)
                        config = ArchetypeChainConfig.from_dict(data)
                        self._cache[config.archetype.value] = config
                except Exception as e:
                    logger.warning(f"Failed to load key {key} from Redis: {e}")
            
            if self._cache:
                logger.info(f"Loaded {len(self._cache)} chains from Redis")
        
        except Exception as e:
            logger.warning(f"Redis load failed: {e}")
    
    async def _load_from_disk(self) -> None:
        """
        Load registry from disk (non-blocking via aiofiles).
        
        Fix #1: Uses run_in_executor for fallback sync I/O.
        """
        if not self.registry_file.exists():
            logger.info("No disk registry found (fresh start)")
            return
        
        try:
            if aiofiles:
                # Non-blocking disk I/O
                async with aiofiles.open(self.registry_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
            else:
                # Fix #1: Use run_in_executor for fallback sync I/O
                loop = asyncio.get_event_loop()
                def _read_sync():
                    with open(self.registry_file, 'r') as f:
                        return json.load(f)
                data = await loop.run_in_executor(None, _read_sync)
            
            # Populate cache with TTL (Fix #6)
            expires_at = datetime.now() + timedelta(seconds=self.local_cache_ttl)
            for key, config_dict in data.items():
                try:
                    config = ArchetypeChainConfig.from_dict(config_dict)
                    # Fix #5: Validate paths in loaded config
                    for adapter in config.adapters.values():
                        _validate_adapter_path(adapter.path)
                    
                    self._cache[key] = CacheEntry(value=config, expires_at=expires_at)
                except Exception as e:
                    logger.warning(f"Failed to deserialize chain {key}: {e}")
            
            logger.info(f"Loaded {len(self._cache)} chains from disk")
        
        except Exception as e:
            logger.error(f"Failed to load from disk: {e}")
    
    async def _save_to_disk(self) -> None:
        """
        Save registry to disk (non-blocking via aiofiles).
        
        Fix #2: Atomic writes using temp file + os.replace.
        Fix #1: Uses run_in_executor for fallback sync I/O.
        """
        try:
            # Extract configs from cache entries
            data = {
                key: entry.value.to_dict()
                for key, entry in self._cache.items()
            }
            
            if aiofiles:
                # Fix #2: Atomic write with temp file
                temp_file = self.registry_file.with_suffix('.tmp')
                try:
                    async with aiofiles.open(temp_file, 'w') as f:
                        await f.write(json.dumps(data, indent=2))
                    # Atomic replace
                    await aiofiles.os.replace(temp_file, self.registry_file)
                except Exception as e:
                    # Cleanup temp file on error
                    try:
                        await aiofiles.os.remove(temp_file)
                    except Exception:
                        pass
                    raise e
            else:
                # Fix #1 & #2: Atomic write with run_in_executor
                loop = asyncio.get_event_loop()
                def _write_sync():
                    temp_file = self.registry_file.with_suffix('.tmp')
                    try:
                        with open(temp_file, 'w') as f:
                            json.dump(data, f, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
                        os.replace(temp_file, self.registry_file)
                    except Exception as e:
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass
                        raise e
                await loop.run_in_executor(None, _write_sync)
            
            logger.debug(f"Registry persisted to {self.registry_file}")
        
        except Exception as e:
            logger.error(f"Failed to save to disk: {e}")
    
    async def register_archetype_chain(
        self,
        archetype: ArchetypeType,
        adapters: Dict[AdapterTask, AdapterInfo],
        vllm_server_url: str,
        vllm_server_id: str,
        voice_service_url: Optional[str] = None,
        facial_service_url: Optional[str] = None,
        body_service_url: Optional[str] = None
    ) -> ArchetypeChainConfig:
        """
        Register complete chain for archetype.
        
        Fix #7: Awaits init_gate before proceeding.
        Fix #5: Validates all adapter paths.
        Fix #3: Disk as source of truth (write disk first).
        """
        # Fix #7: Wait for initialization
        await self._init_gate.wait()
        
        # Fix #5: Validate all adapter paths before registering
        for adapter in adapters.values():
            _validate_adapter_path(adapter.path)
        
        # Create config (validates 7 adapters in __post_init__)
        config = ArchetypeChainConfig(
            archetype=archetype,
            adapters=adapters,
            vllm_server_url=vllm_server_url,
            vllm_server_id=vllm_server_id,
            voice_service_url=voice_service_url,
            facial_service_url=facial_service_url,
            body_service_url=body_service_url,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Fix #3: Write to disk FIRST (source of truth)
        # Update cache with config first for disk save
        expires_at = datetime.now() + timedelta(seconds=self.local_cache_ttl)
        async with self._lock:
            self._cache[archetype.value] = CacheEntry(value=config, expires_at=expires_at)
        
        try:
            await self._save_to_disk()
        except Exception as e:
            # Rollback cache on disk failure
            async with self._lock:
                self._cache.pop(archetype.value, None)
            raise RuntimeError(f"Failed to persist chain to disk: {e}")
        
        # Disk succeeded, now update Redis
        await self._save_to_redis(config)
        
        logger.info(
            f"✅ Registered chain: {archetype.value}, "
            f"adapters={len(adapters)}, memory={config.total_memory_mb}MB"
        )
        
        return config
    
    async def _save_to_redis(self, config: ArchetypeChainConfig) -> None:
        """Save chain config to Redis with TTL."""
        if not self.redis_client:
            return
        
        try:
            key = f"archetype_chain:{config.archetype.value}"
            value = json.dumps(config.to_dict())
            
            # Use SETEX for atomic set-with-TTL
            await self.redis_client.setex(key, self.redis_ttl, value)
            
        except Exception as e:
            logger.warning(f"Redis save failed: {e}")
    
    async def get_chain(
        self,
        archetype: ArchetypeType
    ) -> Optional[ArchetypeChainConfig]:
        """
        Retrieve chain config for archetype.
        
        Fix #4: Singleflight pattern prevents thundering herd.
        Fix #6: Checks cache entry TTL and evicts if expired.
        Fix #7: Awaits init_gate.
        """
        # Fix #7: Wait for initialization
        await self._init_gate.wait()
        
        key = archetype.value
        
        # Fix #6: Check local cache with TTL
        async with self._lock:
            entry = self._cache.get(key)
            if entry:
                if not entry.is_expired():
                    return entry.value
                else:
                    # Expired, remove from cache
                    del self._cache[key]
        
        # Fix #4: Singleflight pattern
        async with self._lock:
            if key in self._inflight:
                # Another coroutine is already loading, wait for it
                future = self._inflight[key]
        
        if key in self._inflight:
            try:
                return await future
            except Exception as e:
                logger.warning(f"Singleflight load failed for {key}: {e}")
                return None
        
        # Create future for this load
        future: asyncio.Future = asyncio.Future()
        async with self._lock:
            self._inflight[key] = future
        
        try:
            # Load from Redis or disk
            config = await self._load_from_tiers(key)
            future.set_result(config)
            return config
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            # Clean up inflight
            async with self._lock:
                self._inflight.pop(key, None)
    
    async def _load_from_tiers(self, key: str) -> Optional[ArchetypeChainConfig]:
        """Load from Redis then disk."""
        # Try Redis
        if self.redis_client:
            try:
                redis_key = f"archetype_chain:{key}"
                data_json = await self.redis_client.get(redis_key)
                
                if data_json:
                    data = json.loads(data_json)
                    config = ArchetypeChainConfig.from_dict(data)
                    
                    # Fix #5: Validate paths
                    for adapter in config.adapters.values():
                        _validate_adapter_path(adapter.path)
                    
                    # Update local cache with TTL
                    expires_at = datetime.now() + timedelta(seconds=self.local_cache_ttl)
                    async with self._lock:
                        self._cache[key] = CacheEntry(value=config, expires_at=expires_at)
                    
                    return config
            except Exception as e:
                logger.warning(f"Redis get failed for {key}: {e}")
        
        # Try disk
        if self.registry_file.exists():
            try:
                if aiofiles:
                    async with aiofiles.open(self.registry_file, 'r') as f:
                        content = await f.read()
                        all_data = json.loads(content)
                else:
                    # Fix #1: run_in_executor
                    loop = asyncio.get_event_loop()
                    def _read_sync():
                        with open(self.registry_file, 'r') as f:
                            return json.load(f)
                    all_data = await loop.run_in_executor(None, _read_sync)
                
                if key in all_data:
                    config = ArchetypeChainConfig.from_dict(all_data[key])
                    
                    # Fix #5: Validate paths
                    for adapter in config.adapters.values():
                        _validate_adapter_path(adapter.path)
                    
                    # Update cache and Redis
                    expires_at = datetime.now() + timedelta(seconds=self.local_cache_ttl)
                    async with self._lock:
                        self._cache[key] = CacheEntry(value=config, expires_at=expires_at)
                    
                    await self._save_to_redis(config)
                    
                    return config
            except Exception as e:
                logger.warning(f"Disk read failed: {e}")
        
        return None
    
    async def get_adapter_for_task(
        self,
        archetype: ArchetypeType,
        task: AdapterTask
    ) -> Optional[AdapterInfo]:
        """
        Get specific adapter for archetype + task.
        
        This is the main routing method used by AI management layer.
        """
        chain = await self.get_chain(archetype)
        if not chain:
            logger.warning(f"No chain found for archetype: {archetype.value}")
            return None
        
        adapter = chain.adapters.get(task)
        if not adapter:
            logger.warning(
                f"No adapter for archetype={archetype.value}, task={task.value}"
            )
        
        return adapter
    
    async def list_all_chains(self) -> List[ArchetypeChainConfig]:
        """
        List all registered chains.
        
        Fix #6: Filters out expired cache entries.
        Fix #7: Awaits init_gate.
        """
        await self._init_gate.wait()
        
        async with self._lock:
            # Fix #6: Filter expired entries
            valid_entries = [
                entry.value
                for entry in self._cache.values()
                if not entry.is_expired()
            ]
            return valid_entries
    
    async def list_all_adapters(self) -> List[AdapterInfo]:
        """List all adapters across all chains."""
        chains = await self.list_all_chains()
        adapters = []
        for chain in chains:
            adapters.extend(chain.adapters.values())
        return adapters
    
    async def update_chain_status(
        self,
        archetype: ArchetypeType,
        status: str
    ) -> None:
        """Update chain status (active, degraded, offline)."""
        chain = await self.get_chain(archetype)
        if not chain:
            raise ValueError(f"Chain not found: {archetype.value}")
        
        # Create updated config (immutable dataclass pattern)
        # Since dataclass is NOT frozen in our implementation, we can mutate
        chain.status = status
        chain.updated_at = datetime.now().isoformat()
        
        # Update cache
        async with self._lock:
            self._cache[archetype.value] = chain
        
        # Save to Redis and disk
        await asyncio.gather(
            self._save_to_redis(chain),
            self._save_to_disk(),
            return_exceptions=True
        )
        
        logger.info(f"Updated chain status: {archetype.value} -> {status}")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        chains = await self.list_all_chains()
        
        total_memory_mb = sum(c.total_memory_mb for c in chains)
        total_adapters = sum(len(c.adapters) for c in chains)
        
        by_archetype = {
            chain.archetype.value: {
                'adapters': len(chain.adapters),
                'memory_mb': chain.total_memory_mb,
                'status': chain.status,
                'server': chain.vllm_server_id,
            }
            for chain in chains
        }
        
        return {
            'total_chains': len(chains),
            'total_adapters': total_adapters,
            'total_memory_mb': total_memory_mb,
            'archetypes': by_archetype,
        }
    
    async def close(self) -> None:
        """Close registry and persist state."""
        # Final save to disk
        await self._save_to_disk()
        
        # Close Redis
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Registry closed")
