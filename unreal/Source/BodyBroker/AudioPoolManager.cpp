// Copyright Epic Games, Inc. All Rights Reserved.

#include "AudioPoolManager.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

UAudioPoolManager::UAudioPoolManager(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

void UAudioPoolManager::Initialize(int32 VoicePoolSize, int32 AmbientPoolSize, int32 WeatherPoolSize, int32 EffectPoolSize, int32 UIPoolSize)
{
	// Set initial pool sizes
	PoolSizes.Empty();
	PoolSizes.Add(EAudioPoolType::Voice, VoicePoolSize);
	PoolSizes.Add(EAudioPoolType::Ambient, AmbientPoolSize);
	PoolSizes.Add(EAudioPoolType::Weather, WeatherPoolSize);
	PoolSizes.Add(EAudioPoolType::Effect, EffectPoolSize);
	PoolSizes.Add(EAudioPoolType::UI, UIPoolSize);

	// Set max pool sizes (growth limits)
	MaxPoolSizes.Empty();
	MaxPoolSizes.Add(EAudioPoolType::Voice, VoicePoolSize * 2);  // Can grow to 2x initial
	MaxPoolSizes.Add(EAudioPoolType::Ambient, AmbientPoolSize * 2);
	MaxPoolSizes.Add(EAudioPoolType::Weather, WeatherPoolSize * 2);
	MaxPoolSizes.Add(EAudioPoolType::Effect, EffectPoolSize * 2);
	MaxPoolSizes.Add(EAudioPoolType::UI, UIPoolSize * 2);

	// Initialize empty pools
	VoicePool.Empty();
	AmbientPool.Empty();
	WeatherPool.Empty();
	EffectPool.Empty();
	UIPool.Empty();

	InUseComponents.Empty();

	UE_LOG(LogTemp, Log, TEXT("AudioPoolManager: Initialized with pool sizes (Voice:%d, Ambient:%d, Weather:%d, Effect:%d, UI:%d)"),
		VoicePoolSize, AmbientPoolSize, WeatherPoolSize, EffectPoolSize, UIPoolSize);
}

TArray<UAudioComponent*>* UAudioPoolManager::GetPoolByType(EAudioPoolType Type)
{
	switch (Type)
	{
		case EAudioPoolType::Voice: return &VoicePool;
		case EAudioPoolType::Ambient: return &AmbientPool;
		case EAudioPoolType::Weather: return &WeatherPool;
		case EAudioPoolType::Effect: return &EffectPool;
		case EAudioPoolType::UI: return &UIPool;
		default: return nullptr;
	}
}

const TArray<UAudioComponent*>* UAudioPoolManager::GetPoolByType(EAudioPoolType Type) const
{
	switch (Type)
	{
		case EAudioPoolType::Voice: return &VoicePool;
		case EAudioPoolType::Ambient: return &AmbientPool;
		case EAudioPoolType::Weather: return &WeatherPool;
		case EAudioPoolType::Effect: return &EffectPool;
		case EAudioPoolType::UI: return &UIPool;
		default: return nullptr;
	}
}

UAudioComponent* UAudioPoolManager::AcquireComponent(EAudioPoolType Type, AActor* Owner, const FVector& Location)
{
	if (!Owner)
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioPoolManager: AcquireComponent called with null Owner"));
		return nullptr;
	}

	// Try to find available component in pool
	UAudioComponent* Component = FindAvailableComponent(Type);
	
	if (!Component)
	{
		// Check if we can grow the pool
		TArray<UAudioComponent*>* Pool = GetPoolByType(Type);
		const int32* MaxSize = MaxPoolSizes.Find(Type);
		
		if (Pool && MaxSize && Pool->Num() < *MaxSize)
		{
			// Create new component
			Component = CreateNewComponent(Type, Owner, Location);
			if (Component)
			{
				Pool->Add(Component);
				UE_LOG(LogTemp, VeryVerbose, TEXT("AudioPoolManager: Created new component for pool %d"), (int32)Type);
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("AudioPoolManager: Pool %d at max size, cannot acquire"), (int32)Type);
			return nullptr;
		}
	}
	else
	{
		// Reset and reposition existing component
		Component->Stop();
		Component->SetWorldLocation(Location);
	}

	if (Component)
	{
		// Mark as in use
		InUseComponents.Add(Component, Type);
		UE_LOG(LogTemp, VeryVerbose, TEXT("AudioPoolManager: Acquired component from pool %d"), (int32)Type);
	}

	return Component;
}

void UAudioPoolManager::ReleaseComponent(UAudioComponent* Component)
{
	if (!Component)
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioPoolManager: ReleaseComponent called with null Component"));
		return;
	}

	// Find which pool this component belongs to
	EAudioPoolType* PoolType = InUseComponents.Find(Component);
	if (!PoolType)
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioPoolManager: Attempted to release component not tracked as in-use"));
		return;
	}

	// Stop the component
	Component->Stop();

	// Remove from in-use tracking
	InUseComponents.Remove(Component);

	UE_LOG(LogTemp, VeryVerbose, TEXT("AudioPoolManager: Released component to pool %d"), (int32)*PoolType);
}

void UAudioPoolManager::PrewarmPools(AActor* OwnerActor)
{
	if (!OwnerActor)
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioPoolManager: PrewarmPools called with null OwnerActor"));
		return;
	}

	// Create initial components for each pool
	for (auto& Pair : PoolSizes)
	{
		EAudioPoolType Type = Pair.Key;
		int32 Size = Pair.Value;

		TArray<UAudioComponent*>* Pool = GetPoolByType(Type);
		if (!Pool)
		{
			continue;
		}

		for (int32 i = 0; i < Size; i++)
		{
			UAudioComponent* Component = CreateNewComponent(Type, OwnerActor, FVector::ZeroVector);
			if (Component)
			{
				Pool->Add(Component);
			}
		}

		UE_LOG(LogTemp, Log, TEXT("AudioPoolManager: Prewarmed pool %d with %d components"), (int32)Type, Size);
	}
}

int32 UAudioPoolManager::GetAvailableCount(EAudioPoolType Type) const
{
	const TArray<UAudioComponent*>* Pool = GetPoolByType(Type);
	if (!Pool)
	{
		return 0;
	}

	// Count components not in use
	int32 Available = 0;
	for (UAudioComponent* Component : *Pool)
	{
		if (Component && !InUseComponents.Contains(Component))
		{
			Available++;
		}
	}

	return Available;
}

int32 UAudioPoolManager::GetInUseCount(EAudioPoolType Type) const
{
	int32 Count = 0;
	for (const auto& Pair : InUseComponents)
	{
		if (Pair.Value == Type)
		{
			Count++;
		}
	}

	return Count;
}

void UAudioPoolManager::ClearAllPools()
{
	// Release all in-use components
	for (auto& Pair : InUseComponents)
	{
		if (UAudioComponent* Component = Pair.Key)
		{
			Component->Stop();
		}
	}
	InUseComponents.Empty();

	// Clear all pools
	VoicePool.Empty();
	AmbientPool.Empty();
	WeatherPool.Empty();
	EffectPool.Empty();
	UIPool.Empty();

	UE_LOG(LogTemp, Log, TEXT("AudioPoolManager: Cleared all pools"));
}

UAudioComponent* UAudioPoolManager::CreateNewComponent(EAudioPoolType Type, AActor* Owner, const FVector& Location)
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

UAudioComponent* UAudioPoolManager::FindAvailableComponent(EAudioPoolType Type) const
{
	const TArray<UAudioComponent*>* Pool = GetPoolByType(Type);
	if (!Pool)
	{
		return nullptr;
	}

	// Find first component not in use
	for (UAudioComponent* Component : *Pool)
	{
		if (Component && !InUseComponents.Contains(Component))
		{
			return Component;
		}
	}

	return nullptr;
}

EAudioLODLevel UAudioPoolManager::CalculateLODLevel(const FVector& SourceLocation, const FVector& ListenerLocation) const
{
	float Distance = FVector::Dist(SourceLocation, ListenerLocation);

	// LOD thresholds (from architecture doc)
	if (Distance < 500.0f)
	{
		return EAudioLODLevel::Full;  // 0-500 units: Full quality
	}
	else if (Distance < 1000.0f)
	{
		return EAudioLODLevel::Reduced;  // 500-1000: Reduced quality
	}
	else if (Distance < 2000.0f)
	{
		return EAudioLODLevel::Minimal;  // 1000-2000: Minimal quality
	}
	else
	{
		return EAudioLODLevel::Culled;  // 2000+: Culled (inaudible)
	}
}

bool UAudioPoolManager::ShouldProcessAudio(EAudioLODLevel CurrentLOD) const
{
	// Only process if not culled
	return CurrentLOD != EAudioLODLevel::Culled;
}

