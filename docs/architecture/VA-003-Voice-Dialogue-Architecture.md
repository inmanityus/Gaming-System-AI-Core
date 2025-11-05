# VA-003: Voice & Dialogue System Architecture
**Date**: 2025-01-29  
**Task**: VA-003 - Voice & Dialogue System  
**Status**: Architecture Design - Ready for Implementation

---

## OVERVIEW

This document defines the architecture for implementing a voice and dialogue system that integrates with AudioManager, provides priority-based dialogue playback, interrupt handling, subtitle broadcasting, lip-sync generation, and concurrent voice management.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **AudioManager** (`unreal/Source/BodyBroker/AudioManager.h`)
   - HTTP integration with backend audio API
   - Category-based volume management (Voice category exists)
   - Blueprint-exposed functions
   - Audio component management

2. **NPC System** (`models/npc.py`)
   - NPC entities with personality vectors
   - Relationship tracking
   - Goal stack for autonomous behavior
   - Current location and state

3. **AI Integration Service** (`services/ai_integration/`)
   - LLM dialogue generation
   - Context management
   - Multi-tier model serving (Tier 1/2/3)

4. **More Requirements** (`docs/More Requirements.md`)
   - Different voices per monster
   - Personality affects voice
   - Voices don’t sound AI-generated

---

## ARCHITECTURE DESIGN

### 1. Dialogue Priority System

#### Priority Levels

**4-Tier Priority System**:
```
Priority 0 - CRITICAL (Immediate)
    - Player death
    - Critical warnings
    - Story-critical dialogue
    - Maximum: 1 concurrent voice

Priority 1 - HIGH (Important)
    - Quest dialogue
    - Major NPC conversations
    - Combat announcements
    - Maximum: 2 concurrent voices

Priority 2 - MEDIUM (Standard)
    - Regular dialogue
    - Exposition
    - Side quest dialogue
    - Maximum: 4 concurrent voices

Priority 3 - LOW (Background)
    - Ambient chatter
    - Background NPCs
    - Environmental audio
    - Maximum: 8 concurrent voices
```

**Total Concurrent Voices**: 8 maximum

#### Priority Queue Design

**Queue Management**:
```cpp
USTRUCT(BlueprintType)
struct FDialogueItem
{
    GENERATED_BODY()
    
    // Dialogue identity
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString DialogueID;
    
    // NPC info
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString NPCID;
    
    // Audio data
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<uint8> AudioData;
    
    // Priority level
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 Priority;
    
    // Metadata
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Text;  // For subtitles
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString SpeakerName;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Duration;
    
    // Timing data for lip-sync
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FWordTiming> WordTimings;
};

UCLASS()
class BODYBROKER_API UDialogueQueue : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    void EnqueueDialogue(const FDialogueItem& Item);
    
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    FDialogueItem DequeueNextDialogue();
    
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    int32 GetActiveDialogueCount() const;
    
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    bool CanPlayDialogue(int32 Priority) const;

private:
    // Priority queues
    UPROPERTY()
    TArray<FDialogueItem> CriticalQueue;
    
    UPROPERTY()
    TArray<FDialogueItem> HighQueue;
    
    UPROPERTY()
    TArray<FDialogueItem> MediumQueue;
    
    UPROPERTY()
    TArray<FDialogueItem> LowQueue;
    
    // Currently playing
    UPROPERTY()
    TMap<FString, FDialogueItem> ActiveDialogues;
    
    // Concurrency limits
    UPROPERTY()
    TMap<int32, int32> MaxConcurrentByPriority;
};
```

### 2. Interrupt Handling System

#### Interrupt Rules

**When to Interrupt**:
1. **Higher Priority Arrives**: New dialogue has higher priority than currently playing
2. **Critical Event**: Critical priority dialogue interrupts everything
3. **Player Initiated**: Player starts new dialogue (interrupts NPC-to-NPC)
4. **Expiration**: Dialogue has been waiting too long in queue

**Interrupt Behavior**:
```cpp
enum class EInterruptType
{
    None,           // No interrupt
    Immediate,      // Stop instantly, play new
    Crossfade,      // Fade out old (0.5s), fade in new
    PauseAndResume, // Pause old, play new, resume old after
};

UFUNCTION(BlueprintCallable, Category = "Dialogue")
void HandleDialogueInterrupt(
    const FDialogueItem& NewDialogue,
    EInterruptType InterruptType = EInterruptType::Immediate
);
```

**Interrupt Priority Matrix**:
```
New\Current     Priority 0    Priority 1    Priority 2    Priority 3
Priority 0      Immediate     Immediate     Immediate     Immediate
Priority 1      No            Immediate     Crossfade     Crossfade
Priority 2      No            No            Crossfade     Crossfade
Priority 3      No            No            No            None
```

### 3. Dialogue Playback System

#### Playback Integration with AudioManager

**DialogueManager Subsystem**:
```cpp
UCLASS()
class BODYBROKER_API UDialogueManager : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    // Initialize
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    void Initialize(AAudioManager* InAudioManager);
    
    // Play dialogue
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    void PlayDialogue(
        const FString& NPCID,
        const FString& Text,
        int32 Priority,
        const FDialogueCompleteDelegate& OnComplete
    );
    
    // Stop dialogue
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    void StopDialogue(const FString& DialogueID);
    
    // Check if playing
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    bool IsDialoguePlaying(const FString& DialogueID) const;
    
    // Get queue status
    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    FDialogueQueueStatus GetQueueStatus() const;
    
private:
    // Audio manager reference
    UPROPERTY()
    AAudioManager* AudioManager;
    
    // Dialogue queue
    UPROPERTY()
    UDialogueQueue* Queue;
    
    // Active audio components
    UPROPERTY()
    TMap<FString, UAudioComponent*> ActiveAudioComponents;
};
```

**Playback Flow**:
```
PlayDialogue(NPCID, Text, Priority)
    ↓
Check TTS Cache
    ↓
If cached: Use audio
If not: Request TTS from backend
    ↓
Generate dialogue item with priority
    ↓
Enqueue to DialogueQueue
    ↓
Queue checks if can play
    ↓
If yes: Pass to AudioManager.PlayAudioFromBackend()
    ↓
Broadcast subtitle event
    ↓
Start lip-sync data processing
    ↓
On complete: Remove from active, play next in queue
```

### 4. Subtitle Event Broadcasting

#### Subtitle System

**Subtitle Data Structure**:
```cpp
USTRUCT(BlueprintType)
struct FSubtitleData
{
    GENERATED_BODY()
    
    // Subtitle text
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Text;
    
    // Speaker
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString SpeakerName;
    
    // Timing
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float DisplayDuration;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float StartTime;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float EndTime;
    
    // Word-level timing
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FWordTiming> WordTimings;
};

USTRUCT(BlueprintType)
struct FWordTiming
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Word;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float StartTime;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Duration;
};
```

**Subtitle Event Broadcasting**:
```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnSubtitleShow, const FSubtitleData&, Subtitle, float, Duration);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSubtitleHide, const FString&, DialogueID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnSubtitleUpdate, const FString&, DialogueID, const FString&, NewText, float, ElapsedTime);

UPROPERTY(BlueprintAssignable, Category = "Dialogue")
FOnSubtitleShow OnSubtitleShow;

UPROPERTY(BlueprintAssignable, Category = "Dialogue")
FOnSubtitleHide OnSubtitleHide;

UPROPERTY(BlueprintAssignable, Category = "Dialogue")
FOnSubtitleUpdate OnSubtitleUpdate;
```

**Subtitle Timing**:
- Display duration = audio duration + 1.0s buffer
- Word timings for highlighting (optional)
- Smooth fade in/out (0.3s transitions)

### 5. Lip-Sync Data Pipeline

#### Lip-Sync Integration

**Lip-Sync Data Format**:
```cpp
USTRUCT(BlueprintType)
struct FLipSyncData
{
    GENERATED_BODY()
    
    // Audio reference
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString AudioID;
    
    // Phoneme timing data
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FPhonemeFrame> Frames;
    
    // Blendshape targets
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, float> BlendshapeWeights;  // "jaw_open", "eye_squint", etc.
};

USTRUCT(BlueprintType)
struct FPhonemeFrame
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Time;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Phoneme;  // "AA", "IH", "TH", etc. (ARPAbet)
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Viseme;   // "silence", "p", "f", "a", etc.
};

// Phoneme-to-Viseme Mapping
static const TMap<FString, FString> PhonemeToVisemeMap = {
    {"SIL", "silence"},
    {"AA", "a"}, {"AE", "a"}, {"AH", "a"}, {"AO", "a"}, {"AW", "a"}, {"AY", "a"},
    {"B", "p"}, {"P", "p"},
    {"CH", "j"}, {"D", "t"}, {"DH", "th"}, {"F", "f"}, {"G", "k"}, {"HH", "th"},
    {"IH", "i"}, {"IY", "i"}, {"JH", "j"}, {"K", "k"}, {"L", "i"}, {"M", "p"},
    {"N", "t"}, {"NG", "t"}, {"OW", "o"}, {"OY", "o"}, {"R", "r"}, {"S", "s"},
    {"SH", "sh"}, {"T", "t"}, {"TH", "th"}, {"UH", "u"}, {"UW", "u"}, {"V", "f"},
    {"W", "u"}, {"Y", "i"}, {"Z", "s"}, {"ZH", "sh"}
};
```

**Lip-Sync Generation**:
```
Text Input → Phoneme Conversion → Viseme Mapping → Frame Generation → Blendshape Weights
```

**Backend API Integration**:
```
POST /api/tts/generate-lipsync
    Request: { "text": "...", "voice_id": "...", "format": "phonemes" }
    Returns: { "audio": base64, "lipsync": {...}, "word_timings": [...] }
```

### 6. Voice Concurrency Management

#### Concurrent Voice Limits

**By Priority**:
```cpp
MaxConcurrentByPriority = {
    {0, 1},  // Critical: 1 voice only
    {1, 2},  // High: 2 voices max
    {2, 4},  // Medium: 4 voices max
    {3, 8}   // Low: 8 voices max
};

Total System Maximum: 8 concurrent voices
```

**Voice Pool Management**:
```cpp
class UVoicePool
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Voice Pool")
    UAudioComponent* AcquireVoiceComponent();
    
    UFUNCTION(BlueprintCallable, Category = "Voice Pool")
    void ReleaseVoiceComponent(UAudioComponent* Component);
    
    UFUNCTION(BlueprintCallable, Category = "Voice Pool")
    int32 GetAvailableCount() const;
    
private:
    // Pool of pre-allocated audio components
    UPROPERTY()
    TArray<UAudioComponent*> Pool;
    
    UPROPERTY()
    TSet<UAudioComponent*> InUse;
    
    // Max pool size
    int32 MaxPoolSize = 8;
};
```

**Spatial Audio Management**:
- Each voice gets 3D positioning
- Distance attenuation applied
- Occlusion checks for each voice
- Prioritize closest voices to player

---

## BACKEND API INTEGRATION

### TTS Service Endpoints

**Voice Generation**:
```
POST /api/tts/generate
    Request: {
        "text": "dialogue text",
        "voice_id": "vampire_lord_marcus",
        "personality_traits": ["arrogant", "sophisticated"],
        "emotion": "angry",
        "format": "wav" | "ogg",
        "sample_rate": 44100
    }
    Returns: {
        "audio": "base64 encoded audio",
        "duration": 3.5,
        "word_timings": [...],
        "lipsync": {...}
    }
```

**Voice Management**:
```
GET /api/voices/
    Returns: List of available voices by monster type

GET /api/voices/{voice_id}
    Returns: Voice metadata (name, type, sample audio)

POST /api/voices/preload
    Request: { "voice_ids": ["voice1", "voice2"] }
    Returns: Preload confirmation
```

### Voice Asset System

**Monster Voice Types**:
- **Humans**: Normal voices
- **Vampires**: Refined, aristocratic
- **Werewolves**: Growling, animalistic
- **Zombies**: Groaning, decayed
- **Ghouls**: Raspy, tortured
- **Liches**: Ethereal, echoing

**Personality-Based Variation**:
```
Personality Traits → Voice Modulation Parameters
- Arrogant: Raise pitch, reduce speed
- Aggressive: Lower pitch, increase speed
- Frightened: Raise pitch, add tremor
- Confident: Steady pitch, moderate speed
```

---

## LIP-SYNC FACIAL ANIMATION INTEGRATION

### Facial System Hooks

**Blendshape Targets**:
```cpp
USTRUCT(BlueprintType)
struct FBlendshapeTarget
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Name;  // "jaw_open", "lip_pucker", "eye_squint", etc.
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Weight;  // 0.0 - 1.0
};

// Common blendshapes for lip-sync
static const TArray<FString> LipSyncBlendshapes = {
    "jaw_open",
    "lip_pucker",
    "lip_stretch",
    "mouth_wide",
    "eye_squint_left",
    "eye_squint_right",
    "eyebrow_raise",
    "nose_scrunch"
};
```

**Viseme → Blendshape Mapping**:
```cpp
static TMap<FString, TMap<FString, float>> VisemeToBlendshapes = {
    {"silence", {{"jaw_open", 0.0}, {"lip_pucker", 0.0}}},
    {"a", {{"jaw_open", 0.8}, {"mouth_wide", 0.6}}},
    {"p", {{"lip_pucker", 0.9}, {"jaw_open", 0.2}}},
    {"f", {{"lip_stretch", 0.7}, {"jaw_open", 0.3}}},
    {"th", {{"lip_stretch", 0.8}, {"jaw_open", 0.4}}},
    {"i", {{"jaw_open", 0.4}, {"mouth_wide", 0.5}}},
    {"u", {{"lip_pucker", 0.6}, {"jaw_open", 0.5}}},
    {"o", {{"lip_pucker", 0.4}, {"jaw_open", 0.6}}},
    {"r", {{"lip_stretch", 0.3}, {"jaw_open", 0.3}}},
    {"s", {{"lip_stretch", 0.5}, {"jaw_open", 0.2}}},
    {"sh", {{"lip_pucker", 0.7}, {"jaw_open", 0.2}}}
};
```

### Facial Animation Integration

**NPC Facial Component**:
```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UNPCFacialComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Facial")
    void PlayLipSync(const FLipSyncData& LipSyncData);
    
    UFUNCTION(BlueprintCallable, Category = "Facial")
    void StopLipSync();
    
    UFUNCTION(BlueprintCallable, Category = "Facial")
    void SetBlendshapeWeight(const FString& BlendshapeName, float Weight);

private:
    // Blendshape references
    UPROPERTY()
    UStaticMeshComponent* FaceMesh;
    
    // Current lip-sync state
    UPROPERTY()
    FLipSyncData CurrentLipSync;
    
    // Animation timeline
    UPROPERTY()
    FTimeline LipSyncTimeline;
};
```

---

## PERFORMANCE BUDGET

### Voice System CPU Budget

**Target**: 0.5ms per frame

**Breakdown**:
- Queue management: 0.05ms
- TTS requests (async): 0.0ms (background)
- Audio playback: 0.2ms (handled by AudioManager)
- Subtitle processing: 0.05ms
- Lip-sync updates: 0.2ms

### Memory Budget

**Voice Assets**: ~100MB total
- 50 unique voices × 2MB average = 100MB

**Runtime Memory**: ~20MB
- Active audio components: 8 × 2MB = 16MB
- Queue buffers: 4MB
- Lip-sync data: negligible

**Total**: ~120MB voice system memory

---

## TESTING STRATEGY

### Unit Tests

**Priority Queue**:
- Test all priority levels
- Test concurrency limits
- Test queue ordering

**Interrupt System**:
- Test interrupt rules
- Test crossfade behavior
- Test pause/resume

**Concurrency**:
- Test max concurrent voices
- Test voice pool management
- Test spatial audio priority

### Integration Tests

**With AudioManager**:
- Verify audio playback works
- Test category volume control
- Test HTTP request handling

**With Facial System**:
- Verify lip-sync data flow
- Test blendshape updates
- Test timing synchronization

---

## BLUEPRINT API

### Designer-Facing Functions

```cpp
// Play dialogue (automatic priority resolution)
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void PlayDialogueForNPC(
    ANPCCharacter* NPC,
    const FString& Text,
    const FDialogueCompleteDelegate& OnComplete
);

// Force priority
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void PlayDialogueWithPriority(
    const FString& Text,
    int32 Priority,
    const FDialogueCompleteDelegate& OnComplete
);

// Interrupt current dialogue
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void InterruptDialogue(const FString& NewDialogueID);

// Queue status
UFUNCTION(BlueprintCallable, Category = "Dialogue")
FDialogueQueueStatus GetQueueStatus();

// Event delegates
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueStarted, const FString&, DialogueID);
UPROPERTY(BlueprintAssignable, Category = "Dialogue")
FOnDialogueStarted OnDialogueStarted;
```

---

## IMPLEMENTATION PHASES

### Phase 1: Core Dialogue Playback
1. Implement UDialogueQueue
2. Integrate with AudioManager
3. Basic priority system
4. Simple interrupt handling

### Phase 2: Subtitles & Events
1. Subtitle data structure
2. Event broadcasting
3. UI integration
4. Word-level timing

### Phase 3: Lip-Sync Integration
1. Phoneme/viseme mapping
2. Lip-sync data generation
3. Facial component integration
4. Blendshape animation

### Phase 4: Polish & Optimization
1. Voice pool management
2. Spatial audio optimization
3. Performance profiling
4. Testing & validation

---

## NEXT STEPS

1. ✅ Architecture design complete
2. ⏳ Implement DialogueQueue C++ class
3. ⏳ Integrate with AudioManager
4. ⏳ Create backend TTS API endpoints
5. ⏳ Design facial animation integration
6. ⏳ Testing & optimization

---

**Status**: ✅ **ARCHITECTURE COMPLETE - READY FOR IMPLEMENTATION**



