#include "vocal_synthesis/dsp/tpt_svf.hpp"
#include <algorithm>
#include <cmath>

namespace vocal_synthesis {
namespace dsp {

namespace {
    constexpr float PI = 3.14159265358979323846f;
    constexpr float DENORMAL_OFFSET = 1.0e-25f;
    
    // Clamp frequency to safe range
    inline float clampFrequency(float freq, float sample_rate) {
        return std::clamp(freq, 20.0f, sample_rate * 0.45f);
    }
    
    // Clamp Q to safe range
    inline float clampQ(float q) {
        return std::clamp(q, 0.3f, 30.0f);
    }
}

//==============================================================================
// TPT_SVF
//==============================================================================

TPT_SVF::TPT_SVF(float sample_rate, Mode mode)
    : sample_rate_(sample_rate)
    , mode_(mode)
{
    updateCoefficients();
}

void TPT_SVF::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
    updateCoefficients();
}

void TPT_SVF::setParameters(float frequency, float q, float gain_db) {
    // Clamp parameters to safe ranges
    frequency_ = clampFrequency(frequency, sample_rate_);
    q_ = clampQ(q);
    gain_db_ = std::clamp(gain_db, -24.0f, 24.0f);
    
    // Recompute internal coefficients from clamped parameters
    updateCoefficients();
}

void TPT_SVF::updateCoefficients() {
    // TPT frequency warping (bilinear transform prewarp)
    // g = tan(π * fc / fs)
    const float omega = PI * frequency_ / sample_rate_;
    g_ = std::tan(omega);
    
    // Damping factor from Q
    // k = 1 / Q
    k_ = 1.0f / q_;
    
    // TPT SVF coefficients (Zavalishin's formulation)
    // a1 = 1 / (1 + g*(g + k))
    // a2 = g * a1
    // a3 = g * a2
    const float denom = 1.0f + g_ * (g_ + k_);
    a1_ = 1.0f / denom;
    a2_ = g_ * a1_;
    a3_ = g_ * a2_;
    
    // Output mixing coefficients (depend on mode)
    // These determine which combination of LP/BP/HP we output
    switch (mode_) {
        case Mode::LOWPASS:
            m0_ = 0.0f;
            m1_ = 0.0f;
            m2_ = 1.0f;
            break;
            
        case Mode::BANDPASS:
            m0_ = 0.0f;
            m1_ = 1.0f;
            m2_ = 0.0f;
            break;
            
        case Mode::HIGHPASS:
            m0_ = 1.0f;
            m1_ = -k_;
            m2_ = -1.0f;
            break;
            
        case Mode::NOTCH:
            m0_ = 1.0f;
            m1_ = -k_;
            m2_ = 0.0f;
            break;
            
        case Mode::PEAK: {
            // Peak/bell filter (for formant boost/cut)
            const float A = std::pow(10.0f, gain_db_ / 40.0f);  // sqrt of linear gain
            m0_ = 1.0f;
            m1_ = k_ * (A * A - 1.0f);
            m2_ = 0.0f;
            break;
        }
        
        case Mode::ALLPASS:
            m0_ = 1.0f;
            m1_ = -2.0f * k_;
            m2_ = 0.0f;
            break;
    }
}

float TPT_SVF::processSample(float input) {
    // Add denormal protection
    input += DENORMAL_OFFSET;
    
    // TPT SVF difference equations (Zavalishin's form)
    // v1 = a1 * s1 + a2 * (input - s2)
    // v2 = s2 + a2 * s1 + a3 * (input - s2)
    // s1_new = 2*v1 - s1
    // s2_new = 2*v2 - s2
    
    const float v1 = a1_ * state_.s1 + a2_ * (input - state_.s2);
    const float v2 = state_.s2 + a2_ * state_.s1 + a3_ * (input - state_.s2);
    
    // Update states (trapezoidal integration)
    state_.s1 = 2.0f * v1 - state_.s1;
    state_.s2 = 2.0f * v2 - state_.s2;
    
    // Compute output from v1 (BP), v2 (LP), and input (HP component)
    const float lp = v2;
    const float bp = v1;
    const float hp = input - k_ * v1 - v2;
    
    // Mix outputs according to mode
    return m0_ * hp + m1_ * bp + m2_ * lp;
}

void TPT_SVF::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    for (size_t i = 0; i < num_samples; ++i) {
        output[i] = processSample(input[i]);
    }
}

void TPT_SVF::processInPlace(float* buffer, size_t num_samples) {
    for (size_t i = 0; i < num_samples; ++i) {
        buffer[i] = processSample(buffer[i]);
    }
}

void TPT_SVF::processAllOutputs(float input, float& lp, float& bp, float& hp) {
    // Add denormal protection
    input += DENORMAL_OFFSET;
    
    // TPT SVF processing
    const float v1 = a1_ * state_.s1 + a2_ * (input - state_.s2);
    const float v2 = state_.s2 + a2_ * state_.s1 + a3_ * (input - state_.s2);
    
    // Update states
    state_.s1 = 2.0f * v1 - state_.s1;
    state_.s2 = 2.0f * v2 - state_.s2;
    
    // All three outputs
    lp = v2;
    bp = v1;
    hp = input - k_ * v1 - v2;
}

//==============================================================================
// TPT_FormantBank
//==============================================================================

TPT_FormantBank::TPT_FormantBank(float sample_rate)
    : sample_rate_(sample_rate)
{
    // Initialize all filters to bandpass mode
    for (auto& filter : filters_) {
        filter.setSampleRate(sample_rate);
        filter.setMode(TPT_SVF::Mode::BANDPASS);
    }
}

void TPT_FormantBank::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
    for (auto& filter : filters_) {
        filter.setSampleRate(sample_rate);
    }
}

void TPT_FormantBank::setFormants(const Formant* formants, size_t num_formants) {
    num_formants_ = std::min(num_formants, MAX_FORMANTS);
    
    for (size_t i = 0; i < num_formants_; ++i) {
        formants_[i] = formants[i];
    }
    
    updateFilters();
}

void TPT_FormantBank::shiftFormants(float shift_hz) {
    for (size_t i = 0; i < num_formants_; ++i) {
        formants_[i].frequency += shift_hz;
        // Clamp to valid range
        formants_[i].frequency = clampFrequency(formants_[i].frequency, sample_rate_);
    }
    updateFilters();
}

void TPT_FormantBank::scaleFormants(float scale) {
    for (size_t i = 0; i < num_formants_; ++i) {
        formants_[i].frequency *= scale;
        // Clamp to valid range
        formants_[i].frequency = clampFrequency(formants_[i].frequency, sample_rate_);
    }
    updateFilters();
}

void TPT_FormantBank::expandBandwidths(float expansion) {
    for (size_t i = 0; i < num_formants_; ++i) {
        formants_[i].bandwidth *= expansion;
        // Clamp to reasonable range
        formants_[i].bandwidth = std::clamp(formants_[i].bandwidth, 10.0f, 2000.0f);
    }
    updateFilters();
}

void TPT_FormantBank::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    // Copy input to output first
    std::copy(input, input + num_samples, output);
    
    // Process through each formant filter in cascade
    for (size_t i = 0; i < num_formants_; ++i) {
        filters_[i].processInPlace(output, num_samples);
    }
}

void TPT_FormantBank::processInPlace(float* buffer, size_t num_samples) {
    // Process through each formant filter in cascade
    for (size_t i = 0; i < num_formants_; ++i) {
        filters_[i].processInPlace(buffer, num_samples);
    }
}

void TPT_FormantBank::reset() {
    for (size_t i = 0; i < num_formants_; ++i) {
        filters_[i].reset();
    }
}

void TPT_FormantBank::updateFilters() {
    for (size_t i = 0; i < num_formants_; ++i) {
        // Convert formant spec to filter parameters
        const float freq = formants_[i].frequency;
        const float q = formants_[i].getQ();
        
        // Set parameters (TPT SVF handles clamping internally)
        filters_[i].setParameters(freq, q, 0.0f);
        
        // Note: amplitude is handled by output scaling in the cascade
        // For now, we process at unity gain and handle overall gain elsewhere
    }
}

} // namespace dsp
} // namespace vocal_synthesis

