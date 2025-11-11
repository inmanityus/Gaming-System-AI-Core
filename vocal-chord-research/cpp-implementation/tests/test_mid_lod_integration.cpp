#include "vocal_synthesis/mid_lod_kernel.hpp"
#include "vocal_synthesis/audio_buffer.hpp"
#include <gtest/gtest.h>

using namespace vocal_synthesis;

TEST(MidLODKernel, ProcessVampire) {
    MidLODKernel kernel(48000.0f);
    
    // Load anchor audio
    AudioBuffer anchor = AudioBuffer::loadFromFile("../../data/anchor_neutral.wav");
    AudioBuffer output(48000, 1);
    output.resize(anchor.numFrames());
    
    // Vampire parameters
    AberrationParams vampire = AberrationParams::createVampire();
    
    // Process
    kernel.process(output.data(), anchor.data(), vampire, anchor.size());
    
    // Save for manual inspection
    output.saveToFile("test_output/mid_lod_vampire.wav");
    
    EXPECT_GT(output.getPeak(), 0.0f);
}

TEST(MidLODKernel, ProcessZombie) {
    MidLODKernel kernel(48000.0f);
    
    AudioBuffer anchor = AudioBuffer::loadFromFile("../../data/anchor_neutral.wav");
    AudioBuffer output(48000, 1);
    output.resize(anchor.numFrames());
    
    AberrationParams zombie = AberrationParams::createZombie();
    
    kernel.process(output.data(), anchor.data(), zombie, anchor.size());
    output.saveToFile("test_output/mid_lod_zombie.wav");
    
    EXPECT_GT(output.getPeak(), 0.0f);
}

TEST(MidLODKernel, ProcessWerewolf) {
    MidLODKernel kernel(48000.0f);
    
    AudioBuffer anchor = AudioBuffer::loadFromFile("../../data/anchor_neutral.wav");
    AudioBuffer output(48000, 1);
    output.resize(anchor.numFrames());
    
    AberrationParams werewolf = AberrationParams::createWerewolf();
    
    kernel.process(output.data(), anchor.data(), werewolf, anchor.size());
    output.saveToFile("test_output/mid_lod_werewolf.wav");
    
    EXPECT_GT(output.getPeak(), 0.0f);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

