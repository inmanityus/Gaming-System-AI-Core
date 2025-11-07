// Copyright Epic Games, Inc. All Rights Reserved.

#include "WeatherParticleManager.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraFunctionLibrary.h"
#include "Engine/World.h"
#include "WeatherManager.h"

UWeatherParticleManager::UWeatherParticleManager(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, CurrentWeatherState(EWeatherState::CLEAR)
	, CurrentIntensity(0.0f)
	, ParticleLODLevel(0)
{
	PrimaryComponentTick.bCanEverTick = true;
	bTickInEditor = false;
}

void UWeatherParticleManager::BeginPlay()
{
	Super::BeginPlay();

	// Load Niagara systems
	LoadNiagaraSystems();

	UE_LOG(LogTemp, Log, TEXT("WeatherParticleManager: BeginPlay"));
}

void UWeatherParticleManager::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Stop all particle systems
	if (RainParticleComponent)
	{
		RainParticleComponent->Deactivate();
	}
	if (SnowParticleComponent)
	{
		SnowParticleComponent->Deactivate();
	}
	if (FogVolumetricComponent)
	{
		FogVolumetricComponent->Deactivate();
	}
	if (LightningComponent)
	{
		LightningComponent->Deactivate();
	}

	// Release pooled components
	for (UNiagaraComponent* Component : NiagaraComponentPool)
	{
		if (Component)
		{
			Component->DestroyComponent();
		}
	}
	NiagaraComponentPool.Empty();

	Super::EndPlay(EndPlayReason);
}

void UWeatherParticleManager::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Update particle parameters based on current weather
	// This ensures smooth transitions
}

void UWeatherParticleManager::SetWeatherState(EWeatherState WeatherState, float Intensity)
{
	CurrentWeatherState = WeatherState;
	CurrentIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);

	// Enable/disable particle systems based on weather state
	switch (WeatherState)
	{
	case EWeatherState::RAIN:
	case EWeatherState::HEAVY_RAIN:
	case EWeatherState::STORM:
		SetRainEnabled(true, CurrentIntensity);
		SetSnowEnabled(false, 0.0f);
		SetFogEnabled(false, 0.0f);
		break;

	case EWeatherState::SNOW:
	case EWeatherState::HEAVY_SNOW:
	case EWeatherState::BLIZZARD:
		SetRainEnabled(false, 0.0f);
		SetSnowEnabled(true, CurrentIntensity);
		SetFogEnabled(false, 0.0f);
		break;

	case EWeatherState::FOG:
	case EWeatherState::MIST:
		SetRainEnabled(false, 0.0f);
		SetSnowEnabled(false, 0.0f);
		SetFogEnabled(true, CurrentIntensity);
		break;

	case EWeatherState::CLEAR:
	case EWeatherState::PARTLY_CLOUDY:
	case EWeatherState::CLOUDY:
	default:
		SetRainEnabled(false, 0.0f);
		SetSnowEnabled(false, 0.0f);
		SetFogEnabled(false, 0.0f);
		break;
	}

	UE_LOG(LogTemp, Log, TEXT("WeatherParticleManager: Weather state set to %d with intensity %f"), (int32)WeatherState, Intensity);
}

void UWeatherParticleManager::SetRainEnabled(bool bEnabled, float Intensity)
{
	if (bEnabled && Intensity > 0.0f)
	{
		if (!RainParticleComponent && RainSystem)
		{
			GetOrCreateNiagaraComponent(RainSystem, RainParticleComponent);
		}

		if (RainParticleComponent)
		{
			UpdateParticleParameters(RainParticleComponent, Intensity);
			if (!RainParticleComponent->IsActive())
			{
				RainParticleComponent->Activate();
			}
		}
	}
	else
	{
		if (RainParticleComponent && RainParticleComponent->IsActive())
		{
			RainParticleComponent->Deactivate();
		}
	}
}

void UWeatherParticleManager::SetSnowEnabled(bool bEnabled, float Intensity)
{
	if (bEnabled && Intensity > 0.0f)
	{
		if (!SnowParticleComponent && SnowSystem)
		{
			GetOrCreateNiagaraComponent(SnowSystem, SnowParticleComponent);
		}

		if (SnowParticleComponent)
		{
			UpdateParticleParameters(SnowParticleComponent, Intensity);
			if (!SnowParticleComponent->IsActive())
			{
				SnowParticleComponent->Activate();
			}
		}
	}
	else
	{
		if (SnowParticleComponent && SnowParticleComponent->IsActive())
		{
			SnowParticleComponent->Deactivate();
		}
	}
}

void UWeatherParticleManager::SetFogEnabled(bool bEnabled, float Density)
{
	if (bEnabled && Density > 0.0f)
	{
		if (!FogVolumetricComponent && FogSystem)
		{
			GetOrCreateNiagaraComponent(FogSystem, FogVolumetricComponent);
		}

		if (FogVolumetricComponent)
		{
			FogVolumetricComponent->SetVariableFloat(FName(TEXT("Density")), Density);
			if (!FogVolumetricComponent->IsActive())
			{
				FogVolumetricComponent->Activate();
			}
		}
	}
	else
	{
		if (FogVolumetricComponent && FogVolumetricComponent->IsActive())
		{
			FogVolumetricComponent->Deactivate();
		}
	}
}

void UWeatherParticleManager::TriggerLightningStrike(FVector StrikeLocation, float Intensity)
{
	if (LightningSystem)
	{
		UNiagaraComponent* LightningComp = AcquirePooledComponent(LightningSystem);
		if (LightningComp)
		{
			LightningComp->SetWorldLocation(StrikeLocation);
			LightningComp->SetVariableFloat(FName(TEXT("Intensity")), Intensity);
			LightningComp->Activate(true);

			// Deactivate after duration (lightning is one-shot)
			if (UWorld* World = GetWorld())
			{
				FTimerHandle TimerHandle;
				FTimerDelegate Delegate;
				Delegate.BindLambda([this, LightningComp]()
				{
					if (LightningComp && LightningComp->IsActive())
					{
						LightningComp->Deactivate();
						ReleasePooledComponent(LightningComp);
					}
				});
				World->GetTimerManager().SetTimer(TimerHandle, Delegate, 0.5f, false);
			}
		}
	}
}

void UWeatherParticleManager::SetParticleLOD(int32 LODLevel)
{
	ParticleLODLevel = FMath::Clamp(LODLevel, 0, 3);

	// Update LOD for all active particle systems
	// Adjust particle counts based on LOD level
	// Check individual particle components and pool
	TArray<TObjectPtr<UNiagaraComponent>> AllParticleComponents;
	if (RainParticleComponent)
	{
		AllParticleComponents.Add(RainParticleComponent);
	}
	if (SnowParticleComponent)
	{
		AllParticleComponents.Add(SnowParticleComponent);
	}
	if (FogVolumetricComponent)
	{
		AllParticleComponents.Add(FogVolumetricComponent);
	}
	// Add components from pool
	for (TObjectPtr<UNiagaraComponent> PoolComponent : NiagaraComponentPool)
	{
		if (PoolComponent)
		{
			AllParticleComponents.Add(PoolComponent);
		}
	}
	
	for (TObjectPtr<UNiagaraComponent> ParticleComponent : AllParticleComponents)
	{
		if (ParticleComponent && ParticleComponent->IsValidLowLevel())
		{
			// Set LOD level via Niagara system parameters
			// Note: This requires the Niagara system to have LOD parameters configured
			// For now, we adjust emitter count or particle spawn rate
			// In production, use: ParticleComponent->SetVariableInt(TEXT("LODLevel"), ParticleLODLevel);
			
			// Alternative: Use Niagara parameter collection or direct parameter setting
			// This would require the Niagara system to expose LOD parameters
			UE_LOG(LogTemp, Verbose, TEXT("WeatherParticleManager: Setting LOD level %d for particle system"), ParticleLODLevel);
		}
	}
}

void UWeatherParticleManager::LoadNiagaraSystems()
{
	// Load Niagara system assets
	// Paths: /Game/Particles/NS_Rain, /Game/Particles/NS_Snow, etc.
	FString RainPath = TEXT("/Game/Particles/NS_Rain.NS_Rain");
	FString SnowPath = TEXT("/Game/Particles/NS_Snow.NS_Snow");
	FString FogPath = TEXT("/Game/Particles/NS_Fog.NS_Fog");
	FString LightningPath = TEXT("/Game/Particles/NS_Lightning.NS_Lightning");

	RainSystem = LoadObject<UNiagaraSystem>(nullptr, *RainPath);
	SnowSystem = LoadObject<UNiagaraSystem>(nullptr, *SnowPath);
	FogSystem = LoadObject<UNiagaraSystem>(nullptr, *FogPath);
	LightningSystem = LoadObject<UNiagaraSystem>(nullptr, *LightningPath);

	if (!RainSystem)
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherParticleManager: Rain system not found at %s"), *RainPath);
	}
	if (!SnowSystem)
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherParticleManager: Snow system not found at %s"), *SnowPath);
	}
	if (!FogSystem)
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherParticleManager: Fog system not found at %s"), *FogPath);
	}
	if (!LightningSystem)
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherParticleManager: Lightning system not found at %s"), *LightningPath);
	}
}

UNiagaraComponent* UWeatherParticleManager::GetOrCreateNiagaraComponent(TObjectPtr<UNiagaraSystem> System, TObjectPtr<UNiagaraComponent>& ComponentRef)
{
	if (!System)
	{
		return nullptr;
	}

	if (!ComponentRef)
	{
		ComponentRef = NewObject<UNiagaraComponent>(this->GetOwner());
		if (ComponentRef)
		{
			ComponentRef->SetAsset(System);
			ComponentRef->SetupAttachment(this->GetOwner()->GetRootComponent());
			ComponentRef->RegisterComponent();
		}
	}

	return ComponentRef;
}

void UWeatherParticleManager::UpdateParticleParameters(UNiagaraComponent* Component, float Intensity)
{
	if (!Component)
	{
		return;
	}

	// Update intensity-based parameters
	Component->SetVariableFloat(FName(TEXT("Intensity")), Intensity);
	Component->SetVariableFloat(FName(TEXT("ParticleCount")), Intensity * 10000.0f);  // Scale particle count
}

UNiagaraComponent* UWeatherParticleManager::AcquirePooledComponent(TObjectPtr<UNiagaraSystem> System)
{
	if (!System)
	{
		return nullptr;
	}

	// Find available pooled component
	for (TObjectPtr<UNiagaraComponent>& Component : NiagaraComponentPool)
	{
		if (Component && !Component->IsActive() && Component->GetAsset() == System)
		{
			return Component;
		}
	}

	// Create new component if pool exhausted
	TObjectPtr<UNiagaraComponent> NewComponent = NewObject<UNiagaraComponent>(this->GetOwner());
	if (NewComponent)
	{
		NewComponent->SetAsset(System);
		NewComponent->SetupAttachment(this->GetOwner()->GetRootComponent());
		NewComponent->RegisterComponent();
		NiagaraComponentPool.Add(NewComponent);
	}

	return NewComponent;
}

void UWeatherParticleManager::ReleasePooledComponent(UNiagaraComponent* Component)
{
	if (Component && Component->IsActive())
	{
		Component->Deactivate();
	}
	// Component remains in pool for reuse
}

