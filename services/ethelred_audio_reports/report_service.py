"""
Audio Report Service - Generates batch reports for archetypes and languages.
Implements TAUD-09.
"""
import asyncio
import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
from uuid import uuid4

import asyncpg
import nats
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Add parent for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.nats_client import get_nats_client
from shared.database import get_postgres_pool

# Import report aggregator
from .report_aggregator import AudioReportAggregator

# Compile protobuf
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2
from services.ethelred_audio.generated import canonical_envelope_pb2 as envelope_pb2

# Metrics
reports_generated = Counter('audio_reports_generated_total', 'Total audio reports generated', ['archetype', 'language'])
report_generation_duration = Histogram('audio_report_generation_seconds', 'Time to generate reports')
report_errors = Counter('audio_report_errors_total', 'Total report generation errors', ['error_type'])
active_report_jobs = Gauge('audio_report_jobs_active', 'Number of active report generation jobs')

logger = logging.getLogger(__name__)


class AudioReportService:
    """Generates and emits audio quality reports."""
    
    def __init__(self):
        self.nc = None
        self.js = None
        self.postgres_pool = None
        self.aggregator = None
        self._running = False
        self._report_interval = 3600  # Generate reports every hour
        self._active_builds: Set[str] = set()
    
    async def connect(self):
        """Connect to NATS and PostgreSQL."""
        # Connect to NATS
        self.nc = await get_nats_client()
        self.js = self.nc.jetstream()
        
        # Connect to PostgreSQL
        self.postgres_pool = await get_postgres_pool()
        
        # Initialize aggregator
        self.aggregator = AudioReportAggregator(self.postgres_pool)
        
        logger.info("Audio Report Service connected to NATS and PostgreSQL")
    
    async def disconnect(self):
        """Disconnect from services."""
        if self.nc:
            await self.nc.close()
        if self.postgres_pool:
            await self.postgres_pool.close()
    
    async def start(self):
        """Start the report service."""
        if self._running:
            logger.warning("Report service already running")
            return
        
        self._running = True
        await self.connect()
        
        # Start Prometheus metrics server
        start_http_server(8094)
        logger.info("Prometheus metrics server started on port 8094")
        
        # Start periodic report generation
        asyncio.create_task(self._periodic_report_generation())
        
        # Start listening for manual report requests
        await self.nc.subscribe(
            "cmd.audio.generate_report",
            cb=self._handle_report_request
        )
        
        logger.info("Audio Report Service started")
        
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Report service cancelled")
        finally:
            await self.disconnect()
    
    async def _periodic_report_generation(self):
        """Periodically generate reports for active builds."""
        while self._running:
            try:
                # Wait for the interval
                await asyncio.sleep(self._report_interval)
                
                # Get active builds from last 24 hours
                async with self.postgres_pool.acquire() as conn:
                    active_builds = await conn.fetch(
                        """
                        SELECT DISTINCT build_id
                        FROM audio_segments
                        WHERE created_at >= NOW() - INTERVAL '24 hours'
                        """
                    )
                
                for row in active_builds:
                    build_id = row['build_id']
                    if build_id not in self._active_builds:
                        self._active_builds.add(build_id)
                        asyncio.create_task(self._generate_build_reports(build_id))
                
            except Exception as e:
                logger.error(f"Error in periodic report generation: {e}", exc_info=True)
                report_errors.labels(error_type='periodic_generation').inc()
    
    async def _handle_report_request(self, msg: nats.Msg):
        """Handle manual report generation request."""
        try:
            request = json.loads(msg.data.decode())
            build_id = request.get('build_id')
            
            if not build_id:
                await msg.respond(json.dumps({
                    'success': False,
                    'error': 'build_id required'
                }).encode())
                return
            
            # Generate reports for this build
            asyncio.create_task(self._generate_build_reports(build_id))
            
            await msg.respond(json.dumps({
                'success': True,
                'message': f'Report generation started for build {build_id}'
            }).encode())
            
        except Exception as e:
            logger.error(f"Error handling report request: {e}", exc_info=True)
            await msg.respond(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
    
    async def _generate_build_reports(self, build_id: str):
        """Generate all reports for a build."""
        active_report_jobs.inc()
        try:
            with report_generation_duration.time():
                # Get all archetype/language combinations for this build
                async with self.postgres_pool.acquire() as conn:
                    combinations = await conn.fetch(
                        """
                        SELECT DISTINCT archetype_id, language_code
                        FROM audio_segments
                        WHERE build_id = $1
                            AND archetype_id IS NOT NULL
                        """,
                        build_id
                    )
                
                logger.info(f"Generating reports for {len(combinations)} archetype/language combinations in build {build_id}")
                
                # Generate report for each combination
                for row in combinations:
                    archetype_id = row['archetype_id']
                    language_code = row['language_code']
                    
                    try:
                        # Generate report
                        report = await self.aggregator.generate_archetype_report(
                            build_id, archetype_id, language_code
                        )
                        
                        # Update comparison with current data
                        if 'comparison_prev_build' in report and report['comparison_prev_build']:
                            comparison = report['comparison_prev_build']
                            # Calculate actual deltas
                            for metric in ['archetype_conformity', 'simulator_stability']:
                                if metric in report['summary']:
                                    current_mean = report['summary'][metric]['mean']
                                    # Get previous mean from stored report
                                    prev_report = await self._get_previous_report(
                                        comparison['build_id'], archetype_id, language_code
                                    )
                                    if prev_report and metric in prev_report.get('summary', {}):
                                        prev_mean = prev_report['summary'][metric]['mean']
                                        comparison['deltas'][f'{metric}_delta'] = current_mean - prev_mean
                        
                        # Store report
                        report_id = await self.aggregator.store_report(report)
                        
                        # Emit AUDIO.REPORT event
                        await self._emit_report_event(report, report_id)
                        
                        reports_generated.labels(
                            archetype=archetype_id,
                            language=language_code
                        ).inc()
                        
                    except Exception as e:
                        logger.error(
                            f"Error generating report for {archetype_id}/{language_code}: {e}",
                            exc_info=True
                        )
                        report_errors.labels(error_type='report_generation').inc()
                
                # Generate build summary
                build_summary = await self.aggregator.get_build_summary(build_id)
                await self._emit_build_summary_event(build_summary)
                
                logger.info(f"Completed report generation for build {build_id}")
                
        finally:
            active_report_jobs.dec()
            # Remove from active builds after processing
            self._active_builds.discard(build_id)
    
    async def _get_previous_report(
        self,
        build_id: str,
        archetype_id: str,
        language_code: str
    ) -> Optional[Dict]:
        """Get previous report data."""
        async with self.postgres_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT report_summary
                FROM audio_archetype_reports
                WHERE build_id = $1
                    AND archetype_id = $2
                    AND language_code = $3
                """,
                build_id, archetype_id, language_code
            )
            
            if row and row['report_summary']:
                try:
                    return json.loads(row['report_summary'])
                except json.JSONDecodeError:
                    return None
            
            return None
    
    def _create_timestamp(self, dt: datetime) -> Any:
        """Create protobuf timestamp."""
        from google.protobuf.timestamp_pb2 import Timestamp
        ts = Timestamp()
        ts.FromDatetime(dt.astimezone(timezone.utc))
        return ts
    
    async def _emit_report_event(self, report: Dict, report_id: str):
        """Emit AUDIO.REPORT event to NATS."""
        # Create AudioReport protobuf
        audio_report = audio_pb2.AudioReport(
            build_id=report['build_id'],
            archetype_id=report['archetype_id'],
            language_code=report['language_code']
        )
        
        # Add summary
        if 'summary' in report and report['num_segments'] > 0:
            summary = audio_pb2.ArchetypeReportSummary(
                num_segments=report['num_segments']
            )
            
            # Add distribution data
            if 'intelligibility' in report['summary']:
                intell_dist = report['summary']['intelligibility'].get('band_distribution', {})
                for band, proportion in intell_dist.items():
                    summary.intelligibility_distribution[band] = proportion
            
            # Add mean scores
            for metric, field in [
                ('naturalness', 'naturalness_mean'),
                ('archetype_conformity', 'archetype_conformity_mean'),
                ('simulator_stability', 'simulator_stability_mean'),
                ('mix_quality', 'mix_quality_mean')
            ]:
                if metric in report['summary']:
                    setattr(summary, field, report['summary'][metric]['mean'])
            
            audio_report.summary.CopyFrom(summary)
        
        # Add common deviations
        audio_report.common_deviations.extend(report.get('common_deviations', []))
        
        # Add comparison with previous build
        if report.get('comparison_prev_build'):
            comparison = report['comparison_prev_build']
            build_comp = audio_pb2.BuildComparison(
                build_id=comparison['build_id']
            )
            
            if 'archetype_conformity_delta' in comparison.get('deltas', {}):
                build_comp.archetype_conformity_delta = comparison['deltas']['archetype_conformity_delta']
            if 'simulator_stability_delta' in comparison.get('deltas', {}):
                build_comp.simulator_stability_delta = comparison['deltas']['simulator_stability_delta']
            
            if comparison.get('notes'):
                build_comp.notes = comparison['notes']
            
            audio_report.comparison_prev_build.CopyFrom(build_comp)
        
        # Create envelope
        now = datetime.now(timezone.utc)
        envelope = envelope_pb2.CanonicalEnvelope(
            trace_id=str(uuid4()),
            build_id=report['build_id'],
            timestamp_range=envelope_pb2.TimestampRange(
                start=self._create_timestamp(now),
                end=self._create_timestamp(now)
            ),
            domain="Audio",
            issue_type="AUDIO.REPORT",
            severity=envelope_pb2.Severity.INFO,
            confidence=1.0,
            goal_tags=["G-QA", "G-DESIGN-FEEDBACK"],
            metadata={
                "report_id": report_id,
                "archetype": report['archetype_id'],
                "language": report['language_code']
            }
        )
        
        # Create NATS message
        nats_message = audio_pb2.NatsAudioReport(
            envelope=envelope,
            payload=audio_report
        )
        
        # Publish to NATS
        await self.nc.publish(
            "events.ethelred.audio.v1.report",
            nats_message.SerializeToString()
        )
        
        logger.info(f"Emitted AUDIO.REPORT event for {report['archetype_id']}/{report['language_code']}")
    
    async def _emit_build_summary_event(self, build_summary: Dict):
        """Emit build-level summary event."""
        # For now, log the summary
        # In production, this could be a separate event type
        logger.info(
            f"Build {build_summary['build_id']} summary: "
            f"{build_summary['total_archetypes']} archetypes, "
            f"{build_summary['total_languages']} languages"
        )


async def main():
    """Run the audio report service."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    service = AudioReportService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Shutting down audio report service...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

