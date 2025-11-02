// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AudioManager.generated.h"

class USoundBase;
class UAudioComponent;
class USoundAttenuation;
class USoundEffectSubmixPreset;
class IHttpRequest;
class IHttpResponse;
class UTimeOfDayManager;

// Forward declaration for HTTP pointers
typedef TSharedPtr<IHttpRequest, ESPMode::ThreadSafe> FHttpRequestPtr;
typedef TSharedPtr<IHttpResponse, ESPMode::ThreadSafe> FHttpResponsePtr;

UENUM(BlueprintType)
enum class EAudioCategory : uint8
{
	Voice		UMETA(DisplayName = "Voice"),
	Ambient		UMETA(DisplayName = "Ambient"),
	Music		UMETA(DisplayName = "Music"),
	Effect		UMETA(DisplayName = "Effect"),
	UI			UMETA(DisplayName = "UI")
};

/**
 * Weather states for audio integration
 * Matches WeatherManager backend weather states (15 total)
 */
UENUM(BlueprintType)
enum class EWeatherState : uint8
{
	CLEAR			UMETA(DisplayName = "Clear"),
	PARTLY_CLOUDY	UMETA(DisplayName = "Partly Cloudy"),
	CLOUDY			UMETA(DisplayName = "Cloudy"),
	RAIN			UMETA(DisplayName = "Rain"),
	HEAVY_RAIN		UMETA(DisplayName = "Heavy Rain"),
	STORM			UMETA(DisplayName = "Storm"),
	FOG				UMETA(DisplayName = "Fog"),
	MIST			UMETA(DisplayName = "Mist"),
	SNOW			UMETA(DisplayName = "Snow"),
	HEAVY_SNOW		UMETA(DisplayName = "Heavy Snow"),
	BLIZZARD		UMETA(DisplayName = "Blizzard"),
	WINDY			UMETA(DisplayName = "Windy"),
	EXTREME_HEAT	UMETA(DisplayName = "Extreme Heat"),
	EXTREME_COLD	UMETA(DisplayName = "Extreme Cold"),
	NUM				UMETA(Hidden)
};

/**
 * Zone types for ambient audio profiles
 */
UENUM(BlueprintType)
enum class EZoneType : uint8
{
	Exterior		UMETA(DisplayName = "Exterior"),
	Interior		UMETA(DisplayName = "Interior"),
	SemiExterior	UMETA(DisplayName = "Semi-Exterior")
};

/**
 * AudioManager - Manages audio playback from backend API
 * Integrates with backend audio service for voice and audio playback
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UAudioManager : public UActorComponent
{
	GENERATED_BODY()

public:
	UAudioManager(const FObjectInitializer& ObjectInitializer);

	// Called when the game starts
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void BeginDestroy() override;

	// Initialize AudioManager with backend URL
	UFUNCTION(BlueprintCallable, Category = "Audio Manager")
	void Initialize(const FString& BackendURL);

	// Play audio from backend API
	UFUNCTION(BlueprintCallable, Category = "Audio Manager")
	void PlayAudioFromBackend(const FString& AudioID, EAudioCategory Category, float Volume = 1.0f);

	// Stop audio playback
	UFUNCTION(BlueprintCallable, Category = "Audio Manager")
	void StopAudio(const FString& AudioID);

	// Set master volume
	UFUNCTION(BlueprintCallable, Category = "Audio Manager")
	void SetMasterVolume(float Volume);

	// Set category volume
	UFUNCTION(BlueprintCallable, Category = "Audio Manager")
	void SetCategoryVolume(EAudioCategory Category, float Volume);

	// Check if audio is playing
	UFUNCTION(BlueprintCallable, Category = "Audio Manager")
	bool IsAudioPlaying(const FString& AudioID) const;

	// ============================================================
	// VA-002: Ambient & Weather Audio Integration Methods
	// ============================================================

	// Time-of-day ambient management
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void SetTimeOfDayAmbient(const FString& TimeState);

	// Weather audio layer management
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void SetWeatherAudioLayer(EWeatherState WeatherState, float Intensity);

	// Zone-based ambient profile
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void SetZoneAmbientProfile(const FString& ZoneProfileName);

	// Audio ducking system
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void DuckAudioByAmount(EAudioCategory Category, float DuckAmount, float Duration);

	// Update ambient profile (time + zone combined)
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void UpdateAmbientProfile(const FString& TimeState, const FString& ZoneProfileName);

	// Trigger weather audio transition
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void TriggerWeatherTransition(EWeatherState OldState, EWeatherState NewState, float Intensity, float TransitionDuration = 5.0f);

	// Play thunder strike event (event-based audio)
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void PlayThunderStrike(float Volume = 0.85f);

	// Calculate audio occlusion (raycast-based)
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	float CalculateAudioOcclusion(const FVector& SourceLocation, const FVector& ListenerLocation) const;

	// Set reverb preset based on zone context
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	void SetReverbPreset(const FString& PresetName, float TransitionDuration = 3.0f);

	// Get current time-of-day ambient state
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	FString GetCurrentTimeOfDayAmbient() const;

	// Get current weather audio state
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	EWeatherState GetCurrentWeatherState() const;

	// Get current zone ambient profile
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|VA-002")
	FString GetCurrentZoneAmbientProfile() const;

private:
	// Backend API URL
	FString BackendURL;

	// Audio components by ID
	UPROPERTY()
	TMap<FString, UAudioComponent*> ActiveAudioComponents;

	// Category volume settings
	UPROPERTY()
	TMap<EAudioCategory, float> CategoryVolumes;

	// Master volume
	UPROPERTY()
	float MasterVolume;

	// HTTP request handler
	void OnAudioRequestComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
	void HandleAudioData(const FString& AudioID, EAudioCategory Category, float Volume, TArray<uint8> AudioData);
	void OnAudioRequestFailed(const FString& AudioID, const FString& Error);

	// Create audio component for playback
	UAudioComponent* CreateAudioComponent(const FString& AudioID, EAudioCategory Category, float Volume);

	// Store request context for HTTP callbacks
	UPROPERTY()
	TMap<FString, FString> PendingAudioIDs;  // URL -> AudioID
	
	UPROPERTY()
	TMap<FString, EAudioCategory> PendingAudioCategories;  // URL -> Category
	
	UPROPERTY()
	TMap<FString, float> PendingAudioVolumes;  // URL -> Volume

	// ============================================================
	// VA-002: Private Implementation Methods
	// ============================================================

	// Initialize VA-002 systems (called from BeginPlay)
	void InitializeVA002Systems();

	// Bind to TimeOfDayManager events
	void BindToTimeOfDayManager();

	// Handle time state changed event
	UFUNCTION()
	void OnTimeStateChanged(FString OldState, FString NewState);

	// Crossfade between two audio profiles
	void CrossfadeAmbientProfile(const FString& OldProfile, const FString& NewProfile, float Duration);

	// Apply ducking to category smoothly
	void ApplyDucking(EAudioCategory Category, float TargetDuckAmount, float Duration);

	// Update weather audio layers based on state and intensity
	void UpdateWeatherLayers(EWeatherState WeatherState, float Intensity);

	// Load MetaSound template by name
	USoundBase* LoadMetaSoundTemplate(const FString& TemplateName);

	// Get weather audio layer names for state
	void GetWeatherAudioLayers(EWeatherState WeatherState, FString& OutLayer1, FString& OutLayer2);

	// Update reverb send level smoothly
	void UpdateReverbSendLevel(float TargetLevel, float Duration);

	// VA-002 State Tracking
	UPROPERTY()
	FString CurrentTimeOfDayState;  // "dawn", "day", "dusk", "night"

	UPROPERTY()
	EWeatherState CurrentWeatherState;

	UPROPERTY()
	float CurrentWeatherIntensity;

	UPROPERTY()
	FString CurrentZoneProfile;

	UPROPERTY()
	FString CurrentReverbPreset;

	// Active audio components for VA-002 systems
	UPROPERTY()
	UAudioComponent* TimeOfDayAmbientComponent;  // Current time-of-day ambient

	UPROPERTY()
	TMap<EWeatherState, UAudioComponent*> WeatherLayerComponents;  // Weather audio layers

	UPROPERTY()
	UAudioComponent* ZoneAmbientComponent;  // Zone-specific ambient

	// Ducking state tracking
	UPROPERTY()
	TMap<EAudioCategory, float> CurrentDuckAmounts;  // Current duck amount per category

	// Timer handles for transitions and ducking
	UPROPERTY()
	TMap<EAudioCategory, FTimerHandle> DuckingTimerHandles;

	UPROPERTY()
	FTimerHandle AmbientCrossfadeTimerHandle;

	UPROPERTY()
	FTimerHandle ReverbTransitionTimerHandle;

	// MetaSound template cache
	UPROPERTY()
	TMap<FString, USoundBase*> MetaSoundTemplateCache;

	// Transition state
	UPROPERTY()
	FString TransitioningToProfile;

	UPROPERTY()
	float TransitionProgress;

	// Crossfade state tracking (for lambda safety - all member variables)
	UPROPERTY()
	int32 CrossfadeStepsCompleted;

	UPROPERTY()
	UAudioComponent* PendingAmbientComponent;  // Component being crossfaded in

	// Crossfade parameters (stored as members to avoid lambda capture issues)
	UPROPERTY()
	float CurrentCategoryVolume;

	UPROPERTY()
	int32 CurrentFadeSteps;

	UPROPERTY()
	float CurrentStepDuration;

	// Ducking state (shared pointer stored as member)
	struct FDuckingState
	{
		int32 StepCount = 0;
		float StartDuck = 0.0f;
		float TargetDuck = 0.0f;
		int32 TotalSteps = 0;
	};
	UPROPERTY()
	TSharedPtr<FDuckingState> CurrentDuckingState;

	// Constants
	static constexpr float DEFAULT_AMBIENT_CROSSFADE_DURATION = 30.0f;  // 30 seconds for time-of-day
	static constexpr float DEFAULT_WEATHER_TRANSITION_DURATION = 5.0f;  // 5 seconds for weather
	static constexpr float DEFAULT_ZONE_TRANSITION_DURATION = 5.0f;  // 5 seconds for zones
	static constexpr float DEFAULT_REVERB_TRANSITION_DURATION = 3.0f;  // 3 seconds for reverb
	static constexpr float MAX_OCCLUSION_DISTANCE = 5000.0f;  // 5000 units max for occlusion checks
};

