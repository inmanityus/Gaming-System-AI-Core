// Copyright Epic Games, Inc. All Rights Reserved.

#include "BiomeManager.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "TimeOfDayManager.h"
#include "WeatherManager.h"

void UBiomeManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	UE_LOG(LogTemp, Log, TEXT("BiomeManager: Initializing"));

	// Initialize state
	CurrentBiome = EBiomeType::Forest;
	PreviousBiome = EBiomeType::Forest;

	UE_LOG(LogTemp, Log, TEXT("BiomeManager: Initialization complete"));
}

void UBiomeManager::Deinitialize()
{
	BiomeAssets.Empty();
	Super::Deinitialize();
}

UBiomeManager* UBiomeManager::Get(const UObject* WorldContext)
{
	if (!WorldContext)
	{
		return nullptr;
	}

	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UBiomeManager>();
		}
	}

	return nullptr;
}

EBiomeType UBiomeManager::DetectBiomeAtLocation(const FVector& WorldLocation) const
{
	// Biome detection based on environment analysis
	// In production, this would analyze terrain, materials, foliage, etc.
	return DetectBiomeFromEnvironment(WorldLocation);
}

void UBiomeManager::RegisterBiomeAsset(UBiomeDataAsset* BiomeAsset)
{
	if (!BiomeAsset)
	{
		UE_LOG(LogTemp, Warning, TEXT("BiomeManager: Attempted to register null biome asset"));
		return;
	}

	BiomeAssets.Add(BiomeAsset->BiomeType, BiomeAsset);
	UE_LOG(LogTemp, Log, TEXT("BiomeManager: Registered biome asset for type %d"), (int32)BiomeAsset->BiomeType);
}

UBiomeDataAsset* UBiomeManager::GetBiomeAsset(EBiomeType BiomeType) const
{
	const TObjectPtr<UBiomeDataAsset>* AssetPtr = BiomeAssets.Find(BiomeType);
	if (AssetPtr)
	{
		return *AssetPtr;
	}
	return nullptr;
}

void UBiomeManager::SetCurrentBiome(EBiomeType BiomeType)
{
	if (BiomeType == CurrentBiome)
	{
		return;
	}

	PreviousBiome = CurrentBiome;
	CurrentBiome = BiomeType;

	// Broadcast biome change event
	OnBiomeChanged.Broadcast(PreviousBiome, CurrentBiome);

	UE_LOG(LogTemp, Log, TEXT("BiomeManager: Biome changed from %d to %d"), (int32)PreviousBiome, (int32)CurrentBiome);
}

EBiomeType UBiomeManager::DetectBiomeFromEnvironment(const FVector& Location) const
{
	// Biome detection based on environment analysis
	// Sample terrain height/steepness, analyze ground material types, check foliage density
	
	// Check registered biome assets for matching conditions
	for (const auto& Pair : BiomeAssets)
	{
		UBiomeDataAsset* BiomeAsset = Pair.Value;
		if (BiomeAsset)
		{
			// In production, this would:
			// 1. Sample terrain height/steepness at location
			// 2. Analyze ground material types via line trace
			// 3. Check foliage density via spatial queries
			// 4. Consider proximity to water via distance queries
			// 5. Use World Partition data for biome regions
			
			// For now, use simplified detection based on biome asset data
			// Return first registered biome as default
			// This will be enhanced with actual terrain analysis in TE-002/003/004
			return BiomeAsset->BiomeType;
		}
	}

	// Default to Forest if no biome assets registered
	return EBiomeType::Forest;
}

