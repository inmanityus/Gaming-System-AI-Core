# Phase 4 Quick Reference Card
**Date**: 2025-01-29  
**Status**: ✅ Code Complete - Ready for Testing

---

## 🚀 QUICK START

### 1. Open Project in UE5 Editor
```powershell
# Navigate to project
cd "E:\Vibe Code\Gaming System\AI Core\unreal"

# Open in UE5 Editor
& "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe" "BodyBroker.uproject"
```

### 2. Verify Compilation
- Project should compile without errors
- Check Output Log for any warnings
- All Phase 4 modules should load

### 3. Create Test Blueprint
- Create `BP_Phase4TestActor` Blueprint
- Add all Phase 4 components (see full guide)
- Configure component properties

### 4. Create Required Assets
- Follow asset creation checklist in `docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md`
- Start with MetaSound templates (most critical)
- Then create reverb effects, animation blueprints, etc.

---

## 📋 CRITICAL ASSETS (Priority Order)

### Priority 1: Audio Assets
1. **MetaSound Templates** (18 assets)
   - Time-of-day: `MS_DawnAmbient`, `MS_DayAmbient`, `MS_DuskAmbient`, `MS_NightAmbient`
   - Weather: `MS_Weather_Rain`, `MS_Weather_Snow`, `MS_Weather_Thunder`, etc.
   - Location: `/Game/Audio/MetaSounds/`

2. **Reverb Effects** (6 assets)
   - `RE_Interior_Small`, `RE_Interior_Large`, `RE_Exterior_Open`, etc.
   - Location: `/Game/Audio/Reverb/`
   - Configure in AudioManager `ReverbEffectMap`

### Priority 2: Animation Assets
3. **Animation Blueprints** (2 assets)
   - `ABP_BodyLanguage` - Body language animations
   - `ABP_MetaHumanExpression` - Facial expressions
   - Location: `/Game/Animation/AnimBlueprints/`

4. **Gesture Montages** (4+ assets)
   - `AM_Gesture_Wave`, `AM_Gesture_Point`, etc.
   - Location: `/Game/Animation/Montages/Gestures/`

### Priority 3: Data Assets
5. **Expression Preset Data Table**
   - `DT_ExpressionPresets`
   - Location: `/Game/Data/Expressions/`

6. **Gesture Data Table**
   - Structure: `FGestureData` (GestureName → Montage)
   - Location: `/Game/Data/Gestures/`

### Priority 4: Visual Effects
7. **Niagara Particle Systems** (4 assets)
   - `NS_Weather_Rain`, `NS_Weather_Snow`, `NS_Weather_Fog`, `NS_Weather_Lightning`
   - Location: `/Game/VFX/Weather/`

8. **Material Instances** (Flora)
   - With parameters: `SeasonProgress`, `WindStrength`, `WindDirection`
   - Location: `/Game/Materials/Flora/`

9. **Biome Data Assets**
   - `DA_Biome_Forest`, `DA_Biome_Desert`, etc.
   - Location: `/Game/Data/Biomes/`

---

## 🔧 KEY CONFIGURATION

### AudioManager Setup
```cpp
// In Blueprint or C++ initialization
AudioManager->Initialize("http://localhost:4000");
AudioManager->SetMasterVolume(1.0f);
AudioManager->SetCategoryVolume(EAudioCategory::Ambient, 0.8f);
AudioManager->SetCategoryVolume(EAudioCategory::Music, 0.7f);
AudioManager->SetCategoryVolume(EAudioCategory::Voice, 1.0f);

// Configure reverb map
AudioManager->ReverbEffectMap.Add("interior_small", ReverbAsset);
AudioManager->ReverbPresetLevels.Add("interior_small", 0.6f);
```

### DialogueManager Setup
```cpp
// Get subsystem from GameInstance
UDialogueManager* DialogueManager = GetWorld()->GetGameInstance()->GetSubsystem<UDialogueManager>();

// Initialize (if needed)
DialogueManager->Initialize();

// Set AudioManager reference
DialogueManager->SetAudioManager(AudioManager);
```

### Component Setup
```cpp
// LipSyncComponent
LipSyncComponent->SetLipSyncEnabled(true);
LipSyncComponent->FindSkeletalMeshComponent(); // Auto-finds on actor

// BodyLanguageComponent
BodyLanguageComponent->LeftHandIKBoneName = "hand_l";
BodyLanguageComponent->RightHandIKBoneName = "hand_r";
BodyLanguageComponent->GestureDataTable = GestureDataTableAsset;

// ExpressionManagerComponent
ExpressionManagerComponent->ExpressionPresetDataTable = ExpressionDataTableAsset;
```

---

## 🧪 QUICK TEST SEQUENCE

### Test 1: AudioManager Basic
```
1. Spawn BP_Phase4TestActor
2. Get AudioManager Component
3. Call: SetTimeOfDayAmbient("day")
4. Verify: Day ambient plays
```

### Test 2: Dialogue Basic
```
1. Get DialogueManager Subsystem
2. Create FDialogueItem:
   - Text: "Hello, world!"
   - Priority: 2
   - NPCID: "test_npc"
3. Call: PlayDialogue(Item)
4. Verify: Dialogue plays (or requests TTS)
```

### Test 3: Lip-Sync Basic
```
1. Get LipSyncComponent
2. Create FLipSyncData with test phonemes
3. Call: StartLipSync(LipSyncData)
4. Verify: Visemes apply to mesh
```

---

## 📊 BLUEPRINT FUNCTION REFERENCE

### AudioManager (24 functions)
- `SetTimeOfDayAmbient(TimeState)`
- `SetWeatherAudioLayer(WeatherState, Intensity)`
- `SetZoneAmbientProfile(ZoneName)`
- `SetReverbPreset(PresetName, Duration)`
- `PlayThunderStrike(Volume)`
- `DuckAudioByAmount(Category, Amount, Duration)`
- `SetMasterVolume(Volume)`
- `SetCategoryVolume(Category, Volume)`
- `PlayAudioFromBackend(AudioID, Category, Volume)`
- `PauseAudio(AudioID)` / `ResumeAudio(AudioID)`
- `SetVolumeOverTime(AudioID, TargetVolume, Duration)`
- `IsAudioPlaying(AudioID)`
- `GetAudioComponent(AudioID)`

### DialogueManager (12+ functions)
- `PlayDialogue(DialogueItem)`
- `StopDialogue(DialogueID)`
- `StopDialogueByNPC(NPCID)`
- `IsDialoguePlaying(DialogueID)`
- `GetDialogueQueueStatus()`
- `RequestNPCDialogue(NPCID, Text, Priority, ...)`
- `GetLipSyncData(DialogueID)`

### LipSyncComponent (5 functions)
- `StartLipSync(LipSyncData)`
- `StopLipSync()`
- `ExtractPhonemesFromAudio(AudioComponent, OutLipSyncData)`
- `SetLipSyncEnabled(Enabled)`

### BodyLanguageComponent (6 functions)
- `PlayGesture(GestureName)`
- `StopGesture()`
- `SetEmotionalState(Emotion, Intensity)`
- `SetHandPosition(LeftPos, RightPos)`
- `SetIdleVariation(VariationIndex)`

### ExpressionManagerComponent (5 functions)
- `SetEmotionalState(Emotion, Intensity)`
- `BlendEmotions(Emotions, Weights)`
- `LoadExpressionPreset(PresetName)`
- `ApplyBlendShapeWeights(Weights)`

---

## 🐛 COMMON ISSUES & FIXES

### Issue: "MetaSound template not found"
**Fix**: Verify asset exists at `/Game/Audio/MetaSounds/{TemplateName}.{TemplateName}`

### Issue: "Reverb not working"
**Fix**: 
1. Create `UReverbEffect` assets
2. Add to `ReverbEffectMap` in AudioManager
3. Configure `ReverbPresetLevels`

### Issue: "Dialogue not playing"
**Fix**:
1. Check AudioManager initialized
2. Verify backend URL set
3. Check TTS service running (if using)

### Issue: "Lip-sync not applying"
**Fix**:
1. Verify skeletal mesh component assigned
2. Check blend shape names match
3. Verify `FLipSyncData` has valid frames

---

## 📚 FULL DOCUMENTATION

- **Runtime Testing Guide**: `docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md`
- **Readiness Report**: `docs/issues/PHASE4-READINESS-REPORT.md`
- **Final Status**: `docs/issues/PHASE4-FINAL-STATUS.md`
- **Complete Fix Summary**: `docs/issues/PHASE4-COMPLETE-FIX-SUMMARY.md`
- **Architecture Docs**: `docs/architecture/VA-002-*.md`, `docs/architecture/VA-003-*.md`

---

## ✅ VERIFICATION CHECKLIST

Before starting runtime tests:
- [x] Project compiles successfully
- [x] All Phase 4 code implemented
- [x] No compilation errors
- [ ] MetaSound templates created (18 assets)
- [ ] Reverb effects created (6 assets)
- [ ] Animation blueprints created (2 assets)
- [ ] Test Blueprint created (`BP_Phase4TestActor`)
- [ ] Components configured in test Blueprint
- [ ] Backend services running (TTS, optional phoneme extraction)

---

**Status**: ✅ Code Complete - Ready for Asset Creation & Runtime Testing

