# Phase 4 Runtime Testing Preparation Guide
**Date**: 2025-01-29  
**Status**: ✅ Code Complete - Ready for UE5 Editor Testing  
**Build Status**: ✅ SUCCESS (8.25 seconds)

---

## OVERVIEW

This guide provides step-by-step instructions for runtime testing Phase 4 systems in UE5 Editor. All code is complete and compiles successfully. This guide focuses on asset creation and test execution.

---

## PREREQUISITES

### ✅ Completed
- [x] UE5 5.6.1 installed (`C:\Program Files\Epic Games\UE_5.6`)
- [x] Project compiles successfully
- [x] All Phase 4 code implemented
- [x] No compilation errors

### ⏳ Required Before Testing
- [ ] Open project in UE5 Editor
- [ ] Create required assets (see Asset Creation section)
- [ ] Configure AudioManager settings
- [ ] Set up test Blueprints

---

## ASSET CREATION CHECKLIST

### 1. MetaSound Templates (VA-002)

**Location**: `/Game/Audio/MetaSounds/`

**Required Assets**:
- `MS_DawnAmbient` - Dawn ambient audio MetaSound
- `MS_DayAmbient` - Day ambient audio MetaSound
- `MS_DuskAmbient` - Dusk ambient audio MetaSound
- `MS_NightAmbient` - Night ambient audio MetaSound
- `MS_Weather_Rain` - Rain weather layer
- `MS_Weather_Rain_Heavy` - Heavy rain weather layer
- `MS_Weather_Snow` - Snow weather layer
- `MS_Weather_Snow_Heavy` - Heavy snow weather layer
- `MS_Weather_Blizzard` - Blizzard weather layer
- `MS_Weather_Wind_Light` - Light wind layer
- `MS_Weather_Wind_Moderate` - Moderate wind layer
- `MS_Weather_Wind_Strong` - Strong wind layer
- `MS_Weather_Wind_Howling` - Howling wind layer
- `MS_Weather_Fog_Ambient` - Fog ambient layer
- `MS_Weather_Mist_Ambient` - Mist ambient layer
- `MS_Weather_Heat_Haze` - Extreme heat layer
- `MS_Weather_Cold_Wind` - Extreme cold layer
- `MS_Weather_Thunder` - Thunder strike event (one-shot)
- `MS_Zone_{ZoneName}` - Zone-specific ambient profiles (create as needed)

**Creation Steps**:
1. Open MetaSound Editor in UE5
2. Create looping MetaSound graphs for ambient/weather layers
3. Configure looping, volume, and spatial settings
4. Save with exact names listed above
5. Place in `/Game/Audio/MetaSounds/` folder

---

### 2. Reverb Effect Assets (VA-002)

**Location**: `/Game/Audio/Reverb/`

**Required Assets**:
- Create `UReverbEffect` assets for different zone types:
  - `RE_Interior_Small` - Small interior spaces
  - `RE_Interior_Large` - Large interior spaces (cathedrals, halls)
  - `RE_Exterior_Open` - Open exterior spaces
  - `RE_Exterior_Urban` - Urban exterior spaces
  - `RE_Exterior_Forest` - Forest exterior spaces
  - `RE_Exterior_Cave` - Cave/interior-like exterior spaces

**Configuration**:
1. Create `UReverbEffect` assets in Content Browser
2. Configure reverb parameters (room size, damping, etc.)
3. In AudioManager Blueprint or C++:
   - Add entries to `ReverbEffectMap` (FString → TSoftObjectPtr<UReverbEffect>)
   - Configure `ReverbPresetLevels` (preset name → send level 0.0-1.0)

**Code Example** (in AudioManager initialization):
```cpp
// In AudioManager::BeginPlay() or initialization function
ReverbEffectMap.Add(TEXT("interior_small"), TSoftObjectPtr<UReverbEffect>(LoadObject<UReverbEffect>(nullptr, TEXT("/Game/Audio/Reverb/RE_Interior_Small.RE_Interior_Small"))));
ReverbPresetLevels.Add(TEXT("interior_small"), 0.6f); // 60% wet level
```

---

### 3. Animation Blueprints (FE-002, FE-003)

**Location**: `/Game/Animation/AnimBlueprints/`

**Required Assets**:
- `ABP_BodyLanguage` - Body language animation blueprint
  - Parameters: `IdleVariation` (int32), `GestureIndex` (int32)
  - IK targets: `LeftHandIKTarget`, `RightHandIKTarget`
- `ABP_MetaHumanExpression` - MetaHuman expression animation blueprint
  - Parameters: `EyeRotationX`, `EyeRotationY`, `EyeRotationZ` (float)
  - Parameters: `Emotion_Happy`, `Emotion_Sad`, `Emotion_Angry`, `Emotion_Surprised` (float)

**Creation Steps**:
1. Create Animation Blueprint from skeletal mesh
2. Add parameters listed above
3. Wire parameters to animation nodes
4. For IK: Configure IK nodes with bone names (`hand_l`, `hand_r`)

---

### 4. Control Rig Assets (FE-002)

**Location**: `/Game/Animation/ControlRigs/`

**Required Assets**:
- `CR_MetaHuman_Facial` - MetaHuman facial Control Rig
  - Controls: Eye rotation, mouth shapes, facial expressions

**Note**: Control Rig integration uses Animation Blueprint parameters as primary method, with blend shapes as fallback.

---

### 5. Gesture Montage Assets (FE-003)

**Location**: `/Game/Animation/Montages/Gestures/`

**Required Assets**:
- Create gesture montages for common gestures:
  - `AM_Gesture_Wave`
  - `AM_Gesture_Point`
  - `AM_Gesture_ThumbsUp`
  - `AM_Gesture_Shrug`
  - (Add more as needed)

**Data Table Setup**:
1. Create Data Table with structure:
```cpp
USTRUCT()
struct FGestureData : public FTableRowBase
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere)
    FName GestureName;
    
    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UAnimMontage> GestureMontage;
};
```
2. Populate with gesture montages
3. Assign to `BodyLanguageComponent::GestureDataTable`

---

### 6. Expression Preset Data Table (FE-001)

**Location**: `/Game/Data/Expressions/`

**Required Asset**:
- `DT_ExpressionPresets` - Data Table with `FExpressionPresetRow` structure

**Structure** (already defined in `ExpressionManagerComponent.h`):
```cpp
USTRUCT()
struct FExpressionPresetRow : public FTableRowBase
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere)
    FName PresetName;
    
    UPROPERTY(EditAnywhere)
    TMap<FString, float> BlendShapeWeights; // Morph target name -> weight
};
```

**Creation Steps**:
1. Create Data Table asset
2. Set Row Structure to `FExpressionPresetRow`
3. Add rows for common expressions (Happy, Sad, Angry, Surprised, etc.)
4. Configure blend shape weights for each expression

---

### 7. Niagara Particle Systems (WS-003)

**Location**: `/Game/VFX/Weather/`

**Required Assets**:
- `NS_Weather_Rain` - Rain particle system
- `NS_Weather_Snow` - Snow particle system
- `NS_Weather_Fog` - Fog volumetric particle system
- `NS_Weather_Lightning` - Lightning strike effect

**Configuration**:
1. Create Niagara systems in Content Browser
2. Configure particle parameters
3. Assign to `WeatherParticleManager` component properties

---

### 8. Material Instances (TE-002)

**Location**: `/Game/Materials/Flora/`

**Required Assets**:
- Material Instances for flora with parameters:
  - `SeasonProgress` (Scalar, 0.0-1.0)
  - `WindStrength` (Scalar, 0.0-1.0)
  - `WindDirection` (Vector3)

**Creation Steps**:
1. Create Material Instances from base flora materials
2. Expose parameters listed above
3. Assign to flora meshes used by `FloraManager`

---

### 9. Biome Data Assets (TE-001)

**Location**: `/Game/Data/Biomes/`

**Required Assets**:
- `DA_Biome_Forest` - Forest biome data asset
- `DA_Biome_Desert` - Desert biome data asset
- `DA_Biome_Tundra` - Tundra biome data asset
- (Add more biome types as needed)

**Structure** (defined in `BiomeManager.h`):
- `UBiomeDataAsset` with `EBiomeType` and biome-specific data

**Creation Steps**:
1. Create Data Asset from `UBiomeDataAsset` class
2. Set `BiomeType` enum value
3. Configure biome-specific parameters
4. Register with `BiomeManager` via `RegisterBiomeAsset()`

---

## TEST BLUEPRINT SETUP

### Test Actor Blueprint: `BP_Phase4TestActor`

**Components**:
- `AudioManager` (Component)
- `DialogueManager` (Subsystem - accessed via GameInstance)
- `LipSyncComponent` (Component)
- `BodyLanguageComponent` (Component)
- `MetaHumanExpressionComponent` (Component)
- `ExpressionManagerComponent` (Component)
- `WeatherParticleManager` (Component)
- `WeatherMaterialManager` (Component)
- `FloraManager` (Subsystem)
- `FaunaManager` (Subsystem)
- `BiomeManager` (Subsystem)
- `EcosystemIntegrationManager` (Subsystem)
- `TimeOfDayManager` (Subsystem)

**Setup Steps**:
1. Create new Blueprint Actor class
2. Add all components listed above
3. Configure component properties:
   - AudioManager: Set backend URL, configure category volumes
   - LipSyncComponent: Assign skeletal mesh component reference
   - BodyLanguageComponent: Assign gesture data table, set IK bone names
   - MetaHumanExpressionComponent: Assign skeletal mesh component reference
   - ExpressionManagerComponent: Assign expression preset data table
   - WeatherParticleManager: Assign Niagara particle systems
   - FloraManager: Register flora types
   - BiomeManager: Register biome assets

---

## RUNTIME TEST EXECUTION

### Test 1: AudioManager Initialization

**Steps**:
1. Spawn `BP_Phase4TestActor` in level
2. Check Output Log for: `"AudioManager: BeginPlay"`
3. Verify AudioManager initializes without errors
4. Check that `InitializeVA002Systems()` completes

**Expected Results**:
- ✅ No errors in log
- ✅ AudioManager component active
- ✅ VA-002 systems initialized

---

### Test 2: Time-of-Day Ambient (VA-002)

**Steps**:
1. Get AudioManager reference from test actor
2. Call `SetTimeOfDayAmbient("dawn")`
3. Verify ambient audio starts playing
4. Call `SetTimeOfDayAmbient("day")` after 5 seconds
5. Verify crossfade occurs (30-second transition)

**Expected Results**:
- ✅ Dawn ambient plays immediately
- ✅ Day ambient crossfades in over 30 seconds
- ✅ No audio popping or artifacts
- ✅ Both components active during crossfade

**Blueprint Node Sequence**:
```
Event BeginPlay
  → Get AudioManager Component
  → Set Time Of Day Ambient (Dawn)
  → Delay 5.0
  → Set Time Of Day Ambient (Day)
```

---

### Test 3: Weather Audio Layering (VA-002)

**Steps**:
1. Call `SetWeatherAudioLayer(EWeatherState::RAIN, 0.5f)`
2. Verify rain layer plays at 50% volume
3. Call `SetWeatherAudioLayer(EWeatherState::STORM, 0.8f)`
4. Verify heavy rain + wind layers play
5. Verify ambient audio ducks appropriately

**Expected Results**:
- ✅ Rain layer plays at correct volume
- ✅ Storm layers (rain + wind) both play
- ✅ Ambient ducks by intensity * 0.6
- ✅ Music ducks by 20%

**Blueprint Node Sequence**:
```
Event BeginPlay
  → Get AudioManager Component
  → Set Weather Audio Layer (Rain, Intensity: 0.5)
  → Delay 3.0
  → Set Weather Audio Layer (Storm, Intensity: 0.8)
```

---

### Test 4: Zone Ambient Profiles (VA-002)

**Steps**:
1. Call `SetZoneAmbientProfile("Forest")`
2. Verify zone ambient plays
3. Call `SetZoneAmbientProfile("Cave")` after 3 seconds
4. Verify crossfade occurs (5-second transition)

**Expected Results**:
- ✅ Forest ambient plays
- ✅ Cave ambient crossfades in over 5 seconds
- ✅ Smooth transition

---

### Test 5: Reverb System (VA-002)

**Steps**:
1. Configure `ReverbEffectMap` with test reverb asset
2. Call `SetReverbPreset("interior_small", 3.0f)`
3. Verify reverb activates
4. Check that audio components receive reverb send levels
5. Call `SetReverbPreset("exterior_open", 3.0f)`
6. Verify reverb transitions smoothly

**Expected Results**:
- ✅ Reverb effect activates
- ✅ Send levels interpolate smoothly
- ✅ All audio components respect reverb send

**Note**: Requires `UReverbEffect` assets and `ReverbEffectMap` configuration.

---

### Test 6: Dialogue Priority System (VA-003)

**Steps**:
1. Get DialogueManager subsystem from GameInstance
2. Create test dialogue items with different priorities
3. Enqueue Priority 3 dialogue
4. Enqueue Priority 0 dialogue (should interrupt)
5. Verify Priority 0 plays immediately
6. Verify Priority 3 is interrupted

**Expected Results**:
- ✅ Priority 0 interrupts Priority 3
- ✅ Priority 3 stops immediately
- ✅ Priority 0 plays

**Blueprint Node Sequence**:
```
Event BeginPlay
  → Get Dialogue Manager Subsystem
  → Play Dialogue (Priority: 3, Text: "Low priority dialogue")
  → Delay 1.0
  → Play Dialogue (Priority: 0, Text: "Critical dialogue")
```

---

### Test 7: Dialogue Crossfade Interrupt (VA-003)

**Steps**:
1. Play Priority 2 dialogue
2. Play Priority 1 dialogue (should crossfade)
3. Verify crossfade occurs over 0.5 seconds
4. Verify old dialogue stops after crossfade

**Expected Results**:
- ✅ Crossfade occurs smoothly
- ✅ Old dialogue fades out
- ✅ New dialogue fades in
- ✅ Old dialogue stops after crossfade completes

---

### Test 8: Dialogue Pause-Resume Interrupt (VA-003)

**Steps**:
1. Play Priority 2 dialogue
2. Play Priority 1 dialogue (should pause Priority 2)
3. Verify Priority 2 pauses
4. Verify Priority 1 plays
5. Wait for Priority 1 to complete
6. Verify Priority 2 resumes automatically

**Expected Results**:
- ✅ Priority 2 pauses when Priority 1 starts
- ✅ Priority 1 plays normally
- ✅ Priority 2 resumes after Priority 1 completes

---

### Test 9: Lip-Sync System (VA-003)

**Steps**:
1. Get LipSyncComponent from test actor
2. Create test `FLipSyncData` with phoneme frames
3. Call `StartLipSync(LipSyncData)`
4. Verify visemes apply to skeletal mesh
5. Verify jaw animation updates over time

**Expected Results**:
- ✅ Lip-sync data accepted
- ✅ Visemes apply to blend shapes
- ✅ Jaw animation updates smoothly

**Test Data Creation** (Blueprint):
```
Create FLipSyncData structure
  → Set AudioID: "test_audio"
  → Set DialogueID: "test_dialogue"
  → Add FPhonemeFrame (Time: 0.0, Phoneme: "AA", Viseme: "a")
  → Add FPhonemeFrame (Time: 0.2, Phoneme: "IH", Viseme: "i")
  → Start Lip Sync
```

---

### Test 10: Expression System (FE-001)

**Steps**:
1. Get ExpressionManagerComponent from test actor
2. Call `SetEmotionalState(EEmotionType::Happy, 1.0f)`
3. Verify blend shapes apply to skeletal mesh
4. Call `LoadExpressionPreset("Happy")`
5. Verify preset loads and applies

**Expected Results**:
- ✅ Emotional state applies blend shapes
- ✅ Preset loads from data table
- ✅ Blend shapes update correctly

---

### Test 11: Body Language IK (FE-003)

**Steps**:
1. Get BodyLanguageComponent from test actor
2. Call `SetHandPosition(LeftPos, RightPos)`
3. Verify IK targets update
4. Call `PlayGesture("Wave")`
5. Verify gesture montage plays

**Expected Results**:
- ✅ IK targets created and positioned
- ✅ Hand positions update via IK
- ✅ Gesture montage plays

**Note**: Requires Animation Blueprint with IK setup and gesture data table.

---

### Test 12: Weather Particle System (WS-003)

**Steps**:
1. Get WeatherParticleManager from test actor
2. Call `SetWeatherState(EWeatherState::RAIN)`
3. Verify rain particle system activates
4. Call `SetWeatherState(EWeatherState::SNOW)`
5. Verify snow particle system activates

**Expected Results**:
- ✅ Rain particles spawn
- ✅ Snow particles spawn
- ✅ Transitions are smooth

---

### Test 13: Ecosystem Integration (TE-004)

**Steps**:
1. Get EcosystemIntegrationManager subsystem
2. Call `InitializeEcosystemForArea(Location, Radius)`
3. Verify flora spawns
4. Verify fauna spawns
5. Call `UpdateEcosystemWeather(EWeatherState::RAIN)`
6. Verify flora/fauna respond to weather

**Expected Results**:
- ✅ Flora spawns in area
- ✅ Fauna spawns in area
- ✅ Weather updates affect flora/fauna behavior

---

## PERFORMANCE VALIDATION

### CPU Budget
- **Target**: < 5% CPU per system
- **Measurement**: Use UE5 Profiler
- **Systems to Profile**:
  - AudioManager (ambient crossfades, weather layers)
  - DialogueManager (priority queue, interrupt handling)
  - LipSyncComponent (phoneme updates)
  - WeatherParticleManager (particle updates)

### Memory Budget
- **Target**: < 100MB per system
- **Measurement**: Use UE5 Memory Profiler
- **Check**: Component counts, audio component pools, particle pools

### Audio Performance
- **Target**: < 50 audio components active simultaneously
- **Measurement**: Count active `UAudioComponent` instances
- **Check**: AudioManager component pools, DialogueManager voice pool

---

## TROUBLESHOOTING

### Issue: MetaSound templates not found
**Solution**: Verify asset paths match exactly. Check `/Game/Audio/MetaSounds/` folder.

### Issue: Reverb not working
**Solution**: 
1. Verify `UReverbEffect` assets created
2. Check `ReverbEffectMap` configuration
3. Verify `AmbientReverbSubmix` assigned in AudioManager

### Issue: Lip-sync not applying
**Solution**:
1. Verify skeletal mesh component assigned
2. Check blend shape names match (`JawOpen`, `MouthOpen`, etc.)
3. Verify `FLipSyncData` has valid phoneme frames

### Issue: Dialogue not playing
**Solution**:
1. Check AudioManager initialized
2. Verify backend URL configured
3. Check TTS backend service running (if using TTS)
4. Verify dialogue item has valid audio data or text

### Issue: IK not working
**Solution**:
1. Verify Animation Blueprint has IK nodes
2. Check bone names match (`hand_l`, `hand_r`)
3. Verify IK targets created in `BeginPlay`

---

## TEST RESULTS TEMPLATE

```markdown
# Phase 4 Runtime Test Results
**Date**: {date}
**UE Version**: 5.6.1
**Build**: {build number}

## Test Results

### VA-002 Tests
- [ ] Test 1: AudioManager Initialization
- [ ] Test 2: Time-of-Day Ambient
- [ ] Test 3: Weather Audio Layering
- [ ] Test 4: Zone Ambient Profiles
- [ ] Test 5: Reverb System

### VA-003 Tests
- [ ] Test 6: Dialogue Priority System
- [ ] Test 7: Dialogue Crossfade Interrupt
- [ ] Test 8: Dialogue Pause-Resume Interrupt
- [ ] Test 9: Lip-Sync System

### FE Tests
- [ ] Test 10: Expression System
- [ ] Test 11: Body Language IK

### WS Tests
- [ ] Test 12: Weather Particle System

### TE Tests
- [ ] Test 13: Ecosystem Integration

## Performance Results
- CPU Usage: {percentage}%
- Memory Usage: {MB}MB
- Audio Components: {count}

## Issues Found
{List any issues}

## Notes
{Additional notes}
```

---

## NEXT STEPS AFTER TESTING

1. **Fix Issues**: Address any runtime issues found
2. **Performance Optimization**: Optimize any systems exceeding budgets
3. **Integration Testing**: Test all systems together
4. **Documentation**: Update architecture docs with runtime findings
5. **Production Readiness**: Verify all systems ready for production use

---

**Status**: ✅ Code Complete - Ready for Asset Creation and Runtime Testing

