"""
4D Vision Analyzer Service
==========================

Orchestrates detector modules to analyze 4D segments and emit
vision issues and scene summaries.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncpg
from nats.aio.client import Client as NATS
from loguru import logger
from prometheus_client import start_http_server

from .detector_base import DetectorFinding, SegmentContext
from .detectors import create_detector, DETECTOR_CLASSES
from ..shared.nats_client import get_nats_client
from ..shared.postgres import get_postgres_pool
from .data_quality import DataQualityAnalyzer, handle_degraded_input
from .metrics import AnalyzerMetricsCollector, track_analysis_metrics


class VisionAnalyzerService:
    """
    Main service for analyzing 4D vision segments.
    """
    
    def __init__(
        self,
        postgres_pool: asyncpg.Pool,
        nats_client: Optional[NATS] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.postgres = postgres_pool
        self.nats = nats_client
        self.config = config or {}
        self.metrics = AnalyzerMetricsCollector()
        self.quality_analyzer = DataQualityAnalyzer(config)
        
        # Initialize detectors
        self.detectors = {}
        self._init_detectors()
        
        # NATS subjects
        self.analyze_subject = "vision.analyze.request"
        self.issue_subject = "vision.issue"
        self.summary_subject = "vision.scene.summary"
        self.health_subject = "vision.health.analyzer"
        
        self._running = False
        self._health_task: Optional[asyncio.Task] = None
        self._workers: List[asyncio.Task] = []
    
    def _init_detectors(self):
        """Initialize detector instances."""
        detector_configs = self.config.get("detectors", {})
        
        for detector_type in DETECTOR_CLASSES:
            config = detector_configs.get(detector_type, {})
            self.detectors[detector_type] = create_detector(detector_type, config)
            logger.info(f"Initialized {detector_type} detector")
    
    async def start(self):
        """Start the analyzer service."""
        logger.info("Starting 4D Vision Analyzer Service")
        
        if not self.nats:
            self.nats = await get_nats_client()
        
        # Subscribe to analysis requests
        await self.nats.subscribe(
            self.analyze_subject,
            "vision_analyzer_workers",  # Queue group for load balancing
            self._handle_analyze_request
        )
        
        self._running = True
        self._health_task = asyncio.create_task(self._publish_health())
        
        # Start worker tasks
        worker_count = self.config.get("worker_count", 3)
        for i in range(worker_count):
            worker = asyncio.create_task(self._process_queue_worker(i))
            self._workers.append(worker)
        
        logger.info(f"Started with {worker_count} workers")
    
    async def stop(self):
        """Stop the analyzer service."""
        logger.info("Stopping 4D Vision Analyzer Service")
        self._running = False
        
        # Cancel health task
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        # Cancel workers
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        if self.nats and self.nats.is_connected:
            await self.nats.drain()
    
    @track_analysis_metrics("overall")
    async def analyze_segment(self, segment_id: str) -> Dict[str, Any]:
        """
        Analyze a 4D segment.
        
        Returns:
            Analysis results with findings and summary
        """
        try:
            # Load segment from database
            segment_context = await self._load_segment(segment_id)
            if not segment_context:
                logger.error(f"Segment {segment_id} not found")
                return {"status": "error", "error": "Segment not found"}
            
            # Assess data quality
            quality_assessment = self.quality_analyzer.assess_segment_quality(segment_context)
            logger.info(f"Segment {segment_id} data quality: {quality_assessment.overall_quality.value}")
            
            if not quality_assessment.can_analyze:
                logger.warning(f"Segment {segment_id} data quality too poor to analyze")
                # Create data quality finding
                quality_finding = self.quality_analyzer.create_data_quality_finding(
                    segment_context, quality_assessment
                )
                if quality_finding:
                    await self._store_finding(segment_id, quality_finding)
                    await self._publish_issue(segment_context, quality_finding)
                
                await self._update_segment_status(segment_id, "failed", "Data quality too poor")
                return {
                    "status": "error",
                    "error": "Data quality too poor to analyze",
                    "quality_assessment": quality_assessment
                }
            
            # Update status to analyzing
            await self._update_segment_status(segment_id, "analyzing")
            
            # Run detectors
            all_findings = []
            detector_results = {}
            
            for detector_type, detector in self.detectors.items():
                try:
                    logger.debug(f"Running {detector_type} detector on segment {segment_id}")
                    
                    findings = await detector.analyze(segment_context)
                    
                    # Adjust findings based on data quality
                    adjusted_findings = handle_degraded_input(findings, quality_assessment)
                    
                    all_findings.extend(adjusted_findings)
                    detector_results[detector_type] = len(adjusted_findings)
                    
                    # Record metrics
                    self.metrics.record_findings(adjusted_findings, detector_type)
                    
                    # Store findings
                    for finding in adjusted_findings:
                        await self._store_finding(segment_id, finding)
                        await self._publish_issue(segment_context, finding)
                        
                except Exception as e:
                    logger.error(f"Error in {detector_type} detector: {e}")
                    detector_results[detector_type] = "error"
            
            # Add data quality finding if needed
            quality_finding = self.quality_analyzer.create_data_quality_finding(
                segment_context, quality_assessment
            )
            if quality_finding:
                all_findings.append(quality_finding)
                await self._store_finding(segment_id, quality_finding)
                await self._publish_issue(segment_context, quality_finding)
            
            # Generate scene summary
            summary = await self._generate_scene_summary(segment_context, all_findings)
            await self._publish_summary(summary)
            
            # Update segment status
            await self._update_segment_status(segment_id, "completed")
            
            logger.info(
                f"Analyzed segment {segment_id}: "
                f"{len(all_findings)} findings across {len(detector_results)} detectors"
            )
            
            return {
                "status": "success",
                "segment_id": segment_id,
                "findings_count": len(all_findings),
                "detector_results": detector_results,
                "summary": summary,
                "data_quality": quality_assessment.overall_quality.value
            }
            
        except Exception as e:
            logger.error(f"Error analyzing segment {segment_id}: {e}")
            await self._update_segment_status(segment_id, "failed", str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_analyze_request(self, msg):
        """Handle analysis request from NATS."""
        try:
            data = json.loads(msg.data.decode())
            segment_id = data.get("segment_id")
            
            if not segment_id:
                logger.error("Analysis request missing segment_id")
                return
            
            # Add to processing queue
            await self._add_to_queue(segment_id, data.get("priority", 5))
            
        except Exception as e:
            logger.error(f"Error handling analysis request: {e}")
    
    async def _process_queue_worker(self, worker_id: int):
        """Worker to process analysis queue."""
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Get next item from queue
                queue_item = await self._get_from_queue()
                if not queue_item:
                    await asyncio.sleep(1)
                    continue
                
                segment_id = str(queue_item["segment_id"])
                logger.debug(f"Worker {worker_id} processing segment {segment_id}")
                
                # Analyze segment
                result = await self.analyze_segment(segment_id)
                
                # Update queue status
                await self._update_queue_status(
                    queue_item["queue_id"],
                    "completed" if result["status"] == "success" else "failed"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _load_segment(self, segment_id: str) -> Optional[SegmentContext]:
        """Load segment from database."""
        async with self.postgres.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM vision_segments
                WHERE segment_id = $1
                """,
                UUID(segment_id)
            )
            
            if not row:
                return None
            
            return SegmentContext(
                segment_id=row["segment_id"],
                build_id=row["build_id"],
                scene_id=row["scene_id"],
                level_name=row["level_name"],
                start_timestamp=row["start_timestamp"],
                end_timestamp=row["end_timestamp"],
                duration_seconds=row["duration_seconds"],
                frame_count=row["frame_count"],
                camera_configs=json.loads(row["camera_configs"]),
                media_uris=json.loads(row["media_uris"]),
                depth_uris=json.loads(row["depth_uris"]),
                gameplay_events=json.loads(row["gameplay_events"]),
                performance_metrics=json.loads(row["performance_metrics"]),
                metadata=json.loads(row["metadata"])
            )
    
    async def _store_finding(self, segment_id: str, finding: DetectorFinding):
        """Store finding in database."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO vision_issues (
                    segment_id, detector_type, issue_type,
                    severity, confidence, timestamp, camera_id,
                    screen_coords, world_coords, description,
                    evidence_refs, metrics, affected_goals,
                    player_impact, explanation, threshold_details
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """,
                UUID(segment_id),
                finding.detector_type,
                finding.issue_type,
                finding.severity,
                finding.confidence,
                finding.timestamp,
                finding.camera_id,
                list(finding.screen_coords) if finding.screen_coords else None,
                list(finding.world_coords) if finding.world_coords else None,
                finding.description,
                json.dumps(finding.evidence_refs),
                json.dumps(finding.metrics),
                finding.affected_goals,
                finding.player_impact,
                f"Detected by {finding.detector_type} detector with confidence {finding.confidence}",
                json.dumps({
                    "severity_threshold": 0.3,
                    "confidence_threshold": 0.7,
                    "detector_version": "0.1.0"
                })
            )
    
    async def _update_segment_status(
        self, 
        segment_id: str, 
        status: str, 
        error: Optional[str] = None
    ):
        """Update segment analysis status."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                UPDATE vision_segments
                SET analysis_status = $2, analyzed_at = $3
                WHERE segment_id = $1
                """,
                UUID(segment_id),
                status,
                datetime.utcnow() if status in ["completed", "failed"] else None
            )
    
    async def _generate_scene_summary(
        self,
        segment: SegmentContext,
        findings: List[DetectorFinding]
    ) -> Dict[str, Any]:
        """Generate scene-level summary."""
        # Count issues by detector
        issue_counts = {}
        severity_sums = {}
        
        for finding in findings:
            detector = finding.detector_type
            issue_counts[detector] = issue_counts.get(detector, 0) + 1
            severity_sums[detector] = severity_sums.get(detector, 0) + finding.severity
        
        # Calculate averages
        avg_severities = {
            detector: severity_sums[detector] / issue_counts[detector]
            for detector in issue_counts
        }
        
        # Identify critical issues
        critical_issues = [
            f"{f.issue_type} ({f.detector_type})"
            for f in findings
            if f.severity >= 0.8
        ]
        
        # Calculate overall scores
        visual_quality = 1.0 - (avg_severities.get("rendering", 0) * 0.5 + 
                               avg_severities.get("animation", 0) * 0.3 +
                               avg_severities.get("physics", 0) * 0.2)
        
        horror_atmosphere = 1.0 - avg_severities.get("lighting", 0)
        
        technical_stability = 1.0 - (avg_severities.get("performance", 0) * 0.6 +
                                   avg_severities.get("flow", 0) * 0.4)
        
        summary = {
            "segment_id": str(segment.segment_id),
            "scene_id": segment.scene_id,
            "build_id": segment.build_id,
            "total_segments": 1,
            "analyzed_segments": 1,
            "issue_counts": issue_counts,
            "avg_severities": avg_severities,
            "critical_issues": critical_issues[:5],  # Top 5
            "visual_quality_score": max(0, min(1, visual_quality)),
            "horror_atmosphere_score": max(0, min(1, horror_atmosphere)),
            "technical_stability_score": max(0, min(1, technical_stability))
        }
        
        # Store in database
        await self._store_scene_summary(summary)
        
        return summary
    
    async def _store_scene_summary(self, summary: Dict[str, Any]):
        """Store or update scene summary."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO vision_scene_summaries (
                    build_id, scene_id, total_segments, analyzed_segments,
                    issue_counts, avg_severities, critical_issues,
                    visual_quality_score, horror_atmosphere_score,
                    technical_stability_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (build_id, scene_id) DO UPDATE SET
                    total_segments = vision_scene_summaries.total_segments + 1,
                    analyzed_segments = vision_scene_summaries.analyzed_segments + 1,
                    issue_counts = $5,
                    avg_severities = $6,
                    critical_issues = $7,
                    visual_quality_score = $8,
                    horror_atmosphere_score = $9,
                    technical_stability_score = $10,
                    last_updated = CURRENT_TIMESTAMP
                """,
                summary["build_id"],
                summary["scene_id"],
                summary["total_segments"],
                summary["analyzed_segments"],
                json.dumps(summary["issue_counts"]),
                json.dumps(summary["avg_severities"]),
                summary["critical_issues"],
                summary["visual_quality_score"],
                summary["horror_atmosphere_score"],
                summary["technical_stability_score"]
            )
    
    async def _publish_issue(self, segment: SegmentContext, finding: DetectorFinding):
        """Publish vision issue event."""
        if not self.nats:
            return
        
        issue_event = {
            "envelope": {
                "trace_id": segment.metadata.get("trace_id", str(segment.segment_id)),
                "session_id": segment.metadata.get("session_id"),
                "player_id": segment.metadata.get("player_id"),
                "build_id": segment.build_id,
                "start_timestamp": segment.start_timestamp.isoformat(),
                "end_timestamp": segment.end_timestamp.isoformat(),
                "domain": "4D",
                "goal_tags": finding.affected_goals
            },
            "segment_id": str(segment.segment_id),
            "finding": {
                "detector_type": finding.detector_type,
                "issue_id": finding.issue_id,
                "issue_type": finding.issue_type,
                "severity": finding.severity,
                "confidence": finding.confidence,
                "timestamp": finding.timestamp.isoformat(),
                "camera_id": finding.camera_id,
                "description": finding.description,
                "evidence_refs": finding.evidence_refs,
                "metrics": finding.metrics
            },
            "affected_goals": finding.affected_goals,
            "player_impact": finding.player_impact,
            "explanation": f"Detected by {finding.detector_type} detector",
            "threshold_details": {
                "severity_threshold": 0.3,
                "confidence_threshold": 0.7
            }
        }
        
        await self.nats.publish(
            self.issue_subject,
            json.dumps(issue_event).encode()
        )
    
    async def _publish_summary(self, summary: Dict[str, Any]):
        """Publish scene summary event."""
        if not self.nats:
            return
        
        summary_event = {
            "envelope": {
                "trace_id": summary.get("segment_id"),
                "build_id": summary["build_id"],
                "domain": "4D",
                "timestamp": datetime.utcnow().isoformat()
            },
            "scene_id": summary["scene_id"],
            "total_segments": summary["total_segments"],
            "analyzed_segments": summary["analyzed_segments"],
            "issue_counts": summary["issue_counts"],
            "avg_severities": summary["avg_severities"],
            "critical_issues": summary["critical_issues"],
            "visual_quality_score": summary["visual_quality_score"],
            "horror_atmosphere_score": summary["horror_atmosphere_score"],
            "technical_stability_score": summary["technical_stability_score"]
        }
        
        await self.nats.publish(
            self.summary_subject,
            json.dumps(summary_event).encode()
        )
    
    async def _add_to_queue(self, segment_id: str, priority: int):
        """Add segment to analysis queue."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                UPDATE vision_analysis_queue
                SET priority = GREATEST(priority, $2)
                WHERE segment_id = $1 AND status = 'pending'
                """,
                UUID(segment_id),
                priority
            )
    
    async def _get_from_queue(self) -> Optional[Dict[str, Any]]:
        """Get next item from analysis queue."""
        async with self.postgres.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE vision_analysis_queue
                SET status = 'processing', 
                    attempts = attempts + 1,
                    last_attempt_at = CURRENT_TIMESTAMP
                WHERE queue_id = (
                    SELECT queue_id 
                    FROM vision_analysis_queue
                    WHERE status = 'pending'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING *
                """
            )
            
            return dict(row) if row else None
    
    async def _update_queue_status(self, queue_id: str, status: str):
        """Update queue item status."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                UPDATE vision_analysis_queue
                SET status = $2, completed_at = $3
                WHERE queue_id = $1
                """,
                UUID(queue_id),
                status,
                datetime.utcnow() if status == "completed" else None
            )
    
    async def _publish_health(self):
        """Periodically publish health status."""
        while self._running:
            try:
                # Check database connectivity
                db_healthy = await self._check_db_health()
                
                # Check queue depth
                queue_depth = await self._get_queue_depth()
                
                # Check detector health
                detector_status = await self._check_detector_health()
                
                # Check worker health
                active_workers = sum(1 for w in self._workers if not w.done())
                
                # Determine overall status
                overall_status = "healthy"
                if not db_healthy or not (self.nats and self.nats.is_connected):
                    overall_status = "unhealthy"
                elif any(s == "failed" for s in detector_status.values()):
                    overall_status = "degraded"
                elif queue_depth > 100:  # High backlog
                    overall_status = "degraded"
                elif active_workers < len(self._workers) * 0.5:  # Half workers down
                    overall_status = "degraded"
                
                health = {
                    "service": "vision_analyzer",
                    "status": overall_status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "database": "connected" if db_healthy else "disconnected",
                        "nats": "connected" if self.nats and self.nats.is_connected else "disconnected",
                        "workers": {
                            "active": active_workers,
                            "total": len(self._workers)
                        },
                        "queue_depth": queue_depth,
                        "detectors": detector_status,
                        "uptime_seconds": self.metrics.get_uptime_seconds()
                    }
                }
                
                # Publish to standard health topic
                if self.nats:
                    await self.nats.publish(
                        self.health_subject,
                        json.dumps(health).encode()
                    )
                    
                    # Also publish to system health for Coordinator
                    if overall_status in ["degraded", "unhealthy"]:
                        system_event = {
                            "domain": "4d_vision",
                            "status": overall_status,
                            "timestamp": datetime.utcnow().isoformat(),
                            "details": {
                                "service": "analyzer",
                                "issues": self._get_health_issues(health)
                            }
                        }
                        await self.nats.publish(
                            "SYS.HEALTH.4D_VISION",
                            json.dumps(system_event).encode()
                        )
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error publishing health: {e}")
                await asyncio.sleep(30)
    
    async def _check_db_health(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.postgres.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
    
    async def _get_queue_depth(self) -> int:
        """Get pending items in queue."""
        try:
            async with self.postgres.acquire() as conn:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM vision_analysis_queue WHERE status = 'pending'"
                )
        except Exception:
            return -1
    
    async def _check_detector_health(self) -> Dict[str, str]:
        """Check health of individual detectors."""
        detector_status = {}
        
        for name, detector in self.detectors.items():
            try:
                # Simple health check - verify detector responds
                caps = detector.get_capabilities()
                if caps and isinstance(caps, dict):
                    detector_status[name] = "operational"
                else:
                    detector_status[name] = "degraded"
            except Exception as e:
                logger.error(f"Detector {name} health check failed: {e}")
                detector_status[name] = "failed"
        
        return detector_status
    
    def _get_health_issues(self, health: Dict[str, Any]) -> List[str]:
        """Extract specific health issues from health data."""
        issues = []
        
        if health["details"]["database"] != "connected":
            issues.append("Database connection lost")
        
        if health["details"]["nats"] != "connected":
            issues.append("NATS connection lost")
        
        workers = health["details"]["workers"]
        if workers["active"] < workers["total"]:
            issues.append(f"Only {workers['active']}/{workers['total']} workers active")
        
        if health["details"]["queue_depth"] > 100:
            issues.append(f"High queue backlog: {health['details']['queue_depth']}")
        
        failed_detectors = [
            name for name, status in health["details"]["detectors"].items() 
            if status == "failed"
        ]
        if failed_detectors:
            issues.append(f"Failed detectors: {', '.join(failed_detectors)}")
        
        return issues


async def main():
    """Main entry point for the service."""
    # Start metrics server
    start_http_server(8092)
    logger.info("Metrics server started on port 8092")
    
    # Initialize resources
    postgres_pool = await get_postgres_pool()
    nats_client = await get_nats_client()
    
    # Create and start service
    service = VisionAnalyzerService(
        postgres_pool=postgres_pool,
        nats_client=nats_client,
        config={
            "worker_count": 3,
            "detectors": {
                "animation": {"confidence_threshold": 0.7},
                "physics": {"confidence_threshold": 0.8},
                "rendering": {"confidence_threshold": 0.75},
                "lighting": {"confidence_threshold": 0.6},
                "performance": {"confidence_threshold": 0.9},
                "flow": {"confidence_threshold": 0.7}
            }
        }
    )
    
    try:
        await service.start()
        logger.info("4D Vision Analyzer Service running. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()
        await postgres_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
