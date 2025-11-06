// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "Engine/Engine.h"
#include "UObject/WeakObjectPtr.h"
#include "Engine/World.h"
#include "BodyBrokerGameMode.generated.h"

// Forward declarations
class ADirectionalLight;
class ASkyLight;
class AExponentialHeightFog;

// World state enum for Day/Night system
UENUM(BlueprintType)
enum class EWorldState : uint8
{
	Day			UMETA(DisplayName = "Day World"),
	Night		UMETA(DisplayName = "Night World")
};

// Delegate for world state changes
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWorldStateChanged, EWorldState, OldState, EWorldState, NewState);

/**
 * BodyBrokerGameMode - Manages dual-world system (Day/Night switching)
 * Core gameplay mode for "The Body Broker" game
 */
UCLASS()
class BODYBROKER_API ABodyBrokerGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ABodyBrokerGameMode(const FObjectInitializer& ObjectInitializer);

	// Called when the game starts
	virtual void BeginPlay() override;

	// Get current world state
	UFUNCTION(BlueprintCallable, Category = "World State")
	EWorldState GetCurrentWorldState() const { return CurrentWorldState; }

	// Check if currently in day world
	UFUNCTION(BlueprintCallable, Category = "World State")
	bool IsDayWorld() const { return CurrentWorldState == EWorldState::Day; }

	// Check if currently in night world
	UFUNCTION(BlueprintCallable, Category = "World State")
	bool IsNightWorld() const { return CurrentWorldState == EWorldState::Night; }

	// Switch to day world
	UFUNCTION(BlueprintCallable, Category = "World State")
	void SwitchToDayWorld();

	// Switch to night world
	UFUNCTION(BlueprintCallable, Category = "World State")
	void SwitchToNightWorld();

	// Switch world state (internal)
	UFUNCTION(BlueprintCallable, Category = "World State")
	void SwitchWorldState(EWorldState NewState);

	// Switch with fade transition
	UFUNCTION(BlueprintCallable, Category = "World State")
	void SwitchWorldStateWithFade(EWorldState NewState, float FadeDuration = 1.0f);

	// Event broadcast when world state changes
	UPROPERTY(BlueprintAssignable, Category = "World State")
	FOnWorldStateChanged OnWorldStateChanged;

	// Transition duration (configurable)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "World State|Transitions")
	float DefaultTransitionDuration;

	// Enable/disable transitions
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "World State|Transitions")
	bool bEnableTransitions;

protected:
	// Current world state
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "World State", SaveGame)
	EWorldState CurrentWorldState;

	// Initial world state (set in BeginPlay if not already set)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "World State")
	EWorldState InitialWorldState;

	// Handle world state transition
	virtual void OnWorldStateTransition(EWorldState OldState, EWorldState NewState);

	// Lighting adjustment functions
	UFUNCTION(BlueprintCallable, Category = "World State|Lighting")
	void AdjustLightingForWorldState(EWorldState WorldState);

	UFUNCTION(BlueprintCallable, Category = "World State|Lighting")
	void ApplyDayLighting();

	UFUNCTION(BlueprintCallable, Category = "World State|Lighting")
	void ApplyNightLighting();

	// Lighting configuration
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "World State|Lighting")
	float DayLightIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "World State|Lighting")
	FLinearColor DayLightColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "World State|Lighting")
	float NightLightIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "World State|Lighting")
	FLinearColor NightLightColor;

private:
	// Validate world state transition
	bool CanTransitionToState(EWorldState NewState) const;

	// Fade transition helpers
	void StartFadeTransition(EWorldState TargetState, float Duration);
	void CompleteFadeTransition();
	void OnFadeOutComplete();

	// Timer handle for fade transitions
	FTimerHandle FadeTransitionTimer;

	// Target state during transition
	EWorldState PendingWorldState;
	
	// Transition state tracking
	bool bTransitionInProgress;

	// Lighting helpers
	void FindLightingActors();
	ADirectionalLight* FindDirectionalLight() const;
	ASkyLight* FindSkyLight() const;
	AExponentialHeightFog* FindExponentialHeightFog() const;

	// Cached lighting actors (weak references)
	TWeakObjectPtr<ADirectionalLight> CachedDirectionalLight;
	TWeakObjectPtr<ASkyLight> CachedSkyLight;
	TWeakObjectPtr<AExponentialHeightFog> CachedExponentialHeightFog;
};

