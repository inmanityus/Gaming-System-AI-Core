"""
Archetype conformity analyzer for audio segments.
Implements TAUD-08 (R-AUD-MET-003).
"""
import logging
from typing import Dict, Tuple, Optional, List
import numpy as np
import json
from scipy import signal
import librosa

logger = logging.getLogger(__name__)


class ArchetypeProfile:
    """Voice profile for a character archetype."""
    
    def __init__(self, archetype_id: str, profile_data: Dict[str, any]):
        self.archetype_id = archetype_id
        self.f0_range = profile_data.get('f0_range', (80, 400))
        self.f0_mean = profile_data.get('f0_mean', 150)
        self.formant_targets = profile_data.get('formant_targets', {
            'F1': (600, 100),   # (mean, std)
            'F2': (1500, 200),
            'F3': (2500, 300)
        })
        self.roughness_range = profile_data.get('roughness_range', (0.0, 0.3))
        self.breathiness_range = profile_data.get('breathiness_range', (0.0, 0.2))
        self.spectral_tilt = profile_data.get('spectral_tilt', -6.0)  # dB/octave
        self.special_features = profile_data.get('special_features', [])


class ArchetypeConformityAnalyzer:
    """
    Analyzes how well audio conforms to character archetype voice profiles.
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.profiles = self._load_archetype_profiles()
        
        # Thresholds for conformity bands
        self.thresholds = {
            'on_profile': 0.75,      # >75% conformity
            'too_clean': 0.90,       # >90% (suspiciously perfect)
            'too_flat': 0.40,        # 40-60% (lacking character)
            'misaligned': 0.0        # <40% conformity
        }
    
    def _load_archetype_profiles(self) -> Dict[str, ArchetypeProfile]:
        """Load archetype voice profiles from configuration."""
        # In production, load from database or config file
        # For now, define some example profiles
        profiles = {
            'vampire_alpha': ArchetypeProfile('vampire_alpha', {
                'f0_range': (80, 150),
                'f0_mean': 110,
                'formant_targets': {
                    'F1': (500, 80),    # Darker vowels
                    'F2': (1200, 150),  # Back vowels
                    'F3': (2200, 200)
                },
                'roughness_range': (0.3, 0.6),  # Gravelly voice
                'breathiness_range': (0.1, 0.3),
                'spectral_tilt': -8.0,  # Darker tone
                'special_features': ['vocal_fry', 'low_resonance']
            }),
            
            'human_agent': ArchetypeProfile('human_agent', {
                'f0_range': (100, 200),
                'f0_mean': 140,
                'formant_targets': {
                    'F1': (600, 100),
                    'F2': (1500, 200),
                    'F3': (2500, 250)
                },
                'roughness_range': (0.0, 0.2),  # Clear voice
                'breathiness_range': (0.0, 0.1),
                'spectral_tilt': -5.0,  # Neutral
                'special_features': ['clear_articulation']
            }),
            
            'corpse_tender': ArchetypeProfile('corpse_tender', {
                'f0_range': (150, 300),
                'f0_mean': 200,
                'formant_targets': {
                    'F1': (700, 120),   # Higher, more nasal
                    'F2': (1800, 250),
                    'F3': (2800, 300)
                },
                'roughness_range': (0.2, 0.4),
                'breathiness_range': (0.3, 0.5),  # Whispery
                'spectral_tilt': -4.0,  # Brighter, thinner
                'special_features': ['whisper_quality', 'nasal_resonance']
            })
        }
        
        return profiles
    
    def analyze(self, audio_data: np.ndarray, archetype_id: str) -> Tuple[float, str]:
        """
        Analyze audio conformity to specified archetype.
        Returns (score, band) where score is 0-1 and band is the classification.
        """
        if archetype_id not in self.profiles:
            logger.warning(f"Unknown archetype: {archetype_id}")
            return 0.5, 'too_flat'
        
        if len(audio_data) == 0:
            return 0.0, 'misaligned'
        
        profile = self.profiles[archetype_id]
        audio_data = self._normalize_audio(audio_data)
        
        # Analyze various voice characteristics
        f0_score = self._analyze_f0_conformity(audio_data, profile)
        formant_score = self._analyze_formant_conformity(audio_data, profile)
        texture_score = self._analyze_texture_conformity(audio_data, profile)
        special_score = self._analyze_special_features(audio_data, profile)
        
        # Combine scores
        score = (
            0.3 * f0_score +
            0.3 * formant_score +
            0.2 * texture_score +
            0.2 * special_score
        )
        
        # Determine band
        if score >= self.thresholds['too_clean']:
            band = 'too_clean'  # Suspiciously perfect match
        elif score >= self.thresholds['on_profile']:
            band = 'on_profile'
        elif score >= self.thresholds['too_flat']:
            band = 'too_flat'
        else:
            band = 'misaligned'
        
        logger.info(f"Archetype conformity for {archetype_id}: score={score:.3f}, band={band}")
        
        return score, band
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
    def _analyze_f0_conformity(self, audio: np.ndarray, profile: ArchetypeProfile) -> float:
        """Analyze fundamental frequency conformity to profile."""
        try:
            # Extract pitch
            pitches, magnitudes = librosa.piptrack(
                y=audio.astype(np.float32),
                sr=self.sample_rate,
                hop_length=512,
                threshold=0.1
            )
            
            # Get valid pitch values
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                if magnitudes[index, t] > 0:
                    pitch = pitches[index, t]
                    if 50 <= pitch <= 500:  # Valid pitch range
                        pitch_values.append(pitch)
            
            if len(pitch_values) < 10:
                return 0.5  # Not enough data
            
            pitch_values = np.array(pitch_values)
            mean_f0 = np.mean(pitch_values)
            
            # Score based on how well F0 matches profile
            f0_deviation = abs(mean_f0 - profile.f0_mean) / profile.f0_mean
            f0_score = max(0, 1 - f0_deviation * 2)
            
            # Check if mostly within range
            in_range = np.sum(
                (pitch_values >= profile.f0_range[0]) & 
                (pitch_values <= profile.f0_range[1])
            ) / len(pitch_values)
            
            range_score = in_range
            
            return 0.6 * f0_score + 0.4 * range_score
            
        except Exception as e:
            logger.warning(f"F0 analysis failed: {e}")
            return 0.5
    
    def _analyze_formant_conformity(self, audio: np.ndarray, profile: ArchetypeProfile) -> float:
        """Analyze formant structure conformity to profile."""
        try:
            # Estimate formants using LPC
            # Pre-emphasis
            pre_emphasis = 0.97
            emphasized = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])
            
            # LPC analysis for formant estimation
            lpc_order = 16  # For formant analysis at 44.1kHz
            
            # Use autocorrelation method for stability
            correlations = np.correlate(emphasized, emphasized, mode='full')
            center = len(correlations) // 2
            autocorr = correlations[center:center + lpc_order + 1]
            
            # Levinson-Durbin recursion
            lpc_coeffs = self._levinson_durbin(autocorr, lpc_order)
            
            if lpc_coeffs is None:
                return 0.5
            
            # Find formant frequencies from LPC roots
            roots = np.roots(np.concatenate(([1], lpc_coeffs)))
            angles = np.angle(roots)
            
            # Convert to frequencies and filter
            formant_freqs = sorted(angles * self.sample_rate / (2 * np.pi))
            formant_freqs = [f for f in formant_freqs if 200 <= f <= 4000]
            
            if len(formant_freqs) < 3:
                return 0.5  # Not enough formants detected
            
            # Compare first 3 formants to profile
            formant_scores = []
            for i, (formant_name, (target_mean, target_std)) in enumerate(profile.formant_targets.items()):
                if i < len(formant_freqs):
                    observed = formant_freqs[i]
                    deviation = abs(observed - target_mean) / target_std
                    score = max(0, 1 - deviation / 3)  # 3 std devs = 0 score
                    formant_scores.append(score)
            
            return np.mean(formant_scores) if formant_scores else 0.5
            
        except Exception as e:
            logger.warning(f"Formant analysis failed: {e}")
            return 0.5
    
    def _levinson_durbin(self, autocorr: np.ndarray, order: int) -> Optional[np.ndarray]:
        """Levinson-Durbin recursion for LPC coefficient calculation."""
        try:
            # Initialize
            error = autocorr[0]
            lpc_coeffs = np.zeros(order)
            
            for i in range(order):
                if error <= 0:
                    return None
                
                # Calculate reflection coefficient
                lambda_val = 0
                for j in range(i):
                    lambda_val -= lpc_coeffs[j] * autocorr[i - j]
                lambda_val -= autocorr[i + 1]
                lambda_val /= error
                
                # Update coefficients
                lpc_coeffs[i] = lambda_val
                for j in range(i):
                    lpc_coeffs[j] += lambda_val * lpc_coeffs[i - 1 - j]
                
                # Update error
                error *= (1 - lambda_val ** 2)
            
            return lpc_coeffs
            
        except Exception:
            return None
    
    def _analyze_texture_conformity(self, audio: np.ndarray, profile: ArchetypeProfile) -> float:
        """Analyze voice texture (roughness, breathiness) conformity."""
        # Calculate roughness using amplitude modulation detection
        roughness_score = self._calculate_roughness_score(audio, profile)
        
        # Calculate breathiness using spectral features
        breathiness_score = self._calculate_breathiness_score(audio, profile)
        
        # Calculate spectral tilt
        tilt_score = self._calculate_spectral_tilt_score(audio, profile)
        
        return 0.4 * roughness_score + 0.3 * breathiness_score + 0.3 * tilt_score
    
    def _calculate_roughness_score(self, audio: np.ndarray, profile: ArchetypeProfile) -> float:
        """Calculate roughness/harshness score."""
        # Detect amplitude modulation in 20-150 Hz range (roughness perception)
        envelope = np.abs(signal.hilbert(audio))
        
        # Low-pass filter the envelope
        nyquist = self.sample_rate / 2
        cutoff = 150 / nyquist
        b, a = signal.butter(4, cutoff, btype='low')
        envelope_filtered = signal.filtfilt(b, a, envelope)
        
        # Calculate modulation depth
        if np.mean(envelope) > 0:
            modulation_depth = np.std(envelope_filtered) / np.mean(envelope)
        else:
            modulation_depth = 0
        
        # Normalize to 0-1 range (typical roughness values)
        roughness = min(modulation_depth * 5, 1.0)
        
        # Score based on how well it matches profile range
        if profile.roughness_range[0] <= roughness <= profile.roughness_range[1]:
            return 1.0
        elif roughness < profile.roughness_range[0]:
            return roughness / profile.roughness_range[0]
        else:
            excess = roughness - profile.roughness_range[1]
            return max(0, 1 - excess * 2)
    
    def _calculate_breathiness_score(self, audio: np.ndarray, profile: ArchetypeProfile) -> float:
        """Calculate breathiness score based on spectral characteristics."""
        # Calculate spectral features
        stft = librosa.stft(audio.astype(np.float32), n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        
        if magnitude.shape[1] < 2:
            return 0.5
        
        # Breathiness correlates with high-frequency noise
        freq_bins = librosa.fft_frequencies(sr=self.sample_rate, n_fft=2048)
        
        # Calculate energy ratio between high frequencies (>3kHz) and speech band (0.5-3kHz)
        high_freq_mask = freq_bins > 3000
        speech_band_mask = (freq_bins > 500) & (freq_bins <= 3000)
        
        high_freq_energy = np.mean(magnitude[high_freq_mask, :] ** 2)
        speech_band_energy = np.mean(magnitude[speech_band_mask, :] ** 2)
        
        if speech_band_energy > 0:
            breathiness = high_freq_energy / speech_band_energy
            breathiness = min(breathiness * 2, 1.0)  # Normalize
        else:
            breathiness = 0
        
        # Score based on profile match
        if profile.breathiness_range[0] <= breathiness <= profile.breathiness_range[1]:
            return 1.0
        elif breathiness < profile.breathiness_range[0]:
            return breathiness / profile.breathiness_range[0]
        else:
            excess = breathiness - profile.breathiness_range[1]
            return max(0, 1 - excess * 2)
    
    def _calculate_spectral_tilt_score(self, audio: np.ndarray, profile: ArchetypeProfile) -> float:
        """Calculate spectral tilt score."""
        # Calculate average spectrum
        stft = librosa.stft(audio.astype(np.float32), n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        avg_spectrum = np.mean(magnitude, axis=1)
        
        if len(avg_spectrum) < 10:
            return 0.5
        
        # Calculate spectral tilt in dB
        freq_bins = librosa.fft_frequencies(sr=self.sample_rate, n_fft=2048)
        
        # Use frequency range 200-4000 Hz
        mask = (freq_bins >= 200) & (freq_bins <= 4000)
        freqs = freq_bins[mask]
        spectrum_db = 20 * np.log10(avg_spectrum[mask] + 1e-10)
        
        if len(freqs) < 2:
            return 0.5
        
        # Fit linear regression to get tilt
        log_freqs = np.log10(freqs)
        coeffs = np.polyfit(log_freqs, spectrum_db, 1)
        tilt_db_per_octave = coeffs[0] * np.log10(2)  # Convert to dB/octave
        
        # Score based on how well tilt matches profile
        tilt_deviation = abs(tilt_db_per_octave - profile.spectral_tilt)
        tilt_score = max(0, 1 - tilt_deviation / 6)  # 6 dB deviation = 0 score
        
        return tilt_score
    
    def _analyze_special_features(self, audio: np.ndarray, profile: ArchetypeProfile) -> float:
        """Analyze special voice features specific to archetype."""
        if not profile.special_features:
            return 1.0  # No special features required
        
        feature_scores = []
        
        for feature in profile.special_features:
            if feature == 'vocal_fry':
                score = self._detect_vocal_fry(audio)
            elif feature == 'whisper_quality':
                score = self._detect_whisper_quality(audio)
            elif feature == 'nasal_resonance':
                score = self._detect_nasal_resonance(audio)
            elif feature == 'low_resonance':
                score = self._detect_low_resonance(audio)
            elif feature == 'clear_articulation':
                score = self._detect_clear_articulation(audio)
            else:
                score = 0.5  # Unknown feature
            
            feature_scores.append(score)
        
        return np.mean(feature_scores) if feature_scores else 1.0
    
    def _detect_vocal_fry(self, audio: np.ndarray) -> float:
        """Detect presence of vocal fry (creaky voice)."""
        # Vocal fry is characterized by low F0 and irregular glottal pulses
        pitches, magnitudes = librosa.piptrack(
            y=audio.astype(np.float32),
            sr=self.sample_rate,
            hop_length=256,  # Smaller hop for better resolution
            threshold=0.1
        )
        
        # Look for very low pitch values (< 80 Hz)
        fry_frames = 0
        total_voiced_frames = 0
        
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            if magnitudes[index, t] > 0:
                total_voiced_frames += 1
                pitch = pitches[index, t]
                if 30 <= pitch <= 80:  # Vocal fry range
                    fry_frames += 1
        
        if total_voiced_frames > 0:
            fry_ratio = fry_frames / total_voiced_frames
            return min(fry_ratio * 3, 1.0)  # Scale up as fry is typically intermittent
        
        return 0.0
    
    def _detect_whisper_quality(self, audio: np.ndarray) -> float:
        """Detect whisper-like quality in voice."""
        # Whisper has high breathiness and low harmonic-to-noise ratio
        # Already calculated in breathiness score, so use spectral flatness
        stft = librosa.stft(audio.astype(np.float32), n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        
        # Calculate spectral flatness
        flatness = librosa.feature.spectral_flatness(S=magnitude)[0]
        
        # Whisper has high spectral flatness (noise-like)
        mean_flatness = np.mean(flatness)
        
        # Map flatness to whisper score
        whisper_score = min(mean_flatness * 2, 1.0)
        
        return whisper_score
    
    def _detect_nasal_resonance(self, audio: np.ndarray) -> float:
        """Detect nasal resonance in voice."""
        # Nasal resonance shows up as anti-formants and specific spectral dips
        # Simplified: look for enhanced energy around 200-400 Hz
        stft = librosa.stft(audio.astype(np.float32), n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        
        freq_bins = librosa.fft_frequencies(sr=self.sample_rate, n_fft=2048)
        
        # Calculate energy in nasal band vs surrounding bands
        nasal_mask = (freq_bins >= 200) & (freq_bins <= 400)
        below_mask = (freq_bins >= 100) & (freq_bins < 200)
        above_mask = (freq_bins > 400) & (freq_bins <= 800)
        
        nasal_energy = np.mean(magnitude[nasal_mask, :])
        surrounding_energy = (np.mean(magnitude[below_mask, :]) + 
                            np.mean(magnitude[above_mask, :])) / 2
        
        if surrounding_energy > 0:
            nasal_prominence = nasal_energy / surrounding_energy
            # Nasal voice has prominence > 1.5
            return min((nasal_prominence - 1) * 2, 1.0)
        
        return 0.5
    
    def _detect_low_resonance(self, audio: np.ndarray) -> float:
        """Detect enhanced low frequency resonance."""
        # Look for strong energy in very low frequencies
        stft = librosa.stft(audio.astype(np.float32), n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        
        freq_bins = librosa.fft_frequencies(sr=self.sample_rate, n_fft=2048)
        
        # Calculate energy ratio
        low_mask = (freq_bins >= 50) & (freq_bins <= 200)
        mid_mask = (freq_bins >= 500) & (freq_bins <= 2000)
        
        low_energy = np.mean(magnitude[low_mask, :] ** 2)
        mid_energy = np.mean(magnitude[mid_mask, :] ** 2)
        
        if mid_energy > 0:
            low_prominence = low_energy / mid_energy
            # Strong low resonance has ratio > 0.5
            return min(low_prominence * 2, 1.0)
        
        return 0.5
    
    def _detect_clear_articulation(self, audio: np.ndarray) -> float:
        """Detect clear articulation (opposite of mumbling)."""
        # Clear articulation has distinct formant transitions and good SNR
        # Use spectral contrast as a proxy
        contrast = librosa.feature.spectral_contrast(
            y=audio.astype(np.float32),
            sr=self.sample_rate
        )
        
        # Higher contrast indicates clearer articulation
        mean_contrast = np.mean(contrast)
        
        # Map to score (typical range 20-40 dB)
        clarity_score = min((mean_contrast - 20) / 20, 1.0)
        clarity_score = max(0, clarity_score)
        
        return clarity_score
