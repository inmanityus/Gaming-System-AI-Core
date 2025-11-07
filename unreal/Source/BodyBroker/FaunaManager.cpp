// Copyright Epic Games, Inc. All Rights Reserved.

#include "FaunaManager.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Actor.h"
#include "BiomeManager.h"

void UFaunaManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	CurrentTimeOfDayState = TEXT("Day");
	CurrentWeatherState = 0; // EWeatherState::CLEAR
	UE_LOG(LogTemp, Log, TEXT("FaunaManager: Initialized"));
}

void UFaunaManager::Deinitialize()
{
	// Clean up all fauna instances
	for (TObjectPtr<AActor> FaunaActor : ActiveFaunaInstances)
	{
		if (FaunaActor)
		{
			FaunaActor->Destroy();
		}
	}
	ActiveFaunaInstances.Empty();
	FaunaDataByBiome.Empty();
	Super::Deinitialize();
}

UFaunaManager* UFaunaManager::Get(const UObject* WorldContext)
{
	if (!WorldContext)
	{
		return nullptr;
	}

	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UFaunaManager>();
		}
	}

	return nullptr;
}

void UFaunaManager::RegisterFaunaType(EBiomeType BiomeType, TSubclassOf<AActor> FaunaClass, int32 MaxPopulation, float SpawnRate)
{
	if (!FaunaClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("FaunaManager: Attempted to register null fauna class"));
		return;
	}

	FFaunaTypeData FaunaData;
	FaunaData.FaunaClass = FaunaClass;
	FaunaData.MaxPopulation = FMath::Max(1, MaxPopulation);
	FaunaData.SpawnRate = FMath::Clamp(SpawnRate, 0.0f, 1.0f);
	FaunaData.CurrentPopulation = 0;

	TArray<FFaunaTypeData>& FaunaList = FaunaDataByBiome.FindOrAdd(BiomeType);
	FaunaList.Add(FaunaData);

	UE_LOG(LogTemp, Log, TEXT("FaunaManager: Registered fauna type for biome %d"), (int32)BiomeType);
}

void UFaunaManager::SpawnFaunaInArea(const FVector& Center, float Radius, EBiomeType BiomeType)
{
	if (TArray<FFaunaTypeData>* FaunaList = FaunaDataByBiome.Find(BiomeType))
	{
		for (FFaunaTypeData& FaunaData : *FaunaList)
		{
			// Check population limit
			if (FaunaData.CurrentPopulation >= FaunaData.MaxPopulation)
			{
				continue;
			}

			// Spawn based on spawn rate
			float RandomValue = FMath::RandRange(0.0f, 1.0f);
			if (RandomValue > FaunaData.SpawnRate)
			{
				continue;
			}

			// Calculate spawn location
			FVector RandomLocation = Center + FVector(
				FMath::RandRange(-Radius, Radius),
				FMath::RandRange(-Radius, Radius),
				0.0f
			);

			FRotator RandomRotation(0.0f, FMath::RandRange(0.0f, 360.0f), 0.0f);

			// Spawn fauna actor
			AActor* SpawnedActor = SpawnFaunaActor(FaunaData.FaunaClass, RandomLocation, RandomRotation);
			if (SpawnedActor)
			{
				ActiveFaunaInstances.Add(SpawnedActor);
				FaunaData.CurrentPopulation++;
				UE_LOG(LogTemp, Verbose, TEXT("FaunaManager: Spawned fauna at %s"), *RandomLocation.ToString());
			}
		}
	}
}

void UFaunaManager::UpdateTimeOfDayBehavior(FString TimeOfDayState)
{
	CurrentTimeOfDayState = TimeOfDayState;

	// Update behavior for all active fauna
	// Communicate with AI controllers or behavior trees via interface
	for (TObjectPtr<AActor> FaunaActor : ActiveFaunaInstances)
	{
		if (FaunaActor && FaunaActor->IsValidLowLevel())
		{
			// Notify fauna of time of day change via interface
			// Check if actor implements IFaunaBehaviorInterface
			// If interface exists, call OnTimeOfDayChanged
			// Otherwise, use event system or direct component access
			
			// Try to find AI controller component
			if (APawn* FaunaPawn = Cast<APawn>(FaunaActor))
			{
				if (AController* Controller = FaunaPawn->GetController())
				{
					// Notify controller of time of day change
					// This would require a custom AI controller with time-of-day awareness
					// For now, we log the notification
					UE_LOG(LogTemp, VeryVerbose, TEXT("FaunaManager: Notifying fauna %s of time of day change to %s"), 
						*FaunaActor->GetName(), *TimeOfDayState);
				}
			}
		}
	}

	UE_LOG(LogTemp, Verbose, TEXT("FaunaManager: Updated time of day behavior to %s"), *TimeOfDayState);
}

void UFaunaManager::UpdateWeatherBehavior(int32 WeatherState)
{
	CurrentWeatherState = WeatherState;

	// Update behavior for all active fauna
	// Communicate with AI controllers via interface
	for (TObjectPtr<AActor> FaunaActor : ActiveFaunaInstances)
	{
		if (FaunaActor && FaunaActor->IsValidLowLevel())
		{
			// Notify fauna of weather change via interface
			// Check if actor implements IFaunaBehaviorInterface
			// If interface exists, call OnWeatherChanged
			// Otherwise, use event system or direct component access
			
			// Try to find AI controller component
			if (APawn* FaunaPawn = Cast<APawn>(FaunaActor))
			{
				if (AController* Controller = FaunaPawn->GetController())
				{
					// Notify controller of weather change
					// This would require a custom AI controller with weather awareness
					// For now, we log the notification
					UE_LOG(LogTemp, VeryVerbose, TEXT("FaunaManager: Notifying fauna %s of weather change to state %d"), 
						*FaunaActor->GetName(), WeatherState);
				}
			}
		}
	}

	UE_LOG(LogTemp, Verbose, TEXT("FaunaManager: Updated weather behavior to state %d"), WeatherState);
}

void UFaunaManager::SetPopulationLimit(EBiomeType BiomeType, int32 MaxPopulation)
{
	if (TArray<FFaunaTypeData>* FaunaList = FaunaDataByBiome.Find(BiomeType))
	{
		for (FFaunaTypeData& FaunaData : *FaunaList)
		{
			FaunaData.MaxPopulation = FMath::Max(1, MaxPopulation);
		}
	}
}

AActor* UFaunaManager::SpawnFaunaActor(TSubclassOf<AActor> FaunaClass, const FVector& Location, const FRotator& Rotation)
{
	if (!FaunaClass || !GetWorld())
	{
		return nullptr;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

	AActor* SpawnedActor = GetWorld()->SpawnActor<AActor>(FaunaClass, Location, Rotation, SpawnParams);
	return SpawnedActor;
}

bool UFaunaManager::IsPopulationLimitReached(EBiomeType BiomeType) const
{
	if (const TArray<FFaunaTypeData>* FaunaList = FaunaDataByBiome.Find(BiomeType))
	{
		for (const FFaunaTypeData& FaunaData : *FaunaList)
		{
			if (FaunaData.CurrentPopulation < FaunaData.MaxPopulation)
			{
				return false;
			}
		}
		return true;
	}
	return false;
}

void UFaunaManager::CleanupInactiveFauna()
{
	// Remove invalid or destroyed fauna instances
	ActiveFaunaInstances.RemoveAll([](const TObjectPtr<AActor>& Actor)
	{
		return !IsValid(Actor);
	});

	// Update population counts
	// In production, this would track which fauna belongs to which type
}

