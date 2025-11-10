"""
Performance Mode Service Server.
"""

import logging
from fastapi import FastAPI
from services.performance_mode import api_routes

_logger = logging.getLogger(__name__)

app = FastAPI(
    title="Performance Mode Service",
    description="Dual-Mode Performance Architecture (REQ-PERF-001)",
    version="1.0.0",
)

app.include_router(api_routes.router)


@app.on_event("startup")
async def startup():
    """Initialize service on startup."""
    _logger.info("Performance Mode Service starting...")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    _logger.info("Performance Mode Service shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)



