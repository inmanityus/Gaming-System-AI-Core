# Zone-Based Ambient Audio System Design
**Date**: 2025-01-29  
**Task**: VA-002-D - Zone-Based Ambient Triggers  
**Status**: Design Complete

---

## OVERVIEW

This document defines the zone-based ambient audio trigger system that manages spatial audio zones with unique ambient profiles, enabling seamless audio transitions as players move between different environments.

---

## ZONE ARCHITECTURE

### Zone Types

**Architecture Categories**:
1. **Exterior Zones** - Open outdoor areas
2. **Interior Zones** - Enclosed indoor spaces
3. **Semi-Exterior Zones** - Partially covered transition areas

**Zone Variations**:
- **Exterior**: Street, Park, Alley, Plaza, Cemetery
- **Interior**: Warehouse, Morgue, Apartment, Lab, Office
- **Semi-Exterior**: Tunnel, Bridge, Market, Rooftop

---

## ZONE AUDIO PROFILES

### Exterior Zones

**Exterior Zone Example: Street**

**Audio Components**:
```
Base Audio:
    - Time-of-Day Ambient (full volume)
    - Weather Audio (full volume)
    - Traffic sounds
    - Crowd murmur

Zone-Specific:
    - Building echoes
    - Street-level details (footsteps, vehicles)
    - Architectural reverb (tall buildings)
    
Audio Mix:
    - Volume: 1.0
    - Reverb: Large open space
    - Occlusion: None (fully exposed)
    - Ducking: None
```

**Other Exterior Zones**:
- **Park**: Add nature sounds, reduce traffic, increase wind
- **Alley**: Add narrow space reverb, dampening, echos
- **Cemetery**: Add eerie ambience, reduce urban sounds
- **Plaza**: Add crowd sounds, increase reverb, open space

### Interior Zones

**Interior Zone Example: Warehouse**

**Audio Components**:
```
Base Audio:
    - Time-of-Day Ambient (muffled by 40%)
    - Weather Audio (completely blocked)
    - Distant urban sounds (barely audible)

Zone-Specific:
    - Warehouse reverb (large echo chamber)
    - Mechanical sounds (HVAC, machinery)
    - Echo and resonance
    - Footstep reverb (concrete/steel floor)
    
Audio Mix:
    - Volume: 0.8
    - Reverb: Large warehouse preset
    - Occlusion: Moderate (60-80% blocking)
    - Ducking: Light (10%)
```

**Interior Zone Profiles**:

| Zone Type | Time-of-Day | Weather | Reverb | Occlusion | Volume |
|-----------|-------------|---------|--------|-----------|--------|
| Warehouse | Muffled 40% | Blocked | Large Echo | 70% | 0.8 |
| Morgue | Muffled 60% | Blocked | Cold Tile | 80% | 0.6 |
| Apartment | Muffled 50% | Blocked | Small Room | 60% | 0.7 |
| Lab | Muffled 50% | Blocked | Clean Room | 70% | 0.7 |
| Office | Muffled 40% | Blocked | Medium Room | 70% | 0.8 |

**Interior Zone Details**:

**Warehouse**:
- Large echo chamber reverb
- Mechanical HVAC sounds
- Concrete footsteps
- Distant urban hum (10% volume)
- Weather blocked

**Morgue**:
- Cold, sterile reverb
- Refrigeration sounds
- Dripping water (sparse)
- Very quiet base ambient
- Horror undertones

**Apartment**:
- Small room reverb
- Neighbor sounds (above/below)
- Building creaks
- Slightly muffled city sounds
- Life-like atmosphere

**Lab**:
- Clean room acoustic
- Equipment humming
- Beeping (sparse)
- Muffled urban sounds
- Clinical atmosphere

### Semi-Exterior Zones

**Semi-Exterior Zone Example: Tunnel**

**Audio Components**:
```
Base Audio:
    - Time-of-Day Ambient (muffled by 20%)
    - Weather Audio (partially blocked, muffled)
    - Partial exposure to outdoor sounds

Zone-Specific:
    - Tunnel reverb (long corridor)
    - Echo effects
    - Wind through opening
    - Partial occlusion
    
Audio Mix:
    - Volume: 0.9
    - Reverb: Long corridor preset
    - Occlusion: Partial (30-50%)
    - Ducking: None
```

**Semi-Exterior Zone Profiles**:

| Zone Type | Time-of-Day | Weather | Reverb | Occlusion | Volume |
|-----------|-------------|---------|--------|-----------|--------|
| Tunnel | Muffled 20% | Partial (50%) | Long Corridor | 40% | 0.9 |
| Bridge | Full 80% | Partial (30%) | Open Space | 20% | 0.95 |
| Market | Muffled 30% | Partial (40%) | Semi-Open | 30% | 0.85 |
| Rooftop | Full 90% | Full | Rooftop Echo | 10% | 1.0 |

---

## ZONE TRANSITION SYSTEM

### Trigger Mechanism

**Overlap Volume System**:
```cpp
UCLASS()
class BODYBROKER_API AAmbientZoneTrigger : public AActor
{
    GENERATED_BODY()

public:
    // Zone profile name
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
    FString ZoneProfileName;
    
    // Zone type
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
    EZoneType ZoneType;
    
    // Max audible distance
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
    float MaxDistance;
    
    // Transition duration
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
    float TransitionDuration;
};
```

**Trigger Behavior**:
- On player overlap: Load zone profile
- On exit: Restore previous zone
- Crossfade duration: 5 seconds
- Distance-based volume scaling

### Zone Transition Logic

**Enter Zone**:
```
Player enters overlap volume
    ↓
ZoneTrigger.OnBeginOverlap(PlayerActor)
    ↓
AudioManager.SetZoneAmbientProfile(ZoneProfileName)
    ↓
MetaSoundPlayer.TransitionToProfile(Profile, 5.0)
    ↓
ReverbController.TransitionToPreset(ZoneReverb, 3.0)
    ↓
OcclusionSystem.UpdateOcclusion(ZoneOcclusion)
```

**Exit Zone**:
```
Player exits overlap volume
    ↓
ZoneTrigger.OnEndOverlap(PlayerActor)
    ↓
AudioManager.RestorePreviousZone()
    ↓
MetaSoundPlayer.TransitionToProfile(PreviousProfile, 5.0)
    ↓
ReverbController.TransitionToPreset(PreviousReverb, 3.0)
```

### Distance-Based Volume Control

**Volume Scaling Formula**:
```
Zone Volume = 1.0 - (PlayerDistance / MaxDistance)

Where:
    PlayerDistance = Distance from zone trigger center
    MaxDistance = Maximum audible distance (default: 500 units)
```

**Volume Curve**:
- **0-100 units**: 1.0 (full volume)
- **100-300 units**: 1.0 → 0.7 (linear fade)
- **300-500 units**: 0.7 → 0.0 (linear fade)
- **500+ units**: 0.0 (inaudible)

**Smooth Transition**:
- Volume updates every frame
- Distance calculated in real-time
- No sudden jumps or pops
- Logarithmic fade curve optional

---

## OCCLUSION SYSTEM

### Occlusion Calculation

**Raycast-Based Occlusion**:
```cpp
UFUNCTION(BlueprintCallable, Category = "Audio Occlusion")
float CalculateOcclusion(FVector SourceLocation, FVector ListenerLocation);
```

**Occlusion Logic**:
```
1. Line trace from source to listener
2. Count wall/geometry hits
3. Each hit adds 15% occlusion (capped at 100%)
4. Return final occlusion amount
```

**Occlusion Amount**:
```
Occlusion = min(1.0, hit_count * 0.15)

Where hit_count = number of geometry intersections
```

**Maximum Occlusion**: 100% (completely blocked)

### Occlusion Effects

**Exterior → Interior**:
- Base ambient ducks by 60%
- Weather audio completely blocked
- Reverb changes to interior preset
- Low-pass filter applied (cutoff ~3000 Hz)

**Interior → Exterior**:
- Base ambient volume increases by 40%
- Weather audio fades in over 5 seconds
- Reverb changes to exterior preset
- Low-pass filter removed

**Filter Implementation**:
```cpp
// Low-pass filter for occlusion
FilterCutoff = 3000.0 * (1.0 - occlusion_amount)

Where occlusion_amount = 0.0 (no filtering) to 1.0 (heavy filtering)
```

### Occlusion by Zone Type

**Exterior Zones**:
- Occlusion: 0-10% (minimal blocking)
- No filtering applied
- Full weather audio
- Full time-of-day ambient

**Interior Zones**:
- Occlusion: 60-80% (moderate to heavy blocking)
- Filtering: 3000-1000 Hz cutoff
- Weather blocked
- Ambient muffled

**Semi-Exterior Zones**:
- Occlusion: 30-50% (partial blocking)
- Filtering: 1500-2000 Hz cutoff
- Weather partial
- Ambient reduced

---

## REVERB/CONTEXT SWITCHING

### Reverb Preset System

**Context-Based Reverb**:

| Context | Reverb Preset | Room Size | Wet Level | Delay | Reflections |
|---------|---------------|-----------|-----------|-------|-------------|
| **Exterior - Day** | City Reverberation | 100% | 30% | 0.1s | 5 |
| **Exterior - Night** | Open Space | 80% | 20% | 0.2s | 3 |
| **Interior - Warehouse** | Large Echo Chamber | 120% | 30% | 0.3s | 8 |
| **Interior - Small Room** | Small Room | 20% | 50% | 0.05s | 2 |
| **Interior - Morgue** | Cold Tile Room | 40% | 60% | 0.1s | 6 |
| **Interior - Hall** | Hall Reverb | 60% | 40% | 0.15s | 4 |
| **Semi-Exterior** | Long Corridor | 80% | 35% | 0.2s | 5 |

**Reverb Application**:
- Affects Ambient category only
- Voice remains dry (100% unaffected)
- Music partially affected (10% reverb send)
- Effects unaffected by zone reverb

### Dynamic Reverb Switching

**Transition Duration**: 3 seconds

**Transition Logic**:
```
Old Preset → New Preset
    ↓
Wet Level: Old → New over 3 seconds
Room Size: Old → New over 3 seconds
Delay: Old → New over 3 seconds
```

**Smooth Transition**:
```cpp
CurrentValue = FMath::Lerp(OldValue, NewValue, FMath::Clamp(ElapsedTime / 3.0f, 0.0f, 1.0f))
```

**Submix-Based**:
- Reverb applied at submix level
- Automatic routing
- Efficient processing
- GPU-accelerated where possible

---

## ZONE PROFILE CONFIGURATION

### Zone Profile Data Structure

```cpp
USTRUCT(BlueprintType)
struct FZoneAudioProfile
{
    GENERATED_BODY()

    // Zone name
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString ProfileName;
    
    // Zone type
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    EZoneType ZoneType;
    
    // Time-of-day ambient multiplier
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float TimeOfDayAmbientMult;
    
    // Weather audio multiplier
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float WeatherAudioMult;
    
    // Occlusion amount (0.0-1.0)
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float OcclusionAmount;
    
    // Reverb preset name
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString ReverbPreset;
    
    // Base volume
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float BaseVolume;
};
```

### Zone Profile Examples

**Street (Exterior)**:
```cpp
FZoneAudioProfile StreetProfile;
StreetProfile.ProfileName = "Street";
StreetProfile.ZoneType = EZoneType::Exterior;
StreetProfile.TimeOfDayAmbientMult = 1.0f;
StreetProfile.WeatherAudioMult = 1.0f;
StreetProfile.OcclusionAmount = 0.0f;
StreetProfile.ReverbPreset = "CityReverberation";
StreetProfile.BaseVolume = 1.0f;
```

**Warehouse (Interior)**:
```cpp
FZoneAudioProfile WarehouseProfile;
WarehouseProfile.ProfileName = "Warehouse";
WarehouseProfile.ZoneType = EZoneType::Interior;
WarehouseProfile.TimeOfDayAmbientMult = 0.6f;  // 40% muffled
WarehouseProfile.WeatherAudioMult = 0.0f;      // Completely blocked
WarehouseProfile.OcclusionAmount = 0.7f;       // 70% occlusion
WarehouseProfile.ReverbPreset = "LargeEchoChamber";
WarehouseProfile.BaseVolume = 0.8f;
```

---

## INTEGRATION WITH WEATHER

### Zone + Weather Interaction

**Exterior Zones**:
```
Audio = TimeOfDayAmbient + WeatherLayers
Volume = Full (1.0)
Reverb = Exterior preset
Occlusion = None
```

**Interior Zones**:
```
Audio = TimeOfDayAmbient (muffled) + No Weather
Volume = 0.6-0.8
Reverb = Interior preset
Occlusion = 60-80%
```

**Semi-Exterior Zones**:
```
Audio = TimeOfDayAmbient (partial) + WeatherLayers (partial)
Volume = 0.85-0.95
Reverb = Semi-Exterior preset
Occlusion = 30-50%
```

### Weather Occlusion Example

**Rain + Interior Zone**:
- Rain sound completely blocked
- Only muffled thunder (if loud enough)
- Ambient reduced
- Interior-only sounds remain

**Storm + Exterior Zone**:
- Full storm audio
- Thunder audible at full volume
- Wind and rain at full intensity
- No attenuation

---

## PERFORMANCE CONSIDERATIONS

### CPU Budget

**Per Zone**:
- Distance calculation: 0.01ms
- Occlusion raycast: 0.02ms (if needed)
- Reverb processing: 0.05ms
- Volume scaling: 0.01ms

**Total**: ~0.1ms per zone per frame

### Memory Budget

**Per Zone Profile**: ~2MB (audio + metadata)
**Total Zones**: ~15-20 zones
**Total Memory**: ~30-40MB

### Optimization Strategy

- Cache zone profiles (avoid repeated lookups)
- Update distance every 5 frames (not every frame)
- Batch occlusion calculations
- Use spatial queries for zone detection
- Limit max active zones to 3

---

## BLUEPRINT INTEGRATION

### Blueprint API

```cpp
UFUNCTION(BlueprintCallable, Category = "Zone Audio")
void SetZoneAmbientProfile(const FString& ZoneProfileName);

UFUNCTION(BlueprintCallable, Category = "Zone Audio")
void RestorePreviousZone();

UFUNCTION(BlueprintCallable, Category = "Zone Audio")
FString GetCurrentZoneProfile();

UFUNCTION(BlueprintCallable, Category = "Zone Audio")
float CalculateOcclusion(FVector SourceLocation, FVector ListenerLocation);
```

### Zone Trigger Blueprint

**AAmbientZoneTrigger**:
- Placed in world via level designer
- Configurable parameters (zone name, type, distance)
- Automatic overlap detection
- Player enter/exit events
- Distance-based volume scaling

---

## TESTING STRATEGY

### Unit Tests

**Zone Transitions**:
- Test all zone type transitions
- Verify 5-second crossfade
- Ensure no audio popping
- Validate reverb switching

**Occlusion System**:
- Test occlusion calculations
- Verify raycast accuracy
- Test filter cutoff values
- Validate partial occlusion

### Integration Tests

**Zone + Weather + Time**:
- All systems working together
- No conflicts or audio artifacts
- Smooth transitions
- Performance acceptable

### Performance Tests

- Profile CPU usage per zone
- Memory allocation patterns
- Distance calculation overhead
- Occlusion raycast impact

---

## NEXT STEPS

1. ✅ Architecture design complete
2. ⏳ Implement zone trigger system in C++
3. ⏳ Create zone profiles database
4. ⏳ Integrate with AudioManager
5. ⏳ Test in-game transitions
6. ⏳ Performance optimization

---

**Status**: ✅ **DESIGN COMPLETE - READY FOR IMPLEMENTATION**



