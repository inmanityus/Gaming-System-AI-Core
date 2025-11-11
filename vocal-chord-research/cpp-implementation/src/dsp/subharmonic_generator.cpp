#include "vocal_synthesis/dsp/subharmonic_generator.hpp"
#include <algorithm>
#include <cmath>
#include <vector>

namespace vocal_synthesis {
namespace dsp {

namespace {
    constexpr float PI = 3.14159265358979323846f;
    constexpr float TWO_PI = 2.0f * PI;
}

//==============================================================================
// SubharmonicGenerator
//==============================================================================

SubharmonicGenerator::SubharmonicGenerator(float sample_rate)
    : sample_rate_(sample_rate)
{
}

void SubharmonicGenerator::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void SubharmonicGenerator::setIntensity(float intensity) {
    intensity_ = std::clamp(intensity, 0.0f, 1.0f);
}

void SubharmonicGenerator::setChaos(float chaos) {
    chaos_ = std::clamp(chaos, 0.0f, 1.0f);
}

void SubharmonicGenerator::setTransformationStruggle(float struggle) {
    struggle_ = std::clamp(struggle, 0.0f, 1.0f);
    // Transformation struggle creates random intensity surges
    // High struggle = more frequent, more intense surges
}

void SubharmonicGenerator::setSubharmonics(float octave, float twelfth, float double_octave) {
    octave_amount_ = std::clamp(octave, 0.0f, 1.0f);
    twelfth_amount_ = std::clamp(twelfth, 0.0f, 1.0f);
    double_octave_amount_ = std::clamp(double_octave, 0.0f, 1.0f);
}

void SubharmonicGenerator::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    for (size_t i = 0; i < num_samples; ++i) {
        const float input_sample = input[i];
        
        // Detect period (approximate F0) from zero crossings
        const float period = detectPeriod(input_sample);
        
        // Generate chaos envelope (intermittent beast control)
        const float chaos_env = generateChaosEnvelope();
        
        // Generate transformation struggle surge
        const float struggle_surge = generateStruggleSurge();
        
        // Calculate phase from detected period
        const float phase = TWO_PI * static_cast<float>(samples_since_crossing_) / period;
        
        // Generate subharmonics
        float subharmonic_sum = 0.0f;
        
        if (octave_amount_ > 0.01f) {
            subharmonic_sum += generateSubharmonic(phase, 2) * octave_amount_;
        }
        
        if (twelfth_amount_ > 0.01f) {
            subharmonic_sum += generateSubharmonic(phase, 3) * twelfth_amount_;
        }
        
        if (double_octave_amount_ > 0.01f) {
            subharmonic_sum += generateSubharmonic(phase, 4) * double_octave_amount_;
        }
        
        // Mix subharmonics with original (modulated by chaos, intensity, and struggle)
        // struggle_surge can add up to 2x multiplier during peak surges
        const float beast_amount = intensity_ * chaos_env * (1.0f + struggle_surge * 2.0f);
        output[i] = input_sample + subharmonic_sum * beast_amount * 0.3f;
    }
}

void SubharmonicGenerator::processInPlace(float* buffer, size_t num_samples) {
    // Create temporary buffer for input (inefficient but safe)
    // TODO: Optimize with circular buffer or in-place algorithm
    std::vector<float> temp(buffer, buffer + num_samples);
    processBuffer(buffer, temp.data(), num_samples);
}

void SubharmonicGenerator::reset() {
    chaos_phase_ = 0.0f;
    chaos_envelope_ = 1.0f;
    prev_sample_ = 0.0f;
    zero_crossing_period_ = 100.0f;
    samples_since_crossing_ = 0;
}

float SubharmonicGenerator::detectPeriod(float sample) {
    // Simple zero-crossing detector
    samples_since_crossing_++;
    
    if ((prev_sample_ <= 0.0f && sample > 0.0f) || 
        (prev_sample_ >= 0.0f && sample < 0.0f)) {
        // Zero crossing detected - update period estimate
        const float detected_period = static_cast<float>(samples_since_crossing_);
        zero_crossing_period_ = 0.9f * zero_crossing_period_ + 0.1f * detected_period;
        samples_since_crossing_ = 0;
    }
    
    prev_sample_ = sample;
    
    // Clamp to reasonable voice range (50-500 Hz at 48kHz)
    return std::clamp(zero_crossing_period_, sample_rate_ / 500.0f, sample_rate_ / 50.0f);
}

float SubharmonicGenerator::generateChaosEnvelope() {
    // Beast "asserts control" intermittently
    constexpr float CHAOS_RATE = 1.2f;  // Hz
    
    chaos_phase_ += TWO_PI * CHAOS_RATE / sample_rate_;
    if (chaos_phase_ >= TWO_PI) {
        chaos_phase_ -= TWO_PI;
    }
    
    // Envelope: chaos_=0 → constant, chaos_=1 → varies 0-1
    const float base_envelope = 0.5f + 0.5f * std::sin(chaos_phase_);
    return (1.0f - chaos_) + chaos_ * base_envelope;
}

float SubharmonicGenerator::generateSubharmonic(float phase, int division) {
    const float subharmonic_phase = phase / static_cast<float>(division);
    return std::sin(subharmonic_phase);
}

float SubharmonicGenerator::generateStruggleSurge() {
    if (struggle_ < 0.001f) {
        return 0.0f;  // No struggle
    }
    
    // Random surges at irregular intervals (transformation struggle)
    // Higher struggle = more frequent, more intense surges
    constexpr float SURGE_BASE_RATE = 0.5f;  // Hz (2 second intervals)
    const float surge_rate = SURGE_BASE_RATE * (1.0f + struggle_ * 3.0f);  // Up to 4x faster
    
    struggle_phase_ += TWO_PI * surge_rate / sample_rate_;
    if (struggle_phase_ >= TWO_PI) {
        struggle_phase_ -= TWO_PI;
        // Generate new random surge intensity
        struggle_surge_value_ = (std::rand() / static_cast<float>(RAND_MAX)) * struggle_;
    }
    
    // Exponential decay envelope for each surge
    const float phase_norm = struggle_phase_ / TWO_PI;
    const float surge_env = std::exp(-phase_norm * 8.0f);  // Fast decay
    
    return struggle_surge_value_ * surge_env;
}

} // namespace dsp
} // namespace vocal_synthesis

