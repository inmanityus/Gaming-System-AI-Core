# GameEventBus Integration Architecture
**Date**: 2025-01-29  
**Task**: INT-001 - Event Bus Integration  
**Status**: Design Complete

---

## OVERVIEW

Complete UE5 GameEventBus subsystem architecture for centralized event broadcasting and subscription, integrating with Python backend and all game systems.

---

## SYSTEM INTEGRATION

### Backend Event Bus (Already Implemented)

**Python Service**: `services/event_bus/event_bus.py`
- 23 event types defined
- Redis pub/sub support
- In-memory fallback
- Fully functional

**Goal**: Create UE5 C++ counterpart

---

## GAME EVENT BUS SUBSYSTEM

### GameEventBusSubsystem Architecture

```cpp
UCLASS()
class UGameEventBusSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    // USubsystem interface
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    // Get singleton instance
    UFUNCTION(BlueprintCallable, Category = "EventBus")
    static UGameEventBusSubsystem* Get(const UObject* WorldContext);

    // Subscribe to event type
    UFUNCTION(BlueprintCallable, Category = "EventBus")
    int32 SubscribeToEvent(EGameEventType EventType, UObject* Subscriber, FName FunctionName);
    
    // Unsubscribe from event type
    UFUNCTION(BlueprintCallable, Category = "EventBus")
    void UnsubscribeFromEvent(EGameEventType EventType, int32 SubscriptionID);
    
    // Publish event
    UFUNCTION(BlueprintCallable, Category = "EventBus")
    void PublishEvent(EGameEventType EventType, const FGameEventData& EventData);

private:
    // Event delegates
    TMap<EGameEventType, FMulticastDelegate> EventDelegates;
    
    // Subscription tracking
    struct FSubscriptionInfo
    {
        UObject* Subscriber;
        FName FunctionName;
        int32 SubscriptionID;
    };
    TMap<EGameEventType, TArray<FSubscriptionInfo>> Subscriptions;
    
    // Generate unique subscription ID
    int32 NextSubscriptionID;
};
```

---

## EVENT TYPES & DELEGATES

### Event Type Enum

```cpp
UENUM(BlueprintType)
enum class EGameEventType : uint8
{
    // Day/Night System
    TimeOfDayChanged,
    DayWorldActivated,
    NightWorldActivated,
    
    // Weather System
    WeatherChanged,
    SeasonChanged,
    WeatherTransitionStarted,
    
    // Audio System
    AudioEventTriggered,
    DialogueStarted,
    DialogueEnded,
    
    // Facial Expressions
    NPCExpressionChanged,
    EmotionalStateUpdated,
    
    // Terrain Ecosystems
    BiomeChanged,
    FloraSpawned,
    FaunaSpawned,
    
    // World State
    WorldStateUpdated,
    PlayerStateChanged,
    NPCStateChanged,
    QuestStateChanged,
    
    // Story Teller
    NarrativeGenerated,
    StoryNodeCompleted,
    
    // AI Systems
    ModelSwitched,
    GuardrailsViolation,
    InferenceCompleted,
    
    // Maximum
    MAX
};
```

### Event Data Structure

```cpp
USTRUCT(BlueprintType)
struct FGameEventData
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    EGameEventType EventType;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Source;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, FString> Data;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FDateTime Timestamp;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString EventID;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString PlayerID;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Priority;  // low, normal, high, critical
};
```

---

## SUBSCRIPTION SYSTEM

### Subscribe/Unsubscribe

```cpp
int32 SubscribeToEvent(EGameEventType EventType, UObject* Subscriber, FName FunctionName)
{
    if (!Subscriber) return -1;
    
    // Create subscription
    FSubscriptionInfo SubInfo;
    SubInfo.Subscriber = Subscriber;
    SubInfo.FunctionName = FunctionName;
    SubInfo.SubscriptionID = NextSubscriptionID++;
    
    // Add to subscriptions
    TArray<FSubscriptionInfo>* Subs = Subscriptions.Find(EventType);
    if (!Subs)
    {
        Subscriptions.Add(EventType, TArray<FSubscriptionInfo>());
        Subs = Subscriptions.Find(EventType);
    }
    Subs->Add(SubInfo);
    
    UE_LOG(LogTemp, Log, TEXT("[EventBus] Subscribed to %s (ID: %d)"), *UEnum::GetValueAsString(EventType), SubInfo.SubscriptionID);
    
    return SubInfo.SubscriptionID;
}

void UnsubscribeFromEvent(EGameEventType EventType, int32 SubscriptionID)
{
    TArray<FSubscriptionInfo>* Subs = Subscriptions.Find(EventType);
    if (!Subs) return;
    
    // Find and remove subscription
    for (int32 i = 0; i < Subs->Num(); i++)
    {
        if ((*Subs)[i].SubscriptionID == SubscriptionID)
        {
            Subs->RemoveAt(i);
            UE_LOG(LogTemp, Log, TEXT("[EventBus] Unsubscribed from %s (ID: %d)"), *UEnum::GetValueAsString(EventType), SubscriptionID);
            return;
        }
    }
}
```

### Delegate Broadcasting

```cpp
void PublishEvent(EGameEventType EventType, const FGameEventData& EventData)
{
    TArray<FSubscriptionInfo>* Subs = Subscriptions.Find(EventType);
    if (!Subs || Subs->Num() == 0)
    {
        UE_LOG(LogTemp, Log, TEXT("[EventBus] Published %s to 0 subscribers"), *UEnum::GetValueAsString(EventType));
        return;
    }
    
    // Broadcast to all subscribers
    for (const auto& Sub : *Subs)
    {
        if (Sub.Subscriber && IsValid(Sub.Subscriber))
        {
            // Call function via UObject reflection
            UFunction* Function = Sub.Subscriber->FindFunction(Sub.FunctionName);
            if (Function)
            {
                Sub.Subscriber->ProcessEvent(Function, &EventData);
            }
        }
    }
    
    UE_LOG(LogTemp, Log, TEXT("[EventBus] Published %s to %d subscribers"), *UEnum::GetValueAsString(EventType), Subs->Num());
}
```

---

## SYSTEM INTEGRATIONS

### TimeOfDayManager Integration

```cpp
// In TimeOfDayManager.cpp

void UTimeOfDayManager::UpdateTimeData(int32 Hour, int32 Minute, int32 Day, const FString& State)
{
    CachedHour = Hour;
    CachedMinute = Minute;
    CachedDay = Day;
    CachedState = State;
    
    // Publish event
    if (UGameEventBusSubsystem* EventBus = UGameEventBusSubsystem::Get(GetWorld()))
    {
        FGameEventData EventData;
        EventData.EventType = EGameEventType::TimeOfDayChanged;
        EventData.Source = TEXT("TimeOfDayManager");
        EventData.Data.Add(TEXT("Hour"), FString::FromInt(Hour));
        EventData.Data.Add(TEXT("Minute"), FString::FromInt(Minute));
        EventData.Data.Add(TEXT("Day"), FString::FromInt(Day));
        EventData.Data.Add(TEXT("State"), State);
        
        EventBus->PublishEvent(EGameEventType::TimeOfDayChanged, EventData);
    }
    
    // Broadcast delegates
    OnTimeChanged.Broadcast(Hour, Minute, Day, State);
}
```

### WeatherManager Integration

```cpp
// In WeatherManager.cpp

void UWeatherManager::SetWeather(EWeatherState NewWeather)
{
    if (NewWeather == CurrentWeather) return;
    
    EWeatherState OldWeather = CurrentWeather;
    CurrentWeather = NewWeather;
    
    // Publish event
    if (UGameEventBusSubsystem* EventBus = UGameEventBusSubsystem::Get(GetWorld()))
    {
        FGameEventData EventData;
        EventData.EventType = EGameEventType::WeatherChanged;
        EventData.Source = TEXT("WeatherManager");
        EventData.Data.Add(TEXT("OldWeather"), UEnum::GetValueAsString(OldWeather));
        EventData.Data.Add(TEXT("NewWeather"), UEnum::GetValueAsString(NewWeather));
        
        EventBus->PublishEvent(EGameEventType::WeatherChanged, EventData);
    }
    
    // Update materials
    ApplyWeatherMaterials();
}
```

### FloraManager Integration

```cpp
// In FloraManager.cpp

void AFLoraManager::SpawnFloraInChunk(UWorldPartitionCell* Cell)
{
    // ... spawn logic ...
    
    // Publish event
    if (UGameEventBusSubsystem* EventBus = UGameEventBusSubsystem::Get(GetWorld()))
    {
        FGameEventData EventData;
        EventData.EventType = EGameEventType::FloraSpawned;
        EventData.Source = TEXT("FloraManager");
        EventData.Data.Add(TEXT("CellName"), Cell->GetName());
        EventData.Data.Add(TEXT("Count"), FString::FromInt(SpawnedCount));
        
        EventBus->PublishEvent(EGameEventType::FloraSpawned, EventData);
    }
}
```

---

## BLUEPRINT API

### Designer Functions

```cpp
// Event bus access
UFUNCTION(BlueprintCallable, Category = "EventBus")
static UGameEventBusSubsystem* Get(const UObject* WorldContext);

// Subscribe
UFUNCTION(BlueprintCallable, Category = "EventBus")
int32 SubscribeToEvent(EGameEventType EventType, UObject* Subscriber, FName FunctionName);

// Unsubscribe
UFUNCTION(BlueprintCallable, Category = "EventBus")
void UnsubscribeFromEvent(EGameEventType EventType, int32 SubscriptionID);

// Publish
UFUNCTION(BlueprintCallable, Category = "EventBus")
void PublishEvent(EGameEventType EventType, const FGameEventData& EventData);
```

### Example Blueprint Usage

```cpp
// In some Blueprint actor
void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    
    // Subscribe to weather changes
    if (UGameEventBusSubsystem* EventBus = UGameEventBusSubsystem::Get(GetWorld()))
    {
        EventBus->SubscribeToEvent(
            EGameEventType::WeatherChanged,
            this,
            TEXT("OnWeatherChanged")
        );
    }
}

UFUNCTION()
void AMyActor::OnWeatherChanged(const FGameEventData& EventData)
{
    FString NewWeather = EventData.Data.FindRef(TEXT("NewWeather"));
    
    UE_LOG(LogTemp, Log, TEXT("[MyActor] Weather changed to: %s"), *NewWeather);
    
    // React to weather change
    HandleWeatherChange(NewWeather);
}
```

---

## PERFORMANCE BUDGET

### Event Bus Budget

**Target**: 0.1ms CPU per event broadcast

**Approach**:
- Direct function calls
- No async overhead
- Minimal allocation
- O(N) for N subscribers

---

## BACKEND INTEGRATION

### HTTP Sync (Optional)

```cpp
void PublishEventToBackend(EGameEventType EventType, const FGameEventData& EventData)
{
    // Optional: Mirror events to Python backend
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(TEXT("http://localhost:8003/api/events/publish"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    
    // Serialize event
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
    JsonObject->SetStringField("event_type", UEnum::GetValueAsString(EventType));
    // ... serialize all fields
    
    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
    
    Request->SetContentAsString(OutputString);
    Request->ProcessRequest();
}
```

---

## TESTING STRATEGY

### Unit Tests

```cpp
TEST(EventBus, PublishSubscribeWorks)
{
    UWorld* World = CreateTestWorld();
    UGameEventBusSubsystem* EventBus = World->GetSubsystem<UGameEventBusSubsystem>();
    
    // Subscribe
    int32 SubID = EventBus->SubscribeToEvent(
        EGameEventType::WeatherChanged,
        TestSubscriber,
        TEXT("HandleEvent")
    );
    
    EXPECT_GT(SubID, 0);
    
    // Publish
    FGameEventData EventData;
    EventData.EventType = EGameEventType::WeatherChanged;
    
    EventBus->PublishEvent(EGameEventType::WeatherChanged, EventData);
    
    EXPECT_EQ(EventReceived, true);
}
```

---

**Status**: ✅ **GAME EVENT BUS INTEGRATION ARCHITECTURE COMPLETE**



