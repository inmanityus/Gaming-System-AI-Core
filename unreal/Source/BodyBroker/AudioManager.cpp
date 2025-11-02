// Copyright Epic Games, Inc. All Rights Reserved.

#include "AudioManager.h"
#include "Components/AudioComponent.h"
#include "Http.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "Sound/SoundAttenuation.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "TimerManager.h"
#include "Kismet/GameplayStatics.h"
#include "TimeOfDayManager.h"
#include "Engine/GameInstance.h"

UAudioManager::UAudioManager(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, MasterVolume(1.0f)
{
	PrimaryComponentTick.bCanEverTick = false;

	// Initialize default category volumes
	CategoryVolumes.Add(EAudioCategory::Voice, 1.0f);
	CategoryVolumes.Add(EAudioCategory::Ambient, 0.8f);
	CategoryVolumes.Add(EAudioCategory::Music, 0.7f);
	CategoryVolumes.Add(EAudioCategory::Effect, 1.0f);
	CategoryVolumes.Add(EAudioCategory::UI, 0.9f);
}

void UAudioManager::BeginPlay()
{
	Super::BeginPlay();
	
	UE_LOG(LogTemp, Log, TEXT("AudioManager: BeginPlay"));

	// Initialize VA-002 systems
	InitializeVA002Systems();
}

void UAudioManager::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Stop all VA-002 audio components
	if (TimeOfDayAmbientComponent)
	{
		TimeOfDayAmbientComponent->Stop();
		TimeOfDayAmbientComponent->DestroyComponent();
		TimeOfDayAmbientComponent = nullptr;
	}

	if (PendingAmbientComponent)
	{
		PendingAmbientComponent->Stop();
		PendingAmbientComponent->DestroyComponent();
		PendingAmbientComponent = nullptr;
	}

	if (ZoneAmbientComponent)
	{
		ZoneAmbientComponent->Stop();
		ZoneAmbientComponent->DestroyComponent();
		ZoneAmbientComponent = nullptr;
	}

	for (auto& Pair : WeatherLayerComponents)
	{
		if (Pair.Value)
		{
			Pair.Value->Stop();
			Pair.Value->DestroyComponent();
		}
	}
	WeatherLayerComponents.Empty();

	// Stop all regular audio components
	for (auto& Pair : ActiveAudioComponents)
	{
		if (Pair.Value)
		{
			Pair.Value->Stop();
			Pair.Value->DestroyComponent();
		}
	}
	ActiveAudioComponents.Empty();

	// Clear timers
	if (UWorld* World = GetWorld())
	{
		if (FTimerManager* TimerManager = &World->GetTimerManager())
		{
			TimerManager->ClearTimer(AmbientCrossfadeTimerHandle);
			TimerManager->ClearTimer(ReverbTransitionTimerHandle);
			for (auto& Pair : DuckingTimerHandles)
			{
				TimerManager->ClearTimer(Pair.Value);
			}
		}
	}

	Super::EndPlay(EndPlayReason);
}

void UAudioManager::BeginDestroy()
{
	// Clear all timers before destruction
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearAllTimersForObject(this);
	}

	// Clear ducking state
	CurrentDuckingState.Reset();
	PendingAmbientComponent = nullptr;

	Super::BeginDestroy();
}

void UAudioManager::Initialize(const FString& InBackendURL)
{
	BackendURL = InBackendURL;
	UE_LOG(LogTemp, Log, TEXT("AudioManager: Initialized with backend URL: %s"), *BackendURL);
}

void UAudioManager::PlayAudioFromBackend(const FString& AudioID, EAudioCategory Category, float Volume)
{
	// Check if already playing
	if (IsAudioPlaying(AudioID))
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioManager: Audio %s is already playing"), *AudioID);
		return;
	}

	// Build API URL
	FString RequestURL = FString::Printf(TEXT("%s/audio/%s"), *BackendURL, *AudioID);

	// Create HTTP request
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->OnProcessRequestComplete().BindUObject(this, &UAudioManager::OnAudioRequestComplete);
	
	// Store request context (use request URL as key)
	PendingAudioIDs.Add(RequestURL, AudioID);
	PendingAudioCategories.Add(RequestURL, Category);
	PendingAudioVolumes.Add(RequestURL, Volume);
	
	HttpRequest->SetURL(RequestURL);
	HttpRequest->SetVerb(TEXT("GET"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("audio/wav"));
	HttpRequest->ProcessRequest();

	UE_LOG(LogTemp, Log, TEXT("AudioManager: Requesting audio %s from %s"), *AudioID, *RequestURL);
}

void UAudioManager::StopAudio(const FString& AudioID)
{
	UAudioComponent** AudioCompPtr = ActiveAudioComponents.Find(AudioID);
	if (AudioCompPtr && *AudioCompPtr)
	{
		(*AudioCompPtr)->Stop();
		(*AudioCompPtr)->DestroyComponent();
		ActiveAudioComponents.Remove(AudioID);
		UE_LOG(LogTemp, Log, TEXT("AudioManager: Stopped audio %s"), *AudioID);
	}
}

void UAudioManager::SetMasterVolume(float Volume)
{
	MasterVolume = FMath::Clamp(Volume, 0.0f, 1.0f);
	
	// Note: Category volume lookup requires storing category per audio component
	// For now, update based on stored category information
	// This is a simplified version - in production, store category with each component

	UE_LOG(LogTemp, Log, TEXT("AudioManager: Master volume set to %f"), MasterVolume);
}

void UAudioManager::SetCategoryVolume(EAudioCategory Category, float Volume)
{
	float ClampedVolume = FMath::Clamp(Volume, 0.0f, 1.0f);
	CategoryVolumes.Add(Category, ClampedVolume);
	
	UE_LOG(LogTemp, Log, TEXT("AudioManager: Category %d volume set to %f"), (int32)Category, ClampedVolume);
}

bool UAudioManager::IsAudioPlaying(const FString& AudioID) const
{
	const UAudioComponent* AudioComp = ActiveAudioComponents.FindRef(AudioID);
	return AudioComp && AudioComp->IsPlaying();
}

void UAudioManager::OnAudioRequestComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
	if (!Request.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("AudioManager: Invalid request"));
		return;
	}

	// Get stored context using request URL
	FString RequestURL = Request->GetURL();
	FString* AudioIDPtr = PendingAudioIDs.Find(RequestURL);
	EAudioCategory* CategoryPtr = PendingAudioCategories.Find(RequestURL);
	float* VolumePtr = PendingAudioVolumes.Find(RequestURL);
	
	if (!AudioIDPtr || !CategoryPtr || !VolumePtr)
	{
		UE_LOG(LogTemp, Error, TEXT("AudioManager: Request context not found for URL: %s"), *RequestURL);
		return;
	}

	FString AudioID = *AudioIDPtr;
	EAudioCategory Category = *CategoryPtr;
	float Volume = *VolumePtr;
	
	PendingAudioIDs.Remove(RequestURL);
	PendingAudioCategories.Remove(RequestURL);
	PendingAudioVolumes.Remove(RequestURL);

	if (!bWasSuccessful || !Response.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("AudioManager: Failed to receive audio %s"), *AudioID);
		OnAudioRequestFailed(AudioID, TEXT("HTTP request failed"));
		return;
	}

	if (Response->GetResponseCode() != 200)
	{
		UE_LOG(LogTemp, Error, TEXT("AudioManager: Audio request failed with code %d"), Response->GetResponseCode());
		OnAudioRequestFailed(AudioID, FString::Printf(TEXT("HTTP %d"), Response->GetResponseCode()));
		return;
	}

	// Get audio data
	TArray<uint8> AudioData = Response->GetContent();
	HandleAudioData(AudioID, Category, Volume, AudioData);
}

void UAudioManager::HandleAudioData(const FString& AudioID, EAudioCategory Category, float Volume, TArray<uint8> AudioData)
{
	// Create sound wave from data
	USoundWave* SoundWave = NewObject<USoundWave>(this);
	if (SoundWave)
	{
		// Note: This is a simplified version. In production, you'd need proper audio format parsing
		// (WAV, OGG, etc.) and proper sound wave setup
		UE_LOG(LogTemp, Warning, TEXT("AudioManager: Sound wave creation from raw data requires proper format parsing"));
	}

	// Create audio component and play
	UAudioComponent* AudioComp = CreateAudioComponent(AudioID, Category, Volume);
	if (AudioComp && SoundWave)
	{
		AudioComp->SetSound(SoundWave);
		AudioComp->Play();
		ActiveAudioComponents.Add(AudioID, AudioComp);
		UE_LOG(LogTemp, Log, TEXT("AudioManager: Playing audio %s"), *AudioID);
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("AudioManager: Failed to create audio component for %s"), *AudioID);
	}
}

void UAudioManager::OnAudioRequestFailed(const FString& AudioID, const FString& Error)
{
	UE_LOG(LogTemp, Error, TEXT("AudioManager: Audio request failed for %s: %s"), *AudioID, *Error);
}

UAudioComponent* UAudioManager::CreateAudioComponent(const FString& AudioID, EAudioCategory Category, float Volume)
{
	UAudioComponent* AudioComp = NewObject<UAudioComponent>(GetOwner());
	if (AudioComp)
	{
		AudioComp->bAutoActivate = false;
		float CategoryVol = CategoryVolumes.FindRef(Category);
		AudioComp->SetVolumeMultiplier(MasterVolume * CategoryVol * Volume);
		AudioComp->RegisterComponent();
	}

	return AudioComp;
}

// ============================================================
// VA-002: Ambient & Weather Audio Integration Implementation
// ============================================================

void UAudioManager::InitializeVA002Systems()
{
	UE_LOG(LogTemp, Log, TEXT("AudioManager: Initializing VA-002 systems"));

	// Initialize state tracking
	CurrentTimeOfDayState = TEXT("day");  // Default to day
	CurrentWeatherState = EWeatherState::CLEAR;
	CurrentWeatherIntensity = 0.0f;
	CurrentZoneProfile = TEXT("");
	CurrentReverbPreset = TEXT("");

	// Initialize crossfade parameters
	CurrentCategoryVolume = 1.0f;
	CurrentFadeSteps = 0;
	CurrentStepDuration = 0.0f;
	CrossfadeStepsCompleted = 0;
	PendingAmbientComponent = nullptr;
	CurrentDuckingState.Reset();

	// Initialize ducking amounts
	CurrentDuckAmounts.Add(EAudioCategory::Voice, 0.0f);  // Voice never ducked
	CurrentDuckAmounts.Add(EAudioCategory::Ambient, 0.0f);
	CurrentDuckAmounts.Add(EAudioCategory::Music, 0.0f);
	CurrentDuckAmounts.Add(EAudioCategory::Effect, 0.0f);
	CurrentDuckAmounts.Add(EAudioCategory::UI, 0.0f);

	// Bind to TimeOfDayManager events
	BindToTimeOfDayManager();

	// Start with default ambient profile
	SetTimeOfDayAmbient(CurrentTimeOfDayState);
}

void UAudioManager::BindToTimeOfDayManager()
{
	if (UWorld* World = GetWorld())
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			if (UTimeOfDayManager* TimeManager = GameInstance->GetSubsystem<UTimeOfDayManager>())
			{
				// Bind to time state changed event
				TimeManager->OnTimeStateChanged.AddDynamic(this, &UAudioManager::OnTimeStateChanged);
				
				// Get initial time state
				int32 Hour, Minute, Day;
				FString State;
				TimeManager->GetCurrentTime(Hour, Minute, Day, State);
				if (!State.IsEmpty())
				{
					CurrentTimeOfDayState = State;
					SetTimeOfDayAmbient(State);
				}

				UE_LOG(LogTemp, Log, TEXT("AudioManager: Bound to TimeOfDayManager events"));
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("AudioManager: TimeOfDayManager subsystem not found"));
			}
		}
	}
}

void UAudioManager::OnTimeStateChanged(FString OldState, FString NewState)
{
	UE_LOG(LogTemp, Log, TEXT("AudioManager: Time state changed from %s to %s"), *OldState, *NewState);
	SetTimeOfDayAmbient(NewState);
}

void UAudioManager::SetTimeOfDayAmbient(const FString& TimeState)
{
	if (TimeState == CurrentTimeOfDayState && TimeOfDayAmbientComponent && TimeOfDayAmbientComponent->IsPlaying())
	{
		UE_LOG(LogTemp, Verbose, TEXT("AudioManager: Time-of-day ambient already set to %s"), *TimeState);
		return;
	}

	FString OldState = CurrentTimeOfDayState;
	CurrentTimeOfDayState = TimeState;

	// Map time state to MetaSound template name
	FString MetaSoundName;
	if (TimeState == TEXT("dawn"))
	{
		MetaSoundName = TEXT("MS_DawnAmbient");
	}
	else if (TimeState == TEXT("day"))
	{
		MetaSoundName = TEXT("MS_DayAmbient");
	}
	else if (TimeState == TEXT("dusk"))
	{
		MetaSoundName = TEXT("MS_DuskAmbient");
	}
	else if (TimeState == TEXT("night"))
	{
		MetaSoundName = TEXT("MS_NightAmbient");
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioManager: Unknown time state %s, defaulting to day"), *TimeState);
		MetaSoundName = TEXT("MS_DayAmbient");
	}

	// Crossfade to new profile
	if (!OldState.IsEmpty() && OldState != TimeState)
	{
		CrossfadeAmbientProfile(OldState, TimeState, DEFAULT_AMBIENT_CROSSFADE_DURATION);
	}
	else
	{
		// First time setup - no crossfade needed
		USoundBase* MetaSound = LoadMetaSoundTemplate(MetaSoundName);
		if (MetaSound)
		{
			// Create or reuse ambient component
			if (!TimeOfDayAmbientComponent)
			{
				TimeOfDayAmbientComponent = NewObject<UAudioComponent>(GetOwner());
				if (TimeOfDayAmbientComponent)
				{
					TimeOfDayAmbientComponent->bAutoActivate = false;
					TimeOfDayAmbientComponent->bIsUISound = false;
					TimeOfDayAmbientComponent->RegisterComponent();
				}
			}

			if (TimeOfDayAmbientComponent)
			{
				TimeOfDayAmbientComponent->SetSound(MetaSound);
				float CategoryVol = CategoryVolumes.FindRef(EAudioCategory::Ambient);
				TimeOfDayAmbientComponent->SetVolumeMultiplier(MasterVolume * CategoryVol);
				TimeOfDayAmbientComponent->Play();
				UE_LOG(LogTemp, Log, TEXT("AudioManager: Playing time-of-day ambient %s"), *MetaSoundName);
			}
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("AudioManager: Failed to load MetaSound template %s"), *MetaSoundName);
		}
	}
}

void UAudioManager::CrossfadeAmbientProfile(const FString& OldProfile, const FString& NewProfile, float Duration)
{
	UE_LOG(LogTemp, Log, TEXT("AudioManager: Crossfading ambient from %s to %s over %f seconds"), *OldProfile, *NewProfile, Duration);

	// Map to MetaSound names
	FString OldMetaSoundName;
	FString NewMetaSoundName;
	
	if (OldProfile == TEXT("dawn")) OldMetaSoundName = TEXT("MS_DawnAmbient");
	else if (OldProfile == TEXT("day")) OldMetaSoundName = TEXT("MS_DayAmbient");
	else if (OldProfile == TEXT("dusk")) OldMetaSoundName = TEXT("MS_DuskAmbient");
	else if (OldProfile == TEXT("night")) OldMetaSoundName = TEXT("MS_NightAmbient");

	if (NewProfile == TEXT("dawn")) NewMetaSoundName = TEXT("MS_DawnAmbient");
	else if (NewProfile == TEXT("day")) NewMetaSoundName = TEXT("MS_DayAmbient");
	else if (NewProfile == TEXT("dusk")) NewMetaSoundName = TEXT("MS_DuskAmbient");
	else if (NewProfile == TEXT("night")) NewMetaSoundName = TEXT("MS_NightAmbient");

	USoundBase* NewMetaSound = LoadMetaSoundTemplate(NewMetaSoundName);
	if (!NewMetaSound)
	{
		UE_LOG(LogTemp, Error, TEXT("AudioManager: Failed to load MetaSound template %s"), *NewMetaSoundName);
		return;
	}

	// Fade out old, fade in new
	if (TimeOfDayAmbientComponent && TimeOfDayAmbientComponent->IsPlaying())
	{
		// Create new component for crossfade
		UAudioComponent* NewAmbientComponent = NewObject<UAudioComponent>(GetOwner());
		if (NewAmbientComponent)
		{
			NewAmbientComponent->bAutoActivate = false;
			NewAmbientComponent->bIsUISound = false;
			NewAmbientComponent->RegisterComponent();
			NewAmbientComponent->SetSound(NewMetaSound);
			float CategoryVol = CategoryVolumes.FindRef(EAudioCategory::Ambient);
			NewAmbientComponent->SetVolumeMultiplier(0.0f);  // Start silent
			NewAmbientComponent->Play();

			// Fade out old component
			if (UWorld* World = GetWorld())
			{
				// Clear any existing crossfade timer
				if (World->GetTimerManager().IsValidTimer(AmbientCrossfadeTimerHandle))
				{
					World->GetTimerManager().ClearTimer(AmbientCrossfadeTimerHandle);
				}

				// Validate component before storing
				if (!IsValid(NewAmbientComponent))
				{
					UE_LOG(LogTemp, Warning, TEXT("AudioManager: Invalid component passed to CrossfadeAmbientProfile"));
					return;
				}

				// Store ALL state as member variables for lambda safety (no local variable captures)
				PendingAmbientComponent = NewAmbientComponent;
				CurrentCategoryVolume = CategoryVol;
				CurrentFadeSteps = 30;  // 30 steps over duration
				CurrentStepDuration = Duration / CurrentFadeSteps;
				CrossfadeStepsCompleted = 0;  // Reset member variable

				FTimerDelegate FadeDelegate;
				FadeDelegate.BindLambda([this]()  // ONLY capture 'this' - use member variables only
				{
					// Validate world and component each time
					UWorld* LambdaWorld = GetWorld();
					if (!LambdaWorld || !IsValid(PendingAmbientComponent))
					{
						if (LambdaWorld)
						{
							LambdaWorld->GetTimerManager().ClearTimer(AmbientCrossfadeTimerHandle);
						}
						return;
					}

					CrossfadeStepsCompleted++;  // Increment member variable (safe)
					float Progress = (float)CrossfadeStepsCompleted / (float)CurrentFadeSteps;
					
					// Fade out old
					if (TimeOfDayAmbientComponent && IsValid(TimeOfDayAmbientComponent))
					{
						float OldVolume = MasterVolume * CurrentCategoryVolume * (1.0f - Progress);
						TimeOfDayAmbientComponent->SetVolumeMultiplier(OldVolume);
					}

					// Fade in new
					if (PendingAmbientComponent && IsValid(PendingAmbientComponent))
					{
						float NewVolume = MasterVolume * CurrentCategoryVolume * Progress;
						PendingAmbientComponent->SetVolumeMultiplier(NewVolume);
					}

					if (Progress >= 1.0f)
					{
						// Complete - stop old, keep new
						if (TimeOfDayAmbientComponent && IsValid(TimeOfDayAmbientComponent))
						{
							TimeOfDayAmbientComponent->Stop();
							TimeOfDayAmbientComponent->DestroyComponent();
						}
						TimeOfDayAmbientComponent = PendingAmbientComponent;
						PendingAmbientComponent = nullptr;  // Clear reference
						
						// Clear timer using validated world pointer
						LambdaWorld->GetTimerManager().ClearTimer(AmbientCrossfadeTimerHandle);
					}
				});

				World->GetTimerManager().SetTimer(AmbientCrossfadeTimerHandle, FadeDelegate, CurrentStepDuration, true);
			}
		}
	}
	else
	{
		// No old component - just start new
		SetTimeOfDayAmbient(NewProfile);
	}
}

void UAudioManager::SetWeatherAudioLayer(EWeatherState WeatherState, float Intensity)
{
	CurrentWeatherState = WeatherState;
	CurrentWeatherIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);

	UpdateWeatherLayers(WeatherState, CurrentWeatherIntensity);

	// Apply ducking based on weather intensity
	// Weather events duck ambient by weather.intensity * 0.6
	float AmbientDuckAmount = CurrentWeatherIntensity * 0.6f;
	ApplyDucking(EAudioCategory::Ambient, AmbientDuckAmount, 2.0f);

	// Music ducks by 20% on weather start
	if (WeatherState != EWeatherState::CLEAR && CurrentWeatherIntensity > 0.3f)
	{
		ApplyDucking(EAudioCategory::Music, 0.2f, 2.0f);
	}
}

void UAudioManager::UpdateWeatherLayers(EWeatherState WeatherState, float Intensity)
{
	FString Layer1Name, Layer2Name;
	GetWeatherAudioLayers(WeatherState, Layer1Name, Layer2Name);

	// Stop all weather layers first
	for (auto& Pair : WeatherLayerComponents)
	{
		if (Pair.Value && Pair.Value->IsPlaying())
		{
			Pair.Value->Stop();
		}
	}

	// Load and play Layer 1 if defined
	if (!Layer1Name.IsEmpty())
	{
		USoundBase* Layer1Sound = LoadMetaSoundTemplate(Layer1Name);
		if (Layer1Sound)
		{
			UAudioComponent** ExistingLayer = WeatherLayerComponents.Find(WeatherState);
			UAudioComponent* LayerComponent = ExistingLayer ? *ExistingLayer : nullptr;
			
			if (!LayerComponent)
			{
				LayerComponent = NewObject<UAudioComponent>(GetOwner());
				if (LayerComponent)
				{
					LayerComponent->bAutoActivate = false;
					LayerComponent->bIsUISound = false;
					LayerComponent->RegisterComponent();
					WeatherLayerComponents.Add(WeatherState, LayerComponent);
				}
			}

			if (LayerComponent)
			{
				LayerComponent->SetSound(Layer1Sound);
				LayerComponent->SetVolumeMultiplier(MasterVolume * Intensity);
				LayerComponent->Play();
				UE_LOG(LogTemp, Log, TEXT("AudioManager: Playing weather layer %s at intensity %f"), *Layer1Name, Intensity);
			}
		}
	}

	// Load and play Layer 2 if defined (for weather states with secondary layers)
	if (!Layer2Name.IsEmpty() && Intensity > 0.5f)  // Layer 2 only for significant intensity
	{
		USoundBase* Layer2Sound = LoadMetaSoundTemplate(Layer2Name);
		if (Layer2Sound)
		{
			// Create separate component for layer 2
			UAudioComponent* Layer2Component = NewObject<UAudioComponent>(GetOwner());
			if (Layer2Component)
			{
				Layer2Component->bAutoActivate = false;
				Layer2Component->bIsUISound = false;
				Layer2Component->RegisterComponent();
				Layer2Component->SetSound(Layer2Sound);
				Layer2Component->SetVolumeMultiplier(MasterVolume * Intensity * 0.7f);  // Layer 2 is quieter
				Layer2Component->Play();
				UE_LOG(LogTemp, Log, TEXT("AudioManager: Playing weather layer 2 %s"), *Layer2Name);
			}
		}
	}

	// Special handling for thunder (STORM, BLIZZARD)
	if (WeatherState == EWeatherState::STORM || WeatherState == EWeatherState::BLIZZARD)
	{
		// Thunder is event-based, not looping - handled by PlayThunderStrike()
		// This method just sets up the weather layers (rain, wind)
	}
}

void UAudioManager::GetWeatherAudioLayers(EWeatherState WeatherState, FString& OutLayer1, FString& OutLayer2)
{
	OutLayer1 = TEXT("");
	OutLayer2 = TEXT("");

	switch (WeatherState)
	{
	case EWeatherState::CLEAR:
		// No layers
		break;
	case EWeatherState::PARTLY_CLOUDY:
		OutLayer1 = TEXT("MS_Weather_Wind_Light");
		break;
	case EWeatherState::CLOUDY:
		OutLayer1 = TEXT("MS_Weather_Wind_Moderate");
		break;
	case EWeatherState::RAIN:
		OutLayer1 = TEXT("MS_Weather_Rain");
		OutLayer2 = TEXT("MS_Weather_Wind_Moderate");
		break;
	case EWeatherState::HEAVY_RAIN:
		OutLayer1 = TEXT("MS_Weather_Rain_Heavy");
		OutLayer2 = TEXT("MS_Weather_Wind_Strong");
		break;
	case EWeatherState::STORM:
		OutLayer1 = TEXT("MS_Weather_Rain_Heavy");
		OutLayer2 = TEXT("MS_Weather_Wind_Strong");
		// Thunder handled separately via PlayThunderStrike()
		break;
	case EWeatherState::FOG:
		OutLayer1 = TEXT("MS_Weather_Fog_Ambient");
		break;
	case EWeatherState::MIST:
		OutLayer1 = TEXT("MS_Weather_Mist_Ambient");
		break;
	case EWeatherState::SNOW:
		OutLayer1 = TEXT("MS_Weather_Snow");
		OutLayer2 = TEXT("MS_Weather_Wind_Moderate");
		break;
	case EWeatherState::HEAVY_SNOW:
		OutLayer1 = TEXT("MS_Weather_Snow_Heavy");
		OutLayer2 = TEXT("MS_Weather_Wind_Strong");
		break;
	case EWeatherState::BLIZZARD:
		OutLayer1 = TEXT("MS_Weather_Blizzard");
		OutLayer2 = TEXT("MS_Weather_Wind_Howling");
		// Thunder handled separately
		break;
	case EWeatherState::WINDY:
		OutLayer1 = TEXT("MS_Weather_Wind_Strong");
		break;
	case EWeatherState::EXTREME_HEAT:
		OutLayer1 = TEXT("MS_Weather_Heat_Haze");
		break;
	case EWeatherState::EXTREME_COLD:
		OutLayer1 = TEXT("MS_Weather_Cold_Wind");
		break;
	default:
		break;
	}
}

void UAudioManager::SetZoneAmbientProfile(const FString& ZoneProfileName)
{
	if (ZoneProfileName == CurrentZoneProfile && ZoneAmbientComponent && ZoneAmbientComponent->IsPlaying())
	{
		return;  // Already set
	}

	FString OldProfile = CurrentZoneProfile;
	CurrentZoneProfile = ZoneProfileName;

	// Zone profiles are MetaSound templates
	FString MetaSoundName = FString::Printf(TEXT("MS_Zone_%s"), *ZoneProfileName);
	USoundBase* ZoneMetaSound = LoadMetaSoundTemplate(MetaSoundName);

	if (ZoneMetaSound)
	{
		if (!ZoneAmbientComponent)
		{
			ZoneAmbientComponent = NewObject<UAudioComponent>(GetOwner());
			if (ZoneAmbientComponent)
			{
				ZoneAmbientComponent->bAutoActivate = false;
				ZoneAmbientComponent->bIsUISound = false;
				ZoneAmbientComponent->RegisterComponent();
			}
		}

		if (ZoneAmbientComponent)
		{
			// Crossfade if transitioning
			if (!OldProfile.IsEmpty() && OldProfile != ZoneProfileName)
			{
				// Simple crossfade (similar to time-of-day)
				ZoneAmbientComponent->FadeOut(DEFAULT_ZONE_TRANSITION_DURATION, 0.0f);
				
				if (UWorld* World = GetWorld())
				{
					FTimerHandle FadeInTimer;
					FTimerDelegate FadeInDelegate;
					FadeInDelegate.BindLambda([this, ZoneMetaSound]()
					{
						if (ZoneAmbientComponent)
						{
							ZoneAmbientComponent->SetSound(ZoneMetaSound);
							float CategoryVol = CategoryVolumes.FindRef(EAudioCategory::Ambient);
							ZoneAmbientComponent->SetVolumeMultiplier(MasterVolume * CategoryVol);
							ZoneAmbientComponent->FadeIn(DEFAULT_ZONE_TRANSITION_DURATION);
						}
					});
					World->GetTimerManager().SetTimer(FadeInTimer, FadeInDelegate, DEFAULT_ZONE_TRANSITION_DURATION, false);
				}
			}
			else
			{
				// First time setup
				ZoneAmbientComponent->SetSound(ZoneMetaSound);
				float CategoryVol = CategoryVolumes.FindRef(EAudioCategory::Ambient);
				ZoneAmbientComponent->SetVolumeMultiplier(MasterVolume * CategoryVol);
				ZoneAmbientComponent->Play();
			}

			UE_LOG(LogTemp, Log, TEXT("AudioManager: Set zone ambient profile to %s"), *ZoneProfileName);
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioManager: Zone ambient profile %s not found"), *MetaSoundName);
	}
}

void UAudioManager::DuckAudioByAmount(EAudioCategory Category, float DuckAmount, float Duration)
{
	DuckAmount = FMath::Clamp(DuckAmount, 0.0f, 1.0f);
	CurrentDuckAmounts.Add(Category, DuckAmount);
	ApplyDucking(Category, DuckAmount, Duration);
}

void UAudioManager::ApplyDucking(EAudioCategory Category, float TargetDuckAmount, float Duration)
{
	// Apply ducking by reducing volume multiplier for audio components in this category
	// This is a simplified implementation - in production, use submix sends or per-component ducking

	TargetDuckAmount = FMath::Clamp(TargetDuckAmount, 0.0f, 1.0f);
	float StartDuckAmount = CurrentDuckAmounts.FindRef(Category);

	// Use timer to smoothly interpolate ducking
	if (UWorld* World = GetWorld())
	{
		FTimerHandle* DuckTimer = DuckingTimerHandles.Find(Category);
		if (DuckTimer && World->GetTimerManager().IsValidTimer(*DuckTimer))
		{
			World->GetTimerManager().ClearTimer(*DuckTimer);
		}

		float StepDuration = 0.1f;  // Update every 100ms
		int32 Steps = FMath::Max(1, (int32)(Duration / StepDuration));
		
		// Store ducking state as member variable (not local - for lambda safety)
		CurrentDuckingState = MakeShareable(new FDuckingState());
		CurrentDuckingState->StartDuck = StartDuckAmount;
		CurrentDuckingState->TargetDuck = TargetDuckAmount;
		CurrentDuckingState->TotalSteps = Steps;
		CurrentDuckingState->StepCount = 0;

		FTimerDelegate DuckDelegate;
		DuckDelegate.BindLambda([this, Category]()  // Only capture 'this' and Category (enum is safe)
		{
			// Validate ducking state exists
			if (!CurrentDuckingState.IsValid())
			{
				// Clear timer and exit
				if (UWorld* World = GetWorld())
				{
					FTimerHandle* TimerHandle = DuckingTimerHandles.Find(Category);
					if (TimerHandle)
					{
						World->GetTimerManager().ClearTimer(*TimerHandle);
					}
				}
				return;
			}

			CurrentDuckingState->StepCount++;  // Increment member shared state (safe)
			float Progress = (float)CurrentDuckingState->StepCount / (float)CurrentDuckingState->TotalSteps;
			float CurrentDuck = FMath::Lerp(CurrentDuckingState->StartDuck, CurrentDuckingState->TargetDuck, Progress);
			CurrentDuckAmounts.Add(Category, CurrentDuck);

			// Apply to all audio components in this category
			// Note: In production, store category with each component for efficient lookup
			// For now, this affects ambient category ducking (weather system primarily uses this)

			if (Category == EAudioCategory::Ambient)
			{
				// Apply ducking to time-of-day and zone ambient
				float BaseVolume = MasterVolume * CategoryVolumes.FindRef(Category) * (1.0f - CurrentDuck);
				
				if (TimeOfDayAmbientComponent && TimeOfDayAmbientComponent->IsPlaying())
				{
					TimeOfDayAmbientComponent->SetVolumeMultiplier(BaseVolume);
				}
				if (ZoneAmbientComponent && ZoneAmbientComponent->IsPlaying())
				{
					ZoneAmbientComponent->SetVolumeMultiplier(BaseVolume);
				}
			}
			else if (Category == EAudioCategory::Music)
			{
				// Apply ducking to music components
				float BaseVolume = MasterVolume * CategoryVolumes.FindRef(Category) * (1.0f - CurrentDuck);
				// In production, track music components separately
			}

			if (Progress >= 1.0f)
			{
				// Complete - clear timer and state
				FTimerHandle* TimerHandle = DuckingTimerHandles.Find(Category);
				if (TimerHandle)
				{
					if (UWorld* World = GetWorld())
					{
						World->GetTimerManager().ClearTimer(*TimerHandle);
					}
				}
				CurrentDuckingState.Reset();  // Clear shared pointer
			}
		});

		FTimerHandle NewTimer;
		World->GetTimerManager().SetTimer(NewTimer, DuckDelegate, StepDuration, true);
		DuckingTimerHandles.Add(Category, NewTimer);
	}
}

void UAudioManager::UpdateAmbientProfile(const FString& TimeState, const FString& ZoneProfileName)
{
	// Update both time-of-day and zone ambient
	SetTimeOfDayAmbient(TimeState);
	if (!ZoneProfileName.IsEmpty())
	{
		SetZoneAmbientProfile(ZoneProfileName);
	}
}

void UAudioManager::TriggerWeatherTransition(EWeatherState OldState, EWeatherState NewState, float Intensity, float TransitionDuration)
{
	UE_LOG(LogTemp, Log, TEXT("AudioManager: Weather transition from %d to %d at intensity %f"), (int32)OldState, (int32)NewState, Intensity);

	// Fade out old weather layers
	for (auto& Pair : WeatherLayerComponents)
	{
		if (Pair.Key == OldState && Pair.Value && Pair.Value->IsPlaying())
		{
			Pair.Value->FadeOut(TransitionDuration, 0.0f);
		}
	}

	// Set new weather state (which will fade in new layers)
	SetWeatherAudioLayer(NewState, Intensity);
}

void UAudioManager::PlayThunderStrike(float Volume)
{
	// Thunder is event-based audio (not looping)
	FString ThunderSoundName = TEXT("MS_Weather_Thunder");
	USoundBase* ThunderSound = LoadMetaSoundTemplate(ThunderSoundName);

	if (ThunderSound)
	{
		// Create temporary audio component for one-shot thunder
		UAudioComponent* ThunderComponent = NewObject<UAudioComponent>(GetOwner());
		if (ThunderComponent)
		{
			ThunderComponent->bAutoActivate = false;
			ThunderComponent->bIsUISound = false;
			ThunderComponent->RegisterComponent();
			ThunderComponent->SetSound(ThunderSound);
			Volume = FMath::Clamp(Volume, 0.0f, 1.0f);
			float RandomizedVolume = FMath::RandRange(Volume * 0.7f, Volume);  // Randomize volume (0.7-1.0x)
			ThunderComponent->SetVolumeMultiplier(MasterVolume * RandomizedVolume);
			
			// Apply low-pass filter for distant thunder (via attenuation settings)
			// In production, use USoundAttenuation with low-pass filter settings

			ThunderComponent->Play();
			
			// Clean up component after playing
			if (UWorld* World = GetWorld())
			{
				FTimerHandle CleanupTimer;
				FTimerDelegate CleanupDelegate;
				CleanupDelegate.BindLambda([ThunderComponent]()
				{
					if (ThunderComponent && !ThunderComponent->IsPlaying())
					{
						ThunderComponent->DestroyComponent();
					}
				});
				World->GetTimerManager().SetTimer(CleanupTimer, CleanupDelegate, 5.0f, false);
			}

			UE_LOG(LogTemp, Log, TEXT("AudioManager: Playing thunder strike at volume %f"), RandomizedVolume);
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("AudioManager: Thunder sound not found: %s"), *ThunderSoundName);
	}
}

float UAudioManager::CalculateAudioOcclusion(const FVector& SourceLocation, const FVector& ListenerLocation) const
{
	// Raycast-based occlusion calculation
	FVector Direction = ListenerLocation - SourceLocation;
	float Distance = Direction.Size();

	if (Distance > MAX_OCCLUSION_DISTANCE)
	{
		return 1.0f;  // Fully occluded if too far
	}

	if (UWorld* World = GetWorld())
	{
		FHitResult HitResult;
		FCollisionQueryParams QueryParams;
		QueryParams.AddIgnoredActor(GetOwner());  // Ignore owner actor

		// Line trace from source to listener
		bool bHit = World->LineTraceSingleByChannel(
			HitResult,
			SourceLocation,
			ListenerLocation,
			ECC_WorldStatic,
			QueryParams
		);

		if (bHit)
		{
			// Each wall hit increases occlusion by 0.15, max 1.0
			// In production, perform multiple traces or use complex occlusion tracing
			return FMath::Min(1.0f, 0.15f);
		}
	}

	return 0.0f;  // No occlusion
}

void UAudioManager::SetReverbPreset(const FString& PresetName, float TransitionDuration)
{
	if (PresetName == CurrentReverbPreset)
	{
		return;  // Already set
	}

	CurrentReverbPreset = PresetName;
	
	// In production, load reverb preset asset and apply to ambient submix
	// This is a placeholder - actual reverb preset loading would use:
	// USoundEffectSubmixPreset* ReverbPreset = LoadObject<USoundEffectSubmixPreset>(nullptr, *PresetPath);
	// Apply to ambient submix send level

	UE_LOG(LogTemp, Log, TEXT("AudioManager: Set reverb preset to %s"), *PresetName);
	
	// Reverb transition is handled via submix send level interpolation
	// Placeholder for future implementation
	UpdateReverbSendLevel(0.5f, TransitionDuration);  // Example: 50% wet level
}

void UAudioManager::UpdateReverbSendLevel(float TargetLevel, float Duration)
{
	// Placeholder for reverb send level interpolation
	// In production, interpolate submix send level for ambient category
	UE_LOG(LogTemp, Verbose, TEXT("AudioManager: Updating reverb send level to %f over %f seconds"), TargetLevel, Duration);
}

USoundBase* UAudioManager::LoadMetaSoundTemplate(const FString& TemplateName)
{
	// Check cache first
	if (USoundBase** CachedSound = MetaSoundTemplateCache.Find(TemplateName))
	{
		if (*CachedSound)
		{
			return *CachedSound;
		}
	}

	// Load MetaSound asset
	// In production, use proper asset path: /Game/Audio/MetaSounds/[TemplateName]
	FString AssetPath = FString::Printf(TEXT("/Game/Audio/MetaSounds/%s.%s"), *TemplateName, *TemplateName);
	
	USoundBase* SoundAsset = LoadObject<USoundBase>(nullptr, *AssetPath);
	if (SoundAsset)
	{
		MetaSoundTemplateCache.Add(TemplateName, SoundAsset);
		return SoundAsset;
	}

	UE_LOG(LogTemp, Warning, TEXT("AudioManager: MetaSound template not found: %s (path: %s)"), *TemplateName, *AssetPath);
	return nullptr;
}

FString UAudioManager::GetCurrentTimeOfDayAmbient() const
{
	return CurrentTimeOfDayState;
}

EWeatherState UAudioManager::GetCurrentWeatherState() const
{
	return CurrentWeatherState;
}

FString UAudioManager::GetCurrentZoneAmbientProfile() const
{
	return CurrentZoneProfile;
}

