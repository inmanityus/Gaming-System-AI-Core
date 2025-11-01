"""
Time Manager Service Server - FastAPI server for time management.
"""

import asyncio
from fastapi import FastAPI
from .api_routes import router

app = FastAPI(
    title="Time Manager Service",
    description="Day/Night time progression and management",
    version="1.0.0"
)

app.include_router(router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "time_manager"}


@app.on_event("startup")
async def startup():
    """Start time progression on server startup."""
    from .api_routes import get_time_manager
    time_manager = get_time_manager()
    await time_manager.start()


@app.on_event("shutdown")
async def shutdown():
    """Stop time progression on server shutdown."""
    from .api_routes import get_time_manager
    time_manager = get_time_manager()
    await time_manager.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4011)

