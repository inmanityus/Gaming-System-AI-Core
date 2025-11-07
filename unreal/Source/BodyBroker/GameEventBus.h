// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "GameEventBus.generated.h"

/**
 * Event types for game event bus
 */
UENUM(BlueprintType)
enum class EGameEventType : uint8
{
	WeatherChanged		UMETA(DisplayName = "Weather Changed"),
	TimeChanged			UMETA(DisplayName = "Time Changed"),
	DialogueStarted		UMETA(DisplayName = "Dialogue Started"),
	DialogueCompleted	UMETA(DisplayName = "Dialogue Completed"),
	ExpressionChanged	UMETA(DisplayName = "Expression Changed"),
	BiomeChanged		UMETA(DisplayName = "Biome Changed"),
	AudioStateChanged	UMETA(DisplayName = "Audio State Changed"),
	Custom				UMETA(DisplayName = "Custom")
};

/**
 * Game event data structure
 */
USTRUCT(BlueprintType)
struct FGameEventData
{
	GENERATED_BODY()

	// Event type
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Event")
	EGameEventType EventType;

	// Event data as JSON string
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Event")
	FString EventData;

	// Source system
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Event")
	FString SourceSystem;

	// Timestamp
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Event")
	float Timestamp;

	FGameEventData()
		: EventType(EGameEventType::Custom)
		, Timestamp(0.0f)
	{}
};

/**
 * GameEventBus - Central event bus for all game systems
 * INT-001: Event Bus Integration
 */
UCLASS()
class BODYBROKER_API UGameEventBus : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Get the singleton instance of GameEventBus.
	 */
	UFUNCTION(BlueprintCallable, Category = "Event Bus")
	static UGameEventBus* Get(const UObject* WorldContext);

	/**
	 * Subscribe to event type.
	 */
	UFUNCTION(BlueprintCallable, Category = "Event Bus")
	void Subscribe(EGameEventType EventType, UObject* Subscriber);

	/**
	 * Unsubscribe from event type.
	 */
	UFUNCTION(BlueprintCallable, Category = "Event Bus")
	void Unsubscribe(EGameEventType EventType, UObject* Subscriber);

	/**
	 * Publish event.
	 */
	UFUNCTION(BlueprintCallable, Category = "Event Bus")
	void PublishEvent(const FGameEventData& EventData);

	/**
	 * Event broadcasted when any event is published.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnGameEvent, const FGameEventData&, EventData);
	UPROPERTY(BlueprintAssignable, Category = "Event Bus|Events")
	FOnGameEvent OnGameEvent;

private:
	// Subscribers by event type (non-UPROPERTY, stored as raw pointers for TMap compatibility)
	TMap<EGameEventType, TArray<TWeakObjectPtr<UObject>>> Subscribers;

	// Event history (last 100 events)
	UPROPERTY()
	TArray<FGameEventData> EventHistory;

	// Max event history size
	static constexpr int32 MAX_EVENT_HISTORY = 100;
};

