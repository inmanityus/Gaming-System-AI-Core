#include "vocal_synthesis/dsp/parameter_smoother.hpp"
#include <algorithm>
#include <cmath>

namespace vocal_synthesis {
namespace dsp {

ParameterSmoother::ParameterSmoother(float sample_rate, float time_constant_ms)
    : sample_rate_(sample_rate)
    , time_constant_ms_(time_constant_ms)
    , current_(0.0f)
    , target_(0.0f)
{
    setTimeConstant(time_constant_ms);
}

void ParameterSmoother::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
    updateAlpha();
}

void ParameterSmoother::setTimeConstant(float time_constant_ms) {
    // Clamp to reasonable range
    time_constant_ms_ = std::clamp(time_constant_ms, 0.1f, 100.0f);
    updateAlpha();
}

void ParameterSmoother::updateAlpha() {
    // Convert time constant from milliseconds to seconds
    const float tau_seconds = time_constant_ms_ * 0.001f;
    
    // One-pole exponential smoothing coefficient
    // alpha = 1 - exp(-1 / (tau * fs))
    // 
    // Derivation:
    // - tau = time constant (63% of the way to target)
    // - For discrete-time: y[n] = y[n-1] + alpha * (target - y[n-1])
    // - Continuous analog: dy/dt = (target - y) / tau
    // - Discretized with bilinear transform: alpha = 1 - exp(-1/(tau*fs))
    alpha_ = 1.0f - std::exp(-1.0f / (tau_seconds * sample_rate_));
    
    // Clamp alpha to valid range [0, 1] for safety
    alpha_ = std::clamp(alpha_, 0.0f, 1.0f);
}

float ParameterSmoother::processSample() {
    // One-pole exponential smoothing
    // y[n] = y[n-1] + alpha * (target - y[n-1])
    current_ = current_ + alpha_ * (target_ - current_);
    
    // If very close to target, snap to target to avoid denormal issues
    // and ensure we actually reach the target value
    constexpr float SNAP_THRESHOLD = 1.0e-6f;
    if (std::abs(current_ - target_) < SNAP_THRESHOLD) {
        current_ = target_;
    }
    
    return current_;
}

void ParameterSmoother::processBuffer(float* output, size_t num_samples) {
    for (size_t i = 0; i < num_samples; ++i) {
        output[i] = processSample();
    }
}

} // namespace dsp
} // namespace vocal_synthesis

