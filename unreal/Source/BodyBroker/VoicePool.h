// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "VoicePool.generated.h"

class UAudioComponent;
class AActor;
class APawn;

/**
 * VoicePool - Manages pool of audio components for concurrent voice playback
 * Implements spatial audio priority and prevents allocation spikes
 */
UCLASS(BlueprintType)
class BODYBROKER_API UVoicePool : public UObject
{
	GENERATED_BODY()

public:
	UVoicePool(const FObjectInitializer& ObjectInitializer);

	// Initialize voice pool with max size
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	void Initialize(int32 MaxPoolSize = 8);

	// Acquire a voice component from the pool
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	UAudioComponent* AcquireVoiceComponent(AActor* Owner, const FVector& Location);

	// Release a voice component back to the pool
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	void ReleaseVoiceComponent(UAudioComponent* Component);

	// Get number of available components in pool
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	int32 GetAvailableCount() const;

	// Get number of components in use
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	int32 GetInUseCount() const;

	// Get total pool size
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	int32 GetPoolSize() const { return MaxPoolSize; }

	// Get player pawn reference (for spatial priority)
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	void SetPlayerPawn(APawn* InPlayerPawn);

	// Calculate spatial priority for location (distance to player)
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	float CalculateSpatialPriority(const FVector& Location) const;

	// Get furthest active voice component (for dropping when at capacity)
	UFUNCTION(BlueprintCallable, Category = "Voice Pool")
	UAudioComponent* GetFurthestActiveComponent() const;

private:
	// Pool of pre-allocated audio components
	UPROPERTY()
	TArray<UAudioComponent*> Pool;

	// Components currently in use
	UPROPERTY()
	TSet<UAudioComponent*> InUse;

	// Track component locations for spatial priority
	UPROPERTY()
	TMap<UAudioComponent*, FVector> ComponentLocations;

	// Max pool size (default 8 per architecture)
	int32 MaxPoolSize;

	// Player pawn reference for spatial calculations
	UPROPERTY()
	TWeakObjectPtr<APawn> PlayerPawn;

	// Create new audio component
	UAudioComponent* CreateNewComponent(AActor* Owner, const FVector& Location);

	// Find best available component from pool
	UAudioComponent* FindAvailableComponent() const;
};

