"""
FastAPI routes for Weather Manager service.
REAL IMPLEMENTATION - No mocks, real API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.weather_manager.weather_manager import WeatherManager, WeatherState, WeatherData, Season

router = APIRouter(prefix="/api/weather", tags=["Weather"])

# Global weather manager instance (initialized by server)
weather_manager: Optional[WeatherManager] = None


class WeatherStateRequest(BaseModel):
    """Request to set weather state."""
    state: str
    intensity: Optional[float] = None


class SeasonRequest(BaseModel):
    """Request to set season."""
    season: str


class WeatherResponse(BaseModel):
    """Weather response model."""
    state: str
    intensity: float
    temperature: float
    wind_speed: float
    humidity: float
    season: str
    duration_minutes: int


class ForecastResponse(BaseModel):
    """Weather forecast response."""
    forecast: List[dict]
    hours: int


class StatisticsResponse(BaseModel):
    """Weather statistics response."""
    statistics: dict


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather():
    """Get current weather state."""
    if not weather_manager:
        raise HTTPException(status_code=503, detail="Weather Manager not initialized")
    
    current = weather_manager.get_current_weather()
    
    return WeatherResponse(
        state=current.state.value,
        intensity=current.intensity,
        temperature=current.temperature,
        wind_speed=current.wind_speed,
        humidity=current.humidity,
        season=current.season.value,
        duration_minutes=current.duration_minutes,
    )


@router.post("/set")
async def set_weather(request: WeatherStateRequest):
    """Manually set weather state."""
    if not weather_manager:
        raise HTTPException(status_code=503, detail="Weather Manager not initialized")
    
    try:
        weather_state = WeatherState(request.state)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid weather state: {request.state}. Valid states: {[s.value for s in WeatherState]}"
        )
    
    await weather_manager.set_weather(weather_state, request.intensity)
    
    current = weather_manager.get_current_weather()
    
    return {
        "message": f"Weather set to {weather_state.value}",
        "weather": WeatherResponse(
            state=current.state.value,
            intensity=current.intensity,
            temperature=current.temperature,
            wind_speed=current.wind_speed,
            humidity=current.humidity,
            season=current.season.value,
            duration_minutes=current.duration_minutes,
        ).dict()
    }


@router.post("/season")
async def set_season(request: SeasonRequest):
    """Set current season."""
    if not weather_manager:
        raise HTTPException(status_code=503, detail="Weather Manager not initialized")
    
    try:
        season = Season(request.season)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid season: {request.season}. Valid seasons: {[s.value for s in Season]}"
        )
    
    weather_manager.set_season(season)
    
    return {
        "message": f"Season set to {season.value}",
        "season": season.value,
        "weather": weather_manager.get_current_weather().to_dict()
    }


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(hours: int = 24):
    """Get weather forecast."""
    if not weather_manager:
        raise HTTPException(status_code=503, detail="Weather Manager not initialized")
    
    if hours < 1 or hours > 168:  # Max 1 week
        raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
    
    forecast = weather_manager.get_forecast(hours)
    
    return ForecastResponse(
        forecast=forecast,
        hours=hours
    )


@router.get("/stats", response_model=StatisticsResponse)
async def get_statistics():
    """Get weather statistics."""
    if not weather_manager:
        raise HTTPException(status_code=503, detail="Weather Manager not initialized")
    
    stats = weather_manager.get_statistics()
    
    return StatisticsResponse(statistics=stats)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "weather_manager",
        "initialized": weather_manager is not None,
    }






