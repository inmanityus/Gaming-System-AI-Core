# Niagara Particle Systems Architecture
**Date**: 2025-01-29  
**Task**: WS-002 - Niagara Particle Systems  
**Status**: Design Complete

---

## OVERVIEW

Complete Niagara particle system architecture for rain, snow, fog, and lightning effects, integrated with WeatherManager and optimized for performance.

---

## SYSTEM INTEGRATION

### Integration with WeatherManager

**Event Subscriptions**:
```cpp
WeatherManager->OnWeatherChanged.AddDynamic(this, &UNiagaraComponent::HandleWeatherChange);
WeatherManager->OnWeatherIntensityChanged.AddDynamic(this, &UNiagaraComponent::HandleIntensityChange);
```

**Parameter Updates**:
- Spawn rates based on weather state + intensity
- Particle properties adjusted dynamically
- LOD based on distance from player

---

## 1. RAIN PARTICLE SYSTEM

### Architecture

**Niagara System**: `NS_Rain`  
**Emitter Type**: GPU Sprite  
**Lifetime**: 0.5-1.0 seconds (based on height)

### Particle Properties

```
Property              Value                 Notes
──────────────────────────────────────────────────────────
Spawn Rate Base       2000 particles/sec    Calibrated base
Color                 [0.7, 0.8, 0.9, 0.8]  Gray-blue tint
Size                  Random(0.05, 0.15)    Droplet size
Velocity              Downward + variation  -300 cm/s + noise
Rotation              Random 360°           Random orientation
```

### Intensity Mapping

```
Weather State      Intensity   Spawn Rate      Notes
───────────────────────────────────────────────────────────
Clear              0.0         0               Off
PartlyCloudy       0.2         0               Not rain
Cloudy             0.4         0               Not rain
Rain               0.6         2000            Moderate
HeavyRain          0.8         5000            Heavy
Storm              1.0         8000            Maximum
```

**Formula**: `SpawnRate = BaseRate * Intensity^1.5`

### Collision System

**Collision Settings**:
- Enabled: Yes
- Collision Mode: Collision (not overlap)
- Collision Radius: Particle size + 10%
- Kill on Collision: Yes
- Spawn Splash Particles: Yes

**Splash System**:
- Niagara system: `NS_Rain_Splash`
- Spawn rate: 1 splash per 5 collisions
- Lifetime: 0.2 seconds
- Size: 50% of raindrop

### LOD System

```
Distance Range      Quality   Spawn Rate    Max Particles
──────────────────────────────────────────────────────────────
0-100m             Full      100%           8000
100-300m           Medium    50%            4000
300-600m           Low       25%            2000
600m+              Minimal   10%            800
```

**LOD Calculation**:
```cpp
float Distance = GetDistanceToPlayer();
float LODMultiplier = CalculateLODMultiplier(Distance);
float EffectiveSpawnRate = BaseSpawnRate * Intensity * LODMultiplier;
```

### Performance Budget

**Target**: 1.5ms GPU per frame (rain only)  
**Particle Count**: 8000 max  
**GPU Memory**: ~10MB

---

## 2. SNOW PARTICLE SYSTEM

### Architecture

**Niagara System**: `NS_Snow`  
**Emitter Type**: GPU Sprite  
**Lifetime**: 2.0-4.0 seconds (slower fall)

### Particle Properties

```
Property              Value                 Notes
──────────────────────────────────────────────────────────
Spawn Rate Base       1500 particles/sec    Calibrated base
Color                 [1.0, 1.0, 1.0, 0.9]  White with alpha
Size                  Random(0.1, 0.3)      Flake size
Velocity              Downward + wind       -50 cm/s + wind
Rotation              Slow rotation         30°/s
SubUV                 Yes                   Flake texture variety
```

### Intensity Mapping

```
Weather State      Intensity   Spawn Rate      Notes
───────────────────────────────────────────────────────────
Clear              0.0         0               Off
PartlyCloudy       0.2         0               Not snow
Cloudy             0.4         0               Not snow
Snow               0.6         1500            Moderate
HeavySnow          0.8         4000            Heavy
Blizzard           1.0         6000            Maximum
```

**Formula**: `SpawnRate = BaseRate * Intensity^1.5`

### Wind Integration

**Wind from WeatherManager**:
```cpp
FVector WindDirection = WeatherManager->GetWindDirection();
float WindSpeed = WeatherManager->GetWindSpeed();
```

**Wind Force on Particles**:
- Apply horizontal force based on wind
- Random variation per particle
- Wind affects rotation and fall speed

### Accumulation System

**Accumulation Logic**:
- Use Niagara's "Attraction to Surface" or "Collision Events"
- Spawn decal particles on surfaces
- Accumulate over time
- Melt based on temperature

**Decal System**: `NS_Snow_Accumulation`
- Spawn: On collision with ground
- Lifetime: 600 seconds (10 minutes)
- Fade: When temperature > 0°C

### LOD System

```
Distance Range      Quality   Spawn Rate    Max Particles
──────────────────────────────────────────────────────────────
0-100m             Full      100%           6000
100-300m           Medium    50%            3000
300-600m           Low       25%            1500
600m+              Minimal   10%            600
```

### Performance Budget

**Target**: 1.2ms GPU per frame (snow only)  
**Particle Count**: 6000 max  
**GPU Memory**: ~8MB

---

## 3. FOG/MIST VOLUMETRIC SYSTEM

### Architecture

**Niagara System**: `NS_Fog`  
**Emitter Type**: GPU Sprite (volumetric render mode)  
**Lifetime**: 10-20 seconds (long lived)

### Particle Properties

```
Property              Value                 Notes
──────────────────────────────────────────────────────────
Spawn Rate Base       500 particles/sec     Dense fog
Color                 [0.8, 0.8, 0.85, 0.5] Fog color
Size                  Large (20-100)        Billboards
Velocity              Slow drift            Wind-driven
Spawn Height          Ground + 500cm        Near surface
```

### Density Mapping

```
Weather State      Intensity   Spawn Rate      Density Multiplier
───────────────────────────────────────────────────────────
Clear              0.0         0               Off
PartlyCloudy       0.2         0               Not fog
Cloudy             0.4         100             20%
Fog                0.6         500             60%
Mist               0.3         200             30%
Storm              0.8         800             80% (enhanced)
```

**Formula**: `EffectiveSpawnRate = BaseRate * DensityMultiplier`

### Volumetric Rendering

**Render Mode**: Volumetric Fog  
**Depth Test**: Enabled  
**Blend Mode**: Translucent  
**Shadows**: Cast/Receive enabled

### Wind Integration

**Fog Drift**:
- Horizontal drift based on wind
- Slow vertical rise (buoyancy)
- Density variation based on wind speed

### LOD System

**Fog Always Active** (no LOD for realism):
- Full quality at all distances
- Adjust spawn area instead
- Reduce spawn rate at distance

**Area Reduction**:
```
Distance        Spawn Radius    Notes
──────────────────────────────────────────────
0-100m         100%             Full area
100-300m        75%             Slightly reduced
300-600m        50%             Reduced area
600m+           25%             Minimal area
```

### Performance Budget

**Target**: 0.5ms GPU per frame (fog only)  
**Particle Count**: 500 max  
**GPU Memory**: ~3MB

---

## 4. LIGHTNING STRIKE SYSTEM

### Architecture

**Niagara System**: `NS_Lightning`  
**Emitter Type**: GPU Ribbon (branching)  
**Duration**: 0.1-0.3 seconds (instant burst)

### Lightning Properties

```
Property              Value                 Notes
──────────────────────────────────────────────────────────
Spawn Mode            Event-based           Not constant
Branches              3-7                   Random
Color                 [1.0, 1.0, 0.9, 1.0]  Bright white
Length                1000-5000 cm          Random
Width                 5-15 cm               Varies
Intensity             Bright (10x bloom)    High exposure
Sound Trigger         Yes                   Thunder sound
```

### Lightning Trigger

**From WeatherManager**:
```cpp
void UWeatherManager::TriggerLightningStrike(FVector Location, float Intensity)
{
    // Spawn lightning
    LightningSystem->TriggerLightning(Location, Intensity);
    
    // Trigger thunder sound
    AudioManager->PlayThunderStrike(Location, Intensity);
}
```

### Strike Pattern

**Branching Algorithm**:
- Main stroke: Straight down
- Side branches: Random angles
- Sub-branches: Smaller, varied
- Flicker: 2-4 rapid bursts

### Bloom/Exposure

**Post-Process Integration**:
- High exposure during strike
- Exponential exposure fade
- Bloom intensity: 10.0x
- Tone curve adjustment

### Performance Budget

**Target**: 0.3ms GPU per frame (when active)  
**Particle Count**: 50-200  
**GPU Memory**: ~1MB  
**Active Frequency**: Rare (every 10-30 seconds in storm)

---

## 5. PARTICLE POOLING SYSTEM

### Pool Architecture

**Pool Types**:
```cpp
enum class EParticlePoolType
{
    Rain,
    Snow,
    Fog,
    Lightning
};
```

**Pool Manager**:
```cpp
class UParticlePoolManager : public UObject
{
    TMap<EParticlePoolType, TArray<UNiagaraComponent*>> Pools;
    TMap<EParticlePoolType, int32> InitialPoolSizes;
    
    void InitializePools();
    UNiagaraComponent* AcquireParticleSystem(EParticlePoolType Type);
    void ReleaseParticleSystem(UNiagaraComponent* System);
};
```

**Pool Sizes**:
```
System        Initial Size    Max Grow    Notes
─────────────────────────────────────────────────
Rain          2               4           Always spawning
Snow          1               2           Seasonal
Fog           1               2           Occasional
Lightning     3               5           Event-based
─────────────────────────────────────────────────
TOTAL         7               13
```

---

## 6. COMPLETE PERFORMANCE BUDGET

### Combined GPU Budget

```
System          Target    Max       Memory    Notes
─────────────────────────────────────────────────────
Rain            1.5ms     2.5ms     10MB      Most common
Snow            1.2ms     2.0ms      8MB      Seasonal
Fog             0.5ms     1.0ms      3MB      Persistent
Lightning       0.3ms     0.8ms      1MB      Rare
─────────────────────────────────────────────────────
TOTAL           3.5ms     6.3ms     22MB      Worst case
```

**Target**: 3.5ms GPU per frame  
**Critical**: 6.3ms max  
**Memory**: 22MB total

### Optimization Strategies

**1. LOD Reduction**:
- Reduce particles by distance
- Disable systems at extreme range
- Quality scaling

**2. Pooling**:
- Pre-allocate systems
- Reuse instead of spawn/destroy
- Memory efficient

**3. Update Throttling**:
```
Rain:     Every frame (critical)
Snow:     Every frame (critical)
Fog:      Every 2 frames (accept)
Lightning: Event-based only
```

**4. Culling**:
- Disable when off-screen
- Skip updates for distant systems
- Don't render beyond max distance

---

## INTEGRATION WITH WEATHERMANAGER

### Event-Based Updates

**OnWeatherChanged**:
```cpp
void BP_WeatherController::HandleWeatherChanged(EWeatherState NewState, EWeatherState OldState)
{
    // Enable/disable systems
    SetSystemActive(NS_Rain, IsRain(NewState));
    SetSystemActive(NS_Snow, IsSnow(NewState));
    SetSystemActive(NS_Fog, IsFog(NewState));
    
    // Update parameters
    UpdateAllSystems(NewState);
}
```

**OnWeatherIntensityChanged**:
```cpp
void BP_WeatherController::HandleIntensityChanged(EWeatherState State, float Intensity)
{
    // Update spawn rates
    UpdateRainSpawnRate(Intensity);
    UpdateSnowSpawnRate(Intensity);
    UpdateFogDensity(Intensity);
}
```

---

## BLUEPRINT API

### Weather Controller Functions

```cpp
// Control systems
UFUNCTION(BlueprintCallable)
void SetSystemActive(UNiagaraSystem* System, bool bActive);

UFUNCTION(BlueprintCallable)
void UpdateRainSpawnRate(float Intensity);

UFUNCTION(BlueprintCallable)
void UpdateSnowSpawnRate(float Intensity);

UFUNCTION(BlueprintCallable)
void UpdateFogDensity(float Intensity);

UFUNCTION(BlueprintCallable)
void TriggerLightning(FVector Location, float Intensity);

// LOD control
UFUNCTION(BlueprintCallable)
void SetLODLevel(int32 LODLevel);  // 0-3
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Create NS_Rain Niagara system
- [ ] Create NS_Snow Niagara system
- [ ] Create NS_Fog Niagara system
- [ ] Create NS_Lightning Niagara system
- [ ] Create NS_Rain_Splash system
- [ ] Create NS_Snow_Accumulation system
- [ ] Implement BP_WeatherController
- [ ] Implement particle pooling
- [ ] Implement LOD system
- [ ] Performance profile all systems
- [ ] Integration testing
- [ ] Visual QA

---

**Status**: ✅ **PARTICLE SYSTEMS ARCHITECTURE COMPLETE**



