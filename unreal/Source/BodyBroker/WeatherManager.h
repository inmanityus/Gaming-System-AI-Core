// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Materials/MaterialParameterCollection.h"
#include "AudioManager.h"  // For EWeatherState enum
#include "WeatherManager.generated.h"

class UTimeOfDayManager;
class UAudioManager;
class UGameEventBus;
class UWeatherPresetLibrary;
class UWeatherPreset;

// Forward declarations
class UMaterialParameterCollection;
class UMaterialParameterCollectionInstance;

// EWeatherState is defined in AudioManager.h - using shared enum

/**
 * Weather transition interpolation mode
 */
UENUM(BlueprintType)
enum class EWeatherTransitionMode : uint8
{
	Linear			UMETA(DisplayName = "Linear"),
	EaseIn			UMETA(DisplayName = "Ease In"),
	EaseOut			UMETA(DisplayName = "Ease Out"),
	EaseInOut		UMETA(DisplayName = "Ease In Out"),
	SmoothStep		UMETA(DisplayName = "Smooth Step")
};

/**
 * Weather parameter data structure
 */
USTRUCT(BlueprintType)
struct FWeatherParameters
{
	GENERATED_BODY()

	// Rain intensity (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float RainIntensity;

	// Snow intensity (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float SnowIntensity;

	// Fog density (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float FogDensity;

	// Wind strength (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float WindStrength;

	// Wind direction (degrees, 0 = North, 90 = East)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float WindDirection;

	// Temperature (Celsius)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float Temperature;

	// Humidity (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float Humidity;

	// Cloud coverage (0.0 to 1.0)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float CloudCoverage;

	// Lightning intensity (0.0 to 1.0, for STORM state)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float LightningIntensity;

	// Wetness factor (0.0 to 1.0, accumulates from rain)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float Wetness;

	// Snow accumulation (0.0 to 1.0, accumulates from snow)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather")
	float SnowAccumulation;

	FWeatherParameters()
		: RainIntensity(0.0f)
		, SnowIntensity(0.0f)
		, FogDensity(0.0f)
		, WindStrength(0.0f)
		, WindDirection(0.0f)
		, Temperature(20.0f)
		, Humidity(0.5f)
		, CloudCoverage(0.0f)
		, LightningIntensity(0.0f)
		, Wetness(0.0f)
		, SnowAccumulation(0.0f)
	{}
};

/**
 * WeatherManager - Manages dynamic weather system
 * WS-001: Core & State Machine
 */
UCLASS()
class BODYBROKER_API UWeatherManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Get the singleton instance of WeatherManager.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	static UWeatherManager* Get(const UObject* WorldContext);

	/**
	 * Set weather state with transition.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	void SetWeatherState(EWeatherState NewState, float TransitionDuration = 5.0f);

	/**
	 * Set weather state immediately (no transition).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	void SetWeatherStateImmediate(EWeatherState NewState);

	/**
	 * Get current weather state.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	EWeatherState GetCurrentWeatherState() const { return CurrentWeatherState; }

	/**
	 * Get current weather parameters.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	FWeatherParameters GetCurrentWeatherParameters() const { return CurrentParameters; }

	/**
	 * Set weather intensity (0.0 to 1.0).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	void SetWeatherIntensity(float Intensity);

	/**
	 * Get weather intensity.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	float GetWeatherIntensity() const { return CurrentIntensity; }

	/**
	 * Set transition mode.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	void SetTransitionMode(EWeatherTransitionMode Mode) { TransitionMode = Mode; }

	/**
	 * Update MPC_Weather Material Parameter Collection.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather")
	void UpdateMaterialParameters();

	/**
	 * Event broadcasted when weather state changes.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWeatherStateChanged, EWeatherState, OldState, EWeatherState, NewState);
	UPROPERTY(BlueprintAssignable, Category = "Weather|Events")
	FOnWeatherStateChanged OnWeatherStateChanged;

	/**
	 * Event broadcasted when weather parameters change.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWeatherParametersChanged, const FWeatherParameters&, Parameters);
	UPROPERTY(BlueprintAssignable, Category = "Weather|Events")
	FOnWeatherParametersChanged OnWeatherParametersChanged;

	/**
	 * Event broadcasted when lightning strikes.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnLightningStrike, FVector, StrikeLocation, float, Intensity);
	UPROPERTY(BlueprintAssignable, Category = "Weather|Events")
	FOnLightningStrike OnLightningStrike;

	/**
	 * Apply weather preset (WS-004).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather|WS-004")
	void ApplyWeatherPreset(UWeatherPreset* Preset);

	/**
	 * Set weather preset library (WS-004).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather|WS-004")
	void SetWeatherPresetLibrary(UWeatherPresetLibrary* Library);

	/**
	 * Get random weather based on season and time of day (WS-004).
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather|WS-004")
	void ApplyRandomWeatherBySeason(float SeasonProgress, const FString& TimeOfDayState);

private:
	// Current weather state
	UPROPERTY()
	EWeatherState CurrentWeatherState;

	// Previous weather state (for transitions)
	UPROPERTY()
	EWeatherState PreviousWeatherState;

	// Current weather parameters
	UPROPERTY()
	FWeatherParameters CurrentParameters;

	// Target weather parameters (for interpolation)
	UPROPERTY()
	FWeatherParameters TargetParameters;

	// Current interpolation progress (0.0 to 1.0)
	UPROPERTY()
	float TransitionProgress;

	// Current transition duration
	UPROPERTY()
	float CurrentTransitionDuration;

	// Transition mode
	UPROPERTY()
	EWeatherTransitionMode TransitionMode;

	// Current weather intensity
	UPROPERTY()
	float CurrentIntensity;

	// Material Parameter Collection reference
	UPROPERTY()
	TObjectPtr<UMaterialParameterCollection> WeatherMPC;

	// Material Parameter Collection Instance (runtime)
	UPROPERTY()
	TObjectPtr<UMaterialParameterCollectionInstance> WeatherMPCInstance;

	// Weather preset library (WS-004)
	UPROPERTY()
	TObjectPtr<UWeatherPresetLibrary> WeatherPresetLibrary;

	// Timer handle for transition updates
	FTimerHandle TransitionTimerHandle;

	// Update interval for transitions (seconds)
	static constexpr float TRANSITION_UPDATE_INTERVAL = 0.1f;

	// Get weather parameters for state
	FWeatherParameters GetParametersForState(EWeatherState State, float Intensity) const;

	// Interpolate between two parameter sets
	FWeatherParameters InterpolateParameters(const FWeatherParameters& From, const FWeatherParameters& To, float Alpha) const;

	// Update transition (called periodically during transitions)
	void UpdateTransition(float DeltaTime);

	// Complete transition
	void CompleteTransition();

	// Apply interpolation curve based on mode
	float ApplyInterpolationCurve(float Alpha) const;

	// Load MPC_Weather asset
	void LoadWeatherMPC();

	// Trigger lightning strike event (for STORM/BLIZZARD)
	void TriggerLightningStrike();
};

