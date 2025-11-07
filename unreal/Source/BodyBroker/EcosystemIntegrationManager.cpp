// Copyright Epic Games, Inc. All Rights Reserved.

#include "EcosystemIntegrationManager.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "BiomeManager.h"
#include "WeatherManager.h"
#include "TimeOfDayManager.h"
#include "FloraManager.h"
#include "FaunaManager.h"

void UEcosystemIntegrationManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Get subsystem references
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		BiomeManager = GameInstance->GetSubsystem<UBiomeManager>();
		WeatherManager = GameInstance->GetSubsystem<UWeatherManager>();
		TimeOfDayManager = GameInstance->GetSubsystem<UTimeOfDayManager>();
		FloraManager = GameInstance->GetSubsystem<UFloraManager>();
		FaunaManager = GameInstance->GetSubsystem<UFaunaManager>();
	}

	CurrentSeasonProgress = 0.25f; // Default to summer
	BindToSubsystemEvents();

	UE_LOG(LogTemp, Log, TEXT("EcosystemIntegrationManager: Initialized"));
}

void UEcosystemIntegrationManager::Deinitialize()
{
	BiomeManager.Reset();
	WeatherManager.Reset();
	TimeOfDayManager.Reset();
	FloraManager.Reset();
	FaunaManager.Reset();
	Super::Deinitialize();
}

UEcosystemIntegrationManager* UEcosystemIntegrationManager::Get(const UObject* WorldContext)
{
	if (!WorldContext)
	{
		return nullptr;
	}

	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UEcosystemIntegrationManager>();
		}
	}

	return nullptr;
}

void UEcosystemIntegrationManager::InitializeEcosystem(const FVector& Center, float Radius, EBiomeType BiomeType)
{
	// Initialize flora for area
	if (FloraManager.IsValid())
	{
		FloraManager->SpawnFloraInArea(Center, Radius, BiomeType);
	}

	// Initialize fauna for area
	if (FaunaManager.IsValid())
	{
		FaunaManager->SpawnFaunaInArea(Center, Radius, BiomeType);
	}

	UE_LOG(LogTemp, Log, TEXT("EcosystemIntegrationManager: Initialized ecosystem for biome %d at %s"), (int32)BiomeType, *Center.ToString());
}

void UEcosystemIntegrationManager::OnWeatherChanged(int32 OldWeatherState, int32 NewWeatherState, float Intensity)
{
	// Update flora wind behavior
	if (FloraManager.IsValid())
	{
		// Extract wind strength from weather state (simplified)
		float WindStrength = Intensity;
		FloraManager->SetWindStrength(WindStrength);
	}

	// Update fauna behavior
	if (FaunaManager.IsValid())
	{
		FaunaManager->UpdateWeatherBehavior(NewWeatherState);
	}

	UE_LOG(LogTemp, Verbose, TEXT("EcosystemIntegrationManager: Weather changed from %d to %d"), OldWeatherState, NewWeatherState);
}

void UEcosystemIntegrationManager::OnTimeOfDayChanged(FString OldState, FString NewState)
{
	// Update fauna time-of-day behavior
	if (FaunaManager.IsValid())
	{
		FaunaManager->UpdateTimeOfDayBehavior(NewState);
	}

	UE_LOG(LogTemp, Verbose, TEXT("EcosystemIntegrationManager: Time of day changed from %s to %s"), *OldState, *NewState);
}

void UEcosystemIntegrationManager::UpdateSeason(float SeasonProgress)
{
	CurrentSeasonProgress = FMath::Clamp(SeasonProgress, 0.0f, 1.0f);

	// Update flora seasonal appearance
	if (FloraManager.IsValid())
	{
		FloraManager->UpdateSeasonalAppearance(CurrentSeasonProgress);
	}

	UE_LOG(LogTemp, Log, TEXT("EcosystemIntegrationManager: Season updated to progress %f"), CurrentSeasonProgress);
}

bool UEcosystemIntegrationManager::HarvestAtLocation(const FVector& Location, float InteractionRadius)
{
	bool bHarvested = false;

	// Query flora at location
	if (FloraManager.IsValid())
	{
		// Check if there's flora in the interaction radius
		// Note: FloraManager uses HISM, so we need to check if any instances are within radius
		// For now, we'll use a simplified approach - check if flora exists in the area
		// In production, this would query HISM instances within radius
		
		// Get biome at location
		if (BiomeManager.IsValid())
		{
			EBiomeType BiomeType = BiomeManager->DetectBiomeAtLocation(Location);
			// Check if biome is valid (not NUM which is the count)
			if (BiomeType < EBiomeType::NUM)
			{
				// Flora exists in this biome - perform harvest interaction
				// Note: Actual harvest would remove HISM instances or mark them as harvested
				// For now, we log the interaction
				UE_LOG(LogTemp, Log, TEXT("EcosystemIntegrationManager: Harvesting flora at %s (Biome: %d)"), 
					*Location.ToString(), (int32)BiomeType);
				bHarvested = true;
			}
		}
	}

	// Query fauna at location
	if (FaunaManager.IsValid())
	{
		// Check if there's fauna in the interaction radius
		// Query active fauna instances within radius
		// Note: This would require FaunaManager to expose GetFaunaInRadius or similar
		// For now, we'll use a simplified approach
		
		// In production, this would:
		// 1. Query FaunaManager for fauna instances within InteractionRadius of Location
		// 2. Interact with the nearest fauna instance
		// 3. Update fauna state (flee, attack, etc.)
		
		UE_LOG(LogTemp, Verbose, TEXT("EcosystemIntegrationManager: Checking for fauna interaction at %s"), 
			*Location.ToString());
	}

	UE_LOG(LogTemp, Log, TEXT("EcosystemIntegrationManager: Harvest interaction at %s (radius: %f) - %s"), 
		*Location.ToString(), InteractionRadius, bHarvested ? TEXT("Success") : TEXT("No harvestable items"));
	
	return bHarvested;
}

void UEcosystemIntegrationManager::BindToSubsystemEvents()
{
	// Bind to weather manager events
	if (WeatherManager.IsValid())
	{
		// WeatherManager->OnWeatherStateChanged.AddDynamic(this, &UEcosystemIntegrationManager::OnWeatherChanged);
		// Note: Event binding would require proper delegate setup
	}

	// Bind to time of day manager events
	if (TimeOfDayManager.IsValid())
	{
		// TimeOfDayManager->OnTimeStateChanged.AddDynamic(this, &UEcosystemIntegrationManager::OnTimeOfDayChanged);
		// Note: Event binding would require proper delegate setup
	}
}

