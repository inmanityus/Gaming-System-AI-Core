"""
Knowledge Base API Service
Provides semantic search and world-scoped queries for storyteller.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncpg
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Knowledge Base API",
    description="Semantic search and knowledge retrieval for storyteller",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
postgres_pool = None


@app.on_event("startup")
async def startup():
    """Initialize database connection."""
    global postgres_pool
    postgres_pool = await asyncpg.create_pool(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5443')),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'Inn0vat1on!'),
        database=os.getenv('POSTGRES_DB', 'gaming_system_ai_core'),
        min_size=2,
        max_size=20
    )
    logger.info("✅ Connected to Knowledge Base")


@app.on_event("shutdown")
async def shutdown():
    """Close database connection."""
    global postgres_pool
    if postgres_pool:
        await postgres_pool.close()


# Request/Response Models
class SemanticSearchRequest(BaseModel):
    query: str
    match_threshold: float = 0.7
    match_count: int = 10
    document_types: Optional[List[str]] = None  # Filter by type


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
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search across narrative documents.
    Uses pgvector cosine similarity.
    """
    try:
        # Generate embedding for query
        # TODO: Integrate with embedding service
        # For now, return text-based search as fallback
        
        async with postgres_pool.acquire() as conn:
            # Text search fallback (until embeddings integrated)
            query = """
                SELECT 
                    id::text, 
                    title, 
                    content,
                    0.8 as similarity,  -- Placeholder
                    document_type,
                    source_file
                FROM narrative_documents
                WHERE content ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            
            rows = await conn.fetch(
                query,
                f"%{request.query}%",
                request.match_count
            )
            
            results = [
                SearchResult(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'][:500] + "..." if len(row['content']) > 500 else row['content'],
                    similarity=row['similarity'],
                    document_type=row['document_type'],
                    source_file=row['source_file']
                )
                for row in rows
            ]
            
            return results
    
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/concepts/create")
async def create_concept(
    name: str,
    concept_type: str,
    description: str,
    scope: str = 'global',
    world_id: Optional[UUID] = None
):
    """Create new narrative concept."""
    async with postgres_pool.acquire() as conn:
        concept_id = await conn.fetchval("""
            INSERT INTO narrative_concepts 
            (name, concept_type, description, scope, world_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, name, concept_type, description, scope, world_id)
        
        return {"id": str(concept_id), "status": "created"}


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

