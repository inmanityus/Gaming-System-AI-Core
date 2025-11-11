#pragma once

#include <cstddef>
#include <cmath>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Subharmonic Generator - Beast undercurrent for werewolf voices
 * 
 * CRITICAL CREATIVE REQUIREMENT (per Story Teller peer review):
 * "For the Werewolf: This isn't just a 'growl' layer. It's a non-linear effect
 *  where the fundamental frequency periodically or chaotically drops an octave,
 *  creating a guttural, animalistic vibration BENEATH the human voice. This
 *  signifies the beast asserting control."
 * 
 * WHAT THIS DOES:
 * - Adds F0/2 (octave down), F0/3, F0/4 subharmonics
 * - Non-linear modulation (chaotic drops, not constant)
 * - Dynamic blending (beast "asserts control" intermittently)
 * - Fry register simulation (vocal fry)
 * 
 * THIS IS NOT:
 * - Simple pitch shift down (too static!)
 * - Constant subharmonic layer (too predictable!)
 * - Separate audio track (not physically integrated!)
 * 
 * CREATIVE GOAL: "Battle between two natures" (Story Teller)
 * 
 * USAGE:
 *   SubharmonicGenerator werewolf_growl(sample_rate);
 *   werewolf_growl.setIntensity(0.7f);  // 70% beast influence
 *   werewolf_growl.setChaos(0.5f);      // 50% chaotic vs controlled
 *   werewolf_growl.processInPlace(audio_buffer, num_samples);
 *   // Result: Human voice with bestial undercurrent, chaotic octave drops
 */
class SubharmonicGenerator {
public:
    /**
     * @brief Constructor
     * @param sample_rate Sample rate in Hz
     */
    explicit SubharmonicGenerator(float sample_rate = 48000.0f);
    
    /**
     * @brief Set sample rate
     */
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Set overall subharmonic intensity
     * @param intensity Effect strength [0.0, 1.0]
     *                  0.0 = no beast, 1.0 = full beast
     */
    void setIntensity(float intensity);
    
    /**
     * @brief Set chaos amount
     * @param chaos Chaos vs control [0.0, 1.0]
     *              0.0 = controlled/constant beast
     *              1.0 = chaotic/intermittent beast
     */
    void setChaos(float chaos);
    
    /**
     * @brief Set transformation struggle intensity
     * @param struggle Transformation struggle [0.0, 1.0]
     *                 0.0 = no struggle, 1.0 = extreme battle
     * 
     * Story Teller refinement: Random subharmonic surges represent
     * beast fighting to break free during transformation
     */
    void setTransformationStruggle(float struggle);
    
    /**
     * @brief Set which subharmonics to generate
     * @param octave F0/2 (octave down) [0, 1]
     * @param twelfth F0/3 (octave + fifth down) [0, 1]
     * @param double_octave F0/4 (two octaves down) [0, 1]
     */
    void setSubharmonics(float octave, float twelfth, float double_octave);
    
    /**
     * @brief Process audio buffer (adds subharmonics)
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
    float intensity_ = 0.0f;        ///< Overall beast influence
    float chaos_ = 0.0f;            ///< Chaos vs control
    float struggle_ = 0.0f;         ///< Transformation struggle
    float octave_amount_ = 1.0f;    ///< F0/2 amount
    float twelfth_amount_ = 0.5f;   ///< F0/3 amount
    float double_octave_amount_ = 0.3f;  ///< F0/4 amount
    
    // Chaos modulation state
    float chaos_phase_ = 0.0f;
    float chaos_envelope_ = 1.0f;
    
    // Struggle surge state
    float struggle_phase_ = 0.0f;
    float struggle_surge_value_ = 0.0f;
    
    // Subharmonic detection state
    float prev_sample_ = 0.0f;
    float zero_crossing_period_ = 100.0f;  // Estimated period in samples
    int samples_since_crossing_ = 0;
    
    /**
     * @brief Detect approximate F0 from zero crossings
     * @param sample Current sample
     * @return Estimated period in samples
     */
    float detectPeriod(float sample);
    
    /**
     * @brief Generate chaos envelope (beast "asserts control")
     * @return Envelope value [0, 1]
     */
    float generateChaosEnvelope();
    
    /**
     * @brief Generate transformation struggle surge
     * @return Surge multiplier [0, 2] - random intensity spikes
     */
    float generateStruggleSurge();
    
    /**
     * @brief Generate subharmonic component
     * @param phase Current phase
     * @param division Frequency division (2, 3, or 4)
     * @return Subharmonic sample
     */
    float generateSubharmonic(float phase, int division);
};

} // namespace dsp
} // namespace vocal_synthesis

