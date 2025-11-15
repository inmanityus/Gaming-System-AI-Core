"""
Simulator stability analyzer for audio segments.
Implements TAUD-08 (R-AUD-MET-004).
"""
import logging
from typing import Dict, Tuple, Optional, List
import numpy as np
from scipy import signal
from scipy.stats import kurtosis, skew

logger = logging.getLogger(__name__)


class SimulatorStabilityAnalyzer:
    """
    Analyzes vocal cord simulator stability and artifacts.
    Detects glitches, instabilities, and processing errors.
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        
        # Thresholds for stability bands
        self.thresholds = {
            'stable': 0.80,      # >80% stability score
            'unstable': 0.0      # <=80% stability score
        }
        
        # Detection parameters
        self.glitch_threshold = 3.0  # Standard deviations
        self.dc_offset_threshold = 0.01  # Maximum allowed DC offset
        self.clipping_threshold = 0.99  # Sample value threshold
        self.noise_floor_db = -60  # Expected noise floor
    
    def analyze(self, audio_data: np.ndarray, simulator_metadata: Optional[Dict] = None) -> Tuple[float, str]:
        """
        Analyze simulator stability.
        Returns (score, band) where score is 0-1 and band is the classification.
        """
        if len(audio_data) == 0:
            return 0.0, 'unstable'
        
        # Normalize for analysis
        audio_data = self._normalize_audio(audio_data)
        
        # Run various stability checks
        glitch_score = self._detect_glitches(audio_data)
        artifact_score = self._detect_processing_artifacts(audio_data)
        continuity_score = self._check_signal_continuity(audio_data)
        quality_score = self._check_signal_quality(audio_data)
        
        # If simulator metadata available, check parameters
        if simulator_metadata:
            param_score = self._check_simulator_parameters(simulator_metadata)
        else:
            param_score = 1.0  # Assume stable if no metadata
        
        # Combine scores
        score = (
            0.3 * glitch_score +
            0.2 * artifact_score +
            0.2 * continuity_score +
            0.2 * quality_score +
            0.1 * param_score
        )
        
        # Determine band
        if score >= self.thresholds['stable']:
            band = 'stable'
        else:
            band = 'unstable'
        
        logger.info(f"Simulator stability: score={score:.3f}, band={band}")
        
        return score, band
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
    def _detect_glitches(self, audio: np.ndarray) -> float:
        """
        Detect audio glitches and discontinuities.
        """
        # Calculate first-order difference
        diff = np.diff(audio)
        
        # Detect outliers using statistical approach
        mean_diff = np.mean(np.abs(diff))
        std_diff = np.std(diff)
        
        if std_diff == 0:
            return 0.0  # Flat signal, definitely unstable
        
        # Find samples that deviate significantly
        glitch_mask = np.abs(diff - np.mean(diff)) > self.glitch_threshold * std_diff
        glitch_ratio = np.sum(glitch_mask) / len(diff)
        
        # Also check for sudden amplitude jumps
        amplitude_envelope = np.abs(signal.hilbert(audio))
        envelope_diff = np.diff(amplitude_envelope)
        
        if len(envelope_diff) > 0:
            envelope_jumps = np.sum(np.abs(envelope_diff) > 0.5) / len(envelope_diff)
        else:
            envelope_jumps = 0
        
        # Score based on glitch presence
        glitch_score = max(0, 1 - glitch_ratio * 100 - envelope_jumps * 10)
        
        return glitch_score
    
    def _detect_processing_artifacts(self, audio: np.ndarray) -> float:
        """
        Detect common digital processing artifacts.
        """
        artifact_scores = []
        
        # Check for clipping
        clipping_ratio = np.sum(np.abs(audio) >= self.clipping_threshold) / len(audio)
        clipping_score = max(0, 1 - clipping_ratio * 50)
        artifact_scores.append(clipping_score)
        
        # Check for DC offset
        dc_offset = np.mean(audio)
        dc_score = max(0, 1 - abs(dc_offset) / self.dc_offset_threshold)
        artifact_scores.append(dc_score)
        
        # Check for quantization noise (stair-stepping)
        # Look at the distribution of sample values
        unique_values = len(np.unique(audio))
        expected_unique = min(len(audio) // 10, 1000)  # Expect variety in samples
        
        if unique_values < expected_unique:
            quantization_score = unique_values / expected_unique
        else:
            quantization_score = 1.0
        artifact_scores.append(quantization_score)
        
        # Check for aliasing (energy above Nyquist)
        fft_vals = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), 1/self.sample_rate)
        
        # Check energy near Nyquist frequency
        nyquist = self.sample_rate / 2
        high_freq_mask = freqs > nyquist * 0.9
        
        if np.sum(high_freq_mask) > 0:
            high_freq_energy = np.sum(np.abs(fft_vals[high_freq_mask]) ** 2)
            total_energy = np.sum(np.abs(fft_vals) ** 2)
            
            if total_energy > 0:
                aliasing_ratio = high_freq_energy / total_energy
                aliasing_score = max(0, 1 - aliasing_ratio * 10)
            else:
                aliasing_score = 0
        else:
            aliasing_score = 1.0
        artifact_scores.append(aliasing_score)
        
        return np.mean(artifact_scores)
    
    def _check_signal_continuity(self, audio: np.ndarray) -> float:
        """
        Check for signal continuity and phase coherence.
        """
        # Use phase analysis to detect discontinuities
        analytic_signal = signal.hilbert(audio)
        instantaneous_phase = np.unwrap(np.angle(analytic_signal))
        
        # Check for phase jumps
        phase_diff = np.diff(instantaneous_phase)
        
        # Remove expected phase progression
        expected_phase_diff = np.median(phase_diff)
        phase_anomalies = phase_diff - expected_phase_diff
        
        # Detect large phase jumps
        phase_jump_threshold = np.pi  # 180 degrees
        phase_jumps = np.sum(np.abs(phase_anomalies) > phase_jump_threshold)
        phase_jump_ratio = phase_jumps / len(phase_diff) if len(phase_diff) > 0 else 0
        
        # Check zero-crossing rate consistency
        zero_crossings = np.where(np.diff(np.signbit(audio)))[0]
        
        if len(zero_crossings) > 1:
            zcr_intervals = np.diff(zero_crossings)
            zcr_variance = np.var(zcr_intervals)
            zcr_mean = np.mean(zcr_intervals)
            
            if zcr_mean > 0:
                zcr_cv = np.sqrt(zcr_variance) / zcr_mean
                # Natural speech has some ZCR variation, but not extreme
                if zcr_cv < 2.0:
                    zcr_score = 1.0
                else:
                    zcr_score = max(0, 1 - (zcr_cv - 2.0) / 3)
            else:
                zcr_score = 0
        else:
            zcr_score = 0.5
        
        # Combine continuity metrics
        continuity_score = 0.6 * (1 - phase_jump_ratio * 10) + 0.4 * zcr_score
        
        return max(0, continuity_score)
    
    def _check_signal_quality(self, audio: np.ndarray) -> float:
        """
        Check overall signal quality metrics.
        """
        quality_scores = []
        
        # Check dynamic range
        if len(audio) > 0:
            # Use percentiles to avoid outlier influence
            p95 = np.percentile(np.abs(audio), 95)
            p5 = np.percentile(np.abs(audio), 5)
            
            if p5 > 0:
                dynamic_range_db = 20 * np.log10(p95 / p5)
                # Good dynamic range is 20-60 dB
                if 20 <= dynamic_range_db <= 60:
                    dr_score = 1.0
                elif dynamic_range_db < 20:
                    dr_score = dynamic_range_db / 20
                else:
                    dr_score = max(0, 1 - (dynamic_range_db - 60) / 40)
            else:
                dr_score = 0.5
        else:
            dr_score = 0
        quality_scores.append(dr_score)
        
        # Check for silence or near-silence
        rms = np.sqrt(np.mean(audio ** 2))
        silence_threshold = 10 ** (self.noise_floor_db / 20)
        
        if rms > silence_threshold:
            silence_score = 1.0
        else:
            silence_score = rms / silence_threshold
        quality_scores.append(silence_score)
        
        # Check statistical properties (should be somewhat Gaussian for speech)
        kurt = kurtosis(audio)
        skewness = abs(skew(audio))
        
        # Speech typically has kurtosis around 3-6
        if 2 <= kurt <= 8:
            kurt_score = 1.0
        elif kurt < 2:
            kurt_score = kurt / 2
        else:
            kurt_score = max(0, 1 - (kurt - 8) / 10)
        quality_scores.append(kurt_score)
        
        # Skewness should be near 0 for good audio
        skew_score = max(0, 1 - skewness)
        quality_scores.append(skew_score)
        
        return np.mean(quality_scores)
    
    def _check_simulator_parameters(self, metadata: Dict) -> float:
        """
        Check simulator parameters for stability issues.
        """
        param_scores = []
        
        # Check glottal parameters
        if 'glottal_tension' in metadata:
            tension = metadata['glottal_tension']
            # Extreme values can cause instability
            if 0.1 <= tension <= 0.9:
                param_scores.append(1.0)
            else:
                param_scores.append(0.5)
        
        if 'vocal_tract_length' in metadata:
            vtl = metadata['vocal_tract_length']
            # Normal range is 0.8 to 1.2 (relative to average)
            if 0.7 <= vtl <= 1.3:
                param_scores.append(1.0)
            else:
                param_scores.append(0.5)
        
        # Check for parameter discontinuities
        if 'parameter_history' in metadata:
            history = metadata['parameter_history']
            if len(history) > 1:
                # Check for sudden parameter jumps
                param_changes = []
                for param_name in history[0].keys():
                    values = [h.get(param_name, 0) for h in history]
                    if len(values) > 1:
                        max_change = np.max(np.abs(np.diff(values)))
                        param_changes.append(max_change)
                
                if param_changes:
                    avg_change = np.mean(param_changes)
                    # Penalize large parameter jumps
                    stability_score = max(0, 1 - avg_change * 2)
                    param_scores.append(stability_score)
        
        # Check simulator state
        if 'error_count' in metadata:
            errors = metadata['error_count']
            if errors == 0:
                param_scores.append(1.0)
            else:
                param_scores.append(max(0, 1 - errors / 10))
        
        return np.mean(param_scores) if param_scores else 1.0
    
    def get_detailed_analysis(self, audio_data: np.ndarray, simulator_metadata: Optional[Dict] = None) -> Dict[str, any]:
        """
        Get detailed stability analysis for debugging.
        """
        audio_data = self._normalize_audio(audio_data)
        
        glitch_score = self._detect_glitches(audio_data)
        artifact_score = self._detect_processing_artifacts(audio_data)
        continuity_score = self._check_signal_continuity(audio_data)
        quality_score = self._check_signal_quality(audio_data)
        param_score = self._check_simulator_parameters(simulator_metadata) if simulator_metadata else 1.0
        
        score, band = self.analyze(audio_data, simulator_metadata)
        
        # Additional detailed metrics
        diff = np.diff(audio_data)
        
        return {
            'overall_score': score,
            'band': band,
            'component_scores': {
                'glitch_detection': glitch_score,
                'artifact_detection': artifact_score,
                'signal_continuity': continuity_score,
                'signal_quality': quality_score,
                'parameter_stability': param_score
            },
            'detailed_metrics': {
                'max_sample_value': float(np.max(np.abs(audio_data))),
                'dc_offset': float(np.mean(audio_data)),
                'clipping_ratio': float(np.sum(np.abs(audio_data) >= self.clipping_threshold) / len(audio_data)),
                'unique_values': int(len(np.unique(audio_data))),
                'max_diff': float(np.max(np.abs(diff))) if len(diff) > 0 else 0,
                'rms_level': float(np.sqrt(np.mean(audio_data ** 2))),
                'kurtosis': float(kurtosis(audio_data)),
                'skewness': float(skew(audio_data))
            }
        }
