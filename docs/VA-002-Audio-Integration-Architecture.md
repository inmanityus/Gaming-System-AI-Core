# VA-002: Ambient & Weather Audio Integration Architecture
**Date**: 2025-01-29  
**Task**: VA-002 - Ambient & Weather Audio Integration  
**Status**: Architecture Design - Ready for Implementation

---

## OVERVIEW

This document defines the architecture for integrating ambient and weather audio systems with the existing AudioManager, TimeOfDayManager, and WeatherManager services.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **AudioManager** (`unreal/Source/BodyBroker/AudioManager.h`)
   - C++ component with category-based volume management
   - HTTP integration with backend audio API
   - Blueprint-exposed functions
   - **Categories**: Voice, Ambient, Music, Effect, UI

2. **TimeOfDayManager** (`unreal/Source/BodyBroker/TimeOfDayManager.h`)
   - Game Instance Subsystem
   - Broadcasts `OnTimeChanged` and `OnTimeStateChanged` events
   - State values: "dawn", "day", "dusk", "night"
   - Continuous time progression system

3. **WeatherManager** (`services/weather_manager/weather_manager.py`)
   - 15 weather states (clear, rain, storm, snow, fog, etc.)
   - Intensity values (0.0 - 1.0)
   - Wind speed and humidity tracking
   - Event bus integration for state changes

---

## ARCHITECTURE DESIGN

### 1. Time-of-Day Ambient MetaSound System

#### MetaSound Profiles

**4 Ambient Profiles** corresponding to time states:

| Time State | Profile Name | Characteristics |
|------------|--------------|----------------|
| dawn | `MS_DawnAmbient` | Birds chirping, morning wind, distant city sounds |
| day | `MS_DayAmbient` | Traffic, crowds, construction, urban life |
| dusk | `MS_DuskAmbient` | Wind picks up, distant sirens, evening atmosphere |
| night | `MS_NightAmbient` | Quiet, occasional wind, distant sounds, eerie silence |

#### MetaSound Design

**Per-Profile Components**:
- **Base Ambient Layer**: Static looping sound field
- **Dynamic Elements**: Sporadic sounds with random intervals
- **Distance Attenuation**: Volume varies with player position
- **Spatial Audio**: 3D positioned sounds

**Transition Logic**:
- 30-second crossfade between profiles
- Smooth parameter interpolation
- No audio popping or sudden jumps
- Automatic profile switching on `TimeStateChanged` event

#### Integration Points

```
TimeOfDayManager.OnTimeStateChanged
    ↓
AmbientAudioController.ReceiveTimeStateChange(OldState, NewState)
    ↓
MetaSoundPlayer.TransitionToProfile(NewState)
    ↓
AudioManager.SetAmbientAudio(NewProfileID)
```

### 2. Weather Audio Layering System

#### Weather Audio Layers

**Layering Strategy**: Weather audio is additive over base ambient

```
Master Audio Output
    ├── Base Ambient (from time-of-day)
    ├── Weather Layer 1: Primary (rain, wind, thunder)
    ├── Weather Layer 2: Secondary (fog muffling, distant sounds)
    └── Weather Layer 3: Tertiary (environmental response)
```

#### Weather-to-Audio Mapping

| Weather State | Audio Layer 1 | Audio Layer 2 | Intensity Control |
|---------------|---------------|---------------|-------------------|
| CLEAR | None | None | N/A |
| PARTLY_CLOUDY | Light wind | None | Low |
| CLOUDY | Moderate wind | None | Medium |
| RAIN | Rain loop | Wind | intensity value |
| HEAVY_RAIN | Heavy rain | Strong wind | intensity value |
| STORM | Rain + Wind | Thunder (event-based) | intensity value |
| FOG | Ambient muffling | None | intensity value |
| MIST | Light ambient muffling | None | Low |
| SNOW | Snow loop | Wind | intensity value |
| HEAVY_SNOW | Heavy snow | Strong wind | intensity value |
| BLIZZARD | Blizzard loop | Howling wind + Thunder | intensity value |
| WINDY | Strong wind loop | None | wind_speed / 100 |
| EXTREME_HEAT | Distant heat haze | None | Low |
| EXTREME_COLD | Cold wind | None | Low |

#### Ducking & Mixing Rules

**Priority System**:
1. **Voice**: Never ducked (100% dry)
2. **Music**: Duck by 20% during weather events
3. **Ambient**: Duck by weather intensity (0-60%)
4. **Weather**: Full volume based on intensity
5. **Effects**: Unaffected

**Ducking Behavior**:
- Weather events duck ambient by `weather.intensity * 0.6`
- Music ducks by 20% on weather start
- Ducking transitions smoothly over 2 seconds
- No audio popping during transitions

#### Thunder Event System

**Thunder Implementation**:
- Event-based audio (not looping)
- Spawned randomly during STORM/BLIZZARD
- Interval: 10-30 seconds between strikes
- Volume: 0.7-1.0 (randomized)
- Low-pass filter for distant thunder
- 3D spatial audio (thunder can come from different directions)

### 3. Zone-Based Ambient Triggers

#### Zone Types

**Architecture Zones**:
- **Exterior**: Streets, parks, open areas
- **Interior**: Buildings, rooms, enclosed spaces
- **Semi-Exterior**: Covered areas, tunnels, transition zones

**Audio Profiles per Zone**:
- Each zone has ambient profile (e.g., "Warehouse", "Morgue", "Apartment")
- Exterior zones use time-of-day + weather audio
- Interior zones use only time-of-day (weather is muffled)
- Semi-exterior blends both systems

#### Zone Transition System

**Trigger Mechanism**:
- Overlap volumes define zones
- On overlap: Load zone's ambient profile
- Crossfade duration: 5 seconds for smooth transitions

**Distance-Based Volume**:
- Ambient volume = `1.0 - (distance_to_trigger / max_distance)`
- Max distance: 500 units
- Fade curve: Linear

#### Integration with Weather

```
Zone Type "Exterior"
    ↓
TimeOfDayManager → Base Ambient
    +
WeatherManager → Weather Layers
    =
Full Audio Profile

Zone Type "Interior"
    ↓
TimeOfDayManager → Base Ambient (muffled by 40%)
    +
WeatherManager → None (completely blocked)
    =
Indoor Audio Profile
```

### 4. Audio Occlusion System

#### Occlusion by Zone Type

**Exterior → Interior**:
- Ambient ducks by 60%
- Weather audio completely blocked
- Reverb changes to "Small Room" preset
- Low-pass filter applied (cutoff ~3000 Hz)

**Interior → Exterior**:
- Ambient volume increases by 40%
- Weather audio fades in over 5 seconds
- Reverb changes to "Large Open Space" preset
- Low-pass filter removed

#### Occlusion Physics

**Raycast-Based Occlusion**:
- Line traces from sound source to player
- Each wall hit increases occlusion
- Final occlusion = `min(1.0, hit_count * 0.15)`
- Maximum occlusion: 100% (completely blocked)

### 5. Reverb/Context Switching

#### Reverb Presets

**Context-Based Reverb**:

| Context | Reverb Preset | Settings |
|---------|---------------|----------|
| Exterior - Day | City Reverberation | Room size: 100%, Wet: 30%, Delay: 0.1s |
| Exterior - Night | Open Space | Room size: 80%, Wet: 20%, Delay: 0.2s |
| Interior - Small Room | Small Room | Room size: 20%, Wet: 50%, Delay: 0.05s |
| Interior - Large Room | Hall Reverb | Room size: 60%, Wet: 40%, Delay: 0.15s |
| Interior - Morgue | Cold Tile Room | Room size: 40%, Wet: 60%, Delay: 0.1s |
| Interior - Warehouse | Large Echo Chamber | Room size: 120%, Wet: 30%, Delay: 0.3s |

**Dynamic Reverb Switching**:
- Reverb preset changes on zone transition
- Transition duration: 3 seconds
- Reverb send level interpolated smoothly
- Submix-based (affects ambient category only)

---

## IMPLEMENTATION DETAILS

### AudioManager Extensions

**New Methods Required**:

```cpp
// Time-of-day ambient management
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void SetTimeOfDayAmbient(const FString& TimeState);

// Weather audio layer management
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void SetWeatherAudioLayer(EWeatherState WeatherState, float Intensity);

// Zone-based ambient
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void SetZoneAmbientProfile(const FString& ZoneProfileName);

// Audio ducking
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void DuckAudioByAmount(EAudioCategory Category, float DuckAmount, float Duration);
```

### MetaSound Integration

**MetaSound Templates**:
- Templates created in UE5 Editor
- Parameters exposed for intensity control
- Dynamic element spawning via MetaSounds
- Event-driven audio support

**Blueprint API**:
- `TriggerWeatherTransition` - Smoothly transition weather audio
- `PlayThunderStrike` - Spawn thunder event
- `UpdateAmbientProfile` - Change ambient based on time/zone

### Backend API Integration

**Audio Service Endpoints**:

```
GET /api/audio/profile/time/{state}
    Returns: Audio profile metadata for time state

GET /api/audio/profile/weather/{state}
    Returns: Weather audio layer metadata

GET /api/audio/occlusion/check
    Request: { "source_pos": [x,y,z], "listener_pos": [x,y,z] }
    Returns: { "occlusion_amount": 0.0-1.0, "hit_count": 0 }

POST /api/audio/event
    Request: { "event_type": "weather_change", "data": {...} }
    Returns: Audio event response
```

### Performance Budget

**Target Performance**:
- Ambient audio: ~0.3ms CPU per frame
- Weather layers: ~0.4ms CPU per frame
- Occlusion checks: ~0.1ms CPU per frame
- **Total**: ~0.8ms CPU per frame

**Memory Budget**:
- Ambient profiles: ~30MB total
- Weather audio: ~20MB total
- Zone profiles: ~15MB total
- Reverb presets: ~5MB total
- **Total**: ~70MB audio memory

### Testing Strategy

**Unit Tests**:
- Time state transition audio switching
- Weather layer priority and ducking
- Zone transition smoothness
- Occlusion calculation accuracy

**Integration Tests**:
- Full audio pipeline (time + weather + zone)
- Backend API response handling
- Memory allocation/deallocation
- Performance profiling

---

## DEPENDENCIES

### Required Systems
- ✅ AudioManager (VA-001) - Complete
- ✅ TimeOfDayManager - Complete
- ⏳ WeatherManager - In progress
- ⏳ Zone System - Needs implementation

### MetaSound Assets
- ⏳ 4 Time-of-day ambient MetaSounds
- ⏳ 15 Weather layer MetaSounds
- ⏳ 10 Zone ambient MetaSounds
- ⏳ Thunder event audio

---

## NEXT STEPS

1. **Phase 1**: Create time-of-day ambient MetaSounds (Task VA-002-B)
2. **Phase 2**: Design weather audio layering implementation (Task VA-002-C)
3. **Phase 3**: Implement zone-based triggers (Task VA-002-D)
4. **Phase 4**: Add occlusion and reverb systems
5. **Phase 5**: Performance optimization and polish

---

**Status**: ✅ **ARCHITECTURE COMPLETE - READY FOR IMPLEMENTATION**



