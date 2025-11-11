#include "vocal_synthesis/dsp/subliminal_audio.hpp"
#include <algorithm>

namespace vocal_synthesis {
namespace dsp {

namespace {
    constexpr float PI = 3.14159265358979323846f;
    constexpr float TWO_PI = 2.0f * PI;
}

SubliminalAudio::SubliminalAudio(float sample_rate)
    : sample_rate_(sample_rate)
{
}

void SubliminalAudio::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void SubliminalAudio::setLayer(LayerType layer, float intensity) {
    intensity = std::clamp(intensity, 0.0f, 1.0f);
    
    switch (layer) {
        case LayerType::HEARTBEAT:
            heartbeat_intensity_ = intensity;
            break;
        case LayerType::BLOOD_FLOW:
            blood_flow_intensity_ = intensity;
            break;
        case LayerType::BREATH_CYCLE:
            breath_intensity_ = intensity;
            break;
        case LayerType::ORGANIC_HUM:
            organic_hum_intensity_ = intensity;
            break;
    }
}

void SubliminalAudio::setHeartbeatRate(float bpm) {
    heartbeat_bpm_ = std::clamp(bpm, 40.0f, 120.0f);
}

void SubliminalAudio::processBuffer(
    float* output,
    const float* input,
    size_t num_samples
) {
    for (size_t i = 0; i < num_samples; ++i) {
        float sample = input[i];
        
        // Add subliminal layers (very quiet!)
        if (heartbeat_intensity_ > 0.001f) {
            sample += generateHeartbeat() * heartbeat_intensity_ * 0.05f;  // Max 5% of signal
        }
        
        if (blood_flow_intensity_ > 0.001f) {
            sample += generateBloodFlow() * blood_flow_intensity_ * 0.03f;  // Max 3% of signal
        }
        
        if (breath_intensity_ > 0.001f) {
            sample += generateBreath() * breath_intensity_ * 0.04f;  // Max 4% of signal
        }
        
        if (organic_hum_intensity_ > 0.001f) {
            sample += generateOrganicHum() * organic_hum_intensity_ * 0.02f;  // Max 2% of signal
        }
        
        output[i] = sample;
    }
}

void SubliminalAudio::processInPlace(float* buffer, size_t num_samples) {
    processBuffer(buffer, buffer, num_samples);
}

void SubliminalAudio::reset() {
    heartbeat_phase_ = 0.0f;
    blood_flow_phase_ = 0.0f;
    breath_phase_ = 0.0f;
}

float SubliminalAudio::generateHeartbeat() {
    // Generate heartbeat pulse (LUB-dub pattern)
    const float beat_freq = heartbeat_bpm_ / 60.0f;  // Convert BPM to Hz
    
    heartbeat_phase_ += TWO_PI * beat_freq / sample_rate_;
    if (heartbeat_phase_ >= TWO_PI) {
        heartbeat_phase_ -= TWO_PI;
    }
    
    // Two-part pulse (LUB at 0, dub at 0.4)
    const float phase_normalized = heartbeat_phase_ / TWO_PI;
    float pulse = 0.0f;
    
    if (phase_normalized < 0.1f) {
        // LUB (stronger)
        pulse = std::sin(phase_normalized * TWO_PI * 5.0f);
    } else if (phase_normalized > 0.4f && phase_normalized < 0.5f) {
        // dub (weaker)
        pulse = std::sin((phase_normalized - 0.4f) * TWO_PI * 5.0f) * 0.6f;
    }
    
    return pulse;
}

float SubliminalAudio::generateBloodFlow() {
    // Whooshing, rhythmic sound synchronized with heartbeat
    const float flow_freq = heartbeat_bpm_ / 60.0f;
    
    blood_flow_phase_ += TWO_PI * flow_freq / sample_rate_;
    if (blood_flow_phase_ >= TWO_PI) {
        blood_flow_phase_ -= TWO_PI;
    }
    
    // Smoother than heartbeat, more of a whoosh
    const float whoosh = std::sin(blood_flow_phase_) * 0.5f + 0.5f;  // [0, 1]
    return whoosh * std::sin(blood_flow_phase_ * 3.0f) * 0.3f;  // Add harmonics
}

float SubliminalAudio::generateBreath() {
    // Very slow breathing cycle (0.2 Hz = 12 breaths/minute)
    constexpr float BREATH_RATE = 0.2f;
    
    breath_phase_ += TWO_PI * BREATH_RATE / sample_rate_;
    if (breath_phase_ >= TWO_PI) {
        breath_phase_ -= TWO_PI;
    }
    
    // Asymmetric (inhale faster than exhale)
    const float phase_norm = breath_phase_ / TWO_PI;
    if (phase_norm < 0.4f) {
        // Inhale
        return std::sin(phase_norm * TWO_PI * 1.25f);
    } else {
        // Exhale (longer, smoother)
        return std::sin((phase_norm - 0.4f) * TWO_PI * 0.833f) * 0.7f;
    }
}

float SubliminalAudio::generateOrganicHum() {
    // Very low frequency presence (sub-bass hum)
    // Adds body without being heard directly
    constexpr float HUM_FREQ = 35.0f;  // Hz (just above infrasound)
    
    static float hum_phase = 0.0f;
    hum_phase += TWO_PI * HUM_FREQ / sample_rate_;
    if (hum_phase >= TWO_PI) {
        hum_phase -= TWO_PI;
    }
    
    return std::sin(hum_phase);
}

} // namespace dsp
} // namespace vocal_synthesis

