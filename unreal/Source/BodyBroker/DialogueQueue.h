// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "DialogueQueue.generated.h"

/**
 * Word timing data for subtitle highlighting and lip-sync
 */
USTRUCT(BlueprintType)
struct FWordTiming
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FString Word;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	float StartTime;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	float Duration;

	FWordTiming()
		: StartTime(0.0f)
		, Duration(0.0f)
	{}
};

/**
 * Dialogue item structure for priority queue
 */
USTRUCT(BlueprintType)
struct FDialogueItem
{
	GENERATED_BODY()

	// Dialogue identity
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FString DialogueID;

	// NPC info
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FString NPCID;

	// Audio data (binary)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	TArray<uint8> AudioData;

	// Priority level (0 = Critical, 1 = High, 2 = Medium, 3 = Low)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	int32 Priority;

	// Metadata
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FString Text;  // For subtitles

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FString SpeakerName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	float Duration;

	// Personality traits that should influence TTS delivery
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	TArray<FString> PersonalityTraits;

	// Emotion hint for TTS delivery
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	FString Emotion;

	// Timing data for lip-sync
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	TArray<FWordTiming> WordTimings;

	FDialogueItem()
		: Priority(2)  // Default to Medium priority
		, Duration(0.0f)
	{}
};

/**
 * Dialogue queue status for Blueprint queries
 */
USTRUCT(BlueprintType)
struct FDialogueQueueStatus
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	int32 CriticalQueueSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	int32 HighQueueSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	int32 MediumQueueSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	int32 LowQueueSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	int32 ActiveDialogueCount;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
	TMap<int32, int32> ActiveCountByPriority;

	FDialogueQueueStatus()
		: CriticalQueueSize(0)
		, HighQueueSize(0)
		, MediumQueueSize(0)
		, LowQueueSize(0)
		, ActiveDialogueCount(0)
	{}
};

/**
 * DialogueQueue - Manages priority-based dialogue queue system
 * Implements 4-tier priority system with concurrency limits
 */
UCLASS(BlueprintType)
class BODYBROKER_API UDialogueQueue : public UObject
{
	GENERATED_BODY()

public:
	UDialogueQueue(const FObjectInitializer& ObjectInitializer);

	// Initialize the queue system
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	void Initialize();

	// Enqueue a dialogue item to the appropriate priority queue
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	void EnqueueDialogue(const FDialogueItem& Item);

	// Dequeue the next dialogue item based on priority and concurrency limits
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	FDialogueItem DequeueNextDialogue();

	// Get the number of active dialogues currently playing
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	int32 GetActiveDialogueCount() const;

	// Get active count for a specific priority level
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	int32 GetActiveDialogueCountByPriority(int32 Priority) const;

	// Check if a dialogue with the given priority can be played (concurrency limits)
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	bool CanPlayDialogue(int32 Priority) const;

	// Mark a dialogue as active (called when playback starts)
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	void MarkDialogueActive(const FString& DialogueID, const FDialogueItem& Item);

	// Mark a dialogue as inactive (called when playback completes or stops)
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	void MarkDialogueInactive(const FString& DialogueID);

	// Get queue status for Blueprint queries
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	FDialogueQueueStatus GetQueueStatus() const;

	// Check if a dialogue is currently active
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	bool IsDialogueActive(const FString& DialogueID) const;

	// Clear all queues and active dialogues
	UFUNCTION(BlueprintCallable, Category = "Dialogue")
	void ClearAll();

private:
	// Priority queues (FIFO within same priority)
	UPROPERTY()
	TArray<FDialogueItem> CriticalQueue;  // Priority 0

	UPROPERTY()
	TArray<FDialogueItem> HighQueue;  // Priority 1

	UPROPERTY()
	TArray<FDialogueItem> MediumQueue;  // Priority 2

	UPROPERTY()
	TArray<FDialogueItem> LowQueue;  // Priority 3

	// Currently playing dialogues
	UPROPERTY()
	TMap<FString, FDialogueItem> ActiveDialogues;

	// Concurrency limits by priority
	UPROPERTY()
	TMap<int32, int32> MaxConcurrentByPriority;

	// Active count by priority (for fast lookups)
	UPROPERTY()
	TMap<int32, int32> ActiveCountByPriority;

	// Helper: Get queue for priority
	TArray<FDialogueItem>* GetQueueForPriority(int32 Priority);

	// Helper: Get const queue for priority
	const TArray<FDialogueItem>* GetQueueForPriority(int32 Priority) const;

	// Helper: Update active count by priority
	void UpdateActiveCountByPriority();
};

