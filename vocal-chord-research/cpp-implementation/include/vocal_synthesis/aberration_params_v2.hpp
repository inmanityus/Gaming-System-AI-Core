#pragma once

#include "vocal_synthesis/types/strong_types.hpp"
#include <string>
#include <array>

namespace vocal_synthesis {

/**
 * @brief Type-safe aberration parameters (v2.0)
 * 
 * REDESIGNED after GPT-5 Codex peer review:
 * - Strong types prevent parameter mix-ups
 * - Automatic range clamping
 * - Compile-time validation
 * - No magic numbers
 * 
 * BEFORE (v1.0 - UNSAFE):
 *   params.formant_shift_hz = 1000.0f;  // Oops! Wrong range, not caught
 *   params.breathiness = 2.0f;          // Out of range, silent bug
 * 
 * AFTER (v2.0 - TYPE SAFE):
 *   params.formant_shift = FrequencyShift{50.0f};  // Explicit type
 *   params.breathiness = Breathiness{2.0f};        // Automatically clamped to 1.0!
 */
struct AberrationParams {
    
    //==========================================================================
    // FORMANT MANIPULATION
    //==========================================================================
    
    /// Formant frequency shift in Hz
    /// Range: [-200, +200] Hz (automatic clamping)
    types::FrequencyShift formant_shift{0.0f};
    
    /// Formant frequency scaling factor
    /// Range: [0.8, 1.2] (automatic clamping)
    types::FormantScale formant_scale{1.0f};
    
    //==========================================================================
    // SPECTRAL MODIFICATIONS
    //==========================================================================
    
    /// Breathiness: unvoiced noise mixed with voiced signal
    /// Range: [0.0, 1.0] (automatic clamping)
    types::Breathiness breathiness{0.0f};
    
    /// Roughness: amplitude and frequency irregularity
    /// Range: [0.0, 1.0] (automatic clamping)
    types::Roughness roughness{0.0f};
    
    /// Hollow resonance: enhanced low-frequency resonances
    /// Range: [0.0, 1.0] (automatic clamping)
    types::HollowResonance hollow_resonance{0.0f};
    
    /// Wet sounds: liquid/mucus-like artifacts
    /// Range: [0.0, 1.0] (automatic clamping)
    types::WetSounds wet_sounds{0.0f};
    
    //==========================================================================
    // DEGRADATION
    //==========================================================================
    
    /// Vocal fold irregularity: jitter and shimmer
    /// Range: [0.0, 1.0] (automatic clamping)
    types::Irregularity vocal_fold_irregularity{0.0f};
    
    /// Bandwidth expansion: widens formant bandwidths
    /// Range: [1.0, 3.0] (automatic clamping)
    types::BandwidthExpansion bandwidth_expansion{1.0f};
    
    //==========================================================================
    // SPECIAL EFFECTS
    //==========================================================================
    
    /// Growl harmonics: subharmonic frequencies
    /// Range: [0.0, 1.0] (automatic clamping)
    types::GrowlAmount growl_harmonics{0.0f};
    
    /// Whisper mode: noise-based synthesis
    /// Range: [0.0, 1.0] (automatic clamping)
    types::WhisperAmount whisper_mode{0.0f};
    
    //==========================================================================
    // TENSION/PRESSURE
    //==========================================================================
    
    /// Tension modifier: vocal fold tension and articulation tightness
    /// Range: [0.3, 1.5] (automatic clamping)
    types::Tension tension_modifier{1.0f};
    
    /// Subglottal pressure: voice intensity and loudness
    /// Range: [0.5, 2.0] (automatic clamping)
    types::SubglottalPressure subglottal_pressure{1.0f};
    
    //==========================================================================
    // UTILITY FUNCTIONS
    //==========================================================================
    
    /**
     * @brief Validate all parameters (always true with clamped types!)
     * 
     * NOTE: With strong types, this always returns true since values
     * are automatically clamped. Kept for API compatibility.
     */
    constexpr bool validate() const {
        return true;  // Strong types guarantee validity
    }
    
    /**
     * @brief Clamp all parameters (no-op with strong types!)
     * 
     * NOTE: With strong types, this is a no-op since clamping
     * happens automatically. Kept for API compatibility.
     */
    void clamp() {
        // No-op: strong types handle clamping automatically
    }
    
    /**
     * @brief Interpolate between two parameter sets
     * @param other Target parameters
     * @param t Interpolation factor [0.0, 1.0]
     * @return Interpolated parameters
     */
    AberrationParams lerp(const AberrationParams& other, float t) const {
        t = std::clamp(t, 0.0f, 1.0f);
        
        AberrationParams result;
        result.formant_shift = types::lerp(formant_shift, other.formant_shift, t);
        result.formant_scale = types::lerp(formant_scale, other.formant_scale, t);
        result.breathiness = types::lerp(breathiness, other.breathiness, t);
        result.roughness = types::lerp(roughness, other.roughness, t);
        result.hollow_resonance = types::lerp(hollow_resonance, other.hollow_resonance, t);
        result.wet_sounds = types::lerp(wet_sounds, other.wet_sounds, t);
        result.vocal_fold_irregularity = types::lerp(vocal_fold_irregularity, other.vocal_fold_irregularity, t);
        result.bandwidth_expansion = types::lerp(bandwidth_expansion, other.bandwidth_expansion, t);
        result.growl_harmonics = types::lerp(growl_harmonics, other.growl_harmonics, t);
        result.whisper_mode = types::lerp(whisper_mode, other.whisper_mode, t);
        result.tension_modifier = types::lerp(tension_modifier, other.tension_modifier, t);
        result.subglottal_pressure = types::lerp(subglottal_pressure, other.subglottal_pressure, t);
        
        return result;
    }
    
    /**
     * @brief Get a human-readable description of the parameters
     */
    std::string describe() const;
    
    /**
     * @brief Get archetype character classification
     */
    enum class Archetype {
        HUMAN,      ///< Clean human voice
        VAMPIRE,    ///< Ethereal/hollow
        ZOMBIE,     ///< Degraded/rough
        WEREWOLF,   ///< Growling/feral
        WRAITH,     ///< Whispered/ghostly
        UNKNOWN     ///< Unclassified
    };
    
    Archetype getArchetype() const;
    
    //==========================================================================
    // PRESET FACTORY FUNCTIONS
    //==========================================================================
    
    /// Create clean human parameters
    static AberrationParams createHuman();
    
    /// Create vampire parameters (hollow, breathy)
    static AberrationParams createVampire();
    
    /// Create zombie parameters (degraded, rough)
    static AberrationParams createZombie();
    
    /// Create werewolf parameters (growling)
    static AberrationParams createWerewolf();
    
    /// Create wraith parameters (whispered)
    static AberrationParams createWraith();
};

/**
 * @brief Emotion state for dynamic voice modulation
 * 
 * Based on PAD (Pleasure-Arousal-Dominance) model of emotion.
 * Maps to physical vocal parameters for natural emotion expression.
 */
struct EmotionState {
    
    /// Arousal: activation/energy level [0.0, 1.0]
    /// Low = calm, relaxed | High = excited, tense
    types::AmplitudeNormalized arousal{0.5f};
    
    /// Valence: pleasantness [0.0, 1.0]
    /// Low = negative (fear, anger) | High = positive (joy, contentment)
    types::AmplitudeNormalized valence{0.5f};
    
    /// Dominance: control/power [0.0, 1.0]
    /// Low = submissive, weak | High = dominant, strong
    types::AmplitudeNormalized dominance{0.5f};
    
    /**
     * @brief Apply emotion modulation to base parameters
     * 
     * Maps emotion dimensions to physical vocal tract changes:
     * - Arousal → tension, F0, breathiness
     * - Valence → formant shift, spectral tilt
     * - Dominance → tension, pressure
     */
    AberrationParams applyTo(const AberrationParams& base) const;
    
    /**
     * @brief Create emotion state from named emotion
     */
    enum class NamedEmotion {
        NEUTRAL,
        FEAR,
        ANGER,
        JOY,
        SADNESS,
        DISGUST
    };
    
    static EmotionState fromNamed(NamedEmotion emotion);
};

} // namespace vocal_synthesis

