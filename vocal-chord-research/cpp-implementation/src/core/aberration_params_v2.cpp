#include "vocal_synthesis/aberration_params_v2.hpp"
#include <sstream>

namespace vocal_synthesis {

std::string AberrationParams::describe() const {
    std::ostringstream oss;
    oss << "AberrationParams (Type-Safe v2.0):\n";
    oss << "  Formant: shift=" << formant_shift.get() << "Hz, scale=" << formant_scale.get() << "\n";
    oss << "  Spectral: breath=" << breathiness.get() << ", rough=" << roughness.get() 
        << ", hollow=" << hollow_resonance.get() << ", wet=" << wet_sounds.get() << "\n";
    oss << "  Degradation: irregularity=" << vocal_fold_irregularity.get() 
        << ", bandwidth=" << bandwidth_expansion.get() << "\n";
    oss << "  Effects: growl=" << growl_harmonics.get() << ", whisper=" << whisper_mode.get() << "\n";
    oss << "  Articulatory: tension=" << tension_modifier.get() 
        << ", pressure=" << subglottal_pressure.get() << "\n";
    oss << "  Archetype: ";
    
    switch (getArchetype()) {
        case Archetype::HUMAN:
            oss << "Human (clean)\n";
            break;
        case Archetype::VAMPIRE:
            oss << "Vampire (ethereal/hollow)\n";
            break;
        case Archetype::ZOMBIE:
            oss << "Zombie (degraded/rough)\n";
            break;
        case Archetype::WEREWOLF:
            oss << "Werewolf (growling/feral)\n";
            break;
        case Archetype::WRAITH:
            oss << "Wraith (whispered/ghostly)\n";
            break;
        case Archetype::UNKNOWN:
            oss << "Unknown/Mixed\n";
            break;
    }
    
    return oss.str();
}

AberrationParams::Archetype AberrationParams::getArchetype() const {
    // Classify based on dominant characteristics
    
    if (breathiness.get() > 0.4f || hollow_resonance.get() > 0.4f) {
        return Archetype::VAMPIRE;
    } else if (roughness.get() > 0.5f || vocal_fold_irregularity.get() > 0.5f) {
        return Archetype::ZOMBIE;
    } else if (growl_harmonics.get() > 0.5f) {
        return Archetype::WEREWOLF;
    } else if (whisper_mode.get() > 0.5f) {
        return Archetype::WRAITH;
    } else if (breathiness.get() < 0.1f && roughness.get() < 0.1f && 
               growl_harmonics.get() < 0.1f && whisper_mode.get() < 0.1f) {
        return Archetype::HUMAN;
    }
    
    return Archetype::UNKNOWN;
}

//==============================================================================
// PRESET FACTORY FUNCTIONS
//==============================================================================

AberrationParams AberrationParams::createHuman() {
    AberrationParams params;
    // All defaults are already clean human values
    return params;
}

AberrationParams AberrationParams::createVampire() {
    AberrationParams params;
    params.formant_shift = types::FrequencyShift{-50.0f};     // Elongated vocal tract
    params.breathiness = types::Breathiness{0.3f};            // Hollow quality
    params.hollow_resonance = types::HollowResonance{0.4f};  // Enhanced resonances
    params.tension_modifier = types::Tension{0.65f};          // Slightly relaxed
    return params;
}

AberrationParams AberrationParams::createZombie() {
    AberrationParams params;
    params.roughness = types::Roughness{0.6f};                       // Degraded vocal folds
    params.vocal_fold_irregularity = types::Irregularity{0.6f};     // Jitter/shimmer
    params.bandwidth_expansion = types::BandwidthExpansion{2.0f};   // Lost resonance clarity
    params.wet_sounds = types::WetSounds{0.5f};                     // Decay/liquid
    params.tension_modifier = types::Tension{0.4f};                 // Weak/damaged
    params.subglottal_pressure = types::SubglottalPressure{0.6f};  // Low breath support
    return params;
}

AberrationParams AberrationParams::createWerewolf() {
    AberrationParams params;
    params.formant_shift = types::FrequencyShift{30.0f};      // Shorter tract (beast)
    params.growl_harmonics = types::GrowlAmount{0.7f};        // Strong subharmonics
    params.roughness = types::Roughness{0.4f};                // Feral quality
    params.tension_modifier = types::Tension{0.8f};           // Tense transformation
    params.subglottal_pressure = types::SubglottalPressure{1.3f};  // Strong breath
    return params;
}

AberrationParams AberrationParams::createWraith() {
    AberrationParams params;
    params.whisper_mode = types::WhisperAmount{0.8f};         // Mostly unvoiced
    params.breathiness = types::Breathiness{0.6f};            // Airy
    params.hollow_resonance = types::HollowResonance{0.3f};  // Ethereal
    params.tension_modifier = types::Tension{0.3f};           // Very relaxed
    return params;
}

//==============================================================================
// EMOTION STATE
//==============================================================================

AberrationParams EmotionState::applyTo(const AberrationParams& base) const {
    AberrationParams modulated = base;
    
    // Arousal effects (high arousal = tense, energetic)
    const float arousal_factor = (arousal.get() - 0.5f) * 2.0f;  // Map to [-1, +1]
    modulated.tension_modifier = types::Tension{
        base.tension_modifier.get() * (1.0f + arousal_factor * 0.3f)
    };
    modulated.breathiness = types::Breathiness{
        base.breathiness.get() + arousal_factor * 0.1f
    };
    
    // Valence effects (positive = brighter formants)
    const float valence_factor = (valence.get() - 0.5f) * 2.0f;
    modulated.formant_shift = types::FrequencyShift{
        base.formant_shift.get() + valence_factor * 20.0f
    };
    
    // Dominance effects (high dominance = strong, controlled)
    const float dominance_factor = (dominance.get() - 0.5f) * 2.0f;
    modulated.tension_modifier = types::Tension{
        modulated.tension_modifier.get() * (1.0f + dominance_factor * 0.2f)
    };
    modulated.subglottal_pressure = types::SubglottalPressure{
        base.subglottal_pressure.get() * (1.0f + dominance_factor * 0.3f)
    };
    
    return modulated;
}

EmotionState EmotionState::fromNamed(NamedEmotion emotion) {
    EmotionState state;
    
    switch (emotion) {
        case NamedEmotion::NEUTRAL:
            state.arousal = types::AmplitudeNormalized{0.5f};
            state.valence = types::AmplitudeNormalized{0.5f};
            state.dominance = types::AmplitudeNormalized{0.5f};
            break;
            
        case NamedEmotion::FEAR:
            state.arousal = types::AmplitudeNormalized{0.8f};   // High energy
            state.valence = types::AmplitudeNormalized{0.2f};   // Negative
            state.dominance = types::AmplitudeNormalized{0.2f}; // Submissive
            break;
            
        case NamedEmotion::ANGER:
            state.arousal = types::AmplitudeNormalized{0.9f};   // Very high energy
            state.valence = types::AmplitudeNormalized{0.2f};   // Negative
            state.dominance = types::AmplitudeNormalized{0.8f}; // Dominant
            break;
            
        case NamedEmotion::JOY:
            state.arousal = types::AmplitudeNormalized{0.7f};   // Energetic
            state.valence = types::AmplitudeNormalized{0.9f};   // Very positive
            state.dominance = types::AmplitudeNormalized{0.6f}; // Confident
            break;
            
        case NamedEmotion::SADNESS:
            state.arousal = types::AmplitudeNormalized{0.3f};   // Low energy
            state.valence = types::AmplitudeNormalized{0.2f};   // Negative
            state.dominance = types::AmplitudeNormalized{0.3f}; // Weak
            break;
            
        case NamedEmotion::DISGUST:
            state.arousal = types::AmplitudeNormalized{0.5f};   // Moderate
            state.valence = types::AmplitudeNormalized{0.2f};   // Negative
            state.dominance = types::AmplitudeNormalized{0.5f}; // Neutral control
            break;
    }
    
    return state;
}

} // namespace vocal_synthesis

