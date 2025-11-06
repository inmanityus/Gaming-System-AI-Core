// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "BodyBrokerSettingsSaveGame.h"
#include "BodyBrokerSettingsWidget.generated.h"

class USlider;
class UCheckBox;
class UComboBoxString;
class USpinBox;
class UButton;
class UTextBlock;

/**
 * BodyBrokerSettingsWidget - UMG widget for settings menu
 * GE-005: Settings System (Audio/Video/Controls)
 */
UCLASS()
class BODYBROKER_API UBodyBrokerSettingsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	// Load settings into UI
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void LoadSettingsIntoUI();

	// Apply settings from UI
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void ApplySettings();

	// Reset to defaults
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void ResetToDefaults();

	// Save settings
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void SaveSettings();

	// Cancel changes
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void CancelChanges();

	// Event delegates
	DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSettingsApplied);
	UPROPERTY(BlueprintAssignable, Category = "Settings|Events")
	FOnSettingsApplied OnSettingsApplied;

	DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSettingsCancelled);
	UPROPERTY(BlueprintAssignable, Category = "Settings|Events")
	FOnSettingsCancelled OnSettingsCancelled;

protected:
	// Settings save game instance
	UPROPERTY()
	TObjectPtr<UBodyBrokerSettingsSaveGame> SettingsSaveGame;

	// Audio settings widgets
	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USlider> MasterVolumeSlider;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USlider> MusicVolumeSlider;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USlider> VoiceVolumeSlider;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USlider> EffectsVolumeSlider;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USlider> UIVolumeSlider;

	// Video settings widgets
	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UComboBoxString> ResolutionComboBox;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UComboBoxString> QualityPresetComboBox;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UComboBoxString> WindowModeComboBox;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UCheckBox> VSyncCheckBox;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USpinBox> FrameRateLimitSpinBox;

	// Controls settings widgets
	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USlider> MouseSensitivitySlider;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UCheckBox> InvertYAxisCheckBox;

	// Gameplay settings widgets
	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UCheckBox> EnableSubtitlesCheckBox;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UComboBoxString> DifficultyComboBox;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<USpinBox> AutoSaveFrequencySpinBox;

	// Action buttons
	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UButton> ApplyButton;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UButton> SaveButton;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UButton> ResetButton;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UButton> CancelButton;

	// Widget event handlers
	UFUNCTION()
	void OnApplyButtonClicked();

	UFUNCTION()
	void OnSaveButtonClicked();

	UFUNCTION()
	void OnResetButtonClicked();

	UFUNCTION()
	void OnCancelButtonClicked();

	// Audio slider handlers
	UFUNCTION()
	void OnMasterVolumeChanged(float Value);

	UFUNCTION()
	void OnMusicVolumeChanged(float Value);

	UFUNCTION()
	void OnVoiceVolumeChanged(float Value);

	UFUNCTION()
	void OnEffectsVolumeChanged(float Value);

	UFUNCTION()
	void OnUIVolumeChanged(float Value);

	// Video handlers
	UFUNCTION()
	void OnResolutionChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnQualityPresetChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnWindowModeChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnVSyncChanged(bool bIsChecked);

	UFUNCTION()
	void OnFrameRateLimitChanged(float Value);

	// Controls handlers
	UFUNCTION()
	void OnMouseSensitivityChanged(float Value);

	UFUNCTION()
	void OnInvertYAxisChanged(bool bIsChecked);

	// Gameplay handlers
	UFUNCTION()
	void OnEnableSubtitlesChanged(bool bIsChecked);

	UFUNCTION()
	void OnDifficultyChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnAutoSaveFrequencyChanged(float Value);

	// Helper functions
	void PopulateResolutionComboBox();
	void PopulateQualityPresetComboBox();
	void PopulateWindowModeComboBox();
	void PopulateDifficultyComboBox();

	// Apply video settings to engine
	void ApplyVideoSettingsToEngine();

	// Apply audio settings to audio manager
	void ApplyAudioSettingsToAudioManager();

	// Store original settings for cancel
	FBodyBrokerAudioSettings OriginalAudioSettings;
	FVideoSettings OriginalVideoSettings;
	FControlsSettings OriginalControlsSettings;
	FGameplaySettings OriginalGameplaySettings;
};

