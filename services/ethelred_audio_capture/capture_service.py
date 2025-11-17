"""
Audio Capture Service - Main service implementation
"""
import asyncio
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import asyncpg
import nats
from nats.js import JetStreamContext
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Add parent for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.nats_client import get_nats_client
from shared.database import get_postgres_pool

# Import our modules
from .segment_processor import SegmentProcessor, AudioSegment, AudioMetadata, AudioBuffer
from .media_storage import MediaStorageHandler, MediaCache

# Compile protobuf
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2

# Metrics
segments_created = Counter('audio_segments_created_total', 'Total segments created', ['segment_type', 'bus_name'])
segment_duration = Histogram('audio_segment_duration_seconds', 'Segment duration distribution', ['segment_type'])
capture_errors = Counter('audio_capture_errors_total', 'Total capture errors', ['error_type'])
active_streams = Gauge('audio_active_streams', 'Number of active audio streams')
storage_latency = Histogram('audio_storage_latency_seconds', 'Time to store audio segments')

logger = logging.getLogger(__name__)


class AudioCaptureService:
    """Main audio capture service."""
    
    def __init__(self, 
                 postgres_pool: asyncpg.Pool,
                 nats_client: nats.NATS,
                 media_storage: MediaStorageHandler,
                 build_id: str):
        self.postgres = postgres_pool
        self.nc = nats_client
        self.media_storage = media_storage
        self.build_id = build_id
        
        # Components
        self.processor = SegmentProcessor()
        self.media_cache = MediaCache(max_size_mb=200)
        
        # Active streams
        self.active_streams: Dict[str, AudioBuffer] = {}
        self.stream_metadata: Dict[str, AudioMetadata] = {}
        
        # NATS subjects
        self.SEGMENT_CREATED_SUBJECT = 'svc.ethelred.audio.v1.segment_created'
    
    async def start(self):
        """Start the capture service."""
        logger.info(f"Starting Audio Capture Service for build {self.build_id}")
        
        # Start metrics server
        start_http_server(8090)
        
        # Subscribe to audio input channels (in production, this would be virtual audio routing)
        # For now, we'll expose APIs that can be called with audio data
        
        logger.info("Audio Capture Service started")
    
    async def create_audio_stream(self, 
                                bus_name: str,
                                sample_rate: int,
                                metadata: AudioMetadata) -> str:
        """Create a new audio stream. Returns stream ID."""
        stream_id = f"stream-{bus_name}-{datetime.utcnow().isoformat()}"
        
        self.active_streams[stream_id] = AudioBuffer(sample_rate)
        self.stream_metadata[stream_id] = metadata
        
        active_streams.inc()
        logger.info(f"Created audio stream {stream_id} for bus {bus_name}")
        
        return stream_id
    
    async def feed_audio_data(self,
                            stream_id: str,
                            audio_data: np.ndarray,
                            game_context: Optional[Dict] = None):
        """Feed audio data to an active stream."""
        if stream_id not in self.active_streams:
            logger.error(f"Unknown stream ID: {stream_id}")
            capture_errors.labels(error_type='unknown_stream').inc()
            return
        
        buffer = self.active_streams[stream_id]
        metadata = self.stream_metadata[stream_id]
        
        # Add to buffer
        buffer.add(audio_data)
        
        # Process if we have enough data
        if buffer.get_duration() >= 1.0:  # Process every second
            await self._process_buffered_audio(stream_id, game_context)
    
    async def _process_buffered_audio(self,
                                    stream_id: str,
                                    game_context: Optional[Dict] = None):
        """Process buffered audio data."""
        buffer = self.active_streams[stream_id]
        metadata = self.stream_metadata[stream_id]
        audio_data = buffer.get_all()
        
        if audio_data is None:
            return
        
        try:
            # Determine processing method based on bus type
            bus_name = metadata.bus_name
            segments = []
            
            if bus_name == 'dialogue_bus' or 'dialogue' in bus_name:
                segments = await self.processor.process_dialogue_stream(
                    audio_data, buffer.sample_rate, metadata, bus_name
                )
            elif bus_name == 'vocals_bus' or 'vocal' in bus_name:
                segments = await self.processor.process_vocalization_stream(
                    audio_data, buffer.sample_rate, metadata, bus_name
                )
            elif bus_name == 'ambient_bus' or 'ambient' in bus_name:
                segments = await self.processor.process_ambient_stream(
                    audio_data, buffer.sample_rate, metadata, bus_name
                )
            else:
                # Default to mixed bus processing
                segments = await self.processor.process_mixed_bus(
                    audio_data, buffer.sample_rate, metadata
                )
            
            # Process each segment
            for segment in segments:
                # Enrich with game context
                if game_context:
                    segment = await self.processor.enrich_metadata(segment, game_context)
                
                # Store and emit
                await self._store_and_emit_segment(segment)
            
            # Clear processed data
            buffer.clear()
            
        except Exception as e:
            logger.error(f"Error processing audio stream {stream_id}: {e}")
            capture_errors.labels(error_type='processing_error').inc()
    
    async def _store_and_emit_segment(self, segment: AudioSegment):
        """Store segment to media storage and emit NATS event."""
        try:
            # Store audio to media storage
            with storage_latency.time():
                media_uri = await self.media_storage.store_segment(
                    segment.audio_data,
                    segment.sample_rate,
                    segment.segment_id,
                    self.build_id
                )
            
            # Store metadata in database
            await self._store_segment_metadata(segment, media_uri)
            
            # Create and emit NATS event
            event = self._create_segment_event(segment, media_uri)
            await self.nc.publish(
                self.SEGMENT_CREATED_SUBJECT,
                event.SerializeToString()
            )
            
            # Update metrics
            segments_created.labels(
                segment_type=segment.segment_type,
                bus_name=segment.metadata.bus_name
            ).inc()
            segment_duration.labels(
                segment_type=segment.segment_type
            ).observe(segment.duration_seconds)
            
            logger.debug(f"Stored and emitted segment {segment.segment_id}")
            
        except Exception as e:
            logger.error(f"Error storing segment {segment.segment_id}: {e}")
            capture_errors.labels(error_type='storage_error').inc()
    
    async def _store_segment_metadata(self, segment: AudioSegment, media_uri: str):
        """Store segment metadata in database."""
        metadata = segment.metadata
        
        await self.postgres.execute("""
            INSERT INTO audio_segments (
                segment_id, build_id, segment_type,
                speaker_id, speaker_role, archetype_id,
                language_code, scene_id, experience_id,
                line_id, emotional_tag, environment_type,
                simulator_applied, media_uri,
                sample_rate, bit_depth, channels,
                duration_seconds, bus_name,
                timestamp_start, timestamp_end,
                capture_metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18,
                $19, $20, $21, $22
            )
        """,
            segment.segment_id, self.build_id, segment.segment_type,
            metadata.speaker_id, metadata.speaker_role, metadata.archetype_id,
            metadata.language_code, metadata.scene_id, metadata.experience_id,
            metadata.line_id, metadata.emotional_tag, metadata.environment_type,
            metadata.simulator_applied, media_uri,
            segment.sample_rate, segment.bit_depth, segment.channels,
            segment.duration_seconds, metadata.bus_name,
            segment.timestamp_start, segment.timestamp_end,
            json.dumps(metadata.additional)
        )
    
    def _create_segment_event(self, segment: AudioSegment, media_uri: str) -> audio_pb2.SegmentCreatedEvent:
        """Create protobuf event for segment."""
        event = audio_pb2.SegmentCreatedEvent()
        
        # Envelope
        event.envelope.trace_id = f"trace-{segment.segment_id}"
        event.envelope.session_id = f"session-{self.build_id}"
        event.envelope.build_id = self.build_id
        event.envelope.domain = "Audio"
        event.envelope.issue_type = "AUDIO.SEGMENT_CREATED"
        event.envelope.severity = audio_pb2.SEVERITY_INFO
        event.envelope.confidence = 1.0
        
        # Timestamp range
        event.envelope.timestamp_range.start.FromDatetime(segment.timestamp_start)
        event.envelope.timestamp_range.end.FromDatetime(segment.timestamp_end)
        
        # Evidence
        event.envelope.evidence_refs.append(media_uri)
        
        # Segment data
        event.segment_id = segment.segment_id
        event.segment_type = self._map_segment_type(segment.segment_type)
        
        # Speaker
        metadata = segment.metadata
        if metadata.speaker_id:
            event.speaker.speaker_id = metadata.speaker_id
        if metadata.speaker_role:
            event.speaker.role = self._map_speaker_role(metadata.speaker_role)
        if metadata.archetype_id:
            event.speaker.archetype_id = metadata.archetype_id
        
        event.language_code = metadata.language_code
        
        # Context
        if metadata.line_id:
            event.context.line_id = metadata.line_id
        if metadata.scene_id:
            event.context.scene_id = metadata.scene_id
        if metadata.experience_id:
            event.context.experience_id = metadata.experience_id
        if metadata.emotional_tag:
            event.context.emotional_tag = metadata.emotional_tag
        if metadata.environment_type:
            event.context.environment_type = metadata.environment_type
        
        event.simulator_applied = metadata.simulator_applied
        
        # Technical details
        event.media_uri = media_uri
        event.sample_rate = segment.sample_rate
        event.bit_depth = segment.bit_depth
        event.channels = segment.channels
        event.duration_seconds = segment.duration_seconds
        event.bus_name = metadata.bus_name
        
        # Additional metadata
        for key, value in metadata.additional.items():
            event.additional_metadata[key] = value
        
        return event
    
    def _map_segment_type(self, segment_type: str) -> int:
        """Map string segment type to protobuf enum."""
        mapping = {
            'dialogue': audio_pb2.SEGMENT_TYPE_DIALOGUE,
            'monster_vocalization': audio_pb2.SEGMENT_TYPE_MONSTER_VOCALIZATION,
            'ambient': audio_pb2.SEGMENT_TYPE_AMBIENT,
            'mixed_bus': audio_pb2.SEGMENT_TYPE_MIXED_BUS
        }
        return mapping.get(segment_type, audio_pb2.SEGMENT_TYPE_UNSPECIFIED)
    
    def _map_speaker_role(self, role: str) -> int:
        """Map string speaker role to protobuf enum."""
        mapping = {
            'npc': audio_pb2.SPEAKER_ROLE_NPC,
            'narrator': audio_pb2.SPEAKER_ROLE_NARRATOR,
            'player': audio_pb2.SPEAKER_ROLE_PLAYER
        }
        return mapping.get(role, audio_pb2.SPEAKER_ROLE_UNSPECIFIED)
    
    async def close_stream(self, stream_id: str, game_context: Optional[Dict] = None):
        """Close an audio stream and process any remaining data."""
        if stream_id not in self.active_streams:
            return
        
        # Process any remaining data
        await self._process_buffered_audio(stream_id, game_context)
        
        # Clean up
        del self.active_streams[stream_id]
        del self.stream_metadata[stream_id]
        active_streams.dec()
        
        logger.info(f"Closed audio stream {stream_id}")
    
    async def stop(self):
        """Stop the capture service."""
        logger.info("Stopping Audio Capture Service")
        
        # Close all active streams
        stream_ids = list(self.active_streams.keys())
        for stream_id in stream_ids:
            await self.close_stream(stream_id)
        
        logger.info("Audio Capture Service stopped")


# API endpoints for testing
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64

app = FastAPI()

# Global service instance
capture_service: Optional[AudioCaptureService] = None


class CreateStreamRequest(BaseModel):
    bus_name: str
    sample_rate: int = 48000
    speaker_id: Optional[str] = None
    language_code: str = 'en-US'
    scene_id: Optional[str] = None


class FeedAudioRequest(BaseModel):
    stream_id: str
    audio_data_base64: str  # Base64 encoded audio data
    game_context: Optional[Dict] = None


@app.post("/streams/create")
async def create_stream(request: CreateStreamRequest) -> Dict[str, str]:
    """Create a new audio stream."""
    if not capture_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    metadata = AudioMetadata(
        speaker_id=request.speaker_id,
        language_code=request.language_code,
        scene_id=request.scene_id,
        bus_name=request.bus_name
    )
    
    stream_id = await capture_service.create_audio_stream(
        request.bus_name,
        request.sample_rate,
        metadata
    )
    
    return {"stream_id": stream_id}


@app.post("/streams/feed")
async def feed_audio(request: FeedAudioRequest):
    """Feed audio data to a stream."""
    if not capture_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Decode audio data
    try:
        audio_bytes = base64.b64decode(request.audio_data_base64)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio data: {e}")
    
    await capture_service.feed_audio_data(
        request.stream_id,
        audio_data,
        request.game_context
    )
    
    return {"status": "ok"}


@app.post("/streams/{stream_id}/close")
async def close_stream(stream_id: str):
    """Close an audio stream."""
    if not capture_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    await capture_service.close_stream(stream_id)
    return {"status": "closed"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "audio-capture"}


async def main():
    """Main entry point."""
    global capture_service
    
    # Initialize components
    postgres_pool = await get_postgres_pool()
    nats_client = await get_nats_client()
    media_storage = MediaStorageHandler(base_path="/media/audio")
    
    # Get build ID from environment or use default
    import os
    build_id = os.environ.get('BUILD_ID', f'build-{datetime.utcnow().strftime("%Y-%m-%d")}')
    
    # Create service
    capture_service = AudioCaptureService(
        postgres_pool,
        nats_client,
        media_storage,
        build_id
    )
    
    await capture_service.start()
    
    # Run FastAPI
    import uvicorn
    await uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=8089)
    ).serve()


if __name__ == "__main__":
    asyncio.run(main())

