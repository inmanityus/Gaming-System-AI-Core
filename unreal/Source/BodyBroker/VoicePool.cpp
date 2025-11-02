// Copyright Epic Games, Inc. All Rights Reserved.

#include "VoicePool.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

UVoicePool::UVoicePool(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, MaxPoolSize(8)
{
}

void UVoicePool::Initialize(int32 InMaxPoolSize)
{
	MaxPoolSize = FMath::Max(1, InMaxPoolSize);  // Minimum 1

	// Pool will be created lazily as needed to avoid creating all components at once
	Pool.Empty();
	InUse.Empty();
	ComponentLocations.Empty();

	UE_LOG(LogTemp, Log, TEXT("VoicePool: Initialized with max size %d"), MaxPoolSize);
}

UAudioComponent* UVoicePool::AcquireVoiceComponent(AActor* Owner, const FVector& Location)
{
	if (!Owner)
	{
		UE_LOG(LogTemp, Warning, TEXT("VoicePool: AcquireVoiceComponent called with null Owner"));
		return nullptr;
	}

	// Check if we're at capacity
	if (InUse.Num() >= MaxPoolSize)
	{
		// At capacity - find furthest component to drop
		UAudioComponent* Furthest = GetFurthestActiveComponent();
		if (Furthest)
		{
			// Release the furthest component
			ReleaseVoiceComponent(Furthest);
			UE_LOG(LogTemp, VeryVerbose, TEXT("VoicePool: At capacity, dropped furthest component"));
		}
		else
		{
			// Cannot acquire - at capacity and no valid component to drop
			UE_LOG(LogTemp, Warning, TEXT("VoicePool: At capacity (%d/%d), cannot acquire component"), InUse.Num(), MaxPoolSize);
			return nullptr;
		}
	}

	// Try to find available component from pool
	UAudioComponent* Component = FindAvailableComponent();
	if (!Component)
	{
		// No available component - create new one
		Component = CreateNewComponent(Owner, Location);
		if (!Component)
		{
			UE_LOG(LogTemp, Error, TEXT("VoicePool: Failed to create new audio component"));
			return nullptr;
		}

		// Add to pool
		Pool.Add(Component);
	}

	// Mark as in use
	InUse.Add(Component);
	ComponentLocations.Add(Component, Location);

	UE_LOG(LogTemp, VeryVerbose, TEXT("VoicePool: Acquired component (in use: %d/%d)"), InUse.Num(), MaxPoolSize);

	return Component;
}

void UVoicePool::ReleaseVoiceComponent(UAudioComponent* Component)
{
	if (!Component)
	{
		UE_LOG(LogTemp, Warning, TEXT("VoicePool: ReleaseVoiceComponent called with null Component"));
		return;
	}

	// Check if component is actually in use
	if (!InUse.Contains(Component))
	{
		UE_LOG(LogTemp, Warning, TEXT("VoicePool: Attempted to release component not in use"));
		return;
	}

	// Remove from in-use set
	InUse.Remove(Component);
	ComponentLocations.Remove(Component);

	// Stop the component
	Component->Stop();

	UE_LOG(LogTemp, VeryVerbose, TEXT("VoicePool: Released component (in use: %d/%d)"), InUse.Num(), MaxPoolSize);
}

int32 UVoicePool::GetAvailableCount() const
{
	return MaxPoolSize - InUse.Num();
}

int32 UVoicePool::GetInUseCount() const
{
	return InUse.Num();
}

void UVoicePool::SetPlayerPawn(APawn* InPlayerPawn)
{
	PlayerPawn = InPlayerPawn;
}

float UVoicePool::CalculateSpatialPriority(const FVector& Location) const
{
	if (!PlayerPawn.IsValid())
	{
		// No player reference - return neutral priority
		return 0.0f;
	}

	FVector PlayerLocation = PlayerPawn->GetActorLocation();
	float Distance = FVector::Dist(Location, PlayerLocation);

	// Inverse distance - closer = higher priority
	// Normalize to 0.0-1.0 range (assuming max distance of 5000 units)
	float MaxDistance = 5000.0f;
	float NormalizedDistance = FMath::Clamp(Distance / MaxDistance, 0.0f, 1.0f);
	float Priority = 1.0f - NormalizedDistance;  // Closer = higher priority

	return Priority;
}

UAudioComponent* UVoicePool::GetFurthestActiveComponent() const
{
	if (!PlayerPawn.IsValid() || InUse.Num() == 0)
	{
		return nullptr;
	}

	FVector PlayerLocation = PlayerPawn->GetActorLocation();
	float MaxDistance = 0.0f;
	UAudioComponent* FurthestComponent = nullptr;

	for (UAudioComponent* Component : InUse)
	{
		const FVector* Location = ComponentLocations.Find(Component);
		if (!Location)
		{
			continue;
		}

		float Distance = FVector::Dist(*Location, PlayerLocation);
		if (Distance > MaxDistance)
		{
			MaxDistance = Distance;
			FurthestComponent = Component;
		}
	}

	return FurthestComponent;
}

UAudioComponent* UVoicePool::CreateNewComponent(AActor* Owner, const FVector& Location)
{
	if (!Owner)
	{
		return nullptr;
	}

	// Create audio component
	UAudioComponent* Component = NewObject<UAudioComponent>(Owner, UAudioComponent::StaticClass());
	if (!Component)
	{
		return nullptr;
	}

	// Attach to owner
	Component->AttachToComponent(Owner->GetRootComponent(), FAttachmentTransformRules::KeepWorldTransform);
	Component->SetWorldLocation(Location);

	// Register component
	Component->RegisterComponent();

	return Component;
}

UAudioComponent* UVoicePool::FindAvailableComponent() const
{
	// Find first component in pool that's not in use
	for (UAudioComponent* Component : Pool)
	{
		if (Component && !InUse.Contains(Component))
		{
			return Component;
		}
	}

	return nullptr;
}

