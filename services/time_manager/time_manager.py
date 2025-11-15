"""
TimeOfDayManager - Day/Night time progression system.
REAL IMPLEMENTATION - No mocks, real time tracking and event broadcasting.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from services.shared.binary_messaging.publisher import publish_binary_event as publish_weather_event


class TimeState(Enum):
    """Time of day states."""
    DAWN = "dawn"  # 5:00 - 7:00
    DAY = "day"  # 7:00 - 18:00
    DUSK = "dusk"  # 18:00 - 20:00
    NIGHT = "night"  # 20:00 - 5:00


@dataclass
class TimeData:
    """Time data structure."""
    hour: int  # 0-23
    minute: int  # 0-59
    day: int  # Day number (starts at 1)
    state: TimeState
    total_minutes: int  # Total minutes since day 1
    
    @property
    def time_string(self) -> str:
        """Get formatted time string (HH:MM)."""
        return f"{self.hour:02d}:{self.minute:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hour": self.hour,
            "minute": self.minute,
            "day": self.day,
            "state": self.state.value,
            "total_minutes": self.total_minutes,
            "time_string": self.time_string,
        }


class TimeAwareInterface(ABC):
    """Interface for systems that need to be notified of time changes."""
    
    @abstractmethod
    async def on_time_changed(self, time_data: TimeData) -> None:
        """Called when time changes."""
        pass
    
    @abstractmethod
    async def on_time_of_day_changed(self, old_state: TimeState, new_state: TimeState) -> None:
        """Called when time of day state changes."""
        pass


class TimeOfDayManager:
    """
    TimeOfDayManager - REAL IMPLEMENTATION.
    
    Manages day/night time progression, broadcasts events, and manages
    time-aware subscribers.
    """
    
    def __init__(
        self,
        time_scale: float = 60.0,  # 1 real second = 60 game minutes
        start_hour: int = 7  # Start at 7:00 AM (day)
    ):
        """
        Initialize TimeOfDayManager.
        
        Args:
            time_scale: Real seconds per game hour (default: 60 = 1 minute real = 1 hour game)
            start_hour: Starting hour (0-23)
        """
        self.time_scale = time_scale  # Real seconds per game hour
        self.game_minutes_per_real_second = 60.0 / time_scale
        
        # Current time state
        self.current_time = TimeData(
            hour=start_hour,
            minute=0,
            day=1,
            state=self._get_state_for_hour(start_hour),
            total_minutes=start_hour * 60
        )
        
        # Time-aware subscribers
        self._subscribers: List[TimeAwareInterface] = []
        self._subscriber_lock = asyncio.Lock()
        
        # Running state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Last update time for calculating progression
        self._last_update_time = time.time()
        
        # Statistics
        self._stats = {
            "total_updates": 0,
            "state_changes": 0,
            "subscribers": 0,
            "events_published": 0,
        }
    
    def _get_state_for_hour(self, hour: int) -> TimeState:
        """Get time state for given hour."""
        if 5 <= hour < 7:
            return TimeState.DAWN
        elif 7 <= hour < 18:
            return TimeState.DAY
        elif 18 <= hour < 20:
            return TimeState.DUSK
        else:  # 20-4
            return TimeState.NIGHT
    
    async def start(self):
        """Start time progression - REAL IMPLEMENTATION."""
        if self._running:
            return
        
        self._running = True
        self._last_update_time = time.time()
        self._task = asyncio.create_task(self._time_progression_loop())
        print(f"[TIME MANAGER] Started - Scale: {self.time_scale}s/hour, Current: {self.current_time.time_string}")
    
    async def stop(self):
        """Stop time progression."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[TIME MANAGER] Stopped")
    
    async def _time_progression_loop(self):
        """Main time progression loop - REAL IMPLEMENTATION."""
        while self._running:
            try:
                # Calculate elapsed real time
                current_real_time = time.time()
                elapsed_real_seconds = current_real_time - self._last_update_time
                self._last_update_time = current_real_time
                
                # Calculate game time progression
                game_minutes_elapsed = elapsed_real_seconds * self.game_minutes_per_real_second
                
                # Update time
                await self._update_time(game_minutes_elapsed)
                
                # Sleep for update interval (1 second)
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[TIME MANAGER] Error in progression loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_time(self, game_minutes_elapsed: float):
        """Update time state - REAL IMPLEMENTATION."""
        old_state = self.current_time.state
        old_time_string = self.current_time.time_string
        
        # Add elapsed minutes
        self.current_time.total_minutes += int(game_minutes_elapsed)
        self.current_time.minute += int(game_minutes_elapsed)
        
        # Handle minute overflow
        while self.current_time.minute >= 60:
            self.current_time.minute -= 60
            self.current_time.hour += 1
        
        # Handle hour overflow (new day)
        while self.current_time.hour >= 24:
            self.current_time.hour -= 24
            self.current_time.day += 1
        
        # Update state
        new_state = self._get_state_for_hour(self.current_time.hour)
        self.current_time.state = new_state
        
        self._stats["total_updates"] += 1
        
        # Check if state changed
        state_changed = old_state != new_state
        if state_changed:
            self._stats["state_changes"] += 1
            await self._handle_state_change(old_state, new_state)
        
        # Broadcast time update event (every update)
        await self._broadcast_time_update()
        
        # Notify subscribers
        await self._notify_subscribers()
    
    async def _handle_state_change(self, old_state: TimeState, new_state: TimeState):
        """Handle time of day state change - REAL IMPLEMENTATION."""
        print(f"[TIME MANAGER] State changed: {old_state.value} → {new_state.value} ({self.current_time.time_string})")
        
        # Publish event via event bus
        # Publish time state change event via distributed messaging
        event_data = {
            "old_state": old_state.value,
            "new_state": new_state.value,
            "hour": self.current_time.hour,
            "minute": self.current_time.minute,
            "day": self.current_time.day,
            "time_string": self.current_time.time_string,
        }
        
        await publish_weather_event("time.changed", event_data)
        self._stats["events_published"] += 1
        
        # Also publish specific activation events
        if new_state == TimeState.DAY:
            await publish_weather_event("time.day_activated", self.current_time.to_dict())
        
        elif new_state == TimeState.NIGHT:
            await publish_weather_event("time.night_activated", self.current_time.to_dict())
    
    async def _broadcast_time_update(self):
        """Broadcast time update event via distributed messaging."""
        # Only broadcast major updates (every minute of game time)
        if self.current_time.minute % 1 == 0:  # Every game minute
            await publish_weather_event("time.updated", {
                "time": self.current_time.to_dict(),
                "update_type": "time_progression"
            })
    
    async def _notify_subscribers(self):
        """Notify all time-aware subscribers - REAL IMPLEMENTATION."""
        async with self._subscriber_lock:
            subscribers = list(self._subscribers)  # Copy list
        
        # Notify all subscribers concurrently
        tasks = []
        for subscriber in subscribers:
            tasks.append(subscriber.on_time_changed(self.current_time))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(self, subscriber: TimeAwareInterface) -> str:
        """
        Subscribe to time updates - REAL IMPLEMENTATION.
        
        Args:
            subscriber: Object implementing TimeAwareInterface
        
        Returns:
            Subscription ID
        """
        subscription_id = str(uuid4())
        
        async with self._subscriber_lock:
            if subscriber not in self._subscribers:
                self._subscribers.append(subscriber)
                self._stats["subscribers"] = len(self._subscribers)
                print(f"[TIME MANAGER] Subscriber added (Total: {len(self._subscribers)})")
        
        return subscription_id
    
    async def unsubscribe(self, subscriber: TimeAwareInterface) -> bool:
        """Unsubscribe from time updates."""
        async with self._subscriber_lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)
                self._stats["subscribers"] = len(self._subscribers)
                print(f"[TIME MANAGER] Subscriber removed (Total: {len(self._subscribers)})")
                return True
        
        return False
    
    def get_current_time(self) -> TimeData:
        """Get current time data."""
        return self.current_time
    
    def set_time(self, hour: int, minute: int = 0, day: int = None):
        """Set time manually - REAL IMPLEMENTATION."""
        old_state = self.current_time.state
        
        self.current_time.hour = hour % 24
        self.current_time.minute = minute % 60
        if day is not None:
            self.current_time.day = day
        
        new_state = self._get_state_for_hour(self.current_time.hour)
        self.current_time.state = new_state
        
        # Recalculate total minutes
        self.current_time.total_minutes = (self.current_time.day - 1) * 24 * 60 + self.current_time.hour * 60 + self.current_time.minute
        
        # Handle state change if needed
        if old_state != new_state:
            asyncio.create_task(self._handle_state_change(old_state, new_state))
        
        print(f"[TIME MANAGER] Time set to {self.current_time.time_string} (Day {self.current_time.day})")
    
    def set_time_scale(self, time_scale: float):
        """Set time scale (real seconds per game hour)."""
        self.time_scale = time_scale
        self.game_minutes_per_real_second = 60.0 / time_scale
        print(f"[TIME MANAGER] Time scale set to {time_scale}s/hour")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            **self._stats,
            "current_time": self.current_time.to_dict(),
            "time_scale": self.time_scale,
            "running": self._running,
        }

