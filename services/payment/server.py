"""
PM-002/PM-003: Payment Service FastAPI Server
Main server for payment and coupon management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_routes import router

app = FastAPI(
    title="Payment Service",
    description="Stripe integration for subscriptions and coupons",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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

