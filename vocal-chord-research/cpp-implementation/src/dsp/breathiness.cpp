#include "vocal_synthesis/dsp/breathiness.hpp"
#include <algorithm>
#include <cmath>

namespace vocal_synthesis {
namespace dsp {

BreathinessEffect::BreathinessEffect(float sample_rate, uint32_t seed)
    : sample_rate_(sample_rate)
    , rng_(seed)
{
}

void BreathinessEffect::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void BreathinessEffect::setAmount(float amount) {
    amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void BreathinessEffect::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    if (amount_ < 0.01f) {
        std::copy(input, input + num_samples, output);
        return;
    }
    
    // Simple high-pass coefficient (cutoff ~500 Hz)
    const float fc = 500.0f;
    const float rc = 1.0f / (2.0f * 3.14159265359f * fc);
    const float dt = 1.0f / sample_rate_;
    const float alpha = rc / (rc + dt);
    
    for (size_t i = 0; i < num_samples; ++i) {
        // Generate white noise
        float noise = dist_(rng_);
        
        // High-pass filter the noise (remove low freqs)
        const float hp_output = alpha * (hp_z1_ + noise);
        hp_z1_ = hp_output;
        
        // Mix noise with signal
        output[i] = input[i] * (1.0f - amount_ * 0.5f) + hp_output * amount_ * 0.3f;
    }
}

void BreathinessEffect::processInPlace(float* buffer, size_t num_samples) {
    processBuffer(buffer, buffer, num_samples);
}

void BreathinessEffect::reset() {
    hp_z1_ = 0.0f;
}

} // namespace dsp
} // namespace vocal_synthesis

