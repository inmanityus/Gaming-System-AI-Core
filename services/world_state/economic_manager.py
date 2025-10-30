"""
Economic Manager - Economic state and market dynamics.
Manages market simulation, resource economy, and trade routes.
"""

import json
import random
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class EconomicManager:
    """
    Manages economic state and market dynamics.
    Handles market simulation, resource economy, and trade routes.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._market_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Economic parameters
        self.market_volatility = 0.1
        self.inflation_rate = 0.02
        self.resource_availability = 0.8
        
        # Resource types and their base values
        self.resource_types = {
            "energy": {"base_price": 100, "volatility": 0.15, "demand": 0.8},
            "materials": {"base_price": 50, "volatility": 0.12, "demand": 0.9},
            "technology": {"base_price": 200, "volatility": 0.20, "demand": 0.6},
            "food": {"base_price": 30, "volatility": 0.08, "demand": 1.0},
            "medicine": {"base_price": 150, "volatility": 0.10, "demand": 0.7},
            "luxury": {"base_price": 300, "volatility": 0.25, "demand": 0.4},
        }
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = await get_redis_pool()
        return self.redis
    
    async def get_market_state(self) -> Dict[str, Any]:
        """
        Get current market state with caching.
        
        Returns:
            Market state dictionary
        """
        cache_key = "economic:market_state"
        
        # Check cache first
        if cache_key in self._market_cache:
            return self._market_cache[cache_key]
        
        # Check Redis cache
        redis = await self._get_redis()
        cached_state = await redis.hgetall(cache_key)
        
        if cached_state:
            # Parse JSON values
            state = {}
            for k, v in cached_state.items():
                try:
                    state[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    state[k] = v
            self._market_cache[cache_key] = state
            return state
        
        # Get market state from world state
        postgres = await self._get_postgres()
        query = """
            SELECT economic_state
            FROM world_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        result = await postgres.fetch(query)
        
        if result and result["economic_state"]:
            economic_state = json.loads(result["economic_state"]) if isinstance(result["economic_state"], str) else result["economic_state"]
        else:
            economic_state = self._get_default_market_state()
        
        # Ensure economic_state is not empty
        if not economic_state:
            economic_state = self._get_default_market_state()
        
        # Cache the result
        self._market_cache[cache_key] = economic_state
        await self._cache_market_state(cache_key, economic_state)
        
        return economic_state
    
    def _get_default_market_state(self) -> Dict[str, Any]:
        """Get default market state."""
        return {
            "market_stability": 0.7,
            "inflation_rate": 0.02,
            "resource_availability": 0.8,
            "resource_prices": {
                resource: config["base_price"]
                for resource, config in self.resource_types.items()
            },
            "market_trends": {
                resource: "stable"
                for resource in self.resource_types.keys()
            },
            "trade_volume": 1000,
            "economic_events": [],
            "last_updated": time.time(),
        }
    
    async def _cache_market_state(self, cache_key: str, state: Dict[str, Any]):
        """Cache market state in Redis."""
        redis = await self._get_redis()
        
        # Prepare data for Redis hash
        cache_data = {}
        for k, v in state.items():
            if isinstance(v, (dict, list)):
                cache_data[k] = json.dumps(v)
            else:
                cache_data[k] = str(v)
        
        # Store with TTL (only if cache_data is not empty)
        if cache_data:
            await redis.hset(cache_key, mapping=cache_data)
            await redis.expire(cache_key, self._cache_ttl)
    
    async def update_market_state(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update market state with new data.
        
        Args:
            updates: Dictionary of market updates
        
        Returns:
            Updated market state
        """
        current_state = await self.get_market_state()
        
        # Apply updates
        for key, value in updates.items():
            if key in current_state:
                if isinstance(current_state[key], dict) and isinstance(value, dict):
                    current_state[key].update(value)
                else:
                    current_state[key] = value
        
        # Update timestamp
        current_state["last_updated"] = time.time()
        
        # Cache the updated state
        cache_key = "economic:market_state"
        self._market_cache[cache_key] = current_state
        await self._cache_market_state(cache_key, current_state)
        
        return current_state
    
    async def simulate_market_dynamics(self) -> Dict[str, Any]:
        """
        Simulate market dynamics and update prices.
        
        Returns:
            Market simulation results
        """
        current_state = await self.get_market_state()
        resource_prices = current_state.get("resource_prices", {})
        market_trends = current_state.get("market_trends", {})
        
        # Simulate price changes for each resource
        price_changes = {}
        new_trends = {}
        
        for resource, config in self.resource_types.items():
            current_price = resource_prices.get(resource, config["base_price"])
            volatility = config["volatility"]
            demand = config["demand"]
            
            # Calculate price change based on volatility and demand
            random_factor = random.uniform(-1, 1)
            demand_factor = (demand - 0.5) * 2  # Convert 0-1 to -1 to 1
            volatility_factor = volatility * random_factor
            
            price_change_percent = (volatility_factor + demand_factor * 0.1) * 0.1
            new_price = current_price * (1 + price_change_percent)
            
            # Ensure price doesn't go below 10% of base price
            min_price = config["base_price"] * 0.1
            new_price = max(min_price, new_price)
            
            price_changes[resource] = {
                "old_price": current_price,
                "new_price": new_price,
                "change_percent": price_change_percent * 100,
            }
            
            resource_prices[resource] = new_price
            
            # Update trend
            if price_change_percent > 0.05:
                new_trends[resource] = "rising"
            elif price_change_percent < -0.05:
                new_trends[resource] = "falling"
            else:
                new_trends[resource] = "stable"
        
        # Update market state
        await self.update_market_state({
            "resource_prices": resource_prices,
            "market_trends": new_trends,
        })
        
        return {
            "price_changes": price_changes,
            "new_trends": new_trends,
            "simulation_time": time.time(),
        }
    
    async def get_resource_price(self, resource_type: str) -> float:
        """
        Get current price for a resource type.
        
        Args:
            resource_type: Type of resource
        
        Returns:
            Current resource price
        """
        market_state = await self.get_market_state()
        resource_prices = market_state.get("resource_prices", {})
        
        if resource_type in resource_prices:
            return resource_prices[resource_type]
        
        # Return base price if not found
        return self.resource_types.get(resource_type, {}).get("base_price", 0)
    
    async def calculate_trade_value(
        self, 
        resource_type: str, 
        quantity: int, 
        buyer_faction: str = None
    ) -> Dict[str, Any]:
        """
        Calculate trade value for a resource transaction.
        
        Args:
            resource_type: Type of resource
            quantity: Quantity to trade
            buyer_faction: Optional buyer faction for relationship discounts
        
        Returns:
            Trade value calculation
        """
        base_price = await self.get_resource_price(resource_type)
        market_state = await self.get_market_state()
        
        # Apply market stability factor
        stability = market_state.get("market_stability", 0.7)
        stability_factor = 0.8 + (stability * 0.4)  # 0.8 to 1.2 range
        
        # Apply inflation
        inflation = market_state.get("inflation_rate", 0.02)
        inflation_factor = 1 + inflation
        
        # Calculate base value
        base_value = base_price * quantity * stability_factor * inflation_factor
        
        # Apply faction relationship discount if buyer specified
        relationship_discount = 0.0
        if buyer_faction:
            # This would integrate with FactionManager
            # For now, use a simple random discount
            relationship_discount = random.uniform(0, 0.1)
        
        final_value = base_value * (1 - relationship_discount)
        
        return {
            "resource_type": resource_type,
            "quantity": quantity,
            "base_price": base_price,
            "base_value": base_value,
            "stability_factor": stability_factor,
            "inflation_factor": inflation_factor,
            "relationship_discount": relationship_discount,
            "final_value": final_value,
            "value_per_unit": final_value / quantity if quantity > 0 else 0,
        }
    
    async def get_market_trends(self) -> Dict[str, str]:
        """
        Get current market trends for all resources.
        
        Returns:
            Dictionary of resource trends
        """
        market_state = await self.get_market_state()
        return market_state.get("market_trends", {})
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Get key economic indicators.
        
        Returns:
            Economic indicators dictionary
        """
        market_state = await self.get_market_state()
        
        # Calculate average price change
        resource_prices = market_state.get("resource_prices", {})
        base_prices = {resource: config["base_price"] for resource, config in self.resource_types.items()}
        
        total_change = 0
        resource_count = 0
        
        for resource, current_price in resource_prices.items():
            if resource in base_prices:
                base_price = base_prices[resource]
                change_percent = ((current_price - base_price) / base_price) * 100
                total_change += change_percent
                resource_count += 1
        
        avg_price_change = total_change / resource_count if resource_count > 0 else 0
        
        # Calculate market volatility
        trends = market_state.get("market_trends", {})
        volatile_resources = sum(1 for trend in trends.values() if trend in ["rising", "falling"])
        volatility_percent = (volatile_resources / len(trends)) * 100 if trends else 0
        
        return {
            "market_stability": market_state.get("market_stability", 0.7),
            "inflation_rate": market_state.get("inflation_rate", 0.02),
            "resource_availability": market_state.get("resource_availability", 0.8),
            "avg_price_change": avg_price_change,
            "market_volatility": volatility_percent,
            "trade_volume": market_state.get("trade_volume", 1000),
            "active_economic_events": len(market_state.get("economic_events", [])),
            "last_updated": market_state.get("last_updated", time.time()),
        }
    
    async def generate_economic_event(
        self, 
        event_type: str, 
        intensity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate an economic event.
        
        Args:
            event_type: Type of economic event
            intensity: Event intensity (0.0 to 1.0)
        
        Returns:
            Generated economic event
        """
        event_types = {
            "market_crash": {
                "description": "Market experiences significant downturn",
                "price_impact": -0.3,
                "stability_impact": -0.2,
            },
            "market_boom": {
                "description": "Market experiences significant upturn",
                "price_impact": 0.3,
                "stability_impact": 0.1,
            },
            "resource_discovery": {
                "description": "New resource deposits discovered",
                "price_impact": -0.1,
                "availability_impact": 0.2,
            },
            "trade_disruption": {
                "description": "Trade routes disrupted by external factors",
                "price_impact": 0.2,
                "stability_impact": -0.1,
            },
        }
        
        if event_type not in event_types:
            raise ValueError(f"Invalid economic event type: {event_type}")
        
        event_config = event_types[event_type]
        
        # Apply intensity scaling
        price_impact = event_config["price_impact"] * intensity
        stability_impact = event_config["stability_impact"] * intensity
        availability_impact = event_config.get("availability_impact", 0) * intensity
        
        # Update market state
        current_state = await self.get_market_state()
        
        # Update resource prices
        resource_prices = current_state.get("resource_prices", {})
        for resource in resource_prices:
            resource_prices[resource] *= (1 + price_impact)
        
        # Update market stability
        new_stability = max(0.0, min(1.0, current_state.get("market_stability", 0.7) + stability_impact))
        
        # Update resource availability
        new_availability = max(0.0, min(1.0, current_state.get("resource_availability", 0.8) + availability_impact))
        
        # Add event to history
        economic_events = current_state.get("economic_events", [])
        economic_events.append({
            "type": event_type,
            "intensity": intensity,
            "description": event_config["description"],
            "timestamp": time.time(),
            "impacts": {
                "price_impact": price_impact,
                "stability_impact": stability_impact,
                "availability_impact": availability_impact,
            },
        })
        
        # Keep only last 10 events
        economic_events = economic_events[-10:]
        
        # Update market state
        await self.update_market_state({
            "resource_prices": resource_prices,
            "market_stability": new_stability,
            "resource_availability": new_availability,
            "economic_events": economic_events,
        })
        
        return {
            "event_type": event_type,
            "intensity": intensity,
            "description": event_config["description"],
            "impacts": {
                "price_impact": price_impact,
                "stability_impact": stability_impact,
                "availability_impact": availability_impact,
            },
            "timestamp": time.time(),
        }
    
    async def clear_cache(self):
        """Clear economic cache."""
        self._market_cache.clear()
        
        redis = await self._get_redis()
        await redis.delete("economic:market_state")
