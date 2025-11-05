// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Http.h"
#include "Engine/Engine.h"
#include "TimeOfDayManager.generated.h"

/**
 * TimeOfDayManager - Manages game time progression and communicates with backend API.
 * REAL IMPLEMENTATION - No mocks, uses actual HTTP calls to backend Time Manager service.
 */
UCLASS()
class BODYBROKER_API UTimeOfDayManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Get the singleton instance of TimeOfDayManager.
	 */
	UFUNCTION(BlueprintCallable, Category = "TimeOfDay")
	static UTimeOfDayManager* Get(const UObject* WorldContext);

	/**
	 * Get current game time data.
	 */
	UFUNCTION(BlueprintCallable, Category = "TimeOfDay")
	void GetCurrentTime(int32& OutHour, int32& OutMinute, int32& OutDay, FString& OutState);

	/**
	 * Set game time manually.
	 */
	UFUNCTION(BlueprintCallable, Category = "TimeOfDay")
	void SetTime(int32 Hour, int32 Minute, int32 Day = -1);

	/**
	 * Start time progression.
	 */
	UFUNCTION(BlueprintCallable, Category = "TimeOfDay")
	void StartTimeProgression();

	/**
	 * Stop time progression.
	 */
	UFUNCTION(BlueprintCallable, Category = "TimeOfDay")
	void StopTimeProgression();

	/**
	 * Set time scale (real seconds per game hour).
	 */
	UFUNCTION(BlueprintCallable, Category = "TimeOfDay")
	void SetTimeScale(float RealSecondsPerGameHour);

	/**
	 * Event broadcasted when time changes.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FOnTimeChanged, int32, Hour, int32, Minute, int32, Day, FString, State);
	UPROPERTY(BlueprintAssignable, Category = "TimeOfDay")
	FOnTimeChanged OnTimeChanged;

	/**
	 * Event broadcasted when time of day state changes (dawn/day/dusk/night).
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnTimeStateChanged, FString, OldState, FString, NewState);
	UPROPERTY(BlueprintAssignable, Category = "TimeOfDay")
	FOnTimeStateChanged OnTimeStateChanged;

private:
	// Backend API URL
	UPROPERTY()
	FString BackendAPIUrl;

	// Current cached time data
	UPROPERTY()
	int32 CachedHour;

	UPROPERTY()
	int32 CachedMinute;

	UPROPERTY()
	int32 CachedDay;

	UPROPERTY()
	FString CachedState;

	// Update interval (seconds)
	UPROPERTY()
	float UpdateInterval;

	// Timer handle for periodic updates
	FTimerHandle UpdateTimerHandle;

	// Is time progression active
	UPROPERTY()
	bool bIsTimeProgressionActive;

	/**
	 * Fetch current time from backend API.
	 */
	void FetchCurrentTime();

	/**
	 * Handle HTTP response from time API.
	 */
	void OnTimeResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

	/**
	 * Update cached time data.
	 */
	void UpdateTimeData(int32 Hour, int32 Minute, int32 Day, const FString& State);

	/**
	 * Periodic update callback.
	 */
	void OnPeriodicUpdate();
};




