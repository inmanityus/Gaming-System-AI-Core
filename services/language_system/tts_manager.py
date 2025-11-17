"""
TTS (Text-to-Speech) manager for multi-language voice generation.
Implements TML-04 (R-ML-TTS-001, R-ML-TTS-002).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import hashlib
import json
import httpx
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class TTSProvider(str, Enum):
    """Available TTS providers."""
    AZURE_COGNITIVE = "azure_cognitive"
    GOOGLE_CLOUD = "google_cloud" 
    AWS_POLLY = "aws_polly"
    ELEVEN_LABS = "eleven_labs"
    RECORDED = "recorded"  # Pre-recorded audio
    HYBRID = "hybrid"      # Mix of recorded and TTS


@dataclass
class VoiceProfile:
    """Voice configuration for a character/archetype."""
    voice_id: str
    provider: TTSProvider
    language_code: str
    
    # Provider-specific settings
    voice_name: str  # Provider's voice name
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume_gain_db: float = 0.0
    
    # Emotion and style parameters
    style: Optional[str] = None  # e.g., "cheerful", "sad", "angry"
    style_degree: float = 1.0
    
    # Horror game specific
    effects: List[str] = None  # e.g., ["whisper", "echo", "distortion"]
    corruption_level: float = 0.0  # 0-1, for supernatural voices
    
    def __post_init__(self):
        if self.effects is None:
            self.effects = []


@dataclass 
class TTSResult:
    """Result of TTS generation."""
    audio_data: bytes
    sample_rate: int
    duration_seconds: float
    
    # Timing information
    phoneme_timings: Optional[List[Dict[str, Any]]] = None
    word_timings: Optional[List[Dict[str, Any]]] = None
    viseme_timings: Optional[List[Dict[str, Any]]] = None
    
    # Metadata
    provider_used: TTSProvider = None
    voice_id: str = None
    cached: bool = False
    generation_time_ms: float = 0


class TTSManager:
    """
    Manages text-to-speech generation across multiple providers and languages.
    Handles voice profiles, caching, and fallback strategies.
    """
    
    def __init__(self, config: Dict[str, Any], cache_manager=None):
        self.config = config
        self.cache = cache_manager
        self.providers = self._initialize_providers()
        self.voice_profiles = {}
        self.default_profiles = self._load_default_profiles()
        
    def _initialize_providers(self) -> Dict[TTSProvider, Any]:
        """Initialize TTS provider clients."""
        providers = {}
        
        # Azure Cognitive Services
        if self.config.get('azure_cognitive_enabled'):
            from .providers.azure_tts import AzureTTSProvider
            providers[TTSProvider.AZURE_COGNITIVE] = AzureTTSProvider(
                self.config['azure_cognitive']
            )
        
        # Google Cloud TTS
        if self.config.get('google_cloud_enabled'):
            from .providers.google_tts import GoogleTTSProvider
            providers[TTSProvider.GOOGLE_CLOUD] = GoogleTTSProvider(
                self.config['google_cloud']
            )
        
        # AWS Polly
        if self.config.get('aws_polly_enabled'):
            from .providers.aws_polly import AWSPollyProvider
            providers[TTSProvider.AWS_POLLY] = AWSPollyProvider(
                self.config['aws_polly']
            )
        
        # Eleven Labs
        if self.config.get('eleven_labs_enabled'):
            from .providers.eleven_labs import ElevenLabsProvider
            providers[TTSProvider.ELEVEN_LABS] = ElevenLabsProvider(
                self.config['eleven_labs']
            )
        
        logger.info(f"Initialized TTS providers: {list(providers.keys())}")
        return providers
    
    def _load_default_profiles(self) -> Dict[str, Dict[str, VoiceProfile]]:
        """Load default voice profiles for each language and archetype."""
        profiles = {}
        
        # English profiles
        profiles['en-US'] = {
            'vampire_alpha': VoiceProfile(
                voice_id='vampire_alpha_en',
                provider=TTSProvider.AZURE_COGNITIVE,
                language_code='en-US',
                voice_name='en-US-GuyNeural',
                speaking_rate=0.85,
                pitch=-0.2,
                style='unfriendly',
                effects=['low_pass', 'reverb'],
                corruption_level=0.3
            ),
            'narrator': VoiceProfile(
                voice_id='narrator_en',
                provider=TTSProvider.AZURE_COGNITIVE,
                language_code='en-US',
                voice_name='en-US-AriaNeural',
                speaking_rate=0.95,
                pitch=0.0,
                style='narration-professional'
            ),
            'human_agent': VoiceProfile(
                voice_id='human_agent_en',
                provider=TTSProvider.GOOGLE_CLOUD,
                language_code='en-US',
                voice_name='en-US-Neural2-C',
                speaking_rate=1.0,
                pitch=0.1
            )
        }
        
        # Japanese profiles
        profiles['ja-JP'] = {
            'vampire_alpha': VoiceProfile(
                voice_id='vampire_alpha_ja',
                provider=TTSProvider.AZURE_COGNITIVE,
                language_code='ja-JP',
                voice_name='ja-JP-KeitaNeural',
                speaking_rate=0.9,
                pitch=-0.15,
                effects=['low_pass', 'echo'],
                corruption_level=0.25
            ),
            'narrator': VoiceProfile(
                voice_id='narrator_ja',
                provider=TTSProvider.GOOGLE_CLOUD,
                language_code='ja-JP',
                voice_name='ja-JP-Neural2-B',
                speaking_rate=0.95,
                pitch=0.0
            )
        }
        
        # Add more language profiles...
        
        return profiles
    
    async def generate_speech(
        self,
        text: str,
        language_code: str,
        speaker_id: Optional[str] = None,
        archetype_id: Optional[str] = None,
        emotion: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Generate speech from text using appropriate voice profile.
        
        Args:
            text: Text to synthesize
            language_code: Target language
            speaker_id: Specific speaker/character ID
            archetype_id: Character archetype for voice selection
            emotion: Emotional style to apply
            **kwargs: Additional provider-specific parameters
            
        Returns:
            TTSResult with audio data and timing information
        """
        # Get voice profile
        profile = await self._get_voice_profile(
            language_code, speaker_id, archetype_id
        )
        
        # Check cache first
        cache_key = self._generate_cache_key(text, profile, emotion)
        if self.cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                cached_result.cached = True
                return cached_result
        
        # Apply emotion to profile if specified
        if emotion:
            profile = self._apply_emotion(profile, emotion)
        
        # Generate speech
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Try primary provider
            result = await self._generate_with_provider(
                text, profile, profile.provider, **kwargs
            )
            
        except Exception as e:
            logger.error(f"Primary TTS provider failed: {e}")
            
            # Try fallback providers
            result = await self._generate_with_fallback(
                text, profile, **kwargs
            )
        
        # Calculate generation time
        result.generation_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Apply post-processing effects
        if profile.effects:
            result = await self._apply_effects(result, profile.effects, profile.corruption_level)
        
        # Cache the result
        if self.cache and result:
            await self.cache.set(cache_key, result)
        
        return result
    
    async def generate_batch(
        self,
        texts: List[Dict[str, Any]],
        language_code: str,
        parallel: bool = True
    ) -> List[TTSResult]:
        """
        Generate speech for multiple texts efficiently.
        
        Args:
            texts: List of dicts with 'text', 'speaker_id', 'emotion' etc.
            language_code: Target language for all texts
            parallel: Whether to generate in parallel
            
        Returns:
            List of TTSResults in same order as inputs
        """
        if parallel:
            # Generate in parallel with concurrency limit
            semaphore = asyncio.Semaphore(self.config.get('max_parallel_tts', 5))
            
            async def generate_with_limit(text_info):
                async with semaphore:
                    return await self.generate_speech(
                        text_info['text'],
                        language_code,
                        speaker_id=text_info.get('speaker_id'),
                        archetype_id=text_info.get('archetype_id'),
                        emotion=text_info.get('emotion')
                    )
            
            tasks = [generate_with_limit(t) for t in texts]
            return await asyncio.gather(*tasks)
        else:
            # Generate sequentially
            results = []
            for text_info in texts:
                result = await self.generate_speech(
                    text_info['text'],
                    language_code,
                    speaker_id=text_info.get('speaker_id'),
                    archetype_id=text_info.get('archetype_id'),
                    emotion=text_info.get('emotion')
                )
                results.append(result)
            return results
    
    async def _get_voice_profile(
        self,
        language_code: str,
        speaker_id: Optional[str] = None,
        archetype_id: Optional[str] = None
    ) -> VoiceProfile:
        """Get appropriate voice profile for the request."""
        # Check for specific speaker profile
        if speaker_id and speaker_id in self.voice_profiles:
            return self.voice_profiles[speaker_id]
        
        # Check for archetype profile in language
        if archetype_id and language_code in self.default_profiles:
            if archetype_id in self.default_profiles[language_code]:
                return self.default_profiles[language_code][archetype_id]
        
        # Fall back to narrator voice for language
        if language_code in self.default_profiles:
            if 'narrator' in self.default_profiles[language_code]:
                return self.default_profiles[language_code]['narrator']
        
        # Ultimate fallback - English narrator
        return self.default_profiles['en-US']['narrator']
    
    def _apply_emotion(self, profile: VoiceProfile, emotion: str) -> VoiceProfile:
        """Apply emotional styling to voice profile."""
        # Create a copy to avoid modifying original
        import copy
        profile = copy.deepcopy(profile)
        
        # Emotion to parameter mappings (provider-specific)
        emotion_mappings = {
            'angry': {
                'speaking_rate': 1.1,
                'pitch': 0.1,
                'style': 'angry',
                'style_degree': 1.5
            },
            'sad': {
                'speaking_rate': 0.9,
                'pitch': -0.1,
                'style': 'sad',
                'style_degree': 1.2
            },
            'fearful': {
                'speaking_rate': 1.2,
                'pitch': 0.2,
                'style': 'fearful',
                'style_degree': 1.3,
                'effects': profile.effects + ['tremolo']
            },
            'whisper': {
                'speaking_rate': 0.8,
                'volume_gain_db': -6,
                'style': 'whispering',
                'effects': profile.effects + ['whisper_filter']
            }
        }
        
        if emotion in emotion_mappings:
            mapping = emotion_mappings[emotion]
            for key, value in mapping.items():
                if hasattr(profile, key):
                    if key == 'effects':
                        # Append to existing effects
                        profile.effects = list(set(profile.effects + value))
                    else:
                        setattr(profile, key, value)
        
        return profile
    
    async def _generate_with_provider(
        self,
        text: str,
        profile: VoiceProfile,
        provider: TTSProvider,
        **kwargs
    ) -> TTSResult:
        """Generate speech using specific provider."""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        provider_client = self.providers[provider]
        
        # Provider-specific generation
        if provider == TTSProvider.AZURE_COGNITIVE:
            return await provider_client.synthesize(
                text,
                voice_name=profile.voice_name,
                language=profile.language_code,
                speaking_rate=profile.speaking_rate,
                pitch=profile.pitch,
                style=profile.style,
                style_degree=profile.style_degree,
                **kwargs
            )
        elif provider == TTSProvider.GOOGLE_CLOUD:
            return await provider_client.synthesize(
                text,
                voice_name=profile.voice_name,
                language_code=profile.language_code,
                speaking_rate=profile.speaking_rate,
                pitch=profile.pitch,
                volume_gain_db=profile.volume_gain_db,
                **kwargs
            )
        # Add other providers...
        else:
            raise NotImplementedError(f"Provider {provider} not implemented")
    
    async def _generate_with_fallback(
        self,
        text: str,
        profile: VoiceProfile,
        **kwargs
    ) -> Optional[TTSResult]:
        """Try fallback providers if primary fails."""
        # Define fallback order
        fallback_order = [
            TTSProvider.AZURE_COGNITIVE,
            TTSProvider.GOOGLE_CLOUD,
            TTSProvider.AWS_POLLY
        ]
        
        # Remove primary provider from fallback
        fallback_order = [p for p in fallback_order if p != profile.provider]
        
        for provider in fallback_order:
            if provider in self.providers:
                try:
                    logger.info(f"Trying fallback provider: {provider}")
                    
                    # Adjust profile for fallback provider
                    fallback_profile = self._adapt_profile_for_provider(profile, provider)
                    
                    return await self._generate_with_provider(
                        text, fallback_profile, provider, **kwargs
                    )
                except Exception as e:
                    logger.error(f"Fallback provider {provider} failed: {e}")
                    continue
        
        raise RuntimeError("All TTS providers failed")
    
    def _adapt_profile_for_provider(
        self, 
        profile: VoiceProfile, 
        provider: TTSProvider
    ) -> VoiceProfile:
        """Adapt voice profile for different provider."""
        import copy
        adapted = copy.deepcopy(profile)
        adapted.provider = provider
        
        # Map voice names between providers
        voice_mappings = {
            # Azure to Google mappings
            ('en-US-GuyNeural', TTSProvider.GOOGLE_CLOUD): 'en-US-Neural2-D',
            ('en-US-AriaNeural', TTSProvider.GOOGLE_CLOUD): 'en-US-Neural2-F',
            ('ja-JP-KeitaNeural', TTSProvider.GOOGLE_CLOUD): 'ja-JP-Neural2-C',
            
            # Azure to AWS mappings
            ('en-US-GuyNeural', TTSProvider.AWS_POLLY): 'Matthew',
            ('en-US-AriaNeural', TTSProvider.AWS_POLLY): 'Joanna',
            
            # Add more mappings...
        }
        
        mapping_key = (profile.voice_name, provider)
        if mapping_key in voice_mappings:
            adapted.voice_name = voice_mappings[mapping_key]
        else:
            # Use default voice for language
            adapted.voice_name = self._get_default_voice(provider, profile.language_code)
        
        return adapted
    
    def _get_default_voice(self, provider: TTSProvider, language_code: str) -> str:
        """Get default voice for provider and language."""
        defaults = {
            TTSProvider.AZURE_COGNITIVE: {
                'en-US': 'en-US-JennyNeural',
                'ja-JP': 'ja-JP-NanamiNeural',
                'zh-CN': 'zh-CN-XiaoxiaoNeural',
                'ko-KR': 'ko-KR-SunHiNeural',
                'fr-FR': 'fr-FR-DeniseNeural',
                'de-DE': 'de-DE-KatjaNeural',
                'es-ES': 'es-ES-ElviraNeural',
                'pt-BR': 'pt-BR-FranciscaNeural'
            },
            TTSProvider.GOOGLE_CLOUD: {
                'en-US': 'en-US-Neural2-C',
                'ja-JP': 'ja-JP-Neural2-B',
                'zh-CN': 'cmn-CN-Standard-A',
                'ko-KR': 'ko-KR-Neural2-A',
                'fr-FR': 'fr-FR-Neural2-A',
                'de-DE': 'de-DE-Neural2-A',
                'es-ES': 'es-ES-Neural2-A',
                'pt-BR': 'pt-BR-Neural2-A'
            },
            TTSProvider.AWS_POLLY: {
                'en-US': 'Joanna',
                'ja-JP': 'Mizuki',
                'zh-CN': 'Zhiyu',
                'ko-KR': 'Seoyeon',
                'fr-FR': 'Celine',
                'de-DE': 'Marlene',
                'es-ES': 'Conchita',
                'pt-BR': 'Vitoria'
            }
        }
        
        if provider in defaults and language_code in defaults[provider]:
            return defaults[provider][language_code]
        
        # Ultimate fallback
        return 'default'
    
    async def _apply_effects(
        self,
        result: TTSResult,
        effects: List[str],
        corruption_level: float
    ) -> TTSResult:
        """Apply audio effects for horror game atmosphere."""
        # This would integrate with audio processing pipeline
        # For now, just mark that effects were requested
        logger.info(f"Effects requested: {effects}, corruption: {corruption_level}")
        
        # In production, this would:
        # 1. Apply filters (low_pass, high_pass, band_pass)
        # 2. Add reverb/echo
        # 3. Apply corruption/distortion
        # 4. Add whisper processing
        # 5. Apply tremolo/vibrato
        
        return result
    
    def _generate_cache_key(
        self,
        text: str,
        profile: VoiceProfile,
        emotion: Optional[str]
    ) -> str:
        """Generate cache key for TTS result."""
        key_parts = [
            text,
            profile.voice_id,
            profile.provider.value,
            str(profile.speaking_rate),
            str(profile.pitch),
            emotion or 'neutral'
        ]
        
        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def get_available_voices(
        self,
        language_code: Optional[str] = None,
        provider: Optional[TTSProvider] = None
    ) -> List[Dict[str, Any]]:
        """Get list of available voices, optionally filtered."""
        voices = []
        
        for p, client in self.providers.items():
            if provider and p != provider:
                continue
                
            provider_voices = await client.list_voices(language_code)
            
            for voice in provider_voices:
                voices.append({
                    'provider': p.value,
                    'voice_id': voice['id'],
                    'name': voice['name'],
                    'language_codes': voice['language_codes'],
                    'gender': voice.get('gender'),
                    'age': voice.get('age'),
                    'style_support': voice.get('style_support', []),
                    'sample_url': voice.get('sample_url')
                })
        
        return voices
    
    async def create_voice_profile(
        self,
        speaker_id: str,
        profile_data: Dict[str, Any]
    ) -> VoiceProfile:
        """Create and store a custom voice profile."""
        profile = VoiceProfile(
            voice_id=profile_data['voice_id'],
            provider=TTSProvider(profile_data['provider']),
            language_code=profile_data['language_code'],
            voice_name=profile_data['voice_name'],
            speaking_rate=profile_data.get('speaking_rate', 1.0),
            pitch=profile_data.get('pitch', 0.0),
            volume_gain_db=profile_data.get('volume_gain_db', 0.0),
            style=profile_data.get('style'),
            style_degree=profile_data.get('style_degree', 1.0),
            effects=profile_data.get('effects', []),
            corruption_level=profile_data.get('corruption_level', 0.0)
        )
        
        self.voice_profiles[speaker_id] = profile
        
        # TODO: Persist to database
        
        return profile
    
    async def estimate_duration(self, text: str, language_code: str) -> float:
        """Estimate speech duration without generating audio."""
        # Simple estimation based on character count and language
        # More sophisticated estimation would consider:
        # - Syllable count
        # - Word complexity
        # - Punctuation pauses
        # - Language-specific speaking rates
        
        char_rates = {
            'en': 14.0,  # Characters per second
            'ja': 10.0,  # Japanese is more compact
            'zh': 8.0,   # Chinese even more so
            'ko': 9.0,
            'fr': 13.0,
            'de': 12.0,
            'es': 14.0,
            'pt': 13.0
        }
        
        lang_prefix = language_code.split('-')[0]
        rate = char_rates.get(lang_prefix, 13.0)
        
        # Account for punctuation pauses
        pause_chars = '.!?;:'
        pause_count = sum(1 for c in text if c in pause_chars)
        
        # Basic formula
        duration = len(text) / rate + (pause_count * 0.5)
        
        return duration
