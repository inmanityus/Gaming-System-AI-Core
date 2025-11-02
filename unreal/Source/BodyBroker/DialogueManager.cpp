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

	// Check if this NPC already has active dialogue - use interrupt system
	if (TWeakObjectPtr<UAudioComponent>* Found = ActiveDialogueComponents.Find(NextItem.NPCID))
	{
		if (UAudioComponent* AC = Found->Get() && AC->IsValid())
		{
			// Find current dialogue item
			FDialogueItem* CurrentItem = nullptr;
			for (auto& Pair : ActiveDialogueItems)
			{
				if (Pair.Value.NPCID == NextItem.NPCID)
				{
					CurrentItem = &Pair.Value;
					break;
				}
			}

			if (CurrentItem)
			{
				// Use interrupt system to handle priority-based interruption
				EInterruptType InterruptType = DetermineInterruptType(NextItem.Priority, CurrentItem->Priority);
				if (InterruptType != EInterruptType::None)
				{
					HandleDialogueInterrupt(NextItem, InterruptType);
					return;  // Interrupt handled, don't continue with normal playback
				}
				else
				{
					// Cannot interrupt - requeue and skip
					DialogueQueue->EnqueueDialogue(NextItem);
					return;
				}
			}
		}
		// Clean up invalid component
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
		
		// Broadcast dialogue started event
		OnDialogueStarted.Broadcast(Item.DialogueID, Item.SpeakerName);

		// Broadcast subtitle show event
		BroadcastSubtitleShow(Item);

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
				
				// Broadcast dialogue started event
				OnDialogueStarted.Broadcast(Item.DialogueID, Item.SpeakerName);

				// Broadcast subtitle show event
				BroadcastSubtitleShow(UpdatedItem);
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

	// Broadcast subtitle hide event
	BroadcastSubtitleHide(DialogueID);

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

	// Clear paused dialogues and crossfade state
	PausedDialogues.Empty();
	CrossfadeProgress.Empty();
}

EInterruptType UDialogueManager::DetermineInterruptType(int32 NewPriority, int32 CurrentPriority) const
{
	// Clamp priorities to valid range
	NewPriority = FMath::Clamp(NewPriority, 0, 3);
	CurrentPriority = FMath::Clamp(CurrentPriority, 0, 3);

	// Interrupt Priority Matrix (from architecture doc):
	// New\Current     Priority 0    Priority 1    Priority 2    Priority 3
	// Priority 0      Immediate     Immediate     Immediate     Immediate
	// Priority 1      No            Immediate     Crossfade     Crossfade
	// Priority 2      No            No            Crossfade     Crossfade
	// Priority 3      No            No            No            None

	if (NewPriority == 0)
	{
		// Priority 0 (Critical) always interrupts immediately
		return EInterruptType::Immediate;
	}
	else if (NewPriority == 1)
	{
		// Priority 1 (High)
		if (CurrentPriority == 0)
		{
			return EInterruptType::None;  // Cannot interrupt Critical
		}
		else if (CurrentPriority == 1)
		{
			return EInterruptType::Immediate;  // Same priority - immediate
		}
		else
		{
			return EInterruptType::Crossfade;  // Interrupt Medium/Low with crossfade
		}
	}
	else if (NewPriority == 2)
	{
		// Priority 2 (Medium)
		if (CurrentPriority <= 1)
		{
			return EInterruptType::None;  // Cannot interrupt Critical/High
		}
		else if (CurrentPriority == 2)
		{
			return EInterruptType::Crossfade;  // Same priority - crossfade
		}
		else
		{
			return EInterruptType::Crossfade;  // Interrupt Low with crossfade
		}
	}
	else  // NewPriority == 3 (Low)
	{
		// Priority 3 (Low) cannot interrupt anything
		return EInterruptType::None;
	}
}

void UDialogueManager::HandleDialogueInterrupt(const FDialogueItem& NewDialogue, EInterruptType InterruptType)
{
	if (NewDialogue.DialogueID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: HandleDialogueInterrupt called with empty DialogueID"));
		return;
	}

	// Find currently playing dialogue for this NPC
	const FDialogueItem* CurrentItem = nullptr;
	for (const auto& Pair : ActiveDialogueItems)
	{
		if (Pair.Value.NPCID == NewDialogue.NPCID)
		{
			CurrentItem = &Pair.Value;
			break;
		}
	}

	// If no current dialogue, just play normally
	if (!CurrentItem)
	{
		PlayDialogueItem(NewDialogue);
		return;
	}

	// Auto-determine interrupt type if None specified
	if (InterruptType == EInterruptType::None)
	{
		InterruptType = DetermineInterruptType(NewDialogue.Priority, CurrentItem->Priority);
		
		if (InterruptType == EInterruptType::None)
		{
			// Cannot interrupt - enqueue normally
			PlayDialogueItem(NewDialogue);
			return;
		}
	}

	// Execute appropriate interrupt type
	switch (InterruptType)
	{
	case EInterruptType::Immediate:
		ExecuteImmediateInterrupt(NewDialogue, *CurrentItem);
		break;
	case EInterruptType::Crossfade:
		ExecuteCrossfadeInterrupt(NewDialogue, *CurrentItem);
		break;
	case EInterruptType::PauseAndResume:
		ExecutePauseAndResumeInterrupt(NewDialogue, *CurrentItem);
		break;
	default:
		// None or invalid - just enqueue
		PlayDialogueItem(NewDialogue);
		break;
	}
}

void UDialogueManager::ExecuteImmediateInterrupt(const FDialogueItem& NewDialogue, const FDialogueItem& CurrentDialogue)
{
	// Stop current dialogue immediately
	StopDialogue(CurrentDialogue.DialogueID);

	// Enqueue and play new dialogue
	DialogueQueue->EnqueueDialogue(NewDialogue);
	DialogueQueue->MarkDialogueActive(NewDialogue.DialogueID, NewDialogue);
	StartDialoguePlayback(NewDialogue);

	UE_LOG(LogTemp, Log, TEXT("DialogueManager: Immediate interrupt - stopped %s, playing %s"),
		*CurrentDialogue.DialogueID, *NewDialogue.DialogueID);
}

void UDialogueManager::ExecuteCrossfadeInterrupt(const FDialogueItem& NewDialogue, const FDialogueItem& CurrentDialogue)
{
	// TODO: Implement crossfade logic when AudioManager supports volume fade
	// For now, use immediate interrupt as fallback
	// Future: Fade out current over 0.5s, fade in new over 0.5s simultaneously

	UE_LOG(LogTemp, Log, TEXT("DialogueManager: Crossfade interrupt requested - %s -> %s (using immediate for now)"),
		*CurrentDialogue.DialogueID, *NewDialogue.DialogueID);

	// Mark current for crossfade
	CrossfadeProgress.Add(CurrentDialogue.DialogueID, 0.0f);

	// For now, use immediate interrupt until AudioManager fade support
	ExecuteImmediateInterrupt(NewDialogue, CurrentDialogue);

	// TODO: When AudioManager has SetVolumeOverTime:
	// - Start fade out for CurrentDialogue (0.5s to 0.0)
	// - Start fade in for NewDialogue (0.5s from 0.0 to 1.0)
	// - On fade complete, stop CurrentDialogue
}

void UDialogueManager::ExecutePauseAndResumeInterrupt(const FDialogueItem& NewDialogue, const FDialogueItem& CurrentDialogue)
{
	// Pause current dialogue (store state for resume)
	// TODO: AudioManager needs pause/resume support
	// For now, store paused state and stop playback
	
	PausedDialogues.Add(CurrentDialogue.DialogueID, CurrentDialogue);

	// Stop current playback (will resume later)
	if (TWeakObjectPtr<UAudioComponent>* Found = ActiveDialogueComponents.Find(CurrentDialogue.NPCID))
	{
		if (UAudioComponent* AC = Found->Get())
		{
			// TODO: Use AC->SetPaused(true) when available
			AC->Stop();  // For now, stop (will need resume logic)
		}
		ActiveDialogueComponents.Remove(CurrentDialogue.NPCID);
	}

	// Mark inactive in queue (but keep in paused map)
	if (DialogueQueue)
	{
		DialogueQueue->MarkDialogueInactive(CurrentDialogue.DialogueID);
	}

	// Remove from active items (moved to paused)
	ActiveDialogueItems.Remove(CurrentDialogue.DialogueID);

	// Enqueue and play new dialogue
	DialogueQueue->EnqueueDialogue(NewDialogue);
	DialogueQueue->MarkDialogueActive(NewDialogue.DialogueID, NewDialogue);
	StartDialoguePlayback(NewDialogue);

	UE_LOG(LogTemp, Log, TEXT("DialogueManager: PauseAndResume interrupt - paused %s, playing %s"),
		*CurrentDialogue.DialogueID, *NewDialogue.DialogueID);

	// TODO: When NewDialogue completes, check PausedDialogues and resume CurrentDialogue
	// This will be handled in HandleDialogueFinished when resume logic is added
}

FSubtitleData UDialogueManager::CreateSubtitleData(const FDialogueItem& Item) const
{
	FSubtitleData Subtitle;
	Subtitle.Text = Item.Text;
	Subtitle.SpeakerName = Item.SpeakerName.IsEmpty() ? Item.NPCID : Item.SpeakerName;
	Subtitle.DialogueID = Item.DialogueID;
	Subtitle.WordTimings = Item.WordTimings;

	// Calculate timing
	float AudioDuration = Item.Duration > 0.0f ? Item.Duration : 3.0f;  // Default 3s if unknown
	Subtitle.DisplayDuration = AudioDuration + 1.0f;  // Audio duration + 1.0s buffer
	Subtitle.StartTime = 0.0f;  // Start from 0
	Subtitle.EndTime = AudioDuration;

	return Subtitle;
}

void UDialogueManager::BroadcastSubtitleShow(const FDialogueItem& Item)
{
	FSubtitleData Subtitle = CreateSubtitleData(Item);
	OnSubtitleShow.Broadcast(Subtitle, Subtitle.DisplayDuration);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Subtitle shown - %s: %s"),
		*Subtitle.SpeakerName, *Subtitle.Text);
}

void UDialogueManager::BroadcastSubtitleHide(const FString& DialogueID)
{
	OnSubtitleHide.Broadcast(DialogueID);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Subtitle hidden - %s"), *DialogueID);
}

void UDialogueManager::BroadcastSubtitleUpdate(const FDialogueItem& Item, float ElapsedTime)
{
	// Update subtitle text based on word-level timing if available
	FString CurrentText = Item.Text;
	
	if (Item.WordTimings.Num() > 0)
	{
		// Find words that should be highlighted based on elapsed time
		// For now, just broadcast the full text
		// Future: Can highlight individual words based on timing
	}

	OnSubtitleUpdate.Broadcast(Item.DialogueID, CurrentText, ElapsedTime);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Subtitle update - %s: %.2fs"), *Item.DialogueID, ElapsedTime);
}

