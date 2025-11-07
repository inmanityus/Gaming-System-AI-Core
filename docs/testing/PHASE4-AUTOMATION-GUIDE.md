# Phase 4 UE5 Editor Automation Guide
**Date**: 2025-01-29  
**Status**: ✅ Scripts Created - Ready for Execution

---

## OVERVIEW

This guide provides step-by-step instructions for using the automated Python scripts to create Phase 4 assets and run runtime tests in UE5 Editor.

---

## PREREQUISITES

- ✅ UE5 5.6.1 installed (`C:\Program Files\Epic Games\UE_5.6`)
- ✅ Project compiles successfully
- ✅ Python Script Plugin enabled in UE5 (already verified)

---

## STEP 1: LAUNCH UE5 EDITOR

### Option A: Manual Launch
1. Navigate to project folder: `E:\Vibe Code\Gaming System\AI Core\unreal`
2. Double-click `BodyBroker.uproject`
3. Wait for UE5 Editor to fully load

### Option B: Command Line Launch
```powershell
& "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe" "E:\Vibe Code\Gaming System\AI Core\unreal\BodyBroker.uproject"
```

---

## STEP 2: OPEN PYTHON CONSOLE

1. In UE5 Editor, go to: **Window > Developer Tools > Python Console**
2. The Python Console window will open
3. You can now execute Python scripts directly

---

## STEP 3: RUN ASSET CREATION SCRIPT

### Quick Test First
Run this to verify Python console is working:
```python
import unreal
print("UE5 Python API loaded successfully!")
```

### Create Assets
Run the asset creation script:
```python
exec(open(r'E:\Vibe Code\Gaming System\AI Core\unreal\Scripts\create_phase4_assets.py').read())
```

**What This Does**:
- Creates directory structure (`/Game/Audio/MetaSounds`, `/Game/Audio/Reverb`, etc.)
- Creates `UReverbEffect` assets (6 assets)
- Creates `BP_Phase4TestActor` Blueprint
- Creates `Phase4TestLevel`
- Provides instructions for manual asset creation (MetaSounds, Data Tables)

**Expected Output**:
```
============================================================
Phase 4 Asset Creation Script
============================================================
Creating MetaSound templates...
  ⚠ MS_DawnAmbient - MetaSound creation requires editor UI...
Creating Reverb Effect assets...
  ✓ Created RE_Interior_Small
  ✓ Created RE_Interior_Large
  ...
============================================================
Asset Creation Summary
============================================================
```

---

## STEP 4: MANUAL ASSET CREATION

Some assets require manual creation in UE5 Editor UI:

### A. MetaSound Templates (18 assets)

**Location**: `/Game/Audio/MetaSounds/`

**Steps**:
1. Right-click in Content Browser → **Audio > MetaSound**
2. Create MetaSound graphs for:
   - `MS_DawnAmbient` - Looping dawn ambient
   - `MS_DayAmbient` - Looping day ambient
   - `MS_DuskAmbient` - Looping dusk ambient
   - `MS_NightAmbient` - Looping night ambient
   - `MS_Weather_Rain` - Looping rain layer
   - `MS_Weather_Snow` - Looping snow layer
   - `MS_Weather_Thunder` - One-shot thunder strike
   - (See full list in `docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md`)

**Note**: For quick testing, you can use placeholder `USoundWave` assets instead of MetaSounds initially.

### B. Data Tables

**Expression Preset Data Table**:
1. Right-click in `/Game/Data/Expressions/`
2. **Create > Miscellaneous > Data Table**
3. Set **Row Structure** to `FExpressionPresetRow`
4. Name: `DT_ExpressionPresets`
5. Add rows: Happy, Sad, Angry, Surprised, etc.
6. Configure blend shape weights for each row

**Gesture Data Table**:
1. Right-click in `/Game/Data/Gestures/`
2. **Create > Miscellaneous > Data Table**
3. Set **Row Structure** to `FGestureData`
4. Name: `DT_GesturePresets`
5. Add rows: Wave, Point, ThumbsUp, Shrug, etc.
6. Assign gesture montages to each row

### C. Configure BP_Phase4TestActor

1. Open `BP_Phase4TestActor` in Blueprint Editor
2. Add Components:
   - **AudioManager** (Component)
   - **LipSyncComponent** (Component)
   - **BodyLanguageComponent** (Component)
   - **MetaHumanExpressionComponent** (Component)
   - **ExpressionManagerComponent** (Component)
   - **WeatherParticleManager** (Component)
   - **WeatherMaterialManager** (Component)
3. Configure Component Properties:
   - **AudioManager**: Set backend URL, assign reverb submix
   - **LipSyncComponent**: Assign skeletal mesh component reference
   - **BodyLanguageComponent**: Assign gesture data table, set IK bone names
   - **ExpressionManagerComponent**: Assign expression preset data table

---

## STEP 5: RUN RUNTIME TESTS

### Quick Test
Run quick verification:
```python
exec(open(r'E:\Vibe Code\Gaming System\AI Core\unreal\Scripts\quick_test_phase4.py').read())
```

### Full Test Suite
1. Open `Phase4TestLevel` (or create new level)
2. Spawn `BP_Phase4TestActor` in the level
3. Run full test suite:
```python
exec(open(r'E:\Vibe Code\Gaming System\AI Core\unreal\Scripts\run_phase4_tests.py').read())
```

**Expected Output**:
```
============================================================
Phase 4 Runtime Testing
============================================================

============================================================
Test 1: AudioManager Initialization
============================================================
  ✓ AudioManager initialized
  ✓ Current time-of-day state: day

============================================================
Test 2: Time-of-Day Ambient
============================================================
  → Setting time-of-day to 'dawn'...
  ✓ Dawn ambient set
  → Setting time-of-day to 'day' (should crossfade)...
  ✓ Day ambient set (crossfade in progress)

============================================================
Test Results Summary
============================================================
Test 1: AudioManager Init: ✓ PASS
Test 2: Time-of-Day Ambient: ✓ PASS
...
Total: 5/5 tests passed

✅ All tests passed!
```

---

## TROUBLESHOOTING

### Issue: Python Console Not Available
**Solution**: Enable Python Script Plugin
1. **Edit > Plugins**
2. Search for "Python Script Plugin"
3. Enable it
4. Restart UE5 Editor

### Issue: Script Execution Errors
**Solution**: Check script paths
- Ensure paths use raw strings: `r'E:\Vibe Code\...'`
- Use forward slashes or double backslashes in paths
- Verify scripts exist at specified locations

### Issue: Assets Not Created
**Solution**: Check Output Log
1. **Window > Developer Tools > Output Log**
2. Look for Python script errors
3. Check that directories exist before creating assets

### Issue: Components Not Found
**Solution**: Verify Component Classes
- Ensure C++ classes are compiled
- Check that components are added to test actor
- Verify component class names match (`AudioManager`, `LipSyncComponent`, etc.)

---

## ALTERNATIVE: MANUAL TESTING

If Python scripts don't work, you can test manually:

### Test AudioManager
1. Spawn `BP_Phase4TestActor`
2. In Blueprint Editor, add Event BeginPlay
3. Call `AudioManager->SetTimeOfDayAmbient("day")`
4. Verify audio plays

### Test DialogueManager
1. Get DialogueManager subsystem from GameInstance
2. Create `FDialogueItem` structure
3. Call `PlayDialogue(Item)`
4. Verify dialogue plays or TTS request sent

### Test Lip-Sync
1. Get `LipSyncComponent` from test actor
2. Create `FLipSyncData` with test phonemes
3. Call `StartLipSync(LipSyncData)`
4. Verify visemes apply to skeletal mesh

---

## NEXT STEPS AFTER TESTING

1. **Fix Issues**: Address any runtime issues found
2. **Performance Optimization**: Profile systems, optimize bottlenecks
3. **Integration Testing**: Test all systems together
4. **Documentation**: Update architecture docs with findings
5. **Production Readiness**: Verify systems ready for production

---

## QUICK REFERENCE

**Script Locations**:
- Asset Creation: `unreal/Scripts/create_phase4_assets.py`
- Runtime Tests: `unreal/Scripts/run_phase4_tests.py`
- Quick Test: `unreal/Scripts/quick_test_phase4.py`

**Python Console Commands**:
```python
# Load script
exec(open(r'FULL_PATH_TO_SCRIPT').read())

# Quick test
import unreal
print(unreal.AudioManager)

# Check actors in level
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for actor in actors:
    print(actor.get_name())
```

---

**Status**: ✅ Scripts Ready - Execute in UE5 Editor Python Console

