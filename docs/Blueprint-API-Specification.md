# Complete Audio System Blueprint API Specification
**Date**: 2025-01-29  
**Task**: VA-004-B - Blueprint API Finalization  
**Status**: Complete

---

## OVERVIEW

This document provides the complete Blueprint API for all audio systems: AudioManager (VA-001), Ambient/Weather/Zones (VA-002), and Voice/Dialogue (VA-003).

---

## AUDIO MANAGER API (VA-001)

### Core Functions

```cpp
// ============================================
// INITIALIZATION & CONTROL
// ============================================

/**
 * Initialize AudioManager with backend URL
 * @param BackendURL - Backend API base URL (e.g., "http://localhost:4011")
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void Initialize(const FString& BackendURL);

/**
 * Play audio from backend API
 * @param AudioID - Unique audio identifier
 * @param Category - Audio category (Voice, Ambient, Music, Effect, UI)
 * @param Volume - Volume multiplier (0.0-1.0), defaults to 1.0
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void PlayAudioFromBackend(const FString& AudioID, EAudioCategory Category, float Volume = 1.0f);

/**
 * Stop audio playback
 * @param AudioID - Audio ID to stop
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void StopAudio(const FString& AudioID);

/**
 * Check if audio is currently playing
 * @param AudioID - Audio ID to check
 * @return True if playing, false otherwise
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
bool IsAudioPlaying(const FString& AudioID) const;

// ============================================
// VOLUME CONTROL
// ============================================

/**
 * Set master volume for all audio
 * @param Volume - Master volume (0.0-1.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void SetMasterVolume(float Volume);

/**
 * Set volume for specific category
 * @param Category - Audio category
 * @param Volume - Category volume (0.0-1.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void SetCategoryVolume(EAudioCategory Category, float Volume);
```

---

## TIME-OF-DAY & AMBIENT API (VA-002)

### Time-of-Day Ambient Functions

```cpp
// ============================================
// TIME-OF-DAY AMBIENT CONTROL
// ============================================

/**
 * Set time-of-day ambient audio profile
 * @param TimeState - Time state ("dawn", "day", "dusk", "night")
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Time Of Day")
void SetTimeOfDayAmbient(const FString& TimeState);

/**
 * Transition to new time-of-day ambient
 * @param TimeState - Target time state
 * @param Duration - Transition duration in seconds (default: 30.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Time Of Day")
void TransitionTimeOfDayAmbient(const FString& TimeState, float Duration = 30.0f);

/**
 * Get current time-of-day ambient state
 * @return Current time state string
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Time Of Day")
FString GetCurrentTimeOfDayAmbient() const;
```

### Weather Audio Functions

```cpp
// ============================================
// WEATHER AUDIO CONTROL
// ============================================

/**
 * Set weather audio layer
 * @param WeatherState - Weather state enum
 * @param Intensity - Weather intensity (0.0-1.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Weather")
void SetWeatherAudioLayer(EWeatherState WeatherState, float Intensity);

/**
 * Transition weather audio smoothly
 * @param NewWeatherState - Target weather state
 * @param Intensity - Target intensity
 * @param Duration - Transition duration in seconds (default: 5.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Weather")
void TransitionWeatherAudio(EWeatherState NewWeatherState, float Intensity, float Duration = 5.0f);

/**
 * Trigger thunder strike event
 * @param StrikeLocation - 3D position of thunder strike
 * @param Volume - Thunder volume (0.7-1.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Weather")
void TriggerThunderStrike(FVector StrikeLocation, float Volume = 0.85f);

/**
 * Update weather intensity dynamically
 * @param Intensity - New intensity value (0.0-1.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Weather")
void UpdateWeatherIntensity(float Intensity);
```

### Zone Audio Functions

```cpp
// ============================================
// ZONE AUDIO CONTROL
// ============================================

/**
 * Set zone ambient profile
 * @param ZoneProfileName - Zone profile name (e.g., "Street", "Warehouse", "Morgue")
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Zone")
void SetZoneAmbientProfile(const FString& ZoneProfileName);

/**
 * Restore previous zone ambient
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Zone")
void RestorePreviousZone();

/**
 * Get current zone profile name
 * @return Current zone profile name
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Zone")
FString GetCurrentZoneProfile() const;

/**
 * Calculate occlusion between source and listener
 * @param SourceLocation - Audio source position
 * @param ListenerLocation - Player/listener position
 * @return Occlusion amount (0.0-1.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager|Zone")
float CalculateOcclusion(FVector SourceLocation, FVector ListenerLocation) const;
```

### Audio Ducking Functions

```cpp
// ============================================
// AUDIO DUCKING CONTROL
// ============================================

/**
 * Duck audio category by amount
 * @param Category - Category to duck
 * @param DuckAmount - Duck amount (0.0-1.0), 1.0 = fully ducked
 * @param Duration - Transition duration in seconds (default: 2.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void DuckAudioByAmount(EAudioCategory Category, float DuckAmount, float Duration = 2.0f);

/**
 * Restore audio category to full volume
 * @param Category - Category to restore
 * @param Duration - Transition duration in seconds (default: 2.0)
 */
UFUNCTION(BlueprintCallable, Category = "Audio Manager")
void RestoreAudioCategory(EAudioCategory Category, float Duration = 2.0f);
```

---

## VOICE & DIALOGUE API (VA-003)

### Dialogue Playback Functions

```cpp
// ============================================
// DIALOGUE PLAYBACK
// ============================================

/**
 * Play dialogue for NPC
 * @param NPC - NPC character reference
 * @param Text - Dialogue text to speak
 * @param OnComplete - Callback when dialogue completes
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void PlayDialogueForNPC(
    ANPCCharacter* NPC,
    const FString& Text,
    const FDialogueCompleteDelegate& OnComplete
);

/**
 * Play dialogue with explicit priority
 * @param Text - Dialogue text
 * @param Priority - Priority level (0=Critical, 1=High, 2=Medium, 3=Low)
 * @param SpeakerName - Speaker name for subtitles
 * @param OnComplete - Callback when complete
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void PlayDialogueWithPriority(
    const FString& Text,
    int32 Priority,
    const FString& SpeakerName,
    const FDialogueCompleteDelegate& OnComplete
);

/**
 * Stop dialogue playback
 * @param DialogueID - Dialogue ID to stop
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void StopDialogue(const FString& DialogueID);

/**
 * Check if dialogue is playing
 * @param DialogueID - Dialogue ID to check
 * @return True if playing, false otherwise
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
bool IsDialoguePlaying(const FString& DialogueID) const;
```

### Dialogue Queue Functions

```cpp
// ============================================
// DIALOGUE QUEUE MANAGEMENT
// ============================================

/**
 * Get current queue status
 * @return Queue status struct
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
FDialogueQueueStatus GetQueueStatus() const;

/**
 * Clear all queued dialogue
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void ClearDialogueQueue();

/**
 * Get number of active concurrent voices
 * @return Active voice count
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
int32 GetActiveVoiceCount() const;
```

### Interrupt Functions

```cpp
// ============================================
// DIALOGUE INTERRUPT CONTROL
// ============================================

/**
 * Interrupt current dialogue
 * @param NewDialogueID - New dialogue to play
 * @param InterruptType - Interrupt type (Immediate, Crossfade, PauseAndResume)
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void InterruptDialogue(const FString& NewDialogueID, EInterruptType InterruptType = EInterruptType::Immediate);

/**
 * Pause current dialogue
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void PauseDialogue();

/**
 * Resume paused dialogue
 */
UFUNCTION(BlueprintCallable, Category = "Dialogue")
void ResumeDialogue();
```

### Subtitle Functions

```cpp
// ============================================
// SUBTITLE CONTROL
// ============================================

/**
 * Show subtitle manually
 * @param Text - Subtitle text
 * @param SpeakerName - Speaker name
 * @param Duration - Display duration in seconds
 */
UFUNCTION(BlueprintCallable, Category = "Subtitle")
void ShowSubtitle(const FString& Text, const FString& SpeakerName, float Duration);

/**
 * Hide subtitle
 */
UFUNCTION(BlueprintCallable, Category = "Subtitle")
void HideSubtitle();

/**
 * Enable/disable subtitles globally
 * @param bEnabled - True to enable, false to disable
 */
UFUNCTION(BlueprintCallable, Category = "Subtitle")
void SetSubtitlesEnabled(bool bEnabled);
```

---

## DELEGATES & EVENTS

### Audio Manager Events

```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAudioStarted, const FString&, AudioID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAudioStopped, const FString&, AudioID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnVolumeChanged, EAudioCategory, Category, float, NewVolume);

UPROPERTY(BlueprintAssignable, Category = "Audio Manager")
FOnAudioStarted OnAudioStarted;

UPROPERTY(BlueprintAssignable, Category = "Audio Manager")
FOnAudioStopped OnAudioStopped;

UPROPERTY(BlueprintAssignable, Category = "Audio Manager")
FOnVolumeChanged OnVolumeChanged;
```

### Dialogue Events

```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueStarted, const FString&, DialogueID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueCompleted, const FString&, DialogueID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueInterrupted, const FString&, InterruptedID);

UPROPERTY(BlueprintAssignable, Category = "Dialogue")
FOnDialogueStarted OnDialogueStarted;

UPROPERTY(BlueprintAssignable, Category = "Dialogue")
FOnDialogueCompleted OnDialogueCompleted;

UPROPERTY(BlueprintAssignable, Category = "Dialogue")
FOnDialogueInterrupted OnDialogueInterrupted;
```

### Subtitle Events

```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnSubtitleShow, const FSubtitleData&, Subtitle, float, Duration);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSubtitleHide, const FString&, DialogueID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnSubtitleUpdate, const FString&, DialogueID, const FString&, NewText, float, ElapsedTime);

UPROPERTY(BlueprintAssignable, Category = "Subtitle")
FOnSubtitleShow OnSubtitleShow;

UPROPERTY(BlueprintAssignable, Category = "Subtitle")
FOnSubtitleHide OnSubtitleHide;

UPROPERTY(BlueprintAssignable, Category = "Subtitle")
FOnSubtitleUpdate OnSubtitleUpdate;
```

---

## DATA STRUCTURES

### Audio Category Enum

```cpp
UENUM(BlueprintType)
enum class EAudioCategory : uint8
{
    Voice   UMETA(DisplayName = "Voice"),
    Ambient UMETA(DisplayName = "Ambient"),
    Music   UMETA(DisplayName = "Music"),
    Effect  UMETA(DisplayName = "Effect"),
    UI      UMETA(DisplayName = "UI")
};
```

### Dialogue Item

```cpp
USTRUCT(BlueprintType)
struct FDialogueItem
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString DialogueID;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString NPCID;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    TArray<uint8> AudioData;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    int32 Priority;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString Text;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    FString SpeakerName;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    float Duration;
};
```

### Subtitle Data

```cpp
USTRUCT(BlueprintType)
struct FSubtitleData
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
    FString Text;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
    FString SpeakerName;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
    float DisplayDuration;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
    TArray<FWordTiming> WordTimings;
};
```

---

## USAGE EXAMPLES

### Example 1: Basic Audio Playback

```cpp
// Get AudioManager
AAudioManager* AudioMgr = GetAudioManager();

// Initialize
AudioMgr->Initialize(TEXT("http://localhost:4011"));

// Play voice audio
AudioMgr->PlayAudioFromBackend(TEXT("vampire_line_001"), EAudioCategory::Voice, 1.0f);

// Set volume
AudioMgr->SetMasterVolume(0.75f);
```

### Example 2: Time-of-Day Ambient

```cpp
// In Blueprint or C++
AudioMgr->SetTimeOfDayAmbient(TEXT("night"));

// Smooth transition
AudioMgr->TransitionTimeOfDayAmbient(TEXT("dawn"), 30.0f);
```

### Example 3: Weather Audio

```cpp
// Set rain
AudioMgr->SetWeatherAudioLayer(EWeatherState::RAIN, 0.7f);

// Transition to storm
AudioMgr->TransitionWeatherAudio(EWeatherState::STORM, 1.0f, 5.0f);

// Trigger thunder
AudioMgr->TriggerThunderStrike(FVector(1000, 500, 200), 0.9f);
```

### Example 4: Dialogue Playback

```cpp
// Play dialogue with priority
AudioMgr->PlayDialogueWithPriority(
    TEXT("What brings you to these parts?"),
    1,  // High priority
    TEXT("Marcus"),
    FDialogueCompleteDelegate()
);

// Check queue
FDialogueQueueStatus Status = AudioMgr->GetQueueStatus();
int32 ActiveVoices = Status.ActiveCount;
```

### Example 5: Zone Transitions

```cpp
// Enter warehouse
AudioMgr->SetZoneAmbientProfile(TEXT("Warehouse"));

// Exit
AudioMgr->RestorePreviousZone();
```

---

## PARAMETER VALIDATION

### Volume Validation

```cpp
float ClampedVolume = FMath::Clamp(Volume, 0.0f, 1.0f);
```

### Priority Validation

```cpp
int32 ClampedPriority = FMath::Clamp(Priority, 0, 3);
```

### Duration Validation

```cpp
float ClampedDuration = FMath::Max(Duration, 0.1f);  // Minimum 0.1s
```

---

## ERROR HANDLING

### Return Values

**Success**: Functions return normally, delegates fire on completion
**Failure**: Errors logged via UE_LOG, delegates fire with error status

### Error Types

```cpp
enum class EAudioError
{
    None,
    InvalidAudioID,
    BackendUnavailable,
    PoolExhausted,
    InvalidPriority
};
```

---

**Status**: ✅ **BLUEPRINT API COMPLETE**



