// Copyright Body Broker - Gaming System AI Core

#pragma once

#include "CoreMinimal.h"
#include "Components/SynthComponent.h"
#include "VocalSynthesisComponent.generated.h"

/**
 * Audio component for real-time vocal synthesis with aberration modeling
 * 
 * Integrates vocal_synthesis C++ library with Unreal Engine audio system.
 * Supports dynamic archetype switching (Human, Vampire, Zombie, Werewolf, Wraith).
 */
UCLASS(ClassGroup = (Audio), meta = (BlueprintSpawnableComponent))
class VOCALSYNTHESIS_API UVocalSynthesisComponent : public USynthComponent
{
	GENERATED_BODY()

public:
	UVocalSynthesisComponent(const FObjectInitializer& ObjectInitializer);
	virtual ~UVocalSynthesisComponent();

	// Archetype selection
	UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
	void SetArchetype(FString ArchetypeName);
	
	// Dynamic intensity control (Story Teller Phase 2B)
	UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
	void SetDynamicIntensity(float BaseIntensity, float Proximity, float Environment);
	
	// Transformation struggle (Werewolf)
	UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
	void SetTransformationStruggle(float Struggle);
	
	// Subliminal layers (Vampire)
	UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
	void EnableSubliminalLayer(FString LayerName, float Intensity);
	
	UFUNCTION(BlueprintCallable, Category = "Vocal Synthesis")
	void SetHeartbeatRate(float BPM);

protected:
	// USynthComponent interface
	virtual int32 OnGenerateAudio(float* OutAudio, int32 NumSamples) override;
	
private:
	// Internal state
	float SampleRate;
	FString CurrentArchetype;
	float BaseIntensity;
	float ProximityFactor;
	float EnvironmentFactor;
	
	// C++ library wrapper (raw pointer for PIMPL idiom)
	class FVocalSynthesisWrapper* Wrapper;
};

