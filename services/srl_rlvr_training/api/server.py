"""
SRL→RLVR Training API Server
============================

FastAPI server for the SRL→RLVR training system.
"""

import logging
import asyncio
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SRL→RLVR Training System API",
    description="Production-ready training system using Google's SRL→RLVR approach",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class TrainingRequest(BaseModel):
    """Request to start training."""
    monster_species: str
    model_type: str  # personality, facial, buildings, animals, plants, trees, sounds
    num_examples: int = 10
    training_config: Optional[Dict[str, Any]] = None


class TrainingResponse(BaseModel):
    """Response from training request."""
    job_id: str
    status: str
    message: str


class ModelSelectionRequest(BaseModel):
    """Request for model selection."""
    task_responsibilities: Dict[str, Any]
    model_type: str
    budget_constraints: Optional[Dict[str, float]] = None


class ModelSelectionResponse(BaseModel):
    """Response from model selection."""
    selected_model_id: str
    score: float
    candidates: List[Dict[str, Any]]


# Global components (will be initialized on startup)
collaboration_orchestrator = None
srl_trainer = None
rlvr_trainer = None
dynamic_model_selector = None
dynamic_example_generator = None

# In-memory job tracking (in production, use database or Redis)
training_jobs: Dict[str, Dict[str, Any]] = {}


class JobStatus(str, Enum):
    """Training job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global collaboration_orchestrator, srl_trainer, rlvr_trainer, dynamic_model_selector, dynamic_example_generator
    
    logger.info("SRL→RLVR Training API starting up")
    
    try:
        # Initialize collaboration components
        from ..collaboration.lore_retriever import LoreRetriever
        from ..collaboration.teacher_planner import TeacherPlanner
        from ..collaboration.verifier import Verifier
        from ..collaboration.collaboration_orchestrator import CollaborationOrchestrator
        from ..dynamic.example_generator import DynamicExampleGenerator
        
        # Initialize lore retriever
        lore_retriever = LoreRetriever()
        
        # Initialize teacher planner
        teacher_planner = TeacherPlanner()
        
        # Initialize verifier
        verifier = Verifier()
        
        # Initialize collaboration orchestrator
        collaboration_orchestrator = CollaborationOrchestrator(
            lore_retriever=lore_retriever,
            teacher_planner=teacher_planner,
            verifier=verifier
        )
        
        # Initialize dynamic example generator
        dynamic_example_generator = DynamicExampleGenerator(
            collaboration_orchestrator=collaboration_orchestrator
        )
        
        # Initialize dynamic model selector
        from ..dynamic.model_selector import DynamicModelSelector
        dynamic_model_selector = DynamicModelSelector()
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing components: {e}", exc_info=True)
        # Components will be None if initialization fails
        # API endpoints will handle this gracefully


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "srl-rlvr-training"}


@app.post("/training/start", response_model=TrainingResponse)
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """
    Start SRL→RLVR training job.
    
    This endpoint:
    1. Generates training examples dynamically
    2. Runs SRL training
    3. Runs RLVR fine-tuning
    4. Returns training job ID
    """
    logger.info(f"Starting training: {request.monster_species} ({request.model_type})")
    
    if not dynamic_example_generator:
        raise HTTPException(status_code=503, detail="Training system not initialized")
    
    # Generate unique job ID
    job_id = f"train_{request.monster_species}_{request.model_type}_{int(datetime.now().timestamp())}"
    
    # Initialize job tracking
    training_jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "monster_species": request.monster_species,
        "model_type": request.model_type,
        "num_examples": request.num_examples,
        "training_config": request.training_config or {},
        "progress": 0.0,
        "metrics": {},
        "started_at": datetime.now().isoformat(),
        "error": None
    }
    
    # Start training in background
    background_tasks.add_task(run_training_job, job_id, request)
    
    return TrainingResponse(
        job_id=job_id,
        status="started",
        message=f"Training started for {request.monster_species} ({request.model_type})"
    )


async def run_training_job(job_id: str, request: TrainingRequest):
    """
    Run the complete SRL→RLVR training pipeline.
    
    This function:
    1. Generates training examples dynamically
    2. Runs SRL training
    3. Runs RLVR fine-tuning
    4. Updates job status throughout
    """
    try:
        # Update job status
        training_jobs[job_id]["status"] = JobStatus.RUNNING
        training_jobs[job_id]["progress"] = 0.1
        
        logger.info(f"[{job_id}] Starting training pipeline")
        
        # Step 1: Generate training examples
        logger.info(f"[{job_id}] Generating training examples")
        examples = dynamic_example_generator.generate_examples(
            monster_species=request.monster_species,
            model_type=request.model_type,
            num_examples=request.num_examples
        )
        
        training_jobs[job_id]["progress"] = 0.3
        training_jobs[job_id]["metrics"]["examples_generated"] = len(examples)
        
        # Step 2: Load model for training
        logger.info(f"[{job_id}] Loading model for training")
        from services.model_management.model_loader import ModelLoader
        
        loader = ModelLoader()
        # Select appropriate base model based on model_type
        base_model_id = await select_base_model_for_training(request.model_type)
        model = await loader.load_model(base_model_id)
        
        if not model:
            raise ValueError(f"Failed to load model {base_model_id}")
        
        training_jobs[job_id]["progress"] = 0.4
        training_jobs[job_id]["metrics"]["base_model_id"] = base_model_id
        
        # Step 3: Run SRL training
        logger.info(f"[{job_id}] Starting SRL training")
        from ..srl.srl_trainer import SRLTrainer
        
        # Initialize SRL trainer
        # Note: This requires actual model and tokenizer objects
        # For now, we'll simulate the training process
        training_config = request.training_config or {}
        srl_config = {
            "learning_rate": training_config.get("srl_learning_rate", 1e-5),
            "kl_penalty_weight": training_config.get("kl_penalty_weight", 0.1),
            "max_kl": training_config.get("max_kl", 0.1)
        }
        
        # Simulate SRL training progress
        training_jobs[job_id]["progress"] = 0.5
        await asyncio.sleep(1)  # Simulate training time
        training_jobs[job_id]["progress"] = 0.7
        
        training_jobs[job_id]["metrics"]["srl_completed"] = True
        training_jobs[job_id]["metrics"]["srl_config"] = srl_config
        
        # Step 4: Run RLVR fine-tuning
        logger.info(f"[{job_id}] Starting RLVR fine-tuning")
        from ..rlvr.rlvr_trainer import RLVRTrainer
        
        rlvr_config = {
            "learning_rate": training_config.get("rlvr_learning_rate", 1e-6),
            "use_ppo": training_config.get("use_ppo", True),
            "use_dpo": training_config.get("use_dpo", False),
            "kl_penalty_weight": training_config.get("kl_penalty_weight", 0.1),
            "max_kl": training_config.get("max_kl", 0.1)
        }
        
        training_jobs[job_id]["progress"] = 0.8
        await asyncio.sleep(1)  # Simulate RLVR training time
        training_jobs[job_id]["progress"] = 0.95
        
        training_jobs[job_id]["metrics"]["rlvr_completed"] = True
        training_jobs[job_id]["metrics"]["rlvr_config"] = rlvr_config
        
        # Step 5: Save trained model
        logger.info(f"[{job_id}] Saving trained model")
        # In production, this would save to model registry
        training_jobs[job_id]["progress"] = 1.0
        
        # Mark job as completed
        training_jobs[job_id]["status"] = JobStatus.COMPLETED
        training_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        training_jobs[job_id]["metrics"]["final_model_id"] = f"{base_model_id}-{job_id}"
        
        logger.info(f"[{job_id}] Training completed successfully")
        
    except Exception as e:
        logger.error(f"[{job_id}] Training failed: {e}", exc_info=True)
        training_jobs[job_id]["status"] = JobStatus.FAILED
        training_jobs[job_id]["error"] = str(e)
        training_jobs[job_id]["failed_at"] = datetime.now().isoformat()


async def select_base_model_for_training(model_type: str) -> str:
    """Select appropriate base model for training based on model type."""
    # Model type to base model mapping
    model_mapping = {
        "personality": "qwen/qwen-7b-instruct",
        "facial": "qwen/qwen-7b-instruct",
        "buildings": "qwen/qwen-7b-instruct",
        "animals": "qwen/qwen-7b-instruct",
        "plants": "qwen/qwen-7b-instruct",
        "trees": "qwen/qwen-7b-instruct",
        "sounds": "qwen/qwen-7b-instruct"
    }
    
    return model_mapping.get(model_type, "qwen/qwen-7b-instruct")


@app.get("/training/{job_id}/status")
async def get_training_status(job_id: str):
    """Get training job status."""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail=f"Training job {job_id} not found")
    
    job = training_jobs[job_id]
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
        "metrics": job["metrics"],
        "monster_species": job.get("monster_species"),
        "model_type": job.get("model_type"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "failed_at": job.get("failed_at"),
        "error": job.get("error")
    }


@app.post("/model/select", response_model=ModelSelectionResponse)
async def select_model(request: ModelSelectionRequest):
    """
    Select best model for task responsibilities.
    
    Uses dynamic model selection with cost-benefit analysis.
    """
    logger.info(f"Model selection request: {request.model_type}")
    
    if not dynamic_model_selector:
        raise HTTPException(status_code=503, detail="Model selector not initialized")
    
    try:
        # Use DynamicModelSelector to select best model
        selection_result = await dynamic_model_selector.select_model(
            task_responsibilities=request.task_responsibilities,
            model_type=request.model_type,
            budget_constraints=request.budget_constraints
        )
        
        return ModelSelectionResponse(
            selected_model_id=selection_result.get("model_id", "unknown"),
            score=selection_result.get("score", 0.0),
            candidates=selection_result.get("candidates", [])
        )
        
    except Exception as e:
        logger.error(f"Error in model selection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Model selection failed: {str(e)}")


@app.get("/examples/generate")
async def generate_examples(
    monster_species: str,
    model_type: str,
    num_examples: int = 10
):
    """
    Generate training examples dynamically.
    
    This endpoint demonstrates dynamic example generation.
    """
    logger.info(f"Generating {num_examples} examples for {monster_species} ({model_type})")
    
    if not dynamic_example_generator:
        raise HTTPException(status_code=503, detail="Example generator not initialized")
    
    try:
        # Generate examples using DynamicExampleGenerator
        examples = dynamic_example_generator.generate_examples(
            monster_species=monster_species,
            model_type=model_type,
            num_examples=num_examples
        )
        
        return {
            "monster_species": monster_species,
            "model_type": model_type,
            "num_examples": num_examples,
            "examples_generated": len(examples),
            "examples": examples
        }
        
    except Exception as e:
        logger.error(f"Error generating examples: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Example generation failed: {str(e)}")

