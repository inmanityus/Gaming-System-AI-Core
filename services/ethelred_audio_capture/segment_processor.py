"""
Audio segment processor - handles segmentation and metadata enrichment
"""
import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
import numpy as np
import json


logger = logging.getLogger(__name__)


@dataclass
class AudioMetadata:
    """Metadata for an audio segment."""
    speaker_id: Optional[str] = None
    speaker_role: Optional[str] = None  # 'npc', 'narrator', 'player'
    archetype_id: Optional[str] = None
    language_code: str = 'en-US'
    scene_id: Optional[str] = None
    experience_id: Optional[str] = None
    line_id: Optional[str] = None
    emotional_tag: Optional[str] = None
    environment_type: Optional[str] = None
    bus_name: str = 'main_mix'
    simulator_applied: bool = False
    additional: Dict[str, str] = field(default_factory=dict)


@dataclass
class AudioSegment:
    """Represents a processed audio segment."""
    segment_id: str
    segment_type: str  # 'dialogue', 'monster_vocalization', 'ambient', 'mixed_bus'
    audio_data: np.ndarray
    sample_rate: int
    timestamp_start: datetime
    timestamp_end: datetime
    metadata: AudioMetadata
    
    @property
    def duration_seconds(self) -> float:
        return len(self.audio_data) / self.sample_rate
    
    @property
    def channels(self) -> int:
        return 1 if len(self.audio_data.shape) == 1 else self.audio_data.shape[1]
    
    @property
    def bit_depth(self) -> int:
        # Assume 16-bit for int16, 32-bit for float32
        if self.audio_data.dtype == np.int16:
            return 16
        elif self.audio_data.dtype == np.float32:
            return 32
        return 24  # Default


class SegmentProcessor:
    """Processes continuous audio streams into segments."""
    
    def __init__(self, 
                 min_silence_duration: float = 0.3,
                 silence_threshold_db: float = -40.0,
                 max_segment_duration: float = 10.0,
                 fixed_window_duration: float = 5.0):
        self.min_silence_duration = min_silence_duration
        self.silence_threshold_db = silence_threshold_db
        self.max_segment_duration = max_segment_duration
        self.fixed_window_duration = fixed_window_duration
        
        # Buffers for different buses
        self.bus_buffers: Dict[str, List[np.ndarray]] = {}
        self.bus_metadata: Dict[str, AudioMetadata] = {}
        self.bus_timestamps: Dict[str, datetime] = {}
    
    def detect_silence(self, audio_data: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
        """Detect silence regions in audio data."""
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            mono_data = np.mean(audio_data, axis=1)
        else:
            mono_data = audio_data
        
        # Calculate RMS in windows
        window_size = int(0.01 * sample_rate)  # 10ms windows
        rms_values = []
        
        for i in range(0, len(mono_data) - window_size, window_size):
            window = mono_data[i:i + window_size]
            rms = np.sqrt(np.mean(window ** 2))
            rms_values.append(rms)
        
        # Convert RMS to dB
        rms_values = np.array(rms_values)
        rms_values[rms_values == 0] = 1e-10  # Avoid log(0)
        db_values = 20 * np.log10(rms_values)
        
        # Find silence regions
        silence_mask = db_values < self.silence_threshold_db
        silence_regions = []
        
        start_idx = None
        for i, is_silent in enumerate(silence_mask):
            if is_silent and start_idx is None:
                start_idx = i
            elif not is_silent and start_idx is not None:
                # Convert window indices to sample indices
                start_sample = start_idx * window_size
                end_sample = i * window_size
                duration = (end_sample - start_sample) / sample_rate
                
                if duration >= self.min_silence_duration:
                    silence_regions.append((start_sample, end_sample))
                start_idx = None
        
        # Handle trailing silence
        if start_idx is not None:
            start_sample = start_idx * window_size
            end_sample = len(mono_data)
            duration = (end_sample - start_sample) / sample_rate
            if duration >= self.min_silence_duration:
                silence_regions.append((start_sample, end_sample))
        
        return silence_regions
    
    async def process_dialogue_stream(self,
                                    audio_data: np.ndarray,
                                    sample_rate: int,
                                    metadata: AudioMetadata,
                                    bus_name: str = 'dialogue_bus') -> List[AudioSegment]:
        """Process dialogue audio using silence detection."""
        segments = []
        
        # Detect silence regions
        silence_regions = self.detect_silence(audio_data, sample_rate)
        
        # Use silence to segment dialogue
        current_pos = 0
        base_timestamp = datetime.utcnow()
        
        for silence_start, silence_end in silence_regions:
            # Extract segment before silence
            if silence_start > current_pos:
                segment_data = audio_data[current_pos:silence_start]
                duration = len(segment_data) / sample_rate
                
                # Skip very short segments
                if duration > 0.1:
                    segment = AudioSegment(
                        segment_id=f"seg-aud-{uuid.uuid4()}",
                        segment_type='dialogue',
                        audio_data=segment_data,
                        sample_rate=sample_rate,
                        timestamp_start=base_timestamp + timedelta(seconds=current_pos/sample_rate),
                        timestamp_end=base_timestamp + timedelta(seconds=silence_start/sample_rate),
                        metadata=metadata
                    )
                    segments.append(segment)
                    logger.debug(f"Created dialogue segment {segment.segment_id} with duration {duration:.2f}s")
            
            current_pos = silence_end
        
        # Handle remaining audio
        if current_pos < len(audio_data):
            remaining_data = audio_data[current_pos:]
            duration = len(remaining_data) / sample_rate
            
            if duration > 0.1:
                segment = AudioSegment(
                    segment_id=f"seg-aud-{uuid.uuid4()}",
                    segment_type='dialogue',
                    audio_data=remaining_data,
                    sample_rate=sample_rate,
                    timestamp_start=base_timestamp + timedelta(seconds=current_pos/sample_rate),
                    timestamp_end=base_timestamp + timedelta(seconds=len(audio_data)/sample_rate),
                    metadata=metadata
                )
                segments.append(segment)
        
        return segments
    
    async def process_ambient_stream(self,
                                   audio_data: np.ndarray,
                                   sample_rate: int,
                                   metadata: AudioMetadata,
                                   bus_name: str = 'ambient_bus') -> List[AudioSegment]:
        """Process ambient audio using fixed windows."""
        segments = []
        window_samples = int(self.fixed_window_duration * sample_rate)
        base_timestamp = datetime.utcnow()
        
        for i in range(0, len(audio_data), window_samples):
            window_data = audio_data[i:i + window_samples]
            
            # Skip incomplete windows
            if len(window_data) < window_samples * 0.9:
                continue
            
            segment = AudioSegment(
                segment_id=f"seg-aud-{uuid.uuid4()}",
                segment_type='ambient',
                audio_data=window_data,
                sample_rate=sample_rate,
                timestamp_start=base_timestamp + timedelta(seconds=i/sample_rate),
                timestamp_end=base_timestamp + timedelta(seconds=(i + len(window_data))/sample_rate),
                metadata=metadata
            )
            segments.append(segment)
            logger.debug(f"Created ambient segment {segment.segment_id}")
        
        return segments
    
    async def process_vocalization_stream(self,
                                        audio_data: np.ndarray,
                                        sample_rate: int,
                                        metadata: AudioMetadata,
                                        bus_name: str = 'vocals_bus') -> List[AudioSegment]:
        """Process monster vocalizations - similar to dialogue but different thresholds."""
        # For vocalizations, we might want different silence thresholds
        segments = []
        
        # Simple energy-based segmentation for now
        silence_regions = self.detect_silence(audio_data, sample_rate)
        current_pos = 0
        base_timestamp = datetime.utcnow()
        
        for silence_start, silence_end in silence_regions:
            if silence_start > current_pos:
                segment_data = audio_data[current_pos:silence_start]
                duration = len(segment_data) / sample_rate
                
                # Monster vocalizations can be shorter
                if duration > 0.05:
                    segment = AudioSegment(
                        segment_id=f"seg-aud-{uuid.uuid4()}",
                        segment_type='monster_vocalization',
                        audio_data=segment_data,
                        sample_rate=sample_rate,
                        timestamp_start=base_timestamp + timedelta(seconds=current_pos/sample_rate),
                        timestamp_end=base_timestamp + timedelta(seconds=silence_start/sample_rate),
                        metadata=metadata
                    )
                    segments.append(segment)
            
            current_pos = silence_end
        
        return segments
    
    async def process_mixed_bus(self,
                              audio_data: np.ndarray,
                              sample_rate: int,
                              metadata: AudioMetadata) -> List[AudioSegment]:
        """Process full mix for overall quality assessment."""
        # Use fixed windows for mixed bus analysis
        segments = []
        window_samples = int(2.0 * sample_rate)  # 2-second windows
        base_timestamp = datetime.utcnow()
        
        for i in range(0, len(audio_data), window_samples):
            window_data = audio_data[i:i + window_samples]
            
            if len(window_data) < window_samples * 0.9:
                continue
            
            segment = AudioSegment(
                segment_id=f"seg-aud-{uuid.uuid4()}",
                segment_type='mixed_bus',
                audio_data=window_data,
                sample_rate=sample_rate,
                timestamp_start=base_timestamp + timedelta(seconds=i/sample_rate),
                timestamp_end=base_timestamp + timedelta(seconds=(i + len(window_data))/sample_rate),
                metadata=metadata
            )
            segments.append(segment)
        
        return segments
    
    async def enrich_metadata(self, 
                            segment: AudioSegment,
                            game_context: Optional[Dict] = None) -> AudioSegment:
        """Enrich segment metadata with game context."""
        if game_context:
            # Update metadata based on game context
            if 'scene_id' in game_context:
                segment.metadata.scene_id = game_context['scene_id']
            if 'line_id' in game_context:
                segment.metadata.line_id = game_context['line_id']
            if 'speaker_info' in game_context:
                speaker = game_context['speaker_info']
                segment.metadata.speaker_id = speaker.get('id')
                segment.metadata.speaker_role = speaker.get('role')
                segment.metadata.archetype_id = speaker.get('archetype_id')
            if 'emotional_context' in game_context:
                segment.metadata.emotional_tag = game_context['emotional_context']
            
            # Store any additional context
            for key, value in game_context.items():
                if key not in ['scene_id', 'line_id', 'speaker_info', 'emotional_context']:
                    segment.metadata.additional[key] = str(value)
        
        return segment


class AudioBuffer:
    """Manages audio buffering for continuous streams."""
    
    def __init__(self, sample_rate: int, max_buffer_duration: float = 30.0):
        self.sample_rate = sample_rate
        self.max_buffer_samples = int(max_buffer_duration * sample_rate)
        self.buffer: List[np.ndarray] = []
        self.total_samples = 0
    
    def add(self, audio_data: np.ndarray):
        """Add audio data to buffer."""
        self.buffer.append(audio_data)
        self.total_samples += len(audio_data)
        
        # Trim buffer if too large
        while self.total_samples > self.max_buffer_samples and len(self.buffer) > 1:
            removed = self.buffer.pop(0)
            self.total_samples -= len(removed)
    
    def get_all(self) -> Optional[np.ndarray]:
        """Get all buffered audio."""
        if not self.buffer:
            return None
        
        return np.concatenate(self.buffer, axis=0)
    
    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
        self.total_samples = 0
    
    def get_duration(self) -> float:
        """Get current buffer duration in seconds."""
        return self.total_samples / self.sample_rate

