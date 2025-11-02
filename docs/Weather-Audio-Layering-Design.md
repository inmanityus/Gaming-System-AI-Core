# Weather Audio Layering System Design
**Date**: 2025-01-29  
**Task**: VA-002-C - Weather Audio Layering Architecture  
**Status**: Design Complete

---

## OVERVIEW

This document defines the weather audio layering system that adds dynamic weather sounds over the base ambient audio, creating immersive weather conditions that respond to WeatherManager state changes.

---

## LAYERING ARCHITECTURE

### Audio Mix Stack

```
Master Audio Output
    ├── Base Ambient (from Time-of-Day)
    ├── Weather Layer 1: Primary Weather Sounds
    ├── Weather Layer 2: Secondary Weather Effects
    ├── Weather Layer 3: Environmental Response
    └── Ducking System (dynamic volume control)
```

### Layer Priority System

**Priority Order**:
1. **Voice**: Never ducked (100% dry, always audible)
2. **Music**: Duck by 20% during active weather
3. **Ambient**: Duck by weather intensity (0-60%)
4. **Weather**: Full volume based on intensity
5. **Effects**: Unaffected

---

## WEATHER-TO-AUDIO MAPPING

### Complete Weather State Mapping

| Weather State | Layer 1 | Layer 2 | Layer 3 | Intensity Multiplier |
|---------------|---------|---------|---------|---------------------|
| **CLEAR** | None | None | None | N/A |
| **PARTLY_CLOUDY** | Light Wind | None | None | 0.3 |
| **CLOUDY** | Moderate Wind | Sky Ambience | None | 0.5 |
| **RAIN** | Rain Loop | Wind Gusts | Impact Sounds | intensity |
| **HEAVY_RAIN** | Heavy Rain Loop | Strong Wind | Intense Impacts | intensity |
| **STORM** | Rain + Wind | Thunder (event) | Lightning Crack | intensity |
| **FOG** | Ambient Muffling | Wind (muffled) | Visibility Loss | intensity |
| **MIST** | Light Muffling | Subtle Wind | None | 0.2 |
| **SNOW** | Snow Loop | Wind (cold) | Footstep Variation | intensity |
| **HEAVY_SNOW** | Heavy Snow Loop | Strong Wind | Drift Sounds | intensity |
| **BLIZZARD** | Blizzard Loop | Howling Wind | Thunder | intensity |
| **WINDY** | Wind Loop (strong) | Debris Sounds | None | wind_speed / 100 |
| **EXTREME_HEAT** | Heat Haze | Air Distortion | Distant Echo | 0.3 |
| **EXTREME_COLD** | Cold Wind | Ice Cracking | Breath Sounds | 0.4 |

---

## DETAILED WEATHER PROFILES

### 1. RAIN (Light Rain)

**Audio Components**:
```
Layer 1 - Rain Loop
    - Continuous rain drops
    - Volume: 0.4 * intensity
    - Frequency: High (500-8000 Hz)
    - Spatial: Omni-directional
    - Variation: 5-10% random pitch shift

Layer 2 - Wind Gusts
    - Sporadic wind bursts
    - Volume: 0.2 * intensity
    - Frequency: 30-500 Hz
    - Sparse (3-5 gusts/minute)
    - Low-pass filter: 2000 Hz

Layer 3 - Impact Sounds
    - Rain hitting surfaces
    - Volume: 0.3 * intensity
    - Sparse (1-3 impacts/second)
    - 3D positioned (roofs, ground)
    - Reverb: Wet surface reflection
```

**MetaSound Template**: `MS_Rain_Light`
**Integration**: WeatherManager.RAIN state → intensity 0.3-0.6

---

### 2. HEAVY_RAIN

**Audio Components**:
```
Layer 1 - Heavy Rain Loop
    - Dense, louder rain
    - Volume: 0.6 * intensity
    - Frequency: Full spectrum (20-8000 Hz)
    - Continuous with saturation
    - Low-pass filter: 12000 Hz (high-end boost)

Layer 2 - Strong Wind
    - Continuous wind with gusts
    - Volume: 0.4 * intensity
    - Frequency: 20-800 Hz
    - Gust events every 5-8 seconds
    - Modulation: 0.5 Hz base

Layer 3 - Intense Impacts
    - Heavy surface impacts
    - Volume: 0.5 * intensity
    - Frequent (5-10 impacts/second)
    - Reverb: Wet, reflective
    - Distance attenuation
```

**MetaSound Template**: `MS_Rain_Heavy`
**Integration**: WeatherManager.HEAVY_RAIN state → intensity 0.7-0.9

**Ducking Behavior**:
- Ambient ducks by 50%
- Music ducks by 20%
- Voice unaffected

---

### 3. STORM

**Audio Components**:
```
Layer 1 - Storm Rain + Wind
    - Combined rain/wind loop
    - Volume: 0.7 * intensity
    - Frequency: Full spectrum
    - Turbulent, chaotic mix
    - Dynamic compression

Layer 2 - Thunder Events
    - Event-based, not looping
    - Spawn interval: 10-30 seconds
    - Volume: 0.7-1.0 (randomized)
    - Duration: 2-5 seconds (varies)
    - 3D positioning (distant to near)
    - Low-pass filter based on distance
    - Lightning crack overlay
    - Reverb: Large open space

Layer 3 - Lightning Crack
    - Tightly synced with thunder
    - Volume: 0.8
    - Sharp, high-frequency burst
    - Duration: 0.1-0.3 seconds
    - Stereo panning for direction
```

**MetaSound Template**: `MS_Storm`
**Integration**: WeatherManager.STORM state → intensity 0.8-1.0

**Thunder Implementation**:
```cpp
UFUNCTION(BlueprintCallable, Category = "Weather Audio")
void SpawnThunderStrike(FVector StrikeLocation, float Volume);
```

**Thunder Variants**:
- Distant rumble (1500+ units away)
- Medium strike (500-1500 units)
- Close strike (< 500 units)
- Volume scales with distance

**Timing Logic**:
- Base interval: 15 seconds
- Variance: ±10 seconds
- Intensity affects frequency:
  - Low intensity (0.5): 20-40 sec between strikes
  - High intensity (1.0): 5-15 sec between strikes

---

### 4. FOG

**Audio Components**:
```
Layer 1 - Ambient Muffling
    - Low-pass filter on all other audio
    - Cutoff frequency: 2000-4000 Hz (based on intensity)
    - Volume: 0.8 (reduces other sounds)
    - Continuous effect

Layer 2 - Muffled Wind
    - Dampened wind sounds
    - Volume: 0.3 * intensity
    - Frequency: 50-500 Hz
    - Low-pass: 2000 Hz
    - Reverb: Dampened, close

Layer 3 - Visibility Loss Audio
    - Subjective audio cue
    - Low-frequency drone
    - Volume: 0.15
    - Creates unease
    - Continuous
```

**MetaSound Template**: `MS_Fog`
**Integration**: WeatherManager.FOG state → intensity 0.5-0.9

**Muffling Effect**:
- Applies to ALL audio (ambient, music, effects)
- Only voice is unaffected
- Real-time DSP filter
- Smoothly transitions in/out over 5 seconds

---

### 5. SNOW

**Audio Components**:
```
Layer 1 - Snow Loop
    - Light snow falling
    - Volume: 0.4 * intensity
    - Frequency: High (2000-8000 Hz)
    - Spatial: 360° positioning
    - Continuous with variation
    - Wind modulation

Layer 2 - Cold Wind
    - Biting cold wind
    - Volume: 0.3 * intensity
    - Frequency: 100-1000 Hz
    - Sporadic gusts
    - Reverb: Open, cold space
    - Low-pass: 4000 Hz

Layer 3 - Footstep Variation
    - Snow crunch on footsteps
    - Volume: 0.2 (when walking)
    - Syncs with player movement
    - Triggered by footstep events
    - Not continuous
```

**MetaSound Template**: `MS_Snow_Light`
**Integration**: WeatherManager.SNOW state → intensity 0.4-0.6

---

### 6. BLIZZARD

**Audio Components**:
```
Layer 1 - Blizzard Loop
    - Intense wind + snow mix
    - Volume: 0.8 * intensity
    - Frequency: Full spectrum
    - Turbulent, harsh
    - Continuous compression

Layer 2 - Howling Wind
    - Extreme wind sounds
    - Volume: 0.7 * intensity
    - Frequency: 30-800 Hz
    - Howling events
    - Reverb: Large echo chamber
    - Oscillation: 1-2 Hz

Layer 3 - Thunder (rare)
    - Thunder strikes in snow
    - Volume: 0.6
    - Spawn: 1-2 per hour
    - Distant, muffled
    - Low-pass: 2000 Hz
```

**MetaSound Template**: `MS_Blizzard`
**Integration**: WeatherManager.BLIZZARD state → intensity 0.9-1.0

**Ducking Behavior**:
- Ambient ducks by 60%
- Music ducks by 30%
- Player voice unaffected
- Other NPCs muffled by 20%

---

### 7. WINDY

**Audio Components**:
```
Layer 1 - Wind Loop
    - Continuous wind
    - Volume: wind_speed / 100 (capped at 0.8)
    - Frequency: 50-1000 Hz
    - Dynamic based on wind_speed
    - Modulation: wind_speed / 50 Hz

Layer 2 - Debris Sounds
    - Objects being blown
    - Volume: 0.3
    - Sparse (5-10 events/minute)
    - 3D positioned
    - Reverb: Open space
    - Frequency: 200-2000 Hz
```

**MetaSound Template**: `MS_Wind_Strong`
**Integration**: WeatherManager.WINDY state → uses wind_speed parameter

**Dynamic Wind**:
- Wind volume directly tied to wind_speed
- Minimum: 0.3 (light wind)
- Maximum: 0.8 (extreme wind)
- Real-time modulation updates

---

## AUDIO DUCKING SYSTEM

### Ducking Rules

**Weather Intensity-Based Ducking**:
```
Ambient Duck Amount = weather.intensity * 0.6
Music Duck Amount = 0.2 (constant)

Final Volume = Base Volume * (1.0 - Duck Amount)
```

**Examples**:
- Light rain (intensity 0.3): Ambient ducks to 82%, Music ducks to 80%
- Heavy rain (intensity 0.8): Ambient ducks to 52%, Music ducks to 80%
- Blizzard (intensity 1.0): Ambient ducks to 40%, Music ducks to 80%

### Ducking Transition

**Duration**: 2 seconds (smooth transition)

**Curve**: Exponential ease-in/out
```
Duck Amount(t) = Duck Target * (1 - e^(-t / 0.5))
Where t = elapsed time (0-2 seconds)
```

**Behavior**:
- No sudden volume changes
- Smooth fade in/out
- No audio popping
- Applies to multiple layers simultaneously

---

## WEATHER TRANSITION SYSTEM

### State Transition Logic

**Event Subscription**:
```cpp
UFUNCTION()
void OnWeatherStateChanged(EWeatherState OldState, EWeatherState NewState, float Intensity);
```

**Transition Behavior**:
1. Fade out old weather audio over 5 seconds
2. Fade in new weather audio over 5 seconds
3. Update ducking parameters over 2 seconds
4. Trigger special events (thunder on STORM)

**Transition Audio Mapping**:
- CLEAR → any weather: 5-second fade-in
- Any weather → CLEAR: 5-second fade-out, restore ambient
- Weather → weather: 5-second crossfade

### Weather Service Integration

**Backend API Endpoints**:
```
GET /api/weather/current
    Returns: { "state": "rain", "intensity": 0.7, ... }

POST /api/weather/transition
    Request: { "target_state": "storm", "transition_time": 5.0 }
    Returns: Transition confirmation
```

**Real-time Updates**:
- WeatherManager polls every 5 seconds
- Intensity changes smoothly over time
- State changes trigger transitions
- Audio layers update automatically

---

## PERFORMANCE BUDGET

### CPU Requirements

**Per Weather Layer**: 0.1-0.15ms per frame
**Thunder Events**: 0.05ms per thunder strike
**Ducking System**: 0.05ms per frame
**Total**: ~0.4ms per frame (target)

**Optimization**:
- Weather loops are streaming audio
- Thunder audio is pre-loaded (small, short clips)
- Ducking uses efficient DSP filters
- Limit max thunder instances to 2

### Memory Budget

**Per Weather Asset**:
- Rain loops: ~5MB
- Wind loops: ~3MB
- Thunder audio: ~1MB (pre-loaded)
- Other sounds: ~2MB

**Total Weather Audio**: ~20MB

### Streaming Strategy

- Load active weather state + next predicted state
- Stream other states from disk
- Pre-cache thunder audio (small, frequent)
- Unload unused weather layers

---

## META SOUND TEMPLATES

### Required MetaSound Assets

**Rain Templates**:
- `MS_Rain_Light` - Light rain profile
- `MS_Rain_Heavy` - Heavy rain profile

**Storm Template**:
- `MS_Storm` - Complete storm system with thunder

**Snow Templates**:
- `MS_Snow_Light` - Light snow profile
- `MS_Snow_Heavy` - Heavy snow profile

**Wind Template**:
- `MS_Wind_Strong` - Strong wind profile

**Special Templates**:
- `MS_Fog` - Fog muffling effect
- `MS_Mist` - Light mist profile
- `MS_Blizzard` - Extreme blizzard profile

### MetaSound Parameter Exposure

**Common Parameters**:
- `Intensity` (float): 0.0-1.0 weather intensity
- `WindSpeed` (float): Wind speed from WeatherManager
- `Distance` (float): Distance to weather source
- `ReverbSend` (float): Reverb amount

**Event Parameters**:
- `TriggerThunder` (bool): Trigger thunder strike
- `ThunderVolume` (float): 0.7-1.0
- `ThunderPosition` (Vector3): 3D position

---

## BLUEPRINT INTEGRATION

### Blueprint API

**Weather Audio Control**:
```cpp
UFUNCTION(BlueprintCallable, Category = "Weather Audio")
void SetWeatherState(EWeatherState State, float Intensity);

UFUNCTION(BlueprintCallable, Category = "Weather Audio")
void TransitionWeatherState(EWeatherState NewState, float Duration);

UFUNCTION(BlueprintCallable, Category = "Weather Audio")
void SetWeatherIntensity(float Intensity);

UFUNCTION(BlueprintCallable, Category = "Weather Audio")
void TriggerThunderStrike(FVector StrikeLocation, float Volume);
```

**Event Delegates**:
```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWeatherStateChanged, EWeatherState, OldState, EWeatherState, NewState);
UPROPERTY(BlueprintAssignable, Category = "Weather Audio")
FOnWeatherStateChanged OnWeatherStateChanged;
```

---

## TESTING STRATEGY

### Unit Tests

**Weather Transitions**:
- Test all 15 weather state transitions
- Verify 5-second fade duration
- Ensure no audio popping
- Validate intensity scaling

**Ducking System**:
- Test ducking calculations
- Verify smooth 2-second transitions
- Ensure voice is never ducked
- Validate music ducking at 20%

**Thunder System**:
- Test thunder spawn intervals
- Verify volume randomization
- Test 3D positioning accuracy
- Ensure max 2 concurrent strikes

### Integration Tests

**WeatherManager → AudioManager**:
- Event subscription works
- State changes trigger audio
- Intensity updates smoothly
- Backend API integration

### Performance Tests

- Profile CPU usage per weather layer
- Memory allocation/deallocation
- Streaming performance
- Thunder spawn impact

---

## NEXT STEPS

1. ✅ Architecture design complete
2. ⏳ Create MetaSound templates in UE5 Editor
3. ⏳ Implement AudioManager weather extensions
4. ⏳ Integrate with WeatherManager service
5. ⏳ Test all weather transitions
6. ⏳ Performance optimization

---

**Status**: ✅ **DESIGN COMPLETE - READY FOR IMPLEMENTATION**



