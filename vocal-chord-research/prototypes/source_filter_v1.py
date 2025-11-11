"""
Vocal Tract Synthesis - Pure Source-Filter Approach (Prototype v1)

Implementation of articulatory speech synthesis using:
- Liljencrants-Fant (LF) Glottal Model for voice source
- Cascade formant filtering with biquad filters
- Physical parameters for vocal tract modeling

This is a proof-of-concept to test the viability of physics-based
vocal synthesis for game audio (1000+ concurrent NPCs).

Author: Claude Sonnet 4.5 (Primary)
Peer Review: Pending GPT-Codex-2
Date: 2025-11-09
"""

import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
from dataclasses import dataclass
from typing import List, Tuple
import matplotlib.pyplot as plt


@dataclass
class VocalTractParams:
    """Physical parameters defining vocal tract characteristics"""
    
    # Glottal source parameters
    f0: float = 120.0  # Fundamental frequency (Hz) - pitch
    open_quotient: float = 0.7  # Glottal open quotient (0-1)
    speed_quotient: float = 1.0  # Speed quotient (asymmetry)
    tenseness: float = 0.5  # Vocal fold tension (0-1)
    
    # Vocal tract parameters
    tract_length: float = 17.5  # Length in cm (male ~17.5, female ~14.5)
    breathiness: float = 0.05  # Aspiration noise level (0-1)
    
    # Formant frequencies (Hz) - for vowel /a/
    f1: float = 800.0  # First formant
    f2: float = 1200.0  # Second formant
    f3: float = 2500.0  # Third formant
    f4: float = 3500.0  # Fourth formant
    
    # Formant bandwidths (Hz)
    bw1: float = 80.0
    bw2: float = 90.0
    bw3: float = 120.0
    bw4: float = 200.0
    
    # Emotion/state modifiers (0-1)
    arousal: float = 0.5  # Affects pressure, F0, tenseness
    valence: float = 0.5  # Affects prosody, spectral tilt
    dominance: float = 0.5  # Affects tension, F0 variance


class LFGlottalModel:
    """
    Liljencrants-Fant (LF) glottal source model
    
    Generates glottal flow derivative waveform based on physical
    parameters of vocal fold vibration.
    """
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        
    def generate_pulse(
        self, 
        f0: float, 
        oq: float, 
        sq: float, 
        te_ratio: float = 0.4
    ) -> np.ndarray:
        """
        Generate one glottal pulse using LF model
        
        Args:
            f0: Fundamental frequency (Hz)
            oq: Open quotient (0-1)
            sq: Speed quotient (asymmetry, usually ~1.0)
            te_ratio: Ratio of excitation time to period
            
        Returns:
            Glottal flow derivative waveform for one period
        """
        T0 = 1.0 / f0  # Period in seconds
        samples_per_period = int(self.sample_rate * T0)
        t = np.linspace(0, T0, samples_per_period, endpoint=False)
        
        # LF model time points
        Te = te_ratio * T0  # Excitation time
        Tp = Te / sq  # Time of peak
        Ta = oq * T0  # Open time
        
        # Compute waveform parameters
        epsilon = 1 / Ta
        omega_g = np.pi / Tp
        
        # Generate waveform
        waveform = np.zeros_like(t)
        
        # Open phase (0 to Te)
        open_mask = t <= Te
        waveform[open_mask] = np.exp(-epsilon * t[open_mask]) * np.sin(omega_g * t[open_mask])
        
        # Return phase (Te to Ta) - exponential decay
        if Ta > Te:
            return_mask = (t > Te) & (t <= Ta)
            t_return = t[return_mask] - Te
            
            # Return phase amplitude matching
            E0 = np.exp(-epsilon * Te) * np.sin(omega_g * Te)
            alpha = -(E0 / (Ta - Te))
            
            waveform[return_mask] = E0 * np.exp(-t_return / (Ta - Te))
        
        # Closed phase (Ta to T0) - zero
        # (already initialized to zero)
        
        # Normalize
        if np.max(np.abs(waveform)) > 0:
            waveform = waveform / np.max(np.abs(waveform))
        
        return waveform
    
    def generate(
        self, 
        duration: float,
        params: VocalTractParams,
        f0_contour: np.ndarray = None
    ) -> np.ndarray:
        """
        Generate glottal source waveform for specified duration
        
        Args:
            duration: Duration in seconds
            params: Vocal tract parameters
            f0_contour: Optional F0 contour (array of pitch values)
            
        Returns:
            Glottal flow derivative waveform
        """
        total_samples = int(self.sample_rate * duration)
        output = np.zeros(total_samples)
        
        current_sample = 0
        
        while current_sample < total_samples:
            # Get current F0 (support for pitch contours)
            if f0_contour is not None:
                progress = current_sample / total_samples
                f0_index = min(int(progress * len(f0_contour)), len(f0_contour) - 1)
                f0 = f0_contour[f0_index]
            else:
                f0 = params.f0
            
            # Generate one pulse
            pulse = self.generate_pulse(
                f0=f0,
                oq=params.open_quotient,
                sq=params.speed_quotient,
                te_ratio=0.4
            )
            
            # Add to output (with tenseness scaling)
            end_sample = min(current_sample + len(pulse), total_samples)
            output_slice = output[current_sample:end_sample]
            pulse_slice = pulse[:len(output_slice)]
            
            output[current_sample:end_sample] += pulse_slice * params.tenseness
            
            current_sample = end_sample
        
        return output


class FormantFilter:
    """
    Cascade formant filter using biquad filters
    
    Models vocal tract resonances (formants) using second-order
    resonant filters in cascade configuration.
    """
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
    
    def design_formant_filter(
        self, 
        frequency: float, 
        bandwidth: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Design a single formant filter (resonant biquad)
        
        Args:
            frequency: Formant center frequency (Hz)
            bandwidth: Formant bandwidth (Hz)
            
        Returns:
            (b, a) filter coefficients for scipy.signal.lfilter
        """
        # Resonant filter using pole placement
        r = np.exp(-np.pi * bandwidth / self.sample_rate)
        theta = 2 * np.pi * frequency / self.sample_rate
        
        # Poles
        pole_r = r
        pole_theta = theta
        
        # Transfer function
        b = [1.0]
        a = [
            1.0,
            -2 * pole_r * np.cos(pole_theta),
            pole_r ** 2
        ]
        
        return np.array(b), np.array(a)
    
    def apply_formants(
        self, 
        signal_data: np.ndarray, 
        params: VocalTractParams
    ) -> np.ndarray:
        """
        Apply cascade formant filtering
        
        Args:
            signal_data: Input signal (glottal source)
            params: Vocal tract parameters (formant frequencies/bandwidths)
            
        Returns:
            Filtered signal with vocal tract resonances
        """
        output = signal_data.copy()
        
        # Apply formant filters in cascade (F1 -> F2 -> F3 -> F4)
        formants = [
            (params.f1, params.bw1),
            (params.f2, params.bw2),
            (params.f3, params.bw3),
            (params.f4, params.bw4),
        ]
        
        for freq, bw in formants:
            b, a = self.design_formant_filter(freq, bw)
            output = signal.lfilter(b, a, output)
        
        return output


class NoiseGenerator:
    """
    Generate aspiration noise for breathiness
    """
    
    @staticmethod
    def generate_noise(duration: float, sample_rate: int = 48000) -> np.ndarray:
        """Generate white noise"""
        samples = int(duration * sample_rate)
        return np.random.randn(samples)
    
    @staticmethod
    def shape_noise(
        noise: np.ndarray,
        cutoff: float = 5000.0,
        sample_rate: int = 48000
    ) -> np.ndarray:
        """Shape noise with lowpass filter"""
        nyquist = sample_rate / 2.0
        normalized_cutoff = cutoff / nyquist
        b, a = signal.butter(4, normalized_cutoff, btype='low')
        return signal.lfilter(b, a, noise)


class SourceFilterSynthesizer:
    """
    Complete source-filter vocal tract synthesizer
    
    Combines glottal source, formant filtering, and aspiration noise
    to generate speech-like audio based on physical parameters.
    """
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.glottal_model = LFGlottalModel(sample_rate)
        self.formant_filter = FormantFilter(sample_rate)
        self.noise_gen = NoiseGenerator()
    
    def apply_emotion_modulation(self, params: VocalTractParams) -> VocalTractParams:
        """
        Apply emotion modulation to vocal tract parameters
        
        Maps arousal/valence/dominance to physical parameters
        """
        modulated = VocalTractParams(**vars(params))
        
        # Arousal effects (energy, activation)
        # High arousal: higher F0, higher pressure (tenseness), faster speech
        arousal_factor = (params.arousal - 0.5) * 2  # -1 to +1
        modulated.f0 *= (1.0 + arousal_factor * 0.3)  # ±30% F0
        modulated.tenseness *= (1.0 + arousal_factor * 0.2)  # ±20% tenseness
        
        # Valence effects (positive/negative emotion)
        # Positive: wider pitch range, brighter timbre
        valence_factor = (params.valence - 0.5) * 2  # -1 to +1
        modulated.f1 *= (1.0 + valence_factor * 0.1)  # ±10% formant shift
        
        # Dominance effects (power, control)
        # High dominance: tenser voice, lower F0 variance
        dominance_factor = (params.dominance - 0.5) * 2  # -1 to +1
        modulated.tenseness *= (1.0 + dominance_factor * 0.15)  # ±15% tenseness
        
        return modulated
    
    def synthesize(
        self, 
        duration: float, 
        params: VocalTractParams,
        add_noise: bool = True
    ) -> np.ndarray:
        """
        Synthesize speech using source-filter model
        
        Args:
            duration: Duration in seconds
            params: Vocal tract parameters
            add_noise: Whether to add aspiration noise
            
        Returns:
            Synthesized audio waveform
        """
        # Apply emotion modulation
        params = self.apply_emotion_modulation(params)
        
        # Generate glottal source
        glottal_source = self.glottal_model.generate(duration, params)
        
        # Apply formant filtering
        filtered = self.formant_filter.apply_formants(glottal_source, params)
        
        # Add aspiration noise if requested
        if add_noise and params.breathiness > 0:
            noise = self.noise_gen.generate_noise(duration, self.sample_rate)
            shaped_noise = self.noise_gen.shape_noise(noise, cutoff=3000.0, sample_rate=self.sample_rate)
            filtered += shaped_noise * params.breathiness * 0.1
        
        # Normalize
        if np.max(np.abs(filtered)) > 0:
            filtered = filtered / np.max(np.abs(filtered)) * 0.8  # Leave headroom
        
        return filtered
    
    def save_wav(self, audio: np.ndarray, filename: str):
        """Save audio to WAV file"""
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(filename, self.sample_rate, audio_int16)
        print(f"Saved: {filename}")


# ==============================================================================
# DEMONSTRATION / TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("VOCAL TRACT SYNTHESIS - Source-Filter Prototype v1")
    print("=" * 70)
    
    # Initialize synthesizer
    synth = SourceFilterSynthesizer(sample_rate=48000)
    
    # Test 1: Human male voice (baseline)
    print("\nTest 1: Human Male Voice (Baseline)")
    print("-" * 70)
    human_params = VocalTractParams(
        f0=120.0,
        tract_length=17.5,
        open_quotient=0.7,
        tenseness=0.6,
        breathiness=0.03,
        # Vowel /a/ formants
        f1=800, bw1=80,
        f2=1200, bw2=90,
        f3=2500, bw3=120,
        f4=3500, bw4=200,
        arousal=0.5,
        valence=0.5,
        dominance=0.5
    )
    
    audio_human = synth.synthesize(duration=2.0, params=human_params)
    synth.save_wav(audio_human, "vocal-chord-research/data/test1_human_male.wav")
    print(f"  Duration: 2.0s | F0: {human_params.f0}Hz | Tract: {human_params.tract_length}cm")
    
    # Test 2: Vampire voice (elongated tract, breathy)
    print("\nTest 2: Vampire Voice (Elongated Tract + Breathiness)")
    print("-" * 70)
    vampire_params = VocalTractParams(
        f0=110.0,  # Slightly lower
        tract_length=19.5,  # +2cm longer
        open_quotient=0.65,
        tenseness=0.65,
        breathiness=0.3,  # Much more breathy
        # Lowered formants due to longer tract
        f1=750, bw1=85,
        f2=1150, bw2=95,
        f3=2400, bw3=130,
        f4=3400, bw4=210,
        arousal=0.4,  # Calm, controlled
        valence=0.3,  # Dark, menacing
        dominance=0.8  # Commanding
    )
    
    audio_vampire = synth.synthesize(duration=2.0, params=vampire_params)
    synth.save_wav(audio_vampire, "vocal-chord-research/data/test2_vampire.wav")
    print(f"  Duration: 2.0s | F0: {vampire_params.f0}Hz | Tract: {vampire_params.tract_length}cm")
    print(f"  Breathiness: {vampire_params.breathiness} | Dominance: {vampire_params.dominance}")
    
    # Test 3: Zombie voice (degraded, irregular)
    print("\nTest 3: Zombie Voice (Degraded Vocal Apparatus)")
    print("-" * 70)
    zombie_params = VocalTractParams(
        f0=90.0,  # Much lower
        tract_length=17.5,
        open_quotient=0.5,  # Irregular
        tenseness=0.2,  # Very loose
        breathiness=0.15,
        # Irregular, wider bandwidths (less precise resonance)
        f1=780, bw1=150,  # Much wider bandwidth
        f2=1180, bw2=180,
        f3=2480, bw3=220,
        f4=3480, bw4=300,
        arousal=0.2,  # Low energy
        valence=0.1,  # Very negative
        dominance=0.2  # Weak
    )
    
    audio_zombie = synth.synthesize(duration=2.0, params=zombie_params)
    synth.save_wav(audio_zombie, "vocal-chord-research/data/test3_zombie.wav")
    print(f"  Duration: 2.0s | F0: {zombie_params.f0}Hz | Tenseness: {zombie_params.tenseness}")
    print(f"  Bandwidth F1: {zombie_params.bw1}Hz (degraded resonance)")
    
    # Test 4: Emotion testing - Fear
    print("\nTest 4: Human Voice with Fear Emotion")
    print("-" * 70)
    fear_params = VocalTractParams(
        f0=140.0,  # Higher pitch
        tract_length=17.5,
        open_quotient=0.75,
        tenseness=0.8,  # Tense throat
        breathiness=0.08,
        f1=820, bw1=70,
        f2=1220, bw2=80,
        f3=2520, bw3=110,
        f4=3520, bw4=190,
        arousal=0.9,  # HIGH arousal
        valence=0.2,  # Negative
        dominance=0.3  # Low control
    )
    
    audio_fear = synth.synthesize(duration=2.0, params=fear_params)
    synth.save_wav(audio_fear, "vocal-chord-research/data/test4_fear.wav")
    print(f"  Duration: 2.0s | Emotion: FEAR")
    print(f"  Arousal: {fear_params.arousal} | Tenseness: {fear_params.tenseness}")
    
    # Test 5: Emotion testing - Rage
    print("\nTest 5: Human Voice with Rage Emotion")
    print("-" * 70)
    rage_params = VocalTractParams(
        f0=100.0,  # Lower, growling
        tract_length=17.5,
        open_quotient=0.6,
        tenseness=0.9,  # Very tense
        breathiness=0.02,
        f1=850, bw1=100,
        f2=1250, bw2=110,
        f3=2550, bw3=140,
        f4=3550, bw4=220,
        arousal=0.95,  # VERY HIGH arousal
        valence=0.1,  # Very negative
        dominance=0.9  # High control/aggression
    )
    
    audio_rage = synth.synthesize(duration=2.0, params=rage_params)
    synth.save_wav(audio_rage, "vocal-chord-research/data/test5_rage.wav")
    print(f"  Duration: 2.0s | Emotion: RAGE")
    print(f"  Arousal: {rage_params.arousal} | Dominance: {rage_params.dominance}")
    
    print("\n" + "=" * 70)
    print("PROTOTYPE COMPLETE")
    print("=" * 70)
    print("\nGenerated 5 test files demonstrating:")
    print("  1. Baseline human voice")
    print("  2. Vampire (physical differences: longer tract, breathiness)")
    print("  3. Zombie (degraded vocal apparatus)")
    print("  4. Fear emotion (high arousal, tense)")
    print("  5. Rage emotion (very high arousal, aggressive)")
    print("\nNext steps:")
    print("  - Peer review by GPT-Codex-2")
    print("  - Quality assessment vs neural TTS")
    print("  - Performance benchmarking")
    print("=" * 70)

