/**
 * @file test_parameter_smoother.cpp
 * @brief Comprehensive unit tests for ParameterSmoother
 * 
 * Test Philosophy (per user mandate):
 * - 100% real tests (NO mock tests)
 * - 100% must pass
 * - Test ALL edge cases
 * - Validate mathematical correctness
 * - Production-quality only
 */

#include "vocal_synthesis/dsp/parameter_smoother.hpp"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>

using namespace vocal_synthesis::dsp;

// Test fixture for common setup
class ParameterSmootherTest : public ::testing::Test {
protected:
    static constexpr float SAMPLE_RATE = 48000.0f;
    static constexpr float TIME_CONSTANT_MS = 5.0f;
    static constexpr float EPSILON = 1.0e-6f;
};

//==============================================================================
// BASIC FUNCTIONALITY TESTS
//==============================================================================

TEST_F(ParameterSmootherTest, InitialState) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    // Should initialize to zero
    EXPECT_FLOAT_EQ(smoother.getValue(), 0.0f);
    EXPECT_FLOAT_EQ(smoother.getTarget(), 0.0f);
    EXPECT_TRUE(smoother.isSettled());
}

TEST_F(ParameterSmootherTest, SetTarget) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    EXPECT_FLOAT_EQ(smoother.getTarget(), 1.0f);
    EXPECT_FLOAT_EQ(smoother.getValue(), 0.0f);  // Current unchanged until processSample()
    EXPECT_FALSE(smoother.isSettled());
}

TEST_F(ParameterSmootherTest, ProcessSample_MovesTowardTarget) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    float prev = smoother.getValue();
    for (int i = 0; i < 10; ++i) {
        float current = smoother.processSample();
        
        // Should monotonically increase toward target
        EXPECT_GT(current, prev);
        EXPECT_LE(current, 1.0f);  // Should never overshoot
        
        prev = current;
    }
}

TEST_F(ParameterSmootherTest, ProcessSample_ConvergesToTarget) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    // Process enough samples to fully converge (5x time constant)
    const int num_samples = static_cast<int>(5.0f * TIME_CONSTANT_MS * SAMPLE_RATE / 1000.0f);
    
    float final_value = 0.0f;
    for (int i = 0; i < num_samples; ++i) {
        final_value = smoother.processSample();
    }
    
    // Should have converged to target
    EXPECT_NEAR(final_value, 1.0f, 0.01f);
    EXPECT_TRUE(smoother.isSettled(0.01f));
}

TEST_F(ParameterSmootherTest, Reset) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    smoother.processSample();
    smoother.processSample();
    
    EXPECT_NE(smoother.getValue(), 0.0f);
    
    smoother.reset(0.5f);
    
    EXPECT_FLOAT_EQ(smoother.getValue(), 0.5f);
    EXPECT_FLOAT_EQ(smoother.getTarget(), 0.5f);
    EXPECT_TRUE(smoother.isSettled());
}

TEST_F(ParameterSmootherTest, SkipToTarget) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    smoother.processSample();  // Start smoothing
    
    EXPECT_NE(smoother.getValue(), 1.0f);
    
    smoother.skipToTarget();
    
    EXPECT_FLOAT_EQ(smoother.getValue(), 1.0f);
    EXPECT_TRUE(smoother.isSettled());
}

//==============================================================================
// MATHEMATICAL CORRECTNESS TESTS
//==============================================================================

TEST_F(ParameterSmootherTest, TimeConstant_63Percent) {
    // After one time constant, should reach ~63% of target
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    // Process exactly one time constant worth of samples
    const int samples_per_tc = static_cast<int>(TIME_CONSTANT_MS * SAMPLE_RATE / 1000.0f);
    
    float value = 0.0f;
    for (int i = 0; i < samples_per_tc; ++i) {
        value = smoother.processSample();
    }
    
    // Should be approximately 63% of the way to target
    // 1 - exp(-1) ≈ 0.632
    EXPECT_NEAR(value, 0.632f, 0.05f);
}

TEST_F(ParameterSmootherTest, TimeConstant_95Percent) {
    // After 3 time constants, should reach ~95% of target
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    // Process 3x time constant
    const int samples_per_tc = static_cast<int>(TIME_CONSTANT_MS * SAMPLE_RATE / 1000.0f);
    
    float value = 0.0f;
    for (int i = 0; i < samples_per_tc * 3; ++i) {
        value = smoother.processSample();
    }
    
    // Should be approximately 95% of the way
    // 1 - exp(-3) ≈ 0.950
    EXPECT_NEAR(value, 0.950f, 0.05f);
}

TEST_F(ParameterSmootherTest, NegativeTarget) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.reset(1.0f);
    smoother.setTarget(-1.0f);
    
    float prev = smoother.getValue();
    for (int i = 0; i < 10; ++i) {
        float current = smoother.processSample();
        
        // Should monotonically decrease toward negative target
        EXPECT_LT(current, prev);
        EXPECT_GE(current, -1.0f);  // Should never overshoot
        
        prev = current;
    }
}

TEST_F(ParameterSmootherTest, NoOvershooting) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    // Process many samples
    for (int i = 0; i < 10000; ++i) {
        float value = smoother.processSample();
        
        // Should NEVER overshoot target
        EXPECT_LE(value, 1.0f);
    }
}

//==============================================================================
// SAMPLE RATE TESTS
//==============================================================================

TEST_F(ParameterSmootherTest, DifferentSampleRates_SameTimeConstant) {
    // Smoothers with different sample rates but same time constant
    // should reach similar percentages at equivalent time points
    
    ParameterSmoother smoother_48k(48000.0f, 5.0f);
    ParameterSmoother smoother_96k(96000.0f, 5.0f);
    
    smoother_48k.setTarget(1.0f);
    smoother_96k.setTarget(1.0f);
    
    // Process one time constant worth of samples for each
    const int samples_48k = static_cast<int>(5.0f * 48000.0f / 1000.0f);
    const int samples_96k = static_cast<int>(5.0f * 96000.0f / 1000.0f);
    
    float value_48k = 0.0f;
    for (int i = 0; i < samples_48k; ++i) {
        value_48k = smoother_48k.processSample();
    }
    
    float value_96k = 0.0f;
    for (int i = 0; i < samples_96k; ++i) {
        value_96k = smoother_96k.processSample();
    }
    
    // Both should reach approximately the same percentage
    EXPECT_NEAR(value_48k, value_96k, 0.02f);
}

TEST_F(ParameterSmootherTest, ChangeSampleRate_MidSmoothing) {
    ParameterSmoother smoother(48000.0f, 5.0f);
    
    smoother.setTarget(1.0f);
    
    // Process some samples
    for (int i = 0; i < 100; ++i) {
        smoother.processSample();
    }
    
    float value_before = smoother.getValue();
    
    // Change sample rate
    smoother.setSampleRate(96000.0f);
    
    // Should continue smoothing (not reset)
    float value_after = smoother.processSample();
    
    EXPECT_NE(value_after, value_before);
    EXPECT_GT(value_after, value_before);  // Still moving toward target
}

//==============================================================================
// TIME CONSTANT TESTS
//==============================================================================

TEST_F(ParameterSmootherTest, ShorterTimeConstant_FasterSmoothing) {
    ParameterSmoother slow(SAMPLE_RATE, 10.0f);
    ParameterSmoother fast(SAMPLE_RATE, 1.0f);
    
    slow.setTarget(1.0f);
    fast.setTarget(1.0f);
    
    // After 100 samples, fast should be closer to target
    for (int i = 0; i < 100; ++i) {
        slow.processSample();
        fast.processSample();
    }
    
    EXPECT_GT(fast.getValue(), slow.getValue());
}

TEST_F(ParameterSmootherTest, TimeConstantLimits) {
    // Time constant should be clamped to valid range
    
    ParameterSmoother smoother(SAMPLE_RATE, 5.0f);
    
    // Try to set very small time constant (should clamp to 0.1ms)
    smoother.setTimeConstant(0.01f);
    // Should still work without issues
    smoother.setTarget(1.0f);
    EXPECT_NO_THROW(smoother.processSample());
    
    // Try to set very large time constant (should clamp to 100ms)
    smoother.setTimeConstant(1000.0f);
    // Should still work
    smoother.setTarget(0.0f);
    EXPECT_NO_THROW(smoother.processSample());
}

//==============================================================================
// EDGE CASES
//==============================================================================

TEST_F(ParameterSmootherTest, ZeroToZero) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    // Target is already at current
    EXPECT_TRUE(smoother.isSettled());
    
    float value = smoother.processSample();
    
    EXPECT_FLOAT_EQ(value, 0.0f);
    EXPECT_TRUE(smoother.isSettled());
}

TEST_F(ParameterSmootherTest, VeryLargeValues) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(10000.0f);
    
    // Should handle large values without overflow
    for (int i = 0; i < 1000; ++i) {
        float value = smoother.processSample();
        EXPECT_FALSE(std::isinf(value));
        EXPECT_FALSE(std::isnan(value));
    }
}

TEST_F(ParameterSmootherTest, RapidTargetChanges) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    // Rapidly change target
    for (int i = 0; i < 100; ++i) {
        smoother.setTarget(i % 2 == 0 ? 1.0f : -1.0f);
        smoother.processSample();
    }
    
    // Should remain stable
    float value = smoother.getValue();
    EXPECT_FALSE(std::isinf(value));
    EXPECT_FALSE(std::isnan(value));
    EXPECT_GE(value, -1.1f);  // Should be within reasonable bounds
    EXPECT_LE(value, 1.1f);
}

//==============================================================================
// BUFFER PROCESSING TESTS
//==============================================================================

TEST_F(ParameterSmootherTest, ProcessBuffer) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    std::vector<float> buffer(100);
    smoother.processBuffer(buffer.data(), buffer.size());
    
    // Buffer should contain smoothed ramp
    for (size_t i = 1; i < buffer.size(); ++i) {
        EXPECT_GT(buffer[i], buffer[i-1]);  // Monotonically increasing
        EXPECT_LE(buffer[i], 1.0f);         // Never overshoot
    }
}

TEST_F(ParameterSmootherTest, ProcessBuffer_EquivalentToSamples) {
    ParameterSmoother smoother1(SAMPLE_RATE, TIME_CONSTANT_MS);
    ParameterSmoother smoother2(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother1.setTarget(1.0f);
    smoother2.setTarget(1.0f);
    
    // Process with buffer
    std::vector<float> buffer(100);
    smoother1.processBuffer(buffer.data(), buffer.size());
    
    // Process sample-by-sample
    std::vector<float> samples(100);
    for (size_t i = 0; i < samples.size(); ++i) {
        samples[i] = smoother2.processSample();
    }
    
    // Results should be identical
    for (size_t i = 0; i < 100; ++i) {
        EXPECT_FLOAT_EQ(buffer[i], samples[i]);
    }
}

//==============================================================================
// STABILITY TESTS
//==============================================================================

TEST_F(ParameterSmootherTest, LongRunningStability) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    smoother.setTarget(1.0f);
    
    // Process for 10 seconds worth of samples
    const int num_samples = static_cast<int>(10.0f * SAMPLE_RATE);
    
    for (int i = 0; i < num_samples; ++i) {
        float value = smoother.processSample();
        
        // Should never produce inf/nan
        ASSERT_FALSE(std::isinf(value)) << "Inf at sample " << i;
        ASSERT_FALSE(std::isnan(value)) << "NaN at sample " << i;
        
        // Should be bounded
        ASSERT_GE(value, -10.0f) << "Underflow at sample " << i;
        ASSERT_LE(value, 10.0f) << "Overflow at sample " << i;
    }
}

TEST_F(ParameterSmootherTest, AlternatingTargets_Stability) {
    ParameterSmoother smoother(SAMPLE_RATE, TIME_CONSTANT_MS);
    
    // Alternate between targets many times
    for (int cycle = 0; cycle < 1000; ++cycle) {
        smoother.setTarget(cycle % 2 == 0 ? 1.0f : -1.0f);
        
        for (int i = 0; i < 10; ++i) {
            float value = smoother.processSample();
            ASSERT_FALSE(std::isinf(value));
            ASSERT_FALSE(std::isnan(value));
        }
    }
}

//==============================================================================
// MAIN TEST RUNNER
//==============================================================================

// main() provided by gtest_main library

