# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Cognitive Layer - Async AI inference for strategic decisions.

Implements REQ-PERF-003: Async AI Architecture (Cognitive Layer).

Runs on separate thread pool, never blocks game loop.
Updates Behavioral Proxy strategy based on game state analysis.
Operates at 0.2-2 Hz (much slower than frame rate).

REVIEWED BY: Claude 4.5 Sonnet (2025-01-29)
PAIR CODING: Complete
"""

import asyncio
import time
import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from collections import deque
import threading

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


_logger = logging.getLogger(__name__)


@dataclass
class CognitiveAnalysis:
    """Result of cognitive layer analysis."""
    strategy: ProxyStrategy
    priority: float
    reasoning: str
    target: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # Reviewer feedback: explicit Optional
    confidence: float = 0.5
    
    def __post_init__(self):
        """Initialize context if None (reviewer feedback: mutable default fix)."""
        if self.context is None:
            self.context = {}


class CognitiveLayer:
    """
    Async cognitive layer for strategic NPC decisions.
    
    Runs on separate thread pool, analyzes game state, and updates
    Behavioral Proxy strategy directives.
    """
    
    def __init__(
        self,
        proxy_manager: ProxyManager,
        llm_client: Optional[LLMClient] = None,
        update_rate_hz: float = 0.5,  # 0.5 Hz = every 2 seconds
        max_workers: Optional[int] = None  # Reviewer feedback: configurable pool size
    ):
        self.proxy_manager = proxy_manager
        self.llm_client = llm_client
        self.update_rate_hz = update_rate_hz
        self.update_interval = 1.0 / update_rate_hz
        
        # Default to CPU count or 4, whichever is smaller (reviewer feedback)
        if max_workers is None:
            max_workers = min(os.cpu_count() or 4, 4)
        
        # Thread pool for async inference
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="cognitive"
        )
        self._running = False
        self._lock = threading.Lock()
        
        # Async loop management (reviewer feedback: lifecycle management)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_task: Optional[asyncio.Task] = None
        self._loop_thread: Optional[threading.Thread] = None
        
        # Queue of NPCs awaiting cognitive analysis (reviewer feedback: bounded queue)
        self.analysis_queue: deque = deque(maxlen=1000)  # Limit queue size
        self._queue_lock = threading.Lock()
        
        # Cache for analysis results (avoid redundant analysis) - thread-safe (reviewer feedback)
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()  # Reentrant lock
        self._cache_ttl = 5.0  # 5 seconds cache TTL
        
    def start(self):
        """Start cognitive layer processing (reviewer feedback: fix race condition)."""
        with self._lock:
            if self._running:
                return
            self._running = True
            # Start async loop in background thread (keep lock until thread starts)
            self._loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(
                target=self._run_async_loop,
                args=(self._loop,),
                daemon=True,
                name="cognitive-main"
            )
            self._loop_thread.start()
            _logger.info(f"Cognitive layer started at {self.update_rate_hz} Hz")
    
    def _run_async_loop(self, loop):
        """Run async loop in separate thread (reviewer feedback: graceful shutdown)."""
        asyncio.set_event_loop(loop)
        try:
            self._loop_task = loop.create_task(self._cognitive_loop())
            loop.run_until_complete(self._loop_task)
        except asyncio.CancelledError:
            pass  # Expected on shutdown
        except Exception as e:
            _logger.exception("Async loop error")
        finally:
            loop.close()
    
    def stop(self, timeout: float = 10.0):
        """
        Stop cognitive layer processing (reviewer feedback: blocking behavior documented).
        
        Blocks until async loop and thread pool shutdown complete.
        
        Args:
            timeout: Maximum seconds to wait for clean shutdown.
        
        Raises:
            TimeoutError: If shutdown takes longer than timeout.
        """
        with self._lock:
            if not self._running:
                return
            self._running = False
        
        # Cancel async loop (reviewer feedback: graceful shutdown)
        if self._loop and self._loop_task:
            self._loop.call_soon_threadsafe(self._loop_task.cancel)
        
        # Wait for thread to finish
        if self._loop_thread:
            self._loop_thread.join(timeout=timeout)
            if self._loop_thread.is_alive():
                raise TimeoutError(f"Cognitive layer shutdown exceeded {timeout}s timeout")
        
        # Shutdown executor
        # Note: timeout parameter for shutdown() was added in Python 3.9
        # For compatibility, we use wait=True and rely on thread join timeout above
        self.executor.shutdown(wait=True)
        _logger.info("Cognitive layer stopped")
    
    def request_analysis(self, npc_id: UUID, priority: int = 0) -> bool:
        """
        Request cognitive analysis for NPC (non-blocking, called from game loop).
        
        Args:
            npc_id: NPC to analyze
            priority: Priority level (higher = more urgent)
        
        Returns:
            True if enqueued, False if queue full or already queued.
        """
        return self.queue_analysis(npc_id, priority)
    
    def queue_analysis(self, npc_id: UUID, priority: int = 0) -> bool:
        """Queue NPC for cognitive analysis (reviewer feedback: bounded queue)."""
        with self._queue_lock:
            # Avoid duplicates
            if npc_id in self.analysis_queue:
                return False
            
            # Check queue bounds
            if len(self.analysis_queue) >= 1000:
                _logger.warning(f"Queue full, dropping NPC {npc_id}")
                return False
            
            self.analysis_queue.append(npc_id)
            return True
    
    def get_pending_count(self) -> int:
        """Get number of NPCs awaiting analysis (non-blocking, reviewer feedback)."""
        with self._queue_lock:
            return len(self.analysis_queue)
    
    async def _cognitive_loop(self):
        """Main cognitive processing loop (reviewer feedback: cache cleanup)."""
        last_cleanup = time.time()
        
        while self._running:
            try:
                # Process batch of NPCs
                await self._process_analysis_batch()
                
                # Periodic cache cleanup (reviewer feedback: resource leak fix)
                current_time = time.time()
                if current_time - last_cleanup > 60.0:  # Every minute
                    self._cleanup_cache()
                    last_cleanup = current_time
                
                # Wait before next cycle
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break  # Expected on shutdown
            except Exception as e:
                _logger.exception("Cognitive loop error")
                await asyncio.sleep(1.0)  # Brief backoff on error
    
    async def _process_analysis_batch(self):
        """Process queued NPCs for cognitive analysis (reviewer feedback: batch processing)."""
        # Get batch of NPCs to analyze
        with self._queue_lock:
            if not self.analysis_queue:
                return
            batch = list(self.analysis_queue)[:10]  # Process up to 10 at a time
            # Remove processed NPCs
            for _ in range(min(10, len(self.analysis_queue))):
                self.analysis_queue.popleft()
        
        # Submit to thread pool (CPU-intensive AI inference)
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                self.executor,
                self._analyze_npc_sync,
                npc_id
            )
            for npc_id in batch
        ]
        
        # Wait for all analyses to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Apply results to proxy manager
        for npc_id, result in zip(batch, results):
            if isinstance(result, Exception):
                _logger.error(f"Analysis failed for NPC {npc_id}: {result}")
                continue
            if result:
                self._apply_analysis(npc_id, result)
    
    def _analyze_npc_sync(self, npc_id: UUID) -> Optional[CognitiveAnalysis]:
        """
        Perform CPU-intensive analysis for single NPC (runs in thread pool).
        
        This is the synchronous version called from thread pool.
        """
        # Check cache first (thread-safe, reviewer feedback)
        cache_key = str(npc_id)
        with self._cache_lock:
            if cache_key in self._analysis_cache:
                cached = self._analysis_cache[cache_key]
                if time.time() - cached.get("timestamp", 0) < self._cache_ttl:
                    return cached.get("analysis")
        
        # Get NPC state (TODO: integrate with state manager)
        npc_state = {
            "npc_id": str(npc_id),
            "health": 100,
            "max_health": 100,
            "personality": {"aggression": 0.5, "curiosity": 0.5, "social": 0.5},
            "current_goal": "survive",
        }
        
        game_context = {
            "enemies": [],
            "obstacles": [],
            "interactables": [],
            "social_areas": [],
        }
        
        # Perform AI inference (this is the slow part)
        try:
            if self.llm_client:
                # Use async LLM client (but we're in sync context)
                # For now, use rule-based as fallback
                analysis = self._rule_based_analysis(npc_state, game_context)
            else:
                analysis = self._rule_based_analysis(npc_state, game_context)
            
            # Cache result (thread-safe)
            with self._cache_lock:
                self._analysis_cache[cache_key] = {
                    "analysis": analysis,
                    "timestamp": time.time()
                }
            
            return analysis
        except Exception as e:
            _logger.error(f"Analysis error for NPC {npc_id}: {e}")
            return None
    
    def _apply_analysis(self, npc_id: UUID, analysis: CognitiveAnalysis):
        """Apply cognitive analysis to behavioral proxy (reviewer feedback)."""
        directive = ProxyDirective(
            strategy=analysis.strategy,
            priority=analysis.priority,
            target=analysis.target,
            context=analysis.context or {},
            expires_at=time.time() + 10.0  # Expire after 10 seconds
        )
        self.proxy_manager.send_directive(npc_id, directive)
    
    # Removed old _analyze_npc - replaced with _analyze_npc_sync and _process_analysis_batch
    
    async def _run_cognitive_analysis(
        self,
        npc_id: UUID,
        npc_state: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> CognitiveAnalysis:
        """Run cognitive analysis using LLM (async)."""
        
        # If LLM client available, use it
        if self.llm_client:
            prompt = self._build_analysis_prompt(npc_state, game_context)
            context = {
                "npc_id": str(npc_id),
                "npc_state": npc_state,
                "game_context": game_context,
            }
            
            try:
                # Use interaction layer for NPC decisions
                result = await self.llm_client.generate_text(
                    layer="interaction",
                    prompt=prompt,
                    context=context,
                    max_tokens=200,
                    temperature=0.7
                )
                
                # Parse LLM response
                return self._parse_llm_response(result.get("text", ""), npc_state, game_context)
                
            except Exception as e:
                _logger.error(f"LLM analysis failed for NPC {npc_id}: {e}")
                # Fallback to rule-based analysis
                return self._rule_based_analysis(npc_state, game_context)
        else:
            # Rule-based analysis (fallback)
            return self._rule_based_analysis(npc_state, game_context)
    
    def _build_analysis_prompt(
        self,
        npc_state: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> str:
        """Build prompt for cognitive analysis."""
        personality = npc_state.get("personality", {})
        enemies = game_context.get("enemies", [])
        health = npc_state.get("health", 100)
        max_health = npc_state.get("max_health", 100)
        
        prompt = f"""Analyze the NPC's situation and recommend a strategy.

NPC Personality: {personality}
Health: {health}/{max_health}
Nearby Enemies: {len(enemies)}
Current Goal: {npc_state.get('current_goal', 'none')}

Available Strategies:
- AGGRESSIVE: Attack enemies, pursue objectives aggressively
- DEFENSIVE: Defend, maintain position, cautious approach
- RETREAT: Flee, avoid combat, escape danger
- NEUTRAL: Balanced approach, adapt to situation
- CURIOUS: Explore, investigate, interact with environment
- SOCIAL: Seek social interactions, avoid conflict

Recommend a strategy (one word: AGGRESSIVE, DEFENSIVE, RETREAT, NEUTRAL, CURIOUS, or SOCIAL) and brief reasoning.
"""
        return prompt
    
    def _parse_llm_response(
        self,
        response: str,
        npc_state: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> CognitiveAnalysis:
        """Parse LLM response into CognitiveAnalysis."""
        response_upper = response.upper()
        
        # Extract strategy
        strategy = ProxyStrategy.NEUTRAL
        if "AGGRESSIVE" in response_upper:
            strategy = ProxyStrategy.AGGRESSIVE
        elif "DEFENSIVE" in response_upper:
            strategy = ProxyStrategy.DEFENSIVE
        elif "RETREAT" in response_upper or "FLEE" in response_upper:
            strategy = ProxyStrategy.RETREAT
        elif "CURIOUS" in response_upper or "EXPLORE" in response_upper:
            strategy = ProxyStrategy.CURIOUS
        elif "SOCIAL" in response_upper:
            strategy = ProxyStrategy.SOCIAL
        
        # Calculate priority based on urgency
        priority = 0.5
        enemies = game_context.get("enemies", [])
        health_ratio = npc_state.get("health", 100) / max(npc_state.get("max_health", 100), 1)
        
        if enemies and health_ratio < 0.3:
            priority = 1.0  # High priority if low health and enemies present
        elif enemies:
            priority = 0.8
        elif health_ratio < 0.5:
            priority = 0.7
        
        # Extract target if mentioned
        target = None
        if enemies:
            target = enemies[0].get("id")
        
        return CognitiveAnalysis(
            strategy=strategy,
            priority=priority,
            reasoning=response[:200],  # Truncate reasoning
            target=target,
            context={"llm_analysis": True},
            confidence=0.7
        )
    
    def _rule_based_analysis(
        self,
        npc_state: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> CognitiveAnalysis:
        """Rule-based analysis (fallback when LLM unavailable)."""
        personality = npc_state.get("personality", {})
        enemies = game_context.get("enemies", [])
        health_ratio = npc_state.get("health", 100) / max(npc_state.get("max_health", 100), 1)
        aggression = personality.get("aggression", 0.5)
        
        # Determine strategy
        if health_ratio < 0.3 and enemies:
            strategy = ProxyStrategy.RETREAT
            priority = 1.0
        elif aggression > 0.7 and enemies:
            strategy = ProxyStrategy.AGGRESSIVE
            priority = 0.9
        elif enemies:
            strategy = ProxyStrategy.DEFENSIVE
            priority = 0.8
        elif personality.get("curiosity", 0.5) > 0.7:
            strategy = ProxyStrategy.CURIOUS
            priority = 0.6
        elif personality.get("social", 0.5) > 0.7:
            strategy = ProxyStrategy.SOCIAL
            priority = 0.6
        else:
            strategy = ProxyStrategy.NEUTRAL
            priority = 0.5
        
        target = None
        if enemies:
            target = enemies[0].get("id")
        
        return CognitiveAnalysis(
            strategy=strategy,
            priority=priority,
            reasoning=f"Rule-based: health={health_ratio:.2f}, aggression={aggression:.2f}, enemies={len(enemies)}",
            target=target,
            context={"rule_based": True},
            confidence=0.8
        )
    
    async def _get_npc_state(self, npc_id: UUID) -> Dict[str, Any]:
        """Get NPC state from database/cache."""
        # TODO: Integrate with state manager
        return {
            "npc_id": str(npc_id),
            "health": 100,
            "max_health": 100,
            "personality": {"aggression": 0.5, "curiosity": 0.5, "social": 0.5},
            "current_goal": "survive",
        }
    
    async def _get_game_context(self, npc_id: UUID) -> Dict[str, Any]:
        """Get game context (enemies, obstacles, etc.)."""
        # TODO: Integrate with game state
        return {
            "enemies": [],
            "obstacles": [],
            "interactables": [],
            "social_areas": [],
        }
    
    def _cleanup_cache(self):
        """Remove expired cache entries (reviewer feedback: thread-safe cleanup)."""
        now = time.time()
        with self._cache_lock:
            expired = [
                key for key, value in self._analysis_cache.items()
                if now - value.get("timestamp", 0) > self._cache_ttl
            ]
            for key in expired:
                del self._analysis_cache[key]
            
            if expired:
                _logger.debug(f"Cleaned {len(expired)} expired cache entries")

