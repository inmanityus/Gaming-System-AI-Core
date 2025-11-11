// Copyright Body Broker - Gaming System AI Core

#include "VocalSynthesisWrapper.h"
#include "vocal_synthesis/audio_buffer.hpp"
#include "vocal_synthesis/aberration_params_v2.hpp"
#include "vocal_synthesis/dsp/glottal_incoherence.hpp"
#include "vocal_synthesis/dsp/subharmonic_generator.hpp"
#include "vocal_synthesis/dsp/pitch_stabilizer.hpp"
#include "vocal_synthesis/dsp/corporeal_noise.hpp"
#include "vocal_synthesis/dsp/subliminal_audio.hpp"

FVocalSynthesisWrapper::FVocalSynthesisWrapper(float InSampleRate)
    : SampleRate(InSampleRate)
    , CurrentArchetype(TEXT("Human"))
{
    // Initialize all DSP objects
    AudioBuffer = std::make_unique<vocal_synthesis::AudioBuffer>(
        static_cast<uint32_t>(SampleRate), 1);
    Params = std::make_unique<vocal_synthesis::AberrationParams>(
        vocal_synthesis::AberrationParams::createHuman());
    GlottalEffect = std::make_unique<vocal_synthesis::dsp::GlottalIncoherence>(SampleRate, 42);
    SubharmonicEffect = std::make_unique<vocal_synthesis::dsp::SubharmonicGenerator>(SampleRate);
    PitchEffect = std::make_unique<vocal_synthesis::dsp::PitchStabilizer>(SampleRate);
    NoiseEffect = std::make_unique<vocal_synthesis::dsp::CorporealNoise>(SampleRate, 42);
    SubliminalEffect = std::make_unique<vocal_synthesis::dsp::SubliminalAudio>(SampleRate);
}

FVocalSynthesisWrapper::~FVocalSynthesisWrapper()
{
    // Smart pointers clean up automatically
}

void FVocalSynthesisWrapper::SetArchetype(const FString& ArchetypeName)
{
    CurrentArchetype = ArchetypeName;
    
    // Load appropriate preset
    if (ArchetypeName == TEXT("Vampire")) {
        *Params = vocal_synthesis::AberrationParams::createVampire();
        PitchEffect->setStabilization(0.7f); // Fixed: setAmount -> setStabilization
        SubliminalEffect->setLayer(vocal_synthesis::dsp::SubliminalAudio::LayerType::HEARTBEAT, 0.08f);
        SubliminalEffect->setLayer(vocal_synthesis::dsp::SubliminalAudio::LayerType::BLOOD_FLOW, 0.05f);
        SubliminalEffect->setHeartbeatRate(60.0f);
    }
    else if (ArchetypeName == TEXT("Zombie")) {
        *Params = vocal_synthesis::AberrationParams::createZombie();
        GlottalEffect->setIntensity(0.6f);
    }
    else if (ArchetypeName == TEXT("Werewolf")) {
        *Params = vocal_synthesis::AberrationParams::createWerewolf();
        SubharmonicEffect->setIntensity(0.7f);
        SubharmonicEffect->setChaos(0.5f);
    }
    else if (ArchetypeName == TEXT("Wraith")) {
        *Params = vocal_synthesis::AberrationParams::createWraith();
    }
    else {
        *Params = vocal_synthesis::AberrationParams::createHuman();
    }
}

void FVocalSynthesisWrapper::SetDynamicIntensity(float BaseIntensity, float Proximity, float Environment)
{
    if (CurrentArchetype == TEXT("Zombie")) {
        GlottalEffect->setDynamicIntensity(BaseIntensity, Proximity, Environment);
    }
}

void FVocalSynthesisWrapper::SetTransformationStruggle(float Struggle)
{
    if (CurrentArchetype == TEXT("Werewolf")) {
        SubharmonicEffect->setTransformationStruggle(Struggle);
    }
}

void FVocalSynthesisWrapper::EnableSubliminalLayer(const FString& LayerName, float Intensity)
{
    using LayerType = vocal_synthesis::dsp::SubliminalAudio::LayerType;
    
    if (LayerName == TEXT("Heartbeat")) {
        SubliminalEffect->setLayer(LayerType::HEARTBEAT, Intensity);
    }
    else if (LayerName == TEXT("BloodFlow")) {
        SubliminalEffect->setLayer(LayerType::BLOOD_FLOW, Intensity);
    }
    else if (LayerName == TEXT("Breath")) {
        SubliminalEffect->setLayer(LayerType::BREATH_CYCLE, Intensity);
    }
    else if (LayerName == TEXT("OrganicHum")) {
        SubliminalEffect->setLayer(LayerType::ORGANIC_HUM, Intensity);
    }
}

void FVocalSynthesisWrapper::SetHeartbeatRate(float BPM)
{
    SubliminalEffect->setHeartbeatRate(BPM);
}

void FVocalSynthesisWrapper::ProcessAudio(float* AudioData, int32 NumSamples)
{
    // Apply archetype-specific processing
    if (CurrentArchetype == TEXT("Zombie")) {
        GlottalEffect->processInPlace(AudioData, NumSamples);
    }
    else if (CurrentArchetype == TEXT("Werewolf")) {
        SubharmonicEffect->processInPlace(AudioData, NumSamples);
    }
    else if (CurrentArchetype == TEXT("Vampire")) {
        PitchEffect->processInPlace(AudioData, NumSamples);
        SubliminalEffect->processInPlace(AudioData, NumSamples);
    }
    
    // Always apply corporeal noise
    NoiseEffect->processInPlace(AudioData, NumSamples);
}

