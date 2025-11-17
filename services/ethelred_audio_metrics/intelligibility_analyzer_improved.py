"""
Enhanced intelligibility analyzer for audio segments.
Implements TAUD-07 (R-AUD-MET-001) with production improvements.
"""
import logging
from typing import Dict, Tuple, Optional, List
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class IntelligibilityConfig:
    """Configuration for intelligibility analysis."""
    sample_rate: int = 48000  # Default to common game audio rate
    
    # Frame processing
    frame_duration_ms: float = 20.0
    frame_overlap_ratio: float = 0.5
    
    # VAD parameters (adaptive for horror game environments)
    vad_energy_percentile: float = 30.0
    vad_zero_crossing_threshold: float = 0.02
    vad_spectral_flatness_threshold: float = 0.5
    
    # Frequency analysis
    min_fft_size: int = 512
    preferred_fft_size: int = 2048
    
    # Horror game specific
    reverb_compensation: bool = True
    noise_floor_adaptation: bool = True
    whisper_mode_detection: bool = True
    
    # Thresholds
    acceptable_threshold: float = 0.75
    degraded_threshold: float = 0.50
    
    # Confidence parameters
    min_audio_duration_ms: float = 100.0
    min_frames_for_analysis: int = 5


class SpectralCache:
    """Cache for spectral computations to avoid redundant FFTs."""
    def __init__(self):
        self._cache: Dict[int, Dict[str, np.ndarray]] = {}
    
    def get_or_compute(self, audio_hash: int, compute_func, *args, **kwargs):
        """Get cached result or compute if not available."""
        if audio_hash not in self._cache:
            self._cache[audio_hash] = compute_func(*args, **kwargs)
        return self._cache[audio_hash]
    
    def clear(self):
        """Clear the cache."""
        self._cache.clear()


class IntelligibilityAnalyzer:
    """
    Enhanced speech intelligibility analyzer for horror game audio.
    Handles complex acoustic environments with reverb, background noise,
    and special voice effects (whispers, distortions).
    """
    
    def __init__(self, config: Optional[IntelligibilityConfig] = None):
        self.config = config or IntelligibilityConfig()
        self.spectral_cache = SpectralCache()
        
        # Frequency bands important for speech intelligibility
        # Based on Articulation Index (AI) standard frequency bands
        self.speech_bands = [
            (200, 400),    # Low frequencies (fundamental)
            (400, 600),
            (600, 800),
            (800, 1200),   # Mid frequencies (formants)
            (1200, 1700),
            (1700, 2400),
            (2400, 3400),  # High frequencies (consonants)
            (3400, 4800)
        ]
        
        # Weights for each band (based on contribution to intelligibility)
        self.band_weights = np.array([0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05])
        
        # Language-specific adjustments (can be overridden)
        self.language_adjustments = {
            'en-US': 1.0,
            'ja-JP': 0.95,  # Japanese has different formant patterns
            'zh-CN': 0.93,  # Tonal language considerations
        }
    
    def analyze(self, audio_data: np.ndarray, 
                language_code: str = 'en-US') -> Tuple[float, str, float]:
        """
        Analyze audio intelligibility with confidence scoring.
        
        Returns:
            score: Intelligibility score (0-1)
            band: Classification ('acceptable', 'degraded', 'unacceptable')
            confidence: Confidence in the analysis (0-1)
        """
        try:
            # Validate input
            if audio_data is None or len(audio_data) == 0:
                return 0.0, 'unacceptable', 0.0
            
            # Check minimum duration
            duration_ms = len(audio_data) / self.config.sample_rate * 1000
            if duration_ms < self.config.min_audio_duration_ms:
                logger.warning(f"Audio too short: {duration_ms:.1f}ms")
                return 0.0, 'unacceptable', 0.1
            
            # Normalize audio
            audio_data, norm_factor = self._normalize_audio(audio_data)
            
            # Get cached spectral data
            audio_hash = hash(audio_data.tobytes())
            spectral_data = self.spectral_cache.get_or_compute(
                audio_hash, self._compute_spectral_features, audio_data
            )
            
            # Enhanced SNR calculation
            snr, snr_confidence = self._calculate_enhanced_snr(
                audio_data, spectral_data
            )
            
            # Calculate spectral clarity with reverb compensation
            spectral_clarity = self._calculate_spectral_clarity(
                spectral_data, compensate_reverb=self.config.reverb_compensation
            )
            
            # Calculate articulation index
            articulation_index = self._calculate_articulation_index(spectral_data)
            
            # Detect special modes (whisper, etc.)
            special_mode_adjustment = 1.0
            if self.config.whisper_mode_detection:
                is_whisper = self._detect_whisper_mode(spectral_data)
                if is_whisper:
                    special_mode_adjustment = 0.8  # Lower expectations for whispers
            
            # Language adjustment
            lang_adjustment = self.language_adjustments.get(language_code, 1.0)
            
            # Combine metrics with adjustments
            base_score = (
                0.3 * self._snr_to_score(snr) +
                0.3 * spectral_clarity +
                0.4 * articulation_index
            )
            
            score = base_score * special_mode_adjustment * lang_adjustment
            score = np.clip(score, 0.0, 1.0)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                snr_confidence, duration_ms, norm_factor, spectral_data
            )
            
            # Determine band
            if score >= self.config.acceptable_threshold:
                band = 'acceptable'
            elif score >= self.config.degraded_threshold:
                band = 'degraded'
            else:
                band = 'unacceptable'
            
            logger.info(
                f"Intelligibility analysis: score={score:.3f}, band={band}, "
                f"confidence={confidence:.3f}, SNR={snr:.1f}dB, "
                f"clarity={spectral_clarity:.3f}, AI={articulation_index:.3f}"
            )
            
            return score, band, confidence
            
        except Exception as e:
            logger.error(f"Intelligibility analysis error: {e}")
            return 0.0, 'unacceptable', 0.0
    
    def _normalize_audio(self, audio: np.ndarray) -> Tuple[np.ndarray, float]:
        """Normalize audio to [-1, 1] range, return normalization factor."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            normalized = audio / max_val
            return normalized, max_val
        return audio, 1.0
    
    def _compute_spectral_features(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute all spectral features at once to avoid redundant FFTs."""
        # Calculate appropriate FFT size
        n_fft = min(self.config.preferred_fft_size, 
                   max(self.config.min_fft_size, 2 ** int(np.log2(len(audio)))))
        
        # Compute FFT
        fft_vals = rfft(audio, n=n_fft)
        fft_freqs = rfftfreq(n_fft, 1/self.config.sample_rate)
        magnitude = np.abs(fft_vals)
        phase = np.angle(fft_vals)
        
        # Compute spectrogram for time-frequency analysis
        nperseg = min(self.config.min_fft_size, len(audio))
        freqs, times, Sxx = signal.spectrogram(
            audio, 
            fs=self.config.sample_rate,
            nperseg=nperseg,
            noverlap=int(nperseg * self.config.frame_overlap_ratio),
            window='hann'
        )
        
        # Compute additional features for horror game audio
        spectral_centroid = self._compute_spectral_centroid(magnitude, fft_freqs)
        spectral_flatness = self._compute_spectral_flatness(magnitude)
        
        return {
            'fft_magnitude': magnitude,
            'fft_phase': phase,
            'fft_freqs': fft_freqs,
            'spectrogram': Sxx,
            'spec_freqs': freqs,
            'spec_times': times,
            'spectral_centroid': spectral_centroid,
            'spectral_flatness': spectral_flatness,
            'n_fft': n_fft
        }
    
    def _calculate_enhanced_snr(self, audio: np.ndarray, 
                               spectral_data: Dict[str, np.ndarray]) -> Tuple[float, float]:
        """
        Enhanced SNR calculation for complex acoustic environments.
        Returns (snr_db, confidence).
        """
        frame_size = int(self.config.frame_duration_ms * self.config.sample_rate / 1000)
        hop_size = int(frame_size * (1 - self.config.frame_overlap_ratio))
        
        # Extract frames
        frames = []
        for i in range(0, len(audio) - frame_size + 1, hop_size):
            frames.append(audio[i:i + frame_size])
        
        if len(frames) < self.config.min_frames_for_analysis:
            return 0.0, 0.1
        
        # Multi-feature VAD
        frame_features = []
        for frame in frames:
            energy = np.sum(frame ** 2)
            zcr = self._zero_crossing_rate(frame)
            spectral_flatness = self._compute_spectral_flatness(np.abs(rfft(frame)))
            
            frame_features.append({
                'energy': energy,
                'zcr': zcr,
                'flatness': spectral_flatness
            })
        
        # Adaptive threshold based on distribution
        energies = [f['energy'] for f in frame_features]
        energy_threshold = np.percentile(energies, self.config.vad_energy_percentile)
        
        # Classify frames using multiple criteria
        speech_frames = []
        noise_frames = []
        
        for i, (frame, features) in enumerate(zip(frames, frame_features)):
            is_speech = (
                features['energy'] > energy_threshold and
                features['zcr'] < self.config.vad_zero_crossing_threshold and
                features['flatness'] < self.config.vad_spectral_flatness_threshold
            )
            
            if is_speech:
                speech_frames.append(frame)
            else:
                noise_frames.append(frame)
        
        # Calculate SNR with confidence
        if not speech_frames:
            return 0.0, 0.2
        if not noise_frames:
            # Very clean signal
            return 40.0, 0.8
        
        speech_power = np.mean([np.sum(f ** 2) for f in speech_frames])
        noise_power = np.mean([np.sum(f ** 2) for f in noise_frames])
        
        if noise_power > 0:
            snr_db = 10 * np.log10(speech_power / noise_power)
            snr_db = np.clip(snr_db, -10, 40)
            
            # Confidence based on frame distribution
            speech_ratio = len(speech_frames) / len(frames)
            confidence = min(1.0, speech_ratio * 2)  # Higher ratio = higher confidence
            
            return snr_db, confidence
        
        return 30.0, 0.7
    
    def _calculate_spectral_clarity(self, spectral_data: Dict[str, np.ndarray],
                                   compensate_reverb: bool = True) -> float:
        """
        Calculate spectral clarity with optional reverb compensation.
        """
        Sxx = spectral_data['spectrogram']
        freqs = spectral_data['spec_freqs']
        
        # Focus on speech frequency range (200-4000 Hz)
        speech_mask = (freqs >= 200) & (freqs <= 4000)
        speech_spectrum = Sxx[speech_mask, :]
        
        if speech_spectrum.size == 0:
            return 0.5
        
        clarity_scores = []
        
        for t, frame in enumerate(speech_spectrum.T):
            if np.max(frame) > 1e-10:
                # Adaptive peak detection
                frame_std = np.std(frame)
                if frame_std > 0:
                    # Find peaks with adaptive threshold
                    height_threshold = np.mean(frame) + frame_std
                    peaks, properties = signal.find_peaks(
                        frame, 
                        height=height_threshold,
                        distance=5  # Minimum distance between peaks
                    )
                    
                    if len(peaks) >= 2:  # Need at least 2 formants
                        # Calculate formant clarity
                        peak_prominences = properties.get('peak_heights', frame[peaks])
                        valley_mean = np.mean(frame)
                        
                        # Formant-to-valley ratio
                        clarity = np.mean(peak_prominences) / (valley_mean + 1e-10)
                        
                        # Reverb compensation
                        if compensate_reverb and t > 0:
                            # Check for smearing across time
                            prev_frame = speech_spectrum[:, t-1]
                            temporal_smearing = np.corrcoef(frame, prev_frame)[0, 1]
                            clarity *= (1 - temporal_smearing * 0.3)  # Reduce by up to 30%
                        
                        clarity_scores.append(np.clip(clarity / 10, 0, 1))
                    else:
                        clarity_scores.append(0.3)
                else:
                    clarity_scores.append(0.0)
        
        return np.mean(clarity_scores) if clarity_scores else 0.5
    
    def _calculate_articulation_index(self, spectral_data: Dict[str, np.ndarray]) -> float:
        """
        Calculate Articulation Index using cached spectral data.
        """
        magnitude = spectral_data['fft_magnitude']
        fft_freqs = spectral_data['fft_freqs']
        
        if len(magnitude) == 0:
            return 0.0
        
        # Calculate energy in each speech band
        band_scores = []
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy < 1e-10:
            return 0.0
        
        for (low_freq, high_freq), weight in zip(self.speech_bands, self.band_weights):
            # Find indices for frequency band
            band_mask = (fft_freqs >= low_freq) & (fft_freqs <= high_freq)
            if not np.any(band_mask):
                band_scores.append(0.0)
                continue
                
            band_energy = np.sum(magnitude[band_mask] ** 2)
            
            # Calculate relative energy (normalized by total)
            relative_energy = band_energy / total_energy
            
            # Expected relative energy for this band
            # Use empirical data for horror game speech
            expected_ratios = {
                (200, 400): 0.15,
                (400, 600): 0.20,
                (600, 800): 0.20,
                (800, 1200): 0.15,
                (1200, 1700): 0.10,
                (1700, 2400): 0.10,
                (2400, 3400): 0.07,
                (3400, 4800): 0.03
            }
            expected_energy = expected_ratios.get((low_freq, high_freq), weight * 0.8)
            
            # Score based on how close we are to expected
            if expected_energy > 0:
                band_score = min(relative_energy / expected_energy, 1.0)
                # Apply sqrt to make scoring less harsh
                band_score = np.sqrt(band_score)
            else:
                band_score = 0.0
            
            band_scores.append(band_score * weight)
        
        # Sum weighted band scores
        articulation_index = np.sum(band_scores) / np.sum(self.band_weights)
        
        return articulation_index
    
    def _detect_whisper_mode(self, spectral_data: Dict[str, np.ndarray]) -> bool:
        """Detect if audio is whispered speech."""
        # Whisper characteristics:
        # 1. High spectral flatness (noise-like)
        # 2. Low fundamental frequency energy
        # 3. High frequency emphasis
        
        magnitude = spectral_data['fft_magnitude']
        freqs = spectral_data['fft_freqs']
        flatness = spectral_data['spectral_flatness']
        
        # Check overall spectral flatness
        if flatness < 0.3:  # Not noise-like enough
            return False
        
        # Check F0 region (50-300 Hz) vs high frequency (2000+ Hz)
        f0_mask = (freqs >= 50) & (freqs <= 300)
        hf_mask = (freqs >= 2000) & (freqs <= 4000)
        
        if np.any(f0_mask) and np.any(hf_mask):
            f0_energy = np.sum(magnitude[f0_mask] ** 2)
            hf_energy = np.sum(magnitude[hf_mask] ** 2)
            
            # Whisper has much more HF than F0
            if hf_energy > f0_energy * 3:
                return True
        
        return False
    
    def _calculate_confidence(self, snr_confidence: float, duration_ms: float,
                            norm_factor: float, spectral_data: Dict[str, np.ndarray]) -> float:
        """Calculate overall confidence in the analysis."""
        # Base confidence on multiple factors
        confidence_factors = []
        
        # SNR confidence
        confidence_factors.append(snr_confidence)
        
        # Duration confidence (longer = more confident)
        duration_confidence = min(1.0, duration_ms / 1000)  # Max confidence at 1s
        confidence_factors.append(duration_confidence)
        
        # Signal level confidence (not too quiet)
        level_confidence = min(1.0, norm_factor * 10)  # Assume max at 0.1
        confidence_factors.append(level_confidence)
        
        # Spectral quality confidence (enough frequency resolution)
        fft_size_confidence = min(1.0, spectral_data['n_fft'] / 1024)
        confidence_factors.append(fft_size_confidence)
        
        # Combined confidence (geometric mean for balanced result)
        confidence = np.power(np.prod(confidence_factors), 1/len(confidence_factors))
        
        return confidence
    
    def _zero_crossing_rate(self, frame: np.ndarray) -> float:
        """Calculate zero crossing rate for a frame."""
        signs = np.sign(frame)
        signs[signs == 0] = -1  # Replace zeros with -1
        return np.sum(signs[:-1] != signs[1:]) / len(frame)
    
    def _compute_spectral_centroid(self, magnitude: np.ndarray, 
                                  freqs: np.ndarray) -> float:
        """Compute spectral centroid."""
        if np.sum(magnitude) > 0:
            return np.sum(freqs * magnitude) / np.sum(magnitude)
        return 0.0
    
    def _compute_spectral_flatness(self, magnitude: np.ndarray) -> float:
        """Compute spectral flatness (0=tonal, 1=noise-like)."""
        if len(magnitude) == 0 or np.all(magnitude == 0):
            return 0.0
        
        # Geometric mean / arithmetic mean
        geometric_mean = np.exp(np.mean(np.log(magnitude + 1e-10)))
        arithmetic_mean = np.mean(magnitude)
        
        if arithmetic_mean > 0:
            return geometric_mean / arithmetic_mean
        return 0.0
    
    def _snr_to_score(self, snr_db: float) -> float:
        """Convert SNR in dB to 0-1 score with non-linear mapping."""
        # Use sigmoid-like mapping for more realistic scoring
        # Center at 15 dB (typical for acceptable speech)
        x = (snr_db - 15) / 10
        return 1 / (1 + np.exp(-x))
    
    def get_detailed_analysis(self, audio_data: np.ndarray, 
                             language_code: str = 'en-US') -> Dict[str, any]:
        """
        Get detailed analysis results for debugging and fine-tuning.
        """
        # Clear cache for fresh analysis
        self.spectral_cache.clear()
        
        score, band, confidence = self.analyze(audio_data, language_code)
        
        # Get spectral features
        audio_data, _ = self._normalize_audio(audio_data)
        audio_hash = hash(audio_data.tobytes())
        spectral_data = self.spectral_cache.get_or_compute(
            audio_hash, self._compute_spectral_features, audio_data
        )
        
        # Calculate individual components
        snr, snr_conf = self._calculate_enhanced_snr(audio_data, spectral_data)
        spectral_clarity = self._calculate_spectral_clarity(spectral_data)
        articulation_index = self._calculate_articulation_index(spectral_data)
        is_whisper = self._detect_whisper_mode(spectral_data)
        
        return {
            'overall_score': score,
            'band': band,
            'confidence': confidence,
            'snr_db': snr,
            'snr_confidence': snr_conf,
            'snr_score': self._snr_to_score(snr),
            'spectral_clarity': spectral_clarity,
            'articulation_index': articulation_index,
            'spectral_centroid_hz': spectral_data['spectral_centroid'],
            'spectral_flatness': spectral_data['spectral_flatness'],
            'is_whisper_detected': is_whisper,
            'language_adjustment': self.language_adjustments.get(language_code, 1.0),
            'components': {
                'snr_weight': 0.3,
                'clarity_weight': 0.3,
                'articulation_weight': 0.4
            },
            'config': {
                'sample_rate': self.config.sample_rate,
                'fft_size': spectral_data['n_fft'],
                'reverb_compensation': self.config.reverb_compensation,
                'whisper_detection': self.config.whisper_mode_detection
            }
        }


# Convenience function for backwards compatibility
def create_analyzer(sample_rate: int = 48000, **kwargs) -> IntelligibilityAnalyzer:
    """Create an analyzer with custom configuration."""
    config = IntelligibilityConfig(sample_rate=sample_rate, **kwargs)
    return IntelligibilityAnalyzer(config)
