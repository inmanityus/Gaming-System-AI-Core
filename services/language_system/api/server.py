from __future__ import annotations

"""
Language System API Server
==========================

FastAPI server for language system endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from services.language_system.core.language_definition import LanguageDefinition, LanguageRegistry
from services.language_system.generation.sentence_generator import SentenceGenerator, SentenceRequest
from services.language_system.grpc_service.grpc_server import LanguageSystemGRPCServer

app = FastAPI(title="Language System API", version="1.0.0")

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

# Initialize components
language_registry = LanguageRegistry()
sentence_generator = SentenceGenerator()

# Initialize gRPC server (will be started separately if needed)
grpc_server = None

# Register all languages on startup
@app.on_event("startup")
async def register_languages():
    """Register all language definitions on startup."""
    try:
        from services.language_system.data.language_definitions import (
            create_vampire_language,
            create_werewolf_language,
            create_zombie_language,
            create_ghoul_language,
            create_lich_language,
            create_italian_language,
            create_french_language,
            create_spanish_language,
            create_common_language,
            create_music_language,
        )
        
        languages = [
            create_vampire_language(),
            create_werewolf_language(),
            create_zombie_language(),
            create_ghoul_language(),
            create_lich_language(),
            create_italian_language(),
            create_french_language(),
            create_spanish_language(),
            create_common_language(),
            create_music_language(),
        ]
        
        for language in languages:
            language_registry.register(language)
        
        print(f"Registered {len(languages)} languages")
    except Exception as e:
        print(f"Error registering languages: {e}")


class GenerateSentenceRequest(BaseModel):
    """Request for sentence generation."""
    language_name: str
    intent: str
    context: Optional[Dict[str, Any]] = None
    emotion: Optional[str] = None
    complexity: int = 1


@app.post("/v1/generate-sentence")
async def generate_sentence(request: GenerateSentenceRequest):
    """Generate a sentence in the specified language."""
    language = language_registry.get(request.language_name)
    if not language:
        raise HTTPException(status_code=404, detail=f"Language '{request.language_name}' not found")
    
    sentence_request = SentenceRequest(
        language=language,
        intent=request.intent,
        context=request.context or {},
        emotion=request.emotion,
        complexity=request.complexity,
    )
    
    sentence = sentence_generator.generate(sentence_request)
    
    return {
        "sentence": sentence,
        "language": request.language_name,
        "intent": request.intent,
    }


@app.get("/v1/languages")
async def list_languages():
    """List all available languages."""
    languages = language_registry.list_all()
    return {"languages": languages}


@app.get("/v1/languages/{language_name}")
async def get_language(language_name: str):
    """Get language definition."""
    language = language_registry.get(language_name)
    if not language:
        raise HTTPException(status_code=404, detail=f"Language '{language_name}' not found")
    
    return language.to_dict()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "language-system"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Language System API",
        "version": "1.0.0",
        "endpoints": {
            "generate_sentence": "/v1/generate-sentence",
            "list_languages": "/v1/languages",
            "get_language": "/v1/languages/{language_name}",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)



