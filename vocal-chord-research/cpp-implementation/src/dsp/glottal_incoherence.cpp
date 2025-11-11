#include "vocal_synthesis/dsp/glottal_incoherence.hpp"
#include <algorithm>
#include <cmath>

namespace vocal_synthesis {
namespace dsp {

namespace {
    constexpr float PI = 3.14159265358979323846f;
    constexpr float TWO_PI = 2.0f * PI;
}

//==============================================================================
// GlottalIncoherence
//==============================================================================

GlottalIncoherence::GlottalIncoherence(float sample_rate, uint32_t seed)
    : sample_rate_(sample_rate)
    , rng_(seed)
{
}

void GlottalIncoherence::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void GlottalIncoherence::setIntensity(float intensity) {
    intensity = std::clamp(intensity, 0.0f, 1.0f);
    
    // Map overall intensity to individual components
    // Zombie characteristics: high jitter + high shimmer + moderate irregularity
    jitter_amount_ = intensity * 0.8f;        // Strong pitch instability
    shimmer_amount_ = intensity * 0.7f;       // Strong amplitude variation
    irregularity_amount_ = intensity * 0.5f;  // Moderate pulse irregularity
}

void GlottalIncoherence::setDynamicIntensity(float base_intensity, float proximity, float environment) {
    base_intensity = std::clamp(base_intensity, 0.0f, 1.0f);
    proximity = std::clamp(proximity, 0.0f, 1.0f);
    environment = std::clamp(environment, 0.0f, 1.0f);
    
    // Story Teller refinement: Intensity increases exponentially with proximity
    // Far away (proximity=0.0): minimal corruption (base * 0.3)
    // Medium distance (proximity=0.5): moderate corruption (base * 0.7)
    // Very close (proximity=1.0): extreme corruption (base * 1.5)
    const float proximity_mult = 0.3f + (proximity * proximity) * 1.2f;  // Exponential curve
    const float modulated_intensity = base_intensity * proximity_mult;
    
    // Environmental factor affects texture (wet environments = more shimmer)
    const float env_shimmer_boost = environment * 0.3f;
    const float env_jitter_boost = (1.0f - environment) * 0.2f;  // Dry = more jitter
    
    // Apply with environmental modulation
    jitter_amount_ = std::clamp(modulated_intensity * 0.8f + env_jitter_boost, 0.0f, 1.0f);
    shimmer_amount_ = std::clamp(modulated_intensity * 0.7f + env_shimmer_boost, 0.0f, 1.0f);
    irregularity_amount_ = std::clamp(modulated_intensity * 0.5f, 0.0f, 1.0f);
}

void GlottalIncoherence::setComponents(float jitter, float shimmer, float pulse_irregularity) {
    jitter_amount_ = std::clamp(jitter, 0.0f, 1.0f);
    shimmer_amount_ = std::clamp(shimmer, 0.0f, 1.0f);
    irregularity_amount_ = std::clamp(pulse_irregularity, 0.0f, 1.0f);
}

void GlottalIncoherence::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    for (size_t i = 0; i < num_samples; ++i) {
        // Generate modulations
        // TODO: Implement jitter (micro-pitch shift via fractional delay)
        // const float jitter = generateJitter();
        const float shimmer = generateShimmer();
        const float irregularity = generateIrregularity();
        
        // Apply jitter (micro-pitch shift via all-pass phase shift approximation)
        // This is a simplified version - full implementation would use fractional delay
        float sample = input[i];
        
        // Apply shimmer (amplitude modulation)
        const float amplitude_mod = 1.0f + shimmer * (shimmer_amount_ * 0.3f);
        sample *= amplitude_mod;
        
        // Apply irregularity (random dropouts/pulses)
        if (irregularity > (1.0f - irregularity_amount_)) {
            sample *= irregularity;  // Partial or full dropout
        }
        
        output[i] = sample;
    }
}

void GlottalIncoherence::processInPlace(float* buffer, size_t num_samples) {
    processBuffer(buffer, buffer, num_samples);
}

void GlottalIncoherence::reset() {
    phase_ = 0.0f;
    envelope_state_ = 1.0f;
}

float GlottalIncoherence::generateJitter() {
    // Low-frequency random modulation for pitch jitter
    // Update phase
    phase_ += TWO_PI * JITTER_RATE_HZ / sample_rate_;
    if (phase_ >= TWO_PI) {
        phase_ -= TWO_PI;
    }
    
    // Generate smooth random modulation (low-pass filtered noise)
    const float noise = dist_(rng_);
    const float modulation = std::sin(phase_) * noise;
    
    return modulation * jitter_amount_;
}

float GlottalIncoherence::generateShimmer() {
    // Low-frequency random modulation for amplitude shimmer
    float phase_shimmer = phase_ * SHIMMER_RATE_HZ / JITTER_RATE_HZ;
    if (phase_shimmer >= TWO_PI) {
        phase_shimmer -= TWO_PI;
    }
    
    const float noise = dist_(rng_);
    const float modulation = std::sin(phase_shimmer) * noise;
    
    return modulation * shimmer_amount_;
}

float GlottalIncoherence::generateIrregularity() {
    // Random pulse dropouts/irregularities
    return dist_(rng_);
}

//==============================================================================
// JitterGenerator
//==============================================================================

JitterGenerator::JitterGenerator(float sample_rate, uint32_t seed)
    : sample_rate_(sample_rate)
    , rng_(seed)
{
}

void JitterGenerator::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void JitterGenerator::setAmount(float amount) {
    amount_ = std::clamp(amount, 0.0f, 1.0f);
}

float JitterGenerator::generateSample() {
    if (amount_ < 0.001f) {
        return 1.0f;  // No jitter
    }
    
    // Generate low-frequency noise for pitch variations
    // Update phase (5-10 Hz modulation typical for jitter)
    constexpr float JITTER_RATE = 7.0f;  // Hz
    phase_ += TWO_PI * JITTER_RATE / sample_rate_;
    if (phase_ >= TWO_PI) {
        phase_ -= TWO_PI;
    }
    
    // Gaussian noise * sinusoidal envelope for smooth jitter
    const float noise = dist_(rng_);
    const float envelope = std::sin(phase_);
    const float jitter = noise * envelope * amount_;
    
    // Return pitch deviation factor
    // amount_=0.1 → ±10% pitch variation
    // amount_=1.0 → ±100% pitch variation (extreme!)
    return 1.0f + jitter * 0.5f;  // Scale to reasonable range
}

void JitterGenerator::reset() {
    phase_ = 0.0f;
}

//==============================================================================
// ShimmerGenerator
//==============================================================================

ShimmerGenerator::ShimmerGenerator(float sample_rate, uint32_t seed)
    : sample_rate_(sample_rate)
    , rng_(seed)
{
}

void ShimmerGenerator::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void ShimmerGenerator::setAmount(float amount) {
    amount_ = std::clamp(amount, 0.0f, 1.0f);
}

float ShimmerGenerator::generateSample() {
    if (amount_ < 0.001f) {
        return 1.0f;  // No shimmer
    }
    
    // Generate low-frequency noise for amplitude variations
    // Shimmer is typically faster than jitter (8-12 Hz)
    constexpr float SHIMMER_RATE = 10.0f;  // Hz
    phase_ += TWO_PI * SHIMMER_RATE / sample_rate_;
    if (phase_ >= TWO_PI) {
        phase_ -= TWO_PI;
    }
    
    // Gaussian noise * sinusoidal envelope
    const float noise = dist_(rng_);
    const float envelope = std::sin(phase_);
    const float shimmer = noise * envelope * amount_;
    
    // Return amplitude factor
    // amount_=0.1 → ±10% amplitude variation
    // amount_=1.0 → ±100% amplitude variation
    return 1.0f + shimmer * 0.5f;  // Scale to reasonable range
}

void ShimmerGenerator::reset() {
    phase_ = 0.0f;
}

} // namespace dsp
} // namespace vocal_synthesis

