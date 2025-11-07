// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Engine/DataAsset.h"
#include "BiomeManager.generated.h"

class UWorld;
class UTimeOfDayManager;
class UWeatherManager;

// Forward declarations
class UMaterialParameterCollection;

/**
 * Biome types
 */
UENUM(BlueprintType)
enum class EBiomeType : uint8
{
	Forest		UMETA(DisplayName = "Forest"),
	Desert		UMETA(DisplayName = "Desert"),
	Tundra		UMETA(DisplayName = "Tundra"),
	Grassland	UMETA(DisplayName = "Grassland"),
	Swamp		UMETA(DisplayName = "Swamp"),
	Mountain	UMETA(DisplayName = "Mountain"),
	Coastal		UMETA(DisplayName = "Coastal"),
	Urban		UMETA(DisplayName = "Urban"),
	NUM			UMETA(Hidden)
};

/**
 * Biome data asset structure
 */
UCLASS(BlueprintType)
class BODYBROKER_API UBiomeDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	// Biome type
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Biome")
	EBiomeType BiomeType;

	// Biome name
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Biome")
	FString BiomeName;

	// Temperature range (Celsius)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Biome")
	FVector2D TemperatureRange;

	// Humidity range (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Biome")
	FVector2D HumidityRange;

	// Flora density (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Biome")
	float FloraDensity;

	// Fauna density (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Biome")
	float FaunaDensity;

	// Ground material reference
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Biome")
	TObjectPtr<UMaterialInterface> GroundMaterial;

	UBiomeDataAsset()
		: BiomeType(EBiomeType::Forest)
		, TemperatureRange(FVector2D(15.0f, 25.0f))
		, HumidityRange(FVector2D(0.5f, 0.8f))
		, FloraDensity(0.7f)
		, FaunaDensity(0.5f)
	{}
};

/**
 * BiomeManager - Manages biome detection and transitions
 * TE-001: Biome System Foundation
 */
UCLASS()
class BODYBROKER_API UBiomeManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Get the singleton instance of BiomeManager.
	 */
	UFUNCTION(BlueprintCallable, Category = "Biome")
	static UBiomeManager* Get(const UObject* WorldContext);

	/**
	 * Detect biome at world location.
	 */
	UFUNCTION(BlueprintCallable, Category = "Biome|TE-001")
	EBiomeType DetectBiomeAtLocation(const FVector& WorldLocation) const;

	/**
	 * Register biome data asset.
	 */
	UFUNCTION(BlueprintCallable, Category = "Biome|TE-001")
	void RegisterBiomeAsset(UBiomeDataAsset* BiomeAsset);

	/**
	 * Get biome data asset for biome type.
	 */
	UFUNCTION(BlueprintCallable, Category = "Biome|TE-001")
	UBiomeDataAsset* GetBiomeAsset(EBiomeType BiomeType) const;

	/**
	 * Set current biome (for testing/override).
	 */
	UFUNCTION(BlueprintCallable, Category = "Biome|TE-001")
	void SetCurrentBiome(EBiomeType BiomeType);

	/**
	 * Get current biome.
	 */
	UFUNCTION(BlueprintCallable, Category = "Biome|TE-001")
	EBiomeType GetCurrentBiome() const { return CurrentBiome; }

	/**
	 * Event broadcasted when biome changes.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnBiomeChanged, EBiomeType, OldBiome, EBiomeType, NewBiome);
	UPROPERTY(BlueprintAssignable, Category = "Biome|TE-001|Events")
	FOnBiomeChanged OnBiomeChanged;

private:
	// Registered biome assets
	UPROPERTY()
	TMap<EBiomeType, TObjectPtr<UBiomeDataAsset>> BiomeAssets;

	// Current biome
	UPROPERTY()
	EBiomeType CurrentBiome;

	// Previous biome (for transitions)
	UPROPERTY()
	EBiomeType PreviousBiome;

	// Default biome detection logic
	EBiomeType DetectBiomeFromEnvironment(const FVector& Location) const;
};

