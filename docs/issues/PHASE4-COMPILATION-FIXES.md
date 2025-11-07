# Phase 4 Compilation Fixes - In Progress

## Issues Found During UE 5.6.1 Compilation

### 1. FFadeState Struct ✅ FIXED
- Moved outside class, added USTRUCT()
- Fixed declaration order (after EAudioCategory)

### 2. OnAudioFinished Delegate Binding ❌ NEEDS FIX
- `FOnAudioFinished` is a DYNAMIC multicast delegate
- Cannot use `AddUObject` - must use `AddDynamic` or lambda
- Need to add callback function that looks up DialogueID from AudioComponent

### 3. FPhonemeFrame Fields ❌ NEEDS FIX
- Struct has `Time` field
- Code tries to use `StartTime` and `Duration`
- Need to either add fields or change code to use `Time`

### 4. Lambda Capture Issue ❌ NEEDS FIX
- `Item` is const in lambda but code tries to modify `Item.WordTimings`
- Need to capture by reference or use mutable lambda

### 5. WeatherParticleManager ❌ NEEDS FIX
- Code references `ActiveParticleComponents` which doesn't exist
- Should use `NiagaraComponentPool` or iterate through individual components

### 6. Delegate Binding Issues ❌ NEEDS FIX
- `BindUObject` signature mismatches
- Need to check parameter types

