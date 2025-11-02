# MetaHuman Integration Architecture
**Date**: 2025-01-29  
**Task**: FE-002 - MetaHuman Integration  
**Status**: Design Complete

---

## OVERVIEW

Complete MetaHuman integration architecture for facial control, eye tracking, blinking, and micro-expressions, built on top of ExpressionManager and integrated with lip-sync.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **ExpressionManager** (`docs/ExpressionManager-Core-Architecture.md`)
   - 8 primary emotions
   - Blending system
   - Transition interpolation
   - Personality modulation

2. **Lip-Sync System** (VA-003)
   - Phoneme/viseme mappings
   - Blendshape targets
   - Facial animation hooks

3. **MetaHuman Framework** (UE5)
   - Control Rig system
   - Blendshape morph targets
   - Facial rig hierarchy

---

## CONTROL RIG INTEGRATION

### Facial Control Setup

**Control Rig Hierarchy**:
```
Face_Root
├── UpperFace
│   ├── Eyebrows
│   ├── Eyes
│   └── Forehead
├── MiddleFace
│   ├── Nose
│   └── Cheeks
└── LowerFace
    ├── Mouth
    ├── Jaw
    └── Chin
```

**Standard Blendshapes**:
```cpp
// Upper face
TArray<FString> UpperFaceBlendshapes = {
    "eyebrow_raise_left", "eyebrow_raise_right",
    "eyebrow_furrow_left", "eyebrow_furrow_right",
    "eye_wide_left", "eye_wide_right",
    "eye_squint_left", "eye_squint_right",
    "eye_closed_left", "eye_closed_right",
    "forehead_wrinkle"
};

// Middle face
TArray<FString> MiddleFaceBlendshapes = {
    "nose_scrunch",
    "cheek_puff_left", "cheek_puff_right",
    "cheek_suck_left", "cheek_suck_right"
};

// Lower face
TArray<FString> LowerFaceBlendshapes = {
    "jaw_open", "jaw_left", "jaw_right",
    "lip_pucker", "lip_stretch_left", "lip_stretch_right",
    "mouth_smile", "mouth_frown",
    "mouth_wide", "mouth_narrow",
    "tongue_out", "tongue_up"
};
```

---

## EYE TRACKING SYSTEM

### Gaze Targeting Architecture

**Eye Control Component**:
```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UEyeTrackingComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    // Set look-at target
    UFUNCTION(BlueprintCallable, Category = "Eye Tracking")
    void SetLookAtTarget(AActor* Target);
    
    UFUNCTION(BlueprintCallable, Category = "Eye Tracking")
    void SetLookAtLocation(FVector TargetLocation);
    
    // Clear tracking
    UFUNCTION(BlueprintCallable, Category = "Eye Tracking")
    void ClearLookAt();

    // Tracking properties
    UFUNCTION(BlueprintCallable, Category = "Eye Tracking")
    void SetTrackingSpeed(float DegreesPerSecond);
    
    UFUNCTION(BlueprintCallable, Category = "Eye Tracking")
    void SetMaxTrackingAngle(float MaxAngle);

private:
    // Current target
    UPROPERTY()
    AActor* CurrentTarget;
    
    UPROPERTY()
    FVector CurrentTargetLocation;
    
    // Tracking limits
    UPROPERTY()
    float TrackingSpeed;  // Degrees per second
    
    UPROPERTY()
    float MaxAngle;  // Max eye rotation in degrees
    
    // Current eye rotation
    UPROPERTY()
    FRotator CurrentEyeRotation;
    
    // Smooth targeting
    void UpdateEyeTracking(float DeltaTime);
    
    // Compute target direction
    FVector GetTargetDirection() const;
};
```

### Smooth Tracking Logic

**Interpolation System**:
```cpp
void UpdateEyeTracking(float DeltaTime)
{
    if (!CurrentTarget && CurrentTargetLocation.IsZero())
    {
        // Return to neutral
        CurrentEyeRotation = FRotator::ZeroRotator;
        return;
    }
    
    FVector TargetDirection = GetTargetDirection();
    FRotator TargetRotation = TargetDirection.Rotation();
    
    // Clamp to max angle
    TargetRotation.Pitch = FMath::ClampAngle(TargetRotation.Pitch, -MaxAngle, MaxAngle);
    TargetRotation.Yaw = FMath::ClampAngle(TargetRotation.Yaw, -MaxAngle, MaxAngle);
    
    // Smooth interpolation
    float DegreesToRotate = FMath::DegreesToRadians(TrackingSpeed * DeltaTime);
    CurrentEyeRotation = FMath::RInterpTo(
        CurrentEyeRotation,
        TargetRotation,
        DeltaTime,
        TrackingSpeed
    );
    
    // Apply to Control Rig
    ApplyEyeRotation(CurrentEyeRotation);
}
```

**Target Selection**:
```cpp
FVector GetTargetDirection() const
{
    FVector EyeLocation = GetOwner()->GetActorLocation() + FVector(0, 0, 160);  // Eye height
    
    if (CurrentTarget)
    {
        FVector TargetLocation = CurrentTarget->GetActorLocation();
        return (TargetLocation - EyeLocation).GetSafeNormal();
    }
    else if (!CurrentTargetLocation.IsZero())
    {
        return (CurrentTargetLocation - EyeLocation).GetSafeNormal();
    }
    
    return FVector::ForwardVector;
}
```

### Typical Settings

**Tracking Parameters**:
```cpp
TrackingSpeed = 90.0f;  // Degrees per second (quick but natural)
MaxAngle = 45.0f;       // Max eye movement (realistic)
```

---

## BLINK SYSTEM

### Automatic Blinking

**Blink Timing**:
```cpp
class UBlinkComponent : public UActorComponent
{
    GENERATED_BODY()

private:
    // Blink timing
    UPROPERTY()
    float MinBlinkInterval;  // 2-5 seconds
    
    UPROPERTY()
    float MaxBlinkInterval;  // 5-8 seconds
    
    UPROPERTY()
    float BlinkDuration;     // 0.1-0.2 seconds
    
    // Current state
    UPROPERTY()
    float TimeSinceLastBlink;
    
    UPROPERTY()
    float NextBlinkTime;
    
    UPROPERTY()
    bool bIsBlinking;
    
    // Update
    void UpdateBlinking(float DeltaTime);
    
    // Trigger blink
    void TriggerBlink();
};

void UpdateBlinking(float DeltaTime)
{
    if (bIsBlinking)
    {
        // Animate blink closing/opening
        float BlinkProgress = /* elapsed / BlinkDuration */;
        
        if (BlinkProgress >= 1.0f)
        {
            bIsBlinking = false;
            TimeSinceLastBlink = 0.0f;
            NextBlinkTime = FMath::RandRange(MinBlinkInterval, MaxBlinkInterval);
        }
    }
    else
    {
        TimeSinceLastBlink += DeltaTime;
        
        if (TimeSinceLastBlink >= NextBlinkTime)
        {
            TriggerBlink();
        }
    }
}
```

---

## MICRO-EXPRESSION SYSTEM

### Subtle Facial Movements

**Micro-Expression Types**:
```cpp
enum class EMicroExpressionType
{
    None,
    EyeTwitch,      // Subtle eye flutter
    LipTwitch,      // Subtle mouth movement
    NostrilFlare,   // Nose movement
    EyebrowTick,    // Brief eyebrow raise
    JawShift,       // Subtle jaw movement
    FacialTension   // Overall tension increase
};

class UMicroExpressionComponent : public UActorComponent
{
    GENERATED_BODY()

private:
    // Trigger micro-expression
    UFUNCTION(BlueprintCallable, Category = "Micro Expression")
    void TriggerMicroExpression(EMicroExpressionType Type, float Intensity = 0.3f);
    
    // Personality-based micro-expressions
    void UpdateMicroExpressions(float DeltaTime);
};
```

**Micro-Expression Triggers**:
```cpp
void TriggerMicroExpression(EMicroExpressionType Type, float Intensity)
{
    TMap<FString, float> Blendshapes;
    
    switch (Type)
    {
        case EMicroExpressionType::EyeTwitch:
            Blendshapes.Add("eye_squint_left", Intensity * 0.3f);
            break;
        case EMicroExpressionType::LipTwitch:
            Blendshapes.Add("lip_stretch_left", Intensity * 0.2f);
            break;
        case EMicroExpressionType::NostrilFlare:
            Blendshapes.Add("nose_scrunch", Intensity * 0.4f);
            break;
        // ... other types
    }
    
    // Apply briefly (0.1-0.3 seconds)
    ApplyMicroExpression(Blendshapes, FMath::RandRange(0.1f, 0.3f));
}
```

---

## EXPRESSION → BLENDSHAPE MAPPING

### Complete Mapping System

**8 Emotions → Blendshapes**:
```cpp
TMap<EEmotion, TMap<FString, float>> EmotionToBlendshapes = {
    {EEmotion::Neutral, {
        {"eye_closed_left", 0.0f}, {"eye_closed_right", 0.0f},
        {"mouth_smile", 0.0f}, {"eyebrow_furrow_left", 0.0f}
    }},
    
    {EEmotion::Happy, {
        {"mouth_smile", 0.8f}, {"eye_squint_left", 0.5f},
        {"eye_squint_right", 0.5f}, {"cheek_puff_left", 0.3f},
        {"cheek_puff_right", 0.3f}
    }},
    
    {EEmotion::Sad, {
        {"mouth_frown", 0.7f}, {"eyebrow_furrow_left", 0.6f},
        {"eyebrow_furrow_right", 0.6f}, {"eyebrow_raise_inner", 0.4f}
    }},
    
    {EEmotion::Angry, {
        {"eyebrow_furrow_left", 0.9f}, {"eyebrow_furrow_right", 0.9f},
        {"eyebrow_lower", 0.8f}, {"nose_scrunch", 0.5f},
        {"mouth_tight", 0.7f}
    }},
    
    {EEmotion::Fear, {
        {"eyebrow_raise_left", 0.8f}, {"eyebrow_raise_right", 0.8f},
        {"eye_wide_left", 0.9f}, {"eye_wide_right", 0.9f},
        {"mouth_wide", 0.6f}
    }},
    
    {EEmotion::Surprise, {
        {"eyebrow_raise_left", 0.9f}, {"eyebrow_raise_right", 0.9f},
        {"eye_wide_left", 1.0f}, {"eye_wide_right", 1.0f},
        {"jaw_open", 0.5f}
    }},
    
    {EEmotion::Disgust, {
        {"nose_scrunch", 0.8f}, {"eyebrow_lower", 0.6f},
        {"mouth_upper_raise", 0.7f}, {"cheek_suck_left", 0.4f}
    }},
    
    {EEmotion::Contempt, {
        {"mouth_asymmetrical", 0.8f}, {"eyebrow_raise_inner", 0.5f},
        {"nose_scrunch", 0.3f}
    }}
};
```

---

## CONTROL RIG INTEGRATION

### Facial Control Component

**Complete System**:
```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UMetaHumanFacialComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    // Initialize with MetaHuman
    UFUNCTION(BlueprintCallable, Category = "MetaHuman")
    void InitializeWithMetaHuman(UMetahumanAsset* MetaHuman);
    
    // Apply blendshape weights
    UFUNCTION(BlueprintCallable, Category = "MetaHuman")
    void ApplyBlendshapes(const TMap<FString, float>& Blendshapes);
    
    // Eye tracking
    UFUNCTION(BlueprintCallable, Category = "MetaHuman")
    void SetLookAtTarget(AActor* Target);
    
    // Lip-sync
    UFUNCTION(BlueprintCallable, Category = "MetaHuman")
    void UpdateLipSync(const TMap<FString, float>& LipSyncBlendshapes);

private:
    // Control Rig reference
    UPROPERTY()
    UControlRigComponent* FacialControlRig;
    
    // Current blendshape weights
    UPROPERTY()
    TMap<FString, float> CurrentBlendshapes;
    
    // Apply to Control Rig
    void ApplyWeightsToControlRig();
};
```

**Blendshape Application**:
```cpp
void ApplyBlendshapes(const TMap<FString, float>& Blendshapes)
{
    // Merge with current (for layered effects)
    for (auto& KV : Blendshapes)
    {
        CurrentBlendshapes[KV.Key] = KV.Value;
    }
    
    // Clamp all values
    for (auto& KV : CurrentBlendshapes)
    {
        CurrentBlendshapes[KV.Key] = FMath::Clamp(KV.Value, 0.0f, 1.0f);
    }
    
    // Apply to Control Rig
    ApplyWeightsToControlRig();
}

void ApplyWeightsToControlRig()
{
    if (!FacialControlRig) return;
    
    // Set blendshape control values
    for (auto& KV : CurrentBlendshapes)
    {
        FacialControlRig->SetControlValue(KV.Key, KV.Value);
    }
}
```

---

## CROSS-CHARACTER COMPATIBILITY

### Universal Blendshape Mapping

**Abstraction Layer**:
```cpp
class UFacialMappingManager : public UObject
{
    GENERATED_BODY()

public:
    // Register character mapping
    UFUNCTION(BlueprintCallable, Category = "Facial Mapping")
    void RegisterCharacterMapping(const FString& CharacterID, const TMap<FString, FString>& Mapping);
    
    // Translate universal → character-specific
    UFUNCTION(BlueprintCallable, Category = "Facial Mapping")
    TMap<FString, float> TranslateBlendshapes(const FString& CharacterID, const TMap<FString, float>& UniversalBlendshapes);

private:
    // Character-specific mappings
    UPROPERTY()
    TMap<FString, TMap<FString, FString>> CharacterMappings;
};
```

**Mapping Example**:
```cpp
// Universal blendshape → Character-specific blendshape
TMap<FString, FString> Mapping = {
    {"mouth_smile", "MH_Mouth_Smile"},
    {"eyebrow_furrow_left", "MH_Eyebrow_Furrow_L"},
    {"eye_squint_left", "MH_Eye_Squint_L"}
    // ... all mappings
};
```

---

## PERFORMANCE BUDGET

### Facial System Budget

**Target**: 0.15ms CPU per NPC per frame

**Breakdown**:
- Blendshape updates: 0.05ms
- Eye tracking: 0.05ms
- Blink system: 0.02ms
- Micro-expressions: 0.03ms

**Memory**: ~10KB per MetaHuman

---

## BLUEPRINT API

### Designer Functions

```cpp
// Initialize
UFUNCTION(BlueprintCallable, Category = "MetaHuman")
void InitializeWithMetaHuman(UMetahumanAsset* MetaHuman);

// Expression control
UFUNCTION(BlueprintCallable, Category = "MetaHuman")
void ApplyExpression(const TMap<FString, float>& Blendshapes);

// Eye tracking
UFUNCTION(BlueprintCallable, Category = "MetaHuman")
void LookAtActor(AActor* Target);

UFUNCTION(BlueprintCallable, Category = "MetaHuman")
void LookAtLocation(FVector Location);

UFUNCTION(BlueprintCallable, Category = "MetaHuman")
void StopLooking();

// Lip-sync
UFUNCTION(BlueprintCallable, Category = "MetaHuman")
void PlayLipSync(const FLipSyncData& Data);
```

---

## INTEGRATION WITH EXPRESSIONMANAGER

### Subscription Pattern

**Event Connection**:
```cpp
// In NPC setup
ExpressionManager->OnExpressionChanged.AddDynamic(MetaHumanComponent, &UMetaHumanFacialComponent::HandleExpressionChange);

void HandleExpressionChange(FEmotionalState State, TMap<FString, float> Blendshapes)
{
    // Apply to MetaHuman
    ApplyBlendshapes(Blendshapes);
}
```

---

**Status**: ✅ **METAHUMAN INTEGRATION ARCHITECTURE COMPLETE**



