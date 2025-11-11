#pragma once

#include <cstddef>
#include <vector>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Pitch Stabilizer - Unnatural stillness for vampire voices
 * 
 * CRITICAL CREATIVE REQUIREMENT (per Story Teller peer review):
 * "For the Vampire: This could be a parameter that introduces extremely sharp,
 *  almost synthetic-sounding resonant peaks, or one that hyper-stabilizes the pitch,
 *  removing all natural human vibrato. It's the 'too-perfect' quality that ventures
 *  into the uncanny valley. It is control, not chaos."
 * 
 * WHAT THIS DOES:
 * - Removes natural vibrato (pitch fluctuations)
 * - Hyper-stabilizes F0 (unnaturally steady pitch)
 * - Creates "too-perfect" quality (uncanny valley)
 * - Simulates predatory control and stillness
 * 
 * THIS IS NOT:
 * - Pitch correction (Auto-Tune style)
 * - Simple low-pass filter (loses expression!)
 * - Constant pitch (needs some micro-variation!)
 * 
 * CREATIVE GOAL: "Humanity hollowed out and replaced with something ancient and cold" (Story Teller)
 * 
 * TECHNICAL APPROACH:
 * - Detect pitch contour via autocorrelation or YIN algorithm
 * - Smooth pitch to remove vibrato (heavy low-pass on F0)
 * - Preserve intentional pitch changes (speech prosody)
 * - Apply via phase vocoder or time-domain pitch shift
 * 
 * USAGE:
 *   PitchStabilizer vampire_control(sample_rate);
 *   vampire_control.setStabilization(0.8f);  // 80% stabilized
 *   vampire_control.processInPlace(audio_buffer, num_samples);
 *   // Result: Unnaturally steady voice, hyper-controlled pitch
 */
class PitchStabilizer {
public:
    /**
     * @brief Constructor
     * @param sample_rate Sample rate in Hz
     */
    explicit PitchStabilizer(float sample_rate = 48000.0f);
    
    /**
     * @brief Set sample rate
     */
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Set stabilization amount
     * @param amount Stabilization strength [0.0, 1.0]
     *               0.0 = natural vibrato
     *               1.0 = completely stable (uncanny!)
     */
    void setStabilization(float amount);
    
    /**
     * @brief Set stabilization time constant
     * @param time_ms Time constant in milliseconds
     *                Shorter = removes fast vibrato (unnatural)
     *                Longer = preserves prosody (natural)
     */
    void setTimeConstant(float time_ms);
    
    /**
     * @brief Process audio buffer (stabilizes pitch)
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
    float stabilization_amount_ = 0.0f;
    float time_constant_ms_ = 50.0f;  ///< Default: 50ms (removes vibrato ~5-6 Hz)
    
    // Pitch detection state
    std::vector<float> pitch_buffer_;
    size_t pitch_buffer_pos_ = 0;
    float detected_pitch_ = 0.0f;
    float smoothed_pitch_ = 0.0f;
    
    // Smoothing coefficient
    float smooth_alpha_ = 0.0f;
    
    /**
     * @brief Detect pitch from audio buffer
     * @param input Audio samples
     * @param num_samples Number of samples
     * @return Estimated F0 in Hz (0 if unvoiced)
     */
    float detectPitch(const float* input, size_t num_samples);
    
    /**
     * @brief Smooth pitch contour (removes vibrato)
     * @param current_pitch Current detected pitch
     * @return Smoothed pitch
     */
    float smoothPitch(float current_pitch);
    
    /**
     * @brief Apply pitch shift to achieve target pitch
     * @param buffer Audio buffer
     * @param num_samples Number of samples
     * @param current_pitch Current pitch
     * @param target_pitch Target pitch
     */
    void applyPitchShift(
        float* buffer,
        size_t num_samples,
        float current_pitch,
        float target_pitch
    );
    
    void updateSmoothingCoeff();
};

} // namespace dsp
} // namespace vocal_synthesis

