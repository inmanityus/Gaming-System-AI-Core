"""
Timing and lip-sync management for localized audio.
Implements TML-05 (R-ML-SYNC-001, R-ML-SYNC-002).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import json
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class TimingType(str, Enum):
    """Types of timing information."""
    PHONEME = "phoneme"      # Individual phoneme timings
    VISEME = "viseme"        # Visual phoneme for lip-sync
    WORD = "word"            # Word-level timings
    SUBTITLE = "subtitle"    # Subtitle display timings
    EMOTION = "emotion"      # Emotion change markers


@dataclass
class TimingMarker:
    """Individual timing marker."""
    type: TimingType
    value: str               # Phoneme/viseme/word/text
    start_time: float       # Start time in seconds
    end_time: float         # End time in seconds
    confidence: float = 1.0  # Confidence score
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def duration(self) -> float:
        """Duration of this marker in seconds."""
        return self.end_time - self.start_time


@dataclass
class TimingData:
    """Complete timing data for an audio segment."""
    audio_duration: float
    sample_rate: int
    language_code: str
    
    # Different timing tracks
    phoneme_markers: List[TimingMarker] = None
    viseme_markers: List[TimingMarker] = None
    word_markers: List[TimingMarker] = None
    subtitle_markers: List[TimingMarker] = None
    emotion_markers: List[TimingMarker] = None
    
    # Original text
    text: str = ""
    
    # Metadata
    generated_by: str = ""
    generation_timestamp: datetime = None
    
    def __post_init__(self):
        # Initialize empty lists if None
        if self.phoneme_markers is None:
            self.phoneme_markers = []
        if self.viseme_markers is None:
            self.viseme_markers = []
        if self.word_markers is None:
            self.word_markers = []
        if self.subtitle_markers is None:
            self.subtitle_markers = []
        if self.emotion_markers is None:
            self.emotion_markers = []
        
        if self.generation_timestamp is None:
            self.generation_timestamp = datetime.utcnow()


class TimingManager:
    """
    Manages timing metadata generation, validation, and synchronization
    for multi-language audio and subtitles.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.phoneme_mappers = self._initialize_phoneme_mappers()
        self.viseme_mappings = self._load_viseme_mappings()
        
    def _initialize_phoneme_mappers(self) -> Dict[str, Any]:
        """Initialize language-specific phoneme mappers."""
        mappers = {}
        
        # English phoneme mapper
        if self.config.get('english_phoneme_enabled', True):
            from .phoneme_mappers.english_mapper import EnglishPhonemeMapper
            mappers['en'] = EnglishPhonemeMapper()
        
        # Japanese phoneme mapper
        if self.config.get('japanese_phoneme_enabled', True):
            from .phoneme_mappers.japanese_mapper import JapanesePhonemeMapper
            mappers['ja'] = JapanesePhonemeMapper()
        
        # Add more language mappers...
        
        return mappers
    
    def _load_viseme_mappings(self) -> Dict[str, str]:
        """Load phoneme to viseme mappings for lip-sync."""
        # Standard viseme set for lip-sync animation
        # Based on common viseme standards (e.g., Microsoft Speech API)
        return {
            # Silence
            'sil': 'sil',
            'sp': 'sil',
            
            # Bilabial
            'p': 'PP',
            'b': 'PP',
            'm': 'PP',
            
            # Labiodental
            'f': 'FF',
            'v': 'FF',
            
            # Interdental
            'th': 'TH',
            'dh': 'TH',
            
            # Alveolar
            't': 'DD',
            'd': 'DD',
            's': 'SS',
            'z': 'SS',
            'n': 'NN',
            'l': 'NN',
            
            # Postalveolar
            'sh': 'CH',
            'zh': 'CH',
            'ch': 'CH',
            'jh': 'CH',
            
            # Velar
            'k': 'KK',
            'g': 'KK',
            'ng': 'KK',
            
            # Glottal
            'h': 'HH',
            
            # Vowels
            'aa': 'AA',
            'ae': 'AA',
            'ah': 'AA',
            'ao': 'AO',
            'aw': 'AO',
            'ay': 'AY',
            'eh': 'EH',
            'er': 'ER',
            'ey': 'EY',
            'ih': 'IH',
            'iy': 'IY',
            'ow': 'OW',
            'oy': 'OW',
            'uh': 'UH',
            'uw': 'UW',
            
            # Default
            '_default': 'NN'
        }
    
    async def generate_timing_data(
        self,
        audio_data: bytes,
        sample_rate: int,
        text: str,
        language_code: str,
        tts_timings: Optional[Dict[str, Any]] = None
    ) -> TimingData:
        """
        Generate comprehensive timing data for audio segment.
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate
            text: Original text
            language_code: Language of the text
            tts_timings: Optional timing data from TTS provider
            
        Returns:
            Complete timing data with all marker types
        """
        # Calculate audio duration
        audio_duration = len(audio_data) / (sample_rate * 2)  # Assuming 16-bit audio
        
        timing_data = TimingData(
            audio_duration=audio_duration,
            sample_rate=sample_rate,
            language_code=language_code,
            text=text,
            generated_by='timing_manager'
        )
        
        # Generate different timing tracks
        if tts_timings:
            # Use TTS provider timings if available
            timing_data = self._parse_tts_timings(timing_data, tts_timings)
        else:
            # Estimate timings if not provided
            timing_data = await self._estimate_timings(timing_data)
        
        # Generate viseme markers from phonemes
        if timing_data.phoneme_markers:
            timing_data.viseme_markers = self._phonemes_to_visemes(
                timing_data.phoneme_markers
            )
        
        # Generate subtitle markers
        timing_data.subtitle_markers = self._generate_subtitle_markers(
            timing_data.word_markers or timing_data.phoneme_markers,
            text,
            language_code
        )
        
        # Validate timing data
        self._validate_timing_data(timing_data)
        
        return timing_data
    
    def _parse_tts_timings(
        self,
        timing_data: TimingData,
        tts_timings: Dict[str, Any]
    ) -> TimingData:
        """Parse timing information from TTS provider."""
        # Azure Cognitive Services format
        if 'phonemes' in tts_timings:
            for phoneme in tts_timings['phonemes']:
                marker = TimingMarker(
                    type=TimingType.PHONEME,
                    value=phoneme['phoneme'],
                    start_time=phoneme['start_ms'] / 1000.0,
                    end_time=phoneme['end_ms'] / 1000.0,
                    confidence=phoneme.get('confidence', 1.0)
                )
                timing_data.phoneme_markers.append(marker)
        
        # Word timings
        if 'words' in tts_timings:
            for word in tts_timings['words']:
                marker = TimingMarker(
                    type=TimingType.WORD,
                    value=word['word'],
                    start_time=word['start_ms'] / 1000.0,
                    end_time=word['end_ms'] / 1000.0,
                    confidence=word.get('confidence', 1.0)
                )
                timing_data.word_markers.append(marker)
        
        # Emotion markers (if supported)
        if 'emotions' in tts_timings:
            for emotion in tts_timings['emotions']:
                marker = TimingMarker(
                    type=TimingType.EMOTION,
                    value=emotion['emotion'],
                    start_time=emotion['start_ms'] / 1000.0,
                    end_time=emotion['end_ms'] / 1000.0,
                    metadata={'intensity': emotion.get('intensity', 1.0)}
                )
                timing_data.emotion_markers.append(marker)
        
        return timing_data
    
    async def _estimate_timings(self, timing_data: TimingData) -> TimingData:
        """Estimate timings when not provided by TTS."""
        # Get language-specific phoneme mapper
        lang_prefix = timing_data.language_code.split('-')[0]
        mapper = self.phoneme_mappers.get(lang_prefix)
        
        if not mapper:
            logger.warning(f"No phoneme mapper for language {lang_prefix}, using basic estimation")
            return self._basic_timing_estimation(timing_data)
        
        # Generate phoneme sequence
        phoneme_sequence = await mapper.text_to_phonemes(timing_data.text)
        
        # Estimate timing for each phoneme
        total_phonemes = len(phoneme_sequence)
        if total_phonemes == 0:
            return timing_data
        
        # Simple linear distribution (more sophisticated would use phoneme duration models)
        time_per_phoneme = timing_data.audio_duration / total_phonemes
        current_time = 0.0
        
        for phoneme in phoneme_sequence:
            duration = self._estimate_phoneme_duration(phoneme, time_per_phoneme)
            
            marker = TimingMarker(
                type=TimingType.PHONEME,
                value=phoneme,
                start_time=current_time,
                end_time=current_time + duration,
                confidence=0.7  # Lower confidence for estimated timings
            )
            timing_data.phoneme_markers.append(marker)
            
            current_time += duration
        
        # Generate word markers from phoneme markers
        timing_data.word_markers = await self._estimate_word_markers(
            timing_data.text,
            timing_data.phoneme_markers,
            mapper
        )
        
        return timing_data
    
    def _basic_timing_estimation(self, timing_data: TimingData) -> TimingData:
        """Basic timing estimation without phoneme analysis."""
        words = timing_data.text.split()
        if not words:
            return timing_data
        
        # Distribute time evenly across words
        time_per_word = timing_data.audio_duration / len(words)
        current_time = 0.0
        
        for word in words:
            marker = TimingMarker(
                type=TimingType.WORD,
                value=word,
                start_time=current_time,
                end_time=current_time + time_per_word,
                confidence=0.5
            )
            timing_data.word_markers.append(marker)
            current_time += time_per_word
        
        return timing_data
    
    def _estimate_phoneme_duration(self, phoneme: str, base_duration: float) -> float:
        """Estimate duration for a specific phoneme."""
        # Phoneme duration factors (relative to average)
        duration_factors = {
            # Short phonemes
            'p': 0.7, 'b': 0.7, 't': 0.7, 'd': 0.7, 'k': 0.7, 'g': 0.7,
            
            # Average phonemes
            'm': 1.0, 'n': 1.0, 'l': 1.0, 'r': 1.0,
            
            # Long phonemes
            's': 1.2, 'sh': 1.2, 'f': 1.2, 'v': 1.2,
            
            # Vowels (generally longer)
            'aa': 1.3, 'iy': 1.3, 'uw': 1.3, 'ow': 1.3,
            
            # Diphthongs (longest)
            'ay': 1.5, 'ey': 1.5, 'oy': 1.5,
            
            # Silence
            'sil': 0.5, 'sp': 0.3
        }
        
        factor = duration_factors.get(phoneme, 1.0)
        return base_duration * factor
    
    async def _estimate_word_markers(
        self,
        text: str,
        phoneme_markers: List[TimingMarker],
        phoneme_mapper: Any
    ) -> List[TimingMarker]:
        """Estimate word boundaries from phoneme markers."""
        words = text.split()
        word_markers = []
        
        phoneme_index = 0
        
        for word in words:
            # Get phonemes for this word
            word_phonemes = await phoneme_mapper.text_to_phonemes(word)
            
            if not word_phonemes or phoneme_index >= len(phoneme_markers):
                continue
            
            # Find start and end times
            start_time = phoneme_markers[phoneme_index].start_time
            end_index = min(phoneme_index + len(word_phonemes), len(phoneme_markers) - 1)
            end_time = phoneme_markers[end_index].end_time
            
            marker = TimingMarker(
                type=TimingType.WORD,
                value=word,
                start_time=start_time,
                end_time=end_time,
                confidence=0.7
            )
            word_markers.append(marker)
            
            phoneme_index = end_index + 1
        
        return word_markers
    
    def _phonemes_to_visemes(self, phoneme_markers: List[TimingMarker]) -> List[TimingMarker]:
        """Convert phoneme markers to viseme markers for lip-sync."""
        viseme_markers = []
        
        for phoneme_marker in phoneme_markers:
            # Map phoneme to viseme
            viseme = self.viseme_mappings.get(
                phoneme_marker.value,
                self.viseme_mappings['_default']
            )
            
            # Create viseme marker
            viseme_marker = TimingMarker(
                type=TimingType.VISEME,
                value=viseme,
                start_time=phoneme_marker.start_time,
                end_time=phoneme_marker.end_time,
                confidence=phoneme_marker.confidence,
                metadata={'source_phoneme': phoneme_marker.value}
            )
            
            # Merge consecutive identical visemes
            if viseme_markers and viseme_markers[-1].value == viseme:
                # Extend previous viseme
                viseme_markers[-1].end_time = phoneme_marker.end_time
            else:
                viseme_markers.append(viseme_marker)
        
        return viseme_markers
    
    def _generate_subtitle_markers(
        self,
        base_markers: List[TimingMarker],
        text: str,
        language_code: str
    ) -> List[TimingMarker]:
        """Generate subtitle timing markers."""
        if not base_markers:
            # Single subtitle for entire duration
            return [TimingMarker(
                type=TimingType.SUBTITLE,
                value=text,
                start_time=0.0,
                end_time=self.config.get('default_subtitle_duration', 5.0),
                confidence=1.0
            )]
        
        # Subtitle configuration
        max_chars_per_line = self.config.get('subtitle_max_chars', 40)
        max_duration = self.config.get('subtitle_max_duration', 7.0)
        min_duration = self.config.get('subtitle_min_duration', 1.0)
        
        subtitle_markers = []
        current_text = ""
        current_start = 0.0
        
        # Use word markers if available, otherwise use phoneme markers
        markers_to_use = [m for m in base_markers if m.type == TimingType.WORD] or base_markers
        
        for i, marker in enumerate(markers_to_use):
            # Add word/phoneme to current subtitle
            if marker.type == TimingType.WORD:
                test_text = (current_text + " " + marker.value).strip()
            else:
                test_text = current_text + marker.value
            
            # Check if we should create a new subtitle
            should_split = (
                len(test_text) > max_chars_per_line or
                marker.end_time - current_start > max_duration or
                (marker.value in '.!?;' and marker.end_time - current_start > min_duration)
            )
            
            if should_split and current_text:
                # Create subtitle marker
                subtitle_marker = TimingMarker(
                    type=TimingType.SUBTITLE,
                    value=current_text.strip(),
                    start_time=current_start,
                    end_time=markers_to_use[i-1].end_time if i > 0 else marker.end_time,
                    confidence=1.0
                )
                subtitle_markers.append(subtitle_marker)
                
                # Start new subtitle
                current_text = marker.value if marker.type == TimingType.WORD else ""
                current_start = marker.start_time
            else:
                current_text = test_text
        
        # Add final subtitle
        if current_text:
            subtitle_marker = TimingMarker(
                type=TimingType.SUBTITLE,
                value=current_text.strip(),
                start_time=current_start,
                end_time=markers_to_use[-1].end_time,
                confidence=1.0
            )
            subtitle_markers.append(subtitle_marker)
        
        return subtitle_markers
    
    def _validate_timing_data(self, timing_data: TimingData):
        """Validate timing data for consistency."""
        # Check that all markers are within audio duration
        all_markers = (
            timing_data.phoneme_markers +
            timing_data.viseme_markers +
            timing_data.word_markers +
            timing_data.subtitle_markers +
            timing_data.emotion_markers
        )
        
        for marker in all_markers:
            if marker.start_time < 0:
                logger.warning(f"Marker has negative start time: {marker}")
                marker.start_time = 0.0
            
            if marker.end_time > timing_data.audio_duration:
                logger.warning(f"Marker extends beyond audio duration: {marker}")
                marker.end_time = timing_data.audio_duration
            
            if marker.start_time >= marker.end_time:
                logger.warning(f"Marker has invalid duration: {marker}")
                marker.end_time = marker.start_time + 0.001
    
    async def align_subtitle_to_audio(
        self,
        subtitle_text: str,
        timing_data: TimingData,
        max_offset: float = 2.0
    ) -> Tuple[List[TimingMarker], float]:
        """
        Align subtitle text to audio timing data.
        
        Args:
            subtitle_text: Subtitle text to align
            timing_data: Reference timing data
            max_offset: Maximum allowed offset in seconds
            
        Returns:
            Aligned subtitle markers and confidence score
        """
        # Use word markers for alignment if available
        if not timing_data.word_markers:
            logger.warning("No word markers available for alignment")
            return timing_data.subtitle_markers, 0.5
        
        # Simple alignment based on word matching
        # More sophisticated alignment would use:
        # - Edit distance algorithms
        # - Phonetic similarity
        # - Machine learning models
        
        subtitle_words = subtitle_text.lower().split()
        audio_words = [m.value.lower() for m in timing_data.word_markers]
        
        # Find best alignment using dynamic programming
        alignment_score, aligned_indices = self._compute_alignment(
            subtitle_words, audio_words
        )
        
        # Generate aligned subtitle markers
        aligned_markers = []
        confidence = alignment_score / len(subtitle_words) if subtitle_words else 0.0
        
        # Group aligned words into subtitle segments
        current_segment = []
        current_indices = []
        
        for i, word in enumerate(subtitle_words):
            if aligned_indices[i] >= 0:
                current_segment.append(word)
                current_indices.append(aligned_indices[i])
                
                # Check if we should create a subtitle
                if (i == len(subtitle_words) - 1 or  # Last word
                    aligned_indices[i+1] - aligned_indices[i] > 3 or  # Gap in alignment
                    len(' '.join(current_segment)) > 40):  # Length limit
                    
                    if current_indices:
                        # Create subtitle marker
                        start_idx = current_indices[0]
                        end_idx = current_indices[-1]
                        
                        marker = TimingMarker(
                            type=TimingType.SUBTITLE,
                            value=' '.join(current_segment),
                            start_time=timing_data.word_markers[start_idx].start_time,
                            end_time=timing_data.word_markers[end_idx].end_time,
                            confidence=confidence
                        )
                        aligned_markers.append(marker)
                    
                    current_segment = []
                    current_indices = []
        
        return aligned_markers, confidence
    
    def _compute_alignment(
        self,
        subtitle_words: List[str],
        audio_words: List[str]
    ) -> Tuple[float, List[int]]:
        """Compute optimal alignment between subtitle and audio words."""
        # Simple alignment using longest common subsequence
        # Returns alignment score and indices
        
        n, m = len(subtitle_words), len(audio_words)
        
        # Dynamic programming table
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        
        # Fill table
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if subtitle_words[i-1] == audio_words[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        # Backtrack to find alignment
        aligned_indices = [-1] * n
        i, j = n, m
        
        while i > 0 and j > 0:
            if subtitle_words[i-1] == audio_words[j-1]:
                aligned_indices[i-1] = j-1
                i -= 1
                j -= 1
            elif dp[i-1][j] > dp[i][j-1]:
                i -= 1
            else:
                j -= 1
        
        alignment_score = dp[n][m]
        
        return alignment_score, aligned_indices
    
    def export_for_ue5(self, timing_data: TimingData) -> Dict[str, Any]:
        """Export timing data in format suitable for Unreal Engine 5."""
        return {
            'audio_duration': timing_data.audio_duration,
            'sample_rate': timing_data.sample_rate,
            'language': timing_data.language_code,
            'visemes': [
                {
                    'type': marker.value,
                    'start': marker.start_time,
                    'end': marker.end_time,
                    'weight': marker.confidence
                }
                for marker in timing_data.viseme_markers
            ],
            'subtitles': [
                {
                    'text': marker.value,
                    'start': marker.start_time,
                    'end': marker.end_time
                }
                for marker in timing_data.subtitle_markers
            ],
            'emotions': [
                {
                    'type': marker.value,
                    'start': marker.start_time,
                    'end': marker.end_time,
                    'intensity': marker.metadata.get('intensity', 1.0)
                }
                for marker in timing_data.emotion_markers
            ]
        }
    
    def calculate_sync_quality(
        self,
        timing_data: TimingData,
        reference_duration: float
    ) -> Dict[str, float]:
        """Calculate synchronization quality metrics."""
        metrics = {}
        
        # Duration accuracy
        duration_diff = abs(timing_data.audio_duration - reference_duration)
        metrics['duration_accuracy'] = 1.0 - min(duration_diff / reference_duration, 1.0)
        
        # Subtitle coverage
        if timing_data.subtitle_markers:
            subtitle_coverage = sum(
                m.duration for m in timing_data.subtitle_markers
            ) / timing_data.audio_duration
            metrics['subtitle_coverage'] = subtitle_coverage
        else:
            metrics['subtitle_coverage'] = 0.0
        
        # Lip-sync density
        if timing_data.viseme_markers:
            viseme_changes = len(timing_data.viseme_markers)
            expected_changes = timing_data.audio_duration * 10  # ~10 viseme changes per second
            metrics['lipsync_density'] = min(viseme_changes / expected_changes, 1.0)
        else:
            metrics['lipsync_density'] = 0.0
        
        # Overall sync quality
        metrics['overall_quality'] = (
            metrics['duration_accuracy'] * 0.3 +
            metrics['subtitle_coverage'] * 0.3 +
            metrics['lipsync_density'] * 0.4
        )
        
        return metrics
