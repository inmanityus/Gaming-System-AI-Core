#include "vocal_synthesis/dsp/corporeal_noise.hpp"
#include <algorithm>
#include <cmath>
#include <vector>

namespace vocal_synthesis {
namespace dsp {

CorporealNoise::CorporealNoise(float sample_rate, uint32_t seed)
    : sample_rate_(sample_rate)
    , rng_(seed)
{
}

void CorporealNoise::setSampleRate(float sample_rate) {
    sample_rate_ = sample_rate;
}

void CorporealNoise::setWetClicks(float amount) {
    wet_click_amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void CorporealNoise::setWetPops(float amount) {
    wet_pop_amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void CorporealNoise::setRaspyInhale(float amount) {
    raspy_inhale_amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void CorporealNoise::setBoneCreaks(float amount) {
    bone_creak_amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void CorporealNoise::setMucusRattle(float amount) {
    mucus_rattle_amount_ = std::clamp(amount, 0.0f, 1.0f);
}

void CorporealNoise::setZombieProfile(float intensity) {
    intensity = std::clamp(intensity, 0.0f, 1.0f);
    
    wet_click_amount_ = intensity * 0.8f;
    wet_pop_amount_ = intensity * 0.7f;
    raspy_inhale_amount_ = intensity * 0.5f;
    bone_creak_amount_ = intensity * 0.2f;
    mucus_rattle_amount_ = intensity * 0.9f;
}

void CorporealNoise::setWerewolfProfile(float intensity) {
    intensity = std::clamp(intensity, 0.0f, 1.0f);
    
    wet_click_amount_ = intensity * 0.3f;
    wet_pop_amount_ = intensity * 0.3f;
    raspy_inhale_amount_ = intensity * 0.4f;
    bone_creak_amount_ = intensity * 0.9f;
    mucus_rattle_amount_ = intensity * 0.2f;
}

void CorporealNoise::processAndMix(
    float* output,
    const float* input,
    size_t num_samples
) {
    for (size_t i = 0; i < num_samples; ++i) {
        const float input_sample = input[i];
        const bool trigger = detectTrigger(input_sample);
        
        float noise_sum = 0.0f;
        
        if (wet_click_amount_ > 0.01f && trigger && uniform_(rng_) < wet_click_amount_ * 0.1f) {
            noise_sum += generateWetClick() * wet_click_amount_;
        }
        
        if (wet_pop_amount_ > 0.01f && trigger && uniform_(rng_) < wet_pop_amount_ * 0.05f) {
            noise_sum += generateWetPop() * wet_pop_amount_;
        }
        
        if (raspy_inhale_amount_ > 0.01f) {
            noise_sum += generateRaspyInhale() * raspy_inhale_amount_;
        }
        
        if (bone_creak_amount_ > 0.01f && trigger && uniform_(rng_) < bone_creak_amount_ * 0.08f) {
            noise_sum += generateBoneCreak() * bone_creak_amount_;
        }
        
        if (mucus_rattle_amount_ > 0.01f) {
            noise_sum += generateMucusRattle() * mucus_rattle_amount_;
        }
        
        output[i] = input_sample + noise_sum * 0.15f;
    }
}

void CorporealNoise::processInPlace(float* buffer, size_t num_samples) {
    std::vector<float> temp(buffer, buffer + num_samples);
    processAndMix(buffer, temp.data(), num_samples);
}

void CorporealNoise::reset() {
    prev_sample_ = 0.0f;
    envelope_follower_ = 0.0f;
    samples_since_trigger_ = 0;
}

bool CorporealNoise::detectTrigger(float sample) {
    const float abs_sample = std::abs(sample);
    const float attack = 0.01f;
    const float release = 0.001f;
    
    if (abs_sample > envelope_follower_) {
        envelope_follower_ += attack * (abs_sample - envelope_follower_);
    } else {
        envelope_follower_ += release * (abs_sample - envelope_follower_);
    }
    
    const bool onset = (abs_sample > prev_sample_ * 1.5f) && (abs_sample > 0.1f);
    
    prev_sample_ = abs_sample;
    samples_since_trigger_++;
    
    if (onset && samples_since_trigger_ > 1000) {
        samples_since_trigger_ = 0;
        return true;
    }
    
    return false;
}

float CorporealNoise::generateWetClick() {
    return gaussian_(rng_) * 0.3f;
}

float CorporealNoise::generateWetPop() {
    return gaussian_(rng_) * 0.5f;
}

float CorporealNoise::generateRaspyInhale() {
    return gaussian_(rng_) * 0.1f;
}

float CorporealNoise::generateBoneCreak() {
    return gaussian_(rng_) * 0.4f;
}

float CorporealNoise::generateMucusRattle() {
    return gaussian_(rng_) * 0.08f;
}

} // namespace dsp
} // namespace vocal_synthesis

