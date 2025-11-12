#!/usr/bin/env python3
"""
Aethelred - AI Management System
Coordinates all AI agents in autonomous development workflow
Part of AADS (Autonomous AI Development System)

Functions:
- Manages ARPs (Autonomous Resolution Packets)
- Coordinates Development Swarm (coder + reviewer agents)
- Enforces 3+ model peer review
- Monitors agent health and performance
- Assigns tasks based on expertise
- Triggers deployments
- Ensures all AI models doing their jobs
- Looks for better AI model options
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import os
import uuid
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Aethelred - AI Management System",
    description="Coordinates autonomous AI development workflow for The Body Broker",
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


# ===== ENUMS =====

class ARPStatus(str, Enum):
    DETECTED = "detected"
    TRIAGING = "triaging"
    ASSIGNED = "assigned"
    CODING = "coding"
    PEER_REVIEW = "peer_review"
    EXPERT_REVIEW = "expert_review"
    REGRESSION_TESTING = "regression_testing"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    REJECTED = "rejected"


class AgentRole(str, Enum):
    CODER = "coder"
    REVIEWER = "reviewer"
    ANALYZER = "analyzer"
    DIAGNOSTICIAN = "diagnostician"


class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    UNRESPONSIVE = "unresponsive"
    OFFLINE = "offline"


# ===== MODELS =====

class ARP(BaseModel):
    """Autonomous Resolution Packet - AI-to-AI issue tracking"""
    arp_id: str = Field(default_factory=lambda: f"ARP-{str(uuid.uuid4())[:8]}")
    version: int = 1
    status: ARPStatus = ARPStatus.DETECTED
    priority_score: int = 0
    
    # Detection
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    source_reports: List[Dict] = []
    consensus_analysis: Optional[str] = None
    
    # Diagnosis
    root_cause_hypothesis: Optional[str] = None
    affected_systems: List[str] = []
    likely_files: List[str] = []
    
    # Assignment
    assigned_to: Optional[str] = None  # Agent ID
    assigned_at: Optional[datetime] = None
    reviewers: List[str] = []
    
    # Development
    solution_plan: Optional[str] = None
    code_iterations: List[Dict] = []
    final_patch: Optional[str] = None
    
    # Expert Oversight
    janus_vetting: Optional[Dict] = None
    janus_final_review: Optional[Dict] = None
    
    # Testing
    regression_tests: Optional[Dict] = None
    
    # Deployment
    deployment_history: List[Dict] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class Agent(BaseModel):
    """AI Agent in the Development Swarm"""
    agent_id: str
    model_name: str  # "gpt-5-codex", "claude-sonnet-4.5", "gemini-2.5-pro"
    role: AgentRole
    status: AgentStatus = AgentStatus.AVAILABLE
    expertise_scores: Dict[str, float] = {}  # {"pathfinding": 0.92, "ui": 0.87}
    current_arp: Optional[str] = None
    total_tasks_completed: int = 0
    success_rate: float = 1.0
    average_completion_time_hours: float = 0.0
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)


class ARPCreateRequest(BaseModel):
    """Request to create new ARP from Consensus Engine"""
    source_reports: List[Dict]
    consensus_analysis: str
    root_cause_hypothesis: str
    affected_systems: List[str]
    priority_score: int


class AgentAssignment(BaseModel):
    """Assignment of ARP to Development Swarm"""
    arp_id: str
    lead_coder: str  # Agent ID
    reviewers: List[str]  # Agent IDs (minimum 2)


# ===== IN-MEMORY STORAGE (Replace with PostgreSQL) =====

arps_db: Dict[str, ARP] = {}
agents_db: Dict[str, Agent] = {}


# ===== INITIALIZATION =====

def initialize_agents():
    """Initialize AI agent pool"""
    # Coder agents
    agents_db["gpt5-codex-01"] = Agent(
        agent_id="gpt5-codex-01",
        model_name="gpt-5-codex",
        role=AgentRole.CODER,
        expertise_scores={"c++": 0.95, "blueprints": 0.85, "python": 0.92}
    )
    
    # Reviewer agents
    agents_db["claude-reviewer-01"] = Agent(
        agent_id="claude-reviewer-01",
        model_name="claude-sonnet-4.5",
        role=AgentRole.REVIEWER,
        expertise_scores={"code_review": 0.93, "security": 0.90}
    )
    
    agents_db["gemini-reviewer-01"] = Agent(
        agent_id="gemini-reviewer-01",
        model_name="gemini-2.5-pro",
        role=AgentRole.REVIEWER,
        expertise_scores={"code_review": 0.89, "architecture": 0.92}
    )
    
    agents_db["deepseek-reviewer-01"] = Agent(
        agent_id="deepseek-reviewer-01",
        model_name="deepseek-v3",
        role=AgentRole.REVIEWER,
        expertise_scores={"code_review": 0.87, "performance": 0.91}
    )
    
    # Analyzer agents (vision)
    agents_db["gpt5-analyzer-01"] = Agent(
        agent_id="gpt5-analyzer-01",
        model_name="gpt-5",
        role=AgentRole.ANALYZER,
        expertise_scores={"ux": 0.94, "ui": 0.90}
    )
    
    agents_db["gemini-analyzer-01"] = Agent(
        agent_id="gemini-analyzer-01",
        model_name="gemini-2.5-pro",
        role=AgentRole.ANALYZER,
        expertise_scores={"atmosphere": 0.96, "visuals": 0.92}
    )
    
    agents_db["claude-analyzer-01"] = Agent(
        agent_id="claude-analyzer-01",
        model_name="claude-sonnet-4.5",
        role=AgentRole.ANALYZER,
        expertise_scores={"bugs": 0.91, "visual_quality": 0.88}
    )
    
    logger.info(f"Initialized {len(agents_db)} AI agents")


@app.on_event("startup")
async def startup():
    """Initialize Aethelred on startup"""
    logger.info("="*60)
    logger.info("AETHELRED - AI Management System Starting")
    logger.info("="*60)
    initialize_agents()
    logger.info(f"Managing {len(agents_db)} AI agents")
    logger.info("Ready to coordinate autonomous development")
    logger.info("="*60)


# ===== API ENDPOINTS =====

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Aethelred - AI Management System",
        "version": "1.0.0",
        "status": "operational",
        "agents_managed": len(agents_db),
        "active_arps": len([a for a in arps_db.values() if a.status not in [ARPStatus.DEPLOYED, ARPStatus.REJECTED, ARPStatus.FAILED]]),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    available_agents = len([a for a in agents_db.values() if a.status == AgentStatus.AVAILABLE])
    busy_agents = len([a for a in agents_db.values() if a.status == AgentStatus.BUSY])
    unresponsive_agents = len([a for a in agents_db.values() if a.status == AgentStatus.UNRESPONSIVE])
    
    return {
        "status": "healthy",
        "agents": {
            "total": len(agents_db),
            "available": available_agents,
            "busy": busy_agents,
            "unresponsive": unresponsive_agents
        },
        "arps": {
            "total": len(arps_db),
            "active": len([a for a in arps_db.values() if a.status not in [ARPStatus.DEPLOYED, ARPStatus.REJECTED, ARPStatus.FAILED]]),
            "deployed": len([a for a in arps_db.values() if a.status == ARPStatus.DEPLOYED])
        }
    }


@app.post("/arp/create")
async def create_arp(
    request: ARPCreateRequest,
    background_tasks: BackgroundTasks
):
    """
    Create new ARP from Consensus Engine
    Automatically assigns to Development Swarm
    """
    arp = ARP(
        source_reports=request.source_reports,
        consensus_analysis=request.consensus_analysis,
        root_cause_hypothesis=request.root_cause_hypothesis,
        affected_systems=request.affected_systems,
        priority_score=request.priority_score
    )
    
    arps_db[arp.arp_id] = arp
    
    logger.info(f"Created {arp.arp_id}: {arp.root_cause_hypothesis}")
    logger.info(f"Priority: {arp.priority_score}, Systems: {arp.affected_systems}")
    
    # Automatically assign to Development Swarm
    background_tasks.add_task(assign_arp_to_swarm, arp.arp_id)
    
    return {
        "status": "created",
        "arp_id": arp.arp_id,
        "message": "ARP created and assigned to Development Swarm"
    }


async def assign_arp_to_swarm(arp_id: str):
    """
    Assign ARP to Development Swarm
    Selects lead coder + minimum 2 reviewers based on expertise
    """
    if arp_id not in arps_db:
        logger.error(f"ARP {arp_id} not found")
        return
    
    arp = arps_db[arp_id]
    arp.status = ARPStatus.ASSIGNED
    
    # Select lead coder (best coder agent available)
    available_coders = [a for a in agents_db.values() if a.role == AgentRole.CODER and a.status == AgentStatus.AVAILABLE]
    
    if not available_coders:
        logger.warning(f"No available coder agents for {arp_id}")
        return
    
    # Select based on expertise in affected systems
    lead_coder = max(available_coders, key=lambda a: sum(a.expertise_scores.get(sys, 0.5) for sys in arp.affected_systems))
    
    # Select minimum 2 reviewers (different model families)
    available_reviewers = [a for a in agents_db.values() if a.role == AgentRole.REVIEWER and a.status == AgentStatus.AVAILABLE]
    
    # Ensure diversity: different model families
    selected_reviewers = []
    used_models = {lead_coder.model_name.split('-')[0]}  # e.g., "gpt5" from "gpt5-codex-01"
    
    for reviewer in available_reviewers:
        reviewer_family = reviewer.model_name.split('-')[0]
        if reviewer_family not in used_models and len(selected_reviewers) < 3:
            selected_reviewers.append(reviewer)
            used_models.add(reviewer_family)
    
    if len(selected_reviewers) < 2:
        logger.error(f"Insufficient diverse reviewers for {arp_id} (need 2, have {len(selected_reviewers)})")
        return
    
    # Assign
    arp.assigned_to = lead_coder.agent_id
    arp.reviewers = [r.agent_id for r in selected_reviewers]
    arp.assigned_at = datetime.utcnow()
    
    # Update agent statuses
    lead_coder.status = AgentStatus.BUSY
    lead_coder.current_arp = arp_id
    for reviewer in selected_reviewers:
        reviewer.status = AgentStatus.BUSY
        reviewer.current_arp = arp_id
    
    logger.info(f"Assigned {arp_id} to Development Swarm:")
    logger.info(f"  Lead Coder: {lead_coder.agent_id} ({lead_coder.model_name})")
    logger.info(f"  Reviewers: {', '.join(r.agent_id + ' (' + r.model_name + ')' for r in selected_reviewers)}")
    
    # TODO: Notify agents via API calls to trigger development


@app.get("/arp")
async def list_arps(
    status: Optional[ARPStatus] = None,
    limit: int = 50
):
    """List ARPs with optional status filter"""
    arps = list(arps_db.values())
    
    if status:
        arps = [a for a in arps if a.status == status]
    
    # Sort by priority (highest first), then by created_at (newest first)
    arps.sort(key=lambda a: (-a.priority_score, -a.created_at.timestamp()))
    
    return {
        "total": len(arps),
        "arps": [a.dict() for a in arps[:limit]]
    }


@app.get("/arp/{arp_id}")
async def get_arp(arp_id: str):
    """Get detailed ARP information"""
    if arp_id not in arps_db:
        raise HTTPException(status_code=404, detail="ARP not found")
    
    arp = arps_db[arp_id]
    
    # Add agent details
    response = arp.dict()
    if arp.assigned_to:
        response["lead_coder_details"] = agents_db.get(arp.assigned_to, {})
    if arp.reviewers:
        response["reviewer_details"] = [agents_db.get(r, {}) for r in arp.reviewers]
    
    return response


@app.patch("/arp/{arp_id}/status")
async def update_arp_status(arp_id: str, status: ARPStatus):
    """Update ARP status"""
    if arp_id not in arps_db:
        raise HTTPException(status_code=404, detail="ARP not found")
    
    arp = arps_db[arp_id]
    old_status = arp.status
    arp.status = status
    arp.updated_at = datetime.utcnow()
    
    if status == ARPStatus.DEPLOYED:
        arp.resolved_at = datetime.utcnow()
    
    logger.info(f"{arp_id} status: {old_status} → {status}")
    
    return {"status": "updated", "arp_id": arp_id, "new_status": status}


@app.get("/agents")
async def list_agents(
    role: Optional[AgentRole] = None,
    status: Optional[AgentStatus] = None
):
    """List all AI agents"""
    agents = list(agents_db.values())
    
    if role:
        agents = [a for a in agents if a.role == role]
    if status:
        agents = [a for a in agents if a.status == status]
    
    return {
        "total": len(agents),
        "agents": [a.dict() for a in agents]
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get detailed agent information"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    # Add current ARP details if working on one
    response = agent.dict()
    if agent.current_arp:
        response["current_arp_details"] = arps_db.get(agent.current_arp, {})
    
    return response


@app.get("/agents/{agent_id}/expertise")
async def get_agent_expertise(agent_id: str):
    """Get agent expertise scores and performance history"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    return {
        "agent_id": agent.agent_id,
        "model_name": agent.model_name,
        "role": agent.role,
        "expertise_scores": agent.expertise_scores,
        "performance": {
            "total_tasks": agent.total_tasks_completed,
            "success_rate": f"{agent.success_rate * 100:.1f}%",
            "avg_completion_hours": agent.average_completion_time_hours
        }
    }


@app.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str):
    """Agent reports it's alive and working"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    agent.last_heartbeat = datetime.utcnow()
    
    # Check if agent was marked unresponsive, restore to busy/available
    if agent.status == AgentStatus.UNRESPONSIVE:
        agent.status = AgentStatus.BUSY if agent.current_arp else AgentStatus.AVAILABLE
        logger.info(f"Agent {agent_id} recovered from unresponsive state")
    
    return {"status": "acknowledged", "agent_id": agent_id}


@app.get("/stats")
async def get_statistics():
    """Get Aethelred statistics"""
    total_arps = len(arps_db)
    active_arps = len([a for a in arps_db.values() if a.status not in [ARPStatus.DEPLOYED, ARPStatus.REJECTED, ARPStatus.FAILED]])
    deployed_arps = len([a for a in arps_db.values() if a.status == ARPStatus.DEPLOYED])
    
    available_agents = len([a for a in agents_db.values() if a.status == AgentStatus.AVAILABLE])
    busy_agents = len([a for a in agents_db.values() if a.status == AgentStatus.BUSY])
    
    return {
        "arps": {
            "total": total_arps,
            "active": active_arps,
            "deployed": deployed_arps,
            "failed": len([a for a in arps_db.values() if a.status == ARPStatus.FAILED])
        },
        "agents": {
            "total": len(agents_db),
            "available": available_agents,
            "busy": busy_agents,
            "unresponsive": len([a for a in agents_db.values() if a.status == AgentStatus.UNRESPONSIVE])
        },
        "performance": {
            "avg_resolution_time_hours": calculate_avg_resolution_time(),
            "success_rate": calculate_overall_success_rate()
        }
    }


def calculate_avg_resolution_time() -> float:
    """Calculate average time to resolve ARPs"""
    resolved = [a for a in arps_db.values() if a.status == ARPStatus.DEPLOYED and a.resolved_at]
    if not resolved:
        return 0.0
    
    total_hours = sum((a.resolved_at - a.created_at).total_seconds() / 3600 for a in resolved)
    return total_hours / len(resolved)


def calculate_overall_success_rate() -> float:
    """Calculate overall ARP success rate"""
    completed = [a for a in arps_db.values() if a.status in [ARPStatus.DEPLOYED, ARPStatus.FAILED, ARPStatus.REJECTED]]
    if not completed:
        return 1.0
    
    successful = len([a for a in completed if a.status == ARPStatus.DEPLOYED])
    return successful / len(completed)


# ===== BACKGROUND TASKS =====

@app.on_event("startup")
async def start_health_monitor():
    """Start background health monitoring of agents"""
    asyncio.create_task(monitor_agent_health())


async def monitor_agent_health():
    """Monitor agent health every 60 seconds"""
    while True:
        await asyncio.sleep(60)
        
        current_time = datetime.utcnow()
        
        for agent in agents_db.values():
            # Check if agent hasn't sent heartbeat in 5 minutes
            time_since_heartbeat = (current_time - agent.last_heartbeat).total_seconds()
            
            if time_since_heartbeat > 300 and agent.status != AgentStatus.OFFLINE:
                logger.warning(f"Agent {agent.agent_id} unresponsive (no heartbeat for {time_since_heartbeat/60:.1f} min)")
                agent.status = AgentStatus.UNRESPONSIVE
                
                # Re-assign any ARPs this agent was working on
                if agent.current_arp:
                    await reassign_arp(agent.current_arp, reason=f"Agent {agent.agent_id} unresponsive")


async def reassign_arp(arp_id: str, reason: str):
    """Re-assign ARP to different agent"""
    if arp_id not in arps_db:
        return
    
    arp = arps_db[arp_id]
    logger.info(f"Re-assigning {arp_id}: {reason}")
    
    # Mark old agent as available
    if arp.assigned_to and arp.assigned_to in agents_db:
        old_agent = agents_db[arp.assigned_to]
        old_agent.status = AgentStatus.AVAILABLE
        old_agent.current_arp = None
    
    # Re-assign using same logic
    await assign_arp_to_swarm(arp_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

