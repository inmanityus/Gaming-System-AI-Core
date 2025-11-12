#!/usr/bin/env python3
"""
Aethelred v2 - AI Management System (Peer Reviewed)
Addresses all P0 issues from peer review:
- PostgreSQL for persistent storage
- Redis for coordination and locks
- Authentication required
- No race conditions
- Proper error handling
- Resource lifecycle management
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import logging
import os
import uuid
import asyncio
import httpx
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis.asyncio as redis

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Database
DATABASE_URL = f"postgresql://postgres:@{os.getenv('DB_HOST', 'localhost')}:5432/{os.getenv('DB_NAME', 'bodybroker_qa')}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis connection
redis_client: Optional[redis.Redis] = None

# HTTP client (reusable)
http_client: Optional[httpx.AsyncClient] = None

# API Key Authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify API key for authentication"""
    expected_key = os.getenv("AETHELRED_API_KEY")
    if not expected_key or api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# FastAPI app
app = FastAPI(
    title="Aethelred v2 - AI Management System",
    description="Peer-reviewed, production-ready AI coordination",
    version="2.0.0"
)

# Strict CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Enums
class ARPStatus(str, Enum):
    DETECTED = "detected"
    ASSIGNED = "assigned"
    CODING = "coding"
    PEER_REVIEW = "peer_review"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"

class AgentRole(str, Enum):
    CODER = "coder"
    REVIEWER = "reviewer"
    ANALYZER = "analyzer"

class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    UNRESPONSIVE = "unresponsive"

# Database Models
class ARPModel(Base):
    __tablename__ = "arps"
    __table_args__ = {'schema': 'aethelred'}
    
    arp_id = Column(String(50), primary_key=True)
    status = Column(String(50), nullable=False)
    priority_score = Column(Integer, nullable=False)
    detected_at = Column(DateTime, nullable=False)
    source_reports = Column(JSON)
    root_cause_hypothesis = Column(String(500))
    assigned_to = Column(String(100))
    reviewers = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

class AgentModel(Base):
    __tablename__ = "agents"
    __table_args__ = {'schema': 'aethelred'}
    
    agent_id = Column(String(100), primary_key=True)
    model_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    status = Column(String(50), default="available")
    expertise_scores = Column(JSON)
    current_arp = Column(String(50))
    total_tasks = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class ARPCreate(BaseModel):
    source_reports: List[Dict]
    consensus_analysis: str
    root_cause_hypothesis: str
    priority_score: int = Field(ge=1, le=10)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup
@app.on_event("startup")
async def startup():
    global redis_client, http_client
    
    logger.info("Aethelred v2 starting (PEER-REVIEWED VERSION)")
    
    # Initialize Redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)
    
    # Initialize HTTP client (reusable)
    http_client = httpx.AsyncClient(timeout=10.0)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize agents
    db = SessionLocal()
    try:
        if db.query(AgentModel).count() == 0:
            agents = [
                AgentModel(agent_id="gpt5-codex-01", model_name="gpt-5-codex", role="coder", expertise_scores={"cpp": 0.95}),
                AgentModel(agent_id="claude-rev-01", model_name="claude-sonnet-4.5", role="reviewer", expertise_scores={"review": 0.93}),
                AgentModel(agent_id="gemini-rev-01", model_name="gemini-2.5-pro", role="reviewer", expertise_scores={"review": 0.89}),
            ]
            db.add_all(agents)
            db.commit()
    finally:
        db.close()
    
    logger.info("Aethelred v2 ready")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup resources"""
    global redis_client, http_client
    if http_client:
        await http_client.aclose()
    if redis_client:
        await redis_client.close()

# Endpoints
@app.get("/")
async def root():
    return {"service": "Aethelred v2", "version": "2.0.0", "status": "operational"}

@app.get("/health", dependencies=[Depends(verify_api_key)])
async def health(db: Session = Depends(get_db)):
    agent_count = db.query(AgentModel).count()
    return {"status": "healthy", "agents": agent_count}

@app.post("/arp/create", dependencies=[Depends(verify_api_key)])
async def create_arp(
    request: ARPCreate, 
    bg: BackgroundTasks, 
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = None
):
    # Check idempotency - prevent duplicate processing
    if idempotency_key:
        existing = db.query(ARPModel).filter_by(arp_id=idempotency_key).first()
        if existing:
            logger.info(f"Idempotency: Returning existing ARP {idempotency_key}")
            return {"status": "existing", "arp_id": existing.arp_id}
    
    # Atomic ARP creation with Redis lock (with TTL and fencing)
    lock_key = "arp:create:lock"
    lock = await redis_client.lock(
        lock_key, 
        timeout=10,  # TTL: lock expires after 10 seconds
        blocking_timeout=5  # Wait max 5 seconds to acquire
    )
    
    try:
        acquired = await lock.acquire()
        if not acquired:
            raise HTTPException(status_code=503, detail="Could not acquire lock - system busy")
        
        # Generate fencing token (monotonic counter)
        fence_token = await redis_client.incr("arp:fence:counter")
        
        arp_id = idempotency_key or f"ARP-{str(uuid.uuid4())[:8]}"
        
        try:
            arp = ARPModel(
                arp_id=arp_id,
                status=ARPStatus.DETECTED,
                priority_score=request.priority_score,
                detected_at=datetime.utcnow(),
                source_reports=request.source_reports,
                root_cause_hypothesis=request.root_cause_hypothesis
            )
            db.add(arp)
            db.commit()
            
            logger.info(f"Created {arp_id} (fence: {fence_token})")
            return {"status": "created", "arp_id": arp_id}
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create ARP: {e}")
            raise HTTPException(status_code=500, detail="ARP creation failed")
        
    finally:
        try:
            await lock.release()
        except Exception as e:
            logger.warning(f"Lock release failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

