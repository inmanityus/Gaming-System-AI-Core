#include "vocal_synthesis/dsp/pitch_stabilizer.hpp"
#include <algorithm>
#include <cmath>
#include <vector>

namespace vocal_synthesis {
namespace dsp {

namespace {
    constexpr float PI = 3.14159265358979323846f;
}

PitchStabilizer::PitchStabilizer(float sample_rate)
    : sample_rate_(sample_rate)
{
    // Initialize pitch buffer for autocorrelation
    // Buffer size for lowest expected pitch (50 Hz at 48kHz = 960 samples)
    pitch_buffer_.resize(static_cast<size_t>(sample_rate / 50.0f));
    
    updateSmoothingCoeff();
}

void PitchStabilizer::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
    pitch_buffer_.resize(static_cast<size_t>(sample_rate / 50.0f));
    updateSmoothingCoeff();
}

void PitchStabilizer::setStabilization(float amount) {
    stabilization_amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void PitchStabilizer::setTimeConstant(float time_ms) {
    time_constant_ms_ = std::clamp(time_ms, 1.0f, 500.0f);
    updateSmoothingCoeff();
}

void PitchStabilizer::updateSmoothingCoeff() {
    // Exponential smoothing coefficient for pitch contour
    // Shorter time = removes fast vibrato (unnatural)
    // Longer time = preserves prosody (natural)
    const float tau_seconds = time_constant_ms_ * 0.001f;
    smooth_alpha_ = 1.0f - std::exp(-1.0f / (tau_seconds * sample_rate_));
    smooth_alpha_ = std::clamp(smooth_alpha_, 0.0f, 1.0f);
}

void PitchStabilizer::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    if (stabilization_amount_ < 0.01f) {
        // No stabilization - pass through
        std::copy(input, input + num_samples, output);
        return;
    }
    
    // Detect current pitch
    const float current_pitch = detectPitch(input, num_samples);
    
    // Smooth pitch (removes vibrato)
    const float target_pitch = smoothPitch(current_pitch);
    
    // Apply pitch correction if needed
    if (current_pitch > 0.0f && target_pitch > 0.0f) {
        std::copy(input, input + num_samples, output);
        applyPitchShift(output, num_samples, current_pitch, target_pitch);
    } else {
        // Unvoiced or detection failed - pass through
        std::copy(input, input + num_samples, output);
    }
}

void PitchStabilizer::processInPlace(float* buffer, size_t num_samples) {
    processBuffer(buffer, buffer, num_samples);
}

void PitchStabilizer::reset() {
    std::fill(pitch_buffer_.begin(), pitch_buffer_.end(), 0.0f);
    pitch_buffer_pos_ = 0;
    detected_pitch_ = 0.0f;
    smoothed_pitch_ = 0.0f;
}

float PitchStabilizer::detectPitch(const float* input, size_t num_samples) {
    // Simplified pitch detection via zero-crossing rate
    // (Real implementation would use YIN, autocorrelation, or cepstrum)
    
    int zero_crossings = 0;
    float prev_sample = pitch_buffer_[pitch_buffer_pos_];
    
    for (size_t i = 0; i < num_samples; ++i) {
        // Update circular buffer
        pitch_buffer_[pitch_buffer_pos_] = input[i];
        pitch_buffer_pos_ = (pitch_buffer_pos_ + 1) % pitch_buffer_.size();
        
        // Count zero crossings
        if ((prev_sample <= 0.0f && input[i] > 0.0f) ||
            (prev_sample >= 0.0f && input[i] < 0.0f)) {
            zero_crossings++;
        }
        
        prev_sample = input[i];
    }
    
    if (zero_crossings < 2) {
        return 0.0f;  // Unvoiced or insufficient data
    }
    
    // Estimate F0 from zero-crossing rate
    // Each period has 2 zero crossings
    const float periods_per_buffer = static_cast<float>(zero_crossings) / 2.0f;
    const float buffer_duration = static_cast<float>(num_samples) / sample_rate_;
    const float estimated_f0 = periods_per_buffer / buffer_duration;
    
    // Clamp to reasonable voice range
    return std::clamp(estimated_f0, 50.0f, 500.0f);
}

float PitchStabilizer::smoothPitch(float current_pitch) {
    if (current_pitch <= 0.0f) {
        return smoothed_pitch_;  // Unvoiced - maintain previous
    }
    
    if (smoothed_pitch_ <= 0.0f) {
        // First voiced frame - initialize
        smoothed_pitch_ = current_pitch;
        return smoothed_pitch_;
    }
    
    // Exponential smoothing (removes vibrato)
    smoothed_pitch_ = smoothed_pitch_ + smooth_alpha_ * (current_pitch - smoothed_pitch_);
    
    return smoothed_pitch_;
}

void PitchStabilizer::applyPitchShift(
    float* buffer,
    size_t num_samples,
    float current_pitch,
    float target_pitch
) {
    // Calculate pitch shift ratio
    const float pitch_ratio = target_pitch / current_pitch;
    
    // Calculate shift amount (cents)
    const float shift_semitones = 12.0f * std::log2(pitch_ratio);
    
    // Apply only if significant AND stabilization is active
    const float shift_with_amount = shift_semitones * stabilization_amount_;
    
    if (std::abs(shift_with_amount) < 0.1f) {
        return;  // Shift too small, don't bother
    }
    
    // Simplified pitch shift using time-domain method
    // (Real implementation would use phase vocoder or PSOLA)
    
    // For now, implement a simple approximation:
    // - Apply slight phase modulation to shift perceived pitch
    // - This is a placeholder for full pitch shifting algorithm
    
    // TODO: Implement full pitch shifting algorithm
    // Options:
    // 1. Phase vocoder (STFT-based, high quality)
    // 2. PSOLA (time-domain, efficient)
    // 3. WSOLA (waveform similarity overlap-add)
    
    // Placeholder: Apply subtle amplitude modulation
    // (This doesn't actually shift pitch - just a placeholder!)
    const float modulation_rate = shift_semitones * 2.0f;  // Approximate
    for (size_t i = 0; i < num_samples; ++i) {
        const float phase = 2.0f * PI * modulation_rate * static_cast<float>(i) / sample_rate_;
        const float mod = 1.0f + 0.02f * stabilization_amount_ * std::sin(phase);
        buffer[i] *= mod;
    }
    
    // NOTE: This is a simplified placeholder!
    // Full implementation requires phase vocoder or PSOLA.
}

} // namespace dsp
} // namespace vocal_synthesis

