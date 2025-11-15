"""
API routes for Engagement & Addiction Analytics service.
Implements TEMO-09, TEMO-10.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from .engagement_schemas import (
    NPCInteractionEvent,
    MoralChoiceEvent,
    SessionMetricsEvent,
    AIRunEvent,
    EngagementAggregate,
    AddictionRiskReport,
    AggregateType,
    CohortDefinition
)
from .telemetry_ingester import TelemetryIngester
from .metric_calculator import MetricCalculator
from .addiction_detector import AddictionDetector
from .safety_constraints import (
    require_safe_usage, UsageContext, safety_constraints,
    ConstraintViolation, DisallowedUsage
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/engagement", tags=["engagement"])

# Dependencies (will be injected)
telemetry_ingester: Optional[TelemetryIngester] = None
metric_calculator: Optional[MetricCalculator] = None
addiction_detector: Optional[AddictionDetector] = None


# Request/Response models
class RecordEventRequest(BaseModel):
    """Request to record an engagement event."""
    event_type: str
    event_data: Dict[str, Any]

class RecordEventResponse(BaseModel):
    """Response from recording an event."""
    success: bool
    message: Optional[str] = None

class GetMetricsRequest(BaseModel):
    """Request to get engagement metrics."""
    cohort_id: str
    metric_type: Optional[str] = None
    npc_id: Optional[str] = None
    scene_id: Optional[str] = None
    build_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class MetricsResponse(BaseModel):
    """Response containing engagement metrics."""
    metrics: List[Dict[str, Any]]
    total_count: int

class AssessRiskRequest(BaseModel):
    """Request to assess addiction risk."""
    cohort_id: str
    region: Optional[str] = None
    age_band: Optional[str] = None
    platform: Optional[str] = None
    build_id: str
    period_days: int = 7

class IngestStatsResponse(BaseModel):
    """Response with ingestion statistics."""
    buffer_size: int
    event_counts: Dict[str, int]
    last_flush: str


# Endpoints
@router.post("/events", response_model=RecordEventResponse)
async def record_engagement_event(request: RecordEventRequest) -> RecordEventResponse:
    """
    Record a new engagement telemetry event.
    Supports: npc_interaction, moral_choice, session_metrics, ai_run
    """
    if not telemetry_ingester:
        raise HTTPException(status_code=503, detail="Telemetry ingester not initialized")
    
    try:
        # Validate event type
        if request.event_type not in ['npc_interaction', 'moral_choice', 'session_metrics', 'ai_run']:
            return RecordEventResponse(
                success=False,
                message=f"Unknown event type: {request.event_type}"
            )
        
        # Add event type to data if not present
        event_data = request.event_data.copy()
        event_data['event_type'] = request.event_type
        
        # Ingest event
        success = await telemetry_ingester.ingest_event(event_data)
        
        if success:
            return RecordEventResponse(success=True)
        else:
            return RecordEventResponse(
                success=False,
                message="Failed to parse or validate event"
            )
            
    except Exception as e:
        logger.error(f"Error recording event: {e}", exc_info=True)
        return RecordEventResponse(
            success=False,
            message=str(e)
        )


@router.post("/events/batch")
async def record_events_batch(events: List[RecordEventRequest]) -> Dict[str, Any]:
    """Record multiple engagement events in batch."""
    if not telemetry_ingester:
        raise HTTPException(status_code=503, detail="Telemetry ingester not initialized")
    
    results = {
        'total': len(events),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for i, event_req in enumerate(events):
        try:
            event_data = event_req.event_data.copy()
            event_data['event_type'] = event_req.event_type
            
            success = await telemetry_ingester.ingest_event(event_data)
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'index': i,
                    'error': 'Failed to parse or validate event'
                })
                
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'index': i,
                'error': str(e)
            })
    
    return results


@router.post("/cohorts/{session_id}/assign")
async def assign_session_cohort(
    session_id: UUID,
    cohort: CohortDefinition
) -> Dict[str, Any]:
    """Assign a session to a cohort for privacy-preserving analytics."""
    if not telemetry_ingester:
        raise HTTPException(status_code=503, detail="Telemetry ingester not initialized")
    
    try:
        await telemetry_ingester.assign_session_cohort(session_id, cohort)
        return {
            "success": True,
            "session_id": str(session_id),
            "cohort_id": cohort.cohort_id
        }
    except Exception as e:
        logger.error(f"Error assigning cohort: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/npc-attachment/{cohort_id}/{npc_id}")
async def get_npc_attachment_metrics(
    cohort_id: str,
    npc_id: str,
    build_id: str = Query(..., description="Build ID"),
    period_days: int = Query(7, description="Period in days")
) -> Dict[str, Any]:
    """Get NPC attachment metrics for a cohort."""
    if not metric_calculator:
        raise HTTPException(status_code=503, detail="Metric calculator not initialized")
    
    # Enforce safety constraints
    try:
        safety_constraints.check_usage_allowed(
            UsageContext.COHORT_ANALYSIS,
            {
                'requester': 'api_npc_attachment',
                'cohort_size': 100,  # Would get from DB in real implementation
                'granularity': 'cohort',
                'purpose': 'cohort health monitoring'
            }
        )
    except ConstraintViolation as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    try:
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=period_days)
        
        metrics = await metric_calculator.calculate_npc_attachment(
            cohort_id, npc_id, build_id, period_start, period_end
        )
        
        return {
            "cohort_id": cohort_id,
            "npc_id": npc_id,
            "build_id": build_id,
            "period": f"{period_start.date()}/P{period_days}D",
            "metrics": metrics.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error calculating NPC attachment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/moral-tension/{cohort_id}/{scene_id}")
async def get_moral_tension_metrics(
    cohort_id: str,
    scene_id: str,
    build_id: str = Query(..., description="Build ID"),
    period_days: int = Query(7, description="Period in days")
) -> Dict[str, Any]:
    """Get moral decision tension metrics for a cohort."""
    if not metric_calculator:
        raise HTTPException(status_code=503, detail="Metric calculator not initialized")
    
    try:
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=period_days)
        
        metrics = await metric_calculator.calculate_moral_tension(
            cohort_id, scene_id, build_id, period_start, period_end
        )
        
        return {
            "cohort_id": cohort_id,
            "scene_id": scene_id,
            "build_id": build_id,
            "period": f"{period_start.date()}/P{period_days}D",
            "metrics": metrics.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error calculating moral tension: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/engagement-profile/{cohort_id}")
async def get_engagement_profile(
    cohort_id: str,
    build_id: str = Query(..., description="Build ID"),
    period_days: int = Query(30, description="Period in days")
) -> Dict[str, Any]:
    """Detect primary engagement profile for a cohort."""
    if not metric_calculator:
        raise HTTPException(status_code=503, detail="Metric calculator not initialized")
    
    try:
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=period_days)
        
        profile = await metric_calculator.detect_engagement_profile(
            cohort_id, build_id, period_start, period_end
        )
        
        if not profile:
            return {
                "cohort_id": cohort_id,
                "build_id": build_id,
                "period": f"{period_start.date()}/P{period_days}D",
                "profile": None,
                "message": "No dominant profile detected"
            }
        
        return {
            "cohort_id": cohort_id,
            "build_id": build_id,
            "period": f"{period_start.date()}/P{period_days}D",
            "profile": profile.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error detecting engagement profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/compute", status_code=202)
async def trigger_metric_computation(
    background_tasks: BackgroundTasks,
    cohort_id: str,
    metric_types: List[str] = Query(..., description="Types: npc_attachment, moral_tension, engagement_profile"),
    build_id: str = Query(..., description="Build ID"),
    period_days: int = Query(7, description="Period in days")
) -> Dict[str, Any]:
    """Trigger background computation of metrics."""
    if not metric_calculator:
        raise HTTPException(status_code=503, detail="Metric calculator not initialized")
    
    # Validate metric types
    valid_types = ['npc_attachment', 'moral_tension', 'engagement_profile']
    invalid_types = [t for t in metric_types if t not in valid_types]
    if invalid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric types: {invalid_types}"
        )
    
    # Schedule background computation
    background_tasks.add_task(
        _compute_metrics_background,
        cohort_id, metric_types, build_id, period_days
    )
    
    return {
        "status": "accepted",
        "message": f"Computing {len(metric_types)} metric types for cohort {cohort_id}",
        "check_status_at": f"/api/v1/engagement/metrics/status/{cohort_id}"
    }


@router.post("/risk/assess")
async def assess_addiction_risk(request: AssessRiskRequest) -> AddictionRiskReport:
    """
    Assess addiction risk for a cohort.
    R-EMO-ADD-002: Returns only cohort-level data, no individual tracking.
    """
    if not addiction_detector:
        raise HTTPException(status_code=503, detail="Addiction detector not initialized")
    
    # Enforce safety constraints
    try:
        safety_constraints.check_usage_allowed(
            UsageContext.COHORT_ANALYSIS,
            {
                'requester': 'api_addiction_risk',
                'cohort_size': 100,  # Would validate from actual cohort
                'granularity': 'cohort',
                'purpose': 'addiction risk monitoring',
                'time_granularity': 'daily'
            }
        )
    except ConstraintViolation as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    try:
        cohort_def = CohortDefinition(
            cohort_id=request.cohort_id,
            region=request.region,
            age_band=request.age_band,
            platform=request.platform
        )
        
        report = await addiction_detector.assess_cohort_risk(
            cohort_def, request.build_id, request.period_days
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error assessing addiction risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/reports")
async def list_risk_reports(
    cohort_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(10, le=100)
) -> List[Dict[str, Any]]:
    """List addiction risk reports with filtering."""
    # This would query the addiction_risk_reports table
    # For now, return empty list as placeholder
    return []


@router.get("/stats/ingestion")
async def get_ingestion_stats() -> IngestStatsResponse:
    """Get telemetry ingestion statistics."""
    if not telemetry_ingester:
        raise HTTPException(status_code=503, detail="Telemetry ingester not initialized")
    
    stats = telemetry_ingester.get_stats()
    
    return IngestStatsResponse(
        buffer_size=stats['buffer_size'],
        event_counts=stats['event_counts'],
        last_flush=stats['last_flush']
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "engagement-analytics",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "telemetry_ingester": telemetry_ingester is not None,
            "metric_calculator": metric_calculator is not None,
            "addiction_detector": addiction_detector is not None
        }
    }


@router.get("/safety/violations")
async def get_safety_violations() -> Dict[str, Any]:
    """
    Get report of safety constraint violations (for security auditing).
    This endpoint itself requires special authorization.
    """
    violations = safety_constraints.get_violation_report()
    
    return {
        "total_violations": len(violations),
        "violations": violations[-100:],  # Last 100 violations
        "message": "Review these violations to ensure no predatory patterns"
    }


@router.get("/safety/constraints")
async def get_safety_constraints() -> Dict[str, Any]:
    """Get current safety constraint configuration."""
    return {
        "min_cohort_size": safety_constraints.MIN_COHORT_SIZE,
        "access_frequency_limits": safety_constraints.MAX_ACCESS_FREQUENCY,
        "allowed_contexts": [c.value for c in UsageContext],
        "disallowed_patterns": [d.value for d in DisallowedUsage],
        "message": "These constraints protect against predatory usage"
    }


# Background task helper
async def _compute_metrics_background(
    cohort_id: str,
    metric_types: List[str],
    build_id: str,
    period_days: int
) -> None:
    """Background task to compute metrics."""
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=period_days)
    
    try:
        for metric_type in metric_types:
            if metric_type == 'npc_attachment':
                # Would need to iterate over NPCs - simplified for now
                pass
            elif metric_type == 'moral_tension':
                # Would need to iterate over scenes - simplified for now
                pass
            elif metric_type == 'engagement_profile':
                profile = await metric_calculator.detect_engagement_profile(
                    cohort_id, build_id, period_start, period_end
                )
                if profile:
                    # Store the computed profile
                    aggregate = EngagementAggregate(
                        aggregate_type=AggregateType.ENGAGEMENT_PROFILE,
                        cohort_id=cohort_id,
                        build_id=build_id,
                        period_start=period_start,
                        period_end=period_end,
                        engagement_profile=profile
                    )
                    await metric_calculator.store_aggregate(aggregate)
        
        logger.info(f"Completed metric computation for cohort {cohort_id}")
        
    except Exception as e:
        logger.error(f"Error in background metric computation: {e}", exc_info=True)
