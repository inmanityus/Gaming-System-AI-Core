# VA-002 Audio Integration - Blueprint API Guide
**Date**: 2025-11-02  
**Status**: Complete

---

## OVERVIEW

This guide provides Blueprint usage examples for all VA-002 Audio Integration features. All methods are exposed via `AudioManager` component.

---

## SETUP

### 1. Add AudioManager Component

**In Blueprint:**
1. Add Component → `Audio Manager`
2. Component is automatically initialized in BeginPlay
3. Bind to TimeOfDayManager events automatically

### 2. Initialize Backend URL (Optional)

```cpp
// In Blueprint BeginPlay or custom event
Audio Manager → Initialize
    Backend URL: "http://localhost:4000"
```

---

## TIME-OF-DAY AMBIENT API

### Get Current Time-of-Day Ambient

```cpp
// Get current ambient state
FString CurrentState = Audio Manager → Get Current Time Of Day Ambient
// Returns: "dawn", "day", "dusk", or "night"
```

### Set Time-of-Day Ambient Manually

```cpp
// Manually set time-of-day ambient
Audio Manager → Set Time Of Day Ambient
    Time State: "day"
```

**Note**: Usually handled automatically via TimeOfDayManager events.

---

## WEATHER AUDIO API

### Set Weather Audio Layer

```cpp
// Set weather audio based on weather state
Audio Manager → Set Weather Audio Layer
    Weather State: EWeatherState::RAIN
    Intensity: 0.7  // 0.0 to 1.0
```

**Weather States Available:**
- `CLEAR` - No weather audio
- `PARTLY_CLOUDY` - Light wind
- `CLOUDY` - Moderate wind
- `RAIN` - Rain + wind layers
- `HEAVY_RAIN` - Heavy rain + strong wind
- `STORM` - Rain + wind + thunder events
- `FOG` - Fog ambient
- `MIST` - Light mist
- `SNOW` - Snow + wind
- `HEAVY_SNOW` - Heavy snow + wind
- `BLIZZARD` - Blizzard + howling wind + thunder
- `WINDY` - Strong wind loop
- `EXTREME_HEAT` - Heat haze
- `EXTREME_COLD` - Cold wind

### Trigger Weather Transition

```cpp
// Smoothly transition between weather states
Audio Manager → Trigger Weather Transition
    Old State: EWeatherState::CLEAR
    New State: EWeatherState::RAIN
    Intensity: 0.5
    Transition Duration: 5.0  // seconds
```

### Play Thunder Strike

```cpp
// Play one-shot thunder event (for STORM/BLIZZARD)
Audio Manager → Play Thunder Strike
    Volume: 0.85  // 0.0 to 1.0 (will be randomized 0.7-1.0x)
```

### Get Current Weather State

```cpp
// Get current weather audio state
EWeatherState CurrentWeather = Audio Manager → Get Current Weather State
```

---

## ZONE-BASED AMBIENT API

### Set Zone Ambient Profile

```cpp
// Set zone-specific ambient profile
Audio Manager → Set Zone Ambient Profile
    Zone Profile Name: "Warehouse"
```

**Zone Profile Names** (examples):
- "Warehouse"
- "Morgue"
- "Apartment"
- "Street"
- "Park"

**Note**: MetaSound assets must exist: `MS_Zone_[ProfileName]`

### Update Combined Ambient Profile

```cpp
// Update both time-of-day and zone ambient
Audio Manager → Update Ambient Profile
    Time State: "night"
    Zone Profile Name: "Morgue"
```

### Get Current Zone Profile

```cpp
// Get current zone ambient profile
FString CurrentZone = Audio Manager → Get Current Zone Ambient Profile
```

---

## AUDIO DUCKING API

### Duck Audio by Amount

```cpp
// Apply ducking to specific audio category
Audio Manager → Duck Audio By Amount
    Category: EAudioCategory::Ambient
    Duck Amount: 0.6  // 0.0 to 1.0 (60% reduction)
    Duration: 2.0  // seconds (transition duration)
```

**Categories Available:**
- `Voice` - Never ducked (always 0.0)
- `Ambient` - Ducking applied automatically by weather
- `Music` - Ducking applied during weather events
- `Effect` - Manual ducking available
- `UI` - Manual ducking available

**Note**: Weather system automatically ducks ambient by `intensity * 0.6` and music by `0.2` during weather events.

---

## AUDIO OCCLUSION API

### Calculate Audio Occlusion

```cpp
// Calculate occlusion between source and listener
float OcclusionAmount = Audio Manager → Calculate Audio Occlusion
    Source Location: (Vector) SourcePosition
    Listener Location: (Vector) ListenerPosition
// Returns: 0.0 (no occlusion) to 1.0 (fully occluded)
```

**Usage Example:**
```cpp
// In NPC dialogue or ambient audio
FVector NPC_Position = NPC_Reference → Get Actor Location
FVector Player_Position = Player_Pawn → Get Actor Location
float Occlusion = Audio Manager → Calculate Audio Occlusion(NPC_Position, Player_Position)

// Apply occlusion to audio volume
float FinalVolume = 1.0 - Occlusion
Audio_Component → Set Volume Multiplier(FinalVolume)
```

---

## REVERB/CONTEXT SWITCHING API

### Set Reverb Preset

```cpp
// Set reverb preset based on zone context
Audio Manager → Set Reverb Preset
    Preset Name: "Small Room"  // or "Large Room", "Morgue", etc.
    Transition Duration: 3.0  // seconds
```

**Reverb Preset Names** (examples):
- "Small Room"
- "Large Room"
- "Hall Reverb"
- "Cold Tile Room"
- "Large Echo Chamber"
- "City Reverberation"
- "Open Space"

**Note**: Reverb presets require UE5 submix setup and preset assets.

---

## COMPLETE USAGE EXAMPLE

### Full Audio System Setup

```cpp
// In GameMode or Level Blueprint BeginPlay

// 1. Initialize Audio Manager
Audio Manager → Initialize("http://localhost:4000")

// 2. Time-of-day ambient is automatic (binds to TimeOfDayManager)
// No setup needed - works automatically

// 3. Set initial weather
Audio Manager → Set Weather Audio Layer
    Weather State: EWeatherState::CLEAR
    Intensity: 0.0

// 4. Set initial zone (when player enters level)
Audio Manager → Set Zone Ambient Profile
    Zone Profile Name: "Street"

// 5. Listen for weather changes (from WeatherManager service)
Event On Weather Changed
    Weather State: EWeatherState
    Intensity: float
    Then:
        Audio Manager → Trigger Weather Transition
            Old State: PreviousWeatherState
            New State: Weather State
            Intensity: Intensity
            Transition Duration: 5.0

// 6. Zone transitions (via overlap volumes)
Event On Zone Enter
    Zone Name: FString
    Then:
        Audio Manager → Set Zone Ambient Profile
            Zone Profile Name: Zone Name
        
        // Set appropriate reverb preset
        if Zone Name == "Interior"
            Audio Manager → Set Reverb Preset("Small Room")
        else if Zone Name == "Exterior"
            Audio Manager → Set Reverb Preset("City Reverberation")
```

---

## EVENT INTEGRATION

### Time-of-Day Events

**Automatic**: AudioManager binds to `TimeOfDayManager.OnTimeStateChanged` automatically.

**Manual Binding** (if needed):
```cpp
// Get TimeOfDayManager
UTimeOfDayManager TimeManager = Game Instance → Get Subsystem(UTimeOfDayManager)

// Bind to event
TimeManager → On Time State Changed
    Add Custom Event → On Time State Changed
        Old State: FString
        New State: FString
        Then:
            Audio Manager → Set Time Of Day Ambient(New State)
```

### Weather Events

**From WeatherManager Service**:
```cpp
// HTTP request to WeatherManager
GET /weather/current
Response: { "state": "RAIN", "intensity": 0.7 }

// Update audio
Audio Manager → Set Weather Audio Layer
    Weather State: Convert String To Weather State(Response.state)
    Intensity: Response.intensity
```

---

## PERFORMANCE NOTES

### CPU Budget
- Time-of-day ambient: ~0.3ms per frame
- Weather layers: ~0.4ms per frame
- Occlusion checks: ~0.1ms per frame
- **Total**: ~0.8ms per frame

### Memory Budget
- Ambient profiles: ~30MB
- Weather audio: ~20MB
- Zone profiles: ~15MB
- Reverb presets: ~5MB
- **Total**: ~70MB

### Best Practices
1. **Don't call occlusion checks every frame** - Use distance-based throttling
2. **Reuse audio components** - System handles this automatically
3. **Limit weather transitions** - Use minimum 5-second transitions
4. **Cache MetaSound templates** - System caches automatically

---

## TROUBLESHOOTING

### No Audio Playing
1. Check MetaSound assets exist in `/Game/Audio/MetaSounds/`
2. Verify asset names match expected format (MS_DawnAmbient, etc.)
3. Check AudioManager logs in Output Log
4. Verify TimeOfDayManager is initialized

### Transitions Not Smooth
1. Verify transition durations are set correctly
2. Check audio component volume multipliers
3. Ensure MetaSound assets support looping
4. Check for audio popping in asset settings

### Weather Audio Not Working
1. Verify WeatherManager service is running
2. Check weather state enum values match
3. Verify intensity values are 0.0-1.0
4. Check logs for MetaSound loading errors

### Zone Audio Not Switching
1. Verify zone profile names match MetaSound asset names
2. Check overlap volumes are set up correctly
3. Verify SetZoneAmbientProfile is called on zone enter
4. Check logs for asset loading errors

---

**Document Status**: ✅ Complete - Ready for UE5 Blueprint Integration

