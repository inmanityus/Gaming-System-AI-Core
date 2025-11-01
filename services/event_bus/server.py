"""
Event Bus Service Server - FastAPI server for event bus.
"""

from fastapi import FastAPI
from .api_routes import router

app = FastAPI(
    title="Game Event Bus Service",
    description="Central event bus for inter-service communication",
    version="1.0.0"
)

app.include_router(router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "event_bus"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4010)

