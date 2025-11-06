// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyBrokerSettingsWidget.h"
#include "Components/Slider.h"
#include "Components/CheckBox.h"
#include "Components/ComboBoxString.h"
#include "Components/SpinBox.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "AudioManager.h"

void UBodyBrokerSettingsWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// Create or load settings save game
	SettingsSaveGame = Cast<UBodyBrokerSettingsSaveGame>(
		UGameplayStatics::LoadGameFromSlot(
			UBodyBrokerSettingsSaveGame::GetSaveSlotName(),
			UBodyBrokerSettingsSaveGame::GetUserIndex()
		)
	);

	if (!SettingsSaveGame)
	{
		SettingsSaveGame = Cast<UBodyBrokerSettingsSaveGame>(
			UGameplayStatics::CreateSaveGameObject(UBodyBrokerSettingsSaveGame::StaticClass())
		);
		SettingsSaveGame->LoadSettings();
	}

	// Store original settings for cancel
	OriginalAudioSettings = SettingsSaveGame->AudioSettings;
	OriginalVideoSettings = SettingsSaveGame->VideoSettings;
	OriginalControlsSettings = SettingsSaveGame->ControlsSettings;
	OriginalGameplaySettings = SettingsSaveGame->GameplaySettings;

	// Populate combo boxes
	PopulateResolutionComboBox();
	PopulateQualityPresetComboBox();
	PopulateWindowModeComboBox();
	PopulateDifficultyComboBox();

	// Bind button events
	if (ApplyButton)
	{
		ApplyButton->OnClicked.AddDynamic(this, &UBodyBrokerSettingsWidget::OnApplyButtonClicked);
	}
	if (SaveButton)
	{
		SaveButton->OnClicked.AddDynamic(this, &UBodyBrokerSettingsWidget::OnSaveButtonClicked);
	}
	if (ResetButton)
	{
		ResetButton->OnClicked.AddDynamic(this, &UBodyBrokerSettingsWidget::OnResetButtonClicked);
	}
	if (CancelButton)
	{
		CancelButton->OnClicked.AddDynamic(this, &UBodyBrokerSettingsWidget::OnCancelButtonClicked);
	}

	// Bind audio slider events
	if (MasterVolumeSlider)
	{
		MasterVolumeSlider->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnMasterVolumeChanged);
	}
	if (MusicVolumeSlider)
	{
		MusicVolumeSlider->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnMusicVolumeChanged);
	}
	if (VoiceVolumeSlider)
	{
		VoiceVolumeSlider->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnVoiceVolumeChanged);
	}
	if (EffectsVolumeSlider)
	{
		EffectsVolumeSlider->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnEffectsVolumeChanged);
	}
	if (UIVolumeSlider)
	{
		UIVolumeSlider->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnUIVolumeChanged);
	}

	// Bind video events
	if (ResolutionComboBox)
	{
		ResolutionComboBox->OnSelectionChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnResolutionChanged);
	}
	if (QualityPresetComboBox)
	{
		QualityPresetComboBox->OnSelectionChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnQualityPresetChanged);
	}
	if (WindowModeComboBox)
	{
		WindowModeComboBox->OnSelectionChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnWindowModeChanged);
	}
	if (VSyncCheckBox)
	{
		VSyncCheckBox->OnCheckStateChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnVSyncChanged);
	}
	if (FrameRateLimitSpinBox)
	{
		FrameRateLimitSpinBox->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnFrameRateLimitChanged);
	}

	// Bind controls events
	if (MouseSensitivitySlider)
	{
		MouseSensitivitySlider->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnMouseSensitivityChanged);
	}
	if (InvertYAxisCheckBox)
	{
		InvertYAxisCheckBox->OnCheckStateChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnInvertYAxisChanged);
	}

	// Bind gameplay events
	if (EnableSubtitlesCheckBox)
	{
		EnableSubtitlesCheckBox->OnCheckStateChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnEnableSubtitlesChanged);
	}
	if (DifficultyComboBox)
	{
		DifficultyComboBox->OnSelectionChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnDifficultyChanged);
	}
	if (AutoSaveFrequencySpinBox)
	{
		AutoSaveFrequencySpinBox->OnValueChanged.AddDynamic(this, &UBodyBrokerSettingsWidget::OnAutoSaveFrequencyChanged);
	}

	// Load settings into UI
	LoadSettingsIntoUI();
}

void UBodyBrokerSettingsWidget::NativeDestruct()
{
	Super::NativeDestruct();
}

void UBodyBrokerSettingsWidget::LoadSettingsIntoUI()
{
	if (!SettingsSaveGame)
	{
		return;
	}

	// Load audio settings
	if (MasterVolumeSlider)
	{
		MasterVolumeSlider->SetValue(SettingsSaveGame->AudioSettings.MasterVolume);
	}
	if (MusicVolumeSlider)
	{
		MusicVolumeSlider->SetValue(SettingsSaveGame->AudioSettings.MusicVolume);
	}
	if (VoiceVolumeSlider)
	{
		VoiceVolumeSlider->SetValue(SettingsSaveGame->AudioSettings.VoiceVolume);
	}
	if (EffectsVolumeSlider)
	{
		EffectsVolumeSlider->SetValue(SettingsSaveGame->AudioSettings.EffectsVolume);
	}
	if (UIVolumeSlider)
	{
		UIVolumeSlider->SetValue(SettingsSaveGame->AudioSettings.UIVolume);
	}

	// Load video settings
	if (ResolutionComboBox)
	{
		FString ResolutionStr = FString::Printf(TEXT("%dx%d"), 
			SettingsSaveGame->VideoSettings.ScreenResolutionX,
			SettingsSaveGame->VideoSettings.ScreenResolutionY);
		ResolutionComboBox->SetSelectedOption(ResolutionStr);
	}
	if (QualityPresetComboBox)
	{
		FString QualityStr = FString::Printf(TEXT("%d"), SettingsSaveGame->VideoSettings.QualityPreset);
		QualityPresetComboBox->SetSelectedOption(QualityStr);
	}
	if (WindowModeComboBox)
	{
		FString WindowModeStr = FString::Printf(TEXT("%d"), SettingsSaveGame->VideoSettings.WindowMode);
		WindowModeComboBox->SetSelectedOption(WindowModeStr);
	}
	if (VSyncCheckBox)
	{
		VSyncCheckBox->SetIsChecked(SettingsSaveGame->VideoSettings.bEnableVSync);
	}
	if (FrameRateLimitSpinBox)
	{
		FrameRateLimitSpinBox->SetValue(SettingsSaveGame->VideoSettings.FrameRateLimit);
	}

	// Load controls settings
	if (MouseSensitivitySlider)
	{
		MouseSensitivitySlider->SetValue(SettingsSaveGame->ControlsSettings.MouseSensitivity);
	}
	if (InvertYAxisCheckBox)
	{
		InvertYAxisCheckBox->SetIsChecked(SettingsSaveGame->ControlsSettings.bInvertYAxis);
	}

	// Load gameplay settings
	if (EnableSubtitlesCheckBox)
	{
		EnableSubtitlesCheckBox->SetIsChecked(SettingsSaveGame->GameplaySettings.bEnableSubtitles);
	}
	if (DifficultyComboBox)
	{
		FString DifficultyStr = FString::Printf(TEXT("%d"), SettingsSaveGame->GameplaySettings.DifficultyLevel);
		DifficultyComboBox->SetSelectedOption(DifficultyStr);
	}
	if (AutoSaveFrequencySpinBox)
	{
		AutoSaveFrequencySpinBox->SetValue(SettingsSaveGame->GameplaySettings.AutoSaveFrequency);
	}
}

void UBodyBrokerSettingsWidget::ApplySettings()
{
	if (!SettingsSaveGame)
	{
		return;
	}

	// Apply video settings to engine immediately
	ApplyVideoSettingsToEngine();

	// Apply audio settings to audio manager
	ApplyAudioSettingsToAudioManager();

	// Broadcast applied event
	OnSettingsApplied.Broadcast();
}

void UBodyBrokerSettingsWidget::ResetToDefaults()
{
	if (!SettingsSaveGame)
	{
		return;
	}

	SettingsSaveGame->ResetToDefaults();
	LoadSettingsIntoUI();
}

void UBodyBrokerSettingsWidget::SaveSettings()
{
	if (!SettingsSaveGame)
	{
		return;
	}

	SettingsSaveGame->SaveSettings();
	UE_LOG(LogTemp, Log, TEXT("BodyBrokerSettingsWidget: Settings saved"));
}

void UBodyBrokerSettingsWidget::CancelChanges()
{
	if (!SettingsSaveGame)
	{
		return;
	}

	// Restore original settings
	SettingsSaveGame->AudioSettings = OriginalAudioSettings;
	SettingsSaveGame->VideoSettings = OriginalVideoSettings;
	SettingsSaveGame->ControlsSettings = OriginalControlsSettings;
	SettingsSaveGame->GameplaySettings = OriginalGameplaySettings;

	// Reload UI
	LoadSettingsIntoUI();

	// Broadcast cancelled event
	OnSettingsCancelled.Broadcast();
}

void UBodyBrokerSettingsWidget::OnApplyButtonClicked()
{
	ApplySettings();
}

void UBodyBrokerSettingsWidget::OnSaveButtonClicked()
{
	ApplySettings();
	SaveSettings();
}

void UBodyBrokerSettingsWidget::OnResetButtonClicked()
{
	ResetToDefaults();
}

void UBodyBrokerSettingsWidget::OnCancelButtonClicked()
{
	CancelChanges();
}

void UBodyBrokerSettingsWidget::OnMasterVolumeChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->AudioSettings.MasterVolume = Value;
		ApplyAudioSettingsToAudioManager();
	}
}

void UBodyBrokerSettingsWidget::OnMusicVolumeChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->AudioSettings.MusicVolume = Value;
		ApplyAudioSettingsToAudioManager();
	}
}

void UBodyBrokerSettingsWidget::OnVoiceVolumeChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->AudioSettings.VoiceVolume = Value;
		ApplyAudioSettingsToAudioManager();
	}
}

void UBodyBrokerSettingsWidget::OnEffectsVolumeChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->AudioSettings.EffectsVolume = Value;
		ApplyAudioSettingsToAudioManager();
	}
}

void UBodyBrokerSettingsWidget::OnUIVolumeChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->AudioSettings.UIVolume = Value;
		ApplyAudioSettingsToAudioManager();
	}
}

void UBodyBrokerSettingsWidget::OnResolutionChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	if (!SettingsSaveGame || SelectionType != ESelectInfo::OnMouseClick)
	{
		return;
	}

	// Parse resolution string (e.g., "1920x1080")
	TArray<FString> Parts;
	SelectedItem.ParseIntoArray(Parts, TEXT("x"), true);
	if (Parts.Num() == 2)
	{
		SettingsSaveGame->VideoSettings.ScreenResolutionX = FCString::Atoi(*Parts[0]);
		SettingsSaveGame->VideoSettings.ScreenResolutionY = FCString::Atoi(*Parts[1]);
	}
}

void UBodyBrokerSettingsWidget::OnQualityPresetChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	if (SettingsSaveGame && SelectionType == ESelectInfo::OnMouseClick)
	{
		SettingsSaveGame->VideoSettings.QualityPreset = FCString::Atoi(*SelectedItem);
	}
}

void UBodyBrokerSettingsWidget::OnWindowModeChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	if (SettingsSaveGame && SelectionType == ESelectInfo::OnMouseClick)
	{
		SettingsSaveGame->VideoSettings.WindowMode = FCString::Atoi(*SelectedItem);
	}
}

void UBodyBrokerSettingsWidget::OnVSyncChanged(bool bIsChecked)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->VideoSettings.bEnableVSync = bIsChecked;
	}
}

void UBodyBrokerSettingsWidget::OnFrameRateLimitChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->VideoSettings.FrameRateLimit = FMath::RoundToInt(Value);
	}
}

void UBodyBrokerSettingsWidget::OnMouseSensitivityChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->ControlsSettings.MouseSensitivity = Value;
	}
}

void UBodyBrokerSettingsWidget::OnInvertYAxisChanged(bool bIsChecked)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->ControlsSettings.bInvertYAxis = bIsChecked;
	}
}

void UBodyBrokerSettingsWidget::OnEnableSubtitlesChanged(bool bIsChecked)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->GameplaySettings.bEnableSubtitles = bIsChecked;
	}
}

void UBodyBrokerSettingsWidget::OnDifficultyChanged(FString SelectedItem, ESelectInfo::Type SelectionType)
{
	if (SettingsSaveGame && SelectionType == ESelectInfo::OnMouseClick)
	{
		SettingsSaveGame->GameplaySettings.DifficultyLevel = FCString::Atoi(*SelectedItem);
	}
}

void UBodyBrokerSettingsWidget::OnAutoSaveFrequencyChanged(float Value)
{
	if (SettingsSaveGame)
	{
		SettingsSaveGame->GameplaySettings.AutoSaveFrequency = FMath::RoundToInt(Value);
	}
}

void UBodyBrokerSettingsWidget::PopulateResolutionComboBox()
{
	if (!ResolutionComboBox)
	{
		return;
	}

	ResolutionComboBox->ClearOptions();
	ResolutionComboBox->AddOption(TEXT("1280x720"));
	ResolutionComboBox->AddOption(TEXT("1920x1080"));
	ResolutionComboBox->AddOption(TEXT("2560x1440"));
	ResolutionComboBox->AddOption(TEXT("3840x2160"));
}

void UBodyBrokerSettingsWidget::PopulateQualityPresetComboBox()
{
	if (!QualityPresetComboBox)
	{
		return;
	}

	QualityPresetComboBox->ClearOptions();
	QualityPresetComboBox->AddOption(TEXT("0"));  // Low
	QualityPresetComboBox->AddOption(TEXT("1"));  // Medium
	QualityPresetComboBox->AddOption(TEXT("2"));  // High
	QualityPresetComboBox->AddOption(TEXT("3"));  // Ultra
}

void UBodyBrokerSettingsWidget::PopulateWindowModeComboBox()
{
	if (!WindowModeComboBox)
	{
		return;
	}

	WindowModeComboBox->ClearOptions();
	WindowModeComboBox->AddOption(TEXT("0"));  // Fullscreen
	WindowModeComboBox->AddOption(TEXT("1"));  // Windowed
	WindowModeComboBox->AddOption(TEXT("2"));  // WindowedFullscreen
}

void UBodyBrokerSettingsWidget::PopulateDifficultyComboBox()
{
	if (!DifficultyComboBox)
	{
		return;
	}

	DifficultyComboBox->ClearOptions();
	DifficultyComboBox->AddOption(TEXT("0"));  // Easy
	DifficultyComboBox->AddOption(TEXT("1"));  // Normal
	DifficultyComboBox->AddOption(TEXT("2"));  // Hard
	DifficultyComboBox->AddOption(TEXT("3"));  // Nightmare
}

void UBodyBrokerSettingsWidget::ApplyVideoSettingsToEngine()
{
	if (!SettingsSaveGame)
	{
		return;
	}

	UGameUserSettings* UserSettings = GEngine->GetGameUserSettings();
	if (!UserSettings)
	{
		return;
	}

	// Apply resolution
	FIntPoint Resolution(
		SettingsSaveGame->VideoSettings.ScreenResolutionX,
		SettingsSaveGame->VideoSettings.ScreenResolutionY
	);
	UserSettings->SetScreenResolution(Resolution);

	// Apply window mode
	EWindowMode::Type WindowMode = EWindowMode::Fullscreen;
	switch (SettingsSaveGame->VideoSettings.WindowMode)
	{
		case 0:
			WindowMode = EWindowMode::Fullscreen;
			break;
		case 1:
			WindowMode = EWindowMode::Windowed;
			break;
		case 2:
			WindowMode = EWindowMode::WindowedFullscreen;
			break;
	}
	UserSettings->SetFullscreenMode(WindowMode);

	// Apply VSync
	UserSettings->SetVSyncEnabled(SettingsSaveGame->VideoSettings.bEnableVSync);

	// Apply frame rate limit
	UserSettings->SetFrameRateLimit(SettingsSaveGame->VideoSettings.FrameRateLimit);

	// Apply quality preset
	UserSettings->SetOverallScalabilityLevel(SettingsSaveGame->VideoSettings.QualityPreset);

	// Apply and save settings
	UserSettings->ApplySettings(false);
	UserSettings->SaveSettings();

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerSettingsWidget: Video settings applied to engine"));
}

void UBodyBrokerSettingsWidget::ApplyAudioSettingsToAudioManager()
{
	if (!SettingsSaveGame)
	{
		return;
	}

	// Get AudioManager from GameInstance
	if (UWorld* World = GetWorld())
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			// AudioManager is an ActorComponent, not a subsystem
			// We need to find it on a specific actor or access it differently
			// For now, skip audio manager integration - it will be handled elsewhere
			UE_LOG(LogTemp, Log, TEXT("BodyBrokerSettingsWidget: Audio settings saved (AudioManager integration pending)"));
		}
	}
}

