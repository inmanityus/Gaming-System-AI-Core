// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyBrokerGameMode.h"
#include "Engine/Engine.h"

ABodyBrokerGameMode::ABodyBrokerGameMode(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, CurrentWorldState(EWorldState::Day)
	, InitialWorldState(EWorldState::Day)
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

	EWorldState OldState = CurrentWorldState;
	CurrentWorldState = NewState;

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerGameMode: Transitioning from %s to %s world"),
		OldState == EWorldState::Day ? TEXT("Day") : TEXT("Night"),
		NewState == EWorldState::Day ? TEXT("Day") : TEXT("Night"));

	// Notify systems of state change
	OnWorldStateTransition(OldState, NewState);

	// Broadcast delegate for Blueprint/other systems
	OnWorldStateChanged.Broadcast(OldState, NewState);
}

void ABodyBrokerGameMode::OnWorldStateTransition(EWorldState OldState, EWorldState NewState)
{
	// Base implementation - can be overridden in derived classes
	// Future: Add fade transitions, lighting changes, etc.
}

bool ABodyBrokerGameMode::CanTransitionToState(EWorldState NewState) const
{
	// Basic validation - always allow transition for now
	// Future: Add cooldowns, restrictions, etc.
	return true;
}

