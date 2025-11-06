// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "BodyBrokerSettingsSaveGame.generated.h"

// Audio settings structure
USTRUCT(BlueprintType)
struct FBodyBrokerAudioSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Audio")
	float MasterVolume;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Audio")
	float MusicVolume;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Audio")
	float VoiceVolume;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Audio")
	float EffectsVolume;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Audio")
	float UIVolume;

	FBodyBrokerAudioSettings()
		: MasterVolume(1.0f)
		, MusicVolume(0.8f)
		, VoiceVolume(1.0f)
		, EffectsVolume(1.0f)
		, UIVolume(0.7f)
	{
	}
};

// Video settings structure
USTRUCT(BlueprintType)
struct FVideoSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Video")
	int32 ScreenResolutionX;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Video")
	int32 ScreenResolutionY;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Video")
	int32 QualityPreset;  // 0=Low, 1=Medium, 2=High, 3=Ultra

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Video")
	int32 WindowMode;  // 0=Fullscreen, 1=Windowed, 2=WindowedFullscreen

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Video")
	bool bEnableVSync;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Video")
	int32 FrameRateLimit;

	FVideoSettings()
		: ScreenResolutionX(1920)
		, ScreenResolutionY(1080)
		, QualityPreset(2)  // High
		, WindowMode(0)  // Fullscreen
		, bEnableVSync(true)
		, FrameRateLimit(60)
	{
	}
};

// Controls settings structure
USTRUCT(BlueprintType)
struct FControlsSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Controls")
	float MouseSensitivity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Controls")
	bool bInvertYAxis;

	// Key bindings stored as string (can be expanded later)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Controls")
	TMap<FString, FString> KeyBindings;

	FControlsSettings()
		: MouseSensitivity(1.0f)
		, bInvertYAxis(false)
	{
	}
};

// Gameplay settings structure
USTRUCT(BlueprintType)
struct FGameplaySettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gameplay")
	bool bEnableSubtitles;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gameplay")
	int32 DifficultyLevel;  // 0=Easy, 1=Normal, 2=Hard, 3=Nightmare

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gameplay")
	int32 AutoSaveFrequency;  // Minutes

	FGameplaySettings()
		: bEnableSubtitles(true)
		, DifficultyLevel(1)  // Normal
		, AutoSaveFrequency(5)  // 5 minutes
	{
	}
};

/**
 * BodyBrokerSettingsSaveGame - Saves player settings (Audio, Video, Controls, Gameplay)
 * Uses UE5 SaveGame system for persistent storage
 */
UCLASS()
class BODYBROKER_API UBodyBrokerSettingsSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UBodyBrokerSettingsSaveGame(const FObjectInitializer& ObjectInitializer);

	// Audio settings
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Settings")
	FBodyBrokerAudioSettings AudioSettings;

	// Video settings
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Settings")
	FVideoSettings VideoSettings;

	// Controls settings
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Settings")
	FControlsSettings ControlsSettings;

	// Gameplay settings
	UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Settings")
	FGameplaySettings GameplaySettings;

	// Save settings to disk
	UFUNCTION(BlueprintCallable, Category = "Settings")
	bool SaveSettings();

	// Load settings from disk
	UFUNCTION(BlueprintCallable, Category = "Settings")
	bool LoadSettings();

	// Reset to default settings
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void ResetToDefaults();

	// Get save game slot name
	static FString GetSaveSlotName() { return TEXT("BodyBrokerSettings"); }
	static int32 GetUserIndex() { return 0; }

private:
	// Initialize default values
	void InitializeDefaults();
};

