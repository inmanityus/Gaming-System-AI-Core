# WeatherManager C++ Architecture Design
**Date**: 2025-01-29  
**Task**: WS-001-A - WeatherManager Core & State Machine  
**Status**: Design Complete

---

## OVERVIEW

This document defines the architecture for implementing WeatherManager as a UE5 C++ Game Instance Subsystem, mirroring TimeOfDayManager and integrating with the existing Python backend service.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **WeatherManager Python Service** (`services/weather_manager/weather_manager.py`)
   - 15 weather states (clear, rain, storm, snow, fog, etc.)
   - Intensity values (0.0-1.0)
   - Temperature, wind speed, humidity tracking
   - Event bus integration
   - Season management

2. **TimeOfDayManager** (`unreal/Source/BodyBroker/TimeOfDayManager.h`)
   - Pattern to follow for C++ implementation
   - Backend HTTP integration
   - Event broadcasting
   - Game Instance Subsystem

3. **AudioManager** (`unreal/Source/BodyBroker/AudioManager.h`)
   - Integration point for weather audio
   - Category-based volume management

---

## C++ CLASS DESIGN

### WeatherManager Header

```cpp
// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Http.h"
#include "Engine/Engine.h"
#include "WeatherManager.generated.h"

/**
 * Weather state enum matching Python service
 */
UENUM(BlueprintType)
enum class EWeatherState : uint8
{
    Clear       UMETA(DisplayName = "Clear"),
    PartlyCloudy UMETA(DisplayName = "Partly Cloudy"),
    Cloudy      UMETA(DisplayName = "Cloudy"),
    Rain        UMETA(DisplayName = "Rain"),
    HeavyRain   UMETA(DisplayName = "Heavy Rain"),
    Storm       UMETA(DisplayName = "Storm"),
    Fog         UMETA(DisplayName = "Fog"),
    Mist        UMETA(DisplayName = "Mist"),
    Snow        UMETA(DisplayName = "Snow"),
    HeavySnow   UMETA(DisplayName = "Heavy Snow"),
    Blizzard    UMETA(DisplayName = "Blizzard"),
    Windy       UMETA(DisplayName = "Windy"),
    ExtremeHeat UMETA(DisplayName = "Extreme Heat"),
    ExtremeCold UMETA(DisplayName = "Extreme Cold")
};

/**
 * Season enum matching Python service
 */
UENUM(BlueprintType)
enum class ESeason : uint8
{
    Spring      UMETA(DisplayName = "Spring"),
    Summer      UMETA(DisplayName = "Summer"),
    Fall        UMETA(DisplayName = "Fall"),
    Winter      UMETA(DisplayName = "Winter")
};

/**
 * WeatherData struct - Cached weather information
 */
USTRUCT(BlueprintType)
struct FWeatherData
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly)
    EWeatherState State;
    
    UPROPERTY(BlueprintReadOnly)
    float Intensity;  // 0.0 - 1.0
    
    UPROPERTY(BlueprintReadOnly)
    float Temperature;  // Celsius
    
    UPROPERTY(BlueprintReadOnly)
    float WindSpeed;  // km/h
    
    UPROPERTY(BlueprintReadOnly)
    float Humidity;  // 0.0 - 1.0
    
    UPROPERTY(BlueprintReadOnly)
    ESeason Season;
    
    UPROPERTY(BlueprintReadOnly)
    int32 DurationMinutes;
    
    FWeatherData()
        : State(EWeatherState::Clear)
        , Intensity(0.0f)
        , Temperature(20.0f)
        , WindSpeed(0.0f)
        , Humidity(0.5f)
        , Season(ESeason::Spring)
        , DurationMinutes(0)
    {}
};

/**
 * WeatherManager - UE5 C++ Game Instance Subsystem
 * Manages weather state and communicates with backend Python service
 * REAL IMPLEMENTATION - No mocks, uses actual HTTP calls
 */
UCLASS()
class BODYBROKER_API UWeatherManager : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    // USubsystem interface
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    /**
     * Get the singleton instance of WeatherManager
     */
    UFUNCTION(BlueprintCallable, Category = "Weather")
    static UWeatherManager* Get(const UObject* WorldContext);

    /**
     * Get current weather data
     */
    UFUNCTION(BlueprintCallable, Category = "Weather")
    void GetCurrentWeather(FWeatherData& OutWeatherData);

    /**
     * Set weather state manually (for testing)
     */
    UFUNCTION(BlueprintCallable, Category = "Weather")
    void SetWeatherState(EWeatherState NewState, float Intensity = 0.5f);

    /**
     * Start weather progression from backend
     */
    UFUNCTION(BlueprintCallable, Category = "Weather")
    void StartWeatherProgression();

    /**
     * Stop weather progression
     */
    UFUNCTION(BlueprintCallable, Category = "Weather")
    void StopWeatherProgression();

    /**
     * Set season
     */
    UFUNCTION(BlueprintCallable, Category = "Weather")
    void SetSeason(ESeason NewSeason);

    /**
     * Event broadcasted when weather changes
     */
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWeatherChanged, EWeatherState, OldState, EWeatherState, NewState);
    UPROPERTY(BlueprintAssignable, Category = "Weather")
    FOnWeatherChanged OnWeatherChanged;

    /**
     * Event broadcasted when weather intensity changes
     */
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnWeatherIntensityChanged, EWeatherState, State, float, OldIntensity, float, NewIntensity);
    UPROPERTY(BlueprintAssignable, Category = "Weather")
    FOnWeatherIntensityChanged OnWeatherIntensityChanged;

    /**
     * Event broadcasted when season changes
     */
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnSeasonChanged, ESeason, OldSeason, ESeason, NewSeason);
    UPROPERTY(BlueprintAssignable, Category = "Weather")
    FOnSeasonChanged OnSeasonChanged;

private:
    // Backend API URL
    UPROPERTY()
    FString BackendAPIUrl;

    // Current cached weather data
    UPROPERTY()
    FWeatherData CachedWeatherData;

    // Update interval (seconds)
    UPROPERTY()
    float UpdateInterval;

    // Timer handle for periodic updates
    FTimerHandle UpdateTimerHandle;

    // Is weather progression active
    UPROPERTY()
    bool bIsWeatherProgressionActive;

    /**
     * Fetch current weather from backend API
     */
    void FetchCurrentWeather();

    /**
     * Handle HTTP response from weather API
     */
    void OnWeatherResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

    /**
     * Update cached weather data
     */
    void UpdateWeatherData(const FWeatherData& NewWeatherData);

    /**
     * Periodic update callback
     */
    void OnPeriodicUpdate();
};
```

---

## STATE TRANSITION SYSTEM

### Transition Logic

**Transition Rules**:
```
Allowed Transitions:
  Clear ↔ PartlyCloudy ↔ Cloudy
  Cloudy → Rain → HeavyRain → Storm
  Clear → Snow → HeavySnow → Blizzard
  Any → Fog / Mist (can overlay)
  Any → Windy (can overlay)
  Season-based: Temperature extremes
```

**Transition Interpolation**:
- Duration: 5 seconds (weather changes)
- Intensity interpolation: Linear over transition time
- Parameter smoothing: All values interpolate simultaneously

### Transition Priority

**Immediate Transitions** (No interpolation):
- Storm starts/stops
- Blizzard starts/stops
- Extreme weather

**Smooth Transitions** (5-second interpolation):
- Clear ↔ Cloudy
- Cloudy → Rain
- Rain → Heavy Rain
- Snow → Heavy Snow
- Temperature changes

---

## BACKEND API INTEGRATION

### HTTP Endpoints

**Current Weather**:
```
GET http://localhost:8007/api/weather/current
    Response: {
        "state": "rain",
        "intensity": 0.7,
        "temperature": 15.0,
        "wind_speed": 25.0,
        "humidity": 0.85,
        "season": "fall",
        "duration_minutes": 45
    }
```

**Set Weather**:
```
POST http://localhost:8007/api/weather/set
    Request: {
        "state": "storm",
        "intensity": 1.0
    }
    Response: Updated weather data
```

**Start Progression**:
```
POST http://localhost:8007/api/weather/start
    Response: { "status": "started" }
```

**Stop Progression**:
```
POST http://localhost:8007/api/weather/stop
    Response: { "status": "stopped" }
```

**Set Season**:
```
POST http://localhost:8007/api/weather/season
    Request: { "season": "winter" }
    Response: { "status": "updated" }
```

### HTTP Response Handling

**Parse JSON**:
```cpp
TSharedPtr<FJsonObject> WeatherObject = JsonObject->GetObjectField(TEXT("weather"));

FWeatherData ParsedData;
ParsedData.State = ParseWeatherState(WeatherObject->GetStringField(TEXT("state")));
ParsedData.Intensity = WeatherObject->GetNumberField(TEXT("intensity"));
ParsedData.Temperature = WeatherObject->GetNumberField(TEXT("temperature"));
ParsedData.WindSpeed = WeatherObject->GetNumberField(TEXT("wind_speed"));
ParsedData.Humidity = WeatherObject->GetNumberField(TEXT("humidity"));
ParsedData.Season = ParseSeason(WeatherObject->GetStringField(TEXT("season")));
ParsedData.DurationMinutes = WeatherObject->GetIntegerField(TEXT("duration_minutes"));

UpdateWeatherData(ParsedData);
```

---

## EVENT BROADCASTING

### Event Types

**OnWeatherChanged**:
- Fires when weather state changes
- OldState and NewState parameters
- Subscribers: Audio, particles, materials, UI

**OnWeatherIntensityChanged**:
- Fires when intensity changes within same state
- State, OldIntensity, NewIntensity parameters
- Subscribers: Audio (ducking), particles (spawn rate)

**OnSeasonChanged**:
- Fires when season changes
- OldSeason and NewSeason parameters
- Subscribers: All systems (weather probabilities change)

### Subscriber Examples

**AudioSystem**:
```cpp
WeatherManager->OnWeatherChanged.AddDynamic(this, &UAudioManager::HandleWeatherChange);
```

**ParticleSystem**:
```cpp
WeatherManager->OnWeatherChanged.AddDynamic(this, &UNiagaraComponent::HandleWeatherChange);
```

**MaterialSystem**:
```cpp
WeatherManager->OnWeatherChanged.AddDynamic(this, &UMaterialParameterCollection::HandleWeatherChange);
```

---

## IMPLEMENTATION STRUCTURE

### C++ Implementation Pattern

**Mirror TimeOfDayManager**:
- Same subsystem initialization pattern
- Same HTTP request/response handling
- Same periodic update logic
- Same event broadcasting approach

**Differences**:
- More complex state machine (15 states vs 4)
- Transition interpolation logic
- Backend API endpoints differ

---

**Status**: ✅ **C++ ARCHITECTURE COMPLETE**



