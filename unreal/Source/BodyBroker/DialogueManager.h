// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "DialogueQueue.h"
#include "DialogueManager.generated.h"

class UAudioManager;
class UDialogueQueue;
class UAudioComponent;
class UVoicePool;
class UWorld;

// Interrupt types
UENUM(BlueprintType)
enum class EInterruptType : uint8
{
	None			UMETA(DisplayName = "None"),
	Immediate		UMETA(DisplayName = "Immediate"),
	Crossfade		UMETA(DisplayName = "Crossfade"),
	PauseAndResume	UMETA(DisplayName = "Pause And Resume")
};

// Subtitle data structure
USTRUCT(BlueprintType)
struct FSubtitleData
{
	GENERATED_BODY()

	// Subtitle text
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	FString Text;

	// Speaker
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	FString SpeakerName;

	// Dialogue ID
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	FString DialogueID;

	// Timing
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	float DisplayDuration;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	float StartTime;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	float EndTime;

	// Word-level timing (optional)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Subtitle")
	TArray<FWordTiming> WordTimings;

	FSubtitleData()
		: DisplayDuration(0.0f)
		, StartTime(0.0f)
		, EndTime(0.0f)
	{}
};

// Phoneme frame for lip-sync
USTRUCT(BlueprintType)
struct FPhonemeFrame
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lip Sync")
	float Time;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lip Sync")
	FString Phoneme;  // "AA", "IH", "TH", etc. (ARPAbet)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lip Sync")
	FString Viseme;   // "silence", "p", "f", "a", etc.

	FPhonemeFrame()
		: Time(0.0f)
	{}
};

// Lip-sync data structure
USTRUCT(BlueprintType)
struct FLipSyncData
{
	GENERATED_BODY()

	// Audio reference
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lip Sync")
	FString AudioID;

	// Dialogue ID
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lip Sync")
	FString DialogueID;

	// Phoneme timing data
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lip Sync")
	TArray<FPhonemeFrame> Frames;

	// Blendshape targets (viseme -> weight mapping)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lip Sync")
	TMap<FString, float> BlendshapeWeights;  // "jaw_open", "lip_pucker", etc.

	FLipSyncData()
	{}
};

// Delegate for dialogue completion
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueComplete, const FString&, DialogueID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnDialogueStarted, const FString&, DialogueID, const FString&, SpeakerName);

// Subtitle event delegates
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnSubtitleShow, const FSubtitleData&, Subtitle, float, Duration);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSubtitleHide, const FString&, DialogueID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnSubtitleUpdate, const FString&, DialogueID, const FString&, NewText, float, ElapsedTime);

/**
 * DialogueManager - Manages dialogue playback system
 * Integrates DialogueQueue with AudioManager for priority-based dialogue playback
 */
UCLASS()
class BODYBROKER_API UDialogueManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	// USubsystem interface
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	// Initialize with AudioManager reference
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void InitializeWithAudioManager(UAudioManager* InAudioManager);

	// Play dialogue with automatic priority resolution
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void PlayDialogue(
		const FString& NPCID,
		const FString& Text,
		int32 Priority = 2,  // Default to Medium priority
		const FString& DialogueID = TEXT("")
	);

	// Play dialogue with explicit DialogueItem
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void PlayDialogueItem(const FDialogueItem& Item);

	// Stop dialogue playback
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void StopDialogue(const FString& DialogueID);

	// Check if dialogue is playing
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	bool IsDialoguePlaying(const FString& DialogueID) const;

	// Get queue status
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	FDialogueQueueStatus GetQueueStatus() const;

	// Process next dialogue in queue (called when current dialogue completes)
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void ProcessNextDialogue();

	// Handle dialogue interrupt based on priority
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void HandleDialogueInterrupt(const FDialogueItem& NewDialogue, EInterruptType InterruptType = EInterruptType::Immediate);

	// Stop dialogue by NPC ID
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void StopDialogueByNPC(const FString& NPCID);

	// Generate and get lip-sync data for dialogue
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager|Lip Sync")
	FLipSyncData GetLipSyncData(const FString& DialogueID) const;

	// Event delegates
	UPROPERTY(BlueprintAssignable, Category = "Dialogue Manager|Events")
	FOnDialogueStarted OnDialogueStarted;

	UPROPERTY(BlueprintAssignable, Category = "Dialogue Manager|Events")
	FOnDialogueComplete OnDialogueComplete;

	// Subtitle event delegates
	UPROPERTY(BlueprintAssignable, Category = "Dialogue Manager|Events|Subtitle")
	FOnSubtitleShow OnSubtitleShow;

	UPROPERTY(BlueprintAssignable, Category = "Dialogue Manager|Events|Subtitle")
	FOnSubtitleHide OnSubtitleHide;

	UPROPERTY(BlueprintAssignable, Category = "Dialogue Manager|Events|Subtitle")
	FOnSubtitleUpdate OnSubtitleUpdate;

private:
	// Audio manager reference (weak - owned externally)
	TWeakObjectPtr<UAudioManager> AudioManager;

	// Dialogue queue (owned by subsystem)
	UPROPERTY()
	TObjectPtr<UDialogueQueue> DialogueQueue;

	// Voice pool for concurrent voice management
	UPROPERTY()
	TObjectPtr<UVoicePool> VoicePool;

	// Active audio components for dialogues (NPCID -> AudioComponent) - weak refs
	UPROPERTY()
	TMap<FString, TWeakObjectPtr<UAudioComponent>> ActiveDialogueComponents;

	// Active dialogue items (DialogueID -> DialogueItem)
	UPROPERTY()
	TMap<FString, FDialogueItem> ActiveDialogueItems;

	// Reentrancy protection
	bool bProcessingQueue;

	// Generate unique DialogueID if not provided
	FString GenerateDialogueID(const FString& NPCID, const FString& Text) const;

	// Handle audio completion callback
	void HandleDialogueFinished(const FString& DialogueID);

	// World cleanup handler
	void OnWorldCleanup(UWorld* World, bool bSessionEnded, bool bCleanupResources);

	// Start playing a dialogue item
	void StartDialoguePlayback(const FDialogueItem& Item);

	// Create subtitle data from dialogue item
	FSubtitleData CreateSubtitleData(const FDialogueItem& Item) const;

	// Broadcast subtitle show event
	void BroadcastSubtitleShow(const FDialogueItem& Item);

	// Broadcast subtitle hide event
	void BroadcastSubtitleHide(const FString& DialogueID);

	// Broadcast subtitle update event (word-level timing if available)
	void BroadcastSubtitleUpdate(const FDialogueItem& Item, float ElapsedTime);

	// Lip-sync generation
	FLipSyncData GenerateLipSyncData(const FDialogueItem& Item) const;

	// Phoneme to viseme conversion
	FString PhonemeToViseme(const FString& Phoneme) const;

	// Get blendshape weights for viseme
	TMap<FString, float> GetBlendshapeWeightsForViseme(const FString& Viseme) const;

	// Request TTS from backend (placeholder - will be implemented in Milestone 7)
	void RequestTTSFromBackend(const FDialogueItem& Item, TFunction<void(const TArray<uint8>&, float)> OnComplete);

	// Determine interrupt type based on priority matrix
	EInterruptType DetermineInterruptType(int32 NewPriority, int32 CurrentPriority) const;

	// Execute immediate interrupt (stop current, start new)
	void ExecuteImmediateInterrupt(const FDialogueItem& NewDialogue, const FDialogueItem& CurrentDialogue);

	// Execute crossfade interrupt (fade out old, fade in new)
	void ExecuteCrossfadeInterrupt(const FDialogueItem& NewDialogue, const FDialogueItem& CurrentDialogue);

	// Execute pause and resume interrupt (pause old, play new, resume old after)
	void ExecutePauseAndResumeInterrupt(const FDialogueItem& NewDialogue, const FDialogueItem& CurrentDialogue);

	// Paused dialogues waiting to resume
	UPROPERTY()
	TMap<FString, FDialogueItem> PausedDialogues;

	// Crossfade state tracking
	UPROPERTY()
	TMap<FString, float> CrossfadeProgress;

	// Crossfade duration constant
	static constexpr float CROSSFADE_DURATION = 0.5f;
};

