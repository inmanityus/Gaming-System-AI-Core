// Copyright Body Broker - Gaming System AI Core

#pragma once

#include "CoreMinimal.h"
#include <memory>

// Forward declarations of vocal_synthesis types
namespace vocal_synthesis {
    class AudioBuffer;
    struct AberrationParams;
    namespace dsp {
        class GlottalIncoherence;
        class SubharmonicGenerator;
        class PitchStabilizer;
        class CorporealNoise;
        class SubliminalAudio;
    }
}

/**
 * C++ wrapper for vocal_synthesis library
 * Manages lifetime and state of C++ DSP objects
 */
class FVocalSynthesisWrapper
{
public:
    FVocalSynthesisWrapper(float SampleRate);
    ~FVocalSynthesisWrapper();
    
    // Archetype control
    void SetArchetype(const FString& ArchetypeName);
    
    // Dynamic intensity (Phase 2B)
    void SetDynamicIntensity(float BaseIntensity, float Proximity, float Environment);
    void SetTransformationStruggle(float Struggle);
    void EnableSubliminalLayer(const FString& LayerName, float Intensity);
    void SetHeartbeatRate(float BPM);
    
    // Audio processing
    void ProcessAudio(float* AudioData, int32 NumSamples);
    
private:
    float SampleRate;
    FString CurrentArchetype;
    
    // Smart pointers to C++ objects
    std::unique_ptr<vocal_synthesis::AudioBuffer> AudioBuffer;
    std::unique_ptr<vocal_synthesis::AberrationParams> Params;
    std::unique_ptr<vocal_synthesis::dsp::GlottalIncoherence> GlottalEffect;
    std::unique_ptr<vocal_synthesis::dsp::SubharmonicGenerator> SubharmonicEffect;
    std::unique_ptr<vocal_synthesis::dsp::PitchStabilizer> PitchEffect;
    std::unique_ptr<vocal_synthesis::dsp::CorporealNoise> NoiseEffect;
    std::unique_ptr<vocal_synthesis::dsp::SubliminalAudio> SubliminalEffect;
};

