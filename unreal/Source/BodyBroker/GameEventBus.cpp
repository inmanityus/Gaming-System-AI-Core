// Copyright Epic Games, Inc. All Rights Reserved.

#include "GameEventBus.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"

void UGameEventBus::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	EventHistory.Empty();
	Subscribers.Empty();
	UE_LOG(LogTemp, Log, TEXT("GameEventBus: Initialized"));
}

void UGameEventBus::Deinitialize()
{
	Subscribers.Empty();
	EventHistory.Empty();
	Super::Deinitialize();
}

UGameEventBus* UGameEventBus::Get(const UObject* WorldContext)
{
	if (!WorldContext)
	{
		return nullptr;
	}

	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UGameEventBus>();
		}
	}

	return nullptr;
}

void UGameEventBus::Subscribe(EGameEventType EventType, UObject* Subscriber)
{
	if (!Subscriber)
	{
		UE_LOG(LogTemp, Warning, TEXT("GameEventBus: Attempted to subscribe null object"));
		return;
	}

	TArray<TWeakObjectPtr<UObject>>* SubscriberList = Subscribers.Find(EventType);
	if (!SubscriberList)
	{
		Subscribers.Add(EventType, TArray<TWeakObjectPtr<UObject>>());
		SubscriberList = Subscribers.Find(EventType);
	}

	if (SubscriberList)
	{
		SubscriberList->AddUnique(Subscriber);
		UE_LOG(LogTemp, Verbose, TEXT("GameEventBus: Subscriber added for event type %d"), (int32)EventType);
	}
}

void UGameEventBus::Unsubscribe(EGameEventType EventType, UObject* Subscriber)
{
	if (!Subscriber)
	{
		return;
	}

	TArray<TWeakObjectPtr<UObject>>* SubscriberList = Subscribers.Find(EventType);
	if (SubscriberList)
	{
		SubscriberList->RemoveAll([Subscriber](const TWeakObjectPtr<UObject>& Obj)
		{
			return Obj.Get() == Subscriber;
		});
		UE_LOG(LogTemp, Verbose, TEXT("GameEventBus: Subscriber removed for event type %d"), (int32)EventType);
	}
}

void UGameEventBus::PublishEvent(const FGameEventData& EventData)
{
	// Add to history
	EventHistory.Add(EventData);
	if (EventHistory.Num() > MAX_EVENT_HISTORY)
	{
		EventHistory.RemoveAt(0);
	}

	// Broadcast to all subscribers
	TArray<TWeakObjectPtr<UObject>>* SubscriberList = Subscribers.Find(EventData.EventType);
	if (SubscriberList)
	{
		// Remove invalid subscribers
		SubscriberList->RemoveAll([](const TWeakObjectPtr<UObject>& Obj)
		{
			return !Obj.IsValid();
		});

		// Notify valid subscribers (via multicast delegate)
		OnGameEvent.Broadcast(EventData);
	}

	// Also broadcast to all-event subscribers (EGameEventType::Custom means all events)
	TArray<TWeakObjectPtr<UObject>>* AllEventSubscribers = Subscribers.Find(EGameEventType::Custom);
	if (AllEventSubscribers)
	{
		AllEventSubscribers->RemoveAll([](const TWeakObjectPtr<UObject>& Obj)
		{
			return !Obj.IsValid();
		});

		OnGameEvent.Broadcast(EventData);
	}

	UE_LOG(LogTemp, VeryVerbose, TEXT("GameEventBus: Published event type %d from %s"), 
		(int32)EventData.EventType, *EventData.SourceSystem);
}

