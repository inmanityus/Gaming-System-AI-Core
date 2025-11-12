#!/usr/bin/env python3
"""
AWS Orchestration Service
Coordinates AI-driven game testing system
Part of Tier 2 Architecture
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import logging
import os
import json
import boto3
from enum import Enum
import asyncio

# Rate limiting (P0-3 CRITICAL FIX)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# P2: Observability
from services.observability import get_logger, ObservabilityService

# Configure logging (structured logging for P2)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = get_logger(__name__)

# Initialize rate limiter (P0-3 CRITICAL FIX)
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title="Body Broker QA Orchestrator",
    description="AI-Driven Game Testing Orchestration Service",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients with region configuration
AWS_REGION = os.getenv('AWS_REGION', os.getenv('S3_REGION', 'us-east-1'))
s3_client = boto3.client('s3', region_name=AWS_REGION)
sqs_client = boto3.client('sqs', region_name=AWS_REGION)
rds_client = boto3.client('rds', region_name=AWS_REGION)

# Configuration
CONFIG = {
    "s3_bucket": os.getenv("S3_BUCKET", "body-broker-qa-captures"),
    "sqs_queue_url": os.getenv("SQS_QUEUE_URL", ""),
    "database_host": os.getenv("DB_HOST", "localhost"),
    "database_name": os.getenv("DB_NAME", "body_broker_qa"),
}


# Models
class CaptureEventType(str, Enum):
    ON_PLAYER_DAMAGE = "OnPlayerDamage"
    ON_ENEMY_SPAWN = "OnEnemySpawn"
    ON_ENTER_NEW_ZONE = "OnEnterNewZone"
    ON_UI_POPUP = "OnUIPopup"
    ON_HARVEST_COMPLETE = "OnHarvestComplete"
    ON_NEGOTIATION_START = "OnNegotiationStart"
    ON_DEATH_TRIGGERED = "OnDeathTriggered"
    ON_COMBAT_START = "OnCombatStart"
    ON_COMBAT_END = "OnCombatEnd"
    BASELINE = "Baseline"


class NewCaptureRequest(BaseModel):
    capture_id: str = Field(..., description="Unique capture identifier")
    event_type: CaptureEventType = Field(..., description="Event that triggered capture")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    screenshot_key: str = Field(..., description="S3 key for screenshot")
    telemetry_key: str = Field(..., description="S3 key for telemetry JSON")
    s3_bucket: str = Field(..., description="S3 bucket name")


class VisionAnalysisRequest(BaseModel):
    capture_id: str
    screenshot_url: str
    telemetry_data: Dict
    priority: int = Field(default=0, description="Analysis priority (0-10)")


class VisionAnalysisResult(BaseModel):
    capture_id: str
    model_name: str  # "gemini-2.5-pro", "gpt-4o", "claude-sonnet-4.5"
    confidence: float  # 0.0-1.0
    is_issue: bool
    category: str  # "atmosphere", "ux", "visual_bug", "performance"
    description: str
    recommendations: Optional[List[str]] = None


class ConsensusResult(BaseModel):
    capture_id: str
    issue_flagged: bool
    consensus_models: List[str]  # Models that agreed
    average_confidence: float
    category: str
    description: str
    recommendations: List[str]


# In-memory storage (replace with PostgreSQL in production)
captures_db = {}
analysis_results_db = {}
consensus_results_db = []


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Body Broker QA Orchestrator",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    P2: Observability metrics for monitoring system health and performance.
    """
    return ObservabilityService.metrics_endpoint()


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "s3": check_s3_health(),
            "sqs": check_sqs_health(),
            "database": "not_implemented"
        },
        "stats": {
            "total_captures": len(captures_db),
            "total_analyses": len(analysis_results_db),
            "consensus_results": len(consensus_results_db)
        }
    }


def check_s3_health() -> str:
    """Check S3 bucket accessibility"""
    try:
        s3_client.head_bucket(Bucket=CONFIG["s3_bucket"])
        return "healthy"
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        return "unhealthy"


def check_sqs_health() -> str:
    """Check SQS queue accessibility"""
    if not CONFIG["sqs_queue_url"]:
        return "not_configured"
    try:
        sqs_client.get_queue_attributes(
            QueueUrl=CONFIG["sqs_queue_url"],
            AttributeNames=['All']
        )
        return "healthy"
    except Exception as e:
        logger.error(f"SQS health check failed: {e}")
        return "unhealthy"


@app.post("/captures/new")
async def register_new_capture(
    request: NewCaptureRequest,
    background_tasks: BackgroundTasks
):
    """
    Register new capture from Local Test Runner Agent
    Triggers vision analysis workflow
    """
    logger.info(f"New capture registered: {request.capture_id} - {request.event_type}")
    
    # Store capture metadata
    captures_db[request.capture_id] = {
        "capture_id": request.capture_id,
        "event_type": request.event_type,
        "timestamp": request.timestamp,
        "screenshot_key": request.screenshot_key,
        "telemetry_key": request.telemetry_key,
        "s3_bucket": request.s3_bucket,
        "status": "pending_analysis",
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Queue vision analysis (background task)
    background_tasks.add_task(
        trigger_vision_analysis,
        request.capture_id,
        request.screenshot_key,
        request.telemetry_key,
        request.s3_bucket
    )
    
    return {
        "status": "accepted",
        "capture_id": request.capture_id,
        "message": "Capture registered, vision analysis queued"
    }


async def trigger_vision_analysis(
    capture_id: str,
    screenshot_key: str,
    telemetry_key: str,
    s3_bucket: str
):
    """Trigger vision analysis for capture"""
    try:
        logger.info(f"Triggering vision analysis for: {capture_id}")
        
        # Get pre-signed URLs for vision models
        screenshot_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_bucket, 'Key': screenshot_key},
            ExpiresIn=3600
        )
        
        # Get telemetry data
        telemetry_obj = s3_client.get_object(Bucket=s3_bucket, Key=telemetry_key)
        telemetry_data = json.loads(telemetry_obj['Body'].read())
        
        # Queue for vision analysis (implement vision integration)
        # TODO: Call vision model APIs
        logger.info(f"Vision analysis queued: {capture_id}")
        
        # Update status
        if capture_id in captures_db:
            captures_db[capture_id]["status"] = "analyzing"
        
    except Exception as e:
        logger.error(f"Vision analysis failed for {capture_id}: {e}")
        if capture_id in captures_db:
            captures_db[capture_id]["status"] = "analysis_failed"
            captures_db[capture_id]["error"] = str(e)


@app.post("/analysis/submit")
async def submit_analysis_result(result: VisionAnalysisResult):
    """
    Receive analysis result from vision model
    Triggers consensus evaluation when all models have responded
    """
    logger.info(f"Analysis result from {result.model_name}: {result.capture_id}")
    
    # Store result
    if result.capture_id not in analysis_results_db:
        analysis_results_db[result.capture_id] = []
    
    analysis_results_db[result.capture_id].append(result.dict())
    
    # Check if we have all 3 model results
    results = analysis_results_db[result.capture_id]
    if len(results) >= 3:
        logger.info(f"All models responded for {result.capture_id} - running consensus")
        consensus = evaluate_consensus(result.capture_id, results)
        consensus_results_db.append(consensus)
        
        # Update capture status
        if result.capture_id in captures_db:
            captures_db[result.capture_id]["status"] = "complete"
            captures_db[result.capture_id]["issue_flagged"] = consensus["issue_flagged"]
    
    return {"status": "accepted", "capture_id": result.capture_id}


def evaluate_consensus(capture_id: str, results: List[Dict]) -> Dict:
    """
    Evaluate consensus across vision models
    Issue flagged only if ≥2 models agree AND average confidence >0.85
    """
    issue_results = [r for r in results if r["is_issue"]]
    
    consensus = {
        "capture_id": capture_id,
        "issue_flagged": False,
        "consensus_models": [],
        "average_confidence": 0.0,
        "category": "none",
        "description": "",
        "recommendations": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check consensus requirement: ≥2 models agree
    if len(issue_results) >= 2:
        # Calculate average confidence
        avg_confidence = sum(r["confidence"] for r in issue_results) / len(issue_results)
        
        # Check confidence threshold: >0.85
        if avg_confidence > 0.85:
            consensus["issue_flagged"] = True
            consensus["consensus_models"] = [r["model_name"] for r in issue_results]
            consensus["average_confidence"] = avg_confidence
            consensus["category"] = issue_results[0]["category"]
            consensus["description"] = issue_results[0]["description"]
            
            # Merge recommendations
            all_recs = []
            for r in issue_results:
                if r.get("recommendations"):
                    all_recs.extend(r["recommendations"])
            consensus["recommendations"] = list(set(all_recs))
            
            logger.info(f"ISSUE FLAGGED: {capture_id} - {consensus['category']} (confidence: {avg_confidence:.2f})")
    
    return consensus


@app.get("/captures/{capture_id}")
async def get_capture_details(capture_id: str):
    """Get details for specific capture"""
    if capture_id not in captures_db:
        raise HTTPException(status_code=404, detail="Capture not found")
    
    capture = captures_db[capture_id]
    
    # Add analysis results if available
    capture["analysis_results"] = analysis_results_db.get(capture_id, [])
    
    # Add consensus result if available
    consensus = next((c for c in consensus_results_db if c["capture_id"] == capture_id), None)
    if consensus:
        capture["consensus"] = consensus
    
    return capture


@app.get("/captures")
async def list_captures(
    event_type: Optional[CaptureEventType] = None,
    issue_flagged: Optional[bool] = None,
    limit: int = 50
):
    """List recent captures with optional filters"""
    captures = list(captures_db.values())
    
    # Filter by event type
    if event_type:
        captures = [c for c in captures if c["event_type"] == event_type]
    
    # Filter by issue status
    if issue_flagged is not None:
        captures = [c for c in captures if c.get("issue_flagged") == issue_flagged]
    
    # Sort by timestamp (newest first)
    captures.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "total": len(captures),
        "captures": captures[:limit]
    }


@app.get("/consensus/issues")
async def get_flagged_issues(limit: int = 100):
    """Get all flagged issues from consensus evaluation"""
    flagged = [c for c in consensus_results_db if c["issue_flagged"]]
    flagged.sort(key=lambda x: x["average_confidence"], reverse=True)
    
    return {
        "total": len(flagged),
        "issues": flagged[:limit]
    }


@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    total_captures = len(captures_db)
    analyzed = len([c for c in captures_db.values() if c["status"] == "complete"])
    issues_flagged = len([c for c in consensus_results_db if c["issue_flagged"]])
    
    # Category breakdown
    categories = {}
    for consensus in consensus_results_db:
        if consensus["issue_flagged"]:
            cat = consensus["category"]
            categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total_captures": total_captures,
        "analyzed": analyzed,
        "pending_analysis": total_captures - analyzed,
        "issues_flagged": issues_flagged,
        "issue_rate": issues_flagged / analyzed if analyzed > 0 else 0,
        "category_breakdown": categories
    }


# Report Generation Endpoints
from models.report import ReportGenerationRequest, Report, ReportFormat
from services.report_pipeline import create_report_pipeline
from services.storage_service import S3StorageService
from services.database_service import DatabaseService
from services.database_config import settings
from services.report_cache import ReportCache
import uuid

# P0-5 CRITICAL FIX: Initialize database service for persistent storage
database_service: Optional[DatabaseService] = None

# Initialize storage service with configured timeouts
storage_service = S3StorageService(
    bucket_name=settings.s3_bucket_reports,
    region=settings.s3_region,
    connect_timeout=5,
    read_timeout=30,
    max_attempts=3
)

# P1-1: Report cache (temporary fallback if DB unavailable)
reports_cache = ReportCache(
    max_size=settings.cache_max_size,
    ttl_hours=settings.cache_ttl_hours
)

# Use cache as fallback, but prefer database when available
reports_db = {}


@app.post("/reports/generate", status_code=202)
@limiter.limit("10/minute")  # P0-3 CRITICAL FIX: Rate limiting to prevent DoS
async def generate_report(
    request: Request,  # Required for rate limiter
    report_request: ReportGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate validation report for a test run.
    
    CRITICAL FIXES APPLIED:
    - P0-3: Rate limiting (10 requests per minute)
    - P0-4: Comprehensive error handling in background task
    """
    logger.info(f"Report generation requested for format: {report_request.format}")
    
    # Validate test_run_id
    if not report_request.test_run_id or len(report_request.test_run_id) < 3:
        raise HTTPException(status_code=400, detail="Invalid test_run_id")
    
    # Generate unique report ID
    report_id = f"rep_{uuid.uuid4().hex[:12]}"
    
    # P0-5: Create report in database (or cache as fallback)
    try:
        if database_service and app.state.use_database:
            # Use database for persistence
            await database_service.create_report(
                report_id=report_id,
                test_run_id=report_request.test_run_id,
                game_title="Marvel Rivals",  # TODO: Get from test run metadata
                game_version="0.8.1-beta",
                test_environment="PC - High Settings",
                format=report_request.format.value,
                status="queued"
            )
            await database_service.log_event(report_id, "queued", "Report generation queued")
        else:
            # Fallback to cache
            logger.warning("Database unavailable, using cache (data will be lost on restart)")
            reports_cache.add(report_id, {
                "id": report_id,
                "test_run_id": report_request.test_run_id,
                "format": report_request.format,
                "status": "queued",
                "created_at": datetime.utcnow().isoformat(),
                "game_title": "Marvel Rivals",
                "test_environment": "PC - High Settings"
            })
    except Exception as e:
        logger.error(f"Failed to create report record: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create report")
    
    # Start generation in background
    background_tasks.add_task(
        execute_report_generation,
        report_id=report_id,
        request=report_request
    )
    
    return {
        "report_id": report_id,
        "status": "queued",
        "message": "Report generation queued",
        "check_status_url": f"/reports/{report_id}"
    }


async def execute_report_generation(
    report_id: str,
    request: ReportGenerationRequest
):
    """
    Execute report generation pipeline with comprehensive error handling.
    
    P0-4 CRITICAL FIX: Comprehensive error handling to prevent silent failures.
    All errors are logged and surfaced to user via report status.
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Starting report generation: {report_id}")
        
        # Update status to processing (P0-5: use database)
        if database_service and app.state.use_database:
            await database_service.update_report(report_id, {
                "status": "processing",
                "started_at": start_time
            })
            await database_service.log_event(report_id, "started", "Report generation started")
        else:
            # Fallback to cache
            existing = reports_cache.get(report_id)
            if existing:
                existing.update({
                    "status": "processing",
                    "started_at": start_time.isoformat()
                })
                reports_cache.add(report_id, existing)
        
        # Create pipeline
        try:
            pipeline = create_report_pipeline(
                captures_db=captures_db,
                consensus_results_db=consensus_results_db,
                analysis_results_db=analysis_results_db,
                storage_service=storage_service
            )
        except Exception as e:
            logger.error(f"Failed to create pipeline for {report_id}: {e}", exc_info=True)
            
            # P0-5: Update in database or cache
            updates = {
                "status": "failed",
                "error_message": f"Pipeline creation failed: {str(e)}",
                "completed_at": datetime.utcnow()
            }
            
            if database_service and app.state.use_database:
                await database_service.update_report(report_id, updates)
                await database_service.log_event(report_id, "failed", str(e))
            else:
                existing = reports_cache.get(report_id)
                if existing:
                    existing.update({k: v.isoformat() if isinstance(v, datetime) else v for k, v in updates.items()})
                    reports_cache.add(report_id, existing)
            return
        
        # Execute pipeline with timeout protection
        try:
            context = await pipeline.execute({
                'report_id': report_id,
                'test_run_id': request.test_run_id,
                'game_title': 'Marvel Rivals',
                'game_version': '0.8.1-beta',
                'test_environment': 'PC - High Settings',
                'format': request.format
            })
        except asyncio.TimeoutError:
            logger.error(f"Report generation timeout for {report_id}")
            reports_db[report_id].update({
                "status": "failed",
                "error_message": "Generation timeout exceeded",
                "completed_at": datetime.utcnow().isoformat()
            })
            return
        except Exception as e:
            logger.error(f"Pipeline execution failed for {report_id}: {e}", exc_info=True)
            reports_db[report_id].update({
                "status": "failed",
                "error_message": f"Pipeline execution failed: {str(e)}",
                "completed_at": datetime.utcnow().isoformat()
            })
            return
        
        # Validate context before updating report
        if not context or 's3_key' not in context:
            logger.error(f"Invalid pipeline context for {report_id}: missing s3_key")
            reports_db[report_id].update({
                "status": "failed",
                "error_message": "Invalid pipeline output: missing storage key",
                "completed_at": datetime.utcnow().isoformat()
            })
            return
        
        # Update report record with successful completion
        duration = (datetime.utcnow() - start_time).total_seconds()
        completed_at = datetime.utcnow()
        
        updates = {
            "status": "completed",
            "completed_at": completed_at,
            "duration_seconds": duration,
            "s3_key": context['s3_key'],
            "file_size_bytes": context['file_size'],
            "report_data": context['report_data'].dict()
        }
        
        # P0-5: Update in database or cache
        if database_service and app.state.use_database:
            await database_service.update_report(report_id, updates)
            await database_service.log_event(report_id, "completed", f"Generated in {duration:.2f}s")
        else:
            existing = reports_cache.get(report_id)
            if existing:
                existing.update({k: v.isoformat() if isinstance(v, datetime) else v for k, v in updates.items()})
                reports_cache.add(report_id, existing)
        
        logger.info(f"Report generation completed: {report_id} in {duration:.2f}s")
        
    except Exception as e:
        # Catch-all for any unexpected errors
        logger.error(f"Unexpected error in report generation for {report_id}: {e}", exc_info=True)
        
        # P0-5: Update in database or cache
        updates = {
            "status": "failed",
            "error_message": f"Unexpected error: {str(e)}",
            "completed_at": datetime.utcnow()
        }
        
        if database_service and app.state.use_database:
            try:
                await database_service.update_report(report_id, updates)
                await database_service.log_event(report_id, "failed", str(e), {"error_type": "unexpected"})
            except Exception as db_error:
                logger.error(f"Failed to update error status in database: {db_error}")
        else:
            existing = reports_cache.get(report_id)
            if existing:
                existing.update({k: v.isoformat() if isinstance(v, datetime) else v for k, v in updates.items()})
                reports_cache.add(report_id, existing)
        
        # Re-raise to ensure error visibility in logs
        raise


@app.get("/reports")
async def list_reports(
    game_title: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all reports with optional filtering.
    
    P0-5: Uses database with pagination.
    """
    # P0-5: Try database first
    if database_service and app.state.use_database:
        try:
            reports = await database_service.list_reports(
                game_title=game_title,
                status=status,
                limit=limit,
                offset=offset
            )
            
            return {
                "total": len(reports),
                "reports": reports,
                "limit": limit,
                "offset": offset,
                "source": "database"
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
    
    # Fallback to cache
    logger.warning("Using cache fallback for list_reports")
    reports = reports_cache.values()
    
    # Filter by game title
    if game_title:
        reports = [r for r in reports if r.get('game_title', '').lower() == game_title.lower()]
    
    # Filter by status
    if status:
        reports = [r for r in reports if r.get('status') == status]
    
    # Sort by created_at (newest first)
    reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {
        "total": len(reports),
        "reports": reports[offset:offset+limit],
        "limit": limit,
        "offset": offset,
        "source": "cache"
    }


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """
    Get report details.
    
    P0-2 + P0-5 FIX: Uses database with secure presigned URLs.
    """
    # P0-5: Try database first, fallback to cache
    report = None
    
    if database_service and app.state.use_database:
        try:
            report = await database_service.get_report(report_id)
        except Exception as e:
            logger.error(f"Database query failed for {report_id}: {e}")
    
    if not report:
        # Fallback to cache
        report = reports_cache.get(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Generate presigned URL if report is completed
    # P0-2 FIX: Short expiration (300s = 5 minutes)
    if report['status'] == 'completed' and report.get('s3_key'):
        try:
            report['download_url'] = storage_service.generate_presigned_url(
                report['s3_key'],
                expiration=300  # 5 minutes (was 3600)
            )
        except FileNotFoundError:
            logger.warning(f"S3 object not found for report {report_id}: {report['s3_key']}")
            report['status'] = 'completed_file_missing'
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {report_id}: {e}")
    
    return report


@app.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download report file"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = reports_db[report_id]
    
    if report['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready for download. Status: {report['status']}"
        )
    
    if not report.get('s3_key'):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Generate presigned URL
    download_url = storage_service.generate_presigned_url(
        report['s3_key'],
        expiration=300  # 5 minutes
    )
    
    return {"download_url": download_url}


@app.get("/reports/{report_id}/export")
async def export_report(
    report_id: str,
    format: ReportFormat = Query(...)
):
    """Export report in different format"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = reports_db[report_id]
    
    if report['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready. Status: {report['status']}"
        )
    
    # If requesting same format, return existing URL
    if format == report['format']:
        download_url = storage_service.generate_presigned_url(
            report['s3_key'],
            expiration=300
        )
        return {"download_url": download_url}
    
    # Otherwise, generate on-demand
    # TODO: Implement on-demand format conversion
    raise HTTPException(
        status_code=501,
        detail="On-demand format conversion not yet implemented"
    )


# P1-2 CRITICAL FIX: Resource cleanup on startup/shutdown
@app.on_event("startup")
async def startup_event():
    """
    Application startup: Initialize services and verify health.
    
    P0-5 + P1-2: Initialize database connection and verify health checks
    """
    global database_service
    
    logger.info("QA Orchestrator starting up...")
    logger.info(f"Configuration: {settings.dict_safe()}")
    
    # P0-5: Initialize database connection
    try:
        database_service = DatabaseService(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            min_pool_size=settings.db_pool_min_size,
            max_pool_size=settings.db_pool_max_size
        )
        await database_service.connect()
        
        # Verify database health
        if await database_service.health_check():
            logger.info("Database connected and healthy")
            app.state.use_database = True
        else:
            logger.error("Database health check failed")
            app.state.use_database = False
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        logger.warning("Falling back to in-memory cache (data will be lost on restart)")
        database_service = None
        app.state.use_database = False
    
    # Verify S3 connectivity
    try:
        storage_service.s3_client.head_bucket(Bucket=storage_service.bucket_name)
        logger.info(f"S3 bucket '{storage_service.bucket_name}' is accessible")
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        logger.warning("Application starting with S3 unavailable - reports will fail")
    
    # Log cache configuration (used as fallback)
    cache_stats = reports_cache.stats()
    logger.info(f"Report cache configured: {cache_stats}")
    
    logger.info("QA Orchestrator startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown: Cleanup resources gracefully.
    
    P0-5 + P1-2: Cleanup database and resources
    """
    logger.info("QA Orchestrator shutting down...")
    
    # P0-5: Disconnect database
    if database_service:
        try:
            await database_service.disconnect()
            logger.info("Database disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting database: {e}")
    
    # Cleanup PDF generation executor
    if hasattr(app.state, 'report_generator'):
        try:
            await app.state.report_generator.cleanup()
            logger.info("Report generator cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up report generator: {e}")
    
    # Log final cache stats
    cache_stats = reports_cache.stats()
    logger.info(f"Final cache statistics: {cache_stats}")
    
    # Allow background tasks to complete
    logger.info("Waiting for background tasks to complete...")
    import asyncio
    await asyncio.sleep(2)
    
    logger.info("QA Orchestrator shutdown complete")


if __name__ == "__main__":
    import uvicorn
    import platform
    import asyncio
    
    # P0-5: Fix for Windows ProactorEventLoop issue with psycopg
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Using SelectorEventLoop for Windows compatibility with psycopg")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

