// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyBrokerSettingsSaveGame.h"
#include "GameFramework/SaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/Engine.h"

UBodyBrokerSettingsSaveGame::UBodyBrokerSettingsSaveGame(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	InitializeDefaults();
}

bool UBodyBrokerSettingsSaveGame::SaveSettings()
{
	if (!UGameplayStatics::SaveGameToSlot(this, GetSaveSlotName(), GetUserIndex()))
	{
		UE_LOG(LogTemp, Error, TEXT("BodyBrokerSettingsSaveGame: Failed to save settings"));
		return false;
	}

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerSettingsSaveGame: Settings saved successfully"));
	return true;
}

bool UBodyBrokerSettingsSaveGame::LoadSettings()
{
	UBodyBrokerSettingsSaveGame* LoadedSettings = Cast<UBodyBrokerSettingsSaveGame>(
		UGameplayStatics::LoadGameFromSlot(GetSaveSlotName(), GetUserIndex())
	);

	if (!LoadedSettings)
	{
		UE_LOG(LogTemp, Warning, TEXT("BodyBrokerSettingsSaveGame: No saved settings found, using defaults"));
		InitializeDefaults();
		return false;
	}

	// Copy loaded settings
	AudioSettings = LoadedSettings->AudioSettings;
	VideoSettings = LoadedSettings->VideoSettings;
	ControlsSettings = LoadedSettings->ControlsSettings;
	GameplaySettings = LoadedSettings->GameplaySettings;

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerSettingsSaveGame: Settings loaded successfully"));
	return true;
}

void UBodyBrokerSettingsSaveGame::ResetToDefaults()
{
	InitializeDefaults();
	UE_LOG(LogTemp, Log, TEXT("BodyBrokerSettingsSaveGame: Settings reset to defaults"));
}

void UBodyBrokerSettingsSaveGame::InitializeDefaults()
{
	// Initialize all settings to default values
	AudioSettings = FBodyBrokerAudioSettings();
	VideoSettings = FVideoSettings();
	ControlsSettings = FControlsSettings();
	GameplaySettings = FGameplaySettings();

	UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerSettingsSaveGame: Initialized with default values"));
}

