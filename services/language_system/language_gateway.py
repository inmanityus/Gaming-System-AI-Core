"""
Language system gateway - central interface for all localization operations.
Implements TML-03 (R-ML-GATE-001, R-ML-GATE-002).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
from datetime import datetime

from .tts_manager import TTSManager, TTSResult, VoiceProfile
from .timing_manager import TimingManager, TimingData
from services.localization.service import LocalizationService

logger = logging.getLogger(__name__)


class LocalizationMode(str, Enum):
    """Localization processing modes."""
    TEXT_ONLY = "text_only"            # Just text localization
    TEXT_WITH_AUDIO = "text_with_audio"  # Text + TTS generation
    FULL_SYNC = "full_sync"            # Text + Audio + Timing
    RECORDED = "recorded"              # Pre-recorded with timing


@dataclass
class LocalizationRequest:
    """Request for localization processing."""
    key: str                          # Localization key
    language_code: str                # Target language
    mode: LocalizationMode            # Processing mode
    
    # Optional context
    context: Optional[Dict[str, Any]] = None
    speaker_id: Optional[str] = None
    archetype_id: Optional[str] = None
    emotion: Optional[str] = None
    
    # Options
    generate_audio: bool = True
    generate_timing: bool = True
    use_cache: bool = True
    
    # Quality settings
    audio_quality: str = "high"  # low, medium, high
    timing_precision: str = "normal"  # fast, normal, precise


@dataclass
class LocalizationResult:
    """Result of localization processing."""
    key: str
    language_code: str
    text: str
    
    # Audio data (if generated)
    audio_data: Optional[bytes] = None
    audio_sample_rate: Optional[int] = None
    audio_duration: Optional[float] = None
    
    # Timing data (if generated)
    timing_data: Optional[TimingData] = None
    
    # Metadata
    mode: LocalizationMode = LocalizationMode.TEXT_ONLY
    cached: bool = False
    processing_time_ms: float = 0
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class LanguageSystemGateway:
    """
    Central gateway for all language system operations.
    Coordinates between localization, TTS, and timing systems.
    """
    
    def __init__(
        self,
        localization_service: LocalizationService,
        tts_manager: TTSManager,
        timing_manager: TimingManager,
        config: Dict[str, Any]
    ):
        self.localization = localization_service
        self.tts = tts_manager
        self.timing = timing_manager
        self.config = config
        
        # Performance settings
        self.max_parallel_requests = config.get('max_parallel_requests', 10)
        self.cache_enabled = config.get('cache_enabled', True)
        
        # Quality presets
        self.quality_presets = self._load_quality_presets()
    
    def _load_quality_presets(self) -> Dict[str, Dict[str, Any]]:
        """Load quality preset configurations."""
        return {
            'low': {
                'tts_quality': 'low',
                'sample_rate': 16000,
                'timing_estimation': True,
                'cache_priority': 'speed'
            },
            'medium': {
                'tts_quality': 'medium',
                'sample_rate': 24000,
                'timing_estimation': False,
                'cache_priority': 'balanced'
            },
            'high': {
                'tts_quality': 'high',
                'sample_rate': 48000,
                'timing_estimation': False,
                'cache_priority': 'quality'
            }
        }
    
    async def process_request(
        self,
        request: LocalizationRequest
    ) -> LocalizationResult:
        """
        Process a single localization request.
        
        Handles text retrieval, audio generation, and timing synchronization
        based on the requested mode.
        """
        start_time = asyncio.get_event_loop().time()
        
        # Initialize result
        result = LocalizationResult(
            key=request.key,
            language_code=request.language_code,
            text="",
            mode=request.mode
        )
        
        try:
            # Step 1: Get localized text
            text = await self.localization.get_string(
                request.key,
                request.language_code,
                request.context
            )
            
            if text.startswith('[') and text.endswith(']'):
                # Missing translation
                result.warnings.append(f"Missing translation for key: {request.key}")
                result.text = text
                return result
            
            result.text = text
            
            # Step 2: Generate audio if needed
            if request.mode in [LocalizationMode.TEXT_WITH_AUDIO, LocalizationMode.FULL_SYNC]:
                if request.generate_audio:
                    tts_result = await self._generate_audio(
                        text, request, result
                    )
                    
                    if tts_result:
                        result.audio_data = tts_result.audio_data
                        result.audio_sample_rate = tts_result.sample_rate
                        result.audio_duration = tts_result.duration_seconds
                        
                        # Step 3: Generate timing if needed
                        if request.mode == LocalizationMode.FULL_SYNC and request.generate_timing:
                            timing_data = await self._generate_timing(
                                tts_result, text, request, result
                            )
                            result.timing_data = timing_data
            
            elif request.mode == LocalizationMode.RECORDED:
                # Load pre-recorded audio and timing
                recorded_data = await self._load_recorded_data(
                    request.key, request.language_code
                )
                
                if recorded_data:
                    result.audio_data = recorded_data['audio_data']
                    result.audio_sample_rate = recorded_data['sample_rate']
                    result.audio_duration = recorded_data['duration']
                    result.timing_data = recorded_data.get('timing_data')
                else:
                    result.warnings.append("No recorded audio found")
            
        except Exception as e:
            logger.error(f"Error processing localization request: {e}")
            result.warnings.append(f"Processing error: {str(e)}")
        
        # Calculate processing time
        result.processing_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return result
    
    async def process_batch(
        self,
        requests: List[LocalizationRequest],
        parallel: bool = True
    ) -> List[LocalizationResult]:
        """
        Process multiple localization requests.
        
        Can process in parallel for better performance.
        """
        if parallel:
            # Process in parallel with concurrency limit
            semaphore = asyncio.Semaphore(self.max_parallel_requests)
            
            async def process_with_limit(request):
                async with semaphore:
                    return await self.process_request(request)
            
            tasks = [process_with_limit(req) for req in requests]
            return await asyncio.gather(*tasks)
        else:
            # Process sequentially
            results = []
            for request in requests:
                result = await self.process_request(request)
                results.append(result)
            return results
    
    async def process_dialogue(
        self,
        dialogue_entries: List[Dict[str, Any]],
        language_code: str,
        mode: LocalizationMode = LocalizationMode.FULL_SYNC
    ) -> List[LocalizationResult]:
        """
        Process a complete dialogue sequence.
        
        Optimized for dialogue with speaker changes and emotional variations.
        """
        # Convert to localization requests
        requests = []
        
        for entry in dialogue_entries:
            request = LocalizationRequest(
                key=entry['key'],
                language_code=language_code,
                mode=mode,
                context=entry.get('context'),
                speaker_id=entry.get('speaker_id'),
                archetype_id=entry.get('archetype_id'),
                emotion=entry.get('emotion'),
                generate_audio=True,
                generate_timing=True
            )
            requests.append(request)
        
        # Process batch with optimization for dialogue
        return await self._process_dialogue_optimized(requests)
    
    async def _process_dialogue_optimized(
        self,
        requests: List[LocalizationRequest]
    ) -> List[LocalizationResult]:
        """Process dialogue with optimizations."""
        # Group by speaker for voice consistency
        speaker_groups = {}
        for i, req in enumerate(requests):
            speaker = req.speaker_id or 'narrator'
            if speaker not in speaker_groups:
                speaker_groups[speaker] = []
            speaker_groups[speaker].append((i, req))
        
        # Process each speaker group
        all_results = [None] * len(requests)
        
        for speaker, group in speaker_groups.items():
            # Process speaker's lines in parallel
            indices, speaker_requests = zip(*group)
            results = await self.process_batch(list(speaker_requests), parallel=True)
            
            # Place results in correct positions
            for idx, result in zip(indices, results):
                all_results[idx] = result
        
        return all_results
    
    async def _generate_audio(
        self,
        text: str,
        request: LocalizationRequest,
        result: LocalizationResult
    ) -> Optional[TTSResult]:
        """Generate audio using TTS."""
        try:
            # Get quality preset
            preset = self.quality_presets.get(
                request.audio_quality, 
                self.quality_presets['medium']
            )
            
            # Generate TTS
            tts_result = await self.tts.generate_speech(
                text,
                request.language_code,
                speaker_id=request.speaker_id,
                archetype_id=request.archetype_id,
                emotion=request.emotion,
                sample_rate=preset['sample_rate']
            )
            
            return tts_result
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            result.warnings.append(f"Audio generation failed: {str(e)}")
            return None
    
    async def _generate_timing(
        self,
        tts_result: TTSResult,
        text: str,
        request: LocalizationRequest,
        result: LocalizationResult
    ) -> Optional[TimingData]:
        """Generate timing data."""
        try:
            # Convert TTS timings if available
            tts_timings = None
            if tts_result.word_timings or tts_result.phoneme_timings:
                tts_timings = {
                    'words': tts_result.word_timings or [],
                    'phonemes': tts_result.phoneme_timings or [],
                    'visemes': tts_result.viseme_timings or []
                }
            
            # Generate comprehensive timing
            timing_data = await self.timing.generate_timing_data(
                tts_result.audio_data,
                tts_result.sample_rate,
                text,
                request.language_code,
                tts_timings
            )
            
            return timing_data
            
        except Exception as e:
            logger.error(f"Timing generation failed: {e}")
            result.warnings.append(f"Timing generation failed: {str(e)}")
            return None
    
    async def _load_recorded_data(
        self,
        key: str,
        language_code: str
    ) -> Optional[Dict[str, Any]]:
        """Load pre-recorded audio and timing data."""
        # This would integrate with asset management system
        # For now, return None
        logger.info(f"Loading recorded data for {key} in {language_code}")
        return None
    
    async def validate_localization(
        self,
        language_code: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate localization completeness and quality.
        
        Checks:
        - Missing translations
        - Audio coverage
        - Timing data availability
        - Quality metrics
        """
        validation_result = {
            'language_code': language_code,
            'timestamp': datetime.utcnow().isoformat(),
            'text_validation': {},
            'audio_validation': {},
            'timing_validation': {},
            'overall_status': 'unknown'
        }
        
        # Text validation
        text_issues = await self.localization.repository.validate_translations(
            language_code
        )
        validation_result['text_validation'] = {
            'total_issues': sum(len(v) for v in text_issues.values()),
            'issues_by_type': text_issues
        }
        
        # Audio validation (check what's been generated)
        # This would query a database or cache
        audio_coverage = await self._calculate_audio_coverage(
            language_code, categories
        )
        validation_result['audio_validation'] = audio_coverage
        
        # Timing validation
        timing_coverage = await self._calculate_timing_coverage(
            language_code, categories
        )
        validation_result['timing_validation'] = timing_coverage
        
        # Overall status
        if (validation_result['text_validation']['total_issues'] == 0 and
            audio_coverage.get('coverage_percentage', 0) > 90 and
            timing_coverage.get('coverage_percentage', 0) > 90):
            validation_result['overall_status'] = 'ready'
        elif (validation_result['text_validation']['total_issues'] < 10 and
              audio_coverage.get('coverage_percentage', 0) > 70):
            validation_result['overall_status'] = 'nearly_ready'
        else:
            validation_result['overall_status'] = 'incomplete'
        
        return validation_result
    
    async def _calculate_audio_coverage(
        self,
        language_code: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate audio generation coverage."""
        # This would query actual audio generation records
        # For now, return mock data
        return {
            'total_strings': 1000,
            'audio_generated': 850,
            'coverage_percentage': 85.0,
            'by_category': {
                'ui': 95.0,
                'narrative': 80.0,
                'system': 90.0
            }
        }
    
    async def _calculate_timing_coverage(
        self,
        language_code: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate timing data coverage."""
        # This would query actual timing generation records
        # For now, return mock data
        return {
            'total_audio_files': 850,
            'timing_generated': 800,
            'coverage_percentage': 94.1,
            'quality_metrics': {
                'high_quality': 700,
                'medium_quality': 80,
                'low_quality': 20
            }
        }
    
    async def pregenerate_assets(
        self,
        language_code: str,
        categories: List[str],
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Pre-generate all localization assets for a language.
        
        Useful for preparing builds or DLC releases.
        """
        logger.info(f"Pre-generating assets for {language_code}, categories: {categories}")
        
        generation_stats = {
            'language_code': language_code,
            'start_time': datetime.utcnow().isoformat(),
            'text_processed': 0,
            'audio_generated': 0,
            'timing_generated': 0,
            'errors': []
        }
        
        # Get all strings for categories
        all_strings = []
        for category in categories:
            strings = await self.localization.repository.get_strings_by_category(
                category, language_code, include_unapproved=False
            )
            all_strings.extend(strings)
        
        generation_stats['text_processed'] = len(all_strings)
        
        # Create requests
        requests = []
        for string_data in all_strings:
            # Skip if already generated and not forcing
            if not force_regenerate and await self._check_asset_exists(
                string_data['key'], language_code
            ):
                continue
            
            request = LocalizationRequest(
                key=string_data['key'],
                language_code=language_code,
                mode=LocalizationMode.FULL_SYNC,
                context=None,  # Could add context from metadata
                archetype_id='narrator',  # Default narrator
                generate_audio=True,
                generate_timing=True,
                audio_quality='high'
            )
            requests.append(request)
        
        # Process in batches
        batch_size = 50
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i+batch_size]
            
            try:
                results = await self.process_batch(batch, parallel=True)
                
                # Count successes
                for result in results:
                    if result.audio_data:
                        generation_stats['audio_generated'] += 1
                    if result.timing_data:
                        generation_stats['timing_generated'] += 1
                    
                    # Store assets
                    await self._store_generated_assets(result)
                    
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                generation_stats['errors'].append({
                    'batch_index': i,
                    'error': str(e)
                })
        
        generation_stats['end_time'] = datetime.utcnow().isoformat()
        
        return generation_stats
    
    async def _check_asset_exists(self, key: str, language_code: str) -> bool:
        """Check if audio/timing assets already exist."""
        # This would check storage system
        # For now, return False
        return False
    
    async def _store_generated_assets(self, result: LocalizationResult):
        """Store generated audio and timing assets."""
        # This would integrate with asset storage system
        # Could be S3, local filesystem, or game asset pipeline
        
        if result.audio_data:
            # Store audio file
            audio_path = f"audio/{result.language_code}/{result.key}.wav"
            logger.info(f"Storing audio: {audio_path}")
            
        if result.timing_data:
            # Store timing data
            timing_path = f"timing/{result.language_code}/{result.key}.json"
            logger.info(f"Storing timing: {timing_path}")
    
    async def get_supported_features(self, language_code: str) -> Dict[str, bool]:
        """
        Get supported features for a language.
        
        Returns which features are available: text, TTS, timing, etc.
        """
        # Check language support across systems
        features = {
            'text_localization': False,
            'tts_generation': False,
            'timing_generation': False,
            'recorded_audio': False,
            'lip_sync': False,
            'subtitle_support': False
        }
        
        # Check text support
        languages = await self.localization.repository.get_supported_languages()
        language_codes = [lang['language_code'] for lang in languages]
        features['text_localization'] = language_code in language_codes
        
        # Check TTS support
        tts_voices = await self.tts.get_available_voices(language_code)
        features['tts_generation'] = len(tts_voices) > 0
        
        # Check timing support (based on phoneme mapper availability)
        lang_prefix = language_code.split('-')[0]
        features['timing_generation'] = lang_prefix in self.timing.phoneme_mappers
        
        # Lip sync requires timing
        features['lip_sync'] = features['timing_generation']
        
        # Subtitles require text
        features['subtitle_support'] = features['text_localization']
        
        # Check for recorded audio (would query asset system)
        # For now, set based on tier 1 languages
        features['recorded_audio'] = language_code in ['en-US', 'ja-JP', 'zh-CN']
        
        return features
