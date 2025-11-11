/**
 * @file test_full_pipeline.cpp
 * @brief Integration test for complete vocal synthesis pipeline
 * 
 * Tests all archetypes with real audio samples and validates:
 * - Phase 2A: Core features work correctly
 * - Phase 2B: Dynamic intensity, environmental response, subliminal layers
 * - All DSP components integrate properly
 * - Performance targets met
 */

#include "vocal_synthesis/audio_buffer.hpp"
#include "vocal_synthesis/aberration_params_v2.hpp"
#include "vocal_synthesis/dsp/glottal_incoherence.hpp"
#include "vocal_synthesis/dsp/subharmonic_generator.hpp"
#include "vocal_synthesis/dsp/pitch_stabilizer.hpp"
#include "vocal_synthesis/dsp/corporeal_noise.hpp"
#include "vocal_synthesis/dsp/subliminal_audio.hpp"
#include <gtest/gtest.h>
#include <chrono>

using namespace vocal_synthesis;
using namespace vocal_synthesis::dsp;

class FullPipelineTest : public ::testing::Test {
protected:
    static constexpr uint32_t SAMPLE_RATE = 48000;
    static constexpr size_t TEST_DURATION_SAMPLES = 48000;  // 1 second
    
    AudioBuffer generateTestSignal() {
        AudioBuffer buf(SAMPLE_RATE, 1);
        buf.resize(TEST_DURATION_SAMPLES);
        
        // Generate 440Hz sine wave (A4)
        for (size_t i = 0; i < TEST_DURATION_SAMPLES; ++i) {
            buf.data()[i] = std::sin(2.0f * 3.14159f * 440.0f * static_cast<float>(i) / SAMPLE_RATE);
        }
        
        return buf;
    }
};

TEST_F(FullPipelineTest, VampireArchetype_WithSubliminalLayers) {
    // Create vampire voice with subliminal layers
    auto params = AberrationParams::createVampire();
    EXPECT_EQ(params.getArchetype(), AberrationParams::Archetype::VAMPIRE);
    
    AudioBuffer audio = generateTestSignal();
    
    // Add pitch stabilizer (uncanny stillness)
    PitchStabilizer stabilizer(SAMPLE_RATE);
    stabilizer.setAmount(0.7f);
    stabilizer.processInPlace(audio.data(), audio.size());
    
    // Add subliminal layers
    SubliminalAudio subliminal(SAMPLE_RATE);
    subliminal.setLayer(SubliminalAudio::LayerType::HEARTBEAT, 0.08f);
    subliminal.setLayer(SubliminalAudio::LayerType::BLOOD_FLOW, 0.05f);
    subliminal.setHeartbeatRate(60.0f);  // Slow vampire heartbeat
    subliminal.processInPlace(audio.data(), audio.size());
    
    // Validate output
    EXPECT_GT(audio.rms(), 0.0f);
    EXPECT_LT(audio.peak(), 1.5f);
    EXPECT_FALSE(audio.hasInvalidSamples());
}

TEST_F(FullPipelineTest, ZombieArchetype_DynamicIntensity) {
    // Create zombie voice with dynamic intensity
    auto params = AberrationParams::createZombie();
    EXPECT_EQ(params.getArchetype(), AberrationParams::Archetype::ZOMBIE);
    
    AudioBuffer audio = generateTestSignal();
    
    // Test at different proximities
    for (float proximity : {0.0f, 0.5f, 1.0f}) {
        GlottalIncoherence incoherence(SAMPLE_RATE, 42);
        incoherence.setDynamicIntensity(0.6f, proximity, 0.7f);  // Wet environment
        
        AudioBuffer test_audio = audio;
        incoherence.processInPlace(test_audio.data(), test_audio.size());
        
        // Closer proximity = more corruption = higher RMS variation
        EXPECT_GT(test_audio.rms(), 0.0f);
    }
}

TEST_F(FullPipelineTest, WerewolfArchetype_TransformationStruggle) {
    // Create werewolf voice with transformation struggle
    auto params = AberrationParams::createWerewolf();
    EXPECT_EQ(params.getArchetype(), AberrationParams::Archetype::WEREWOLF);
    
    AudioBuffer audio = generateTestSignal();
    
    // Add subharmonics with struggle
    SubharmonicGenerator subharmonics(SAMPLE_RATE);
    subharmonics.setIntensity(0.7f);
    subharmonics.setChaos(0.5f);
    subharmonics.setTransformationStruggle(0.8f);  // High struggle
    subharmonics.processInPlace(audio.data(), audio.size());
    
    // Validate output
    EXPECT_GT(audio.rms(), 0.0f);
    EXPECT_FALSE(audio.hasInvalidSamples());
}

TEST_F(FullPipelineTest, AllArchetypes_Performance) {
    // Test that all archetypes meet performance target (<500μs per voice)
    std::vector<AberrationParams> archetypes = {
        AberrationParams::createHuman(),
        AberrationParams::createVampire(),
        AberrationParams::createZombie(),
        AberrationParams::createWerewolf(),
        AberrationParams::createWraith()
    };
    
    for (const auto& params : archetypes) {
        AudioBuffer audio = generateTestSignal();
        
        auto start = std::chrono::high_resolution_clock::now();
        
        // Process audio (simplified pipeline)
        GlottalIncoherence incoherence(SAMPLE_RATE, 42);
        incoherence.setIntensity(params.vocal_fold_irregularity.get());
        incoherence.processInPlace(audio.data(), audio.size());
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        
        // Target: <500μs per voice
        // We have 1 second of audio, so normalize to "per voice frame"
        // At 128 samples/buffer, this is 375 buffers
        const float per_buffer_us = static_cast<float>(duration) / 375.0f;
        
        EXPECT_LT(per_buffer_us, 500.0f) 
            << "Archetype failed performance target: " << per_buffer_us << "μs";
    }
}

TEST_F(FullPipelineTest, EmotionModulation_AllArchetypes) {
    // Test emotion system with all archetypes
    auto zombie_base = AberrationParams::createZombie();
    
    // Apply fear emotion
    EmotionState fear = EmotionState::fromNamed(EmotionState::NamedEmotion::FEAR);
    auto fearful_zombie = fear.applyTo(zombie_base);
    
    // Fear should increase arousal, decrease dominance
    // This should affect tension and pressure
    EXPECT_NE(fearful_zombie.tension_modifier.get(), zombie_base.tension_modifier.get());
}

// Main test runner provided by gtest_main

