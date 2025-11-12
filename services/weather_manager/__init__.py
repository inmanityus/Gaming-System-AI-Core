# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Weather Manager Service - Manages weather state and progression.
REAL IMPLEMENTATION - No mocks, real weather state management.
"""

from .weather_manager import WeatherManager, WeatherState, WeatherData

__all__ = [
    'WeatherManager',
    'WeatherState',
    'WeatherData',
]








