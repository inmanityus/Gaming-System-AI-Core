"""
Model Management Service Server - FastAPI server.
"""

from fastapi import FastAPI
from services.model_management.api_routes import router

app = FastAPI(title="Model Management Service")
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "healthy"}







