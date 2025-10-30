"""
Event System - Global event generation and processing.
Handles dynamic event creation, processing, and propagation.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class EventSystem:
    """
    Manages global events with generation, processing, and propagation.
    Handles event triggers, processing pipeline, and history tracking.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._event_queue: List[Dict[str, Any]] = []
        self._processing = False
        
        # Event types and their configurations
        self.event_types = {
            "economic": {
                "weight": 0.3,
                "triggers": ["market_volatility", "resource_scarcity", "trade_disruption"],
                "duration": 3600,  # 1 hour
            },
            "political": {
                "weight": 0.25,
                "triggers": ["faction_conflict", "leadership_change", "policy_change"],
                "duration": 7200,  # 2 hours
            },
            "social": {
                "weight": 0.2,
                "triggers": ["population_migration", "cultural_shift", "social_unrest"],
                "duration": 1800,  # 30 minutes
            },
            "natural": {
                "weight": 0.15,
                "triggers": ["weather_change", "disaster", "resource_discovery"],
                "duration": 14400,  # 4 hours
            },
            "technological": {
                "weight": 0.1,
                "triggers": ["innovation", "breakthrough", "system_failure"],
                "duration": 10800,  # 3 hours
            },
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
    
    async def generate_event(
        self,
        event_type: str,
        trigger: str,
        intensity: float = 0.5,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new event.
        
        Args:
            event_type: Type of event (economic, political, social, natural, technological)
            trigger: What triggered the event
            intensity: Event intensity (0.0 to 1.0)
            description: Optional event description
            metadata: Optional event metadata
        
        Returns:
            Generated event dictionary
        """
        if event_type not in self.event_types:
            raise ValueError(f"Invalid event type: {event_type}")
        
        event_config = self.event_types[event_type]
        event_id = str(uuid4())
        
        # Generate event based on type and intensity
        event = {
            "id": event_id,
            "type": event_type,
            "trigger": trigger,
            "intensity": intensity,
            "description": description or self._generate_event_description(event_type, trigger, intensity),
            "status": "active",
            "duration": event_config["duration"],
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(seconds=event_config["duration"])).isoformat(),
            "impact": self._calculate_event_impact(event_type, intensity),
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Store event in database
        await self._store_event(event)
        
        # Add to processing queue
        self._event_queue.append(event)
        
        # Start processing if not already running
        if not self._processing:
            asyncio.create_task(self._process_event_queue())
        
        return event
    
    def _generate_event_description(self, event_type: str, trigger: str, intensity: float) -> str:
        """Generate event description based on type and intensity."""
        descriptions = {
            "economic": {
                "market_volatility": f"Market volatility {'increases' if intensity > 0.5 else 'decreases'} significantly",
                "resource_scarcity": f"Resource scarcity {'worsens' if intensity > 0.5 else 'improves'} across regions",
                "trade_disruption": f"Trade routes experience {'major' if intensity > 0.7 else 'minor'} disruptions",
            },
            "political": {
                "faction_conflict": f"Faction tensions {'escalate' if intensity > 0.5 else 'de-escalate'} rapidly",
                "leadership_change": f"Leadership changes occur with {'significant' if intensity > 0.5 else 'minimal'} impact",
                "policy_change": f"New policies are implemented with {'major' if intensity > 0.5 else 'minor'} consequences",
            },
            "social": {
                "population_migration": f"Population migration {'increases' if intensity > 0.5 else 'decreases'} significantly",
                "cultural_shift": f"Cultural shifts {'accelerate' if intensity > 0.5 else 'slow down'} across regions",
                "social_unrest": f"Social unrest {'grows' if intensity > 0.5 else 'diminishes'} in affected areas",
            },
            "natural": {
                "weather_change": f"Weather patterns {'shift dramatically' if intensity > 0.5 else 'change gradually'}",
                "disaster": f"Natural disaster {'strikes' if intensity > 0.5 else 'threatens'} the region",
                "resource_discovery": f"New resources are {'discovered' if intensity > 0.5 else 'identified'} in the area",
            },
            "technological": {
                "innovation": f"Technological innovation {'accelerates' if intensity > 0.5 else 'progresses'} steadily",
                "breakthrough": f"Major breakthrough {'occurs' if intensity > 0.5 else 'approaches'} in technology",
                "system_failure": f"System failures {'increase' if intensity > 0.5 else 'decrease'} across networks",
            },
        }
        
        return descriptions.get(event_type, {}).get(trigger, f"Event of type {event_type} triggered by {trigger}")
    
    def _calculate_event_impact(self, event_type: str, intensity: float) -> Dict[str, float]:
        """Calculate event impact on different systems."""
        base_impact = intensity * 0.5  # Base impact multiplier
        
        impacts = {
            "economic": base_impact * (1.2 if event_type == "economic" else 0.8),
            "political": base_impact * (1.2 if event_type == "political" else 0.8),
            "social": base_impact * (1.2 if event_type == "social" else 0.8),
            "natural": base_impact * (1.2 if event_type == "natural" else 0.8),
            "technological": base_impact * (1.2 if event_type == "technological" else 0.8),
        }
        
        return impacts
    
    async def _store_event(self, event: Dict[str, Any]):
        """Store event in database."""
        postgres = await self._get_postgres()
        
        query = """
            INSERT INTO world_events
            (id, event_type, trigger, intensity, description, status, duration,
             start_time, end_time, impact, metadata, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb, $12)
        """
        
        await postgres.execute(
            query,
            event["id"],
            event["type"],
            event["trigger"],
            event["intensity"],
            event["description"],
            event["status"],
            event["duration"],
            event["start_time"],
            event["end_time"],
            json.dumps(event["impact"]),
            json.dumps(event["metadata"]),
            event["created_at"],
        )
    
    async def _process_event_queue(self):
        """Process event queue asynchronously."""
        self._processing = True
        
        while self._event_queue:
            event = self._event_queue.pop(0)
            await self._process_event(event)
        
        self._processing = False
    
    async def _process_event(self, event: Dict[str, Any]):
        """Process a single event."""
        try:
            # Apply event impact to world state
            await self._apply_event_impact(event)
            
            # Propagate event to other services
            await self._propagate_event(event)
            
            # Schedule event completion
            await self._schedule_event_completion(event)
            
        except Exception as e:
            print(f"Error processing event {event['id']}: {e}")
    
    async def _apply_event_impact(self, event: Dict[str, Any]):
        """Apply event impact to world state."""
        # This would integrate with WorldStateManager
        # For now, just log the impact
        print(f"Applying event impact: {event['type']} - {event['impact']}")
    
    async def _propagate_event(self, event: Dict[str, Any]):
        """Propagate event to other services."""
        # This would send event to other services via ServiceCoordinator
        # For now, just log the propagation
        print(f"Propagating event: {event['type']} - {event['id']}")
    
    async def _schedule_event_completion(self, event: Dict[str, Any]):
        """Schedule event completion."""
        # Schedule event to be marked as completed after duration
        await asyncio.sleep(event["duration"])
        await self.complete_event(event["id"])
    
    async def complete_event(self, event_id: str) -> bool:
        """Mark event as completed."""
        postgres = await self._get_postgres()
        
        query = """
            UPDATE world_events
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        await postgres.execute(query, event_id)
        return True
    
    async def get_active_events(self) -> List[Dict[str, Any]]:
        """Get all active events."""
        postgres = await self._get_postgres()
        
        query = """
            SELECT id, event_type, trigger, intensity, description, status, duration,
                   start_time, end_time, impact, metadata, created_at, updated_at
            FROM world_events
            WHERE status = 'active'
            ORDER BY created_at DESC
        """
        
        results = await postgres.fetch_all(query)
        
        events = []
        for result in results:
            events.append({
                "id": result["id"],
                "type": result["event_type"],
                "trigger": result["trigger"],
                "intensity": result["intensity"],
                "description": result["description"],
                "status": result["status"],
                "duration": result["duration"],
                "start_time": result["start_time"],
                "end_time": result["end_time"],
                "impact": json.loads(result["impact"]) if isinstance(result["impact"], str) else result["impact"],
                "metadata": json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"],
                "created_at": result["created_at"].isoformat() if result["created_at"] else None,
                "updated_at": result["updated_at"].isoformat() if result["updated_at"] else None,
            })
        
        return events
    
    async def get_event_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get event history."""
        postgres = await self._get_postgres()
        
        query = """
            SELECT id, event_type, trigger, intensity, description, status, duration,
                   start_time, end_time, impact, metadata, created_at, updated_at
            FROM world_events
            ORDER BY created_at DESC
            LIMIT $1
        """
        
        results = await postgres.fetch_all(query, limit)
        
        events = []
        for result in results:
            events.append({
                "id": result["id"],
                "type": result["event_type"],
                "trigger": result["trigger"],
                "intensity": result["intensity"],
                "description": result["description"],
                "status": result["status"],
                "duration": result["duration"],
                "start_time": result["start_time"],
                "end_time": result["end_time"],
                "impact": json.loads(result["impact"]) if isinstance(result["impact"], str) else result["impact"],
                "metadata": json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"],
                "created_at": result["created_at"].isoformat() if result["created_at"] else None,
                "updated_at": result["updated_at"].isoformat() if result["updated_at"] else None,
            })
        
        return events
    
    async def get_event_statistics(self) -> Dict[str, Any]:
        """Get event statistics."""
        postgres = await self._get_postgres()
        
        # Get event counts by type
        query = """
            SELECT event_type, COUNT(*) as count, AVG(intensity) as avg_intensity
            FROM world_events
            GROUP BY event_type
        """
        
        results = await postgres.fetch_all(query)
        
        stats = {
            "total_events": 0,
            "active_events": 0,
            "event_types": {},
            "avg_intensity": 0.0,
        }
        
        for result in results:
            event_type = result["event_type"]
            count = result["count"]
            avg_intensity = float(result["avg_intensity"]) if result["avg_intensity"] else 0.0
            
            stats["event_types"][event_type] = {
                "count": count,
                "avg_intensity": avg_intensity,
            }
            stats["total_events"] += count
        
        # Get active events count
        active_query = "SELECT COUNT(*) as count FROM world_events WHERE status = 'active'"
        active_result = await postgres.fetch(active_query)
        stats["active_events"] = active_result["count"] if active_result else 0
        
        # Calculate overall average intensity
        if stats["total_events"] > 0:
            intensity_query = "SELECT AVG(intensity) as avg_intensity FROM world_events"
            intensity_result = await postgres.fetch(intensity_query)
            stats["avg_intensity"] = float(intensity_result["avg_intensity"]) if intensity_result["avg_intensity"] else 0.0
        
        return stats
