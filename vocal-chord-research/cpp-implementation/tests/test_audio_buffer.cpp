/**
 * @file test_audio_buffer.cpp
 * @brief Comprehensive unit tests for AudioBuffer
 * 
 * Test Philosophy (per user mandate):
 * - 100% real tests (NO mock tests)
 * - 100% must pass
 * - Test ALL edge cases
 * - Production-quality only
 */

#include "vocal_synthesis/audio_buffer.hpp"
#include <gtest/gtest.h>
#include <cmath>
#include <filesystem>
#include <numbers>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace vocal_synthesis;
namespace fs = std::filesystem;

class AudioBufferTest : public ::testing::Test {
protected:
    static constexpr float EPSILON = 1.0e-6f;
    static constexpr uint32_t SAMPLE_RATE = 48000;
    
    // Test data directory
    const std::string test_data_dir_ = "test_output/audio_buffer/";
    
    void SetUp() override {
        // Create test output directory
        fs::create_directories(test_data_dir_);
    }
};

//==============================================================================
// CONSTRUCTION TESTS
//==============================================================================

TEST_F(AudioBufferTest, DefaultConstruction) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    
    EXPECT_EQ(buffer.sampleRate(), SAMPLE_RATE);
    EXPECT_EQ(buffer.numChannels(), 1);
    EXPECT_EQ(buffer.size(), 0);
    EXPECT_EQ(buffer.numFrames(), 0);
    EXPECT_FLOAT_EQ(buffer.durationSeconds(), 0.0f);
}

TEST_F(AudioBufferTest, ConstructionWithSamples) {
    std::vector<float> samples = {0.1f, 0.2f, 0.3f, 0.4f};
    AudioBuffer buffer(samples, SAMPLE_RATE, 2);  // 2 channels
    
    EXPECT_EQ(buffer.sampleRate(), SAMPLE_RATE);
    EXPECT_EQ(buffer.numChannels(), 2);
    EXPECT_EQ(buffer.size(), 4);
    EXPECT_EQ(buffer.numFrames(), 2);
}

TEST_F(AudioBufferTest, InvalidSampleRate) {
    EXPECT_THROW(AudioBuffer(0, 1), std::invalid_argument);
}

TEST_F(AudioBufferTest, InvalidChannelCount) {
    EXPECT_THROW(AudioBuffer(SAMPLE_RATE, 0), std::invalid_argument);
    EXPECT_THROW(AudioBuffer(SAMPLE_RATE, 17), std::invalid_argument);
}

TEST_F(AudioBufferTest, MismatchedSamplesAndChannels) {
    std::vector<float> samples = {0.1f, 0.2f, 0.3f};  // 3 samples
    // 2 channels requires even number of samples
    EXPECT_THROW(AudioBuffer(samples, SAMPLE_RATE, 2), std::invalid_argument);
}

//==============================================================================
// BASIC OPERATIONS
//==============================================================================

TEST_F(AudioBufferTest, Resize) {
    AudioBuffer buffer(SAMPLE_RATE, 2);
    
    buffer.resize(100);  // 100 frames
    
    EXPECT_EQ(buffer.numFrames(), 100);
    EXPECT_EQ(buffer.size(), 200);  // 100 frames * 2 channels
}

TEST_F(AudioBufferTest, Clear) {
    std::vector<float> samples = {1.0f, 2.0f, 3.0f, 4.0f};
    AudioBuffer buffer(samples, SAMPLE_RATE, 1);
    
    buffer.clear();
    
    for (size_t i = 0; i < buffer.size(); ++i) {
        EXPECT_FLOAT_EQ(buffer.data()[i], 0.0f);
    }
}

TEST_F(AudioBufferTest, Duration) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(SAMPLE_RATE);  // 1 second worth
    
    EXPECT_NEAR(buffer.durationSeconds(), 1.0f, 0.001f);
}

//==============================================================================
// ANALYSIS FUNCTIONS
//==============================================================================

TEST_F(AudioBufferTest, GetRMS_Silence) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(1000);
    buffer.clear();
    
    EXPECT_FLOAT_EQ(buffer.rms(), 0.0f);
}

TEST_F(AudioBufferTest, GetRMS_UnitySine) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(1000);
    
    // Generate sine wave with amplitude 1.0
    for (size_t i = 0; i < buffer.size(); ++i) {
        buffer.data()[i] = std::sin(2.0f * static_cast<float>(M_PI) * 440.0f * static_cast<float>(i) / SAMPLE_RATE);
    }
    
    // RMS of sine wave = amplitude / sqrt(2) ≈ 0.707
    EXPECT_NEAR(buffer.rms(), 0.707f, 0.01f);
}

TEST_F(AudioBufferTest, GetPeak) {
    std::vector<float> samples = {0.1f, -0.5f, 0.3f, -0.8f, 0.2f};
    AudioBuffer buffer(samples, SAMPLE_RATE, 1);
    
    EXPECT_FLOAT_EQ(buffer.peak(), 0.8f);
}

TEST_F(AudioBufferTest, GetPeak_Empty) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    EXPECT_FLOAT_EQ(buffer.peak(), 0.0f);
}

//==============================================================================
// NORMALIZE
//==============================================================================

TEST_F(AudioBufferTest, Normalize_ToPeak) {
    std::vector<float> samples = {0.1f, -0.2f, 0.3f, -0.4f};
    AudioBuffer buffer(samples, SAMPLE_RATE, 1);
    
    buffer.normalize(1.0f);
    
    // Peak should now be 1.0
    EXPECT_NEAR(buffer.peak(), 1.0f, EPSILON);
    
    // Relative amplitudes preserved
    EXPECT_NEAR(buffer.data()[0] / buffer.data()[1], 0.1f / (-0.2f), 0.01f);
}

TEST_F(AudioBufferTest, Normalize_Silence) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(100);
    buffer.clear();
    
    // Should not crash on silent signal
    EXPECT_NO_THROW(buffer.normalize(1.0f));
    
    // Should remain silent
    EXPECT_FLOAT_EQ(buffer.peak(), 0.0f);
}

//==============================================================================
// FILE I/O
//==============================================================================

TEST_F(AudioBufferTest, DISABLED_SaveAndLoadWAV) {
    // DISABLED: File I/O not enabled in build (VOCAL_ENABLE_FILE_IO=OFF)
    // Enable with: cmake -D VOCAL_ENABLE_FILE_IO=ON ..
    
    // Create buffer with known content
    std::vector<float> samples;
    for (int i = 0; i < 1000; ++i) {
        samples.push_back(static_cast<float>(std::sin(2.0f * static_cast<float>(M_PI) * 440.0f * static_cast<float>(i) / SAMPLE_RATE)));
    }
    AudioBuffer original(samples, SAMPLE_RATE, 1);
    
    // Save to file
    std::string filepath = test_data_dir_ + "test_audio.wav";
    original.saveToFile(filepath);
    
    // Load from file
    AudioBuffer loaded = AudioBuffer::loadFromFile(filepath);
    
    // Verify
    EXPECT_EQ(loaded.sampleRate(), original.sampleRate());
    EXPECT_EQ(loaded.numChannels(), original.numChannels());
    EXPECT_EQ(loaded.numFrames(), original.numFrames());
    
    // Samples should be close (some precision loss from 16-bit PCM)
    for (size_t i = 0; i < loaded.size(); ++i) {
        EXPECT_NEAR(loaded.data()[i], original.data()[i], 0.01f);
    }
}

TEST_F(AudioBufferTest, LoadNonexistentFile) {
    EXPECT_THROW(AudioBuffer::loadFromFile("nonexistent_file.wav"), std::runtime_error);
}

//==============================================================================
// MIXING
//==============================================================================

TEST_F(AudioBufferTest, Mix_SameLength) {
    std::vector<float> samples1 = {1.0f, 2.0f, 3.0f, 4.0f};
    std::vector<float> samples2 = {0.5f, 1.0f, 1.5f, 2.0f};
    
    AudioBuffer buffer1(samples1, SAMPLE_RATE, 1);
    AudioBuffer buffer2(samples2, SAMPLE_RATE, 1);
    
    buffer1.mixFrom(buffer2, 1.0f);
    
    EXPECT_FLOAT_EQ(buffer1.data()[0], 1.5f);
    EXPECT_FLOAT_EQ(buffer1.data()[1], 3.0f);
    EXPECT_FLOAT_EQ(buffer1.data()[2], 4.5f);
    EXPECT_FLOAT_EQ(buffer1.data()[3], 6.0f);
}

TEST_F(AudioBufferTest, Mix_WithGain) {
    std::vector<float> samples1 = {1.0f, 2.0f};
    std::vector<float> samples2 = {1.0f, 1.0f};
    
    AudioBuffer buffer1(samples1, SAMPLE_RATE, 1);
    AudioBuffer buffer2(samples2, SAMPLE_RATE, 1);
    
    buffer1.mixFrom(buffer2, 0.5f);  // Mix at half gain
    
    EXPECT_FLOAT_EQ(buffer1.data()[0], 1.5f);
    EXPECT_FLOAT_EQ(buffer1.data()[1], 2.5f);
}

TEST_F(AudioBufferTest, Mix_DifferentLengths) {
    std::vector<float> samples1 = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    std::vector<float> samples2 = {1.0f, 1.0f, 1.0f};
    
    AudioBuffer buffer1(samples1, SAMPLE_RATE, 1);
    AudioBuffer buffer2(samples2, SAMPLE_RATE, 1);
    
    buffer1.mixFrom(buffer2, 1.0f);
    
    // First 3 samples mixed
    EXPECT_FLOAT_EQ(buffer1.data()[0], 2.0f);
    EXPECT_FLOAT_EQ(buffer1.data()[1], 3.0f);
    EXPECT_FLOAT_EQ(buffer1.data()[2], 4.0f);
    
    // Last 2 samples unchanged
    EXPECT_FLOAT_EQ(buffer1.data()[3], 4.0f);
    EXPECT_FLOAT_EQ(buffer1.data()[4], 5.0f);
}

TEST_F(AudioBufferTest, Mix_MismatchedSampleRates) {
    AudioBuffer buffer1(48000, 1);
    AudioBuffer buffer2(44100, 1);
    
    EXPECT_THROW(buffer1.mixFrom(buffer2, 1.0f), std::invalid_argument);
}

//==============================================================================
// APPEND
//==============================================================================

TEST_F(AudioBufferTest, Append) {
    std::vector<float> samples1 = {1.0f, 2.0f};
    std::vector<float> samples2 = {3.0f, 4.0f};
    
    AudioBuffer buffer1(samples1, SAMPLE_RATE, 1);
    AudioBuffer buffer2(samples2, SAMPLE_RATE, 1);
    
    buffer1.append(buffer2);
    
    EXPECT_EQ(buffer1.size(), 4);
    EXPECT_FLOAT_EQ(buffer1.data()[0], 1.0f);
    EXPECT_FLOAT_EQ(buffer1.data()[1], 2.0f);
    EXPECT_FLOAT_EQ(buffer1.data()[2], 3.0f);
    EXPECT_FLOAT_EQ(buffer1.data()[3], 4.0f);
}

//==============================================================================
// EXTRACT RANGE
//==============================================================================

TEST_F(AudioBufferTest, ExtractRange) {
    std::vector<float> samples = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    AudioBuffer buffer(samples, SAMPLE_RATE, 1);
    
    AudioBuffer extracted = buffer.slice(1, 4);  // Extract frames 1-4 (end exclusive)
    
    EXPECT_EQ(extracted.numFrames(), 3);
    EXPECT_FLOAT_EQ(extracted.data()[0], 2.0f);
    EXPECT_FLOAT_EQ(extracted.data()[1], 3.0f);
    EXPECT_FLOAT_EQ(extracted.data()[2], 4.0f);
}

TEST_F(AudioBufferTest, ExtractRange_OutOfBounds) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(5);
    
    // Out of bounds start returns empty buffer (no exception)
    AudioBuffer extracted = buffer.slice(10, 12);
    EXPECT_EQ(extracted.numFrames(), 0);
}

TEST_F(AudioBufferTest, ExtractRange_BeyondEnd) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(5);
    
    // Request end beyond available - should clamp to end
    AudioBuffer extracted = buffer.slice(3, 100);
    
    EXPECT_EQ(extracted.numFrames(), 2);  // Only 2 frames available (3 to 5)
}

//==============================================================================
// GAIN
//==============================================================================

TEST_F(AudioBufferTest, ApplyGain) {
    std::vector<float> samples = {1.0f, 2.0f, 3.0f, 4.0f};
    AudioBuffer buffer(samples, SAMPLE_RATE, 1);
    
    buffer.applyGain(0.5f);
    
    EXPECT_FLOAT_EQ(buffer.data()[0], 0.5f);
    EXPECT_FLOAT_EQ(buffer.data()[1], 1.0f);
    EXPECT_FLOAT_EQ(buffer.data()[2], 1.5f);
    EXPECT_FLOAT_EQ(buffer.data()[3], 2.0f);
}

//==============================================================================
// FADES
//==============================================================================

// NOTE: Fade functionality removed from AudioBuffer (not needed for core DSP)
// If needed in future, implement as separate DSP utility

/*
TEST_F(AudioBufferTest, FadeIn_Linear) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(5);
    std::fill(buffer.data(), buffer.data() + buffer.size(), 1.0f);
    
    buffer.fade(AudioBuffer::FadeType::LINEAR_IN, 5);
    
    // Should be 0 at start, 1 at end
    EXPECT_NEAR(buffer.data()[0], 0.0f, EPSILON);
    EXPECT_NEAR(buffer.data()[4], 1.0f, EPSILON);
    
    // Middle values should be interpolated
    EXPECT_NEAR(buffer.data()[2], 0.5f, 0.01f);
}

TEST_F(AudioBufferTest, FadeOut_Linear) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    buffer.resize(5);
    std::fill(buffer.data(), buffer.data() + buffer.size(), 1.0f);
    
    buffer.fade(AudioBuffer::FadeType::LINEAR_OUT, 5);
    
    // Should be 1 at start, 0 at end
    EXPECT_NEAR(buffer.data()[0], 1.0f, EPSILON);
    EXPECT_NEAR(buffer.data()[4], 0.0f, EPSILON);
}
*/

//==============================================================================
// EDGE CASES
//==============================================================================

TEST_F(AudioBufferTest, EmptyBuffer_Operations) {
    AudioBuffer buffer(SAMPLE_RATE, 1);
    
    // These should not crash
    EXPECT_NO_THROW(buffer.clear());
    EXPECT_NO_THROW(buffer.normalize());
    EXPECT_EQ(buffer.rms(), 0.0f);
    EXPECT_EQ(buffer.peak(), 0.0f);
}

TEST_F(AudioBufferTest, Multichannel) {
    AudioBuffer buffer(SAMPLE_RATE, 2);
    buffer.resize(100);  // 100 frames, 2 channels = 200 samples
    
    EXPECT_EQ(buffer.numFrames(), 100);
    EXPECT_EQ(buffer.size(), 200);
}

//==============================================================================
// MAIN TEST RUNNER
//==============================================================================

// main() provided by gtest_main library

