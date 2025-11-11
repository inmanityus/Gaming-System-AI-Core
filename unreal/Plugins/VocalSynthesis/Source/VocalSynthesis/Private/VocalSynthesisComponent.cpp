// Copyright Body Broker - Gaming System AI Core

#include "VocalSynthesisComponent.h"
#include "VocalSynthesisWrapper.h"
#include "Audio.h"

UVocalSynthesisComponent::UVocalSynthesisComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, Wrapper(nullptr)
{
	PrimaryComponentTick.bCanEverTick = false;
	SampleRate = 48000.0f;
	CurrentArchetype = TEXT("Human");
	BaseIntensity = 0.5f;
	ProximityFactor = 0.0f;
	EnvironmentFactor = 0.5f;
	
	// Initialize C++ wrapper
	Wrapper = new FVocalSynthesisWrapper(SampleRate);
}

UVocalSynthesisComponent::~UVocalSynthesisComponent()
{
	// Manual cleanup for PIMPL
	if (Wrapper)
	{
		delete Wrapper;
		Wrapper = nullptr;
	}
}

void UVocalSynthesisComponent::SetArchetype(FString ArchetypeName)
{
	CurrentArchetype = ArchetypeName;
	if (Wrapper)
	{
		Wrapper->SetArchetype(ArchetypeName);
	}
}

void UVocalSynthesisComponent::SetDynamicIntensity(float InBaseIntensity, float InProximity, float InEnvironment)
{
	BaseIntensity = FMath::Clamp(InBaseIntensity, 0.0f, 1.0f);
	ProximityFactor = FMath::Clamp(InProximity, 0.0f, 1.0f);
	EnvironmentFactor = FMath::Clamp(InEnvironment, 0.0f, 1.0f);
	
	if (Wrapper)
	{
		Wrapper->SetDynamicIntensity(BaseIntensity, ProximityFactor, EnvironmentFactor);
	}
}

void UVocalSynthesisComponent::SetTransformationStruggle(float Struggle)
{
	if (Wrapper)
	{
		Wrapper->SetTransformationStruggle(Struggle);
	}
}

void UVocalSynthesisComponent::EnableSubliminalLayer(FString LayerName, float Intensity)
{
	if (Wrapper)
	{
		Wrapper->EnableSubliminalLayer(LayerName, Intensity);
	}
}

void UVocalSynthesisComponent::SetHeartbeatRate(float BPM)
{
	if (Wrapper)
	{
		Wrapper->SetHeartbeatRate(BPM);
	}
}

int32 UVocalSynthesisComponent::OnGenerateAudio(float* OutAudio, int32 NumSamples)
{
	if (Wrapper)
	{
		Wrapper->ProcessAudio(OutAudio, NumSamples);
		return NumSamples;
	}
	
	// Fallback: silence
	FMemory::Memzero(OutAudio, NumSamples * sizeof(float));
	return NumSamples;
}

