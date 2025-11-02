// Copyright Epic Games, Inc. All Rights Reserved.

#include "DialogueManager.h"
#include "AudioManager.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/GameModeBase.h"
#include "Kismet/GameplayStatics.h"
#include "Delegates/Delegate.h"
#include "WorldDelegates.h"
#include "Misc/ScopeGuard.h"

void UDialogueManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Try to resolve AudioManager dependency automatically
	if (!AudioManager.IsValid())
	{
		if (UGameInstance* GI = GetGameInstance())
		{
			// Note: AudioManager is currently a component, not a subsystem
			// This will need to be set via InitializeWithAudioManager for now
			// In future, if AudioManager becomes a subsystem, use: Collection.InitializeDependency<UAudioManager>();
		}
	}

	// Create DialogueQueue
	DialogueQueue = NewObject<UDialogueQueue>(this);
	if (ensure(DialogueQueue))
	{
		DialogueQueue->Initialize();
		UE_LOG(LogTemp, Log, TEXT("DialogueManager: DialogueQueue initialized"));
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: Failed to create DialogueQueue"));
	}

	// Initialize reentrancy flag
	bProcessingQueue = false;

	// Register world cleanup delegate
	FWorldDelegates::OnWorldCleanup.AddUObject(this, &UDialogueManager::OnWorldCleanup);

	UE_LOG(LogTemp, Log, TEXT("DialogueManager: Subsystem initialized"));
}

void UDialogueManager::Deinitialize()
{
	// Unregister world cleanup delegate
	FWorldDelegates::OnWorldCleanup.RemoveAll(this);

	// Stop and cleanup all active dialogues
	for (auto& Pair : ActiveDialogueComponents)
	{
		if (UAudioComponent* AC = Pair.Value.Get())
		{
			// Remove any bound delegates
			AC->OnAudioFinished.RemoveAll(this);
			AC->Stop();
			// Note: Don't destroy - components are owned by their actors/world
		}
	}
	ActiveDialogueComponents.Empty();
	ActiveDialogueItems.Empty();

	// Clear queue
	if (DialogueQueue)
	{
		DialogueQueue->ClearAll();
		DialogueQueue = nullptr;
	}

	// Clear audio manager reference
	AudioManager.Reset();
	bProcessingQueue = false;

	Super::Deinitialize();
}

void UDialogueManager::InitializeWithAudioManager(UAudioManager* InAudioManager)
{
	if (!InAudioManager)
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: InitializeWithAudioManager called with null AudioManager"));
		return;
	}

	AudioManager = InAudioManager;
	UE_LOG(LogTemp, Log, TEXT("DialogueManager: AudioManager reference set"));
}

FString UDialogueManager::GenerateDialogueID(const FString& NPCID, const FString& Text) const
{
	// Generate unique ID from NPCID + timestamp + hash of text
	FString Timestamp = FString::Printf(TEXT("%lld"), FDateTime::Now().ToUnixTimestamp());
	uint32 TextHash = GetTypeHash(Text);
	return FString::Printf(TEXT("%s_%s_%u"), *NPCID, *Timestamp, TextHash);
}

void UDialogueManager::PlayDialogue(const FString& NPCID, const FString& Text, int32 Priority, const FString& DialogueID)
{
	// Validate inputs
	if (NPCID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: PlayDialogue called with empty NPCID"));
		return;
	}

	if (Text.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: PlayDialogue called with empty Text"));
		return;
	}

	// Generate DialogueID if not provided
	FString FinalDialogueID = DialogueID.IsEmpty() ? GenerateDialogueID(NPCID, Text) : DialogueID;

	// Create dialogue item
	FDialogueItem Item;
	Item.DialogueID = FinalDialogueID;
	Item.NPCID = NPCID;
	Item.Text = Text;
	Item.Priority = FMath::Clamp(Priority, 0, 3);
	Item.SpeakerName = NPCID;  // Default to NPCID, can be overridden later

	// Enqueue dialogue
	PlayDialogueItem(Item);
}

void UDialogueManager::PlayDialogueItem(const FDialogueItem& Item)
{
	// Validate item
	if (Item.DialogueID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: PlayDialogueItem called with empty DialogueID"));
		return;
	}

	if (!DialogueQueue)
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: DialogueQueue is null"));
		return;
	}

	// Enqueue dialogue
	DialogueQueue->EnqueueDialogue(Item);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Enqueued dialogue %s (Priority: %d)"),
		*Item.DialogueID, Item.Priority);

	// Process queue (try to play immediately if possible)
	ProcessNextDialogue();
}

void UDialogueManager::StopDialogue(const FString& DialogueID)
{
	if (DialogueID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: StopDialogue called with empty DialogueID"));
		return;
	}

	// Stop audio component
	if (UAudioComponent* AudioComp = ActiveDialogueComponents.FindRef(DialogueID))
	{
		AudioComp->Stop();
		AudioComp->DestroyComponent();
		ActiveDialogueComponents.Remove(DialogueID);
	}

	// Mark as inactive in queue
	if (DialogueQueue)
	{
		DialogueQueue->MarkDialogueInactive(DialogueID);
	}

	// Remove from active items
	ActiveDialogueItems.Remove(DialogueID);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Stopped dialogue %s"), *DialogueID);

	// Process next in queue
	ProcessNextDialogue();
}

bool UDialogueManager::IsDialoguePlaying(const FString& DialogueID) const
{
	if (DialogueID.IsEmpty())
	{
		return false;
	}

	// Check if active in queue
	if (DialogueQueue && DialogueQueue->IsDialogueActive(DialogueID))
	{
		return true;
	}

	// Check if any component is playing (by NPCID - need to find DialogueID mapping)
	const FDialogueItem* Item = ActiveDialogueItems.Find(DialogueID);
	if (Item && !Item->NPCID.IsEmpty())
	{
		const TWeakObjectPtr<UAudioComponent>* Found = ActiveDialogueComponents.Find(Item->NPCID);
		if (Found && Found->IsValid())
		{
			return true;
		}
	}

	return false;
}

FDialogueQueueStatus UDialogueManager::GetQueueStatus() const
{
	if (!DialogueQueue)
	{
		return FDialogueQueueStatus();
	}

	return DialogueQueue->GetQueueStatus();
}

void UDialogueManager::ProcessNextDialogue()
{
	if (!DialogueQueue)
	{
		return;
	}

	if (!AudioManager.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: ProcessNextDialogue - AudioManager not available"));
		return;
	}

	// Reentrancy protection
	if (bProcessingQueue)
	{
		return;
	}

	TGuardValue<bool> GuardProcessing(bProcessingQueue, true);

	// Try to dequeue next dialogue
	FDialogueItem NextItem = DialogueQueue->DequeueNextDialogue();
	if (NextItem.DialogueID.IsEmpty())
	{
		// No dialogue available or concurrency limits reached
		return;
	}

	// Check if this NPC already has active dialogue (priority preemption handled by queue)
	if (TWeakObjectPtr<UAudioComponent>* Found = ActiveDialogueComponents.Find(NextItem.NPCID))
	{
		if (UAudioComponent* AC = Found->Get())
		{
			// Stop existing dialogue for this NPC
			AC->OnAudioFinished.RemoveAll(this);
			AC->Stop();
		}
		ActiveDialogueComponents.Remove(NextItem.NPCID);
	}

	// Mark as active in queue
	DialogueQueue->MarkDialogueActive(NextItem.DialogueID, NextItem);

	// Start playback
	StartDialoguePlayback(NextItem);
}

void UDialogueManager::StartDialoguePlayback(const FDialogueItem& Item)
{
	if (!AudioManager.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: Cannot start playback - AudioManager is null"));
		// Mark as finished to avoid stalling the queue
		if (!bProcessingQueue)
		{
			ProcessNextDialogue();
		}
		return;
	}

	// Store active dialogue item
	ActiveDialogueItems.Add(Item.DialogueID, Item);

	// If audio data already exists, play directly
	if (Item.AudioData.Num() > 0)
	{
		// Use DialogueID as AudioID
		AudioManager->PlayAudioFromBackend(Item.DialogueID, EAudioCategory::Voice, 1.0f);
		
		// TODO: AudioManager needs to return UAudioComponent* or provide callback
		// For now, we track by NPCID and will need to extend AudioManager in future
		// Store placeholder in ActiveDialogueComponents
		// ActiveDialogueComponents.Add(Item.NPCID, nullptr); // Will be set when AudioManager is extended
		
		UE_LOG(LogTemp, Log, TEXT("DialogueManager: Started playback for dialogue %s"), *Item.DialogueID);
		
		// Broadcast event
		OnDialogueStarted.Broadcast(Item.DialogueID, Item.SpeakerName);

		// TODO: Set up completion callback when AudioManager supports it
		// For now, this will need manual polling or AudioManager extension
	}
	else
	{
		// Request TTS from backend (placeholder)
		RequestTTSFromBackend(Item, [this, Item](const TArray<uint8>& AudioData, float Duration)
		{
			// Update item with audio data
			FDialogueItem UpdatedItem = Item;
			UpdatedItem.AudioData = AudioData;
			UpdatedItem.Duration = Duration;

			// Play the audio
			if (AudioManager.IsValid())
			{
				AudioManager->PlayAudioFromBackend(Item.DialogueID, EAudioCategory::Voice, 1.0f);
				
				UE_LOG(LogTemp, Log, TEXT("DialogueManager: Started playback for dialogue %s (from TTS)"), *Item.DialogueID);
				
				// Broadcast event
				OnDialogueStarted.Broadcast(Item.DialogueID, Item.SpeakerName);
			}
		});
	}
}

void UDialogueManager::RequestTTSFromBackend(const FDialogueItem& Item, TFunction<void(const TArray<uint8>&, float)> OnComplete)
{
	// PLACEHOLDER: This will be implemented in Milestone 7 with full backend integration
	// For now, just log and call OnComplete with empty data
	
	UE_LOG(LogTemp, Warning, TEXT("DialogueManager: RequestTTSFromBackend called (placeholder - will be implemented in M7)"));
	UE_LOG(LogTemp, Warning, TEXT("  DialogueID: %s, Text: %s"), *Item.DialogueID, *Item.Text);

	// Call completion with empty data (will fail playback, but system won't hang)
	// In real implementation, this will make HTTP request to TTS backend
	OnComplete(TArray<uint8>(), 0.0f);
}

void UDialogueManager::HandleDialogueFinished(const FString& DialogueID)
{
	if (DialogueID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: HandleDialogueFinished called with empty DialogueID"));
		return;
	}

	// Get dialogue item
	const FDialogueItem* Item = ActiveDialogueItems.Find(DialogueID);
	if (!Item)
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: HandleDialogueFinished called for unknown DialogueID: %s"), *DialogueID);
		return;
	}

	// Remove from active components (by NPCID)
	ActiveDialogueComponents.Remove(Item->NPCID);

	// Mark as inactive in queue
	if (DialogueQueue)
	{
		DialogueQueue->MarkDialogueInactive(DialogueID);
	}

	// Remove from active items
	ActiveDialogueItems.Remove(DialogueID);

	// Broadcast completion event
	OnDialogueComplete.Broadcast(DialogueID);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Dialogue %s completed"), *DialogueID);

	// Process next dialogue in queue
	if (!bProcessingQueue)
	{
		ProcessNextDialogue();
	}
}

void UDialogueManager::StopDialogueByNPC(const FString& NPCID)
{
	if (NPCID.IsEmpty())
	{
		return;
	}

	// Stop audio component if exists
	if (TWeakObjectPtr<UAudioComponent>* Found = ActiveDialogueComponents.Find(NPCID))
	{
		if (UAudioComponent* AC = Found->Get())
		{
			AC->OnAudioFinished.RemoveAll(this);
			AC->Stop();
		}
		ActiveDialogueComponents.Remove(NPCID);
	}

	// Find and mark dialogue inactive
	FString DialogueIDToRemove;
	for (const auto& Pair : ActiveDialogueItems)
	{
		if (Pair.Value.NPCID == NPCID)
		{
			DialogueIDToRemove = Pair.Key;
			break;
		}
	}

	if (!DialogueIDToRemove.IsEmpty())
	{
		if (DialogueQueue)
		{
			DialogueQueue->MarkDialogueInactive(DialogueIDToRemove);
		}
		ActiveDialogueItems.Remove(DialogueIDToRemove);
	}

	// Continue processing
	if (!bProcessingQueue)
	{
		ProcessNextDialogue();
	}
}

void UDialogueManager::OnWorldCleanup(UWorld* World, bool bSessionEnded, bool bCleanupResources)
{
	// Only cleanup if this is the current world
	UWorld* CurrentWorld = GetWorld();
	if (World != CurrentWorld)
	{
		return;
	}

	// Clear audio components for this world
	for (auto& Pair : ActiveDialogueComponents)
	{
		if (UAudioComponent* AC = Pair.Value.Get())
		{
			AC->OnAudioFinished.RemoveAll(this);
			AC->Stop();
		}
	}
	ActiveDialogueComponents.Empty();

	// Clear active items (they're world-specific)
	ActiveDialogueItems.Empty();

	// Optionally clear queue if it contains world-dependent items
	// For now, keep queue intact for seamless travel scenarios
}

