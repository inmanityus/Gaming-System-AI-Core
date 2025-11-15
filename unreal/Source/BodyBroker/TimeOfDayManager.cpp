// Copyright Epic Games, Inc. All Rights Reserved.

#include "TimeOfDayManager.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Engine/Engine.h"
#include "TimerManager.h"

void UTimeOfDayManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Set default backend API URL (can be overridden via config)
	BackendAPIUrl = TEXT("http://localhost:8002/api/time");

	// Initialize cached values
	CachedHour = 7;
	CachedMinute = 0;
	CachedDay = 1;
	CachedState = TEXT("day");
	bIsTimeProgressionActive = false;
	UpdateInterval = 1.0f; // Update every 1 second

	UE_LOG(LogTemp, Log, TEXT("[TimeOfDayManager] Initialized - Backend API: %s"), *BackendAPIUrl);
}

void UTimeOfDayManager::Deinitialize()
{
	// Stop any active timers
	if (UWorld* World = GetWorld())
	{
		if (FTimerManager* TimerManager = &World->GetTimerManager())
		{
			TimerManager->ClearTimer(UpdateTimerHandle);
		}
	}

	Super::Deinitialize();
}

UTimeOfDayManager* UTimeOfDayManager::Get(const UObject* WorldContext)
{
	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UTimeOfDayManager>();
		}
	}
	return nullptr;
}

void UTimeOfDayManager::GetCurrentTime(int32& OutHour, int32& OutMinute, int32& OutDay, FString& OutState)
{
	OutHour = CachedHour;
	OutMinute = CachedMinute;
	OutDay = CachedDay;
	OutState = CachedState;
}

void UTimeOfDayManager::SetTime(int32 Hour, int32 Minute, int32 Day)
{
	// Validate inputs
	if (Hour < 0 || Hour >= 24)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TimeOfDayManager] Invalid hour: %d"), Hour);
		return;
	}
	if (Minute < 0 || Minute >= 60)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TimeOfDayManager] Invalid minute: %d"), Minute);
		return;
	}

	// Create HTTP request to backend API
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->OnProcessRequestComplete().BindUObject(this, &UTimeOfDayManager::OnTimeResponseReceived);
	
	// Set request URL
	FString URL = FString::Printf(TEXT("%s/set"), *BackendAPIUrl);
	Request->SetURL(URL);
	Request->SetVerb(TEXT("POST"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	// Create JSON body
	TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
	JsonObject->SetNumberField(TEXT("hour"), Hour);
	JsonObject->SetNumberField(TEXT("minute"), Minute);
	if (Day >= 0)
	{
		JsonObject->SetNumberField(TEXT("day"), Day);
	}

	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
	Request->SetContentAsString(OutputString);

	// Send request
	if (!Request->ProcessRequest())
	{
		UE_LOG(LogTemp, Error, TEXT("[TimeOfDayManager] Failed to process SetTime request"));
	}

	UE_LOG(LogTemp, Log, TEXT("[TimeOfDayManager] Setting time to %02d:%02d (Day %d)"), Hour, Minute, Day);
}

void UTimeOfDayManager::StartTimeProgression()
{
	if (bIsTimeProgressionActive)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TimeOfDayManager] Time progression already active"));
		return;
	}

	// Send start request to backend
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/start"), *BackendAPIUrl));
	Request->SetVerb(TEXT("POST"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	Request->ProcessRequest();

	// Start periodic updates
	if (UWorld* World = GetWorld())
	{
		FTimerManager& TimerManager = World->GetTimerManager();
		TimerManager.SetTimer(
			UpdateTimerHandle,
			this,
			&UTimeOfDayManager::OnPeriodicUpdate,
			UpdateInterval,
			true // Loop
		);
	}

	bIsTimeProgressionActive = true;
	UE_LOG(LogTemp, Log, TEXT("[TimeOfDayManager] Time progression started"));
}

void UTimeOfDayManager::StopTimeProgression()
{
	if (!bIsTimeProgressionActive)
	{
		return;
	}

	// Stop periodic updates
	if (UWorld* World = GetWorld())
	{
		FTimerManager& TimerManager = World->GetTimerManager();
		TimerManager.ClearTimer(UpdateTimerHandle);
	}

	// Send stop request to backend
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/stop"), *BackendAPIUrl));
	Request->SetVerb(TEXT("POST"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	Request->ProcessRequest();

	bIsTimeProgressionActive = false;
	UE_LOG(LogTemp, Log, TEXT("[TimeOfDayManager] Time progression stopped"));
}

void UTimeOfDayManager::SetTimeScale(float RealSecondsPerGameHour)
{
	if (RealSecondsPerGameHour <= 0.0f)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TimeOfDayManager] Invalid time scale: %f"), RealSecondsPerGameHour);
		return;
	}

	// Send time scale update to backend
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->SetURL(FString::Printf(TEXT("%s/scale"), *BackendAPIUrl));
	Request->SetVerb(TEXT("POST"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

	TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
	JsonObject->SetNumberField(TEXT("time_scale"), RealSecondsPerGameHour);

	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
	Request->SetContentAsString(OutputString);
	Request->ProcessRequest();

	UE_LOG(LogTemp, Log, TEXT("[TimeOfDayManager] Time scale set to %f seconds per game hour"), RealSecondsPerGameHour);
}

void UTimeOfDayManager::FetchCurrentTime()
{
	// Create HTTP request to get current time
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->OnProcessRequestComplete().BindUObject(this, &UTimeOfDayManager::OnTimeResponseReceived);
	Request->SetURL(FString::Printf(TEXT("%s/current"), *BackendAPIUrl));
	Request->SetVerb(TEXT("GET"));
	
	if (!Request->ProcessRequest())
	{
		UE_LOG(LogTemp, Error, TEXT("[TimeOfDayManager] Failed to process FetchCurrentTime request"));
	}
}

void UTimeOfDayManager::OnTimeResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
	if (!bWasSuccessful || !Response.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("[TimeOfDayManager] HTTP request failed"));
		return;
	}

	int32 ResponseCode = Response->GetResponseCode();
	if (ResponseCode != 200)
	{
		UE_LOG(LogTemp, Error, TEXT("[TimeOfDayManager] HTTP request returned error code: %d"), ResponseCode);
		return;
	}

	// Parse JSON response
	FString ResponseString = Response->GetContentAsString();
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("[TimeOfDayManager] Failed to parse JSON response"));
		return;
	}

	// Extract time data
	TSharedPtr<FJsonObject> TimeObject = JsonObject->GetObjectField(TEXT("time"));
	if (!TimeObject.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("[TimeOfDayManager] Invalid time object in response"));
		return;
	}

	int32 Hour = TimeObject->GetIntegerField(TEXT("hour"));
	int32 Minute = TimeObject->GetIntegerField(TEXT("minute"));
	int32 Day = TimeObject->GetIntegerField(TEXT("day"));
	FString State = TimeObject->GetStringField(TEXT("state"));

	UpdateTimeData(Hour, Minute, Day, State);
}

void UTimeOfDayManager::UpdateTimeData(int32 Hour, int32 Minute, int32 Day, const FString& State)
{
	// Check if state changed
	bool bStateChanged = (CachedState != State);
	FString OldState = CachedState;

	// Update cached values
	CachedHour = Hour;
	CachedMinute = Minute;
	CachedDay = Day;
	CachedState = State;

	// Broadcast events
	OnTimeChanged.Broadcast(Hour, Minute, Day, State);

	if (bStateChanged)
	{
		OnTimeStateChanged.Broadcast(OldState, State);
		UE_LOG(LogTemp, Log, TEXT("[TimeOfDayManager] Time state changed: %s -> %s"), *OldState, *State);
	}
}

void UTimeOfDayManager::OnPeriodicUpdate()
{
	// Fetch current time from backend
	FetchCurrentTime();
}











