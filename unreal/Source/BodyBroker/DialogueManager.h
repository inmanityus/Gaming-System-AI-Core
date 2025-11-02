// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "DialogueQueue.h"
#include "DialogueManager.generated.h"

class UAudioManager;
class UDialogueQueue;
class UAudioComponent;
class UWorld;

// Delegate for dialogue completion
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDialogueComplete, const FString&, DialogueID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnDialogueStarted, const FString&, DialogueID, const FString&, SpeakerName);

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

	// Stop dialogue by NPC ID
	UFUNCTION(BlueprintCallable, Category = "Dialogue Manager")
	void StopDialogueByNPC(const FString& NPCID);

	// Event delegates
	UPROPERTY(BlueprintAssignable, Category = "Dialogue Manager|Events")
	FOnDialogueStarted OnDialogueStarted;

	UPROPERTY(BlueprintAssignable, Category = "Dialogue Manager|Events")
	FOnDialogueComplete OnDialogueComplete;

private:
	// Audio manager reference (weak - owned externally)
	TWeakObjectPtr<UAudioManager> AudioManager;

	// Dialogue queue (owned by subsystem)
	UPROPERTY()
	TObjectPtr<UDialogueQueue> DialogueQueue;

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

	// Request TTS from backend (placeholder - will be implemented in Milestone 7)
	void RequestTTSFromBackend(const FDialogueItem& Item, TFunction<void(const TArray<uint8>&, float)> OnComplete);
};

