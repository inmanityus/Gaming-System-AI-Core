# Time-of-Day Ambient MetaSound Design
**Date**: 2025-01-29  
**Task**: VA-002-B - Time-of-Day Ambient MetaSound Profiles  
**Status**: Design Complete

---

## OVERVIEW

This document defines the four ambient MetaSound profiles that correspond to time-of-day states, providing immersive audio backgrounds that dynamically respond to game time progression.

---

## META SOUN D PROFILES

### 1. Dawn Ambient (05:00 - 08:00)

**MetaSound Name**: `MS_DawnAmbient`

**Profile Characteristics**:
- Peaceful, hopeful atmosphere
- Natural sounds dominate
- Urban elements distant and muffled
- Transitional mood from night to day

**Audio Layers**:
```
Layer 1: Birds Chirping (Dynamic)
    - Bird species: Crow, sparrow, robin
    - Density: Sparse (8-12 chirps/minute)
    - Volume: 0.4-0.6
    - Random interval spawn
    - 3D positioning (above player, scattered)

Layer 2: Morning Wind
    - Natural wind sounds
    - Frequency: Low (0.3-0.5 Hz)
    - Volume: 0.3
    - Continuous loop
    - Low-pass filter: 3000 Hz

Layer 3: Distant City Ambience
    - Muffled traffic
    - Far-away sirens (rare)
    - Urban hum
    - Volume: 0.2
    - Distance: 2000+ units
    - High attenuation

Layer 4: Atmospheric Texture
    - Subtle reverb
    - Slight echo delay
    - Volume: 0.1
    - Continuous drone
```

**MetaSound Graph Structure**:
```
Inputs:
    - TimeState (string): "dawn"
    - PlayerPosition (Vector3)
    - WindSpeed (float)

Outputs:
    - MasterAmbientOut
    - ReverbSend
    - DistanceAttenuation

Dynamic Elements:
    - Bird chirp spawner (random interval 8-12/min)
    - Wind gust variation (0.5 Hz modulation)
    - Distant sound emitters (sparse, far away)
```

**Blueprint Parameters**:
- `BirdChirpFrequency` (float): 0.5 (spawns/minute multiplier)
- `WindIntensity` (float): 0.3-0.5
- `CityAmbienceDistance` (float): 2000.0

---

### 2. Day Ambient (08:00 - 18:00)

**MetaSound Name**: `MS_DayAmbient`

**Profile Characteristics**:
- Active, bustling atmosphere
- High-energy urban sounds
- Traffic, crowds, construction
- Peak activity period

**Audio Layers**:
```
Layer 1: Traffic Loop
    - Continuous vehicle sounds
    - Volume: 0.6
    - Frequency: Full spectrum
    - Distance: 500-1000 units
    - Panning: Stereo field (left/right)
    - Dynamic layering: 3-5 vehicle types

Layer 2: Crowd Murmur
    - Indistinct conversations
    - Volume: 0.4
    - 10-20 simultaneous voices
    - Random walk patterns
    - 3D positioned

Layer 3: Construction/Machinery
    - Sporadic construction sounds
    - Volume: 0.3-0.5 (varies by time)
    - Event-based (10-20 events/hour)
    - Distance: 800-1200 units
    - Low-pass for distance

Layer 4: Urban Texture
    - Street-level details
    - Footsteps (occasional)
    - Car doors closing
    - Horns (rare, 2-5/hour)
    - Volume: 0.2
```

**MetaSound Graph Structure**:
```
Inputs:
    - TimeState (string): "day"
    - Hour (int): Current hour (affects activity level)
    - PlayerPosition (Vector3)

Outputs:
    - MasterAmbientOut
    - ReverbSend (City Reverberation)

Dynamic Elements:
    - Vehicle spawner (continuous loop with variation)
    - Crowd positioning system (10-20 NPCs)
    - Construction event timer (rare, random)
    - Urban texture player (random interval)
```

**Blueprint Parameters**:
- `ActivityLevel` (float): 0.5-1.0 (peaks at noon)
- `TrafficVolume` (float): 0.6
- `CrowdDensity` (float): 0.4

**Time Variations**:
- **Morning (08:00-12:00)**: Rising activity, traffic peaks
- **Afternoon (12:00-16:00)**: Sustained high activity
- **Late Afternoon (16:00-18:00)**: Traffic buildup, crowd shifts

---

### 3. Dusk Ambient (18:00 - 21:00)

**MetaSound Name**: `MS_DuskAmbient`

**Profile Characteristics**:
- Transitional, moody atmosphere
- Winds intensify
- Urban sounds diminish
- Eerie undertones emerge

**Audio Layers**:
```
Layer 1: Evening Wind
    - Stronger than dawn
    - Frequency: 0.5-0.8 Hz
    - Volume: 0.5
    - Continuous with gusts
    - Whistling at higher wind speeds

Layer 2: Diminishing Traffic
    - Fewer vehicles
    - Lower volume (0.3)
    - More distant
    - Sparse honking

Layer 3: Distant Sirens
    - Occasional police/fire
    - Volume: 0.4
    - Distance: 1500+ units
    - Doppler effect

Layer 4: Eerie Ambience
    - Low-frequency hum
    - Slight dissonance
    - Volume: 0.15
    - Creates unease
    - Foreshadowing night
```

**MetaSound Graph Structure**:
```
Inputs:
    - TimeState (string): "dusk"
    - WindSpeed (float): From WeatherManager
    - PlayerPosition (Vector3)

Outputs:
    - MasterAmbientOut
    - ReverbSend (Transitional Space)
    - WindModulation (affects other layers)

Dynamic Elements:
    - Wind intensity controller
    - Siren spawner (1-2/hour)
    - Traffic decayer (gradual volume reduction)
    - Eerie texture drone (subtle, continuous)
```

**Blueprint Parameters**:
- `WindIntensity` (float): 0.5-0.8
- `TrafficDecay` (float): 0.5 (reduction multiplier)
- `EerieAmount` (float): 0.15

**Transition Behavior**:
- Crossfades from Day Ambient over 30 seconds
- Wind gradually increases
- Traffic sounds fade out
- Eerie tones fade in

---

### 4. Night Ambient (21:00 - 05:00)

**MetaSound Name**: `MS_NightAmbient`

**Profile Characteristics**:
- Quiet, ominous atmosphere
- Minimal urban sounds
- Enhanced hearing of distant threats
- Horror-ready ambience

**Audio Layers**:
```
Layer 1: Night Wind
    - Subtle, haunting
    - Frequency: 0.2-0.4 Hz
    - Volume: 0.4
    - Whispers and howls
    - Occasional gust

Layer 2: Distant City
    - Very muffled traffic
    - Volume: 0.15
    - Distance: 3000+ units
    - Barely audible
    - High attenuation

Layer 3: Ambient Night Sounds
    - Insects chirping (sparse)
    - Occasional dog bark (500-1000 units)
    - Rare distant voices
    - Volume: 0.2
    - Sparse (2-5 events/hour)

Layer 4: Ominous Drone
    - Low-frequency base
    - Subtle dissonance
    - Volume: 0.2
    - Creates tension
    - Continuous

Layer 5: Horror Elements (Dynamic)
    - Distant howls (very rare, 1-2/night)
    - Strange mechanical sounds
    - Unexplained noises
    - Volume: 0.3
    - Random timing
    - Fade in/out
```

**MetaSound Graph Structure**:
```
Inputs:
    - TimeState (string): "night"
    - PlayerPosition (Vector3)
    - DangerLevel (float): Increases with proximity to threats

Outputs:
    - MasterAmbientOut
    - ReverbSend (Open Night Space)
    - TensionModulator

Dynamic Elements:
    - Wind controller (subtle but present)
    - Sparse sound spawner (2-5 events/hour)
    - Horror event trigger (rare, context-based)
    - Tension oscillator (subtle pulse)
```

**Blueprint Parameters**:
- `WindIntensity` (float): 0.4
- `DangerLevel` (float): 0.0-1.0 (affects horror elements)
- `UrbanVolume` (float): 0.1 (very quiet)

**Horror Integration**:
- Horror elements activate when `DangerLevel > 0.5`
- Fade in over 10 seconds
- Increase tension oscillator
- Trigger rare howl events

---

## META SOUND TRANSITION SYSTEM

### Crossfading Logic

**Transition Duration**: 30 seconds (configurable)

**Crossfade Curve**: Smooth logarithmic fade
```
Old Profile Volume = 1.0 - (t / 30.0)
New Profile Volume = t / 30.0

Where t = elapsed time (0-30 seconds)
```

**Transition Behavior**:
- Old profile fades out over 30 seconds
- New profile fades in over 30 seconds
- No volume clipping or popping
- Parameter interpolation for smooth blending
- Reverb transitions separately (3-second fade)

### Trigger Mechanism

**Event Subscriber**:
```cpp
UFUNCTION()
void OnTimeStateChanged(FString OldState, FString NewState);
```

**Blueprint Event**:
```
TimeOfDayManager → OnTimeStateChanged
    ↓
AmbientAudioController → ReceiveTimeStateChange(OldState, NewState)
    ↓
MetaSoundPlayer → TransitionToProfile(NewState)
    ↓
AudioManager → SetAmbientAudio(ProfileID)
```

**State Mapping**:
- "dawn" → MS_DawnAmbient
- "day" → MS_DayAmbient
- "dusk" → MS_DuskAmbient
- "night" → MS_NightAmbient

---

## PERFORMANCE CONSIDERATIONS

### CPU Budget per Profile

**Target**: 0.3ms per frame per profile

**Breakdown**:
- Base ambient loop: 0.1ms
- Dynamic element spawning: 0.1ms
- Distance calculations: 0.05ms
- Reverb processing: 0.05ms

**Optimization**:
- Pre-calculate dynamic element spawn times
- Use object pooling for 3D sounds
- Limit max simultaneous sounds to 10
- Cache distance calculations (update every 5 frames)

### Memory Budget

**Per Profile**: ~7-8MB uncompressed audio
**Total**: ~30MB for all 4 profiles

**Streaming Strategy**:
- Load current profile + next profile in memory
- Stream other profiles from disk
- Preload on time transition prediction

---

## TESTING STRATEGY

### Unit Tests

**Transition Tests**:
- Verify all 4 state transitions work
- Test 30-second crossfade smoothness
- Ensure no audio popping

**Performance Tests**:
- Profile CPU usage < 0.3ms
- Memory usage < 8MB per profile
- No frame spikes during transitions

**Integration Tests**:
- TimeOfDayManager → AmbientAudioController
- Backend API response handling
- Blueprint event triggering

---

## CREATION INSTRUCTIONS

### MetaSound Asset Creation (UE5 Editor)

1. **Create MetaSound Template**
   - Right-click Content Browser → Sounds → MetaSound
   - Choose "Ambient Template"
   - Name: `MS_DawnAmbient` (repeat for all 4)

2. **Add Audio Sources**
   - Import ambient audio files
   - Set as streaming (for memory)
   - Configure looping properties

3. **Build Dynamic Elements**
   - Add random interval nodes
   - Create spawner graph
   - Link to 3D positioning

4. **Expose Parameters**
   - Make parameters Blueprint-accessible
   - Set default values
   - Add validation

5. **Optimize Performance**
   - Enable distance culling
   - Set max audible distance
   - Configure LOD levels

---

## NEXT STEPS

1. ✅ Architecture design complete
2. ⏳ Create MetaSound assets in UE5 Editor
3. ⏳ Implement transition system in AudioManager
4. ⏳ Test with TimeOfDayManager integration
5. ⏳ Performance profiling and optimization

---

**Status**: ✅ **DESIGN COMPLETE - READY FOR ASSET CREATION**



