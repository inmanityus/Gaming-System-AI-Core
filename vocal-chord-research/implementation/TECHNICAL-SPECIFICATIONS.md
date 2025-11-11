# VOCAL CHORD EMULATION - TECHNICAL SPECIFICATIONS v1.0

**Document Version**: 1.0  
**Date**: 2025-11-09  
**Status**: APPROVED for implementation  
**Author**: Claude Sonnet 4.5  
**Peer Review**: Pending GPT-5 Pro

---

## 1. SYSTEM OVERVIEW

### 1.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VOCAL SYNTHESIS SYSTEM                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────┐      ┌──────────────────────────┐  │
│  │  Anchor Pipeline   │      │  Aberration Transform    │  │
│  │  (Offline)         │─────>│  (Real-time)             │  │
│  │                    │      │                          │  │
│  │ - TTS Generation   │      │ - Formant Shift          │  │
│  │ - Voice Recording  │      │ - Breathiness            │  │
│  │ - Phoneme Library  │      │ - Roughness              │  │
│  │ - Caching          │      │ - Hollow Resonance       │  │
│  └────────────────────┘      │ - Wet Sounds             │  │
│                               │ - Growl Harmonics        │  │
│                               │ - Whisper Mode           │  │
│                               └──────────────────────────┘  │
│                                          │                   │
│                                          ▼                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              LOD Manager (Level of Detail)              │ │
│  │                                                          │ │
│  │  Near (32 voices)  │  Mid (128 voices) │ Far (840)     │ │
│  │  - Full 48kHz      │  - 24kHz          │ - Crowd bus   │ │
│  │  - All modules     │  - Reduced        │ - Minimal     │ │
│  │  - <1ms each       │  - <0.5ms each    │ - Shared      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                          │                   │
│                                          ▼                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              NPC Voice Manager                          │ │
│  │                                                          │ │
│  │  - Voice Assignment    - Parameter Control              │ │
│  │  - Emotion Mapping     - Performance Monitoring         │ │
│  │  - Caching             - Streaming                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Spectral Seed Synthesizer (Ethereal)         │ │
│  │                                                          │ │
│  │  - Seed Generation     - Granular Synthesis             │ │
│  │  - Spectral Shaping    - Effect Processing              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Game Audio     │
                    │  Mixer (UE5)    │
                    └─────────────────┘
```

### 1.2 Technology Stack

**Core Implementation**:
- **Language**: C++17 (performance-critical synthesis)
- **Build System**: CMake 3.20+
- **Audio I/O**: libsndfile, PortAudio
- **DSP**: Custom (no external DSP libraries - full control)
- **Math**: Eigen 3.4+ (linear algebra)

**Python Integration**:
- **Bindings**: pybind11 2.11+
- **Testing**: pytest
- **Prototyping**: NumPy, SciPy

**UE5 Integration**:
- **Plugin**: C++ UE5 audio plugin
- **Audio Mixer**: Custom submix
- **API**: Blueprints + C++

**GPU Acceleration** (Optional Phase 2):
- **Framework**: CUDA 12.0+
- **Target**: Batch synthesis for distant voices

---

## 2. CORE COMPONENTS

### 2.1 Anchor Pipeline (Offline)

**Purpose**: Generate high-quality base audio for transformation

**Input**: Text, Phoneme sequence, or Audio file  
**Output**: 48kHz mono WAV anchor audio  
**Processing**: Offline, one-time per phoneme/word/phrase

**Specifications**:
```cpp
class AnchorPipeline {
public:
    // Generate anchor from text using TTS
    AudioBuffer generateFromText(
        const std::string& text,
        const TTSConfig& config
    );
    
    // Load anchor from recording
    AudioBuffer loadFromFile(const std::string& filepath);
    
    // Create phoneme library
    void buildPhonemeLibrary(
        const std::vector<std::string>& phonemes,
        const TTSConfig& config
    );
    
    // Cache management
    bool isCached(const std::string& key);
    AudioBuffer getFromCache(const std::string& key);
    void addToCache(const std::string& key, const AudioBuffer& audio);
};
```

**TTS Integration Options**:
1. **OpenAI TTS** (recommended for quality)
2. **Google Cloud TTS**
3. **Azure TTS**
4. **Coqui TTS** (open source, local)
5. **Voice Recordings** (professional voice actors)

**Quality Requirements**:
- Sample Rate: 48kHz minimum
- Bit Depth: 16-bit PCM or higher
- Quality: ≥4.2 MOS (clean baseline)
- Latency: Not critical (offline)

---

### 2.2 Aberration Transform (Real-time)

**Purpose**: Apply physical vocal tract transformation to anchor

**Input**: Anchor audio + AberrationParams  
**Output**: Transformed audio with archetype characteristics  
**Processing**: Real-time, <1ms per voice (near LOD)

**Specifications**:
```cpp
struct AberrationParams {
    // Formant shifting (vocal tract length)
    float formant_shift_hz;        // -200 to +200 Hz
    float formant_scale;            // 0.8 to 1.2
    
    // Spectral modifications
    float breathiness;              // 0.0 to 1.0
    float roughness;                // 0.0 to 1.0
    float hollow_resonance;         // 0.0 to 1.0
    float wet_sounds;               // 0.0 to 1.0
    
    // Degradation
    float vocal_fold_irregularity;  // 0.0 to 1.0
    float bandwidth_expansion;      // 1.0 to 3.0
    
    // Special effects
    float growl_harmonics;          // 0.0 to 1.0
    float whisper_mode;             // 0.0 to 1.0
    
    // Tension/pressure
    float tension_modifier;         // 0.3 to 1.5
    float subglottal_pressure;      // 0.5 to 2.0
};

class AberrationTransform {
public:
    // Apply full transformation
    AudioBuffer transform(
        const AudioBuffer& anchor,
        const AberrationParams& params
    );
    
    // Individual transforms (composable)
    void applyFormantShift(AudioBuffer& audio, float shift_hz, float scale);
    void addBreathiness(AudioBuffer& audio, float amount);
    void addRoughness(AudioBuffer& audio, float amount);
    void addHollowResonance(AudioBuffer& audio, float amount);
    void addWetSounds(AudioBuffer& audio, float amount);
    void expandBandwidth(AudioBuffer& audio, float expansion);
    void addGrowlHarmonics(AudioBuffer& audio, float amount);
    void addWhisperMode(AudioBuffer& audio, float amount);
};
```

**Performance Requirements**:
- **Near LOD** (32 voices): <1ms per voice (full quality)
- **Mid LOD** (128 voices): <0.5ms per voice (reduced quality)
- **Far LOD** (840 voices): Crowd bus processing (shared)

**Optimization Strategies**:
- **SIMD**: AVX2/AVX-512 for vector operations
- **SoA Layout**: Structure-of-Arrays for cache efficiency
- **Pre-computation**: Filter coefficients cached
- **Early Exit**: Skip processing for silent/occluded voices

---

### 2.3 LOD Manager (Level of Detail)

**Purpose**: Dynamically adjust voice quality based on distance/importance

**LOD Tiers**:

```cpp
enum class VoiceLOD {
    NEAR,   // Full quality, 48kHz, all effects
    MID,    // Reduced quality, 24kHz, essential effects
    FAR     // Minimal, crowd bus, shared processing
};

class LODManager {
public:
    // Update LOD assignments based on listener position
    void update(
        const Vector3& listenerPos,
        const std::vector<NPCVoice*>& voices
    );
    
    // Get LOD tier for voice
    VoiceLOD getLOD(const NPCVoice* voice) const;
    
    // Performance budgets (ms per frame)
    struct LODBudget {
        float near_budget_ms = 30.0f;   // 32 voices @ ~1ms each
        float mid_budget_ms = 60.0f;     // 128 voices @ ~0.5ms each
        float far_budget_ms = 10.0f;     // Crowd bus processing
    };
    
    void setBudget(const LODBudget& budget);
};
```

**LOD Assignment Strategy**:
1. **Distance**: Closer = higher LOD
2. **Importance**: Story NPCs always near LOD
3. **Visibility**: On-screen NPCs higher LOD
4. **Budget**: Dynamic downgrade if exceeding frame budget

**LOD Transitions**:
- Smooth crossfade (100ms) to avoid pops
- Hysteresis to prevent flickering
- Priority system for limited slots

---

### 2.4 NPC Voice Manager

**Purpose**: Assign and manage voices for all NPCs

**Specifications**:
```cpp
struct NPCVoiceConfig {
    std::string archetype;          // "vampire", "zombie", etc.
    AberrationParams base_params;   // Base transformation
    EmotionState current_emotion;   // Current emotional state
    float variation_seed;           // Individual variation (0-1)
};

class NPCVoiceManager {
public:
    // Voice lifecycle
    VoiceHandle assignVoice(uint32_t npc_id, const NPCVoiceConfig& config);
    void releaseVoice(VoiceHandle handle);
    
    // Voice control
    void speak(
        VoiceHandle handle,
        const std::string& text,
        const EmotionState& emotion
    );
    void stop(VoiceHandle handle);
    
    // Parameter updates
    void updateEmotion(VoiceHandle handle, const EmotionState& emotion);
    void updateState(VoiceHandle handle, const NPCState& state);
    
    // Performance monitoring
    PerformanceStats getStats() const;
    void setPerformanceBudget(float max_ms_per_frame);
};
```

**Emotion Mapping**:
```cpp
struct EmotionState {
    float arousal;      // 0.0 (low) to 1.0 (high)
    float valence;      // 0.0 (negative) to 1.0 (positive)
    float dominance;    // 0.0 (submissive) to 1.0 (dominant)
};

// Emotion → Physical Parameters
AberrationParams applyEmotionModulation(
    const AberrationParams& base,
    const EmotionState& emotion
) {
    AberrationParams modulated = base;
    
    // Arousal effects
    float arousal_factor = (emotion.arousal - 0.5f) * 2.0f; // -1 to +1
    modulated.tension_modifier *= (1.0f + arousal_factor * 0.3f);
    modulated.breathiness += arousal_factor * 0.1f;
    
    // Valence effects
    float valence_factor = (emotion.valence - 0.5f) * 2.0f;
    modulated.formant_shift_hz += valence_factor * 20.0f;
    
    // Dominance effects
    float dominance_factor = (emotion.dominance - 0.5f) * 2.0f;
    modulated.tension_modifier *= (1.0f + dominance_factor * 0.2f);
    
    return modulated;
}
```

---

### 2.5 Spectral Seed Synthesizer (Ethereal)

**Purpose**: Alternative synthesis for non-corporeal beings

**Specifications**:
```cpp
struct SpectralSeedParams {
    // Seed mixture weights
    float whisper_amount;
    float wind_amount;
    float chains_amount;
    float dust_amount;
    float echo_amount;
    
    // Spectral shaping
    std::vector<float> formant_center_freq;
    std::vector<float> formant_bandwidth;
    
    // Prosody
    float grain_rate;
    float grain_duration;
    
    // Ethereal qualities
    float shimmer;
    float reverb_amount;
    float spectral_blur;
};

class SpectralSeedSynthesizer {
public:
    // Synthesize ethereal voice
    AudioBuffer synthesize(
        float duration_sec,
        const SpectralSeedParams& params
    );
    
    // Seed generators
    AudioBuffer generateWhisper(float duration);
    AudioBuffer generateWind(float duration);
    AudioBuffer generateChains(float duration);
    AudioBuffer generateDust(float duration);
    AudioBuffer generateEcho(float duration, const AudioBuffer& source);
    
    // Spectral processing
    void applyFormantShaping(AudioBuffer& audio, const std::vector<float>& freqs, const std::vector<float>& bws);
    void applyGranularPattern(AudioBuffer& audio, float grain_rate, float grain_duration);
    void applyShimmer(AudioBuffer& audio, float amount);
    void applySpectralBlur(AudioBuffer& audio, float amount);
};
```

---

## 3. DATA STRUCTURES

### 3.1 AudioBuffer

```cpp
class AudioBuffer {
private:
    std::vector<float> samples_;
    uint32_t sample_rate_;
    uint32_t num_channels_;

public:
    // Construction
    AudioBuffer(uint32_t sample_rate = 48000, uint32_t num_channels = 1);
    AudioBuffer(const std::vector<float>& samples, uint32_t sample_rate, uint32_t num_channels = 1);
    
    // Access
    float* data() { return samples_.data(); }
    const float* data() const { return samples_.data(); }
    size_t size() const { return samples_.size(); }
    size_t numFrames() const { return samples_.size() / num_channels_; }
    
    // Properties
    uint32_t sampleRate() const { return sample_rate_; }
    uint32_t numChannels() const { return num_channels_; }
    float durationSeconds() const { return static_cast<float>(numFrames()) / sample_rate_; }
    
    // Operations
    void resize(size_t num_frames);
    void clear();
    void normalize(float peak = 0.8f);
    
    // File I/O
    static AudioBuffer loadFromFile(const std::string& filepath);
    void saveToFile(const std::string& filepath) const;
};
```

### 3.2 Archetype Profiles

```cpp
struct ArchetypeProfile {
    std::string name;
    AberrationParams base_params;
    EmotionState default_emotion;
    
    // Voice characteristics
    struct VoiceCharacteristics {
        float f0_min;           // Minimum fundamental frequency
        float f0_max;           // Maximum fundamental frequency
        float f0_default;       // Default pitch
        float formant_scale;    // Overall formant scaling
    } voice_characteristics;
    
    // Variation ranges (for individual NPCs)
    struct VariationRanges {
        float f0_variation;     // ±% variation in pitch
        float param_variation;  // ±% variation in aberration params
    } variation;
    
    // Performance hints
    struct PerformanceHints {
        bool use_gpu;           // Suggest GPU acceleration
        bool cache_aggressive;  // Aggressive caching
        float lod_distance_mult; // LOD distance multiplier
    } performance;
};

// Predefined archetype profiles
namespace ArchetypeProfiles {
    extern const ArchetypeProfile HUMAN_MALE;
    extern const ArchetypeProfile HUMAN_FEMALE;
    extern const ArchetypeProfile VAMPIRE;
    extern const ArchetypeProfile ZOMBIE;
    extern const ArchetypeProfile WEREWOLF_HUMAN;
    extern const ArchetypeProfile WEREWOLF_BEAST;
    extern const ArchetypeProfile LICH;
    extern const ArchetypeProfile GHOUL;
    extern const ArchetypeProfile WRAITH;
}
```

---

## 4. PERFORMANCE SPECIFICATIONS

### 4.1 Targets

| Metric | Target | Critical Path |
|--------|---------|--------------|
| Concurrent Voices | 1000+ | LOD system |
| Latency (Near LOD) | <1ms per voice | SIMD optimization |
| Latency (Mid LOD) | <0.5ms per voice | Reduced effects |
| Latency (Far LOD) | <0.01ms per voice | Crowd bus |
| Total Audio Budget | 100ms per frame | 60fps = 16.67ms frame |
| Memory per Voice | <100MB | Caching + pooling |
| Cache Hit Rate | >95% | Anchor library |

### 4.2 Optimization Strategies

**SIMD (Single Instruction Multiple Data)**:
```cpp
// Example: AVX2 vectorized formant filtering
void applyFormantFilterSIMD(
    float* __restrict__ output,
    const float* __restrict__ input,
    size_t num_samples,
    const FormantFilterCoeffs& coeffs
) {
    __m256 b0 = _mm256_set1_ps(coeffs.b[0]);
    __m256 b1 = _mm256_set1_ps(coeffs.b[1]);
    __m256 b2 = _mm256_set1_ps(coeffs.b[2]);
    __m256 a1 = _mm256_set1_ps(coeffs.a[1]);
    __m256 a2 = _mm256_set1_ps(coeffs.a[2]);
    
    for (size_t i = 0; i < num_samples; i += 8) {
        // Process 8 samples simultaneously
        __m256 x = _mm256_loadu_ps(&input[i]);
        __m256 y = /* filter computation */;
        _mm256_storeu_ps(&output[i], y);
    }
}
```

**Structure-of-Arrays (SoA)**:
```cpp
// BAD: Array-of-Structures (cache-unfriendly)
struct Voice {
    float sample[1024];
    float filter_state[4];
    AberrationParams params;
};
std::vector<Voice> voices; // Poor cache locality

// GOOD: Structure-of-Arrays (cache-friendly)
struct VoiceBank {
    std::vector<float> samples;       // All samples contiguous
    std::vector<float> filter_states; // All states contiguous
    std::vector<AberrationParams> params; // All params contiguous
    
    size_t num_voices;
    size_t samples_per_voice;
};
```

**Memory Pooling**:
```cpp
class AudioBufferPool {
public:
    AudioBuffer* acquire(size_t num_frames);
    void release(AudioBuffer* buffer);
    
private:
    std::vector<std::unique_ptr<AudioBuffer>> pool_;
    std::vector<AudioBuffer*> available_;
};
```

---

## 5. QUALITY SPECIFICATIONS

### 5.1 Targets

| Metric | Target | Measurement Method |
|--------|---------|-------------------|
| Intelligibility | ≥95% | Transcription accuracy test |
| Quality (MOS) | ≥4.0/5.0 | Subjective listening test |
| Archetype Recognition | ≥80% | Classification test |
| Emotion Recognition | ≥70% | Emotion identification test |

### 5.2 Testing Methodology

**Intelligibility Test**:
1. Generate 100 test sentences per archetype
2. Use speech recognition API (Google, Azure)
3. Calculate word error rate (WER)
4. Target: WER <5% (≥95% accuracy)

**Quality (MOS) Test**:
1. Generate paired samples (anchor vs transformed)
2. 20+ human raters evaluate on 1-5 scale
3. Calculate mean opinion score (MOS)
4. Target: MOS ≥4.0

**Archetype Recognition Test**:
1. Generate 20 samples per archetype
2. Human raters classify blind
3. Calculate accuracy
4. Target: ≥80% correct classification

**Emotion Recognition Test**:
1. Generate samples with 5 emotions per archetype
2. Human raters identify emotion blind
3. Calculate accuracy
4. Target: ≥70% correct identification

---

## 6. INTEGRATION SPECIFICATIONS

### 6.1 UE5 Plugin Architecture

```cpp
// UE5 Audio Plugin Interface
class VOCALSYNTHESISPLUGIN_API UVocalSynthesisSubsystem : public UAudioSubsystem {
    GENERATED_BODY()
    
public:
    // Initialization
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    
    // Voice management
    UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
    FVoiceHandle AssignVoice(int32 NPCID, const FArchetypeConfig& Config);
    
    UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
    void ReleaseVoice(FVoiceHandle Handle);
    
    UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
    void Speak(FVoiceHandle Handle, const FString& Text, const FEmotionState& Emotion);
    
    // Real-time updates
    UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
    void UpdateEmotion(FVoiceHandle Handle, const FEmotionState& Emotion);
    
private:
    std::unique_ptr<VocalSynthesisEngine> engine_;
    std::unique_ptr<NPCVoiceManager> voice_manager_;
};
```

### 6.2 Blueprint Integration

**Blueprint Nodes**:
- `Assign Voice to NPC`
- `Release NPC Voice`
- `Speak with Emotion`
- `Update Voice Emotion`
- `Get Voice Performance Stats`

**Data Structures**:
```cpp
USTRUCT(BlueprintType)
struct FArchetypeConfig {
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString ArchetypeName;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FAberrationParams AberrationParams;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FEmotionState DefaultEmotion;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float VariationSeed;
};
```

---

## 7. BUILD SYSTEM

### 7.1 CMake Configuration

```cmake
cmake_minimum_required(VERSION 3.20)
project(VocalSynthesis VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Options
option(VOCAL_BUILD_TESTS "Build unit tests" ON)
option(VOCAL_BUILD_PYTHON_BINDINGS "Build Python bindings" ON)
option(VOCAL_ENABLE_SIMD "Enable SIMD optimizations" ON)
option(VOCAL_ENABLE_GPU "Enable GPU acceleration" OFF)

# Dependencies
find_package(Eigen3 3.4 REQUIRED)
find_package(sndfile REQUIRED)
find_package(portaudio REQUIRED)

if(VOCAL_BUILD_PYTHON_BINDINGS)
    find_package(pybind11 REQUIRED)
endif()

if(VOCAL_ENABLE_GPU)
    find_package(CUDA 12.0 REQUIRED)
endif()

# Source files
add_library(vocal_synthesis
    src/core/audio_buffer.cpp
    src/core/aberration_transform.cpp
    src/core/spectral_seed.cpp
    src/core/lod_manager.cpp
    src/core/npc_voice_manager.cpp
    # ... more sources
)

target_include_directories(vocal_synthesis PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(vocal_synthesis
    PUBLIC Eigen3::Eigen
    PRIVATE sndfile::sndfile portaudio
)

# SIMD optimizations
if(VOCAL_ENABLE_SIMD)
    if(MSVC)
        target_compile_options(vocal_synthesis PRIVATE /arch:AVX2)
    else()
        target_compile_options(vocal_synthesis PRIVATE -mavx2 -mfma)
    endif()
endif()

# Python bindings
if(VOCAL_BUILD_PYTHON_BINDINGS)
    pybind11_add_module(vocal_synthesis_py
        bindings/python/vocal_synthesis.cpp
    )
    target_link_libraries(vocal_synthesis_py PRIVATE vocal_synthesis)
endif()

# Tests
if(VOCAL_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

### 7.2 Directory Structure

```
vocal-synthesis/
├── CMakeLists.txt
├── include/
│   └── vocal_synthesis/
│       ├── audio_buffer.hpp
│       ├── aberration_transform.hpp
│       ├── spectral_seed.hpp
│       ├── lod_manager.hpp
│       ├── npc_voice_manager.hpp
│       └── archetype_profiles.hpp
├── src/
│   ├── core/
│   │   ├── audio_buffer.cpp
│   │   ├── aberration_transform.cpp
│   │   ├── spectral_seed.cpp
│   │   ├── lod_manager.cpp
│   │   └── npc_voice_manager.cpp
│   ├── dsp/
│   │   ├── formant_filter.cpp
│   │   ├── noise_generator.cpp
│   │   └── effects.cpp
│   └── utils/
│       ├── file_io.cpp
│       └── performance.cpp
├── bindings/
│   └── python/
│       └── vocal_synthesis.cpp
├── tests/
│   ├── unit/
│   │   ├── test_audio_buffer.cpp
│   │   ├── test_aberration.cpp
│   │   └── test_spectral_seed.cpp
│   └── integration/
│       ├── test_full_pipeline.cpp
│       └── test_performance.cpp
├── benchmarks/
│   ├── bench_aberration.cpp
│   └── bench_lod.cpp
└── docs/
    ├── api/
    └── examples/
```

---

## 8. TESTING STRATEGY

### 8.1 Unit Tests

```cpp
// Example: test_aberration.cpp
#include <gtest/gtest.h>
#include <vocal_synthesis/aberration_transform.hpp>

TEST(AberrationTransform, ApplyFormantShift) {
    AudioBuffer anchor(48000, 1);
    // ... populate anchor with test signal
    
    AberrationTransform transform;
    AberrationParams params;
    params.formant_shift_hz = -50.0f;
    
    AudioBuffer result = transform.transform(anchor, params);
    
    // Verify formant shift occurred
    // ... spectral analysis
    EXPECT_LT(computeCenterFrequency(result), computeCenterFrequency(anchor));
}

TEST(AberrationTransform, ZeroParamsNoChange) {
    AudioBuffer anchor(48000, 1);
    // ... populate anchor
    
    AberrationTransform transform;
    AberrationParams params; // All zeros/defaults
    
    AudioBuffer result = transform.transform(anchor, params);
    
    // Result should be nearly identical to anchor
    float diff = computeRMSDifference(anchor, result);
    EXPECT_LT(diff, 0.01f);
}
```

### 8.2 Integration Tests

```cpp
// Example: test_full_pipeline.cpp
TEST(FullPipeline, AnchorToTransformedVoice) {
    // Load anchor
    AudioBuffer anchor = AudioBuffer::loadFromFile("test_data/anchor_neutral.wav");
    
    // Apply vampire transformation
    AberrationTransform transform;
    AberrationParams vampire_params = ArchetypeProfiles::VAMPIRE.base_params;
    
    AudioBuffer transformed = transform.transform(anchor, vampire_params);
    
    // Verify quality
    EXPECT_GT(transformed.durationSeconds(), 0.0f);
    EXPECT_EQ(transformed.sampleRate(), 48000);
    
    // Verify breathiness added
    float breathiness = estimateBreathiness(transformed);
    EXPECT_GT(breathiness, estimateBreathiness(anchor));
    
    // Save for manual inspection
    transformed.saveToFile("test_output/vampire_transformed.wav");
}
```

### 8.3 Performance Tests

```cpp
// Example: bench_aberration.cpp
#include <benchmark/benchmark.h>
#include <vocal_synthesis/aberration_transform.hpp>

static void BM_AberrationTransform_Near(benchmark::State& state) {
    AudioBuffer anchor(48000, 1);
    anchor.resize(48000); // 1 second
    
    AberrationTransform transform;
    AberrationParams params = ArchetypeProfiles::VAMPIRE.base_params;
    
    for (auto _ : state) {
        AudioBuffer result = transform.transform(anchor, params);
        benchmark::DoNotOptimize(result);
    }
    
    state.SetItemsProcessed(state.iterations());
}
BENCHMARK(BM_AberrationTransform_Near);

static void BM_AberrationTransform_1000Voices(benchmark::State& state) {
    // Simulate 1000 concurrent voices
    std::vector<AudioBuffer> anchors(1000);
    for (auto& anchor : anchors) {
        anchor = AudioBuffer(48000, 1);
        anchor.resize(2400); // 50ms chunks
    }
    
    AberrationTransform transform;
    AberrationParams params = ArchetypeProfiles::ZOMBIE.base_params;
    
    for (auto _ : state) {
        for (auto& anchor : anchors) {
            AudioBuffer result = transform.transform(anchor, params);
            benchmark::DoNotOptimize(result);
        }
    }
    
    state.SetItemsProcessed(state.iterations() * 1000);
}
BENCHMARK(BM_AberrationTransform_1000Voices);
```

---

## 9. DEPLOYMENT

### 9.1 Platform Support

**Primary Platforms**:
- Windows 10/11 (x64)
- Linux (Ubuntu 20.04+, x64)
- *(Future)* macOS (Intel/Apple Silicon)

**Game Engine**:
- Unreal Engine 5.3+

**Dependencies**:
- Eigen 3.4+ (header-only, bundled)
- libsndfile (bundled or system)
- PortAudio (bundled or system)

### 9.2 Distribution

**C++ Library**:
- Static library (.lib/.a)
- Dynamic library (.dll/.so) for plugin architecture

**UE5 Plugin**:
- Packaged as UE5 plugin
- Distributed through marketplace or direct

**Python Bindings** (Optional):
- PyPI package: `pip install vocal-synthesis`
- Wheels for Windows/Linux

---

## 10. MONITORING & DEBUGGING

### 10.1 Performance Monitoring

```cpp
struct PerformanceStats {
    // Timing
    float total_synthesis_time_ms;
    float avg_voice_time_ms;
    float max_voice_time_ms;
    
    // Voice counts
    uint32_t num_near_lod_voices;
    uint32_t num_mid_lod_voices;
    uint32_t num_far_lod_voices;
    uint32_t num_total_voices;
    
    // Memory
    size_t memory_used_bytes;
    size_t cache_size_bytes;
    float cache_hit_rate;
    
    // Quality
    float avg_quality_estimate;
};

class PerformanceMonitor {
public:
    void beginFrame();
    void endFrame();
    
    void beginVoiceSynthesis(VoiceHandle handle, VoiceLOD lod);
    void endVoiceSynthesis(VoiceHandle handle);
    
    PerformanceStats getStats() const;
    void logStats(const std::string& filepath);
};
```

### 10.2 Debug Visualization

**Features**:
- Real-time waveform display
- Spectrogram visualization
- Formant tracking overlay
- LOD tier visualization (color-coded NPCs)
- Performance graphs (frame time, voice count)

**Tools**:
- UE5 Debug Draw integration
- Standalone visualization tool
- Export to CSV for analysis

---

**END OF TECHNICAL SPECIFICATIONS v1.0**

This document will be peer-reviewed by GPT-5 Pro before implementation begins.

