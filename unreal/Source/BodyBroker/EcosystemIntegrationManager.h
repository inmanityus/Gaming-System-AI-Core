// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "BiomeManager.h"
#include "WeatherManager.h"
#include "TimeOfDayManager.h"
#include "EcosystemIntegrationManager.generated.h"

class UFloraManager;
class UFaunaManager;

/**
 * EcosystemIntegrationManager - Integrates all ecosystem systems (biomes, flora, fauna, weather, time)
 * TE-004: Environmental Response & Polish
 */
UCLASS()
class BODYBROKER_API UEcosystemIntegrationManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Get the singleton instance of EcosystemIntegrationManager.
	 */
	UFUNCTION(BlueprintCallable, Category = "Ecosystem|TE-004")
	static UEcosystemIntegrationManager* Get(const UObject* WorldContext);

	/**
	 * Initialize ecosystem for area.
	 */
	UFUNCTION(BlueprintCallable, Category = "Ecosystem|TE-004")
	void InitializeEcosystem(const FVector& Center, float Radius, EBiomeType BiomeType);

	/**
	 * Update ecosystem based on weather changes.
	 */
	UFUNCTION(BlueprintCallable, Category = "Ecosystem|TE-004")
	void OnWeatherChanged(int32 OldWeatherState, int32 NewWeatherState, float Intensity);

	/**
	 * Update ecosystem based on time of day changes.
	 */
	UFUNCTION(BlueprintCallable, Category = "Ecosystem|TE-004")
	void OnTimeOfDayChanged(FString OldState, FString NewState);

	/**
	 * Update ecosystem based on seasonal changes.
	 */
	UFUNCTION(BlueprintCallable, Category = "Ecosystem|TE-004")
	void UpdateSeason(float SeasonProgress); // 0.0 = Spring, 1.0 = Winter

	/**
	 * Harvest/interact with flora/fauna at location.
	 */
	UFUNCTION(BlueprintCallable, Category = "Ecosystem|TE-004")
	bool HarvestAtLocation(const FVector& Location, float InteractionRadius);

private:
	// Subsystem references
	TWeakObjectPtr<UBiomeManager> BiomeManager;
	TWeakObjectPtr<UWeatherManager> WeatherManager;
	TWeakObjectPtr<UTimeOfDayManager> TimeOfDayManager;
	TWeakObjectPtr<UFloraManager> FloraManager;
	TWeakObjectPtr<UFaunaManager> FaunaManager;

	// Current season progress
	UPROPERTY()
	float CurrentSeasonProgress;

	// Bind to subsystem events
	void BindToSubsystemEvents();
};

