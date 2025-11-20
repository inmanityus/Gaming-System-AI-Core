"""
FastAPI service for Token Window Management System.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime

from .context_engine import ContextEngine
from .tokenizer_service import TokenizerService
from .llm_gateway import LLMGateway
from .models import MODEL_CONFIGS


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# FastAPI app
app = FastAPI(
    title="Token Window Management System",
    description="Prevents AI model crashes by managing token windows",
    version="1.0.0"
)


# Global instances
context_engine = ContextEngine()
tokenizer_service = TokenizerService()
llm_gateway = LLMGateway(context_engine)


# Request/Response models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    model: str = Field(default="gpt-4o", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Max output tokens (auto-calculated if not provided)")
    stream: bool = Field(default=True, description="Stream the response")


class TokenCountRequest(BaseModel):
    text: Optional[str] = Field(None, description="Text to count tokens for")
    messages: Optional[List[ChatMessage]] = Field(None, description="Messages to count tokens for")
    model: str = Field(default="gpt-4", description="Model for tokenization")


class SessionInfoResponse(BaseModel):
    session_id: str
    model: str
    message_count: int
    total_tokens: int
    token_percentage: float
    compression_count: int
    created_at: str
    last_activity: str


# API endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Token Window Management System",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/chat/completions")
async def create_chat_completion(request: ChatRequest):
    """
    Create a chat completion with automatic token management.
    Prevents token limit crashes through proactive context management.
    """
    try:
        # Convert messages to dict format
        messages = [msg.dict() for msg in request.messages]
        
        # Create completion through gateway
        if request.stream:
            # Return streaming response
            async def generate():
                try:
                    async for chunk in llm_gateway.create_completion(
                        model=request.model,
                        messages=messages,
                        session_id=request.session_id,
                        stream=True,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    ):
                        # Format as SSE
                        data = json.dumps({"content": chunk})
                        yield f"data: {data}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    error_data = json.dumps({"error": str(e)})
                    yield f"data: {error_data}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        else:
            # Return non-streaming response
            result = await llm_gateway.create_completion(
                model=request.model,
                messages=messages,
                session_id=request.session_id,
                stream=False,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return result
            
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tokens/count")
async def count_tokens(request: TokenCountRequest):
    """Count tokens for text or messages."""
    try:
        if request.text:
            token_count = tokenizer_service.count_tokens(request.text, request.model)
        elif request.messages:
            messages = [msg.dict() for msg in request.messages]
            token_count = tokenizer_service.count_tokens(messages, request.model)
        else:
            raise ValueError("Either text or messages must be provided")
        
        # Get model info for context
        model_info = MODEL_CONFIGS.get(request.model)
        
        return {
            "token_count": token_count,
            "model": request.model,
            "context_window": model_info.token_window.total_window if model_info else None,
            "percentage_used": (
                token_count / model_info.token_window.total_window * 100
                if model_info else None
            )
        }
        
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str) -> SessionInfoResponse:
    """Get information about a specific session."""
    session_info = context_engine.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionInfoResponse(**session_info)


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    return {
        "sessions": [
            context_engine.get_session_info(sid)
            for sid in context_engine.sessions.keys()
        ],
        "total": len(context_engine.sessions)
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in context_engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del context_engine.sessions[session_id]
    return {"message": f"Session {session_id} deleted"}


@app.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    return llm_gateway.get_metrics()


@app.get("/models")
async def list_models():
    """List available models and their token windows."""
    return {
        "models": {
            name: {
                "name": info.name,
                "provider": info.provider,
                "input_window": info.token_window.input_window,
                "max_output_window": info.token_window.max_output_window,
                "total_window": info.token_window.total_window,
                "supports_streaming": info.supports_streaming,
                "supports_vision": info.supports_vision,
                "cost_per_1k_input": info.cost_per_1k_input,
                "cost_per_1k_output": info.cost_per_1k_output
            }
            for name, info in MODEL_CONFIGS.items()
        }
    }


@app.post("/sessions/cleanup")
async def cleanup_sessions(background_tasks: BackgroundTasks, max_age_hours: int = 24):
    """Clean up old inactive sessions."""
    background_tasks.add_task(
        context_engine.cleanup_old_sessions,
        max_age_hours
    )
    return {"message": f"Cleanup initiated for sessions older than {max_age_hours} hours"}


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")


# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    logger.info("Token Window Management System starting up...")
    # Could initialize connections, load models, etc.


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Token Window Management System shutting down...")
    # Save any persistent state if needed
