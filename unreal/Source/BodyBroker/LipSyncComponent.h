// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "DialogueManager.h"
#include "LipSyncComponent.generated.h"

class USkeletalMeshComponent;
class UAnimInstance;

/**
 * LipSyncComponent - Handles lip-sync and phoneme extraction from dialogue
 * FE-003: Lip-Sync & Audio Integration
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API ULipSyncComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	ULipSyncComponent(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Start lip-sync for dialogue.
	 */
	UFUNCTION(BlueprintCallable, Category = "Lip Sync|FE-003")
	void StartLipSync(const FLipSyncData& LipSyncData);

	/**
	 * Stop lip-sync.
	 */
	UFUNCTION(BlueprintCallable, Category = "Lip Sync|FE-003")
	void StopLipSync();

	/**
	 * Extract phonemes from audio using local analysis when backend data is unavailable.
	 */
	UFUNCTION(BlueprintCallable, Category = "Lip Sync|FE-003")
	void ExtractPhonemesFromAudio(UAudioComponent* AudioComponent, FLipSyncData& OutLipSyncData);

	/**
	 * Update jaw animation based on phonemes.
	 */
	UFUNCTION(BlueprintCallable, Category = "Lip Sync|FE-003")
	void UpdateJawAnimation(float DeltaTime);

	/**
	 * Set lip-sync enabled.
	 */
	UFUNCTION(BlueprintCallable, Category = "Lip Sync|FE-003")
	void SetLipSyncEnabled(bool bEnabled);

private:
	// Skeletal mesh component
	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> SkeletalMeshComponent;

	// Current lip-sync data
	UPROPERTY()
	FLipSyncData CurrentLipSyncData;

	// Current phoneme index
	int32 CurrentPhonemeIndex;

	// Current playback time
	float CurrentPlaybackTime;

	// Lip-sync enabled
	bool bLipSyncEnabled;

	// Find skeletal mesh component
	void FindSkeletalMeshComponent();

	// Apply viseme to blend shapes
	void ApplyViseme(const FString& VisemeName, float Weight);

	// Convert phoneme to viseme
	FString PhonemeToViseme(const FString& Phoneme) const;

	// Simple heuristic to map energy to phoneme label
	FString SelectPhonemeForEnergy(float NormalizedEnergy) const;
};

