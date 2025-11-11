#pragma once

#include <cstddef>
#include <random>

namespace vocal_synthesis {
namespace dsp {

/**
 * @brief Corporeal Noise Layers - Physical body failure sounds
 * 
 * CRITICAL CREATIVE REQUIREMENT (per Story Teller peer review):
 * "We need ADDITIVE SYNTHESIS, not just filtering. A dedicated noise generator
 *  that doesn't process the anchor audio, but is TRIGGERED by it:
 *  - Wet Clicks & Pops (Zombie's wet mouth sounds)
 *  - Raspy Inhalation (dry/empty or fluid-filled lungs)
 *  - Bone Creaks (Werewolf's jaw distension)"
 * 
 * THIS IS THE KEY INNOVATION:
 * - NOT filtering the audio signal (that's just EQ!)
 * - ADDITIVE synthesis triggered/synchronized with speech
 * - Simulates physical processes of body failure
 * - Creates "termites" not just "wall paint"
 * 
 * CREATIVE GOAL: "Corrupted flesh, not digital effects" (Story Teller)
 * 
 * NOISE TYPES:
 * 1. **Wet Clicks** - Zombie mouth sounds (saliva, decay)
 * 2. **Wet Pops** - Lip/tongue separation sounds
 * 3. **Raspy Inhale** - Damaged lung sounds (fluid/empty)
 * 4. **Bone Creaks** - Skeletal sounds (jaw, neck movement)
 * 5. **Mucus Rattle** - Throat/lung fluid movement
 * 
 * USAGE:
 *   CorporealNoise zombie_body(sample_rate);
 *   zombie_body.setWetClicks(0.7f);  // 70% wet mouth
 *   zombie_body.setRaspyInhale(0.5f);
 *   zombie_body.processAndMix(audio_buffer, num_samples);
 *   // Result: Speech + physical body failure sounds layered
 */
class CorporealNoise {
public:
    /**
     * @brief Noise type
     */
    enum class NoiseType {
        WET_CLICK,      ///< Wet mouth click (Zombie)
        WET_POP,        ///< Lip/tongue pop (Zombie)
        RASPY_INHALE,   ///< Damaged lung inhale (Zombie/Vampire)
        BONE_CREAK,     ///< Skeletal creak (Werewolf/Lich)
        MUCUS_RATTLE    ///< Throat fluid rattle (Zombie/Ghoul)
    };
    
    /**
     * @brief Constructor
     * @param sample_rate Sample rate in Hz
     * @param seed Random seed
     */
    explicit CorporealNoise(float sample_rate = 48000.0f, uint32_t seed = 42);
    
    /**
     * @brief Set sample rate
     */
    void setSampleRate(float sample_rate);
    
    /**
     * @brief Set noise amounts (all [0, 1])
     */
    void setWetClicks(float amount);
    void setWetPops(float amount);
    void setRaspyInhale(float amount);
    void setBoneCreaks(float amount);
    void setMucusRattle(float amount);
    
    /**
     * @brief Set all zombie-specific noises at once
     * @param intensity Overall zombie decay intensity [0, 1]
     */
    void setZombieProfile(float intensity);
    
    /**
     * @brief Set all werewolf-specific noises at once
     * @param intensity Overall werewolf transformation [0, 1]
     */
    void setWerewolfProfile(float intensity);
    
    /**
     * @brief Process and MIX with input (additive synthesis!)
     * 
     * CRITICAL: This ADDS noise to the signal, doesn't filter it!
     * 
     * @param output Output buffer (input + noise)
     * @param input Input buffer (original audio)
     * @param num_samples Number of samples
     */
    void processAndMix(
        float* output,
        const float* input,
        size_t num_samples
    );
    
    /**
     * @brief Process in-place (adds noise to buffer)
     * @param buffer Input/output buffer
     * @param num_samples Number of samples
     */
    void processInPlace(float* buffer, size_t num_samples);
    
    /**
     * @brief Reset internal state
     */
    void reset();
    
private:
    float sample_rate_;
    
    // Noise amounts
    float wet_click_amount_ = 0.0f;
    float wet_pop_amount_ = 0.0f;
    float raspy_inhale_amount_ = 0.0f;
    float bone_creak_amount_ = 0.0f;
    float mucus_rattle_amount_ = 0.0f;
    
    // Random state
    std::mt19937 rng_;
    std::uniform_real_distribution<float> uniform_{0.0f, 1.0f};
    std::normal_distribution<float> gaussian_{0.0f, 1.0f};
    
    // Detection state (for triggering noises)
    float prev_sample_ = 0.0f;
    float envelope_follower_ = 0.0f;
    int samples_since_trigger_ = 0;
    
    /**
     * @brief Detect speech events (for triggering noises)
     * @param sample Current audio sample
     * @return true if noise should be triggered
     */
    bool detectTrigger(float sample);
    
    /**
     * @brief Generate wet click sound
     * @return Click sample
     */
    float generateWetClick();
    
    /**
     * @brief Generate wet pop sound
     * @return Pop sample
     */
    float generateWetPop();
    
    /**
     * @brief Generate raspy inhale sound
     * @return Raspy sample
     */
    float generateRaspyInhale();
    
    /**
     * @brief Generate bone creak sound
     * @return Creak sample
     */
    float generateBoneCreak();
    
    /**
     * @brief Generate mucus rattle sound
     * @return Rattle sample
     */
    float generateMucusRattle();
};

} // namespace dsp
} // namespace vocal_synthesis

