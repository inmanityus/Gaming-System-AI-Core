"""
FastAPI server for Weather Manager service.
REAL IMPLEMENTATION - No mocks, real server.
"""

from fastapi import FastAPI

from api_routes import router, weather_manager
from weather_manager import WeatherManager, Season

app = FastAPI(
    title="Weather Manager Service",
    description="Weather state management and progression system",
    version="1.0.0"
)

# Include API routes
app.include_router(router)

# Initialize weather manager on startup
@app.on_event("startup")
async def startup_event():
    """Initialize weather manager on startup."""
    global weather_manager
    
    # Create weather manager instance
    weather_manager = WeatherManager(season=Season.SPRING)
    
    # Start weather progression
    await weather_manager.start()
    
    print("[WEATHER SERVER] Weather Manager initialized and started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global weather_manager
    
    if weather_manager:
        await weather_manager.stop()
        print("[WEATHER SERVER] Weather Manager stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)






