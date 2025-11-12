# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
TTS Integration Module
======================

Integrates language system with Text-to-Speech (TTS) for audio generation.
"""

import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


# Cloud TTS imports
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    AWS_POLLY_AVAILABLE = True
except ImportError:
    AWS_POLLY_AVAILABLE = False

try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

# Local TTS imports
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TTSRequest:
    """Request for TTS generation."""
    text: str
    language: str
    voice_id: Optional[str] = None  # Specific voice to use
    emotion: Optional[str] = None  # Emotional tone
    speed: float = 1.0  # Speech speed multiplier
    pitch: float = 1.0  # Pitch adjustment
    volume: float = 1.0  # Volume level
    quality: str = "high"  # low, medium, high


@dataclass
class TTSResult:
    """Result of TTS generation."""
    audio_data: bytes  # Audio file data
    audio_format: str  # wav, mp3, ogg, etc.
    duration_seconds: float
    sample_rate: int
    voice_used: str
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TTSIntegration:
    """
    TTS integration for language system.
    
    Supports:
    - Multiple TTS engines (local and cloud)
    - Language-specific voice characteristics
    - Phoneme-based synthesis for made-up languages
    - Real-time or pre-generation
    - Quality vs. performance optimization
    """
    
    def __init__(self):
        """Initialize TTS Integration."""
        # Initialize cloud TTS clients
        self.polly_client = None
        if AWS_POLLY_AVAILABLE:
            try:
                self.polly_client = boto3.client('polly', region_name=os.getenv('AWS_REGION', 'us-east-1'))
                logger.info("AWS Polly client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS Polly: {e}")
        
        self.google_tts_client = None
        if GOOGLE_TTS_AVAILABLE:
            try:
                self.google_tts_client = texttospeech.TextToSpeechClient()
                logger.info("Google Cloud TTS client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google TTS: {e}")
        
        # Initialize local TTS engine
        self.local_tts_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.local_tts_engine = pyttsx3.init()
                logger.info("Local TTS engine (pyttsx3) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize local TTS engine: {e}")
        
        # TTS engine configuration
        self.tts_engines = {
            "local": {
                "name": "Local TTS Engine",
                "supports_languages": ["common", "vampire", "werewolf"],  # Made-up languages
                "quality": "medium",
                "latency": "low",
            },
            "cloud": {
                "name": "Cloud TTS API",
                "supports_languages": ["italian", "french", "spanish", "common"],  # Real languages
                "quality": "high",
                "latency": "medium",
            },
            "phoneme": {
                "name": "Phoneme-based Synthesizer",
                "supports_languages": ["vampire", "werewolf", "zombie", "ghoul", "lich"],  # All made-up
                "quality": "medium",
                "latency": "low",
            },
        }
        
        # Voice bank configuration
        self.voice_banks = {
            "vampire": {
                "voices": ["vampire_male_1", "vampire_female_1", "vampire_elder"],
                "characteristics": ["sibilant", "dark", "ritualistic"],
            },
            "werewolf": {
                "voices": ["werewolf_male_1", "werewolf_female_1", "werewolf_alpha"],
                "characteristics": ["guttural", "growling", "aggressive"],
            },
            "common": {
                "voices": ["common_male_1", "common_female_1", "common_neutral"],
                "characteristics": ["clear", "neutral"],
            },
        }
        
        logger.info("TTSIntegration initialized")
    
    async def generate_speech(
        self,
        request: TTSRequest,
        language_def: LanguageDefinition
    ) -> TTSResult:
        """
        Generate speech audio from text.
        
        Args:
            request: TTS request
            language_def: Language definition
            
        Returns:
            TTSResult with audio data
        """
        logger.info(f"Generating TTS for {request.language}: {request.text[:50]}...")
        
        # Select appropriate TTS engine
        engine = self._select_engine(language_def)
        
        # Select voice
        voice = self._select_voice(request, language_def)
        
        # Generate audio based on engine type
        if engine == "phoneme" or language_def.language_type in [LanguageType.MONSTER, LanguageType.RITUAL, LanguageType.ANCIENT]:
            # Use phoneme-based synthesis for made-up languages
            result = await self._generate_phoneme_speech(request, language_def, voice)
        elif engine == "cloud":
            # Use cloud TTS for real languages
            result = await self._generate_cloud_speech(request, language_def, voice)
        else:
            # Use local TTS engine
            result = await self._generate_local_speech(request, language_def, voice)
        
        return result
    
    def _select_engine(self, language_def: LanguageDefinition) -> str:
        """Select appropriate TTS engine for language."""
        if language_def.language_type in [LanguageType.MONSTER, LanguageType.RITUAL, LanguageType.ANCIENT]:
            return "phoneme"
        elif language_def.language_type == LanguageType.HUMAN:
            return "cloud"  # Real languages use cloud TTS
        else:
            return "local"
    
    def _select_voice(
        self,
        request: TTSRequest,
        language_def: LanguageDefinition
    ) -> str:
        """Select voice for TTS generation."""
        if request.voice_id:
            return request.voice_id
        
        # Select default voice based on language
        language_name_lower = language_def.name.lower()
        
        if language_name_lower in self.voice_banks:
            voices = self.voice_banks[language_name_lower]["voices"]
            return voices[0]  # Use first available voice
        
        # Fallback
        return "common_neutral"
    
    async def _generate_phoneme_speech(
        self,
        request: TTSRequest,
        language_def: LanguageDefinition,
        voice: str
    ) -> TTSResult:
        """Generate speech using phoneme-based synthesis."""
        logger.info(f"Generating phoneme-based speech for {language_def.name}")
        
        try:
            # Convert text to phonemes using language definition
            phonemes = self._text_to_phonemes(request.text, language_def)
            
            # Apply phonotactics rules
            valid_phonemes = self._apply_phonotactics(phonemes, language_def)
            
            # Use espeak-ng or festival for phoneme-to-speech synthesis
            # espeak-ng supports phoneme input via SSML or direct phoneme strings
            audio_data = await self._synthesize_phonemes(valid_phonemes, voice, language_def, request.speed, request.pitch)
            
            # Calculate duration (estimate based on phoneme count)
            duration = len(valid_phonemes) * 0.08  # ~80ms per phoneme
            
            return TTSResult(
                audio_data=audio_data,
                audio_format="wav",
                duration_seconds=duration,
                sample_rate=22050,
                voice_used=voice,
                language=request.language,
                metadata={
                    "method": "phoneme_synthesis",
                    "phonemes_used": len(valid_phonemes),
                    "original_phonemes": len(phonemes),
                    "voice_characteristics": self.voice_banks.get(language_def.name.lower(), {}).get("characteristics", [])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in phoneme synthesis: {e}")
            # Fallback to empty audio on error
            return TTSResult(
                audio_data=b"",
                audio_format="wav",
                duration_seconds=len(request.text) * 0.1,
                sample_rate=22050,
                voice_used=voice,
                language=request.language,
                metadata={
                    "method": "phoneme_synthesis",
                    "error": str(e)
                }
            )
    
    def _text_to_phonemes(self, text: str, language_def: LanguageDefinition) -> List[str]:
        """Convert text to phonemes using language definition."""
        # Simple phoneme mapping (in production, use more sophisticated conversion)
        phonemes = []
        for char in text.lower():
            # Map characters to phonemes based on language definition
            if char in language_def.phoneme_inventory.vowels:
                phonemes.append(char)
            elif char in language_def.phoneme_inventory.consonants:
                phonemes.append(char)
            # Add space phoneme for word boundaries
            elif char == ' ':
                phonemes.append(' ')
        
        return phonemes
    
    def _apply_phonotactics(self, phonemes: List[str], language_def: LanguageDefinition) -> List[str]:
        """Apply phonotactics rules to phoneme sequence."""
        # In production, apply complex phonotactics rules
        # For now, return as-is (validation would happen here)
        return [p for p in phonemes if p.strip()]  # Remove empty strings
    
    async def _synthesize_phonemes(self, phonemes: List[str], voice: str, language_def: LanguageDefinition, speed: float = 1.0, pitch: float = 1.0) -> bytes:
        """Synthesize audio from phonemes using espeak-ng or festival."""
        try:
            # Use espeak-ng for phoneme synthesis (supports phoneme input)
            # Format phonemes for espeak-ng
            phoneme_string = ' '.join(phonemes)
            
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            try:
                # Use espeak-ng with phoneme input
                # espeak-ng -x (phoneme mode) -s (speed) -p (pitch) -v (voice)
                # Use provided speed and pitch
                speed_wpm = int(150 * speed)
                pitch_value = int(50 * pitch)
                cmd = [
                    'espeak-ng',
                    '-x',  # Phoneme mode
                    '-s', str(speed_wpm),  # Speed (words per minute)
                    '-p', str(pitch_value),  # Pitch (0-99)
                    '-v', voice if voice else 'en',  # Voice
                    '-w', output_path,  # Output file
                    phoneme_string
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        audio_data = f.read()
                    return audio_data
                else:
                    logger.warning(f"espeak-ng synthesis failed: {result.stderr}")
                    # Fallback: generate silent audio
                    return self._generate_silent_audio(duration_seconds=len(phonemes) * 0.08)
                    
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
                    
        except FileNotFoundError:
            logger.warning("espeak-ng not found, using fallback")
            return self._generate_silent_audio(duration_seconds=len(phonemes) * 0.08)
        except Exception as e:
            logger.error(f"Error in phoneme synthesis: {e}")
            return self._generate_silent_audio(duration_seconds=len(phonemes) * 0.08)
    
    def _generate_silent_audio(self, duration_seconds: float, sample_rate: int = 22050) -> bytes:
        """Generate silent audio as fallback."""
        import numpy as np
        import wave
        import io
        
        # Generate silent audio
        num_samples = int(duration_seconds * sample_rate)
        silent_audio = np.zeros(num_samples, dtype=np.int16)
        
        # Convert to WAV bytes
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silent_audio.tobytes())
        
        return wav_buffer.getvalue()
    
    async def _generate_cloud_speech(
        self,
        request: TTSRequest,
        language_def: LanguageDefinition,
        voice: str
    ) -> TTSResult:
        """Generate speech using cloud TTS API (AWS Polly or Google TTS)."""
        logger.info(f"Generating cloud TTS for {language_def.name}")
        
        # Try AWS Polly first, then Google TTS
        if self.polly_client:
            try:
                return await self._generate_polly_speech(request, voice)
            except Exception as e:
                logger.warning(f"AWS Polly failed: {e}, trying Google TTS")
        
        if self.google_tts_client:
            try:
                return await self._generate_google_tts_speech(request, voice)
            except Exception as e:
                logger.warning(f"Google TTS failed: {e}")
        
        # Fallback to local TTS if cloud services unavailable
        logger.warning("Cloud TTS unavailable, using local fallback")
        return await self._generate_local_speech(request, language_def, voice)
    
    async def _generate_polly_speech(self, request: TTSRequest, voice: str) -> TTSResult:
        """Generate speech using AWS Polly."""
        # Map language to Polly voice
        voice_map = {
            "common": "Joanna",
            "italian": "Bianca",
            "french": "Celine",
            "spanish": "Conchita"
        }
        
        polly_voice = voice_map.get(request.language.lower(), "Joanna")
        
        # Polly SSML parameters
        ssml_text = f"""
        <speak>
            <prosody rate="{request.speed * 100}%" pitch="{request.pitch * 100}%">
                {request.text}
            </prosody>
        </speak>
        """
        
        try:
            response = self.polly_client.synthesize_speech(
                Text=request.text,
                TextType='text',
                OutputFormat='mp3',
                VoiceId=polly_voice,
                Engine='neural' if request.quality == "high" else 'standard'
            )
            
            audio_data = response['AudioStream'].read()
            
            # Estimate duration (Polly returns ~150 words/minute)
            words_per_minute = 150
            word_count = len(request.text.split())
            duration = (word_count / words_per_minute) * 60
            
            return TTSResult(
                audio_data=audio_data,
                audio_format="mp3",
                duration_seconds=duration,
                sample_rate=24000,  # Polly standard
                voice_used=polly_voice,
                language=request.language,
                metadata={
                    "method": "aws_polly",
                    "engine": "neural" if request.quality == "high" else "standard",
                    "voice_id": polly_voice
                }
            )
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS Polly error: {e}")
            raise
    
    async def _generate_google_tts_speech(self, request: TTSRequest, voice: str) -> TTSResult:
        """Generate speech using Google Cloud TTS."""
        # Map language to Google TTS voice
        language_code_map = {
            "common": "en-US",
            "italian": "it-IT",
            "french": "fr-FR",
            "spanish": "es-ES"
        }
        
        language_code = language_code_map.get(request.language.lower(), "en-US")
        
        # Select voice
        voices = self.google_tts_client.list_voices(language_code=language_code)
        selected_voice = None
        for v in voices.voices:
            if voice.lower() in v.name.lower() or v.name.startswith(language_code):
                selected_voice = v
                break
        
        if not selected_voice:
            # Use first available voice
            selected_voice = voices.voices[0] if voices.voices else None
        
        synthesis_input = texttospeech.SynthesisInput(text=request.text)
        
        # Configure voice
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=selected_voice.name if selected_voice else None,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        # Configure audio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=request.speed,
            pitch=request.pitch,
            volume_gain_db=20 * (request.volume - 1.0)  # Convert 0-1 to dB
        )
        
        try:
            response = self.google_tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            audio_data = response.audio_content
            
            # Estimate duration
            words_per_minute = 150
            word_count = len(request.text.split())
            duration = (word_count / words_per_minute) * 60
            
            return TTSResult(
                audio_data=audio_data,
                audio_format="mp3",
                duration_seconds=duration,
                sample_rate=24000,  # Google TTS standard
                voice_used=selected_voice.name if selected_voice else "default",
                language=request.language,
                metadata={
                    "method": "google_cloud_tts",
                    "language_code": language_code,
                    "voice_name": selected_voice.name if selected_voice else "default"
                }
            )
            
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            raise
    
    async def _generate_local_speech(
        self,
        request: TTSRequest,
        language_def: LanguageDefinition,
        voice: str
    ) -> TTSResult:
        """Generate speech using local TTS engine (pyttsx3)."""
        logger.info(f"Generating local TTS for {language_def.name}")
        
        if not self.local_tts_engine:
            # Fallback: generate silent audio
            logger.warning("Local TTS engine not available")
            return TTSResult(
                audio_data=self._generate_silent_audio(len(request.text) * 0.1),
                audio_format="wav",
                duration_seconds=len(request.text) * 0.1,
                sample_rate=22050,
                voice_used=voice,
                language=request.language,
                metadata={
                    "method": "local_tts",
                    "engine": "fallback",
                    "error": "Local TTS engine not available"
                }
            )
        
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            try:
                # Configure voice and properties
                voices = self.local_tts_engine.getProperty('voices')
                if voices and voice:
                    # Try to find matching voice
                    for v in voices:
                        if voice.lower() in v.name.lower():
                            self.local_tts_engine.setProperty('voice', v.id)
                            break
                
                # Set speech properties
                self.local_tts_engine.setProperty('rate', int(150 * request.speed))  # Speed (words per minute)
                self.local_tts_engine.setProperty('volume', request.volume)
                
                # Save to file
                self.local_tts_engine.save_to_file(request.text, output_path)
                self.local_tts_engine.runAndWait()
                
                # Read audio file
                if os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        audio_data = f.read()
                    
                    # Estimate duration
                    duration = len(request.text) * 0.1
                    
                    return TTSResult(
                        audio_data=audio_data,
                        audio_format="wav",
                        duration_seconds=duration,
                        sample_rate=22050,
                        voice_used=voice,
                        language=request.language,
                        metadata={
                            "method": "local_tts",
                            "engine": "pyttsx3",
                            "voice": voice
                        }
                    )
                else:
                    raise FileNotFoundError("TTS output file not created")
                    
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
                    
        except Exception as e:
            logger.error(f"Error in local TTS generation: {e}")
            # Fallback to silent audio
            return TTSResult(
                audio_data=self._generate_silent_audio(len(request.text) * 0.1),
                audio_format="wav",
                duration_seconds=len(request.text) * 0.1,
                sample_rate=22050,
                voice_used=voice,
                language=request.language,
                metadata={
                    "method": "local_tts",
                    "engine": "fallback",
                    "error": str(e)
                }
            )
    
    def get_available_voices(self, language: str) -> List[str]:
        """Get available voices for a language."""
        language_lower = language.lower()
        if language_lower in self.voice_banks:
            return self.voice_banks[language_lower]["voices"]
        return ["default"]
    
    def get_voice_characteristics(self, language: str) -> List[str]:
        """Get voice characteristics for a language."""
        language_lower = language.lower()
        if language_lower in self.voice_banks:
            return self.voice_banks[language_lower]["characteristics"]
        return []

