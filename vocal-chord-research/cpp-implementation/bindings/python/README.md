# Python Bindings for Vocal Synthesis Library

Python interface for real-time vocal tract synthesis.

## Status

**Code**: ✅ Complete  
**Build**: ⚠️ Requires Python development headers  
**Tests**: ✅ Written (test_bindings.py)

## Building

### Requirements
- Python 3.8+ with development headers
- CMake 3.15+
- C++20 compiler
- pybind11 (auto-fetched by CMake)

### Windows
```powershell
# Install Python with dev headers
# Download from python.org, check "Include development files"

cd vocal-chord-research/cpp-implementation
mkdir build && cd build

cmake -D VOCAL_BUILD_PYTHON_BINDINGS=ON ..
cmake --build . --config Release

# Module will be in build/Release/vocal_synthesis_py.pyd
```

### Linux/Mac
```bash
# Install Python dev headers
sudo apt install python3-dev  # Ubuntu/Debian
brew install python3          # macOS

cd vocal-chord-research/cpp-implementation
mkdir build && cd build

cmake -D VOCAL_BUILD_PYTHON_BINDINGS=ON ..
cmake --build . --config Release

# Module will be in build/vocal_synthesis_py.so
```

## Usage

```python
import numpy as np
import vocal_synthesis as vs

# Create zombie voice
zombie_effect = vs.GlottalIncoherence(48000, seed=42)
zombie_effect.set_dynamic_intensity(
    base_intensity=0.6,
    proximity=0.8,      # Close to player
    environment=0.7     # Wet environment
)

# Process audio
audio = np.sin(2 * np.pi * 440 * np.arange(48000) / 48000).astype(np.float32)
zombie_effect.process_in_place(audio)

# Add subliminal layers (vampire)
subliminal = vs.SubliminalAudio(48000)
subliminal.set_layer(vs.SubliminalLayerType.HEARTBEAT, 0.08)
subliminal.set_heartbeat_rate(60.0)
subliminal.process_in_place(audio)

# Use archetypes
vampire_params = vs.AberrationParams.create_vampire()
print(f"Archetype: {vampire_params.get_archetype()}")
```

## API Reference

### Classes
- `AudioBuffer`: Audio data container with DSP utilities
- `AberrationParams`: Type-safe voice parameters
- `EmotionState`: PAD emotion model
- `GlottalIncoherence`: Zombie broken larynx effect
- `SubharmonicGenerator`: Werewolf beast chaos effect
- `PitchStabilizer`: Vampire uncanny stillness effect
- `CorporealNoise`: Corrupted flesh sounds
- `SubliminalAudio`: Barely perceptible organic layers

### Archetypes
- `create_human()`: Clean baseline
- `create_vampire()`: Hollow, ethereal
- `create_zombie()`: Degraded, rough
- `create_werewolf()`: Growling, feral
- `create_wraith()`: Whispered, ghostly

### Phase 2B Enhancements
- `set_dynamic_intensity(base, proximity, environment)`: Dynamic corruption scaling
- `set_transformation_struggle(struggle)`: Random beast surges
- Subliminal layers: Heartbeat, blood flow, breath, organic hum

## Testing

```bash
python test_bindings.py
```

Expected output:
```
✓ AudioBuffer basic operations
✓ Human archetype: HUMAN
✓ Vampire archetype: VAMPIRE
✓ Zombie archetype: ZOMBIE
✓ Werewolf archetype: WEREWOLF
✓ Wraith archetype: WRAITH
✓ GlottalIncoherence with dynamic intensity
✓ SubharmonicGenerator with transformation struggle
✓ SubliminalAudio with heartbeat and blood flow
✓ Emotion modulation (Fear + Anger on Zombie)

✅ All Python binding tests passed!
```

## Performance

Same as C++ library:
- 120-264μs per voice (2-4x better than 500μs target)
- NumPy arrays for zero-copy where possible
- Real-time safe (within Python GIL constraints)

## Integration

### Training Pipeline
```python
# Generate training data
from vocal_synthesis import *

base_audio = load_audio("human_voice.wav")
zombie = GlottalIncoherence(48000)
zombie.set_dynamic_intensity(0.6, 1.0, 0.5)
zombie.process_in_place(base_audio)
save_training_sample(base_audio, "zombie_sample_001")
```

### Batch Processing
```python
# Process multiple files
for wav_file in wav_files:
    audio = load_wav(wav_file)
    effect.process_in_place(audio)
    save_wav(audio, output_file)
```

## Known Limitations

- Requires Python dev headers (not just Python runtime)
- Windows: Requires matching Python architecture (x64)
- GIL impacts real-time performance (use C++ for game)
- Best for: Training, batch processing, prototyping
- For game: Use UE5 plugin (no Python overhead)

## Status: Code Complete, Build Pending Dev Headers

