// Copyright Epic Games, Inc. All Rights Reserved.

#include "WeatherManager.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "TimerManager.h"
#include "Kismet/GameplayStatics.h"
#include "TimeOfDayManager.h"
#include "AudioManager.h"
#include "GameEventBus.h"
#include "WeatherPresetLibrary.h"

void UWeatherManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	UE_LOG(LogTemp, Log, TEXT("WeatherManager: Initializing"));

	// Initialize state
	CurrentWeatherState = EWeatherState::CLEAR;
	PreviousWeatherState = EWeatherState::CLEAR;
	CurrentIntensity = 0.0f;
	TransitionProgress = 0.0f;
	CurrentTransitionDuration = 0.0f;
	TransitionMode = EWeatherTransitionMode::SmoothStep;

	// Initialize parameters to clear weather
	CurrentParameters = GetParametersForState(EWeatherState::CLEAR, 0.0f);
	TargetParameters = CurrentParameters;

	// Load Material Parameter Collection
	LoadWeatherMPC();

	// Create MPC instance if MPC is valid
	if (WeatherMPC)
	{
		if (UWorld* World = GetWorld())
		{
			WeatherMPCInstance = World->GetParameterCollectionInstance(WeatherMPC);
			if (WeatherMPCInstance)
			{
				UE_LOG(LogTemp, Log, TEXT("WeatherManager: MPC instance created"));
				UpdateMaterialParameters();
			}
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherManager: WeatherMPC not found - material parameters will not update"));
	}

	// Get TimeOfDayManager reference for event binding
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		TWeakObjectPtr<UTimeOfDayManager> TimeOfDayManagerRef = GameInstance->GetSubsystem<UTimeOfDayManager>();
		if (TimeOfDayManagerRef.IsValid())
		{
			UE_LOG(LogTemp, Log, TEXT("WeatherManager: TimeOfDayManager reference acquired"));
			// TimeOfDayManager integration will be handled via event bus
		}
	}

	// Get AudioManager reference (component on player pawn)
	// AudioManager integration will be handled via event bus or direct reference lookup when needed
	UE_LOG(LogTemp, Log, TEXT("WeatherManager: AudioManager will be accessed via event bus"));
}

void UWeatherManager::Deinitialize()
{
	// Stop transition timer
	if (UWorld* World = GetWorld())
	{
		if (FTimerManager* TimerManager = &World->GetTimerManager())
		{
			if (TransitionTimerHandle.IsValid())
			{
				TimerManager->ClearTimer(TransitionTimerHandle);
			}
		}
	}

	Super::Deinitialize();
}

UWeatherManager* UWeatherManager::Get(const UObject* WorldContext)
{
	if (!WorldContext)
	{
		return nullptr;
	}

	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UWeatherManager>();
		}
	}

	return nullptr;
}

void UWeatherManager::SetWeatherState(EWeatherState NewState, float TransitionDuration)
{
	if (NewState == CurrentWeatherState)
	{
		return; // No change needed
	}

	PreviousWeatherState = CurrentWeatherState;
	CurrentWeatherState = NewState;
	CurrentTransitionDuration = FMath::Max(0.1f, TransitionDuration);
	TransitionProgress = 0.0f;

	// Calculate target parameters
	TargetParameters = GetParametersForState(NewState, CurrentIntensity);

	// Broadcast state change event
	OnWeatherStateChanged.Broadcast(PreviousWeatherState, CurrentWeatherState);

	// Publish to GameEventBus
	if (UGameEventBus* EventBus = UGameEventBus::Get(GetWorld()))
	{
		FGameEventData EventData;
		EventData.EventType = EGameEventType::WeatherChanged;
		EventData.SourceSystem = TEXT("WeatherManager");
		EventData.Timestamp = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
		EventData.EventData = FString::Printf(TEXT("{\"OldState\":%d,\"NewState\":%d}"), (int32)PreviousWeatherState, (int32)CurrentWeatherState);
		EventBus->PublishEvent(EventData);
	}

	// Start transition timer
	if (UWorld* World = GetWorld())
	{
		FTimerManager& TimerManager = World->GetTimerManager();
		if (TransitionTimerHandle.IsValid())
		{
			TimerManager.ClearTimer(TransitionTimerHandle);
		}

		FTimerDelegate TimerDelegate;
		TimerDelegate.BindUObject(this, &UWeatherManager::UpdateTransition, TRANSITION_UPDATE_INTERVAL);
		TimerManager.SetTimer(TransitionTimerHandle, TimerDelegate, TRANSITION_UPDATE_INTERVAL, true);
	}

	UE_LOG(LogTemp, Log, TEXT("WeatherManager: Weather state changed from %d to %d"), (int32)PreviousWeatherState, (int32)CurrentWeatherState);
}

void UWeatherManager::SetWeatherStateImmediate(EWeatherState NewState)
{
	PreviousWeatherState = CurrentWeatherState;
	CurrentWeatherState = NewState;
	TransitionProgress = 1.0f;

	// Set parameters immediately
	CurrentParameters = GetParametersForState(NewState, CurrentIntensity);
	TargetParameters = CurrentParameters;

	// Stop transition timer
	if (UWorld* World = GetWorld())
	{
		if (FTimerManager* TimerManager = &World->GetTimerManager())
		{
			if (TransitionTimerHandle.IsValid())
			{
				TimerManager->ClearTimer(TransitionTimerHandle);
			}
		}
	}

	// Update materials immediately
	UpdateMaterialParameters();

	// Broadcast events
	OnWeatherStateChanged.Broadcast(PreviousWeatherState, CurrentWeatherState);
	OnWeatherParametersChanged.Broadcast(CurrentParameters);

	UE_LOG(LogTemp, Log, TEXT("WeatherManager: Weather state set immediately to %d"), (int32)NewState);
}

void UWeatherManager::SetWeatherIntensity(float Intensity)
{
	CurrentIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);

	// Recalculate parameters with new intensity
	TargetParameters = GetParametersForState(CurrentWeatherState, CurrentIntensity);

	// Update immediately if not transitioning
	if (TransitionProgress >= 1.0f)
	{
		CurrentParameters = TargetParameters;
		UpdateMaterialParameters();
		OnWeatherParametersChanged.Broadcast(CurrentParameters);
	}
}

void UWeatherManager::UpdateMaterialParameters()
{
	if (!WeatherMPCInstance)
	{
		return;
	}

	// Update Material Parameter Collection with current weather parameters
	WeatherMPCInstance->SetScalarParameterValue(TEXT("RainIntensity"), CurrentParameters.RainIntensity);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("SnowIntensity"), CurrentParameters.SnowIntensity);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("FogDensity"), CurrentParameters.FogDensity);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("WindStrength"), CurrentParameters.WindStrength);
	WeatherMPCInstance->SetVectorParameterValue(TEXT("WindDirection"), 
		FLinearColor(CurrentParameters.WindDirection, 0.0f, 0.0f, 0.0f));
	WeatherMPCInstance->SetScalarParameterValue(TEXT("Temperature"), CurrentParameters.Temperature);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("Humidity"), CurrentParameters.Humidity);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("CloudCoverage"), CurrentParameters.CloudCoverage);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("LightningIntensity"), CurrentParameters.LightningIntensity);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("Wetness"), CurrentParameters.Wetness);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("SnowAccumulation"), CurrentParameters.SnowAccumulation);
}

FWeatherParameters UWeatherManager::GetParametersForState(EWeatherState State, float Intensity) const
{
	FWeatherParameters Params;

	switch (State)
	{
	case EWeatherState::CLEAR:
		Params.RainIntensity = 0.0f;
		Params.SnowIntensity = 0.0f;
		Params.FogDensity = 0.0f;
		Params.WindStrength = 0.1f * Intensity;
		Params.Temperature = 20.0f + (Intensity * 5.0f);
		Params.Humidity = 0.3f + (Intensity * 0.2f);
		Params.CloudCoverage = 0.0f;
		Params.LightningIntensity = 0.0f;
		Params.Wetness = 0.0f;
		Params.SnowAccumulation = 0.0f;
		break;

	case EWeatherState::RAIN:
		Params.RainIntensity = 0.3f + (Intensity * 0.4f);
		Params.SnowIntensity = 0.0f;
		Params.FogDensity = 0.1f * Intensity;
		Params.WindStrength = 0.3f + (Intensity * 0.3f);
		Params.Temperature = 15.0f - (Intensity * 5.0f);
		Params.Humidity = 0.7f + (Intensity * 0.2f);
		Params.CloudCoverage = 0.6f + (Intensity * 0.3f);
		Params.LightningIntensity = 0.0f;
		Params.Wetness = 0.5f + (Intensity * 0.4f);
		Params.SnowAccumulation = 0.0f;
		break;

	case EWeatherState::STORM:
		Params.RainIntensity = 0.8f + (Intensity * 0.2f);
		Params.SnowIntensity = 0.0f;
		Params.FogDensity = 0.2f * Intensity;
		Params.WindStrength = 0.7f + (Intensity * 0.3f);
		Params.Temperature = 12.0f - (Intensity * 5.0f);
		Params.Humidity = 0.9f + (Intensity * 0.1f);
		Params.CloudCoverage = 1.0f;
		Params.LightningIntensity = 0.5f + (Intensity * 0.5f);
		Params.Wetness = 0.9f + (Intensity * 0.1f);
		Params.SnowAccumulation = 0.0f;
		break;

	case EWeatherState::SNOW:
		Params.RainIntensity = 0.0f;
		Params.SnowIntensity = 0.3f + (Intensity * 0.4f);
		Params.FogDensity = 0.1f * Intensity;
		Params.WindStrength = 0.2f + (Intensity * 0.3f);
		Params.Temperature = -5.0f - (Intensity * 10.0f);
		Params.Humidity = 0.6f + (Intensity * 0.2f);
		Params.CloudCoverage = 0.7f + (Intensity * 0.3f);
		Params.LightningIntensity = 0.0f;
		Params.Wetness = 0.0f;
		Params.SnowAccumulation = 0.3f + (Intensity * 0.5f);
		break;

	case EWeatherState::FOG:
		Params.RainIntensity = 0.0f;
		Params.SnowIntensity = 0.0f;
		Params.FogDensity = 0.4f + (Intensity * 0.5f);
		Params.WindStrength = 0.1f;
		Params.Temperature = 10.0f;
		Params.Humidity = 0.9f;
		Params.CloudCoverage = 0.3f;
		Params.LightningIntensity = 0.0f;
		Params.Wetness = 0.2f * Intensity;
		Params.SnowAccumulation = 0.0f;
		break;

	default:
		// Default to clear weather
		Params = GetParametersForState(EWeatherState::CLEAR, Intensity);
		break;
	}

	return Params;
}

FWeatherParameters UWeatherManager::InterpolateParameters(const FWeatherParameters& From, const FWeatherParameters& To, float Alpha) const
{
	FWeatherParameters Result;
	float CurveAlpha = ApplyInterpolationCurve(Alpha);

	Result.RainIntensity = FMath::Lerp(From.RainIntensity, To.RainIntensity, CurveAlpha);
	Result.SnowIntensity = FMath::Lerp(From.SnowIntensity, To.SnowIntensity, CurveAlpha);
	Result.FogDensity = FMath::Lerp(From.FogDensity, To.FogDensity, CurveAlpha);
	Result.WindStrength = FMath::Lerp(From.WindStrength, To.WindStrength, CurveAlpha);
	Result.WindDirection = FMath::Lerp(From.WindDirection, To.WindDirection, CurveAlpha);
	Result.Temperature = FMath::Lerp(From.Temperature, To.Temperature, CurveAlpha);
	Result.Humidity = FMath::Lerp(From.Humidity, To.Humidity, CurveAlpha);
	Result.CloudCoverage = FMath::Lerp(From.CloudCoverage, To.CloudCoverage, CurveAlpha);
	Result.LightningIntensity = FMath::Lerp(From.LightningIntensity, To.LightningIntensity, CurveAlpha);
	Result.Wetness = FMath::Lerp(From.Wetness, To.Wetness, CurveAlpha);
	Result.SnowAccumulation = FMath::Lerp(From.SnowAccumulation, To.SnowAccumulation, CurveAlpha);

	return Result;
}

void UWeatherManager::UpdateTransition(float DeltaTime)
{
	if (!GetWorld())
	{
		return;
	}

	if (TransitionProgress >= 1.0f)
	{
		CompleteTransition();
		return;
	}

	TransitionProgress += TRANSITION_UPDATE_INTERVAL / CurrentTransitionDuration;
	TransitionProgress = FMath::Clamp(TransitionProgress, 0.0f, 1.0f);

	// Interpolate parameters
	CurrentParameters = InterpolateParameters(
		GetParametersForState(PreviousWeatherState, CurrentIntensity),
		TargetParameters,
		TransitionProgress
	);

	// Update material parameters
	UpdateMaterialParameters();

	// Broadcast parameter changes
	OnWeatherParametersChanged.Broadcast(CurrentParameters);

	// Check if transition is complete
	if (TransitionProgress >= 1.0f)
	{
		CompleteTransition();
	}
}

void UWeatherManager::CompleteTransition()
{
	// Stop transition timer
	if (UWorld* World = GetWorld())
	{
		if (FTimerManager* TimerManager = &World->GetTimerManager())
		{
			if (TransitionTimerHandle.IsValid())
			{
				TimerManager->ClearTimer(TransitionTimerHandle);
			}
		}
	}

	// Ensure final parameters are set
	CurrentParameters = TargetParameters;
	UpdateMaterialParameters();

	// Trigger lightning strikes for storms/blizzards
	if (CurrentWeatherState == EWeatherState::STORM || CurrentWeatherState == EWeatherState::BLIZZARD)
	{
		if (CurrentParameters.LightningIntensity > 0.3f)
		{
			TriggerLightningStrike();
		}
	}

	UE_LOG(LogTemp, Log, TEXT("WeatherManager: Transition complete to state %d"), (int32)CurrentWeatherState);
}

float UWeatherManager::ApplyInterpolationCurve(float Alpha) const
{
	switch (TransitionMode)
	{
	case EWeatherTransitionMode::Linear:
		return Alpha;

	case EWeatherTransitionMode::EaseIn:
		return Alpha * Alpha;

	case EWeatherTransitionMode::EaseOut:
		return 1.0f - FMath::Pow(1.0f - Alpha, 2.0f);

	case EWeatherTransitionMode::EaseInOut:
		return Alpha < 0.5f
			? 2.0f * Alpha * Alpha
			: 1.0f - FMath::Pow(-2.0f * Alpha + 2.0f, 2.0f) / 2.0f;

	case EWeatherTransitionMode::SmoothStep:
		return Alpha * Alpha * (3.0f - 2.0f * Alpha);

	default:
		return Alpha;
	}
}

void UWeatherManager::LoadWeatherMPC()
{
	// Load Material Parameter Collection
	FString MPCPath = TEXT("/Game/Materials/MPC_Weather.MPC_Weather");
	WeatherMPC = LoadObject<UMaterialParameterCollection>(nullptr, *MPCPath);

	if (WeatherMPC)
	{
		UE_LOG(LogTemp, Log, TEXT("WeatherManager: Loaded Material Parameter Collection"));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherManager: Failed to load Material Parameter Collection at %s"), *MPCPath);
	}
}

void UWeatherManager::TriggerLightningStrike()
{
	if (!GetWorld())
	{
		return;
	}

	// Calculate strike location (near player or random)
	FVector StrikeLocation;
	if (APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(GetWorld(), 0))
	{
		FVector PlayerLocation = PlayerPawn->GetActorLocation();
		FVector RandomOffset = FVector(
			FMath::RandRange(-5000.0f, 5000.0f),
			FMath::RandRange(-5000.0f, 5000.0f),
			10000.0f
		);
		StrikeLocation = PlayerLocation + RandomOffset;
	}
	else
	{
		// Default location if no player
		StrikeLocation = FVector(0.0f, 0.0f, 10000.0f);
	}

	float Intensity = CurrentParameters.LightningIntensity * FMath::FRandRange(0.8f, 1.0f);

	// Broadcast lightning strike event
	OnLightningStrike.Broadcast(StrikeLocation, Intensity);

	// Notify AudioManager to play thunder sound
	if (UWorld* World = GetWorld())
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			// AudioManager is a component, not a subsystem, so we need to find it
			// This will be handled via event bus or direct reference
			UE_LOG(LogTemp, Log, TEXT("WeatherManager: Lightning strike at location %s with intensity %f"),
				*StrikeLocation.ToString(), Intensity);
		}
	}
}

void UWeatherManager::ApplyWeatherPreset(UWeatherPreset* Preset)
{
	if (!Preset)
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherManager: Attempted to apply null weather preset"));
		return;
	}

	SetWeatherIntensity(Preset->Intensity);
	SetWeatherState(Preset->WeatherState, Preset->TransitionDuration);
	UE_LOG(LogTemp, Log, TEXT("WeatherManager: Applied weather preset '%s'"), *Preset->PresetName);
}

void UWeatherManager::SetWeatherPresetLibrary(UWeatherPresetLibrary* Library)
{
	WeatherPresetLibrary = Library;
	UE_LOG(LogTemp, Log, TEXT("WeatherManager: Weather preset library set"));
}

void UWeatherManager::ApplyRandomWeatherBySeason(float SeasonProgress, const FString& TimeOfDayState)
{
	if (!WeatherPresetLibrary)
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherManager: No weather preset library set"));
		return;
	}

	UWeatherPreset* RandomPreset = WeatherPresetLibrary->GetRandomWeatherPreset(SeasonProgress, TimeOfDayState);
	if (RandomPreset)
	{
		ApplyWeatherPreset(RandomPreset);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherManager: No valid weather preset found for season %f and time %s"), SeasonProgress, *TimeOfDayState);
	}
}
