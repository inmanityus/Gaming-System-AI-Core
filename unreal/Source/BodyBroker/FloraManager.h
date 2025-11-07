// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "BiomeManager.h"
#include "FloraManager.generated.h"

class UStaticMesh;
class UMaterialInterface;

/**
 * FloraManager - Manages flora (plants, trees, etc.) with HISM pooling and streaming
 * TE-002: Flora Management System
 */
UCLASS()
class BODYBROKER_API UFloraManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Get the singleton instance of FloraManager.
	 */
	UFUNCTION(BlueprintCallable, Category = "Flora|TE-002")
	static UFloraManager* Get(const UObject* WorldContext);

	/**
	 * Register flora type for a biome.
	 */
	UFUNCTION(BlueprintCallable, Category = "Flora|TE-002")
	void RegisterFloraType(EBiomeType BiomeType, UStaticMesh* Mesh, UMaterialInterface* Material, float Density);

	/**
	 * Spawn flora in area.
	 */
	UFUNCTION(BlueprintCallable, Category = "Flora|TE-002")
	void SpawnFloraInArea(const FVector& Center, float Radius, EBiomeType BiomeType);

	/**
	 * Set wind strength for foliage animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "Flora|TE-002")
	void SetWindStrength(float WindStrength);

	/**
	 * Set wind direction for foliage animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "Flora|TE-002")
	void SetWindDirection(const FVector& WindDirection);

	/**
	 * Update seasonal appearance.
	 */
	UFUNCTION(BlueprintCallable, Category = "Flora|TE-002")
	void UpdateSeasonalAppearance(float SeasonProgress); // 0.0 = Spring, 0.25 = Summer, 0.5 = Fall, 0.75 = Winter

private:
	// Flora type data
	struct FFloraTypeData
	{
		TObjectPtr<UStaticMesh> Mesh;
		TObjectPtr<UMaterialInterface> Material;
		float Density;
	};

	// Flora data by biome
	TMap<EBiomeType, TArray<FFloraTypeData>> FloraDataByBiome;

	// Active HISM components (pooled)
	UPROPERTY()
	TArray<TObjectPtr<UHierarchicalInstancedStaticMeshComponent>> HISMComponents;

	// Current wind strength
	UPROPERTY()
	float CurrentWindStrength;

	// Current wind direction
	UPROPERTY()
	FVector CurrentWindDirection;

	// Season progress (0.0 to 1.0)
	UPROPERTY()
	float CurrentSeasonProgress;

	// Get or create HISM component for mesh
	UHierarchicalInstancedStaticMeshComponent* GetOrCreateHISMComponent(UStaticMesh* Mesh, UMaterialInterface* Material);

	// Update HISM wind parameters
	void UpdateHISMWindParameters();
};

