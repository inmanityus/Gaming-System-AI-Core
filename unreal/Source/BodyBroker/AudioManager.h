// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AudioManager.generated.h"

class USoundBase;
class UAudioComponent;
class IHttpRequest;
class IHttpResponse;

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
};

