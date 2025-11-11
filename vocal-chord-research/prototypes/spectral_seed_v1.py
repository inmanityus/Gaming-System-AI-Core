"""
Vocal Tract Synthesis - Spectral Seed Approach (Prototype v3)

Alternative approach for ethereal/non-corporeal beings (Wraiths, Spirits, Ghosts)
that don't have physical vocal tracts.

Concept: Instead of modeling throat/vocal chords, use granular synthesis of
thematic "seed" sounds that coalesce into speech-like patterns.

Seeds for Wraiths:
- Grave dust rustles
- Chain clinks
- Whispered regrets
- Wind through ruins
- Distant echoes

Process:
1. Generate/load seed sounds (thematic audio textures)
2. Apply granular synthesis (small grains arranged in speech patterns)
3. Spectral filtering to shape into phoneme-like sounds
4. Prosodic modulation for speech rhythm

Result: Voice doesn't come FROM a throat, but COALESCES from the air itself

Author: Claude Sonnet 4.5 (Primary)
Concept: Story Teller (Gemini 2.5 Pro)
Peer Review: Pending GPT-Codex-2
Date: 2025-11-09
"""

import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
from dataclasses import dataclass
from typing import List, Tuple, Dict
import os


@dataclass
class SpectralSeedParams:
    """Parameters for spectral seed synthesis"""
    
    # Seed mixture weights (0-1 each, can sum > 1)
    whisper_amount: float = 0.5
    wind_amount: float = 0.3
    chains_amount: float = 0.1
    dust_amount: float = 0.2
    echo_amount: float = 0.4
    
    # Spectral shaping
    formant_center_freq: List[float] = None  # Formant-like resonances
    formant_bandwidth: List[float] = None
    
    # Prosody
    pitch_contour: np.ndarray = None  # Pitch pattern (for prosodic rhythm)
    grain_rate: float = 50.0  # Grains per second
    grain_duration: float = 0.05  # Duration of each grain (seconds)
    
    # Ethereal qualities
    shimmer: float = 0.3  # Amplitude variation (ghostly flickering)
    reverb_amount: float = 0.6  # Spatial depth
    spectral_blur: float = 0.4  # Smearing of frequencies (non-solid)
    
    def __post_init__(self):
        if self.formant_center_freq is None:
            # Default formant-like resonances for speech intelligibility
            self.formant_center_freq = [500.0, 1200.0, 2500.0]
        if self.formant_bandwidth is None:
            self.formant_bandwidth = [150.0, 200.0, 300.0]


class SeedGenerator:
    """Generate thematic seed sounds for spectral synthesis"""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
    
    def generate_whisper(self, duration: float) -> np.ndarray:
        """Generate breathy whisper-like sound"""
        samples = int(duration * self.sample_rate)
        
        # White noise base
        whisper = np.random.randn(samples)
        
        # Shape with bandpass for vocal frequencies
        nyquist = self.sample_rate / 2.0
        low = 200.0 / nyquist
        high = 4000.0 / nyquist
        b, a = signal.butter(4, [low, high], btype='band')
        whisper = signal.lfilter(b, a, whisper)
        
        # Add amplitude modulation (breathiness variation)
        t = np.arange(samples) / self.sample_rate
        mod_freq = 3.0 + np.random.rand() * 2.0  # 3-5 Hz variation
        modulation = 0.5 + 0.5 * np.sin(2 * np.pi * mod_freq * t)
        whisper *= modulation
        
        return whisper * 0.5
    
    def generate_wind(self, duration: float) -> np.ndarray:
        """Generate wind-through-ruins sound"""
        samples = int(duration * self.sample_rate)
        
        # Colored noise (1/f-like spectrum)
        wind = np.random.randn(samples)
        
        # Low-pass for wind-like quality
        nyquist = self.sample_rate / 2.0
        cutoff = 1500.0 / nyquist
        b, a = signal.butter(6, cutoff, btype='low')
        wind = signal.lfilter(b, a, wind)
        
        # Slow amplitude modulation (wind gusts)
        t = np.arange(samples) / self.sample_rate
        gust_freq = 0.5 + np.random.rand() * 0.5  # 0.5-1 Hz
        gusts = 0.4 + 0.6 * (1 + np.sin(2 * np.pi * gust_freq * t)) / 2
        wind *= gusts
        
        return wind * 0.4
    
    def generate_chains(self, duration: float) -> np.ndarray:
        """Generate metallic chain clink sounds"""
        samples = int(duration * self.sample_rate)
        chains = np.zeros(samples)
        
        # Random sparse impacts
        num_impacts = int(duration * 3)  # ~3 clinks per second
        impact_positions = np.random.randint(0, samples, num_impacts)
        
        for pos in impact_positions:
            if pos < samples:
                # Metallic resonance (several close frequencies)
                freq1 = 1200.0 + np.random.rand() * 400.0
                freq2 = 1800.0 + np.random.rand() * 600.0
                freq3 = 3200.0 + np.random.rand() * 800.0
                
                # Decay envelope
                decay_length = int(0.3 * self.sample_rate)  # 300ms decay
                end_pos = min(pos + decay_length, samples)
                impact_samples = end_pos - pos
                
                t = np.arange(impact_samples) / self.sample_rate
                envelope = np.exp(-t * 8.0)  # Fast decay
                
                # Three resonances
                impact = (
                    np.sin(2 * np.pi * freq1 * t) * 0.4 +
                    np.sin(2 * np.pi * freq2 * t) * 0.3 +
                    np.sin(2 * np.pi * freq3 * t) * 0.2
                ) * envelope
                
                chains[pos:end_pos] += impact[:impact_samples]
        
        return chains * 0.3
    
    def generate_dust(self, duration: float) -> np.ndarray:
        """Generate grave dust rustle sound"""
        samples = int(duration * self.sample_rate)
        
        # High-frequency noise (dusty, gritty)
        dust = np.random.randn(samples)
        
        # High-pass filter
        nyquist = self.sample_rate / 2.0
        cutoff = 4000.0 / nyquist
        b, a = signal.butter(4, cutoff, btype='high')
        dust = signal.lfilter(b, a, dust)
        
        # Fast amplitude fluctuations (granular rustling)
        t = np.arange(samples) / self.sample_rate
        flutter_freq = 20.0 + np.random.rand() * 10.0  # 20-30 Hz flutter
        flutter = 0.3 + 0.7 * (1 + np.sin(2 * np.pi * flutter_freq * t)) / 2
        dust *= flutter
        
        return dust * 0.25
    
    def generate_echo(self, duration: float, source: np.ndarray = None) -> np.ndarray:
        """Generate echo/reverb tail"""
        samples = int(duration * self.sample_rate)
        
        if source is None:
            # Generate impulse for echo
            source = np.random.randn(samples) * 0.1
        
        # Multi-tap delay for echo
        delays = [0.15, 0.28, 0.42, 0.61]  # Seconds
        feedbacks = [0.4, 0.3, 0.2, 0.15]
        
        echo = source.copy()
        for delay, feedback in zip(delays, feedbacks):
            delay_samples = int(delay * self.sample_rate)
            if delay_samples < len(source):
                delayed = np.zeros_like(source)
                delayed[delay_samples:] = source[:-delay_samples]
                echo += delayed * feedback
        
        return echo * 0.5
    
    def mix_seeds(
        self,
        duration: float,
        params: SpectralSeedParams
    ) -> np.ndarray:
        """Mix all seed sounds according to parameters"""
        
        seeds = {}
        
        if params.whisper_amount > 0:
            seeds['whisper'] = self.generate_whisper(duration) * params.whisper_amount
        
        if params.wind_amount > 0:
            seeds['wind'] = self.generate_wind(duration) * params.wind_amount
        
        if params.chains_amount > 0:
            seeds['chains'] = self.generate_chains(duration) * params.chains_amount
        
        if params.dust_amount > 0:
            seeds['dust'] = self.generate_dust(duration) * params.dust_amount
        
        # Mix all seeds
        mixed = np.zeros(int(duration * self.sample_rate))
        for seed_name, seed_audio in seeds.items():
            mixed += seed_audio
        
        # Add echo to entire mix
        if params.echo_amount > 0:
            echoed = self.generate_echo(duration, mixed)
            mixed = mixed * (1.0 - params.echo_amount) + echoed * params.echo_amount
        
        return mixed


class SpectralShaper:
    """Shape spectral seed audio into speech-like patterns"""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
    
    def apply_formant_shaping(
        self,
        audio: np.ndarray,
        formant_freqs: List[float],
        formant_bandwidths: List[float]
    ) -> np.ndarray:
        """Apply formant-like resonances for speech intelligibility"""
        
        output = audio.copy()
        
        for freq, bw in zip(formant_freqs, formant_bandwidths):
            # Resonant bandpass filter
            nyquist = self.sample_rate / 2.0
            
            # Bandwidth in normalized frequency
            low = max((freq - bw/2) / nyquist, 0.01)
            high = min((freq + bw/2) / nyquist, 0.99)
            
            if low < high:
                b, a = signal.butter(2, [low, high], btype='band')
                resonance = signal.lfilter(b, a, audio)
                output += resonance * 0.5
        
        return output
    
    def apply_granular_pattern(
        self,
        audio: np.ndarray,
        grain_rate: float,
        grain_duration: float,
        pitch_contour: np.ndarray = None
    ) -> np.ndarray:
        """Apply granular synthesis pattern for speech-like rhythm"""
        
        samples = len(audio)
        output = np.zeros(samples)
        
        # Grain properties
        grain_samples = int(grain_duration * self.sample_rate)
        grain_spacing = int(self.sample_rate / grain_rate)
        
        # Envelope for grain (raised cosine)
        grain_env = 0.5 * (1 - np.cos(2 * np.pi * np.arange(grain_samples) / grain_samples))
        
        # Place grains
        grain_position = 0
        source_position = 0
        
        while grain_position < samples - grain_samples:
            # Extract grain from source
            if source_position + grain_samples < len(audio):
                grain = audio[source_position:source_position + grain_samples] * grain_env
                
                # Place grain in output
                output[grain_position:grain_position + grain_samples] += grain
                
                # Advance positions
                grain_position += grain_spacing
                source_position += grain_samples
                
                # Wrap source if needed
                if source_position >= len(audio) - grain_samples:
                    source_position = 0
            else:
                break
        
        return output
    
    def apply_shimmer(
        self,
        audio: np.ndarray,
        shimmer_amount: float
    ) -> np.ndarray:
        """Apply amplitude shimmer (ghostly flickering)"""
        
        if shimmer_amount <= 0:
            return audio
        
        t = np.arange(len(audio)) / self.sample_rate
        
        # Multiple shimmer frequencies for complex variation
        shimmer = np.ones_like(audio)
        shimmer += np.sin(2 * np.pi * 4.0 * t) * shimmer_amount * 0.15
        shimmer += np.sin(2 * np.pi * 7.3 * t) * shimmer_amount * 0.10
        shimmer += np.sin(2 * np.pi * 11.7 * t) * shimmer_amount * 0.08
        
        return audio * shimmer
    
    def apply_spectral_blur(
        self,
        audio: np.ndarray,
        blur_amount: float
    ) -> np.ndarray:
        """Apply spectral blurring (non-solid, ethereal quality)"""
        
        if blur_amount <= 0:
            return audio
        
        # Use moving average in spectral domain (approximate)
        # Simplified: apply time-domain smoothing
        window_size = int(blur_amount * 100)  # Blur kernel size
        if window_size > 1:
            kernel = np.ones(window_size) / window_size
            blurred = np.convolve(audio, kernel, mode='same')
            return audio * (1.0 - blur_amount) + blurred * blur_amount
        
        return audio


class SpectralSeedSynthesizer:
    """
    Complete spectral seed synthesis system for ethereal beings
    
    Generates voice-like sounds from thematic audio seeds rather than
    modeling physical vocal tracts.
    """
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.seed_gen = SeedGenerator(sample_rate)
        self.shaper = SpectralShaper(sample_rate)
    
    def synthesize(
        self,
        duration: float,
        params: SpectralSeedParams
    ) -> np.ndarray:
        """
        Synthesize ethereal voice using spectral seed approach
        
        Args:
            duration: Duration in seconds
            params: Spectral seed parameters
            
        Returns:
            Synthesized audio (speech-like sound from seeds)
        """
        
        # Generate and mix seed sounds
        mixed_seeds = self.seed_gen.mix_seeds(duration, params)
        
        # Apply formant shaping for speech-like quality
        shaped = self.shaper.apply_formant_shaping(
            mixed_seeds,
            params.formant_center_freq,
            params.formant_bandwidth
        )
        
        # Apply granular pattern for rhythm
        granular = self.shaper.apply_granular_pattern(
            shaped,
            params.grain_rate,
            params.grain_duration,
            params.pitch_contour
        )
        
        # Apply ethereal effects
        shimmered = self.shaper.apply_shimmer(granular, params.shimmer)
        final = self.shaper.apply_spectral_blur(shimmered, params.spectral_blur)
        
        # Normalize
        if np.max(np.abs(final)) > 0:
            final = final / np.max(np.abs(final)) * 0.75
        
        return final
    
    def save_wav(self, audio: np.ndarray, filename: str):
        """Save audio to WAV file"""
        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(filename, self.sample_rate, audio_int16)
        print(f"Saved: {filename}")


# ==============================================================================
# ETHEREAL BEING PRESETS
# ==============================================================================

ETHEREAL_PRESETS = {
    "wraith_standard": SpectralSeedParams(
        whisper_amount=0.6,
        wind_amount=0.3,
        chains_amount=0.15,
        dust_amount=0.1,
        echo_amount=0.5,
        formant_center_freq=[400.0, 1000.0, 2200.0],
        formant_bandwidth=[200.0, 250.0, 350.0],
        grain_rate=45.0,
        grain_duration=0.06,
        shimmer=0.4,
        spectral_blur=0.5,
        reverb_amount=0.7,
    ),
    
    "wraith_ancient": SpectralSeedParams(
        whisper_amount=0.4,
        wind_amount=0.2,
        chains_amount=0.3,  # More chains (bound spirit)
        dust_amount=0.3,  # More dust (ancient)
        echo_amount=0.7,  # More echoes (distant)
        formant_center_freq=[350.0, 900.0, 2000.0],
        formant_bandwidth=[250.0, 300.0, 400.0],
        grain_rate=40.0,  # Slower speech
        grain_duration=0.08,
        shimmer=0.5,
        spectral_blur=0.6,
        reverb_amount=0.8,
    ),
    
    "wraith_vengeful": SpectralSeedParams(
        whisper_amount=0.7,
        wind_amount=0.5,  # Turbulent
        chains_amount=0.25,
        dust_amount=0.05,
        echo_amount=0.4,
        formant_center_freq=[450.0, 1100.0, 2400.0],
        formant_bandwidth=[150.0, 200.0, 300.0],  # Tighter (more focused)
        grain_rate=55.0,  # Faster, urgent
        grain_duration=0.04,
        shimmer=0.6,  # More flickering (agitated)
        spectral_blur=0.4,
        reverb_amount=0.5,
    ),
    
    "spirit_benevolent": SpectralSeedParams(
        whisper_amount=0.8,  # Soft, gentle
        wind_amount=0.1,
        chains_amount=0.0,  # No chains (not bound)
        dust_amount=0.05,
        echo_amount=0.3,  # Less echo (present)
        formant_center_freq=[500.0, 1200.0, 2500.0],  # More human-like
        formant_bandwidth=[150.0, 180.0, 250.0],
        grain_rate=50.0,
        grain_duration=0.05,
        shimmer=0.2,  # Less flickering (stable)
        spectral_blur=0.3,
        reverb_amount=0.4,
    ),
}


# ==============================================================================
# DEMONSTRATION / TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("VOCAL TRACT SYNTHESIS - Spectral Seed Prototype v3")
    print("=" * 70)
    print("\nThis prototype demonstrates an alternative approach for")
    print("ethereal/non-corporeal beings that don't have physical throats.")
    print("\nInstead of modeling vocal tracts, we use:")
    print("  - Thematic seed sounds (whispers, wind, chains, dust, echoes)")
    print("  - Granular synthesis for speech rhythm")
    print("  - Spectral shaping for intelligibility")
    print("\nResult: Voice coalesces from air, not produced by throat")
    print("=" * 70)
    
    # Initialize synthesizer
    synth = SpectralSeedSynthesizer(sample_rate=48000)
    
    # Generate voices for different ethereal beings
    print("\n" + "=" * 70)
    print("GENERATING ETHEREAL VOICES")
    print("=" * 70)
    
    duration = 3.0  # 3 seconds per sample
    
    for preset_name, params in ETHEREAL_PRESETS.items():
        print(f"\n[{preset_name.upper()}]")
        
        # Synthesize
        audio = synth.synthesize(duration, params)
        
        # Save
        output_file = f"vocal-chord-research/data/spectral_{preset_name}.wav"
        synth.save_wav(audio, output_file)
        
        # Show key parameters
        print(f"  Whisper: {params.whisper_amount:.2f}")
        print(f"  Wind: {params.wind_amount:.2f}")
        print(f"  Chains: {params.chains_amount:.2f}")
        print(f"  Dust: {params.dust_amount:.2f}")
        print(f"  Echo: {params.echo_amount:.2f}")
        print(f"  Shimmer: {params.shimmer:.2f}")
        print(f"  Spectral blur: {params.spectral_blur:.2f}")
    
    print("\n" + "=" * 70)
    print("PROTOTYPE COMPLETE")
    print("=" * 70)
    print("\nGenerated spectral seed voices for 4 ethereal types:")
    print("  - wraith_standard (balanced ethereal quality)")
    print("  - wraith_ancient (distant, bound, echoing)")
    print("  - wraith_vengeful (turbulent, agitated, focused)")
    print("  - spirit_benevolent (gentle, present, stable)")
    print("\nKey Innovation: Spectral Seed Synthesis")
    print("  - Voice doesn't come FROM a throat")
    print("  - Voice COALESCES from thematic sounds")
    print("  - Perfect for non-corporeal beings")
    print("  - Narratively honest (no fake throat for ghosts)")
    print("\nNext steps:")
    print("  - Peer review by GPT-Codex-2")
    print("  - Compare to physical modeling approaches")
    print("  - Test intelligibility and character recognition")
    print("=" * 70)

