"""
Economic Simulator - Economic model with market dynamics.
Simulates supply/demand, price fluctuations, and economic events.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncpg
import redis.asyncio as aioredis


class EconomicSimulator:
    """
    Simulates economic dynamics in the world.
    Handles supply/demand, price fluctuations, and economic events.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._market_state: Dict[str, Any] = {}
        self._price_history: Dict[str, List[float]] = {}
        self._base_prices: Dict[str, float] = {
            "body_part": 100.0,
            "augmentation": 500.0,
            "weapon": 200.0,
            "medicine": 50.0,
            "information": 150.0,
            "service": 75.0
        }
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = get_state_manager_client()
        return self.redis
    
    async def simulate_economic_cycle(self, world_state_id: str) -> Dict[str, Any]:
        """
        Simulate one economic cycle.
        
        Args:
            world_state_id: World state UUID
        
        Returns:
            Economic simulation result
        """
        # Load economic state
        economic_state = await self._load_economic_state(world_state_id)
        
        # Calculate supply and demand
        supply_demand = await self._calculate_supply_demand(world_state_id)
        
        # Update prices based on supply/demand
        price_changes = await self._update_prices(economic_state, supply_demand)
        
        # Generate economic events
        events = await self._generate_economic_events(world_state_id, economic_state, supply_demand)
        
        # Update market state
        await self._update_market_state(world_state_id, price_changes, events)
        
        return {
            "world_state_id": world_state_id,
            "price_changes": price_changes,
            "events": events,
            "timestamp": time.time()
        }
    
    async def _load_economic_state(self, world_state_id: str) -> Dict[str, Any]:
        """Load economic state from database."""
        postgres = await self._get_postgres()
        
        world_state = await postgres.fetch(
            "SELECT economic_state FROM world_states WHERE id = $1",
            world_state_id
        )
        
        if not world_state:
            raise ValueError(f"World state {world_state_id} not found")
        
        economic_state = world_state.get("economic_state")
        if isinstance(economic_state, str):
            try:
                economic_state = json.loads(economic_state)
            except json.JSONDecodeError:
                economic_state = {}
        
        if not isinstance(economic_state, dict):
            economic_state = {}
        
        # Initialize if missing
        if not economic_state:
            economic_state = {
                "prices": self._base_prices.copy(),
                "market_volatility": 0.1,
                "economic_health": 0.5,
                "last_update": time.time()
            }
        
        return economic_state
    
    async def _calculate_supply_demand(self, world_state_id: str) -> Dict[str, Any]:
        """Calculate supply and demand for different goods."""
        postgres = await self._get_postgres()
        
        # Get transaction history (last 24 game days)
        # Note: transactions table doesn't have world_state_id, use player_id filter if needed
        # For simulation, we'll use all recent transactions as proxy for economic activity
        transactions = await postgres.fetch_all(
            """
            SELECT transaction_type, meta_data, amount
            FROM transactions
            WHERE created_at > NOW() - INTERVAL '24 days'
            ORDER BY created_at DESC
            LIMIT 1000
            """,
        )
        
        # Calculate supply (items sold)
        supply = {}
        demand = {}
        
        for transaction in transactions:
            # Extract item_type from meta_data or use default
            meta = transaction.get("meta_data", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            
            item_type = meta.get("item_type", "unknown") if isinstance(meta, dict) else "unknown"
            quantity = meta.get("quantity", 1) if isinstance(meta, dict) else 1
            
            trans_type = transaction.get("transaction_type", "")
            if trans_type == "sell":
                supply[item_type] = supply.get(item_type, 0) + quantity
            elif trans_type == "buy":
                demand[item_type] = demand.get(item_type, 0) + quantity
        
        # Calculate supply/demand ratio
        supply_demand_ratio = {}
        for item_type in set(list(supply.keys()) + list(demand.keys())):
            supply_val = supply.get(item_type, 0)
            demand_val = demand.get(item_type, 0)
            
            if demand_val > 0:
                ratio = supply_val / demand_val
            else:
                ratio = 2.0 if supply_val > 0 else 1.0  # Excess supply or balanced
            
            supply_demand_ratio[item_type] = {
                "supply": supply_val,
                "demand": demand_val,
                "ratio": ratio
            }
        
        return supply_demand_ratio
    
    async def _update_prices(self, economic_state: Dict[str, Any], supply_demand: Dict[str, Any]) -> Dict[str, float]:
        """Update prices based on supply/demand."""
        current_prices = economic_state.get("prices", self._base_prices.copy())
        volatility = economic_state.get("market_volatility", 0.1)
        price_changes = {}
        
        for item_type, s_d in supply_demand.items():
            if item_type not in current_prices:
                current_prices[item_type] = self._base_prices.get(item_type, 100.0)
            
            current_price = current_prices[item_type]
            ratio = s_d["ratio"]
            
            # Price adjustment based on supply/demand
            # ratio < 1.0 = high demand, increase price
            # ratio > 1.0 = high supply, decrease price
            if ratio < 0.5:
                # Very high demand
                price_multiplier = 1.0 + (volatility * 2.0)
            elif ratio < 1.0:
                # Moderate demand
                price_multiplier = 1.0 + volatility
            elif ratio > 2.0:
                # Very high supply
                price_multiplier = 1.0 - (volatility * 2.0)
            elif ratio > 1.0:
                # Moderate supply
                price_multiplier = 1.0 - volatility
            else:
                # Balanced
                price_multiplier = 1.0
            
            new_price = max(current_price * price_multiplier, current_price * 0.5)  # Min 50% of base
            new_price = min(new_price, current_price * 2.0)  # Max 200% of current
            
            price_changes[item_type] = new_price - current_price
            current_prices[item_type] = new_price
            
            # Track price history
            if item_type not in self._price_history:
                self._price_history[item_type] = []
            self._price_history[item_type].append(new_price)
            
            # Keep only last 100 prices
            if len(self._price_history[item_type]) > 100:
                self._price_history[item_type] = self._price_history[item_type][-100:]
        
        return price_changes
    
    async def _generate_economic_events(self, world_state_id: str, economic_state: Dict[str, Any], supply_demand: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate economic events based on market conditions."""
        events = []
        
        # Check for price spikes/crashes
        for item_type, prices in self._price_history.items():
            if len(prices) >= 5:
                recent_avg = sum(prices[-5:]) / 5
                older_avg = sum(prices[-10:-5]) / 5 if len(prices) >= 10 else recent_avg
                
                if older_avg > 0:
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100
                    
                    if abs(change_percent) > 20:  # 20% change threshold
                        event_type = "price_spike" if change_percent > 0 else "price_crash"
                        events.append({
                            "type": event_type,
                            "item_type": item_type,
                            "change_percent": change_percent,
                            "current_price": prices[-1],
                            "description": f"{item_type} prices {'spiked' if change_percent > 0 else 'crashed'} by {abs(change_percent):.1f}%"
                        })
        
        # Check for supply/demand imbalances
        for item_type, s_d in supply_demand.items():
            ratio = s_d["ratio"]
            
            if ratio < 0.3:
                events.append({
                    "type": "shortage",
                    "item_type": item_type,
                    "severity": "critical",
                    "description": f"Critical shortage of {item_type} - demand far exceeds supply"
                })
            elif ratio > 3.0:
                events.append({
                    "type": "surplus",
                    "item_type": item_type,
                    "severity": "major",
                    "description": f"Major surplus of {item_type} - supply far exceeds demand"
                })
        
        return events
    
    async def _update_market_state(self, world_state_id: str, price_changes: Dict[str, float], events: List[Dict[str, Any]]):
        """Update market state in database."""
        postgres = await self._get_postgres()
        
        # Load current economic state
        economic_state = await self._load_economic_state(world_state_id)
        
        # Update prices
        current_prices = economic_state.get("prices", self._base_prices.copy())
        for item_type, change in price_changes.items():
            if item_type in current_prices:
                current_prices[item_type] += change
            else:
                current_prices[item_type] = self._base_prices.get(item_type, 100.0) + change
        
        economic_state["prices"] = current_prices
        economic_state["last_update"] = time.time()
        
        # Calculate economic health based on volatility and stability
        total_price_change = sum(abs(change) for change in price_changes.values())
        avg_price = sum(current_prices.values()) / len(current_prices) if current_prices else 0
        
        if avg_price > 0:
            volatility_percent = (total_price_change / avg_price) * 100
            economic_state["market_volatility"] = min(volatility_percent / 100.0, 1.0)
            
            # Economic health: lower volatility = better health
            economic_state["economic_health"] = max(0.0, 1.0 - economic_state["market_volatility"])
        
        # Store events in economic state
        if "recent_events" not in economic_state:
            economic_state["recent_events"] = []
        
        economic_state["recent_events"].extend(events)
        
        # Keep only last 50 events
        if len(economic_state["recent_events"]) > 50:
            economic_state["recent_events"] = economic_state["recent_events"][-50:]
        
        # Update world state economic_state column directly
        await postgres.execute(
            """
            UPDATE world_states
            SET economic_state = $1::jsonb, updated_at = NOW()
            WHERE id = $2
            """,
            json.dumps(economic_state),
            world_state_id
        )
    
    async def get_current_prices(self, world_state_id: str) -> Dict[str, float]:
        """Get current market prices."""
        economic_state = await self._load_economic_state(world_state_id)
        return economic_state.get("prices", self._base_prices.copy())
    
    async def get_price_history(self, item_type: str, days: int = 30) -> List[float]:
        """Get price history for an item type."""
        if item_type not in self._price_history:
            return []
        
        prices = self._price_history[item_type]
        if days > 0:
            return prices[-days:]
        
        return prices

