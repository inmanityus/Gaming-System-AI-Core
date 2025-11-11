#pragma once

#include <cstddef>
#include <random>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Breathiness effect - adds aspiration noise to voice
 * 
 * Mixes filtered noise with the voiced signal to simulate:
 * - Incomplete glottal closure
 * - Air leakage through vocal folds
 * - Weak/damaged vocal folds
 * - Hollow/ethereal quality
 */
class BreathinessEffect {
public:
    explicit BreathinessEffect(float sample_rate = 48000.0f, uint32_t seed = 44);
    
    void setSampleRate(float sample_rate);
    void setAmount(float amount);  ///< [0, 1] - 0 = clean, 1 = very breathy
    
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
    std::mt19937 rng_;
    std::normal_distribution<float> dist_{0.0f, 1.0f};
    
    // High-pass filter state (for shaping noise)
    float hp_z1_ = 0.0f;
};

} // namespace dsp
} // namespace vocal_synthesis

