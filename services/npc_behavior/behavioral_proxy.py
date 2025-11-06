"""
Behavioral Proxy - Fast, frame-rate-safe NPC behavior system.

Implements REQ-PERF-003: Async AI Architecture (Behavioral Proxy).

The proxy runs every frame (<0.5ms budget) and handles immediate, real-time actions.
The cognitive layer (async) updates strategy but never blocks the game loop.

REVIEWED BY: Claude 4.5 Sonnet (2025-01-29)
PAIR CODING: Complete
"""

import time
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import threading

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Logger for performance warnings
_logger = logging.getLogger(__name__)


class ProxyActionType(Enum):
    """Immediate action types handled by proxy."""
    IDLE = "idle"
    MOVE = "move"
    DODGE = "dodge"
    ATTACK = "attack"
    DEFEND = "defend"
    INTERACT = "interact"
    FLEE = "flee"


class ProxyStrategy(Enum):
    """Strategy directives from cognitive layer."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    RETREAT = "retreat"
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    SOCIAL = "social"


@dataclass
class ProxyDirective:
    """Strategy directive from cognitive layer."""
    strategy: ProxyStrategy
    priority: float  # 0.0 to 1.0
    target: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    expires_at: Optional[float] = None  # None = no expiration


@dataclass
class ProxyAction:
    """Immediate action to execute."""
    action_type: ProxyActionType
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: float = 0.5
    timestamp: float = field(default_factory=time.time)


class BehavioralProxy:
    """
    Fast, frame-rate-safe behavioral proxy.
    
    Runs every frame (<0.5ms budget) and handles immediate actions.
    Receives strategy updates from async cognitive layer.
    """
    
    # Behavioral constants (reviewer feedback: replace magic numbers)
    DODGE_DISTANCE_THRESHOLD = 2.0  # meters
    ATTACK_RANGE = 5.0  # meters
    DEFENSIVE_RANGE = 3.0  # meters
    DEFENSIVE_MAX_RANGE = 10.0  # meters
    RETREAT_RANGE = 20.0  # meters
    INTERACT_RANGE = 2.0  # meters
    
    # Rate limiting (reviewer feedback: security concern)
    MAX_DIRECTIVES_PER_SECOND = 10
    
    # Strategy to state flag mapping (reviewer feedback: optimization)
    _STRATEGY_STATE_MAP = {
        ProxyStrategy.RETREAT: {"fleeing": True, "in_combat": False},
        ProxyStrategy.AGGRESSIVE: {"in_combat": True, "fleeing": False},
        ProxyStrategy.DEFENSIVE: {"in_combat": True, "fleeing": False},
        ProxyStrategy.NEUTRAL: {"fleeing": False, "in_combat": False},
        ProxyStrategy.CURIOUS: {"fleeing": False, "in_combat": False},
        ProxyStrategy.SOCIAL: {"fleeing": False, "in_combat": False},
    }
    
    def __init__(self, npc_id: UUID):
        self.npc_id = npc_id
        self.current_strategy: ProxyStrategy = ProxyStrategy.NEUTRAL
        self.strategy_directives: deque = deque(maxlen=10)  # Keep last 10 directives
        self.action_queue: deque = deque(maxlen=50)  # Keep last 50 actions
        
        # State for immediate actions
        self.current_target: Optional[str] = None
        
        # Thread-safe state flags (reviewer feedback: add thread safety)
        self._state_flags_lock = threading.Lock()
        self._state_flags: Dict[str, bool] = {
            "in_combat": False,
            "fleeing": False,
            "interacting": False,
            "moving": False,
        }
        
        # Thread-safe lock for strategy updates
        self._strategy_lock = threading.Lock()
        
        # Rate limiting for directives (reviewer feedback: security)
        self._directive_timestamps = deque(maxlen=self.MAX_DIRECTIVES_PER_SECOND)
        
        # Performance tracking with rolling window (reviewer feedback: memory leak fix)
        self._perf_lock = threading.Lock()
        self._perf_window_size = 1000  # Track last 1000 frames
        self._frame_times = deque(maxlen=self._perf_window_size)
        self._total_frames = 0  # Lifetime counter
        
    def update(self, frame_time_ms: float, game_state: Dict[str, Any]) -> Optional[ProxyAction]:
        """
        Update proxy and return immediate action.
        
        Args:
            frame_time_ms: Available frame time in milliseconds (must be positive)
            game_state: Current game state (enemies, obstacles, etc.)
        
        Returns:
            Action to execute this frame, or None
        
        Raises:
            ValueError: If frame_time_ms is negative or game_state is None
        """
        # Input validation (reviewer feedback)
        if frame_time_ms < 0:
            raise ValueError(f"frame_time_ms must be positive, got {frame_time_ms}")
        if game_state is None:
            raise ValueError("game_state cannot be None")
        
        start_time = time.time()
        
        # Check for new strategy directives (non-blocking)
        self._update_strategy()
        
        # Process immediate actions based on strategy and game state
        action = self._process_immediate_action(game_state)
        
        # Update performance tracking (thread-safe, reviewer feedback)
        elapsed_ms = (time.time() - start_time) * 1000
        with self._perf_lock:
            self._frame_times.append(elapsed_ms)
            self._total_frames += 1
        
        # Warn if exceeding budget (0.5ms) - use logger (reviewer feedback)
        if elapsed_ms > 0.5 and _logger.isEnabledFor(logging.WARNING):
            _logger.warning(
                "Proxy frame time %.3fms exceeds 0.5ms budget for NPC %s",
                elapsed_ms,
                self.npc_id
            )
        
        return action
    
    def _update_strategy(self):
        """Update current strategy from directives (non-blocking)."""
        directive = None
        
        # Get most recent valid directive (reviewer feedback: fix race condition)
        with self._strategy_lock:
            if not self.strategy_directives:
                return
            
            current_time = time.time()
            
            # Remove expired directives
            while self.strategy_directives:
                candidate = self.strategy_directives[0]
                if candidate.expires_at and current_time > candidate.expires_at:
                    self.strategy_directives.popleft()
                else:
                    directive = self.strategy_directives[0]
                    break
        
        # Process directive outside lock (reviewer feedback: minimize lock time)
        if directive:
            self.current_strategy = directive.strategy
            if directive.target:
                self.current_target = directive.target
            
            # Update state flags using pre-computed mapping (reviewer feedback: optimization)
            state_updates = self._STRATEGY_STATE_MAP.get(directive.strategy, {})
            for flag, value in state_updates.items():
                self._set_state_flag(flag, value)
    
    @property
    def state_flags(self) -> Dict[str, bool]:
        """Thread-safe access to state flags (reviewer feedback)."""
        with self._state_flags_lock:
            return self._state_flags.copy()
    
    def _set_state_flag(self, flag: str, value: bool):
        """Thread-safe state flag update (reviewer feedback)."""
        with self._state_flags_lock:
            self._state_flags[flag] = value
    
    def _validate_entities(self, entities: List[Any]) -> List[Dict[str, Any]]:
        """Validate and filter entity list (reviewer feedback: game state validation)."""
        if not isinstance(entities, list):
            return []
        
        validated = []
        for entity in entities:
            if isinstance(entity, dict) and "distance" in entity and "id" in entity:
                try:
                    # Ensure distance is numeric
                    float(entity["distance"])
                    validated.append(entity)
                except (ValueError, TypeError):
                    continue
        return validated
    
    def _find_nearest(self, entities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find nearest entity by distance (reviewer feedback: cache nearest entities)."""
        if not entities:
            return None
        return min(entities, key=lambda e: e.get("distance", float('inf')))
    
    def _process_immediate_action(self, game_state: Dict[str, Any]) -> Optional[ProxyAction]:
        """Process immediate action based on strategy and game state."""
        
        # Validate and cache nearest entities (reviewer feedback: avoid repeated min() calls)
        validated_obstacles = self._validate_entities(game_state.get("obstacles", []))
        validated_enemies = self._validate_entities(game_state.get("enemies", []))
        validated_interactables = self._validate_entities(game_state.get("interactables", []))
        validated_social_areas = self._validate_entities(game_state.get("social_areas", []))
        
        # Find nearest entities (single pass each)
        nearest_obstacle = self._find_nearest(validated_obstacles)
        nearest_enemy = self._find_nearest(validated_enemies)
        nearest_interactable = self._find_nearest(validated_interactables)
        nearest_social_area = self._find_nearest(validated_social_areas)
        
        # Collect candidate actions (reviewer feedback: priority-based selection)
        candidate_actions: List[ProxyAction] = []
        
        # Check for immediate threats (walls, obstacles) - highest priority
        if nearest_obstacle:
            obstacle_distance = nearest_obstacle.get("distance", float('inf'))
            if obstacle_distance < self.DODGE_DISTANCE_THRESHOLD:
                candidate_actions.append(ProxyAction(
                    action_type=ProxyActionType.DODGE,
                    target=nearest_obstacle.get("id"),
                    priority=1.0,
                    parameters={"direction": "away"}
                ))
        
        # Check for visible enemies
        if nearest_enemy:
            enemy_distance = nearest_enemy.get("distance", float('inf'))
            
            # Strategy-based action selection
            if self.current_strategy == ProxyStrategy.AGGRESSIVE:
                if enemy_distance < self.ATTACK_RANGE:
                    candidate_actions.append(ProxyAction(
                        action_type=ProxyActionType.ATTACK,
                        target=nearest_enemy.get("id"),
                        priority=0.9,
                        parameters={"weapon": "primary"}
                    ))
                else:
                    candidate_actions.append(ProxyAction(
                        action_type=ProxyActionType.MOVE,
                        target=nearest_enemy.get("id"),
                        priority=0.8,
                        parameters={"toward": True}
                    ))
            
            elif self.current_strategy == ProxyStrategy.DEFENSIVE:
                if enemy_distance < self.DEFENSIVE_RANGE:
                    candidate_actions.append(ProxyAction(
                        action_type=ProxyActionType.DEFEND,
                        target=nearest_enemy.get("id"),
                        priority=0.9
                    ))
                elif enemy_distance < self.DEFENSIVE_MAX_RANGE:
                    candidate_actions.append(ProxyAction(
                        action_type=ProxyActionType.MOVE,
                        target=nearest_enemy.get("id"),
                        priority=0.7,
                        parameters={"away": True}
                    ))
            
            elif self.current_strategy == ProxyStrategy.RETREAT:
                if enemy_distance < self.RETREAT_RANGE:
                    candidate_actions.append(ProxyAction(
                        action_type=ProxyActionType.FLEE,
                        target=nearest_enemy.get("id"),
                        priority=1.0,
                        parameters={"direction": "away", "speed": "max"}
                    ))
        
        # Check for interactable objects
        if nearest_interactable and self.current_strategy == ProxyStrategy.CURIOUS:
            interactable_distance = nearest_interactable.get("distance", float('inf'))
            if interactable_distance < self.INTERACT_RANGE:
                candidate_actions.append(ProxyAction(
                    action_type=ProxyActionType.INTERACT,
                    target=nearest_interactable.get("id"),
                    priority=0.6
                ))
        
        # Check for social areas
        if nearest_social_area and self.current_strategy == ProxyStrategy.SOCIAL:
            candidate_actions.append(ProxyAction(
                action_type=ProxyActionType.MOVE,
                target=nearest_social_area.get("id"),
                priority=0.5
            ))
        
        # Return highest priority action (reviewer feedback: priority-based selection)
        if candidate_actions:
            return max(candidate_actions, key=lambda a: a.priority)
        
        # Default: idle
        return ProxyAction(
            action_type=ProxyActionType.IDLE,
            priority=0.1
        )
    
    def receive_directive(self, directive: ProxyDirective):
        """
        Receive strategy directive from cognitive layer (thread-safe).
        
        This is called by the async cognitive layer to update strategy.
        
        Args:
            directive: Strategy directive to apply
        
        Raises:
            TypeError: If directive is not a ProxyDirective
        """
        # Input validation (reviewer feedback)
        if not isinstance(directive, ProxyDirective):
            raise TypeError(f"Expected ProxyDirective, got {type(directive)}")
        
        # Rate limiting (reviewer feedback: security concern)
        current_time = time.time()
        
        with self._strategy_lock:
            # Rate limiting check
            self._directive_timestamps.append(current_time)
            
            if len(self._directive_timestamps) >= self.MAX_DIRECTIVES_PER_SECOND:
                time_span = current_time - self._directive_timestamps[0]
                if time_span < 1.0:
                    # Too many directives in short time
                    if _logger.isEnabledFor(logging.WARNING):
                        _logger.warning(
                            "Rate limit exceeded for NPC %s: %d directives in %.2fs",
                            self.npc_id,
                            len(self._directive_timestamps),
                            time_span
                        )
                    return  # Drop directive
            
            self.strategy_directives.append(directive)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics (thread-safe, reviewer feedback)."""
        with self._perf_lock:
            if not self._frame_times:
                return {
                    "npc_id": str(self.npc_id),
                    "frame_count": 0,
                    "total_frames": 0,
                    "avg_frame_time_ms": 0.0,
                    "max_frame_time_ms": 0.0,
                    "current_strategy": self.current_strategy.value,
                    "budget_exceeded": False,
                }
            
            return {
                "npc_id": str(self.npc_id),
                "frame_count": len(self._frame_times),
                "total_frames": self._total_frames,
                "avg_frame_time_ms": sum(self._frame_times) / len(self._frame_times),
                "max_frame_time_ms": max(self._frame_times),
                "current_strategy": self.current_strategy.value,
                "budget_exceeded": max(self._frame_times) > 0.5,
            }


class ProxyManager:
    """
    Manages multiple behavioral proxies.
    
    Provides centralized access and performance monitoring.
    """
    
    def __init__(self):
        self.proxies: Dict[UUID, BehavioralProxy] = {}
        self._lock = threading.Lock()
    
    def get_or_create_proxy(self, npc_id: UUID) -> BehavioralProxy:
        """Get or create proxy for NPC."""
        with self._lock:
            if npc_id not in self.proxies:
                self.proxies[npc_id] = BehavioralProxy(npc_id)
            return self.proxies[npc_id]
    
    def update_proxy(self, npc_id: UUID, frame_time_ms: float, game_state: Dict[str, Any]) -> Optional[ProxyAction]:
        """Update proxy and return action (optimized lock usage, reviewer feedback)."""
        # Separate read path (no lock needed for update)
        if npc_id in self.proxies:
            return self.proxies[npc_id].update(frame_time_ms, game_state)
        
        # Write path (only lock for creation)
        with self._lock:
            if npc_id not in self.proxies:
                self.proxies[npc_id] = BehavioralProxy(npc_id)
            proxy = self.proxies[npc_id]
        
        return proxy.update(frame_time_ms, game_state)
    
    def send_directive(self, npc_id: UUID, directive: ProxyDirective):
        """Send directive to proxy."""
        with self._lock:
            if npc_id in self.proxies:
                self.proxies[npc_id].receive_directive(directive)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get aggregate performance statistics."""
        with self._lock:
            stats = {
                "total_proxies": len(self.proxies),
                "proxies": [],
                "aggregate": {
                    "total_frames": 0,
                    "total_time_ms": 0.0,
                    "max_frame_time_ms": 0.0,
                    "budget_violations": 0,
                }
            }
            
            for proxy in self.proxies.values():
                proxy_stats = proxy.get_performance_stats()
                stats["proxies"].append(proxy_stats)
                
                stats["aggregate"]["total_frames"] += proxy_stats["frame_count"]
                stats["aggregate"]["total_time_ms"] += proxy_stats["avg_frame_time_ms"] * proxy_stats["frame_count"]
                if proxy_stats["max_frame_time_ms"] > stats["aggregate"]["max_frame_time_ms"]:
                    stats["aggregate"]["max_frame_time_ms"] = proxy_stats["max_frame_time_ms"]
                if proxy_stats["budget_exceeded"]:
                    stats["aggregate"]["budget_violations"] += 1
            
            if stats["aggregate"]["total_frames"] > 0:
                stats["aggregate"]["avg_frame_time_ms"] = (
                    stats["aggregate"]["total_time_ms"] / stats["aggregate"]["total_frames"]
                )
            else:
                stats["aggregate"]["avg_frame_time_ms"] = 0.0
            
            return stats
    
    def remove_proxy(self, npc_id: UUID) -> bool:
        """
        Remove proxy for NPC (reviewer feedback: cleanup method).
        
        Args:
            npc_id: NPC to remove
        
        Returns:
            True if proxy was removed, False if not found
        """
        with self._lock:
            if npc_id in self.proxies:
                del self.proxies[npc_id]
                return True
            return False
    
    def clear_inactive_proxies(self, inactive_threshold_seconds: float = 60.0):
        """
        Remove proxies that haven't been updated recently (reviewer feedback: cleanup).
        
        Args:
            inactive_threshold_seconds: Time threshold for inactivity
        """
        current_time = time.time()
        to_remove = []
        
        with self._lock:
            for npc_id, proxy in self.proxies.items():
                # Check if proxy has recent activity
                with proxy._perf_lock:
                    if proxy._frame_times:
                        # Last frame time is most recent
                        last_update_ms = proxy._frame_times[-1]
                        last_update_seconds = current_time - (last_update_ms / 1000.0)
                        if last_update_seconds > inactive_threshold_seconds:
                            to_remove.append(npc_id)
                    elif proxy._total_frames == 0:
                        # Never updated
                        to_remove.append(npc_id)
            
            for npc_id in to_remove:
                del self.proxies[npc_id]

