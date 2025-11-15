"""
Audio Metrics Service - Analyzes audio segments and produces quality scores
"""
import asyncio
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import asyncpg
import nats
from nats.js import JetStreamContext
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Add parent for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.nats_client import get_nats_client
from shared.database import get_postgres_pool

# Import audio capture media storage for retrieval
from services.ethelred_audio_capture.media_storage import MediaStorageHandler, MediaCache

# Import real analyzers (Milestone 3)
from services.ethelred_audio_metrics.intelligibility_analyzer import IntelligibilityAnalyzer
from services.ethelred_audio_metrics.naturalness_analyzer import NaturalnessAnalyzer
from services.ethelred_audio_metrics.archetype_analyzer import ArchetypeConformityAnalyzer
from services.ethelred_audio_metrics.simulator_analyzer import SimulatorStabilityAnalyzer

# Compile protobuf
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2

# Metrics
segments_analyzed = Counter('audio_segments_analyzed_total', 'Total segments analyzed', ['segment_type'])
analysis_duration = Histogram('audio_analysis_duration_seconds', 'Time to analyze segments', ['metric_type'])
analysis_errors = Counter('audio_analysis_errors_total', 'Total analysis errors', ['error_type'])
score_distribution = Histogram('audio_score_distribution', 'Distribution of scores', ['score_type', 'band'])
active_analysis_queue = Gauge('audio_analysis_queue_depth', 'Number of segments waiting for analysis')

logger = logging.getLogger(__name__)


class AudioMetricsAnalyzer:
    """Analyzes audio segments to produce quality metrics."""
    
    def __init__(self):
        # Initialize real analyzers (Milestone 3)
        self.intelligibility_analyzer = IntelligibilityAnalyzer()
        self.naturalness_analyzer = NaturalnessAnalyzer()
        self.archetype_analyzer = ArchetypeConformityAnalyzer()
        self.simulator_analyzer = SimulatorStabilityAnalyzer()
        
    async def analyze_intelligibility(self, 
                                    audio_data: np.ndarray, 
                                    sample_rate: int,
                                    language_code: str) -> Tuple[float, str]:
        """Analyze speech intelligibility using real analyzer."""
        with analysis_duration.labels(metric_type='intelligibility').time():
            # Use real intelligibility analyzer
            return self.intelligibility_analyzer.analyze(audio_data)
    
    async def analyze_naturalness(self,
                                audio_data: np.ndarray,
                                sample_rate: int) -> Tuple[float, str]:
        """Analyze speech naturalness and prosody using real analyzer."""
        with analysis_duration.labels(metric_type='naturalness').time():
            # Use real naturalness analyzer
            return self.naturalness_analyzer.analyze(audio_data)
    
    async def analyze_archetype_conformity(self,
                                         audio_data: np.ndarray,
                                         sample_rate: int,
                                         archetype_id: Optional[str]) -> Tuple[float, str]:
        """Analyze conformity to archetype voice profile using real analyzer."""
        with analysis_duration.labels(metric_type='archetype').time():
            if not archetype_id:
                return 1.0, "on_profile"  # No archetype to compare
            
            # Use real archetype conformity analyzer
            return self.archetype_analyzer.analyze(audio_data, archetype_id)
    
    async def analyze_simulator_stability(self,
                                        audio_data: np.ndarray,
                                        sample_rate: int,
                                        simulator_applied: bool,
                                        simulator_metadata: Optional[Dict] = None) -> Tuple[float, str]:
        """Analyze vocal simulator stability using real analyzer."""
        with analysis_duration.labels(metric_type='simulator').time():
            if not simulator_applied:
                return 1.0, "stable"  # No simulator to analyze
            
            # Use real simulator stability analyzer
            return self.simulator_analyzer.analyze(audio_data, simulator_metadata)
    
    async def analyze_mix_quality(self,
                                audio_data: np.ndarray,
                                sample_rate: int) -> Tuple[float, str]:
        """Analyze overall mix quality (stub)."""
        with analysis_duration.labels(metric_type='mix_quality').time():
            # Check for various quality issues
            
            # RMS level
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            # Dynamic range (simplified)
            peak = np.max(np.abs(audio_data))
            dynamic_range = peak / (rms + 1e-10)
            
            # Noise floor estimate (very simplified)
            quiet_threshold = np.percentile(np.abs(audio_data), 10)
            
            # Score based on heuristics
            score = 0.8
            band = "ok"
            
            if rms < 0.05:
                score -= 0.2  # Too quiet
                band = "unbalanced"
            elif rms > 0.8:
                score -= 0.3  # Too loud
                band = "clipping"
            
            if dynamic_range < 2:
                score -= 0.1  # Poor dynamic range
            
            if quiet_threshold > 0.1:
                score -= 0.15  # High noise floor
                if band == "ok":
                    band = "noisy"
            
            score = max(0.0, min(1.0, score + np.random.uniform(-0.05, 0.05)))
            
            return score, band


class AudioMetricsService:
    """Main audio metrics service."""
    
    def __init__(self,
                 postgres_pool: asyncpg.Pool,
                 nats_client: nats.NATS,
                 media_storage: MediaStorageHandler):
        self.postgres = postgres_pool
        self.nc = nats_client
        self.media_storage = media_storage
        
        # Components
        self.analyzer = AudioMetricsAnalyzer()
        self.media_cache = MediaCache(max_size_mb=500)
        
        # Processing queue
        self.processing_queue = asyncio.Queue(maxsize=100)
        self.workers = []
        
        # NATS subjects
        self.SEGMENT_CREATED_SUBJECT = 'svc.ethelred.audio.v1.segment_created'
        self.SCORES_SUBJECT = 'events.ethelred.audio.v1.scores'
    
    async def start(self, num_workers: int = 4):
        """Start the metrics service."""
        logger.info(f"Starting Audio Metrics Service with {num_workers} workers")
        
        # Start metrics server
        start_http_server(8091)
        
        # Subscribe to segment created events
        await self.nc.subscribe(
            self.SEGMENT_CREATED_SUBJECT,
            cb=self._handle_segment_created,
            queue='audio-metrics'
        )
        
        # Start worker tasks
        for i in range(num_workers):
            worker = asyncio.create_task(self._process_segments(i))
            self.workers.append(worker)
        
        logger.info("Audio Metrics Service started")
    
    async def _handle_segment_created(self, msg):
        """Handle incoming segment created events."""
        try:
            # Parse event
            event = audio_pb2.SegmentCreatedEvent()
            event.ParseFromString(msg.data)
            
            # Add to processing queue
            await self.processing_queue.put(event)
            active_analysis_queue.set(self.processing_queue.qsize())
            
            logger.debug(f"Queued segment {event.segment_id} for analysis")
            
        except Exception as e:
            logger.error(f"Error handling segment created event: {e}")
            analysis_errors.labels(error_type='parsing_error').inc()
    
    async def _process_segments(self, worker_id: int):
        """Worker task to process segments from queue."""
        logger.info(f"Worker {worker_id} started")
        
        while True:
            try:
                # Get segment from queue
                event = await self.processing_queue.get()
                active_analysis_queue.set(self.processing_queue.qsize())
                
                # Process segment
                await self._analyze_segment(event)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                analysis_errors.labels(error_type='processing_error').inc()
    
    async def _analyze_segment(self, event: audio_pb2.SegmentCreatedEvent):
        """Analyze a single audio segment."""
        segment_id = event.segment_id
        logger.debug(f"Analyzing segment {segment_id}")
        
        try:
            # Retrieve audio data
            audio_data, sample_rate = await self._get_audio_data(event.media_uri)
            if audio_data is None:
                logger.error(f"Failed to retrieve audio for segment {segment_id}")
                analysis_errors.labels(error_type='retrieval_error').inc()
                return
            
            # Run all analyses
            intelligibility_score, intelligibility_band = await self.analyzer.analyze_intelligibility(
                audio_data, sample_rate, event.language_code
            )
            
            naturalness_score, naturalness_band = await self.analyzer.analyze_naturalness(
                audio_data, sample_rate
            )
            
            archetype_score, archetype_band = await self.analyzer.analyze_archetype_conformity(
                audio_data, sample_rate, event.speaker.archetype_id if event.speaker.archetype_id else None
            )
            
            simulator_score, simulator_band = await self.analyzer.analyze_simulator_stability(
                audio_data, sample_rate, event.simulator_applied
            )
            
            mix_score, mix_band = await self.analyzer.analyze_mix_quality(
                audio_data, sample_rate
            )
            
            # Store scores in database
            await self._store_scores(
                segment_id,
                intelligibility_score, intelligibility_band,
                naturalness_score, naturalness_band,
                archetype_score, archetype_band,
                simulator_score, simulator_band,
                mix_score, mix_band
            )
            
            # Create and emit scores event
            scores_event = self._create_scores_event(
                event,
                intelligibility_score, intelligibility_band,
                naturalness_score, naturalness_band,
                archetype_score, archetype_band,
                simulator_score, simulator_band,
                mix_score, mix_band
            )
            
            await self.nc.publish(
                self.SCORES_SUBJECT,
                scores_event.SerializeToString()
            )
            
            # Update metrics
            segments_analyzed.labels(segment_type=self._get_segment_type_name(event.segment_type)).inc()
            
            # Update score distributions
            score_distribution.labels(score_type='intelligibility', band=intelligibility_band).observe(intelligibility_score)
            score_distribution.labels(score_type='naturalness', band=naturalness_band).observe(naturalness_score)
            score_distribution.labels(score_type='archetype', band=archetype_band).observe(archetype_score)
            score_distribution.labels(score_type='simulator', band=simulator_band).observe(simulator_score)
            score_distribution.labels(score_type='mix_quality', band=mix_band).observe(mix_score)
            
            logger.info(f"Analyzed segment {segment_id}: intelligibility={intelligibility_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error analyzing segment {segment_id}: {e}")
            analysis_errors.labels(error_type='analysis_error').inc()
    
    async def _get_audio_data(self, media_uri: str) -> Optional[Tuple[np.ndarray, int]]:
        """Retrieve audio data from media storage."""
        # Check cache first
        cached = self.media_cache.get(media_uri)
        if cached:
            return cached
        
        # Retrieve from storage
        result = await self.media_storage.retrieve_segment(media_uri)
        if result:
            audio_data, sample_rate = result
            # Normalize to float32 [-1, 1]
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Cache for future use
            self.media_cache.put(media_uri, audio_data, sample_rate)
            
            return audio_data, sample_rate
        
        return None
    
    async def _store_scores(self, segment_id: str, *scores):
        """Store analysis scores in database."""
        await self.postgres.execute("""
            INSERT INTO audio_scores (
                segment_id,
                intelligibility, intelligibility_band,
                naturalness, naturalness_band,
                archetype_conformity, archetype_band,
                simulator_stability, stability_band,
                mix_quality, mix_quality_band,
                analysis_version
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (segment_id) DO UPDATE SET
                intelligibility = EXCLUDED.intelligibility,
                intelligibility_band = EXCLUDED.intelligibility_band,
                naturalness = EXCLUDED.naturalness,
                naturalness_band = EXCLUDED.naturalness_band,
                archetype_conformity = EXCLUDED.archetype_conformity,
                archetype_band = EXCLUDED.archetype_band,
                simulator_stability = EXCLUDED.simulator_stability,
                stability_band = EXCLUDED.stability_band,
                mix_quality = EXCLUDED.mix_quality,
                mix_quality_band = EXCLUDED.mix_quality_band,
                analyzed_at = CURRENT_TIMESTAMP
        """, segment_id, *scores, "v0.1.0-stub")
    
    def _create_scores_event(self, 
                           segment_event: audio_pb2.SegmentCreatedEvent,
                           *scores) -> audio_pb2.AudioScoresEvent:
        """Create audio scores protobuf event."""
        event = audio_pb2.AudioScoresEvent()
        
        # Copy envelope with updated type
        event.envelope.CopyFrom(segment_event.envelope)
        event.envelope.issue_type = "AUDIO.SCORES"
        
        # Copy segment info
        event.segment_id = segment_event.segment_id
        event.segment_type = segment_event.segment_type
        event.speaker.CopyFrom(segment_event.speaker)
        event.language_code = segment_event.language_code
        event.context.CopyFrom(segment_event.context)
        event.simulator_applied = segment_event.simulator_applied
        
        # Set scores
        (intelligibility_score, intelligibility_band,
         naturalness_score, naturalness_band,
         archetype_score, archetype_band,
         simulator_score, simulator_band,
         mix_score, mix_band) = scores
        
        event.scores.intelligibility = intelligibility_score
        event.scores.naturalness = naturalness_score
        event.scores.archetype_conformity = archetype_score
        event.scores.simulator_stability = simulator_score
        event.scores.mix_quality = mix_score
        
        # Set bands using enum mapping
        event.bands.intelligibility = self._map_intelligibility_band(intelligibility_band)
        event.bands.naturalness = self._map_naturalness_band(naturalness_band)
        event.bands.archetype_conformity = self._map_archetype_band(archetype_band)
        event.bands.simulator_stability = self._map_stability_band(simulator_band)
        event.bands.mix_quality = self._map_mix_quality_band(mix_band)
        
        # Add some stub additional metrics
        event.additional_metrics["snr_db"] = float(np.random.uniform(30, 50))
        event.additional_metrics["pitch_variability"] = float(np.random.uniform(0.5, 0.9))
        
        return event
    
    def _get_segment_type_name(self, segment_type: int) -> str:
        """Convert protobuf enum to string."""
        mapping = {
            audio_pb2.SEGMENT_TYPE_DIALOGUE: "dialogue",
            audio_pb2.SEGMENT_TYPE_MONSTER_VOCALIZATION: "monster_vocalization",
            audio_pb2.SEGMENT_TYPE_AMBIENT: "ambient",
            audio_pb2.SEGMENT_TYPE_MIXED_BUS: "mixed_bus"
        }
        return mapping.get(segment_type, "unknown")
    
    def _map_intelligibility_band(self, band: str) -> int:
        """Map string band to protobuf enum."""
        mapping = {
            "acceptable": audio_pb2.INTELLIGIBILITY_ACCEPTABLE,
            "degraded": audio_pb2.INTELLIGIBILITY_DEGRADED,
            "unacceptable": audio_pb2.INTELLIGIBILITY_UNACCEPTABLE
        }
        return mapping.get(band, audio_pb2.INTELLIGIBILITY_UNSPECIFIED)
    
    def _map_naturalness_band(self, band: str) -> int:
        mapping = {
            "ok": audio_pb2.NATURALNESS_OK,
            "robotic": audio_pb2.NATURALNESS_ROBOTIC,
            "monotone": audio_pb2.NATURALNESS_MONOTONE
        }
        return mapping.get(band, audio_pb2.NATURALNESS_UNSPECIFIED)
    
    def _map_archetype_band(self, band: str) -> int:
        mapping = {
            "on_profile": audio_pb2.ARCHETYPE_ON_PROFILE,
            "too_clean": audio_pb2.ARCHETYPE_TOO_CLEAN,
            "too_flat": audio_pb2.ARCHETYPE_TOO_FLAT,
            "misaligned": audio_pb2.ARCHETYPE_MISALIGNED
        }
        return mapping.get(band, audio_pb2.ARCHETYPE_UNSPECIFIED)
    
    def _map_stability_band(self, band: str) -> int:
        mapping = {
            "stable": audio_pb2.STABILITY_STABLE,
            "unstable": audio_pb2.STABILITY_UNSTABLE
        }
        return mapping.get(band, audio_pb2.STABILITY_UNSPECIFIED)
    
    def _map_mix_quality_band(self, band: str) -> int:
        mapping = {
            "ok": audio_pb2.MIX_QUALITY_OK,
            "noisy": audio_pb2.MIX_QUALITY_NOISY,
            "clipping": audio_pb2.MIX_QUALITY_CLIPPING,
            "unbalanced": audio_pb2.MIX_QUALITY_UNBALANCED
        }
        return mapping.get(band, audio_pb2.MIX_QUALITY_UNSPECIFIED)
    
    async def stop(self):
        """Stop the metrics service."""
        logger.info("Stopping Audio Metrics Service")
        
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Audio Metrics Service stopped")


async def main():
    """Main entry point."""
    # Initialize components
    postgres_pool = await get_postgres_pool()
    nats_client = await get_nats_client()
    
    # Media storage path from environment or default
    import os
    media_path = os.environ.get('MEDIA_STORAGE_PATH', '/media/audio')
    media_storage = MediaStorageHandler(base_path=media_path)
    
    # Create service
    service = AudioMetricsService(
        postgres_pool,
        nats_client,
        media_storage
    )
    
    # Start service
    await service.start(num_workers=4)
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await service.stop()
        await nats_client.close()
        await postgres_pool.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
