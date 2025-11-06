// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyBrokerGameMode.h"
#include "Engine/Engine.h"
#include "TimerManager.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "EngineUtils.h"

ABodyBrokerGameMode::ABodyBrokerGameMode(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, CurrentWorldState(EWorldState::Day)
	, InitialWorldState(EWorldState::Day)
	, DefaultTransitionDuration(1.0f)
	, bEnableTransitions(true)
	, PendingWorldState(EWorldState::Day)
	, bTransitionInProgress(false)
	, DayLightIntensity(3.0f)
	, DayLightColor(1.0f, 0.95f, 0.9f, 1.0f)  // Warm daylight
	, NightLightIntensity(0.5f)
	, NightLightColor(0.2f, 0.25f, 0.4f, 1.0f)  // Cool moonlight
{
}

void ABodyBrokerGameMode::BeginPlay()
{
	Super::BeginPlay();

	// Initialize world state if not already set
	if (CurrentWorldState == EWorldState::Day && InitialWorldState != EWorldState::Day)
	{
		// Set initial state without transition (first time only)
		CurrentWorldState = InitialWorldState;
	}

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: World state initialized to %s"), 
		CurrentWorldState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));
}

void ABodyBrokerGameMode::SwitchToDayWorld()
{
	SwitchWorldState(EWorldState::Day);
}

void ABodyBrokerGameMode::SwitchToNightWorld()
{
	SwitchWorldState(EWorldState::Night);
}

void ABodyBrokerGameMode::SwitchWorldState(EWorldState NewState)
{
	if (NewState == CurrentWorldState)
	{
		UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerGameMode: Already in %s world, skipping transition"),
			NewState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));
		return;
	}

	if (!CanTransitionToState(NewState))
	{
		UE_LOG(LogTemp, Warning, TEXT("BodyBrokerGameMode: Cannot transition to %s world"),
			NewState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));
		return;
	}

	if (bEnableTransitions && bTransitionInProgress == false)
	{
		// Use fade transition if enabled
		StartFadeTransition(NewState, DefaultTransitionDuration);
		return;
	}

	// Immediate transition (no fade)
	EWorldState OldState = CurrentWorldState;
	CurrentWorldState = NewState;

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Transitioning from %s to %s world (immediate)"),
		OldState == EWorldState::Day ? TEXT("Day") : TEXT("Night"),
		NewState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));

	// Notify systems of state change
	OnWorldStateTransition(OldState, NewState);

	// Broadcast delegate for Blueprint/other systems
	OnWorldStateChanged.Broadcast(OldState, NewState);
}

void ABodyBrokerGameMode::SwitchWorldStateWithFade(EWorldState NewState, float FadeDuration)
{
	if (NewState == CurrentWorldState)
	{
		UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerGameMode: Already in %s world, skipping transition"),
			NewState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));
		return;
	}

	if (!CanTransitionToState(NewState))
	{
		UE_LOG(LogTemp, Warning, TEXT("BodyBrokerGameMode: Cannot transition to %s world"),
			NewState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));
		return;
	}

	StartFadeTransition(NewState, FadeDuration);
}

void ABodyBrokerGameMode::OnWorldStateTransition(EWorldState OldState, EWorldState NewState)
{
	// Apply lighting adjustments for new world state
	AdjustLightingForWorldState(NewState);
}

bool ABodyBrokerGameMode::CanTransitionToState(EWorldState NewState) const
{
	// Prevent new transition if one is in progress
	if (bTransitionInProgress)
	{
		return false;
	}

	// Basic validation - always allow transition for now
	// Future: Add cooldowns, restrictions, etc.
	return true;
}

void ABodyBrokerGameMode::StartFadeTransition(EWorldState TargetState, float Duration)
{
	if (bTransitionInProgress)
	{
		UE_LOG(LogTemp, Warning, TEXT("BodyBrokerGameMode: Transition already in progress, ignoring new request"));
		return;
	}

	PendingWorldState = TargetState;
	bTransitionInProgress = true;

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Starting fade transition to %s world (duration: %.2f)"),
		TargetState == EWorldState::Day ? TEXT("Day") : TEXT("Night"), Duration);

	// Clear any existing timer
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(FadeTransitionTimer);

		// Fade out (half duration)
		float FadeOutTime = Duration * 0.5f;
		FTimerDelegate FadeOutDelegate;
		FadeOutDelegate.BindUObject(this, &ABodyBrokerGameMode::OnFadeOutComplete);
		World->GetTimerManager().SetTimer(
			FadeTransitionTimer,
			FadeOutDelegate,
			FadeOutTime,
			false
		);
	}

	// TODO: Trigger fade out visual effect (UMG widget fade, post-process fade, etc.)
	// This will be handled in Blueprint or visual effects system
}

void ABodyBrokerGameMode::OnFadeOutComplete()
{
	EWorldState TargetState = PendingWorldState;
	UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Fade out complete, switching world state"));

	// Perform the actual state change while faded
	EWorldState OldState = CurrentWorldState;
	CurrentWorldState = TargetState;

	// Notify systems of state change
	OnWorldStateTransition(OldState, TargetState);

	// Broadcast delegate
	OnWorldStateChanged.Broadcast(OldState, TargetState);

	// Start fade in
	if (UWorld* World = GetWorld())
	{
		float FadeInTime = DefaultTransitionDuration * 0.5f;
		FTimerDelegate FadeInDelegate;
		FadeInDelegate.BindUObject(this, &ABodyBrokerGameMode::CompleteFadeTransition);
		World->GetTimerManager().SetTimer(
			FadeTransitionTimer,
			FadeInDelegate,
			FadeInTime,
			false
		);
	}

	// TODO: Trigger fade in visual effect
}

void ABodyBrokerGameMode::CompleteFadeTransition()
{
	EWorldState TargetState = PendingWorldState;
	UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Fade transition complete to %s world"),
		TargetState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));

	bTransitionInProgress = false;
	PendingWorldState = EWorldState::Day; // Reset

	// TODO: Trigger any post-transition effects
}

void ABodyBrokerGameMode::AdjustLightingForWorldState(EWorldState WorldState)
{
	if (WorldState == EWorldState::Day)
	{
		ApplyDayLighting();
	}
	else
	{
		ApplyNightLighting();
	}
}

void ABodyBrokerGameMode::ApplyDayLighting()
{
	FindLightingActors();

	// Adjust DirectionalLight
	if (ADirectionalLight* DirectionalLight = FindDirectionalLight())
	{
		UDirectionalLightComponent* LightComp = DirectionalLight->GetComponentByClass<UDirectionalLightComponent>();
		if (LightComp)
		{
			LightComp->SetIntensity(DayLightIntensity);
			LightComp->SetLightColor(DayLightColor);
			UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Applied day lighting (intensity: %.2f)"), DayLightIntensity);
		}
	}

	// Adjust SkyLight
	if (ASkyLight* SkyLight = FindSkyLight())
	{
		USkyLightComponent* SkyLightComp = SkyLight->GetLightComponent();
		if (SkyLightComp)
		{
			SkyLightComp->SetIntensity(DayLightIntensity * 0.3f);  // SkyLight typically lower
			UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Applied day sky lighting"));
		}
	}
}

void ABodyBrokerGameMode::ApplyNightLighting()
{
	FindLightingActors();

	// Adjust DirectionalLight
	if (ADirectionalLight* DirectionalLight = FindDirectionalLight())
	{
		UDirectionalLightComponent* LightComp = DirectionalLight->GetComponentByClass<UDirectionalLightComponent>();
		if (LightComp)
		{
			LightComp->SetIntensity(NightLightIntensity);
			LightComp->SetLightColor(NightLightColor);
			UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Applied night lighting (intensity: %.2f)"), NightLightIntensity);
		}
	}

	// Adjust SkyLight
	if (ASkyLight* SkyLight = FindSkyLight())
	{
		USkyLightComponent* SkyLightComp = SkyLight->GetLightComponent();
		if (SkyLightComp)
		{
			SkyLightComp->SetIntensity(NightLightIntensity * 0.3f);
			UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Applied night sky lighting"));
		}
	}
}

void ABodyBrokerGameMode::FindLightingActors()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// Find DirectionalLight
	if (!CachedDirectionalLight.IsValid())
	{
		for (TActorIterator<ADirectionalLight> ActorItr(World); ActorItr; ++ActorItr)
		{
			ADirectionalLight* Light = *ActorItr;
			if (IsValid(Light))
			{
				CachedDirectionalLight = Light;
				break;
			}
		}
	}

	// Find SkyLight
	if (!CachedSkyLight.IsValid())
	{
		for (TActorIterator<ASkyLight> ActorItr(World); ActorItr; ++ActorItr)
		{
			ASkyLight* SkyLightActor = *ActorItr;
			if (IsValid(SkyLightActor))
			{
				CachedSkyLight = SkyLightActor;
				break;
			}
		}
	}

	// Find ExponentialHeightFog
	if (!CachedExponentialHeightFog.IsValid())
	{
		for (TActorIterator<AExponentialHeightFog> ActorItr(World); ActorItr; ++ActorItr)
		{
			AExponentialHeightFog* Fog = *ActorItr;
			if (IsValid(Fog))
			{
				CachedExponentialHeightFog = Fog;
				break;
			}
		}
	}
}

ADirectionalLight* ABodyBrokerGameMode::FindDirectionalLight() const
{
	if (CachedDirectionalLight.IsValid())
	{
		return CachedDirectionalLight.Get();
	}
	return nullptr;
}

ASkyLight* ABodyBrokerGameMode::FindSkyLight() const
{
	if (CachedSkyLight.IsValid())
	{
		return CachedSkyLight.Get();
	}
	return nullptr;
}

AExponentialHeightFog* ABodyBrokerGameMode::FindExponentialHeightFog() const
{
	if (CachedExponentialHeightFog.IsValid())
	{
		return CachedExponentialHeightFog.Get();
	}
	return nullptr;
}

