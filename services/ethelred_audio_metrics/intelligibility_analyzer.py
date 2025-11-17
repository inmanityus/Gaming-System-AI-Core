"""
Intelligibility analyzer for audio segments.
Implements TAUD-07 (R-AUD-MET-001).
Enhanced for production use with horror game audio considerations.
"""
import logging
from typing import Dict, Tuple, Optional, List
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class IntelligibilityConfig:
    """Configuration for intelligibility analysis."""
    sample_rate: int = 48000  # Default to common game audio rate
    
    # VAD parameters (adaptive for horror game environments)
    vad_energy_percentile: float = 30.0
    vad_zero_crossing_threshold: float = 0.02
    
    # Frequency analysis
    min_fft_size: int = 512
    preferred_fft_size: int = 2048
    
    # Thresholds (can be overridden via environment)
    acceptable_threshold: float = float(os.getenv('INTELLIGIBILITY_ACCEPTABLE_THRESHOLD', '0.75'))
    degraded_threshold: float = float(os.getenv('INTELLIGIBILITY_DEGRADED_THRESHOLD', '0.50'))
    
    # Confidence parameters
    min_audio_duration_ms: float = 100.0
    min_frames_for_analysis: int = 5


class IntelligibilityAnalyzer:
    """
    Analyzes speech intelligibility using signal-to-noise ratio,
    spectral clarity, and articulation index methods.
    Enhanced for horror game audio with reverb and special effects.
    """
    
    def __init__(self, sample_rate: int = 48000, config: Optional[IntelligibilityConfig] = None):
        self.config = config or IntelligibilityConfig(sample_rate=sample_rate)
        self.sample_rate = self.config.sample_rate
        self._spectral_cache = {}  # Cache for FFT computations
        
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
        
        # Thresholds for intelligibility bands (from config)
        self.thresholds = {
            'acceptable': self.config.acceptable_threshold,
            'degraded': self.config.degraded_threshold,
            'unacceptable': 0.0
        }
    
    def analyze(self, audio_data: np.ndarray, return_confidence: bool = False) -> Tuple[float, str] | Tuple[float, str, float]:
        """
        Analyze audio intelligibility.
        Returns (score, band) where score is 0-1 and band is the classification.
        If return_confidence is True, also returns confidence score (0-1).
        """
        try:
            if audio_data is None or len(audio_data) == 0:
                return (0.0, 'unacceptable', 0.0) if return_confidence else (0.0, 'unacceptable')
            
            # Check minimum duration
            duration_ms = len(audio_data) / self.sample_rate * 1000
            if duration_ms < self.config.min_audio_duration_ms:
                logger.warning(f"Audio too short: {duration_ms:.1f}ms")
                return (0.0, 'unacceptable', 0.1) if return_confidence else (0.0, 'unacceptable')
        
            # Normalize audio and track normalization factor for confidence
            audio_data, norm_factor = self._normalize_audio_with_factor(audio_data)
            
            # Compute spectral features once and cache
            spectral_data = self._compute_spectral_features_cached(audio_data)
            
            # Calculate metrics using cached spectral data
            snr, snr_confidence = self._calculate_snr_with_confidence(audio_data)
            spectral_clarity = self._calculate_spectral_clarity_cached(spectral_data)
            articulation_index = self._calculate_articulation_index_cached(spectral_data)
            
            # Combine metrics (weighted average)
            score = (
                0.3 * self._snr_to_score(snr) +
                0.3 * spectral_clarity +
                0.4 * articulation_index
            )
            
            # Calculate confidence if requested
            confidence = 1.0
            if return_confidence:
                confidence = self._calculate_confidence(
                    snr_confidence, duration_ms, norm_factor
                )
        
            # Determine band
            if score >= self.thresholds['acceptable']:
                band = 'acceptable'
            elif score >= self.thresholds['degraded']:
                band = 'degraded'
            else:
                band = 'unacceptable'
            
            logger.info(f"Intelligibility analysis: score={score:.3f}, band={band}, "
                       f"SNR={snr:.1f}dB, clarity={spectral_clarity:.3f}, AI={articulation_index:.3f}, "
                       f"confidence={confidence:.3f}")
            
            return (score, band, confidence) if return_confidence else (score, band)
            
        except Exception as e:
            logger.error(f"Intelligibility analysis error: {e}")
            return (0.0, 'unacceptable', 0.0) if return_confidence else (0.0, 'unacceptable')
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
    def _normalize_audio_with_factor(self, audio: np.ndarray) -> Tuple[np.ndarray, float]:
        """Normalize audio to [-1, 1] range, return normalization factor."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val, max_val
        return audio, 1.0
    
    def _calculate_snr_with_confidence(self, audio: np.ndarray) -> Tuple[float, float]:
        """
        Calculate signal-to-noise ratio using voice activity detection.
        Returns (SNR in dB, confidence).
        """
        snr = self._calculate_snr(audio)
        # Simple confidence based on SNR value
        if snr < 0:
            confidence = 0.3
        elif snr > 30:
            confidence = 0.8
        else:
            confidence = 0.5 + (snr / 60)  # Linear scale 0.5 to 0.8
        return snr, confidence
    
    def _calculate_snr(self, audio: np.ndarray) -> float:
        """
        Calculate signal-to-noise ratio using voice activity detection.
        Returns SNR in dB.
        """
        # Simple VAD using energy threshold
        frame_size = int(0.02 * self.sample_rate)  # 20ms frames
        hop_size = frame_size // 2
        
        frames = []
        for i in range(0, len(audio) - frame_size, hop_size):
            frames.append(audio[i:i + frame_size])
        
        if not frames:
            return 0.0
        
        # Calculate energy per frame
        energies = [np.sum(frame ** 2) for frame in frames]
        energy_threshold = np.percentile(energies, 30)  # Bottom 30% assumed to be noise
        
        # Separate speech and noise frames
        speech_frames = [f for f, e in zip(frames, energies) if e > energy_threshold]
        noise_frames = [f for f, e in zip(frames, energies) if e <= energy_threshold]
        
        if not speech_frames or not noise_frames:
            return 20.0  # Default reasonable SNR if can't separate
        
        # Calculate power
        speech_power = np.mean([np.sum(f ** 2) for f in speech_frames])
        noise_power = np.mean([np.sum(f ** 2) for f in noise_frames])
        
        if noise_power > 0:
            snr_db = 10 * np.log10(speech_power / noise_power)
            return max(-10, min(40, snr_db))  # Clamp to reasonable range
        
        return 30.0  # High SNR if no noise detected
    
    def _snr_to_score(self, snr_db: float) -> float:
        """Convert SNR in dB to 0-1 score."""
        # Map SNR range [-10, 30] to [0, 1]
        return max(0, min(1, (snr_db + 10) / 40))
    
    def _calculate_spectral_clarity(self, audio: np.ndarray) -> float:
        """DEPRECATED: Use _calculate_spectral_clarity_cached instead."""
        spectral_data = self._compute_spectral_features_cached(audio)
        return self._calculate_spectral_clarity_cached(spectral_data)
    
    def _calculate_spectral_clarity_old(self, audio: np.ndarray) -> float:
        """
        Calculate spectral clarity based on formant structure visibility.
        """
        # Compute spectrogram
        nperseg = min(512, len(audio))
        if nperseg < 256:
            return 0.5  # Default for very short audio
            
        freqs, times, Sxx = signal.spectrogram(
            audio, 
            fs=self.sample_rate,
            nperseg=nperseg,
            noverlap=nperseg // 2
        )
        
        # Focus on speech frequency range (200-4000 Hz)
        speech_mask = (freqs >= 200) & (freqs <= 4000)
        speech_spectrum = Sxx[speech_mask, :]
        
        if speech_spectrum.size == 0:
            return 0.5
        
        # Calculate spectral contrast (peak to valley ratio)
        spectral_contrast_per_frame = []
        for frame in speech_spectrum.T:
            if np.max(frame) > 0:
                # Find peaks (formants) and valleys
                peaks = signal.find_peaks(frame, height=np.max(frame) * 0.3)[0]
                if len(peaks) >= 2:  # Need at least 2 formants
                    peak_mean = np.mean(frame[peaks])
                    valley_mean = np.mean(frame)
                    contrast = peak_mean / (valley_mean + 1e-10)
                    spectral_contrast_per_frame.append(min(contrast / 10, 1.0))
                else:
                    spectral_contrast_per_frame.append(0.3)
            else:
                spectral_contrast_per_frame.append(0.0)
        
        return np.mean(spectral_contrast_per_frame) if spectral_contrast_per_frame else 0.5
    
    def _calculate_articulation_index(self, audio: np.ndarray) -> float:
        """DEPRECATED: Use _calculate_articulation_index_cached instead."""
        spectral_data = self._compute_spectral_features_cached(audio)
        return self._calculate_articulation_index_cached(spectral_data)
    
    def _calculate_articulation_index_old(self, audio: np.ndarray) -> float:
        """
        Calculate Articulation Index based on band importance weighting.
        """
        # Calculate FFT
        n_fft = min(2048, len(audio))
        if n_fft < 512:
            return 0.5  # Default for very short audio
            
        fft_vals = rfft(audio, n=n_fft)
        fft_freqs = rfftfreq(n_fft, 1/self.sample_rate)
        magnitude = np.abs(fft_vals)
        
        # Calculate energy in each speech band
        band_scores = []
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        for (low_freq, high_freq), weight in zip(self.speech_bands, self.band_weights):
            # Find indices for frequency band
            band_mask = (fft_freqs >= low_freq) & (fft_freqs <= high_freq)
            band_energy = np.sum(magnitude[band_mask] ** 2)
            
            # Calculate relative energy (normalized by total)
            relative_energy = band_energy / total_energy
            
            # Expected relative energy for this band (based on typical speech)
            expected_energy = weight * 0.8  # 80% of weight as expected
            
            # Score based on how close we are to expected
            if expected_energy > 0:
                band_score = min(relative_energy / expected_energy, 1.0)
            else:
                band_score = 0.0
            
            band_scores.append(band_score * weight)
        
        # Sum weighted band scores
        articulation_index = sum(band_scores) / sum(self.band_weights)
        
        return articulation_index
    
    def _compute_spectral_features_cached(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute spectral features once and cache them."""
        audio_hash = hash(audio.tobytes())
        
        if audio_hash in self._spectral_cache:
            return self._spectral_cache[audio_hash]
        
        # Calculate appropriate FFT size
        n_fft = min(self.config.preferred_fft_size, 
                   max(self.config.min_fft_size, len(audio)))
        if n_fft < self.config.min_fft_size:
            n_fft = self.config.min_fft_size
        
        # Compute FFT
        fft_vals = rfft(audio, n=n_fft)
        fft_freqs = rfftfreq(n_fft, 1/self.sample_rate)
        magnitude = np.abs(fft_vals)
        
        # Compute spectrogram
        nperseg = min(512, len(audio))
        if nperseg >= 256:
            freqs, times, Sxx = signal.spectrogram(
                audio, 
                fs=self.sample_rate,
                nperseg=nperseg,
                noverlap=nperseg // 2,
                window='hann'
            )
        else:
            # For very short audio, create minimal spectrogram
            freqs = fft_freqs[:10]
            times = np.array([0])
            Sxx = magnitude[:10].reshape(-1, 1)
        
        spectral_data = {
            'fft_magnitude': magnitude,
            'fft_freqs': fft_freqs,
            'spectrogram': Sxx,
            'spec_freqs': freqs,
            'spec_times': times,
            'n_fft': n_fft
        }
        
        # Cache the results
        self._spectral_cache[audio_hash] = spectral_data
        
        return spectral_data
    
    def _calculate_spectral_clarity_cached(self, spectral_data: Dict[str, np.ndarray]) -> float:
        """Calculate spectral clarity using cached spectral data."""
        Sxx = spectral_data['spectrogram']
        freqs = spectral_data['spec_freqs']
        
        # Focus on speech frequency range (200-4000 Hz)
        speech_mask = (freqs >= 200) & (freqs <= 4000)
        speech_spectrum = Sxx[speech_mask, :]
        
        if speech_spectrum.size == 0:
            return 0.5
        
        # Calculate spectral contrast (peak to valley ratio)
        spectral_contrast_per_frame = []
        for frame in speech_spectrum.T:
            frame_max = np.max(frame)
            if frame_max > 1e-10:
                # Find peaks (formants) and valleys
                peaks = signal.find_peaks(frame, height=frame_max * 0.3)[0]
                if len(peaks) >= 2:  # Need at least 2 formants
                    peak_mean = np.mean(frame[peaks])
                    valley_mean = np.mean(frame)
                    contrast = peak_mean / (valley_mean + 1e-10)
                    spectral_contrast_per_frame.append(min(contrast / 10, 1.0))
                else:
                    spectral_contrast_per_frame.append(0.3)
            else:
                spectral_contrast_per_frame.append(0.0)
        
        return np.mean(spectral_contrast_per_frame) if spectral_contrast_per_frame else 0.5
    
    def _calculate_articulation_index_cached(self, spectral_data: Dict[str, np.ndarray]) -> float:
        """Calculate Articulation Index using cached spectral data."""
        magnitude = spectral_data['fft_magnitude']
        fft_freqs = spectral_data['fft_freqs']
        
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
            
            # Expected relative energy for this band (based on typical speech)
            expected_energy = weight * 0.8  # 80% of weight as expected
            
            # Score based on how close we are to expected
            if expected_energy > 0:
                band_score = min(relative_energy / expected_energy, 1.0)
            else:
                band_score = 0.0
            
            band_scores.append(band_score * weight)
        
        # Sum weighted band scores
        articulation_index = np.sum(band_scores) / np.sum(self.band_weights)
        
        return articulation_index
    
    def _calculate_confidence(self, snr_confidence: float, duration_ms: float, 
                            norm_factor: float) -> float:
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
        
        # Combined confidence (geometric mean for balanced result)
        if confidence_factors:
            confidence = np.power(np.prod(confidence_factors), 1/len(confidence_factors))
        else:
            confidence = 0.5
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    def get_detailed_analysis(self, audio_data: np.ndarray) -> Dict[str, any]:
        """
        Get detailed analysis results for debugging and fine-tuning.
        """
        # Clear cache for fresh analysis
        self._spectral_cache.clear()
        
        audio_data, norm_factor = self._normalize_audio_with_factor(audio_data)
        
        snr, snr_confidence = self._calculate_snr_with_confidence(audio_data)
        spectral_data = self._compute_spectral_features_cached(audio_data)
        spectral_clarity = self._calculate_spectral_clarity_cached(spectral_data)
        articulation_index = self._calculate_articulation_index_cached(spectral_data)
        
        score, band, confidence = self.analyze(audio_data, return_confidence=True)
        
        return {
            'overall_score': score,
            'band': band,
            'confidence': confidence,
            'snr_db': snr,
            'snr_confidence': snr_confidence,
            'snr_score': self._snr_to_score(snr),
            'spectral_clarity': spectral_clarity,
            'articulation_index': articulation_index,
            'components': {
                'snr_weight': 0.3,
                'clarity_weight': 0.3,
                'articulation_weight': 0.4
            },
            'config': {
                'sample_rate': self.sample_rate,
                'acceptable_threshold': self.config.acceptable_threshold,
                'degraded_threshold': self.config.degraded_threshold
            }
        }

