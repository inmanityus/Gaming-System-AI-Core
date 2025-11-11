#pragma once

#include <cstddef>
#include <random>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Roughness effect - amplitude/frequency modulation for vocal damage
 */
class RoughnessEffect {
public:
    explicit RoughnessEffect(float sample_rate = 48000.0f, uint32_t seed = 45);
    
    void setSampleRate(float sample_rate);
    void setAmount(float amount);  ///< [0, 1] - 0 = smooth, 1 = very rough
    
    void processBuffer(
        float* output,
        const float* input,
        size_t num_samples
    );
    
    void processInPlace(float* buffer, size_t num_samples);
    void reset();
    
private:
    float sample_rate_;
    float amount_ = 0.0f;
    float phase_ = 0.0f;
    std::mt19937 rng_;
    std::uniform_real_distribution<float> dist_{-1.0f, 1.0f};
};

} // namespace dsp
} // namespace vocal_synthesis

