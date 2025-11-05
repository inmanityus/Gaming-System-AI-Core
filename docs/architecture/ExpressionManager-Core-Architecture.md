# ExpressionManager Core Architecture
**Date**: 2025-01-29  
**Task**: FE-001 - Core Emotion System  
**Status**: Design Complete

---

## OVERVIEW

This document defines the architecture for implementing a facial expression and emotion system that integrates with NPC personality vectors, provides smooth emotion blending, and broadcasts expression changes for visual updates.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **NPC Model** (`models/npc.py`)
   - 50-dimensional personality vector
   - Stats: health, aggression, intelligence, charisma
   - Current state tracking
   - Relationships

2. **More Requirements** (`docs/More Requirements.md`)
   - Facial emotions affect perception
   - Body language combined with facial
   - Personality influences expressions

3. **Voice/Dialogue System** (VA-003)
   - Lip-sync data pipeline
   - Phoneme/viseme mappings
   - Facial animation hooks

---

## CORE EMOTION SYSTEM

### Basic Emotions

**8 Primary Emotions**:
```cpp
UENUM(BlueprintType)
enum class EEmotion : uint8
{
    Neutral     UMETA(DisplayName = "Neutral"),
    Happy       UMETA(DisplayName = "Happy"),
    Sad         UMETA(DisplayName = "Sad"),
    Angry       UMETA(DisplayName = "Angry"),
    Fear        UMETA(DisplayName = "Fear"),
    Surprise    UMETA(DisplayName = "Surprise"),
    Disgust     UMETA(DisplayName = "Disgust"),
    Contempt    UMETA(DisplayName = "Contempt")
};
```

### Emotional Intensity

**Intensity Levels**:
```cpp
struct FEmotionIntensity
{
    float Value;  // 0.0 - 1.0
    
    // Categorization
    bool IsSubtle() const { return Value < 0.3f; }
    bool IsModerate() const { return Value >= 0.3f && Value < 0.7f; }
    bool IsStrong() const { return Value >= 0.7f; }
};
```

---

## C++ CLASS DESIGN

### ExpressionManagerComponent Header

```cpp
// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ExpressionManagerComponent.generated.h"

/**
 * Current emotional state with intensity
 */
USTRUCT(BlueprintType)
struct FEmotionalState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly)
    EEmotion PrimaryEmotion;
    
    UPROPERTY(BlueprintReadOnly)
    float PrimaryIntensity;
    
    // Secondary emotion (for blending)
    UPROPERTY(BlueprintReadOnly)
    EEmotion SecondaryEmotion;
    
    UPROPERTY(BlueprintReadOnly)
    float SecondaryIntensity;
    
    FEmotionalState()
        : PrimaryEmotion(EEmotion::Neutral)
        , PrimaryIntensity(0.0f)
        , SecondaryEmotion(EEmotion::Neutral)
        , SecondaryIntensity(0.0f)
    {}
};

/**
 * ExpressionManagerComponent
 * Manages NPC facial expressions and emotional states
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UExpressionManagerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UExpressionManagerComponent(const FObjectInitializer& ObjectInitializer);

    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // Set primary emotion
    UFUNCTION(BlueprintCallable, Category = "Expression")
    void SetEmotion(EEmotion Emotion, float Intensity = 1.0f, float TransitionDuration = 0.5f);

    // Blend two emotions
    UFUNCTION(BlueprintCallable, Category = "Expression")
    void BlendEmotions(EEmotion Emotion1, float Intensity1, EEmotion Emotion2, float Intensity2);

    // Get current emotional state
    UFUNCTION(BlueprintCallable, Category = "Expression")
    FEmotionalState GetCurrentEmotionalState() const;

    // Set personality trait modulation
    UFUNCTION(BlueprintCallable, Category = "Expression")
    void SetPersonalityTrait(const FString& TraitName, float TraitValue);

    // Events
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnEmotionChanged, EEmotion, OldEmotion, EEmotion, NewEmotion);
    UPROPERTY(BlueprintAssignable, Category = "Expression")
    FOnEmotionChanged OnEmotionChanged;

private:
    // Current emotional state
    UPROPERTY()
    FEmotionalState CurrentState;

    // Target state (for interpolation)
    UPROPERTY()
    FEmotionalState TargetState;

    // Transition progress (0.0 - 1.0)
    UPROPERTY()
    float TransitionProgress;

    // Transition duration
    UPROPERTY()
    float TransitionDuration;

    // Personality trait modulation
    UPROPERTY()
    TMap<FString, float> PersonalityTraits;

    // Update transitions
    void UpdateTransition(float DeltaTime);

    // Compute blended expression
    FEmotionalState ComputeBlendedExpression() const;

    // Broadcast events
    void BroadcastEmotionChanged();
};
```

---

## EMOTION BLENDING SYSTEM

### Blending Logic

**Primary + Secondary Blend**:
```cpp
FEmotionalState ComputeBlendedExpression() const
{
    FEmotionalState Blended;
    
    // Total intensity
    float TotalIntensity = CurrentState.PrimaryIntensity + CurrentState.SecondaryIntensity;
    
    if (TotalIntensity > 0.0f)
    {
        // Normalize
        Blended.PrimaryEmotion = CurrentState.PrimaryEmotion;
        Blended.PrimaryIntensity = CurrentState.PrimaryIntensity / TotalIntensity;
        Blended.SecondaryEmotion = CurrentState.SecondaryEmotion;
        Blended.SecondaryIntensity = CurrentState.SecondaryIntensity / TotalIntensity;
    }
    else
    {
        // Neutral
        Blended.PrimaryEmotion = EEmotion::Neutral;
        Blended.PrimaryIntensity = 1.0f;
        Blended.SecondaryEmotion = EEmotion::Neutral;
        Blended.SecondaryIntensity = 0.0f;
    }
    
    return Blended;
}
```

### Transition Interpolation

**Smooth Transitions**:
```cpp
void UpdateTransition(float DeltaTime)
{
    if (TransitionProgress < 1.0f)
    {
        TransitionProgress += DeltaTime / TransitionDuration;
        TransitionProgress = FMath::Clamp(TransitionProgress, 0.0f, 1.0f);
        
        // Interpolate primary emotion
        float Alpha = FMath::SmoothStep(0.0f, 1.0f, TransitionProgress);
        CurrentState.PrimaryEmotion = TargetState.PrimaryEmotion;
        CurrentState.PrimaryIntensity = FMath::Lerp(
            CurrentState.PrimaryIntensity,
            TargetState.PrimaryIntensity,
            Alpha
        );
        
        // Broadcast if transition complete
        if (TransitionProgress >= 1.0f)
        {
            BroadcastEmotionChanged();
        }
    }
}
```

---

## PERSONALITY MODULATION

### Personality → Expression Mapping

**Modulation Factors**:
```cpp
// Personality traits affect expression intensity
float ComputePersonalityModulation(EEmotion Emotion) const
{
    float Modulation = 1.0f;
    
    // Example mappings
    if (Emotion == EEmotion::Angry)
    {
        float Aggression = PersonalityTraits.FindRef("aggression");
        Modulation *= Aggression;  // More aggressive = stronger angry
    }
    else if (Emotion == EEmotion::Happy)
    {
        float Charisma = PersonalityTraits.FindRef("charisma");
        Modulation *= Charisma;  // More charismatic = brighter smile
    }
    else if (Emotion == EEmotion::Fear)
    {
        float Cowardice = PersonalityTraits.FindRef("cowardice");
        Modulation *= Cowardice;  // More cowardly = more fearful
    }
    
    return FMath::Clamp(Modulation, 0.0f, 2.0f);
}
```

### Update with Personality

```cpp
void SetEmotion(EEmotion Emotion, float Intensity, float TransitionDuration)
{
    // Apply personality modulation
    float PersonalityModulation = ComputePersonalityModulation(Emotion);
    float AdjustedIntensity = Intensity * PersonalityModulation;
    
    // Set target
    TargetState.PrimaryEmotion = Emotion;
    TargetState.PrimaryIntensity = FMath::Clamp(AdjustedIntensity, 0.0f, 1.0f);
    TransitionDuration = TransitionDuration;
    TransitionProgress = 0.0f;
}
```

---

## EXPRESSION PRESET SYSTEM

### Preset Data Structure

```cpp
USTRUCT(BlueprintType)
struct FExpressionPreset
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString PresetName;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    EEmotion PrimaryEmotion;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float PrimaryIntensity;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    EEmotion SecondaryEmotion;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float SecondaryIntensity;
    
    // Blendshape weights for this preset
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, float> BlendshapeWeights;
};
```

### Preset Library

**Common Presets**:
```cpp
// Data table structure
static TMap<EEmotion, FExpressionPreset> EmotionPresets = {
    {EEmotion::Neutral, {
        .PrimaryEmotion = EEmotion::Neutral,
        .PrimaryIntensity = 0.0f,
        .BlendshapeWeights = {{"jaw_open", 0.0}, {"eyebrow_raise", 0.0}}
    }},
    {EEmotion::Happy, {
        .PrimaryEmotion = EEmotion::Happy,
        .PrimaryIntensity = 0.7f,
        .BlendshapeWeights = {{"mouth_smile", 0.8}, {"eye_squint", 0.5}}
    }},
    {EEmotion::Angry, {
        .PrimaryEmotion = EEmotion::Angry,
        .PrimaryIntensity = 0.8f,
        .BlendshapeWeights = {{"eyebrow_furrow", 0.9}, {"mouth_frown", 0.7}}
    }},
    {EEmotion::Fear, {
        .PrimaryEmotion = EEmotion::Fear,
        .PrimaryIntensity = 0.6f,
        .BlendshapeWeights = {{"eyebrow_raise", 0.8}, {"eye_wide", 0.9}}
    }}
    // ... other emotions
};
```

---

## BLENDSHAPE MAPPING

### Emotion → Blendshape Translation

**Standard Blendshapes**:
```cpp
TMap<EEmotion, TMap<FString, float>> ComputeBlendshapeWeights(const FEmotionalState& State) const
{
    TMap<FString, float> Blendshapes;
    
    // Get primary emotion presets
    auto PrimaryPreset = EmotionPresets.Find(State.PrimaryEmotion);
    if (PrimaryPreset)
    {
        // Apply primary with intensity
        for (auto& KV : PrimaryPreset->BlendshapeWeights)
        {
            Blendshapes[KV.Key] = KV.Value * State.PrimaryIntensity;
        }
    }
    
    // Blend secondary if present
    if (State.SecondaryIntensity > 0.0f)
    {
        auto SecondaryPreset = EmotionPresets.Find(State.SecondaryEmotion);
        if (SecondaryPreset)
        {
            for (auto& KV : SecondaryPreset->BlendshapeWeights)
            {
                // Blend with existing
                Blendshapes[KV.Key] = FMath::Max(
                    Blendshapes.FindRef(KV.Key),
                    KV.Value * State.SecondaryIntensity
                );
            }
        }
    }
    
    return Blendshapes;
}
```

---

## EVENT BROADCASTING

### Expression Change Events

**Delegate Definition**:
```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(
    FOnExpressionChanged,
    FEmotionalState, OldState,
    FEmotionalState, NewState,
    TMap<FString, float>, BlendshapeWeights
);

UPROPERTY(BlueprintAssignable, Category = "Expression")
FOnExpressionChanged OnExpressionChanged;
```

**Broadcast Logic**:
```cpp
void BroadcastEmotionChanged()
{
    // Compute blendshape weights
    TMap<FString, float> CurrentBlendshapes = ComputeBlendshapeWeights(CurrentState);
    
    // Broadcast to subscribers (MetaHuman, audio, etc.)
    OnExpressionChanged.Broadcast(CurrentState, CurrentState, CurrentBlendshapes);
}
```

---

## INTEGRATION POINTS

### With NPC Personality

**Load Personality Traits**:
```cpp
void UExpressionManagerComponent::InitializeFromNPC(ANPCCharacter* NPC)
{
    // Load personality vector from NPC
    auto PersonalityDict = NPC->GetPersonalityVectorAsDict();
    
    // Map to expression traits
    PersonalityTraits.Add("aggression", PersonalityDict["aggression"]);
    PersonalityTraits.Add("charisma", PersonalityDict["charisma"]);
    PersonalityTraits.Add("cowardice", PersonalityDict["cowardice"]);
    // ... map all relevant traits
}
```

### With MetaHuman Facial System

**Subscribe to Updates**:
```cpp
// In MetaHuman component
ExpressionManager->OnExpressionChanged.AddDynamic(this, &UMetaHumanComponent::HandleExpressionChange);

void UMetaHumanComponent::HandleExpressionChange(FEmotionalState State, TMap<FString, float> Blendshapes)
{
    // Update blendshapes
    for (auto& KV : Blendshapes)
    {
        SetBlendshapeWeight(KV.Key, KV.Value);
    }
}
```

---

## PERFORMANCE BUDGET

### Update Budget

**CPU Target**: 0.05ms per NPC per frame

**Breakdown**:
- Emotion computation: 0.01ms
- Transition updates: 0.01ms
- Blendshape calculation: 0.01ms
- Event broadcasting: 0.02ms

**Memory**: ~5KB per NPC

---

## BLUEPRINT API

### Designer Functions

```cpp
// Set emotion
UFUNCTION(BlueprintCallable, Category = "Expression")
void SetEmotion(EEmotion Emotion, float Intensity = 1.0f, float Duration = 0.5f);

// Blend emotions
UFUNCTION(BlueprintCallable, Category = "Expression")
void BlendEmotions(EEmotion Emo1, float Int1, EEmotion Emo2, float Int2);

// Get current state
UFUNCTION(BlueprintCallable, Category = "Expression")
FEmotionalState GetCurrentState() const;

// Load personality
UFUNCTION(BlueprintCallable, Category = "Expression")
void LoadPersonalityFromNPC(ANPCCharacter* NPC);
```

---

**Status**: ✅ **CORE EMOTION SYSTEM ARCHITECTURE COMPLETE**



