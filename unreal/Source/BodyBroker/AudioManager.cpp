// Copyright Epic Games, Inc. All Rights Reserved.

#include "AudioManager.h"
#include "Components/AudioComponent.h"
#include "Http.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "Engine/Engine.h"

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
}

void UAudioManager::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Stop all audio components
	for (auto& Pair : ActiveAudioComponents)
	{
		if (Pair.Value)
		{
			Pair.Value->Stop();
			Pair.Value->DestroyComponent();
		}
	}
	ActiveAudioComponents.Empty();

	Super::EndPlay(EndPlayReason);
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

