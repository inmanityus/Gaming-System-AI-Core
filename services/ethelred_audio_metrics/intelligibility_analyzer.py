"""
Intelligibility analyzer for audio segments.
Implements TAUD-07 (R-AUD-MET-001).
"""
import logging
from typing import Dict, Tuple, Optional
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq

logger = logging.getLogger(__name__)


class IntelligibilityAnalyzer:
    """
    Analyzes speech intelligibility using signal-to-noise ratio,
    spectral clarity, and articulation index methods.
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        
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
        self.band_weights = [0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05]
        
        # Thresholds for intelligibility bands
        self.thresholds = {
            'acceptable': 0.75,      # >75% intelligibility score
            'degraded': 0.50,        # 50-75% intelligibility
            'unacceptable': 0.0      # <50% intelligibility
        }
    
    def analyze(self, audio_data: np.ndarray) -> Tuple[float, str]:
        """
        Analyze audio intelligibility.
        Returns (score, band) where score is 0-1 and band is the classification.
        """
        if len(audio_data) == 0:
            return 0.0, 'unacceptable'
        
        # Normalize audio
        audio_data = self._normalize_audio(audio_data)
        
        # Calculate SNR
        snr = self._calculate_snr(audio_data)
        
        # Calculate spectral clarity
        spectral_clarity = self._calculate_spectral_clarity(audio_data)
        
        # Calculate articulation index
        articulation_index = self._calculate_articulation_index(audio_data)
        
        # Combine metrics (weighted average)
        score = (
            0.3 * self._snr_to_score(snr) +
            0.3 * spectral_clarity +
            0.4 * articulation_index
        )
        
        # Determine band
        if score >= self.thresholds['acceptable']:
            band = 'acceptable'
        elif score >= self.thresholds['degraded']:
            band = 'degraded'
        else:
            band = 'unacceptable'
        
        logger.info(f"Intelligibility analysis: score={score:.3f}, band={band}, "
                   f"SNR={snr:.1f}dB, clarity={spectral_clarity:.3f}, AI={articulation_index:.3f}")
        
        return score, band
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
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
    
    def get_detailed_analysis(self, audio_data: np.ndarray) -> Dict[str, any]:
        """
        Get detailed analysis results for debugging and fine-tuning.
        """
        audio_data = self._normalize_audio(audio_data)
        
        snr = self._calculate_snr(audio_data)
        spectral_clarity = self._calculate_spectral_clarity(audio_data)
        articulation_index = self._calculate_articulation_index(audio_data)
        
        score, band = self.analyze(audio_data)
        
        return {
            'overall_score': score,
            'band': band,
            'snr_db': snr,
            'snr_score': self._snr_to_score(snr),
            'spectral_clarity': spectral_clarity,
            'articulation_index': articulation_index,
            'components': {
                'snr_weight': 0.3,
                'clarity_weight': 0.3,
                'articulation_weight': 0.4
            }
        }
