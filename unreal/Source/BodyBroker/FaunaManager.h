// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "BiomeManager.h"
#include "FaunaManager.generated.h"

class AActor;
class UBehaviorTree;

/**
 * FaunaManager - Manages fauna (animals, creatures) spawning and behavior
 * TE-003: Fauna System
 */
UCLASS()
class BODYBROKER_API UFaunaManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Get the singleton instance of FaunaManager.
	 */
	UFUNCTION(BlueprintCallable, Category = "Fauna|TE-003")
	static UFaunaManager* Get(const UObject* WorldContext);

	/**
	 * Register fauna type for a biome.
	 */
	UFUNCTION(BlueprintCallable, Category = "Fauna|TE-003")
	void RegisterFaunaType(EBiomeType BiomeType, TSubclassOf<AActor> FaunaClass, int32 MaxPopulation, float SpawnRate);

	/**
	 * Spawn fauna in area.
	 */
	UFUNCTION(BlueprintCallable, Category = "Fauna|TE-003")
	void SpawnFaunaInArea(const FVector& Center, float Radius, EBiomeType BiomeType);

	/**
	 * Update fauna behavior based on time of day.
	 */
	UFUNCTION(BlueprintCallable, Category = "Fauna|TE-003")
	void UpdateTimeOfDayBehavior(FString TimeOfDayState); // "Day", "Night", "Dawn", "Dusk"

	/**
	 * Update fauna behavior based on weather.
	 */
	UFUNCTION(BlueprintCallable, Category = "Fauna|TE-003")
	void UpdateWeatherBehavior(int32 WeatherState); // EWeatherState as int32

	/**
	 * Set population limit for fauna type.
	 */
	UFUNCTION(BlueprintCallable, Category = "Fauna|TE-003")
	void SetPopulationLimit(EBiomeType BiomeType, int32 MaxPopulation);

private:
	// Fauna type data
	struct FFaunaTypeData
	{
		TSubclassOf<AActor> FaunaClass;
		int32 MaxPopulation;
		float SpawnRate;
		int32 CurrentPopulation;
	};

	// Fauna data by biome
	TMap<EBiomeType, TArray<FFaunaTypeData>> FaunaDataByBiome;

	// Active fauna instances
	UPROPERTY()
	TArray<TObjectPtr<AActor>> ActiveFaunaInstances;

	// Current time of day state
	UPROPERTY()
	FString CurrentTimeOfDayState;

	// Current weather state
	UPROPERTY()
	int32 CurrentWeatherState;

	// Spawn fauna actor
	AActor* SpawnFaunaActor(TSubclassOf<AActor> FaunaClass, const FVector& Location, const FRotator& Rotation);

	// Check if population limit reached
	bool IsPopulationLimitReached(EBiomeType BiomeType) const;

	// Clean up inactive fauna
	void CleanupInactiveFauna();
};

