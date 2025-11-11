#include "vocal_synthesis/dsp/roughness.hpp"
#include <algorithm>
#include <cmath>

namespace vocal_synthesis {
namespace dsp {

RoughnessEffect::RoughnessEffect(float sample_rate, uint32_t seed)
    : sample_rate_(sample_rate)
    , rng_(seed)
{
}

void RoughnessEffect::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void RoughnessEffect::setAmount(float amount) {
    amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void RoughnessEffect::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    if (amount_ < 0.01f) {
        std::copy(input, input + num_samples, output);
        return;
    }
    
    constexpr float TWO_PI = 2.0f * 3.14159265359f;
    constexpr float ROUGHNESS_RATE = 30.0f;  // Hz modulation
    
    for (size_t i = 0; i < num_samples; ++i) {
        phase_ += TWO_PI * ROUGHNESS_RATE / sample_rate_;
        if (phase_ >= TWO_PI) phase_ -= TWO_PI;
        
        const float noise = dist_(rng_);
        const float modulation = 1.0f + amount_ * 0.2f * std::sin(phase_) * noise;
        
        output[i] = input[i] * modulation;
    }
}

void RoughnessEffect::processInPlace(float* buffer, size_t num_samples) {
    processBuffer(buffer, buffer, num_samples);
}

void RoughnessEffect::reset() {
    phase_ = 0.0f;
}

} // namespace dsp
} // namespace vocal_synthesis

