"""
Naturalness analyzer for audio segments.
Implements TAUD-07 (R-AUD-MET-002).
"""
import logging
from typing import Dict, Tuple, Optional
import numpy as np
from scipy import signal
from scipy.stats import entropy
import librosa

logger = logging.getLogger(__name__)


class NaturalnessAnalyzer:
    """
    Analyzes speech naturalness using prosody features,
    pitch variations, and rhythm patterns.
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        
        # Natural speech characteristics
        self.natural_f0_range = (80, 400)  # Hz, typical human pitch range
        self.natural_f0_variation = (0.1, 0.4)  # Coefficient of variation
        
        # Thresholds for naturalness bands
        self.thresholds = {
            'ok': 0.70,           # >70% naturalness score
            'robotic': 0.40,      # 40-70% naturalness
            'monotone': 0.0       # <40% naturalness
        }
    
    def analyze(self, audio_data: np.ndarray) -> Tuple[float, str]:
        """
        Analyze audio naturalness.
        Returns (score, band) where score is 0-1 and band is the classification.
        """
        if len(audio_data) == 0:
            return 0.0, 'monotone'
        
        # Normalize audio
        audio_data = self._normalize_audio(audio_data)
        
        # Extract prosody features
        pitch_score = self._analyze_pitch_variation(audio_data)
        rhythm_score = self._analyze_rhythm_patterns(audio_data)
        spectral_score = self._analyze_spectral_dynamics(audio_data)
        
        # Combine metrics
        score = (
            0.4 * pitch_score +      # Pitch variation is key to naturalness
            0.3 * rhythm_score +     # Natural rhythm patterns
            0.3 * spectral_score     # Spectral dynamics
        )
        
        # Determine band
        if score >= self.thresholds['ok']:
            band = 'ok'
        elif score >= self.thresholds['robotic']:
            band = 'robotic'
        else:
            band = 'monotone'
        
        logger.info(f"Naturalness analysis: score={score:.3f}, band={band}, "
                   f"pitch={pitch_score:.3f}, rhythm={rhythm_score:.3f}, spectral={spectral_score:.3f}")
        
        return score, band
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
    def _analyze_pitch_variation(self, audio: np.ndarray) -> float:
        """
        Analyze pitch (F0) variation patterns.
        Natural speech has moderate pitch variation, not too flat or extreme.
        """
        try:
            # Extract pitch using autocorrelation method
            # For better accuracy, use librosa's piptrack or other advanced methods
            pitches, magnitudes = librosa.piptrack(
                y=audio.astype(np.float32),
                sr=self.sample_rate,
                hop_length=512,
                threshold=0.1
            )
            
            # Get pitch values where magnitude is significant
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                if magnitudes[index, t] > 0:
                    pitch = pitches[index, t]
                    if self.natural_f0_range[0] <= pitch <= self.natural_f0_range[1]:
                        pitch_values.append(pitch)
            
            if len(pitch_values) < 10:  # Not enough voiced segments
                return 0.3  # Low score for unvoiced/whispered speech
            
            pitch_values = np.array(pitch_values)
            
            # Calculate coefficient of variation
            mean_pitch = np.mean(pitch_values)
            std_pitch = np.std(pitch_values)
            
            if mean_pitch > 0:
                cv = std_pitch / mean_pitch
                
                # Score based on how well CV matches natural range
                if self.natural_f0_variation[0] <= cv <= self.natural_f0_variation[1]:
                    # Perfect range
                    variation_score = 1.0
                elif cv < self.natural_f0_variation[0]:
                    # Too monotone
                    variation_score = cv / self.natural_f0_variation[0]
                else:
                    # Too variable (unnatural)
                    excess = cv - self.natural_f0_variation[1]
                    variation_score = max(0.3, 1.0 - excess * 2)
            else:
                variation_score = 0.0
            
            # Check for pitch contours (natural rises and falls)
            contour_score = self._analyze_pitch_contours(pitch_values)
            
            return 0.7 * variation_score + 0.3 * contour_score
            
        except Exception as e:
            logger.warning(f"Pitch analysis failed: {e}")
            return 0.5  # Default middle score on error
    
    def _analyze_pitch_contours(self, pitch_values: np.ndarray) -> float:
        """Analyze naturalness of pitch contours."""
        if len(pitch_values) < 5:
            return 0.5
        
        # Calculate pitch differences
        pitch_diffs = np.diff(pitch_values)
        
        # Count direction changes (peaks and valleys)
        direction_changes = 0
        for i in range(1, len(pitch_diffs)):
            if pitch_diffs[i-1] * pitch_diffs[i] < 0:  # Sign change
                direction_changes += 1
        
        # Natural speech has moderate direction changes
        # Too few = monotone, too many = unnatural
        changes_per_second = direction_changes / (len(pitch_values) / 50)  # Assuming ~50 frames/sec
        
        if 2 <= changes_per_second <= 8:  # Natural range
            return 1.0
        elif changes_per_second < 2:
            return changes_per_second / 2
        else:
            return max(0.3, 1.0 - (changes_per_second - 8) / 10)
    
    def _analyze_rhythm_patterns(self, audio: np.ndarray) -> float:
        """
        Analyze speech rhythm and timing patterns.
        Natural speech has irregular but structured rhythm.
        """
        # Detect onset events (speech bursts)
        onset_envelope = librosa.onset.onset_strength(
            y=audio.astype(np.float32),
            sr=self.sample_rate,
            hop_length=512
        )
        
        # Find peaks in onset strength
        peaks = signal.find_peaks(onset_envelope, height=np.max(onset_envelope) * 0.3)[0]
        
        if len(peaks) < 3:
            return 0.5  # Not enough rhythm events
        
        # Calculate inter-onset intervals
        ioi = np.diff(peaks) * 512 / self.sample_rate  # Convert to seconds
        
        if len(ioi) == 0:
            return 0.5
        
        # Natural speech has moderate variability in timing
        # Too regular = robotic, too irregular = unnatural
        ioi_cv = np.std(ioi) / (np.mean(ioi) + 1e-10)
        
        # Score based on IOI variability
        if 0.3 <= ioi_cv <= 0.7:  # Natural range
            rhythm_score = 1.0
        elif ioi_cv < 0.3:  # Too regular (robotic)
            rhythm_score = ioi_cv / 0.3
        else:  # Too irregular
            rhythm_score = max(0.4, 1.0 - (ioi_cv - 0.7))
        
        # Check for natural pauses
        pause_score = self._analyze_pauses(ioi)
        
        return 0.6 * rhythm_score + 0.4 * pause_score
    
    def _analyze_pauses(self, inter_onset_intervals: np.ndarray) -> float:
        """Analyze naturalness of pause patterns."""
        if len(inter_onset_intervals) == 0:
            return 0.5
        
        # Natural speech has occasional longer pauses
        mean_ioi = np.mean(inter_onset_intervals)
        long_pauses = inter_onset_intervals > mean_ioi * 2
        pause_ratio = np.sum(long_pauses) / len(inter_onset_intervals)
        
        # Natural pause ratio is around 10-20%
        if 0.1 <= pause_ratio <= 0.2:
            return 1.0
        elif pause_ratio < 0.1:
            return 0.5 + pause_ratio * 5  # Too few pauses
        else:
            return max(0.3, 1.0 - (pause_ratio - 0.2) * 2)  # Too many pauses
    
    def _analyze_spectral_dynamics(self, audio: np.ndarray) -> float:
        """
        Analyze spectral dynamics over time.
        Natural speech has varying spectral characteristics.
        """
        # Compute spectral features over time
        hop_length = 512
        n_mfcc = 13
        
        try:
            # Extract MFCCs
            mfccs = librosa.feature.mfcc(
                y=audio.astype(np.float32),
                sr=self.sample_rate,
                n_mfcc=n_mfcc,
                hop_length=hop_length
            )
            
            if mfccs.shape[1] < 10:
                return 0.5  # Too short for analysis
            
            # Calculate temporal variation in spectral features
            mfcc_deltas = librosa.feature.delta(mfccs)
            
            # Measure spectral flux (change over time)
            spectral_flux = np.mean(np.abs(mfcc_deltas), axis=0)
            mean_flux = np.mean(spectral_flux)
            
            # Natural speech has moderate spectral flux
            # Too low = monotone/synthetic, too high = unnatural
            if 0.1 <= mean_flux <= 0.5:
                flux_score = 1.0
            elif mean_flux < 0.1:
                flux_score = mean_flux / 0.1
            else:
                flux_score = max(0.3, 1.0 - (mean_flux - 0.5) * 2)
            
            # Check spectral centroid variation
            spectral_centroid = librosa.feature.spectral_centroid(
                y=audio.astype(np.float32),
                sr=self.sample_rate,
                hop_length=hop_length
            )[0]
            
            if len(spectral_centroid) > 1:
                centroid_cv = np.std(spectral_centroid) / (np.mean(spectral_centroid) + 1e-10)
                
                # Natural range for centroid variation
                if 0.1 <= centroid_cv <= 0.3:
                    centroid_score = 1.0
                elif centroid_cv < 0.1:
                    centroid_score = centroid_cv / 0.1
                else:
                    centroid_score = max(0.4, 1.0 - (centroid_cv - 0.3) * 3)
            else:
                centroid_score = 0.5
            
            return 0.6 * flux_score + 0.4 * centroid_score
            
        except Exception as e:
            logger.warning(f"Spectral dynamics analysis failed: {e}")
            return 0.5
    
    def get_detailed_analysis(self, audio_data: np.ndarray) -> Dict[str, any]:
        """
        Get detailed analysis results for debugging and fine-tuning.
        """
        audio_data = self._normalize_audio(audio_data)
        
        pitch_score = self._analyze_pitch_variation(audio_data)
        rhythm_score = self._analyze_rhythm_patterns(audio_data)
        spectral_score = self._analyze_spectral_dynamics(audio_data)
        
        score, band = self.analyze(audio_data)
        
        return {
            'overall_score': score,
            'band': band,
            'pitch_variation_score': pitch_score,
            'rhythm_pattern_score': rhythm_score,
            'spectral_dynamics_score': spectral_score,
            'components': {
                'pitch_weight': 0.4,
                'rhythm_weight': 0.3,
                'spectral_weight': 0.3
            }
        }

