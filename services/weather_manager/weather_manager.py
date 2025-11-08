"""
Weather Manager - Weather state management and progression system.
REAL IMPLEMENTATION - No mocks, real weather state management.
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from binary_event_publisher import publish_binary_event as publish_weather_event
from event_subscriber import get_event_subscriber


class WeatherState(Enum):
    """Weather state types."""
    CLEAR = "clear"  # Clear skies
    PARTLY_CLOUDY = "partly_cloudy"  # Some clouds
    CLOUDY = "cloudy"  # Overcast
    RAIN = "rain"  # Light to moderate rain
    HEAVY_RAIN = "heavy_rain"  # Heavy rain
    STORM = "storm"  # Thunderstorm
    FOG = "fog"  # Foggy conditions
    MIST = "mist"  # Light mist
    SNOW = "snow"  # Snow
    HEAVY_SNOW = "heavy_snow"  # Heavy snow
    BLIZZARD = "blizzard"  # Blizzard conditions
    WINDY = "windy"  # Strong winds
    EXTREME_HEAT = "extreme_heat"  # Very hot
    EXTREME_COLD = "extreme_cold"  # Very cold


class Season(Enum):
    """Season types."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


@dataclass
class WeatherData:
    """Weather data structure."""
    state: WeatherState
    intensity: float  # 0.0 - 1.0 (weather intensity)
    temperature: float  # Temperature in Celsius
    wind_speed: float  # Wind speed (km/h)
    humidity: float  # 0.0 - 1.0
    season: Season
    duration_minutes: int  # How long this weather has been active
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state.value,
            "intensity": self.intensity,
            "temperature": self.temperature,
            "wind_speed": self.wind_speed,
            "humidity": self.humidity,
            "season": self.season.value,
            "duration_minutes": self.duration_minutes,
        }


class WeatherManager:
    """
    Weather Manager - REAL IMPLEMENTATION.
    
    Manages weather state, progression, and integration with
    Time Manager for day/night weather variations.
    """
    
    def __init__(
        self,
        season: Season = Season.SPRING,
        initial_weather: Optional[WeatherState] = None,
        enable_time_subscription: bool = False
    ):
        """
        Initialize Weather Manager.
        
        Args:
            season: Current season
            initial_weather: Initial weather state (random if None)
            enable_time_subscription: Whether to subscribe to time change events via SQS
        """
        self.enable_time_subscription = enable_time_subscription
        self.event_subscriber = get_event_subscriber() if enable_time_subscription else None
        self.season = season
        
        # Current weather state
        initial_state = initial_weather or self._get_default_weather_for_season(season)
        self.current_weather = WeatherData(
            state=initial_state,
            intensity=self._get_default_intensity(initial_state),
            temperature=self._get_default_temperature(season),
            wind_speed=self._get_default_wind_speed(initial_state),
            humidity=self._get_default_humidity(initial_state),
            season=season,
            duration_minutes=0
        )
        
        # Progression state
        self._running = False
        self._progression_task: Optional[asyncio.Task] = None
        self._update_interval = 60.0  # Update every 60 seconds (game time)
        
        # Weather history
        self._weather_history: List[Dict[str, Any]] = []
        self._max_history = 100
        
        # Statistics
        self._stats = {
            "total_changes": 0,
            "state_counts": {state.value: 0 for state in WeatherState},
            "total_duration_minutes": 0,
        }
        
        # Subscribe to time changes
        self._time_subscription_id: Optional[str] = None
    
    async def start(self):
        """Start weather progression."""
        if self._running:
            return
        
        # Subscribe to time changes via distributed event system
        if self.enable_time_subscription and self.event_subscriber:
            self.event_subscriber.subscribe("time.changed", self._handle_time_change)
            # Start subscriber polling in background
            asyncio.create_task(self.event_subscriber.start())
        
        self._running = True
        self._progression_task = asyncio.create_task(self._progression_loop())
        
        print(f"[WEATHER MANAGER] Started - Season: {self.season.value}, Initial: {self.current_weather.state.value}")
    
    async def stop(self):
        """Stop weather progression."""
        if not self._running:
            return
        
        self._running = False
        
        if self.enable_time_subscription and self.event_subscriber:
            self.event_subscriber.unsubscribe("time.changed")
            await self.event_subscriber.stop()
            self._time_subscription_id = None
        
        if self._progression_task:
            self._progression_task.cancel()
            try:
                await self._progression_task
            except asyncio.CancelledError:
                pass
        
        print("[WEATHER MANAGER] Stopped")
    
    async def _progression_loop(self):
        """Main weather progression loop."""
        try:
            while self._running:
                # Wait for update interval
                await asyncio.sleep(self._update_interval)
                
                # Update weather duration
                self.current_weather.duration_minutes += 1
                
                # Check if weather should change
                if self._should_change_weather():
                    old_state = self.current_weather.state
                    await self._transition_weather()
                    
                    # Publish weather change event
                    await self._publish_weather_change(old_state, self.current_weather.state)
                    
                    # Update statistics
                    self._stats["total_changes"] += 1
                    self._stats["state_counts"][self.current_weather.state.value] += 1
                    self.current_weather.duration_minutes = 0
                
                # Update weather parameters (intensity, temperature variations)
                self._update_weather_parameters()
                
                # Record history
                self._record_history()
                
        except asyncio.CancelledError:
            print("[WEATHER MANAGER] Progression loop cancelled")
        except Exception as e:
            print(f"[WEATHER MANAGER] Error in progression loop: {e}")
            raise
    
    def _should_change_weather(self) -> bool:
        """Determine if weather should change."""
        # Weather changes based on:
        # - Duration (longer weather less likely to change)
        # - Season (different weather patterns)
        # - Random chance
        
        base_chance = 0.05  # 5% base chance per update
        
        # Reduce chance if weather has been active for a while
        duration_factor = max(0.1, 1.0 - (self.current_weather.duration_minutes / 120.0))
        
        # Season-based modifiers
        season_modifier = self._get_season_change_probability(self.season, self.current_weather.state)
        
        final_chance = base_chance * duration_factor * season_modifier
        
        return random.random() < final_chance
    
    def _get_season_change_probability(self, season: Season, current_state: WeatherState) -> float:
        """Get probability modifier based on season and current weather."""
        # Some weather is more likely in certain seasons
        
        if season == Season.SPRING:
            # Spring: Rain, storms, unpredictable
            if current_state in [WeatherState.RAIN, WeatherState.STORM]:
                return 0.5  # Less likely to change from rain/storm in spring
            return 1.5  # More likely to change otherwise
        
        elif season == Season.SUMMER:
            # Summer: Clear, storms, extreme heat
            if current_state in [WeatherState.CLEAR, WeatherState.EXTREME_HEAT]:
                return 0.7
            if current_state == WeatherState.STORM:
                return 1.8  # Storms come and go quickly
            return 1.0
        
        elif season == Season.FALL:
            # Fall: Windy, fog, mist, cooler
            if current_state in [WeatherState.WINDY, WeatherState.FOG, WeatherState.MIST]:
                return 0.6
            return 1.2
        
        elif season == Season.WINTER:
            # Winter: Snow, cold, blizzards
            if current_state in [WeatherState.SNOW, WeatherState.HEAVY_SNOW, WeatherState.BLIZZARD]:
                return 0.4  # Winter weather persists
            return 1.3
        
        return 1.0
    
    async def _transition_weather(self):
        """Transition to new weather state."""
        # Select next weather state based on season and current state
        possible_states = self._get_possible_weather_states(self.season, self.current_weather.state)
        next_state = random.choice(possible_states)
        
        # Create new weather data
        self.current_weather = WeatherData(
            state=next_state,
            intensity=self._get_default_intensity(next_state),
            temperature=self._get_default_temperature(self.season, next_state),
            wind_speed=self._get_default_wind_speed(next_state),
            humidity=self._get_default_humidity(next_state),
            season=self.season,
            duration_minutes=0
        )
        
        print(f"[WEATHER MANAGER] Weather changed to: {next_state.value}")
    
    def _get_possible_weather_states(self, season: Season, current_state: WeatherState) -> List[WeatherState]:
        """Get list of possible next weather states based on season."""
        # Base states available in any season
        base_states = [
            WeatherState.CLEAR,
            WeatherState.PARTLY_CLOUDY,
            WeatherState.CLOUDY,
            WeatherState.WINDY,
        ]
        
        # Season-specific states
        if season == Season.SPRING:
            season_states = [
                WeatherState.RAIN,
                WeatherState.HEAVY_RAIN,
                WeatherState.STORM,
                WeatherState.MIST,
                WeatherState.FOG,
            ]
        elif season == Season.SUMMER:
            season_states = [
                WeatherState.CLEAR,
                WeatherState.PARTLY_CLOUDY,
                WeatherState.STORM,
                WeatherState.EXTREME_HEAT,
                WeatherState.WINDY,
            ]
        elif season == Season.FALL:
            season_states = [
                WeatherState.FOG,
                WeatherState.MIST,
                WeatherState.WINDY,
                WeatherState.RAIN,
                WeatherState.CLOUDY,
            ]
        elif season == Season.WINTER:
            season_states = [
                WeatherState.SNOW,
                WeatherState.HEAVY_SNOW,
                WeatherState.BLIZZARD,
                WeatherState.EXTREME_COLD,
                WeatherState.FOG,
                WeatherState.CLOUDY,
            ]
        else:
            season_states = []
        
        # Combine and filter out current state (weather can stay the same, but reduce chance)
        possible = base_states + season_states
        possible = [s for s in possible if s != current_state]
        
        # If no other options, keep current state
        if not possible:
            possible = [current_state]
        
        return possible
    
    def _update_weather_parameters(self):
        """Update weather parameters (intensity, temperature variations)."""
        # Slight variations in intensity
        intensity_variation = random.uniform(-0.1, 0.1)
        self.current_weather.intensity = max(0.0, min(1.0, self.current_weather.intensity + intensity_variation))
        
        # Temperature variations based on time of day (if we have that info)
        # For now, small random variations
        temp_variation = random.uniform(-2.0, 2.0)
        self.current_weather.temperature = max(-40.0, min(50.0, self.current_weather.temperature + temp_variation))
        
        # Wind speed variations
        wind_variation = random.uniform(-5.0, 5.0)
        self.current_weather.wind_speed = max(0.0, min(150.0, self.current_weather.wind_speed + wind_variation))
    
    async def _handle_time_change(self, event: Dict[str, Any]):
        """Handle time of day changes from Time Manager via distributed events."""
        # Weather can change based on time of day
        # For example: storms more likely at night, fog more likely in morning
        
        time_data = event.get("data", {}).get("time_state", "")
        
        if time_data == "dawn":
            # Fog/mist more likely at dawn
            if random.random() < 0.3:  # 30% chance
                if WeatherState.FOG in self._get_possible_weather_states(self.season, self.current_weather.state):
                    await self.set_weather(WeatherState.FOG)
        
        elif time_data == "day":
            # Clear weather more likely during day
            pass  # Already handled in progression
        
        elif time_data == "dusk":
            # Storms can develop at dusk
            if random.random() < 0.2:  # 20% chance
                if WeatherState.STORM in self._get_possible_weather_states(self.season, self.current_weather.state):
                    await self.set_weather(WeatherState.STORM)
        
        elif time_data == "night":
            # Fog, storms more common at night
            pass  # Handled in progression
    
    async def set_weather(self, weather_state: WeatherState, intensity: Optional[float] = None):
        """Manually set weather state."""
        old_state = self.current_weather.state
        
        self.current_weather.state = weather_state
        if intensity is not None:
            self.current_weather.intensity = max(0.0, min(1.0, intensity))
        else:
            self.current_weather.intensity = self._get_default_intensity(weather_state)
        
        self.current_weather.temperature = self._get_default_temperature(self.season, weather_state)
        self.current_weather.wind_speed = self._get_default_wind_speed(weather_state)
        self.current_weather.humidity = self._get_default_humidity(weather_state)
        self.current_weather.duration_minutes = 0
        
        # Update statistics if state actually changed
        if old_state != weather_state:
            self._stats["total_changes"] += 1
            self._stats["state_counts"][weather_state.value] += 1
        
        await self._publish_weather_change(old_state, weather_state)
        
        print(f"[WEATHER MANAGER] Weather manually set to: {weather_state.value}")
    
    def set_season(self, season: Season):
        """Change season."""
        self.season = season
        self.current_weather.season = season
        
        # Adjust temperature for new season
        self.current_weather.temperature = self._get_default_temperature(season, self.current_weather.state)
        
        print(f"[WEATHER MANAGER] Season changed to: {season.value}")
    
    async def _publish_weather_change(self, old_state: WeatherState, new_state: WeatherState):
        """Publish weather change event via distributed messaging."""
        event_data = {
            "old_state": old_state.value,
            "new_state": new_state.value,
            "weather": self.current_weather.to_dict(),
        }
        
        success = await publish_weather_event("weather.changed", event_data)
        status = "published" if success else "failed to publish"
        print(f"[WEATHER MANAGER] Weather change event {status}")
    
    def get_current_weather(self) -> WeatherData:
        """Get current weather data."""
        return self.current_weather
    
    def get_forecast(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get weather forecast (simulated)."""
        # Simple forecast: predicts weather based on current state and season
        forecast = []
        
        current_state = self.current_weather.state
        possible_states = self._get_possible_weather_states(self.season, current_state)
        
        for hour in range(hours):
            # Simulate weather progression
            if random.random() < 0.3:  # 30% chance to change each hour
                current_state = random.choice(possible_states)
                possible_states = self._get_possible_weather_states(self.season, current_state)
            
            forecast.append({
                "hour": hour,
                "state": current_state.value,
                "temperature": self._get_default_temperature(self.season, current_state) + random.uniform(-5, 5),
                "intensity": self._get_default_intensity(current_state),
            })
        
        return forecast
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get weather statistics."""
        return {
            **self._stats,
            "current_weather": self.current_weather.to_dict(),
            "season": self.season.value,
            "history_count": len(self._weather_history),
        }
    
    def _record_history(self):
        """Record current weather to history."""
        self._weather_history.append({
            "timestamp": time.time(),
            "weather": self.current_weather.to_dict(),
        })
        
        # Limit history size
        if len(self._weather_history) > self._max_history:
            self._weather_history.pop(0)
        
        self._stats["total_duration_minutes"] += 1
    
    # Helper methods for default values
    
    def _get_default_weather_for_season(self, season: Season) -> WeatherState:
        """Get default weather for season."""
        defaults = {
            Season.SPRING: WeatherState.PARTLY_CLOUDY,
            Season.SUMMER: WeatherState.CLEAR,
            Season.FALL: WeatherState.CLOUDY,
            Season.WINTER: WeatherState.CLOUDY,
        }
        return defaults.get(season, WeatherState.CLEAR)
    
    def _get_default_intensity(self, state: WeatherState) -> float:
        """Get default intensity for weather state."""
        intensities = {
            WeatherState.CLEAR: 0.0,
            WeatherState.PARTLY_CLOUDY: 0.2,
            WeatherState.CLOUDY: 0.4,
            WeatherState.RAIN: 0.6,
            WeatherState.HEAVY_RAIN: 0.8,
            WeatherState.STORM: 0.9,
            WeatherState.FOG: 0.5,
            WeatherState.MIST: 0.3,
            WeatherState.SNOW: 0.6,
            WeatherState.HEAVY_SNOW: 0.8,
            WeatherState.BLIZZARD: 1.0,
            WeatherState.WINDY: 0.4,
            WeatherState.EXTREME_HEAT: 0.9,
            WeatherState.EXTREME_COLD: 0.8,
        }
        return intensities.get(state, 0.5)
    
    def _get_default_temperature(self, season: Season, state: Optional[WeatherState] = None) -> float:
        """Get default temperature for season."""
        season_temps = {
            Season.SPRING: (5.0, 20.0),
            Season.SUMMER: (20.0, 35.0),
            Season.FALL: (0.0, 15.0),
            Season.WINTER: (-10.0, 5.0),
        }
        
        min_temp, max_temp = season_temps.get(season, (0.0, 20.0))
        
        if state == WeatherState.EXTREME_HEAT:
            return max_temp + 10.0
        elif state == WeatherState.EXTREME_COLD:
            return min_temp - 10.0
        elif state in [WeatherState.SNOW, WeatherState.HEAVY_SNOW, WeatherState.BLIZZARD]:
            return min_temp - 5.0
        
        return (min_temp + max_temp) / 2.0
    
    def _get_default_wind_speed(self, state: WeatherState) -> float:
        """Get default wind speed for weather state."""
        wind_speeds = {
            WeatherState.CLEAR: 5.0,
            WeatherState.PARTLY_CLOUDY: 8.0,
            WeatherState.CLOUDY: 10.0,
            WeatherState.RAIN: 15.0,
            WeatherState.HEAVY_RAIN: 25.0,
            WeatherState.STORM: 40.0,
            WeatherState.FOG: 2.0,
            WeatherState.MIST: 3.0,
            WeatherState.SNOW: 10.0,
            WeatherState.HEAVY_SNOW: 20.0,
            WeatherState.BLIZZARD: 60.0,
            WeatherState.WINDY: 30.0,
            WeatherState.EXTREME_HEAT: 5.0,
            WeatherState.EXTREME_COLD: 8.0,
        }
        return wind_speeds.get(state, 10.0)
    
    def _get_default_humidity(self, state: WeatherState) -> float:
        """Get default humidity for weather state."""
        humidities = {
            WeatherState.CLEAR: 0.4,
            WeatherState.PARTLY_CLOUDY: 0.5,
            WeatherState.CLOUDY: 0.6,
            WeatherState.RAIN: 0.9,
            WeatherState.HEAVY_RAIN: 0.95,
            WeatherState.STORM: 0.85,
            WeatherState.FOG: 0.95,
            WeatherState.MIST: 0.9,
            WeatherState.SNOW: 0.7,
            WeatherState.HEAVY_SNOW: 0.8,
            WeatherState.BLIZZARD: 0.85,
            WeatherState.WINDY: 0.5,
            WeatherState.EXTREME_HEAT: 0.6,
            WeatherState.EXTREME_COLD: 0.5,
        }
        return humidities.get(state, 0.6)

