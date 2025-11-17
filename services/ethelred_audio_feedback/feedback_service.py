"""
Audio Feedback Service - Generates design feedback based on audio metrics.
Implements TAUD-10.
"""
import asyncio
import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import asyncpg
import nats
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Add parent for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.nats_client import get_nats_client
from shared.database import get_postgres_pool

# Import feedback generator
from .feedback_generator import FeedbackGenerator

# Compile protobuf
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2
from services.ethelred_audio.generated import canonical_envelope_pb2 as envelope_pb2

# Metrics
feedback_generated = Counter('audio_feedback_generated_total', 'Total feedback generated', ['archetype'])
feedback_generation_duration = Histogram('audio_feedback_generation_seconds', 'Time to generate feedback')
feedback_errors = Counter('audio_feedback_errors_total', 'Total feedback generation errors', ['error_type'])
active_feedback_jobs = Gauge('audio_feedback_jobs_active', 'Number of active feedback generation jobs')

logger = logging.getLogger(__name__)


class AudioFeedbackService:
    """Generates non-auto-tuning feedback for audio improvements."""
    
    def __init__(self):
        self.nc = None
        self.js = None
        self.postgres_pool = None
        self.feedback_generator = FeedbackGenerator()
        self._running = False
    
    async def connect(self):
        """Connect to NATS and PostgreSQL."""
        # Connect to NATS
        self.nc = await get_nats_client()
        self.js = self.nc.jetstream()
        
        # Connect to PostgreSQL
        self.postgres_pool = await get_postgres_pool()
        
        logger.info("Audio Feedback Service connected to NATS and PostgreSQL")
    
    async def disconnect(self):
        """Disconnect from services."""
        if self.nc:
            await self.nc.close()
        if self.postgres_pool:
            await self.postgres_pool.close()
    
    async def start(self):
        """Start the feedback service."""
        if self._running:
            logger.warning("Feedback service already running")
            return
        
        self._running = True
        await self.connect()
        
        # Start Prometheus metrics server
        start_http_server(8095)
        logger.info("Prometheus metrics server started on port 8095")
        
        # Subscribe to report events to generate feedback
        await self.nc.subscribe(
            "events.ethelred.audio.v1.report",
            cb=self._handle_report_event
        )
        
        # Subscribe to manual feedback requests
        await self.nc.subscribe(
            "cmd.audio.generate_feedback",
            cb=self._handle_feedback_request
        )
        
        logger.info("Audio Feedback Service started")
        
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Feedback service cancelled")
        finally:
            await self.disconnect()
    
    async def _handle_report_event(self, msg: nats.Msg):
        """Handle incoming audio report events."""
        try:
            # Parse protobuf message
            nats_report = audio_pb2.NatsAudioReport()
            nats_report.ParseFromString(msg.data)
            
            # Extract report data
            report = nats_report.payload
            envelope = nats_report.envelope
            
            # Skip if not enough data
            if report.summary.num_segments < 10:
                logger.info(
                    f"Skipping feedback for {report.archetype_id} - "
                    f"insufficient segments ({report.summary.num_segments})"
                )
                return
            
            # Generate feedback
            asyncio.create_task(
                self._generate_feedback_for_report(
                    report.build_id,
                    report.archetype_id,
                    report.language_code
                )
            )
            
        except Exception as e:
            logger.error(f"Error handling report event: {e}", exc_info=True)
            feedback_errors.labels(error_type='report_event_handling').inc()
    
    async def _handle_feedback_request(self, msg: nats.Msg):
        """Handle manual feedback generation request."""
        try:
            request = json.loads(msg.data.decode())
            build_id = request.get('build_id')
            archetype_id = request.get('archetype_id')
            
            if not build_id:
                await msg.respond(json.dumps({
                    'success': False,
                    'error': 'build_id required'
                }).encode())
                return
            
            # Generate feedback
            if archetype_id:
                # Single archetype
                asyncio.create_task(
                    self._generate_feedback_for_archetype(build_id, archetype_id)
                )
            else:
                # All archetypes
                asyncio.create_task(
                    self._generate_feedback_for_build(build_id)
                )
            
            await msg.respond(json.dumps({
                'success': True,
                'message': f'Feedback generation started for build {build_id}'
            }).encode())
            
        except Exception as e:
            logger.error(f"Error handling feedback request: {e}", exc_info=True)
            await msg.respond(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
    
    async def _generate_feedback_for_report(
        self,
        build_id: str,
        archetype_id: str,
        language_code: str
    ):
        """Generate feedback for a specific report."""
        active_feedback_jobs.inc()
        try:
            with feedback_generation_duration.time():
                # Fetch report data
                async with self.postgres_pool.acquire() as conn:
                    report_row = await conn.fetchrow(
                        """
                        SELECT report_summary
                        FROM audio_archetype_reports
                        WHERE build_id = $1
                            AND archetype_id = $2
                            AND language_code = $3
                        """,
                        build_id, archetype_id, language_code
                    )
                
                if not report_row or not report_row['report_summary']:
                    logger.warning(
                        f"No report found for {build_id}/{archetype_id}/{language_code}"
                    )
                    return
                
                report_data = json.loads(report_row['report_summary'])
                
                # Get detailed metrics if available
                detailed_metrics = await self._get_detailed_metrics(
                    build_id, archetype_id, language_code
                )
                
                # Generate feedback
                feedback = self.feedback_generator.generate_archetype_feedback(
                    archetype_id, report_data, detailed_metrics
                )
                
                # Add language info
                feedback['language_code'] = language_code
                
                # Store feedback
                await self._store_feedback(feedback)
                
                # Emit feedback event
                await self._emit_feedback_event(feedback)
                
                feedback_generated.labels(archetype=archetype_id).inc()
                
                logger.info(
                    f"Generated feedback for {archetype_id}/{language_code}: "
                    f"{len(feedback['findings'])} findings"
                )
                
        except Exception as e:
            logger.error(
                f"Error generating feedback for {archetype_id}: {e}",
                exc_info=True
            )
            feedback_errors.labels(error_type='feedback_generation').inc()
        finally:
            active_feedback_jobs.dec()
    
    async def _generate_feedback_for_archetype(
        self,
        build_id: str,
        archetype_id: str
    ):
        """Generate feedback for all languages of an archetype."""
        # Get all languages for this archetype
        async with self.postgres_pool.acquire() as conn:
            languages = await conn.fetch(
                """
                SELECT DISTINCT language_code
                FROM audio_archetype_reports
                WHERE build_id = $1 AND archetype_id = $2
                """,
                build_id, archetype_id
            )
        
        for row in languages:
            await self._generate_feedback_for_report(
                build_id, archetype_id, row['language_code']
            )
    
    async def _generate_feedback_for_build(self, build_id: str):
        """Generate feedback for all archetypes in a build."""
        # Get all archetype/language combinations
        async with self.postgres_pool.acquire() as conn:
            combinations = await conn.fetch(
                """
                SELECT DISTINCT archetype_id, language_code
                FROM audio_archetype_reports
                WHERE build_id = $1
                """,
                build_id
            )
        
        for row in combinations:
            await self._generate_feedback_for_report(
                build_id, row['archetype_id'], row['language_code']
            )
        
        # Generate simulator feedback if applicable
        await self._generate_simulator_feedback(build_id)
    
    async def _get_detailed_metrics(
        self,
        build_id: str,
        archetype_id: str,
        language_code: str
    ) -> Optional[Dict]:
        """Get detailed voice characteristic metrics."""
        # In a full implementation, this would aggregate detailed
        # measurements from individual segments
        # For now, return placeholder data
        return {
            'mean_f0': 120,  # Hz
            'roughness': 0.4,
            'breathiness': 0.2,
            'spectral_tilt': -6.5  # dB/octave
        }
    
    async def _generate_simulator_feedback(self, build_id: str):
        """Generate feedback for simulator stability across build."""
        async with self.postgres_pool.acquire() as conn:
            # Get aggregated simulator stability data
            stability_data = await conn.fetch(
                """
                SELECT 
                    seg.archetype_id,
                    AVG(s.simulator_stability_score) as avg_stability,
                    COUNT(*) as segment_count,
                    SUM(CASE WHEN s.simulator_stability_band = 'unstable' THEN 1 ELSE 0 END) as unstable_count
                FROM audio_scores s
                JOIN audio_segments seg ON s.segment_id = seg.segment_id
                WHERE seg.build_id = $1
                    AND seg.simulator_applied = true
                GROUP BY seg.archetype_id
                HAVING AVG(s.simulator_stability_score) < 0.9
                """,
                build_id
            )
        
        for row in stability_data:
            archetype_id = row['archetype_id']
            aggregated_data = {
                'mean_stability': float(row['avg_stability']),
                'instability_rate': row['unstable_count'] / row['segment_count'],
                'instability_types': {
                    'glitches': 0.05,  # Would be calculated from detailed analysis
                    'parameter_jumps': 0.02,
                    'clipping': 0.01
                }
            }
            
            # Generate simulator-specific feedback
            simulator_profile_id = f"{archetype_id}_v1"
            feedback = self.feedback_generator.generate_simulator_feedback(
                simulator_profile_id, aggregated_data
            )
            
            # Store and emit
            feedback['build_id'] = build_id
            feedback['archetype_id'] = archetype_id
            
            await self._store_feedback(feedback)
            await self._emit_feedback_event(feedback)
    
    async def _store_feedback(self, feedback: Dict):
        """Store feedback in database."""
        # For now, log it
        # In production, would store in a feedback table
        logger.info(
            f"Storing feedback for {feedback.get('archetype_id')}: "
            f"{len(feedback.get('findings', []))} findings"
        )
    
    def _create_timestamp(self, dt: datetime) -> Any:
        """Create protobuf timestamp."""
        from google.protobuf.timestamp_pb2 import Timestamp
        ts = Timestamp()
        ts.FromDatetime(dt.astimezone(timezone.utc))
        return ts
    
    async def _emit_feedback_event(self, feedback: Dict):
        """Emit AUDIO.FEEDBACK event to NATS."""
        # Create AudioFeedback protobuf
        audio_feedback = audio_pb2.AudioFeedback(
            build_id=feedback['build_id'],
            archetype_id=feedback['archetype_id']
        )
        
        if 'simulator_profile_id' in feedback:
            audio_feedback.simulator_profile_id = feedback['simulator_profile_id']
        
        # Add findings
        for finding in feedback.get('findings', []):
            fb_finding = audio_pb2.FeedbackFinding(
                dimension=finding['dimension'],
                observed_mean=finding['observed_mean'],
                target_range=finding['target_range'],
                recommendation=finding['recommendation']
            )
            audio_feedback.findings.append(fb_finding)
        
        # Add training examples
        for example in feedback.get('candidate_training_examples', []):
            training_ex = audio_pb2.CandidateTrainingExample(
                segment_id=example['segment_id'],
                media_uri=example['media_uri'],
                labels=example['labels']
            )
            audio_feedback.candidate_training_examples.append(training_ex)
        
        if feedback.get('notes'):
            audio_feedback.notes = feedback['notes']
        
        # Create envelope
        now = datetime.now(timezone.utc)
        envelope = envelope_pb2.CanonicalEnvelope(
            trace_id=str(uuid4()),
            build_id=feedback['build_id'],
            timestamp_range=envelope_pb2.TimestampRange(
                start=self._create_timestamp(now),
                end=self._create_timestamp(now)
            ),
            domain="Audio",
            issue_type="AUDIO.FEEDBACK",
            severity=envelope_pb2.Severity.INFO,
            confidence=1.0,
            goal_tags=["G-DESIGN-FEEDBACK"],
            metadata={
                "archetype": feedback['archetype_id'],
                "auto_apply": "false"  # Never auto-apply
            }
        )
        
        # Create NATS message
        nats_message = audio_pb2.NatsAudioFeedback(
            envelope=envelope,
            payload=audio_feedback
        )
        
        # Publish to NATS
        await self.nc.publish(
            "events.ethelred.audio.v1.feedback",
            nats_message.SerializeToString()
        )
        
        logger.info(f"Emitted AUDIO.FEEDBACK event for {feedback['archetype_id']}")


async def main():
    """Run the audio feedback service."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    service = AudioFeedbackService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Shutting down audio feedback service...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

