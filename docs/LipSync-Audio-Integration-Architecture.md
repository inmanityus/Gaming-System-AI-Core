# Lip-Sync & Audio Integration Architecture
**Date**: 2025-01-29  
**Task**: FE-003 - Lip-Sync & Audio Integration  
**Status**: Design Complete

---

## OVERVIEW

Complete lip-sync integration architecture connecting Dialogue/Voice system (VA-003) with MetaHuman facial animation (FE-002), including caching, synchronization, and performance optimization.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **Voice/Dialogue System** (VA-003)
   - Phoneme/viseme mappings complete
   - Backend TTS API
   - Word timing data
   - FLipSyncData structure

2. **MetaHuman System** (FE-002)
   - Blendshape control
   - Facial component complete
   - Control Rig integration

3. **ExpressionManager** (FE-001)
   - Emotional state blending
   - Expression presets
   - Event broadcasting

---

## INTEGRATION ARCHITECTURE

### Complete Pipeline

```
Audio Playback → Phoneme Data → Viseme Mapping → Blendshape Weights → Facial Animation
```

### LipSyncFacialComponent

**Complete Component**:
```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API ULipSyncFacialComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    // Play lip-sync from dialogue
    UFUNCTION(BlueprintCallable, Category = "LipSync")
    void PlayLipSyncFromDialogue(const FDialogueItem& DialogueItem);
    
    // Play pre-generated lip-sync
    UFUNCTION(BlueprintCallable, Category = "LipSync")
    void PlayLipSync(const FLipSyncData& LipSyncData);
    
    // Stop lip-sync
    UFUNCTION(BlueprintCallable, Category = "LipSync")
    void StopLipSync();
    
    // Set playback speed
    UFUNCTION(BlueprintCallable, Category = "LipSync")
    void SetPlaybackSpeed(float Speed = 1.0f);

private:
    // Current lip-sync data
    UPROPERTY()
    FLipSyncData CurrentLipSync;
    
    // Current playback time
    UPROPERTY()
    float CurrentPlaybackTime;
    
    // Animation timeline
    UPROPERTY()
    FTimeline LipSyncTimeline;
    
    // Update frames
    void UpdateLipSyncFrame(float Time);
    
    // Apply blendshapes
    void ApplyBlendshapes(const TMap<FString, float>& Blendshapes);
};
```

---

## DATA CACHING SYSTEM

### Cache Architecture

**LipSyncCache**:
```cpp
class ULipSyncCache : public UObject
{
    GENERATED_BODY()

public:
    // Check if cached
    UFUNCTION(BlueprintCallable, Category = "LipSync Cache")
    bool IsCached(const FString& AudioID) const;
    
    // Get cached data
    UFUNCTION(BlueprintCallable, Category = "LipSync Cache")
    FLipSyncData GetCachedData(const FString& AudioID) const;
    
    // Cache new data
    UFUNCTION(BlueprintCallable, Category = "LipSync Cache")
    void CacheLipSyncData(const FString& AudioID, const FLipSyncData& Data);
    
    // Preload cache
    UFUNCTION(BlueprintCallable, Category = "LipSync Cache")
    void PreloadAudio(const FString& AudioID);

private:
    // Cached data
    UPROPERTY()
    TMap<FString, FLipSyncData> Cache;
    
    // Access timestamps (for LRU)
    UPROPERTY()
    TMap<FString, float> AccessTimestamps;
    
    // Max cache size
    int32 MaxCacheEntries = 100;
    
    // LRU eviction
    void EvictLRU();
};
```

**LRU Eviction**:
```cpp
void EvictLRU()
{
    if (Cache.Num() < MaxCacheEntries)
        return;
    
    // Find oldest accessed
    FString OldestID;
    float OldestTime = MAX_FLT;
    
    for (auto& KV : AccessTimestamps)
    {
        if (KV.Value < OldestTime)
        {
            OldestTime = KV.Value;
            OldestID = KV.Key;
        }
    }
    
    // Remove
    if (!OldestID.IsEmpty())
    {
        Cache.Remove(OldestID);
        AccessTimestamps.Remove(OldestID);
    }
}
```

---

## SYNCHRONIZATION SYSTEM

### Audio→Facial Sync

**Timeline-Based Playback**:
```cpp
void ULipSyncFacialComponent::PlayLipSync(const FLipSyncData& LipSyncData)
{
    CurrentLipSync = LipSyncData;
    CurrentPlaybackTime = 0.0f;
    
    // Setup timeline
    FOnTimelineFloat PlaybackCallback;
    PlaybackCallback.BindUFunction(this, FName("UpdateLipSyncFrame"));
    
    LipSyncTimeline.AddInterpFloat(LipSyncTimelineCurve, PlaybackCallback);
    LipSyncTimeline.SetLooping(false);
    LipSyncTimeline.PlayFromStart();
}

void UpdateLipSyncFrame(float Time)
{
    CurrentPlaybackTime = Time;
    
    // Find current frame
    FPhonemeFrame* CurrentFrame = nullptr;
    
    for (auto& Frame : CurrentLipSync.Frames)
    {
        if (Frame.Time <= Time)
        {
            CurrentFrame = &Frame;
        }
        else
        {
            break;
        }
    }
    
    if (CurrentFrame)
    {
        // Map viseme → blendshapes
        auto VisemeBlendshapes = VisemeToBlendshapes.Find(CurrentFrame->Viseme);
        if (VisemeBlendshapes)
        {
            ApplyBlendshapes(*VisemeBlendshapes);
        }
    }
}
```

### Drift Correction

**Synchronization System**:
```cpp
class USyncMonitor
{
    float AudioPlaybackTime;
    float FacialPlaybackTime;
    float MaxDriftAllowed = 0.1f;  // 100ms
    
    void CheckSync(float DeltaTime)
    {
        float Drift = FMath::Abs(AudioPlaybackTime - FacialPlaybackTime);
        
        if (Drift > MaxDriftAllowed)
        {
            // Correct drift
            FacialPlaybackTime = AudioPlaybackTime;
            JumpToFrame(FacialPlaybackTime);
        }
    }
};
```

---

## PERFORMANCE OPTIMIZATION

### Update Frequency

**Throttling Strategy**:
```cpp
struct FUpdateRate
{
    int32 UpdateIntervalFrames = 1;  // Every frame
    int32 FrameSkip = 0;
    
    bool ShouldUpdate()
    {
        FrameSkip++;
        if (FrameSkip >= UpdateIntervalFrames)
        {
            FrameSkip = 0;
            return true;
        }
        return false;
    }
};

FUpdateRate UpdateRate = {1};  // Every frame for active speakers

void TickComponent(float DeltaTime)
{
    if (!UpdateRate.ShouldUpdate())
        return;
    
    // Update lip-sync
    UpdateLipSyncFrame(CurrentPlaybackTime);
}
```

### LOD System

**Distance-Based Quality**:
```cpp
enum class ELipSyncLOD
{
    Full,        // 0-100m:  Every frame, full quality
    Reduced,     // 100-300m: Every 2 frames, reduced quality
    Minimal,     // 300-600m: Every 5 frames, minimal quality
    Disabled     // 600m+:    No lip-sync
};

ELipSyncLOD CalculateLOD(float Distance)
{
    if (Distance < 100.0f) return ELipSyncLOD::Full;
    if (Distance < 300.0f) return ELipSyncLOD::Reduced;
    if (Distance < 600.0f) return ELipSyncLOD::Minimal;
    return ELipSyncLOD::Disabled;
}
```

---

## PERFORMANCE BUDGET

### Per-Character Budget

**Target**: 0.3ms CPU per character per frame

**Breakdown**:
- Frame lookup: 0.05ms
- Viseme mapping: 0.05ms
- Blendshape update: 0.10ms
- Timeline management: 0.05ms
- Drift correction: 0.05ms

**Memory**: ~5KB per active lip-sync

---

## COMPLETE INTEGRATION FLOW

### From Dialogue to Facial

```
DialogueManager.PlayDialogue()
    ↓
Generate/Retrieve LipSyncData
    ↓
Cache LipSyncData
    ↓
Start Audio Playback
    ↓
Start LipSyncFacialComponent.PlayLipSync()
    ↓
Timeline updates frames at audio time
    ↓
Viseme → Blendshapes mapping
    ↓
Apply to MetaHuman FacialComponent
    ↓
On complete: Stop and cleanup
```

---

## BLUEPRINT API

### Designer Functions

```cpp
// Play lip-sync from dialogue
UFUNCTION(BlueprintCallable, Category = "LipSync")
void PlayLipSyncFromDialogue(const FDialogueItem& DialogueItem);

// Manual control
UFUNCTION(BlueprintCallable, Category = "LipSync")
void PlayLipSync(const FLipSyncData& LipSyncData);

// Stop
UFUNCTION(BlueprintCallable, Category = "LipSync")
void StopLipSync();

// Caching
UFUNCTION(BlueprintCallable, Category = "LipSync Cache")
void PreloadLipSyncData(const FString& AudioID);
```

---

## TESTING & VALIDATION

### Accuracy Testing

**Test Strategy**:
- Manual visual validation
- Synchronization timing checks
- Frame accuracy verification
- Drift monitoring

**Target**: >90% accuracy

---

**Status**: ✅ **LIP-SYNC INTEGRATION ARCHITECTURE COMPLETE**



