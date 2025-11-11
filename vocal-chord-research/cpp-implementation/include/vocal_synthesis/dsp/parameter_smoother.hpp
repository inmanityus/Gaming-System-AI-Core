#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief One-pole exponential parameter smoother
 * 
 * CRITICAL (per GPT-5 Pro peer review):
 * - Smooth PARAMETERS, not filter coefficients
 * - Sample-rate aware smoothing
 * - Prevents zipper noise and maintains stability
 * 
 * Based on the difference equation:
 *   y[n] = y[n-1] + alpha * (target - y[n-1])
 * 
 * Where alpha controls the smoothing time:
 *   alpha = 1 - exp(-1 / (tau * sample_rate))
 *   tau = time constant in seconds (typically 2-10ms for audio)
 * 
 * PERFORMANCE:
 * - ~3 ops per sample (very cheap)
 * - No denormal issues (clamped to target when close enough)
 * - Guaranteed stable (alpha always in [0, 1])
 */
class ParameterSmoother {
public:
    /**
     * @brief Constructor
     * @param sample_rate Sample rate in Hz
     * @param time_constant_ms Smoothing time in milliseconds (default: 5ms)
     */
    explicit ParameterSmoother(float sample_rate = 48000.0f, float time_constant_ms = 5.0f);
    
    /**
     * @brief Set sample rate (updates smoothing coefficient)
     * @param sample_rate Sample rate in Hz
     */
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Set smoothing time constant
     * @param time_constant_ms Time in milliseconds (clamped to [0.1, 100])
     */
    void setTimeConstant(float time_constant_ms);
    
    /**
     * @brief Set target value (what we're smoothing toward)
     * @param target Target value
     */
    void setTarget(float target) {
        target_ = target;
    }
    
    /**
     * @brief Get current smoothed value
     */
    float getValue() const {
        return current_;
    }
    
    /**
     * @brief Get target value
     */
    float getTarget() const {
        return target_;
    }
    
    /**
     * @brief Check if smoother has reached target (within threshold)
     * @param threshold Closeness threshold (default: 0.0001)
     */
    bool isSettled(float threshold = 0.0001f) const {
        return std::abs(current_ - target_) < threshold;
    }
    
    /**
     * @brief Process one sample (advance smoother state)
     * @return Current smoothed value
     */
    float processSample();
    
    /**
     * @brief Process buffer (returns array of smoothed values)
     * @param output Output buffer for smoothed values
     * @param num_samples Number of samples to process
     */
    void processBuffer(float* output, size_t num_samples);
    
    /**
     * @brief Reset smoother to a specific value (instant jump)
     * @param value Value to reset to
     */
    void reset(float value = 0.0f) {
        current_ = value;
        target_ = value;
    }
    
    /**
     * @brief Skip to target immediately (no smoothing)
     */
    void skipToTarget() {
        current_ = target_;
    }
    
private:
    float sample_rate_;
    float time_constant_ms_;
    float alpha_;        ///< Smoothing coefficient (computed from tau and fs)
    float current_;      ///< Current smoothed value
    float target_;       ///< Target value
    
    void updateAlpha();
};

/**
 * @brief Multi-parameter smoother for parameter structs
 * 
 * Template-based smoother that can smooth entire parameter structures
 * by smoothing each float field independently.
 * 
 * Example usage:
 *   struct VoiceParams {
 *       float frequency;
 *       float q;
 *       float gain;
 *   };
 *   
 *   MultiParameterSmoother<VoiceParams> smoother(48000.0f, 5.0f);
 *   smoother.setTarget({1000.0f, 5.0f, 1.0f});
 *   VoiceParams smoothed = smoother.processSample();
 */
template<typename ParamStruct>
class MultiParameterSmoother {
public:
    MultiParameterSmoother(float sample_rate = 48000.0f, float time_constant_ms = 5.0f)
        : sample_rate_(sample_rate)
        , time_constant_ms_(time_constant_ms)
    {
        updateAlpha();
    }
    
    void setSampleRate(float sample_rate) {
        sample_rate_ = sample_rate;
        updateAlpha();
    }
    
    void setTimeConstant(float time_constant_ms) {
        time_constant_ms_ = std::clamp(time_constant_ms, 0.1f, 100.0f);
        updateAlpha();
    }
    
    void setTarget(const ParamStruct& target) {
        target_ = target;
    }
    
    const ParamStruct& getCurrent() const {
        return current_;
    }
    
    const ParamStruct& getTarget() const {
        return target_;
    }
    
    /**
     * @brief Process one sample (smooth all parameters)
     * @return Current smoothed parameter struct
     */
    ParamStruct processSample() {
        // Smooth each float field independently
        smoothField(current_, target_, alpha_);
        return current_;
    }
    
    void reset(const ParamStruct& value) {
        current_ = value;
        target_ = value;
    }
    
    void skipToTarget() {
        current_ = target_;
    }
    
private:
    float sample_rate_;
    float time_constant_ms_;
    float alpha_;
    ParamStruct current_;
    ParamStruct target_;
    
    void updateAlpha() {
        const float tau_seconds = time_constant_ms_ * 0.001f;
        alpha_ = 1.0f - std::exp(-1.0f / (tau_seconds * sample_rate_));
    }
    
    /**
     * @brief Smooth all float fields in a struct (compile-time reflection)
     * 
     * NOTE: This is a simplified version. In production, use:
     * - boost::pfr for struct reflection, or
     * - Manual field-by-field smoothing, or
     * - C++20 designated initializers
     */
    template<typename T>
    void smoothField(T& current, const T& target, float alpha) {
        // For now, assume T has public float fields that can be smoothed
        // In production, implement proper reflection or manual smoothing
        
        // Example for common parameter types:
        if constexpr (std::is_same_v<T, float>) {
            current = current + alpha * (target - current);
        } else {
            // For struct types, smooth each field
            // This is a placeholder - implement per-struct smoothing
            static_assert(std::is_same_v<T, float>, 
                "MultiParameterSmoother requires custom smoothField implementation for non-float types");
        }
    }
};

} // namespace dsp
} // namespace vocal_synthesis

