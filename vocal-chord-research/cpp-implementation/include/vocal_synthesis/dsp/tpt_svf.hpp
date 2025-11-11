#pragma once

#include <cstddef>
#include <cmath>
#include <array>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Topology-Preserving Transform (TPT) State Variable Filter
 * 
 * A numerically stable, time-varying-safe filter suitable for real-time audio.
 * Based on Vadim Zavalishin's "The Art of VA Filter Design" (Native Instruments).
 * 
 * KEY ADVANTAGES over Direct Form biquads:
 * - Stable when parameters change every sample
 * - No coefficient smoothing needed (smooth parameters directly)
 * - No zipper noise from parameter changes
 * - Guaranteed stable for all parameter ranges
 * - Multiple simultaneous outputs (lowpass, bandpass, highpass, notch)
 * 
 * PERFORMANCE:
 * - ~15-20 ops per sample (comparable to biquad)
 * - SIMD-friendly (can process multiple voices in parallel)
 * - No denormal issues (with proper FTZ/DAZ)
 * 
 * CRITICAL DESIGN DECISION (per GPT-5 Pro peer review):
 * - Smooth *parameters* (frequency, Q, gain), NOT filter coefficients
 * - Recompute internal coefficients from smoothed params each sample or block
 * - This guarantees stability during parameter changes
 */
class TPT_SVF {
public:
    /**
     * @brief Filter mode
     */
    enum class Mode {
        LOWPASS,   ///< Lowpass output
        BANDPASS,  ///< Bandpass output (use this for formants!)
        HIGHPASS,  ///< Highpass output
        NOTCH,     ///< Notch (lowpass + highpass)
        PEAK,      ///< Peak/bell (boost/cut at center freq)
        ALLPASS    ///< Allpass (phase shift only)
    };
    
    /**
     * @brief Filter state (2 integrators)
     */
    struct State {
        float s1 = 0.0f;  ///< Integrator 1 state
        float s2 = 0.0f;  ///< Integrator 2 state
        
        void reset() {
            s1 = s2 = 0.0f;
        }
    };
    
    /**
     * @brief Constructor
     * @param sample_rate Sample rate in Hz
     * @param mode Filter mode
     */
    TPT_SVF(float sample_rate = 48000.0f, Mode mode = Mode::BANDPASS);
    
    /**
     * @brief Set sample rate (updates internal coefficients)
     * @param sample_rate Sample rate in Hz
     */
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Set filter mode
     * @param mode Filter mode
     */
    void setMode(Mode mode) { mode_ = mode; }
    
    /**
     * @brief Get current mode
     */
    Mode getMode() const { return mode_; }
    
    /**
     * @brief Set filter parameters
     * 
     * CRITICAL: Smooth these parameters externally at control rate!
     * Do NOT smooth the filter coefficients.
     * 
     * @param frequency Center frequency in Hz (clamped to [20, fs*0.45])
     * @param q Quality factor (clamped to [0.3, 30])
     * @param gain_db Gain in dB (for PEAK mode only, clamped to [-24, +24])
     */
    void setParameters(float frequency, float q, float gain_db = 0.0f);
    
    /**
     * @brief Get current parameters
     */
    float getFrequency() const { return frequency_; }
    float getQ() const { return q_; }
    float getGain() const { return gain_db_; }
    
    /**
     * @brief Process single sample
     * @param input Input sample
     * @return Filtered output
     */
    float processSample(float input);
    
    /**
     * @brief Process buffer
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
     * @brief Reset filter state
     */
    void reset() { state_.reset(); }
    
    /**
     * @brief Get all filter outputs simultaneously (for debugging/analysis)
     * @param input Input sample
     * @param lp Output: lowpass
     * @param bp Output: bandpass
     * @param hp Output: highpass
     */
    void processAllOutputs(float input, float& lp, float& bp, float& hp);
    
private:
    // Parameters (smoothed externally)
    float sample_rate_ = 48000.0f;
    float frequency_ = 1000.0f;
    float q_ = 5.0f;
    float gain_db_ = 0.0f;
    Mode mode_ = Mode::BANDPASS;
    
    // Internal coefficients (recomputed from parameters)
    float g_ = 0.0f;   ///< tan(π * fc / fs) - frequency warp
    float k_ = 0.0f;   ///< 1/Q - damping
    float a1_ = 0.0f;  ///< 1 / (1 + g*(g+k))
    float a2_ = 0.0f;  ///< g*a1
    float a3_ = 0.0f;  ///< g*a2
    float m0_ = 1.0f;  ///< Output mixing coefficient 0
    float m1_ = 0.0f;  ///< Output mixing coefficient 1
    float m2_ = 0.0f;  ///< Output mixing coefficient 2
    
    // State
    State state_;
    
    // Update internal coefficients from parameters
    void updateCoefficients();
};

/**
 * @brief Bank of TPT SVF filters for multi-formant synthesis
 * 
 * Replaces the unstable Direct Form I biquad cascade.
 * Each formant is a bandpass TPT SVF filter.
 * 
 * ADVANTAGES (per GPT-5 Pro review):
 * - Time-varying safe (can modulate frequency/Q per sample)
 * - No coefficient smoothing artifacts
 * - Stable cascade (proper gain management)
 * - Real-time parameter updates without pops/clicks
 */
class TPT_FormantBank {
public:
    /**
     * @brief Formant specification
     */
    struct Formant {
        float frequency;  ///< Center frequency in Hz
        float bandwidth;  ///< Bandwidth in Hz
        float amplitude;  ///< Amplitude (0.0 to 1.0)
        
        /**
         * @brief Convert bandwidth to Q factor
         */
        float getQ() const {
            return frequency / std::max(bandwidth, 1.0f);
        }
    };
    
    static constexpr size_t MAX_FORMANTS = 5;
    
    TPT_FormantBank() = default;
    explicit TPT_FormantBank(float sample_rate);
    
    /**
     * @brief Set sample rate
     * @param sample_rate Sample rate in Hz
     */
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Set formants
     * @param formants Array of formant specs
     * @param num_formants Number of formants (1-5)
     */
    void setFormants(const Formant* formants, size_t num_formants);
    
    /**
     * @brief Shift all formant frequencies
     * @param shift_hz Frequency shift in Hz
     */
    void shiftFormants(float shift_hz);
    
    /**
     * @brief Scale all formant frequencies
     * @param scale Scaling factor
     */
    void scaleFormants(float scale);
    
    /**
     * @brief Expand all bandwidths
     * @param expansion Expansion factor
     */
    void expandBandwidths(float expansion);
    
    /**
     * @brief Process buffer through formant cascade
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
     * @brief Reset all filter states
     */
    void reset();
    
    /**
     * @brief Get number of active formants
     */
    size_t getNumFormants() const { return num_formants_; }
    
private:
    float sample_rate_ = 48000.0f;
    std::array<TPT_SVF, MAX_FORMANTS> filters_;
    std::array<Formant, MAX_FORMANTS> formants_;
    size_t num_formants_ = 0;
    
    void updateFilters();
};

} // namespace dsp
} // namespace vocal_synthesis

