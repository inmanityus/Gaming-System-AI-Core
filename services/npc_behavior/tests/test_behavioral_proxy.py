"""
Tests for Behavioral Proxy architecture.
"""

import pytest
import time
from uuid import uuid4

from services.npc_behavior.behavioral_proxy import (
    BehavioralProxy,
    ProxyManager,
    ProxyDirective,
    ProxyStrategy,
    ProxyActionType,
)


def test_proxy_creation():
    """Test proxy creation."""
    npc_id = uuid4()
    proxy = BehavioralProxy(npc_id)
    
    assert proxy.npc_id == npc_id
    assert proxy.current_strategy == ProxyStrategy.NEUTRAL
    assert len(proxy.strategy_directives) == 0
    assert len(proxy.action_queue) == 0


def test_proxy_update_performance():
    """Test proxy update performance (<0.5ms budget)."""
    npc_id = uuid4()
    proxy = BehavioralProxy(npc_id)
    
    game_state = {
        "enemies": [],
        "obstacles": [],
        "interactables": [],
        "social_areas": [],
    }
    
    # Run multiple updates and measure performance
    start_time = time.time()
    for _ in range(100):
        action = proxy.update(3.33, game_state)
    elapsed_ms = (time.time() - start_time) * 1000 / 100  # Average per update
    
    # Should be well under 0.5ms
    assert elapsed_ms < 0.5, f"Proxy update took {elapsed_ms:.3f}ms, exceeds 0.5ms budget"
    
    stats = proxy.get_performance_stats()
    assert stats["avg_frame_time_ms"] < 0.5


def test_proxy_strategy_directive():
    """Test strategy directive application."""
    npc_id = uuid4()
    proxy = BehavioralProxy(npc_id)
    
    # Send directive
    directive = ProxyDirective(
        strategy=ProxyStrategy.AGGRESSIVE,
        priority=0.9,
        target="enemy_123"
    )
    proxy.receive_directive(directive)
    
    # Update should use new strategy
    game_state = {
        "enemies": [{"id": "enemy_123", "distance": 5.0}],
        "obstacles": [],
        "interactables": [],
        "social_areas": [],
    }
    
    action = proxy.update(3.33, game_state)
    
    assert proxy.current_strategy == ProxyStrategy.AGGRESSIVE
    assert action is not None
    assert action.action_type in [ProxyActionType.ATTACK, ProxyActionType.MOVE]


def test_proxy_dodge_obstacle():
    """Test proxy dodges obstacles."""
    npc_id = uuid4()
    proxy = BehavioralProxy(npc_id)
    
    game_state = {
        "enemies": [],
        "obstacles": [{"id": "wall_1", "distance": 1.5}],  # Close obstacle
        "interactables": [],
        "social_areas": [],
    }
    
    action = proxy.update(3.33, game_state)
    
    assert action is not None
    assert action.action_type == ProxyActionType.DODGE
    assert action.target == "wall_1"


def test_proxy_manager():
    """Test proxy manager."""
    manager = ProxyManager()
    
    npc_id1 = uuid4()
    npc_id2 = uuid4()
    
    # Get proxies
    proxy1 = manager.get_or_create_proxy(npc_id1)
    proxy2 = manager.get_or_create_proxy(npc_id2)
    
    assert proxy1.npc_id == npc_id1
    assert proxy2.npc_id == npc_id2
    
    # Send directive
    directive = ProxyDirective(
        strategy=ProxyStrategy.DEFENSIVE,
        priority=0.8
    )
    manager.send_directive(npc_id1, directive)
    
    # Verify directive received
    assert len(proxy1.strategy_directives) > 0


def test_proxy_retreat_strategy():
    """Test retreat strategy."""
    npc_id = uuid4()
    proxy = BehavioralProxy(npc_id)
    
    # Set retreat strategy
    directive = ProxyDirective(
        strategy=ProxyStrategy.RETREAT,
        priority=1.0
    )
    proxy.receive_directive(directive)
    
    game_state = {
        "enemies": [{"id": "enemy_1", "distance": 15.0}],
        "obstacles": [],
        "interactables": [],
        "social_areas": [],
    }
    
    action = proxy.update(3.33, game_state)
    
    assert proxy.current_strategy == ProxyStrategy.RETREAT
    assert proxy.state_flags["fleeing"] == True
    assert action is not None
    assert action.action_type == ProxyActionType.FLEE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

