// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "AudioPoolManager.generated.h"

class UAudioComponent;

// Audio LOD levels
UENUM(BlueprintType)
enum class EAudioLODLevel : uint8
{
	Full		UMETA(DisplayName = "Full Quality"),
	Reduced		UMETA(DisplayName = "Reduced Quality"),
	Minimal		UMETA(DisplayName = "Minimal Quality"),
	Culled		UMETA(DisplayName = "Culled")
};

// Audio pool types
UENUM(BlueprintType)
enum class EAudioPoolType : uint8
{
	Voice		UMETA(DisplayName = "Voice"),
	Ambient		UMETA(DisplayName = "Ambient"),
	Weather		UMETA(DisplayName = "Weather"),
	Effect		UMETA(DisplayName = "Effect"),
	UI			UMETA(DisplayName = "UI")
};

/**
 * AudioPoolManager - Manages pools of audio components for efficient reuse
 * Prevents allocation spikes and reduces memory fragmentation
 */
UCLASS(BlueprintType)
class BODYBROKER_API UAudioPoolManager : public UObject
{
	GENERATED_BODY()

public:
	UAudioPoolManager(const FObjectInitializer& ObjectInitializer);

	// Initialize pools with sizes
	UFUNCTION(BlueprintCallable, Category = "Audio Pool")
	void Initialize(int32 VoicePoolSize = 4, int32 AmbientPoolSize = 2, int32 WeatherPoolSize = 3, int32 EffectPoolSize = 8, int32 UIPoolSize = 4);

	// Acquire component from appropriate pool
	UFUNCTION(BlueprintCallable, Category = "Audio Pool")
	UAudioComponent* AcquireComponent(EAudioPoolType Type, AActor* Owner, const FVector& Location = FVector::ZeroVector);

	// Release component back to pool
	UFUNCTION(BlueprintCallable, Category = "Audio Pool")
	void ReleaseComponent(UAudioComponent* Component);

	// Prewarm all pools (create initial components)
	UFUNCTION(BlueprintCallable, Category = "Audio Pool")
	void PrewarmPools(AActor* OwnerActor);

	// Get available count for pool type
	UFUNCTION(BlueprintCallable, Category = "Audio Pool")
	int32 GetAvailableCount(EAudioPoolType Type) const;

	// Get in-use count for pool type
	UFUNCTION(BlueprintCallable, Category = "Audio Pool")
	int32 GetInUseCount(EAudioPoolType Type) const;

	// Clear all pools
	UFUNCTION(BlueprintCallable, Category = "Audio Pool")
	void ClearAllPools();

	// Audio LOD calculation
	UFUNCTION(BlueprintCallable, Category = "Audio LOD")
	EAudioLODLevel CalculateLODLevel(const FVector& SourceLocation, const FVector& ListenerLocation) const;

	// Check if audio should be processed at given LOD
	UFUNCTION(BlueprintCallable, Category = "Audio LOD")
	bool ShouldProcessAudio(EAudioLODLevel CurrentLOD) const;

private:
	// Pools by type
	UPROPERTY()
	TMap<EAudioPoolType, TArray<UAudioComponent*>> Pools;

	// In-use tracking (Component -> PoolType)
	UPROPERTY()
	TMap<UAudioComponent*, EAudioPoolType> InUseComponents;

	// Pool size limits
	UPROPERTY()
	TMap<EAudioPoolType, int32> PoolSizes;

	// Max pool sizes (growth limits)
	UPROPERTY()
	TMap<EAudioPoolType, int32> MaxPoolSizes;

	// Create new audio component
	UAudioComponent* CreateNewComponent(EAudioPoolType Type, AActor* Owner, const FVector& Location);

	// Find available component in pool
	UAudioComponent* FindAvailableComponent(EAudioPoolType Type) const;
};

