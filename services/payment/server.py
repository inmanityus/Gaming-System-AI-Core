"""
PM-002/PM-003: Payment Service FastAPI Server
Main server for payment and coupon management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from payment.api_routes import router

app = FastAPI(
    title="Payment Service",
    description="Stripe integration for subscriptions and coupons",
    version="1.0.0"
)

# CORS middleware
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # SECURITY FIX 2025-11-09
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Payment Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "payment"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4001)

