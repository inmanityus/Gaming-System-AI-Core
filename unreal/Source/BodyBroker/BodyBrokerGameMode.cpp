// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyBrokerGameMode.h"
#include "Engine/Engine.h"
#include "TimerManager.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"

ABodyBrokerGameMode::ABodyBrokerGameMode(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, CurrentWorldState(EWorldState::Day)
	, InitialWorldState(EWorldState::Day)
	, DefaultTransitionDuration(1.0f)
	, bEnableTransitions(true)
	, PendingWorldState(EWorldState::Day)
	, bTransitionInProgress(false)
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
	// Base implementation - can be overridden in derived classes
	// Future: Add fade transitions, lighting changes, etc.
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

