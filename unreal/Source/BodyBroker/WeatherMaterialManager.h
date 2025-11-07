// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Materials/MaterialParameterCollection.h"
#include "WeatherManager.h"
#include "WeatherMaterialManager.generated.h"

class UMaterialInterface;
class UMaterialInstanceDynamic;
class UMaterialParameterCollectionInstance;

/**
 * Puddle data structure
 */
USTRUCT()
struct FPuddleData
{
	GENERATED_BODY()

	FVector Location;
	float Size;
	float Depth;
	float Age;
	float EvaporationRate;

	FPuddleData()
		: Location(FVector::ZeroVector)
		, Size(0.0f)
		, Depth(0.0f)
		, Age(0.0f)
		, EvaporationRate(0.1f)
	{}
};

/**
 * WeatherMaterialManager - Manages material effects for weather (wetness, snow, wind)
 * WS-003: Material Integration
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UWeatherMaterialManager : public UActorComponent
{
	GENERATED_BODY()

public:
	UWeatherMaterialManager(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Set weather state and update material parameters.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void SetWeatherState(EWeatherState WeatherState, float Intensity);

	/**
	 * Set wetness level (0.0 to 1.0).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void SetWetnessLevel(float Wetness);

	/**
	 * Set snow accumulation level (0.0 to 1.0).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void SetSnowAccumulation(float Accumulation);

	/**
	 * Set wind strength (0.0 to 1.0).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void SetWindStrength(float WindStrength);

	/**
	 * Set wind direction.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void SetWindDirection(const FVector& WindDirection);

	/**
	 * Register a material for weather effects.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void RegisterMaterial(UMaterialInterface* Material, UMaterialInstanceDynamic*& OutMaterialInstance);

	/**
	 * Create dynamic puddle at location.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void CreatePuddle(const FVector& Location, float Size, float Depth);

	/**
	 * Update cloud material parameters.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Materials|WS-003")
	void UpdateCloudMaterial(float CloudDensity, float CloudCoverage);

private:
	// Material Parameter Collection for global weather parameters
	UPROPERTY()
	TObjectPtr<UMaterialParameterCollection> WeatherMPC;

	// Material Parameter Collection Instance
	UPROPERTY()
	TObjectPtr<UMaterialParameterCollectionInstance> WeatherMPCInstance;

	// Registered materials with dynamic instances
	UPROPERTY()
	TMap<TObjectPtr<UMaterialInterface>, TObjectPtr<UMaterialInstanceDynamic>> RegisteredMaterials;

	// Current weather state
	UPROPERTY()
	EWeatherState CurrentWeatherState;

	// Current wetness level
	UPROPERTY()
	float CurrentWetness;

	// Current snow accumulation
	UPROPERTY()
	float CurrentSnowAccumulation;

	// Current wind strength
	UPROPERTY()
	float CurrentWindStrength;

	// Current wind direction
	UPROPERTY()
	FVector CurrentWindDirection;

	// Puddle locations and data
	UPROPERTY()
	TArray<FPuddleData> ActivePuddles;

	// Load Material Parameter Collection
	void LoadMaterialParameterCollection();

	// Update Material Parameter Collection values
	void UpdateMPCParameters();

	// Update registered material instances
	void UpdateMaterialInstances();

	// Update puddle evaporation
	void UpdatePuddles(float DeltaTime);
};

