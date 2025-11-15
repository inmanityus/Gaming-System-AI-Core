"""
4D Vision Coverage Analytics Job

Implements T4D-11: Aggregates segment/issue data per build/scene
and emits coverage/trend events.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
import asyncpg
from loguru import logger
from nats.aio.client import Client as NATS
import numpy as np

from services.shared.db_utils import get_postgres_pool
from services.shared.nats_client import NATSClient


class CoverageAnalyzer:
    """Analyzes 4D Vision coverage and trends."""
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres = postgres_pool
        self._cache = {}
        
    async def calculate_build_coverage(self, build_id: str, since: datetime) -> Dict[str, Any]:
        """Calculate coverage metrics for a build."""
        async with self.postgres.acquire() as conn:
            # Get all segments for this build
            segments = await conn.fetch(
                """
                SELECT 
                    segment_id,
                    level_name,
                    scene_type,
                    duration_seconds,
                    created_at
                FROM vision_segments
                WHERE build_id = $1 AND created_at >= $2
                ORDER BY created_at
                """,
                build_id, since
            )
            
            # Get issue counts by type
            issues = await conn.fetch(
                """
                SELECT 
                    vi.issue_type,
                    vi.severity,
                    COUNT(*) as count,
                    AVG(vi.confidence) as avg_confidence
                FROM vision_issues vi
                JOIN vision_segments vs ON vi.segment_id = vs.segment_id
                WHERE vs.build_id = $1 AND vs.created_at >= $2
                GROUP BY vi.issue_type, vi.severity
                """,
                build_id, since
            )
            
            # Calculate coverage metrics
            total_segments = len(segments)
            total_duration = sum(s['duration_seconds'] for s in segments)
            
            # Scene coverage
            scenes_covered = set(s['level_name'] for s in segments)
            scene_types_covered = set(s['scene_type'] for s in segments if s['scene_type'])
            
            # Issue breakdown
            issues_by_type = {}
            issues_by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            
            for issue in issues:
                issue_type = issue['issue_type']
                severity = issue['severity']
                count = issue['count']
                
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = {
                        "count": 0,
                        "avg_confidence": 0,
                        "severity_breakdown": {}
                    }
                
                issues_by_type[issue_type]["count"] += count
                issues_by_type[issue_type]["avg_confidence"] = float(issue['avg_confidence'])
                
                # Map severity float to category
                if severity < 0.3:
                    sev_cat = "low"
                elif severity < 0.6:
                    sev_cat = "medium"
                elif severity < 0.8:
                    sev_cat = "high"
                else:
                    sev_cat = "critical"
                    
                issues_by_severity[sev_cat] += count
                
                if sev_cat not in issues_by_type[issue_type]["severity_breakdown"]:
                    issues_by_type[issue_type]["severity_breakdown"][sev_cat] = 0
                issues_by_type[issue_type]["severity_breakdown"][sev_cat] += count
            
            return {
                "build_id": build_id,
                "analysis_period": {
                    "start": since.isoformat(),
                    "end": datetime.utcnow().isoformat()
                },
                "coverage": {
                    "total_segments": total_segments,
                    "total_duration_seconds": total_duration,
                    "scenes_covered": list(scenes_covered),
                    "scene_count": len(scenes_covered),
                    "scene_types_covered": list(scene_types_covered)
                },
                "issues": {
                    "total_count": sum(i['count'] for i in issues),
                    "by_type": issues_by_type,
                    "by_severity": issues_by_severity
                },
                "quality_score": self._calculate_quality_score(
                    total_segments, issues_by_severity, total_duration
                )
            }
    
    async def calculate_scene_coverage(self, build_id: str, scene_name: str) -> Dict[str, Any]:
        """Calculate coverage for a specific scene."""
        async with self.postgres.acquire() as conn:
            # Get segments for this scene
            segments = await conn.fetch(
                """
                SELECT 
                    segment_id,
                    duration_seconds,
                    performance_metrics,
                    created_at
                FROM vision_segments
                WHERE build_id = $1 AND level_name = $2
                ORDER BY created_at
                """,
                build_id, scene_name
            )
            
            if not segments:
                return {
                    "build_id": build_id,
                    "scene_name": scene_name,
                    "coverage": "no_data"
                }
            
            # Get issues for these segments
            segment_ids = [s['segment_id'] for s in segments]
            issues = await conn.fetch(
                """
                SELECT 
                    issue_type,
                    severity,
                    detector_type,
                    affected_goals
                FROM vision_issues
                WHERE segment_id = ANY($1::uuid[])
                """,
                segment_ids
            )
            
            # Performance analysis
            fps_values = []
            for seg in segments:
                if seg['performance_metrics']:
                    metrics = seg['performance_metrics']
                    if 'avg_fps' in metrics:
                        fps_values.append(metrics['avg_fps'])
            
            # Goal impact analysis
            goal_impacts = {}
            for issue in issues:
                if issue['affected_goals']:
                    for goal in issue['affected_goals']:
                        if goal not in goal_impacts:
                            goal_impacts[goal] = 0
                        goal_impacts[goal] += 1
            
            return {
                "build_id": build_id,
                "scene_name": scene_name,
                "coverage": {
                    "segment_count": len(segments),
                    "total_duration": sum(s['duration_seconds'] for s in segments),
                    "first_tested": segments[0]['created_at'].isoformat(),
                    "last_tested": segments[-1]['created_at'].isoformat()
                },
                "issues": {
                    "total": len(issues),
                    "by_detector": self._count_by_field(issues, 'detector_type'),
                    "by_type": self._count_by_field(issues, 'issue_type'),
                    "critical_count": sum(1 for i in issues if i['severity'] >= 0.8)
                },
                "performance": {
                    "avg_fps": np.mean(fps_values) if fps_values else None,
                    "min_fps": np.min(fps_values) if fps_values else None,
                    "fps_stability": np.std(fps_values) if fps_values else None
                },
                "goal_impacts": goal_impacts
            }
    
    async def calculate_trends(self, build_ids: List[str], window_hours: int = 24) -> Dict[str, Any]:
        """Calculate trend data across builds."""
        if not build_ids:
            return {"error": "No builds to analyze"}
        
        async with self.postgres.acquire() as conn:
            # Get issue trends
            issue_trends = await conn.fetch(
                """
                WITH build_issues AS (
                    SELECT 
                        vs.build_id,
                        vi.issue_type,
                        COUNT(*) as count,
                        AVG(vi.severity) as avg_severity
                    FROM vision_issues vi
                    JOIN vision_segments vs ON vi.segment_id = vs.segment_id
                    WHERE vs.build_id = ANY($1::text[])
                        AND vs.created_at >= NOW() - INTERVAL '%s hours'
                    GROUP BY vs.build_id, vi.issue_type
                )
                SELECT * FROM build_issues
                ORDER BY build_id, issue_type
                """,
                build_ids, window_hours
            )
            
            # Get coverage trends
            coverage_trends = await conn.fetch(
                """
                SELECT 
                    build_id,
                    COUNT(DISTINCT level_name) as scenes_tested,
                    COUNT(*) as total_segments,
                    SUM(duration_seconds) as total_duration,
                    MIN(created_at) as first_test,
                    MAX(created_at) as last_test
                FROM vision_segments
                WHERE build_id = ANY($1::text[])
                    AND created_at >= NOW() - INTERVAL '%s hours'
                GROUP BY build_id
                ORDER BY build_id
                """,
                build_ids, window_hours
            )
        
        # Process trends
        trends_by_build = {}
        for build in coverage_trends:
            build_id = build['build_id']
            trends_by_build[build_id] = {
                "coverage": {
                    "scenes_tested": build['scenes_tested'],
                    "total_segments": build['total_segments'],
                    "total_duration": build['total_duration'],
                    "test_window": {
                        "start": build['first_test'].isoformat(),
                        "end": build['last_test'].isoformat()
                    }
                },
                "issues": {}
            }
        
        # Add issue data
        for issue in issue_trends:
            build_id = issue['build_id']
            issue_type = issue['issue_type']
            
            if build_id in trends_by_build:
                trends_by_build[build_id]["issues"][issue_type] = {
                    "count": issue['count'],
                    "avg_severity": float(issue['avg_severity'])
                }
        
        # Calculate deltas between builds
        deltas = []
        for i in range(1, len(build_ids)):
            prev_build = build_ids[i-1]
            curr_build = build_ids[i]
            
            if prev_build in trends_by_build and curr_build in trends_by_build:
                prev_data = trends_by_build[prev_build]
                curr_data = trends_by_build[curr_build]
                
                # Issue count delta
                prev_issues = sum(i["count"] for i in prev_data["issues"].values())
                curr_issues = sum(i["count"] for i in curr_data["issues"].values())
                
                deltas.append({
                    "from_build": prev_build,
                    "to_build": curr_build,
                    "issue_delta": curr_issues - prev_issues,
                    "coverage_delta": {
                        "scenes": curr_data["coverage"]["scenes_tested"] - 
                                 prev_data["coverage"]["scenes_tested"],
                        "segments": curr_data["coverage"]["total_segments"] - 
                                   prev_data["coverage"]["total_segments"]
                    }
                })
        
        return {
            "builds_analyzed": build_ids,
            "window_hours": window_hours,
            "by_build": trends_by_build,
            "deltas": deltas,
            "summary": {
                "improving": len([d for d in deltas if d["issue_delta"] < 0]),
                "degrading": len([d for d in deltas if d["issue_delta"] > 0]),
                "stable": len([d for d in deltas if d["issue_delta"] == 0])
            }
        }
    
    def _calculate_quality_score(self, segments: int, severity_counts: Dict[str, int], 
                                duration: float) -> float:
        """Calculate overall quality score (0-1, higher is better)."""
        if segments == 0:
            return 0.0
        
        # Weight issues by severity
        weighted_issues = (
            severity_counts["low"] * 0.1 +
            severity_counts["medium"] * 0.3 +
            severity_counts["high"] * 0.6 +
            severity_counts["critical"] * 1.0
        )
        
        # Normalize by duration (issues per minute)
        issues_per_minute = weighted_issues / (duration / 60) if duration > 0 else 0
        
        # Convert to quality score (inverse, with diminishing returns)
        quality = 1.0 / (1.0 + issues_per_minute * 0.1)
        
        return round(quality, 3)
    
    def _count_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Count occurrences by field value."""
        counts = {}
        for item in items:
            value = item.get(field, "unknown")
            if value not in counts:
                counts[value] = 0
            counts[value] += 1
        return counts


class CoverageJob:
    """Main coverage job that runs periodically."""
    
    def __init__(self, postgres_pool: asyncpg.Pool, nats_client: NATSClient,
                 config: Optional[Dict[str, Any]] = None):
        self.postgres = postgres_pool
        self.nats = nats_client
        self.config = config or {}
        self.analyzer = CoverageAnalyzer(postgres_pool)
        
        # Job configuration
        self.interval_seconds = self.config.get("interval_seconds", 300)  # 5 minutes
        self.lookback_hours = self.config.get("lookback_hours", 24)
        self.build_limit = self.config.get("build_limit", 10)
        
        self._running = False
        self._task = None
        
    async def start(self):
        """Start the coverage job."""
        if self._running:
            logger.warning("Coverage job already running")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Coverage job started, interval={self.interval_seconds}s")
    
    async def stop(self):
        """Stop the coverage job."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Coverage job stopped")
    
    async def _run_loop(self):
        """Main job loop."""
        while self._running:
            try:
                await self._run_analysis()
            except Exception as e:
                logger.error(f"Coverage analysis failed: {e}")
                
            # Wait for next run
            await asyncio.sleep(self.interval_seconds)
    
    async def _run_analysis(self):
        """Run coverage analysis and emit events."""
        logger.info("Starting coverage analysis")
        
        # Get recent builds
        since = datetime.utcnow() - timedelta(hours=self.lookback_hours)
        builds = await self._get_recent_builds(since)
        
        if not builds:
            logger.warning("No builds found for coverage analysis")
            return
        
        logger.info(f"Analyzing {len(builds)} builds")
        
        # Analyze each build
        for build_id in builds[:self.build_limit]:
            try:
                # Calculate build coverage
                coverage_data = await self.analyzer.calculate_build_coverage(build_id, since)
                
                # Emit coverage event
                await self._emit_coverage_event(coverage_data)
                
                # Analyze key scenes
                for scene in coverage_data["coverage"]["scenes_covered"][:5]:  # Top 5 scenes
                    scene_data = await self.analyzer.calculate_scene_coverage(build_id, scene)
                    await self._emit_scene_coverage_event(scene_data)
                    
            except Exception as e:
                logger.error(f"Failed to analyze build {build_id}: {e}")
        
        # Calculate trends
        if len(builds) > 1:
            try:
                trend_data = await self.analyzer.calculate_trends(
                    builds[:self.build_limit], 
                    self.lookback_hours
                )
                await self._emit_trend_event(trend_data)
            except Exception as e:
                logger.error(f"Failed to calculate trends: {e}")
        
        # Store coverage summary
        await self._store_coverage_summary()
        
        logger.info("Coverage analysis completed")
    
    async def _get_recent_builds(self, since: datetime) -> List[str]:
        """Get list of recent build IDs."""
        async with self.postgres.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT build_id
                FROM vision_segments
                WHERE created_at >= $1
                ORDER BY build_id DESC
                """,
                since
            )
            return [row['build_id'] for row in rows]
    
    async def _emit_coverage_event(self, data: Dict[str, Any]):
        """Emit VISION.COVERAGE event."""
        event = {
            "event_id": str(UUID.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "coverage_report",
            "data": data
        }
        
        await self.nats.publish("VISION.COVERAGE", json.dumps(event))
        logger.debug(f"Emitted coverage event for build {data['build_id']}")
    
    async def _emit_scene_coverage_event(self, data: Dict[str, Any]):
        """Emit scene-level coverage event."""
        event = {
            "event_id": str(UUID.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "scene_coverage_report",
            "data": data
        }
        
        await self.nats.publish("VISION.COVERAGE.SCENE", json.dumps(event))
    
    async def _emit_trend_event(self, data: Dict[str, Any]):
        """Emit VISION.TRENDS event."""
        event = {
            "event_id": str(UUID.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "trend_report",
            "data": data
        }
        
        await self.nats.publish("VISION.TRENDS", json.dumps(event))
        logger.debug(f"Emitted trend event for {len(data['builds_analyzed'])} builds")
    
    async def _store_coverage_summary(self):
        """Store coverage metrics summary."""
        async with self.postgres.acquire() as conn:
            # Get overall metrics
            summary = await conn.fetchrow(
                """
                WITH recent_data AS (
                    SELECT * FROM vision_segments
                    WHERE created_at >= NOW() - INTERVAL '%s hours'
                )
                SELECT 
                    COUNT(DISTINCT build_id) as builds_analyzed,
                    COUNT(DISTINCT level_name) as unique_scenes,
                    COUNT(*) as total_segments,
                    SUM(duration_seconds) as total_duration,
                    (
                        SELECT COUNT(*) FROM vision_issues vi
                        JOIN recent_data rd ON vi.segment_id = rd.segment_id
                    ) as total_issues
                FROM recent_data
                """,
                self.lookback_hours
            )
            
            # Update or insert summary
            await conn.execute(
                """
                INSERT INTO vision_coverage_metrics 
                    (metric_type, time_window, data, created_at)
                VALUES 
                    ($1, $2, $3, $4)
                """,
                "daily_summary",
                f"{self.lookback_hours}h",
                json.dumps({
                    "builds_analyzed": summary['builds_analyzed'],
                    "unique_scenes": summary['unique_scenes'],
                    "total_segments": summary['total_segments'],
                    "total_duration": summary['total_duration'],
                    "total_issues": summary['total_issues'],
                    "issues_per_hour": summary['total_issues'] / self.lookback_hours
                        if self.lookback_hours > 0 else 0
                }),
                datetime.utcnow()
            )


async def main():
    """Main entry point for coverage job."""
    # Initialize components
    postgres = await get_postgres_pool()
    nats_client = await NATSClient.connect()
    
    # Create and start job
    job = CoverageJob(postgres, nats_client, {
        "interval_seconds": 300,  # 5 minutes
        "lookback_hours": 24,
        "build_limit": 10
    })
    
    try:
        await job.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Shutting down coverage job")
    finally:
        await job.stop()
        await nats_client.close()
        await postgres.close()


if __name__ == "__main__":
    logger.add("logs/coverage_job.log", rotation="100 MB")
    asyncio.run(main())
