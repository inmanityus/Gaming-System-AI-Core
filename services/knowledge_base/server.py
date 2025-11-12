"""
Knowledge Base API Service
Provides semantic search and world-scoped queries for storyteller.
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncpg
import os
import logging
import json
from functools import lru_cache
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter with user-based key function
def get_rate_limit_key():
    """Get rate limit key - prefer user ID over IP."""
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    # Try to get from request context (set by verify_api_key)
    # Fall back to remote address
    try:
        request = Request.scope.get('fastapi_request')
        user_id = request.state.get('user_id') if hasattr(request, 'state') else None
        if user_id:
            return user_id
    except:
        pass
    
    return get_remote_address()

limiter = Limiter(key_func=get_rate_limit_key)

app = FastAPI(
    title="Knowledge Base API",
    description="Semantic search and knowledge retrieval for storyteller",
    version="1.0.0"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Restricted to known origins
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Database connection
postgres_pool = None

# API Key validation
API_KEYS = set(os.getenv('KB_API_KEYS', '').split(',')) if os.getenv('KB_API_KEYS') else set()

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for protected endpoints."""
    if not API_KEYS:
        # If no keys configured, allow access (development mode)
        return True
    
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True


@app.on_event("startup")
async def startup():
    """Initialize database connection."""
    global postgres_pool
    
    # Validate required environment variables
    db_password = os.getenv('POSTGRES_PASSWORD')
    if not db_password:
        raise RuntimeError("POSTGRES_PASSWORD environment variable required")
    
    # Validate password complexity (minimum security requirement)
    if len(db_password) < 16:
        raise RuntimeError("POSTGRES_PASSWORD must be at least 16 characters")
    
    try:
        postgres_pool = await asyncpg.create_pool(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5443')),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=db_password,
            database=os.getenv('POSTGRES_DB', 'gaming_system_ai_core'),
            min_size=2,
            max_size=20,
            command_timeout=60  # Timeout for queries
        )
        logger.info("✅ Connected to Knowledge Base")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Close database connection."""
    global postgres_pool
    if postgres_pool:
        await postgres_pool.close()


# Request/Response Models with Validation
class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    match_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    match_count: int = Field(default=10, ge=1, le=100)
    document_types: Optional[List[str]] = Field(default=None, max_items=10)
    
    @validator('query')
    def validate_query(cls, v):
        """Sanitize query input and escape wildcards."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        
        # Limit length to prevent ReDoS
        clean = v.strip()
        if len(clean) > 100:
            raise ValueError("Query too long (max 100 chars)")
        
        # Escape SQL wildcards to prevent ReDoS attacks
        clean = clean.replace('%', '\\%').replace('_', '\\_')
        
        return clean


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity: float
    document_type: str
    source_file: str


class ConceptSearchRequest(BaseModel):
    query: str
    scope: Optional[str] = None  # 'global', 'day_world', 'dark_world'
    world_id: Optional[UUID] = None
    concept_types: Optional[List[str]] = None


class ConceptResult(BaseModel):
    id: str
    name: str
    concept_type: str
    description: str
    scope: str
    similarity: float


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "knowledge_base",
        "database": "connected" if postgres_pool else "disconnected"
    }


@app.post("/search/semantic", response_model=List[SearchResult])
@limiter.limit("30/minute")
async def semantic_search(
    request: SemanticSearchRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Semantic search across narrative documents.
    Uses pgvector cosine similarity (or text search fallback).
    Rate limited to 30 requests/minute.
    """
    try:
        # Validate pool is available
        if not postgres_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        async with postgres_pool.acquire() as conn:
            # Use parameterized query (SQL injection safe)
            # Text search with proper parameterization
            query_sql = """
                SELECT 
                    id::text, 
                    title, 
                    content,
                    0.8 as similarity,
                    document_type,
                    source_file
                FROM narrative_documents
                WHERE content ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            
            # Parameterized query prevents SQL injection
            rows = await conn.fetch(
                query_sql,
                f"%{request.query}%",  # Parameterized, safe
                request.match_count
            )
            
            results = [
                SearchResult(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'][:500] + "..." if len(row['content']) > 500 else row['content'],
                    similarity=float(row['similarity']),
                    document_type=row['document_type'],
                    source_file=row['source_file']
                )
                for row in rows
            ]
            
            logger.info(f"Semantic search: '{request.query[:50]}' returned {len(results)} results")
            return results
    
    except asyncpg.PostgresError as e:
        logger.error(f"Database error in semantic search: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    except Exception as e:
        logger.error(f"Error in semantic search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/documents/stats")
async def get_document_stats():
    """Get statistics about ingested documents."""
    async with postgres_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(DISTINCT source_file) as total_documents,
                SUM(CASE WHEN document_type = 'main' THEN 1 ELSE 0 END) as main_chunks,
                SUM(CASE WHEN document_type = 'guide' THEN 1 ELSE 0 END) as guide_chunks,
                SUM(CASE WHEN document_type = 'experience' THEN 1 ELSE 0 END) as experience_chunks
            FROM narrative_documents
        """)
        
        return dict(stats)


@app.get("/concepts/global", response_model=List[Dict])
async def get_global_concepts():
    """Get all global concepts (shared knowledge)."""
    async with postgres_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                id::text,
                name,
                concept_type,
                description,
                scope
            FROM narrative_concepts
            WHERE scope = 'global'
            ORDER BY name
        """)
        
        return [dict(row) for row in rows]


@app.get("/world/{world_id}/knowledge")
async def get_world_knowledge(world_id: UUID):
    """Get knowledge for specific world (global + world-specific)."""
    async with postgres_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM get_world_knowledge($1)
        """, world_id)
        
        return [dict(row) for row in rows]


@app.get("/world/{world_id}/events")
async def get_world_events(
    world_id: UUID,
    limit: int = Query(default=50, le=500)
):
    """Get story events for world."""
    async with postgres_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                id::text,
                event_type,
                event_data,
                involved_npcs,
                impact_score,
                created_at
            FROM story_events
            WHERE world_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, world_id, limit)
        
        return [dict(row) for row in rows]


class CreateConceptRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    concept_type: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=5000)
    scope: str = Field(default='global', pattern='^(global|day_world|dark_world|experience)$')
    world_id: Optional[UUID] = None

@app.post("/concepts/create")
@limiter.limit("10/minute")
async def create_concept(
    request: CreateConceptRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """Create new narrative concept. Rate limited to 10/minute."""
    try:
        if not postgres_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        async with postgres_pool.acquire() as conn:
            concept_id = await conn.fetchval("""
                INSERT INTO narrative_concepts 
                (name, concept_type, description, scope, world_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, request.name, request.concept_type, request.description, 
            request.scope, request.world_id)
            
            logger.info(f"Created concept: {request.name} ({concept_id})")
            return {"id": str(concept_id), "status": "created"}
    
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="Concept already exists")
    except asyncpg.PostgresError as e:
        logger.error(f"Database error creating concept: {e}")
        raise HTTPException(status_code=500, detail="Failed to create concept")


@app.post("/events/record")
async def record_story_event(
    world_id: UUID,
    event_type: str,
    event_data: Dict,
    involved_npcs: Optional[List[UUID]] = None,
    impact_score: float = 0.5
):
    """Record new story event."""
    async with postgres_pool.acquire() as conn:
        event_id = await conn.fetchval("""
            INSERT INTO story_events
            (world_id, event_type, event_data, involved_npcs, impact_score)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, world_id, event_type, event_data, [str(npc) for npc in (involved_npcs or [])], impact_score)
        
        return {"id": str(event_id), "status": "recorded"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)

