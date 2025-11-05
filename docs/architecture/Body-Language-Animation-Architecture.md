# Body Language Animation Architecture
**Date**: 2025-01-29  
**Task**: FE-004 - Body Language System  
**Status**: Design Complete

---

## OVERVIEW

Complete body language animation system architecture for gestures, posture, idle variations, and procedural hand positioning, integrated with facial expressions and personality systems.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **ExpressionManager** (FE-001)
   - Emotional states
   - Personality modulation
   - Event broadcasting

2. **MetaHuman** (FE-002)
   - Facial animation
   - Eye tracking
   - Micro-expressions

3. **Personality Model** (`models/npc.py`)
   - 50-dimensional personality vector
   - Stats: aggression, intelligence, charisma

---

## ANIMATION BLUEPRINT LAYERS

### Layered Animation System

**Layer Hierarchy**:
```
Base Layer (Locomotion)
    ↓
Idle Layer (Idle variations)
    ↓
Gesture Layer (Additive gestures)
    ↓
Posture Layer (Posture modifications)
    ↓
Final Output
```

### Animation Blueprint Architecture

```cpp
UCLASS()
class UBodyLanguageAnimBP : public UAnimInstance
{
    GENERATED_BODY()

public:
    // Personality-driven idle selection
    UPROPERTY(BlueprintReadWrite, Category = "Body Language")
    int32 IdleVariationIndex;
    
    // Gesture playback
    UPROPERTY(BlueprintReadWrite, Category = "Body Language")
    UAnimSequence* CurrentGesture;
    
    // Posture modifier
    UPROPERTY(BlueprintReadWrite, Category = "Body Language")
    float PostureIntensity;
    
    // Hand positions
    UPROPERTY(BlueprintReadWrite, Category = "Body Language")
    FVector LeftHandTarget;
    
    UPROPERTY(BlueprintReadWrite, Category = "Body Language")
    FVector RightHandTarget;
    
    // Blueprint functions
    UFUNCTION(BlueprintImplementableEvent, Category = "Body Language")
    void PlayGesture(UAnimSequence* GestureSequence, float BlendInTime);
    
    UFUNCTION(BlueprintImplementableEvent, Category = "Body Language")
    void SetPosture(float Intensity);
    
    UFUNCTION(BlueprintImplementableEvent, Category = "Body Language")
    void UpdateHandPositions();
};
```

---

## GESTURE LIBRARY SYSTEM

### Gesture Data Structure

```cpp
USTRUCT(BlueprintType)
struct FGestureData
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString GestureID;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    UAnimSequence* AnimSequence;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Duration;
    
    // Personality suitability (0.0-1.0 per trait)
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, float> PersonalitySuitability;
    
    // Trigger conditions
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<EEmotion> SuitableEmotions;
    
    // Usage
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 MaxUsesPerConversation;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float CooldownTime;
};

// Gesture types
enum class EGestureType
{
    Greeting,       // Wave, nod, bow
    Pointing,       // Point at object/person
    Thinking,       // Chin scratch, arms crossed
    Nervous,        // Hand wringing, fidgeting
    Dominant,       // Expansive, hands on hips
    Submissive,     // Arms down, slight lean
    Emphasis,       // Hand chops, sweeping
    Dismissive      // Wave away, dismiss
};
```

### Gesture Library

```cpp
class UGestureLibrary : public UDataAsset
{
    GENERATED_BODY()

public:
    // Get gesture by type and personality
    UFUNCTION(BlueprintCallable, Category = "Gestures")
    UAnimSequence* GetGesture(
        EGestureType Type,
        const TMap<FString, float>& PersonalityTraits
    );
    
    // Find matching gestures for emotion
    UFUNCTION(BlueprintCallable, Category = "Gestures")
    TArray<UAnimSequence*> GetGesturesForEmotion(EEmotion Emotion);

private:
    UPROPERTY(EditAnywhere, Category = "Gestures")
    TArray<FGestureData> GestureDatabase;
    
    // Personality matching
    float CalculatePersonalityMatch(const FGestureData& Gesture, const TMap<FString, float>& Personality);
};
```

### Gesture Selection Logic

```cpp
UAnimSequence* GetGesture(EGestureType Type, const TMap<FString, float>& Personality)
{
    // Filter by type
    TArray<FGestureData> Candidates;
    for (auto& Gesture : GestureDatabase)
    {
        if (Gesture.GestureType == Type)
        {
            Candidates.Add(Gesture);
        }
    }
    
    if (Candidates.Num() == 0)
        return nullptr;
    
    // Score by personality match
    float BestScore = 0.0f;
    FGestureData* BestGesture = nullptr;
    
    for (auto& Gesture : Candidates)
    {
        float Score = CalculatePersonalityMatch(Gesture, Personality);
        if (Score > BestScore)
        {
            BestScore = Score;
            BestGesture = &Gesture;
        }
    }
    
    return BestGesture ? BestGesture->AnimSequence : nullptr;
}

float CalculatePersonalityMatch(const FGestureData& Gesture, const TMap<FString, float>& Personality)
{
    float TotalScore = 0.0f;
    float TotalWeight = 0.0f;
    
    for (auto& KV : Gesture.PersonalitySuitability)
    {
        float PersonalityValue = Personality.FindRef(KV.Key);
        float MatchScore = 1.0f - FMath::Abs(PersonalityValue - KV.Value);
        TotalScore += MatchScore;
        TotalWeight += 1.0f;
    }
    
    return TotalWeight > 0.0f ? TotalScore / TotalWeight : 0.5f;
}
```

---

## PERSONALITY-DRIVEN IDLE VARIATIONS

### Idle System

**Idle Variation Types**:
```cpp
enum class EIdleType
{
    Casual,         // Relaxed, natural
    Alert,          // Ready, tense
    Bored,          // Slouching, fidgeting
    Nervous,        // Anxious, quick movements
    Confident,      // Upright, relaxed
    Dominant,       // Expansive posture
    Submissive,     // Closed, smaller
    Thinking,       // Contemplative
    CasualAggressive // Relaxed but hostile
};

class UIdleVariationLibrary : public UDataAsset
{
    UPROPERTY(EditAnywhere, Category = "Idle")
    TMap<EIdleType, TArray<UBlendSpace*>> IdleVariations;
    
    // Select idle based on personality
    UFUNCTION(BlueprintCallable)
    UBlendSpace* GetIdleVariation(const TMap<FString, float>& Personality);
};
```

**Personality → Idle Mapping**:
```cpp
UBlendSpace* GetIdleVariation(const TMap<FString, float>& Personality)
{
    EIdleType IdleType = EIdleType::Casual;
    
    float Aggression = Personality.FindRef("aggression");
    float Confidence = Personality.FindRef("charisma");
    float Nervousness = Personality.FindRef("nervousness");
    
    // Determine idle type from personality
    if (Aggression > 0.7f && Confidence > 0.6f)
        IdleType = EIdleType::Dominant;
    else if (Nervousness > 0.6f)
        IdleType = EIdleType::Nervous;
    else if (Confidence > 0.7f)
        IdleType = EIdleType::Confident;
    else if (Aggression > 0.7f)
        IdleType = EIdleType::CasualAggressive;
    else
        IdleType = EIdleType::Casual;
    
    // Get random variation
    auto Variations = IdleVariations.Find(IdleType);
    if (Variations && Variations->Num() > 0)
    {
        int32 Index = FMath::RandRange(0, Variations->Num() - 1);
        return (*Variations)[Index];
    }
    
    return nullptr;
}
```

---

## PROCEDURAL HAND POSITIONING

### IK System

**Hand IK Component**:
```cpp
class UHandIKComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    // Set procedural hand position
    UFUNCTION(BlueprintCallable, Category = "Hand IK")
    void SetHandTarget(EHandType Hand, FVector TargetLocation);
    
    // Set relative to body part
    UFUNCTION(BlueprintCallable, Category = "Hand IK")
    void SetHandTargetRelative(EHandType Hand, FVector RelativeOffset);

private:
    UPROPERTY()
    FIKChain LeftHandIK;
    
    UPROPERTY()
    FIKChain RightHandIK;
    
    // Natural positioning
    void UpdateNaturalPositions();
};

enum class EHandType
{
    Left,
    Right,
    Both
};
```

**Natural Positioning Rules**:
```cpp
void UpdateNaturalPositions()
{
    // Default relaxed position
    FVector ChestLocation = GetChestLocation();
    FVector HipLocation = GetHipLocation();
    
    // Left hand: hip level, slightly forward
    FVector DefaultLeft = HipLocation + FVector(15.0f, -30.0f, 0.0f);
    
    // Right hand: chest level, forward
    FVector DefaultRight = ChestLocation + FVector(20.0f, 30.0f, -10.0f);
    
    // Apply with smoothing
    LeftHandIK.SetTarget(DefaultLeft);
    RightHandIK.SetTarget(DefaultRight);
}
```

**Emotion → Posture Mapping**:
```cpp
FHandPositions GetHandPositionsForEmotion(EEmotion Emotion) const
{
    FHandPositions Positions;
    
    switch (Emotion)
    {
        case EEmotion::Angry:
            Positions.LeftHand = FVector(40, -20, -5);  // Arms out
            Positions.RightHand = FVector(40, 20, -5);
            break;
        case EEmotion::Fear:
            Positions.LeftHand = FVector(0, -10, 20);  // Protective
            Positions.RightHand = FVector(0, 10, 20);
            break;
        case EEmotion::Confident:
            Positions.LeftHand = FVector(20, -30, -10);  // Hands on hips
            Positions.RightHand = FVector(20, 30, -10);
            break;
        default:
            Positions = GetNaturalPositions();
            break;
    }
    
    return Positions;
}
```

---

## BODY LANGUAGE MANAGER

### Complete Component

```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UBodyLanguageManager : public UActorComponent
{
    GENERATED_BODY()

public:
    // Initialize with personality
    UFUNCTION(BlueprintCallable, Category = "Body Language")
    void InitializeWithPersonality(const TMap<FString, float>& Personality);
    
    // Set emotion (triggers body language)
    UFUNCTION(BlueprintCallable, Category = "Body Language")
    void SetEmotion(EEmotion Emotion, float Intensity);
    
    // Play gesture
    UFUNCTION(BlueprintCallable, Category = "Body Language")
    void PlayGesture(EGestureType GestureType);
    
    // Update on tick
    virtual void TickComponent(float DeltaTime) override;

private:
    // Personality traits
    UPROPERTY()
    TMap<FString, float> PersonalityTraits;
    
    // Current emotion
    UPROPERTY()
    EEmotion CurrentEmotion;
    
    // Components
    UPROPERTY()
    UBodyLanguageAnimBP* AnimBP;
    
    UPROPERTY()
    UHandIKComponent* HandIK;
    
    UPROPERTY()
    UGestureLibrary* GestureLibrary;
    
    UPROPERTY()
    UIdleVariationLibrary* IdleLibrary;
    
    // Update systems
    void UpdateGestureSelection();
    void UpdateIdleVariation();
    void UpdateHandPositions();
};
```

---

## PERFORMANCE BUDGET

### Animation System Budget

**Target**: 0.5ms CPU per NPC per frame

**Breakdown**:
- Animation blending: 0.20ms
- Gesture selection: 0.05ms
- IK solving: 0.15ms
- Idle selection: 0.05ms
- Posture updates: 0.05ms

**Memory**: ~50KB per NPC

---

## BLUEPRINT API

### Designer Functions

```cpp
// Initialize
UFUNCTION(BlueprintCallable)
void InitializeWithPersonality(const TMap<FString, float>& Personality);

// Control
UFUNCTION(BlueprintCallable)
void SetEmotion(EEmotion Emotion, float Intensity);

UFUNCTION(BlueprintCallable)
void PlayGesture(EGestureType GestureType);

// Get current state
UFUNCTION(BlueprintCallable)
FBodyLanguageState GetCurrentState() const;
```

---

**Status**: ✅ **BODY LANGUAGE ARCHITECTURE COMPLETE**



