/**
 * @file types.hpp
 * @brief Fundamental types for Vocal Synthesis System
 * @version 1.0.0
 * @date 2025-11-09
 * 
 * Core type definitions used throughout the vocal synthesis system.
 * Designed for real-time performance, cache-efficiency, and SIMD optimization.
 */

#pragma once

#include <cstdint>
#include <cstddef>
#include <vector>
#include <array>
#include <memory>
#include <string>

namespace vocal_synthesis {

// ============================================================================
// Configuration Constants
// ============================================================================

/// Default sample rate (Hz)
constexpr uint32_t DEFAULT_SAMPLE_RATE = 48000;

/// Default number of audio channels (mono)
constexpr uint32_t DEFAULT_NUM_CHANNELS = 1;

/// Near LOD buffer size (samples)
constexpr size_t NEAR_BUFFER_SIZE = 64;

/// Mid/Far LOD buffer size (samples)
constexpr size_t MID_FAR_BUFFER_SIZE = 128;

/// Control rate for feature envelopes (Hz)
constexpr uint32_t CONTROL_RATE = 240;

/// Maximum number of Near LOD voices
constexpr size_t MAX_NEAR_VOICES = 32;

/// Maximum number of Mid LOD voices
constexpr size_t MAX_MID_VOICES = 128;

/// Maximum number of Far LOD cluster buses
constexpr size_t MAX_FAR_BUSES = 24;

/// SIMD lane width (AVX2 = 8 floats)
constexpr size_t SIMD_WIDTH = 8;

// ============================================================================
// Basic Types
// ============================================================================

/// Sample type (32-bit float)
using Sample = float;

/// Sample rate type
using SampleRate = uint32_t;

/// Voice identifier
using VoiceID = uint32_t;

/// NPC identifier
using NPCID = uint32_t;

/// Invalid voice ID sentinel
constexpr VoiceID INVALID_VOICE_ID = 0xFFFFFFFF;

// ============================================================================
// LOD (Level of Detail) System
// ============================================================================

/**
 * @brief Voice LOD tiers
 * 
 * Determines synthesis quality and computational cost.
 * - NEAR: Full quality, highest cost (32 max)
 * - MID: Reduced quality, medium cost (128 max)
 * - FAR: Minimal quality, lowest cost (aggregated into buses)
 */
enum class VoiceLOD : uint8_t {
    NEAR = 0,  ///< Near field: Full 48kHz, all effects
    MID = 1,   ///< Mid field: 24kHz, essential effects only
    FAR = 2    ///< Far field: Crowd bus, shared synthesis
};

/**
 * @brief Convert LOD enum to string
 */
inline const char* toString(VoiceLOD lod) {
    switch (lod) {
        case VoiceLOD::NEAR: return "NEAR";
        case VoiceLOD::MID:  return "MID";
        case VoiceLOD::FAR:  return "FAR";
        default:             return "UNKNOWN";
    }
}

// ============================================================================
// Emotion System
// ============================================================================

/**
 * @brief Emotional state representation
 * 
 * Uses the PAD (Pleasure-Arousal-Dominance) model for emotion.
 * Maps emotions to physical vocal tract parameters.
 * 
 * @note Full definition in aberration_params_v2.hpp (v2.0 with strong types)
 */
struct EmotionState;

// ============================================================================
// Aberration Parameters
// ============================================================================

/**
 * @brief Physical transformation parameters for vocal tract aberration
 * 
 * Defines how to transform anchor audio through physical vocal tract modeling.
 * Based on anatomical and physical voice production parameters.
 * 
 * @note Full definition in aberration_params_v2.hpp (v2.0 with strong types)
 */
struct AberrationParams;

// ============================================================================
// Anchor Feature Envelope
// ============================================================================

/**
 * @brief Anchor audio features for transformation
 * 
 * Compact representation of voice characteristics extracted from
 * high-quality anchor audio (TTS or recordings).
 * 
 * Updated at control rate (240 Hz) for efficient real-time processing.
 */
struct AnchorFeature {
    float f0;              ///< Fundamental frequency (Hz)
    float energy;          ///< RMS energy [0.0, 1.0]
    bool voiced;           ///< Voiced/unvoiced flag
    float noise_mix;       ///< Noise component [0.0, 1.0]
    
    // Spectral envelope (24-40 coefficients)
    static constexpr size_t NUM_CEPSTRA = 24;
    std::array<float, NUM_CEPSTRA> cepstra; ///< Bark-scale cepstral coefficients
    
    /// Default constructor
    AnchorFeature() : f0(0.0f), energy(0.0f), voiced(false), noise_mix(0.0f) {
        cepstra.fill(0.0f);
    }
};

/**
 * @brief Anchor Feature Envelope (sequence of features)
 * 
 * Complete feature representation for a phoneme, word, or utterance.
 */
struct AnchorFeatureEnvelope {
    SampleRate sample_rate = DEFAULT_SAMPLE_RATE;
    std::vector<AnchorFeature> features; ///< Feature frames at control rate
    
    // Phoneme timing information
    struct PhonemeSegment {
        std::string phoneme;   ///< Phoneme label (IPA or ARPABET)
        size_t start_frame;    ///< Start frame index
        size_t end_frame;      ///< End frame index
        float duration_sec;    ///< Duration in seconds
    };
    std::vector<PhonemeSegment> phonemes;
    
    // Prosody information
    struct ProsodyTag {
        size_t frame_index;    ///< Frame index
        std::string tag;       ///< Tag type (e.g., "stress", "pause")
        float value;           ///< Tag value
    };
    std::vector<ProsodyTag> prosody;
    
    /// Get duration in seconds
    float durationSeconds() const {
        return static_cast<float>(features.size()) / CONTROL_RATE;
    }
    
    /// Get number of feature frames
    size_t numFrames() const {
        return features.size();
    }
};

// ============================================================================
// Performance Statistics
// ============================================================================

/**
 * @brief Real-time performance statistics
 * 
 * Telemetry data for monitoring and optimization.
 */
struct PerformanceStats {
    // Timing
    float total_synthesis_time_ms = 0.0f;  ///< Total time for all voices
    float avg_voice_time_us = 0.0f;        ///< Average time per voice (µs)
    float max_voice_time_us = 0.0f;        ///< Max time per voice (µs)
    float buffer_time_ms = 0.0f;           ///< Audio buffer duration
    float cpu_usage_percent = 0.0f;        ///< CPU utilization
    
    // Voice counts
    uint32_t num_near_voices = 0;          ///< Active Near LOD voices
    uint32_t num_mid_voices = 0;           ///< Active Mid LOD voices
    uint32_t num_far_voices = 0;           ///< Active Far LOD voices (total)
    uint32_t num_far_buses = 0;            ///< Active Far LOD buses
    uint32_t num_total_voices = 0;         ///< Total active voices
    uint32_t num_voices_stolen = 0;        ///< Voices stolen this frame
    
    // Memory
    size_t memory_used_bytes = 0;          ///< Total memory used
    size_t cache_size_bytes = 0;           ///< Cache size
    float cache_hit_rate = 0.0f;           ///< Cache hit rate [0.0, 1.0]
    
    // Quality
    float avg_quality_estimate = 0.0f;     ///< Estimated average quality
    uint32_t num_underruns = 0;            ///< Audio buffer underruns
    uint32_t num_denormals_detected = 0;   ///< Denormals detected
    
    // Real-time safety
    bool ftz_daz_enabled = false;          ///< FTZ/DAZ mode active
    bool real_time_safe = true;            ///< No allocations in callback
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * @brief Clamp value to range [min, max]
 */
template<typename T>
inline T clamp(T value, T min, T max) {
    return (value < min) ? min : ((value > max) ? max : value);
}

/**
 * @brief Linear interpolation
 */
template<typename T>
inline T lerp(T a, T b, float t) {
    return a + (b - a) * t;
}

/**
 * @brief Convert samples to seconds
 */
inline float samplesToSeconds(size_t samples, SampleRate sample_rate) {
    return static_cast<float>(samples) / static_cast<float>(sample_rate);
}

/**
 * @brief Convert seconds to samples
 */
inline size_t secondsToSamples(float seconds, SampleRate sample_rate) {
    return static_cast<size_t>(seconds * static_cast<float>(sample_rate));
}

/**
 * @brief Check if FTZ/DAZ is enabled (flush-to-zero, denormals-are-zero)
 */
bool isFTZDAZEnabled();

/**
 * @brief Enable FTZ/DAZ mode for denormal prevention
 */
void enableFTZDAZ();

} // namespace vocal_synthesis

