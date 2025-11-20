"""
Custom middleware for Gaming System AI Core API
Handles request logging, error handling, and performance monitoring
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import json

logger = structlog.get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.perf_counter()
        
        # Log request
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
        except Exception as e:
            error = str(e)
            logger.error(
                "request_failed",
                request_id=request_id,
                error=error,
                exc_info=True
            )
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response
            if response:
                logger.info(
                    "request_completed",
                    request_id=request_id,
                    status_code=response.status_code,
                    duration_ms=duration_ms
                )
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            else:
                logger.error(
                    "request_error",
                    request_id=request_id,
                    duration_ms=duration_ms,
                    error=error
                )
        
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except ValueError as e:
            # Handle validation errors
            return Response(
                content=json.dumps({
                    "error": "Validation Error",
                    "detail": str(e),
                    "request_id": getattr(request.state, "request_id", None)
                }),
                status_code=400,
                media_type="application/json"
            )
        except Exception as e:
            # Handle all other errors
            logger.error(
                "unhandled_error",
                error=str(e),
                exc_info=True,
                request_id=getattr(request.state, "request_id", None)
            )
            
            return Response(
                content=json.dumps({
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None)
                }),
                status_code=500,
                media_type="application/json"
            )
