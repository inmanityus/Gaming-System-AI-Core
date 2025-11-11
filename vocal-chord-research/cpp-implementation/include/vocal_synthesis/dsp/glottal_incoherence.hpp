#pragma once

#include <cstddef>
#include <random>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Glottal Incoherence - Simulates broken/damaged larynx
 * 
 * CRITICAL CREATIVE REQUIREMENT (per Story Teller peer review):
 * "For the Zombie: It's not 'breathiness'; it's a stuttering, sputtering of air
 *  through non-functional vocal folds. Think jitter, shimmer, and random amplitude
 *  modulation. It's the sound of the signal source itself FAILING."
 * 
 * WHAT THIS DOES:
 * - Jitter: Random pitch variations (F0 instability)
 * - Shimmer: Random amplitude variations
 * - Pulse irregularity: Non-periodic vocal fold vibrations
 * - Chaos: Breakdown of regular voicing patterns
 * 
 * THIS IS NOT:
 * - Generic breathiness (too clean)
 * - Simple noise addition (too static)
 * - Filter-based effect (wrong domain!)
 * 
 * CREATIVE GOAL: "Voice fighting against entropy" (Story Teller)
 * 
 * USAGE:
 *   GlottalIncoherence zombie_larynx(sample_rate);
 *   zombie_larynx.setIntensity(0.6f);  // 60% broken
 *   zombie_larynx.processInPlace(audio_buffer, num_samples);
 *   // Result: Stuttering, irregular, failing voice
 */
class GlottalIncoherence {
public:
    /**
     * @brief Constructor
     * @param sample_rate Sample rate in Hz
     * @param seed Random seed (for reproducible randomness)
     */
    explicit GlottalIncoherence(float sample_rate = 48000.0f, uint32_t seed = 42);
    
    /**
     * @brief Set sample rate
     */
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Set overall incoherence intensity
     * @param intensity Overall effect strength [0.0, 1.0]
     *                  0.0 = clean, 1.0 = completely broken
     */
    void setIntensity(float intensity);
    
    /**
     * @brief Set dynamic intensity with environmental modulation
     * @param base_intensity Base effect strength [0.0, 1.0]
     * @param proximity Proximity factor [0.0, 1.0] - 0=far, 1=very close
     * @param environment Environmental chaos [0.0, 1.0] - affects texture
     * 
     * Story Teller refinement: Zombie corruption intensifies with proximity
     */
    void setDynamicIntensity(float base_intensity, float proximity, float environment = 0.5f);
    
    /**
     * @brief Set individual component intensities (advanced control)
     * @param jitter F0 jitter amount [0.0, 1.0]
     * @param shimmer Amplitude shimmer amount [0.0, 1.0]
     * @param pulse_irregularity Pulse timing irregularity [0.0, 1.0]
     */
    void setComponents(float jitter, float shimmer, float pulse_irregularity);
    
    /**
     * @brief Process audio buffer (adds incoherence)
     * @param output Output buffer
     * @param input Input buffer
     * @param num_samples Number of samples
     */
    void processBuffer(
        float* output,
        const float* input,
        size_t num_samples
    );
    
    /**
     * @brief Process in-place
     * @param buffer Input/output buffer
     * @param num_samples Number of samples
     */
    void processInPlace(float* buffer, size_t num_samples);
    
    /**
     * @brief Reset internal state
     */
    void reset();
    
private:
    float sample_rate_;
    
    // Intensities
    float jitter_amount_ = 0.0f;       ///< F0 jitter [0, 1]
    float shimmer_amount_ = 0.0f;      ///< Amplitude shimmer [0, 1]
    float irregularity_amount_ = 0.0f; ///< Pulse irregularity [0, 1]
    
    // Internal state
    float phase_ = 0.0f;               ///< Current phase for modulation
    float envelope_state_ = 1.0f;      ///< Amplitude envelope state
    
    // Random number generation
    std::mt19937 rng_;
    std::uniform_real_distribution<float> dist_{-1.0f, 1.0f};
    
    // Modulation rates (in Hz)
    static constexpr float JITTER_RATE_HZ = 5.0f;       ///< Pitch jitter frequency
    static constexpr float SHIMMER_RATE_HZ = 8.0f;      ///< Amplitude shimmer frequency
    static constexpr float IRREGULARITY_RATE_HZ = 3.0f; ///< Pulse irregularity rate
    
    /**
     * @brief Generate jitter modulation for one sample
     * @return Jitter value [-1, +1]
     */
    float generateJitter();
    
    /**
     * @brief Generate shimmer modulation for one sample
     * @return Shimmer value [0, 1]
     */
    float generateShimmer();
    
    /**
     * @brief Generate pulse irregularity for one sample
     * @return Irregularity factor [0, 1]
     */
    float generateIrregularity();
};

/**
 * @brief Jitter generator (F0 pitch instability)
 * 
 * Adds random variations to fundamental frequency.
 * Simulates vocal fold tension irregularities.
 */
class JitterGenerator {
public:
    explicit JitterGenerator(float sample_rate = 48000.0f, uint32_t seed = 42);
    
    void setSampleRate(float sample_rate);
    void setAmount(float amount);  ///< [0, 1] - 0 = none, 1 = extreme
    
    /**
     * @brief Generate jitter for current sample
     * @return Pitch deviation factor [1-amount, 1+amount]
     */
    float generateSample();
    
    void reset();
    
private:
    float sample_rate_;
    float amount_ = 0.0f;
    float phase_ = 0.0f;
    std::mt19937 rng_;
    std::normal_distribution<float> dist_{0.0f, 1.0f};
};

/**
 * @brief Shimmer generator (amplitude instability)
 * 
 * Adds random variations to amplitude.
 * Simulates vocal fold mass/stiffness irregularities.
 */
class ShimmerGenerator {
public:
    explicit ShimmerGenerator(float sample_rate = 48000.0f, uint32_t seed = 43);
    
    void setSampleRate(float sample_rate);
    void setAmount(float amount);  ///< [0, 1] - 0 = none, 1 = extreme
    
    /**
     * @brief Generate shimmer for current sample
     * @return Amplitude factor [1-amount, 1+amount]
     */
    float generateSample();
    
    void reset();
    
private:
    float sample_rate_;
    float amount_ = 0.0f;
    float phase_ = 0.0f;
    std::mt19937 rng_;
    std::normal_distribution<float> dist_{0.0f, 1.0f};
};

} // namespace dsp
} // namespace vocal_synthesis

