// Copyright Epic Games, Inc. All Rights Reserved.

#include "DialogueQueue.h"
#include "Engine/Engine.h"

UDialogueQueue::UDialogueQueue(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// Initialize will be called explicitly to set up concurrency limits
}

void UDialogueQueue::Initialize()
{
	// Set concurrency limits by priority (from architecture doc)
	MaxConcurrentByPriority.Empty();
	MaxConcurrentByPriority.Add(0, 1);  // Critical: 1 voice only
	MaxConcurrentByPriority.Add(1, 2);  // High: 2 voices max
	MaxConcurrentByPriority.Add(2, 4);  // Medium: 4 voices max
	MaxConcurrentByPriority.Add(3, 8);  // Low: 8 voices max

	// Initialize active count tracking
	ActiveCountByPriority.Empty();
	ActiveCountByPriority.Add(0, 0);
	ActiveCountByPriority.Add(1, 0);
	ActiveCountByPriority.Add(2, 0);
	ActiveCountByPriority.Add(3, 0);

	UE_LOG(LogTemp, Log, TEXT("DialogueQueue: Initialized with priority system"));
}

void UDialogueQueue::EnqueueDialogue(const FDialogueItem& Item)
{
	// Clamp priority to valid range (0-3)
	int32 ValidPriority = FMath::Clamp(Item.Priority, 0, 3);

	// Get the appropriate queue
	TArray<FDialogueItem>* Queue = GetQueueForPriority(ValidPriority);
	if (!Queue)
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueQueue: Invalid priority %d, defaulting to Medium (2)"), ValidPriority);
		ValidPriority = 2;
		Queue = GetQueueForPriority(ValidPriority);
	}

	if (Queue)
	{
		// Add to end of queue (FIFO within same priority)
		Queue->Add(Item);

		UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueQueue: Enqueued dialogue %s with priority %d (queue size: %d)"),
			*Item.DialogueID, ValidPriority, Queue->Num());
	}
}

FDialogueItem UDialogueQueue::DequeueNextDialogue()
{
	FDialogueItem EmptyItem;

	// Check queues in priority order (0 = highest priority)
	for (int32 Priority = 0; Priority <= 3; Priority++)
	{
		TArray<FDialogueItem>* Queue = GetQueueForPriority(Priority);
		if (!Queue)
		{
			continue;
		}

		// Check if we can play this priority level
		if (!CanPlayDialogue(Priority))
		{
			// Can't play this priority yet due to concurrency limits
			continue;
		}

		// Check if queue has items
		if (Queue->Num() > 0)
		{
			// Safe removal with move semantics (FIFO - first element)
			FDialogueItem Item = MoveTemp((*Queue)[0]);
			Queue->RemoveAt(0, 1, false);  // Don't shrink immediately for performance

			UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueQueue: Dequeued dialogue %s from priority %d"),
				*Item.DialogueID, Priority);

			return Item;
		}
	}

	// No items available
	return EmptyItem;
}

int32 UDialogueQueue::GetActiveDialogueCount() const
{
	return ActiveDialogues.Num();
}

int32 UDialogueQueue::GetActiveDialogueCountByPriority(int32 Priority) const
{
	const int32* Count = ActiveCountByPriority.Find(Priority);
	return Count ? *Count : 0;
}

bool UDialogueQueue::CanPlayDialogue(int32 Priority) const
{
	// Validate priority range
	if (Priority < 0 || Priority > 3)
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueQueue: CanPlayDialogue called with invalid priority %d"), Priority);
		return false;
	}

	// Clamp priority to valid range
	Priority = FMath::Clamp(Priority, 0, 3);

	// Get max concurrent for this priority
	const int32* MaxConcurrent = MaxConcurrentByPriority.Find(Priority);
	if (!MaxConcurrent)
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueQueue: Priority %d not initialized in MaxConcurrentByPriority"), Priority);
		return false;
	}

	// Get current active count for this priority
	const int32* CurrentCount = ActiveCountByPriority.Find(Priority);
	const int32 Current = CurrentCount ? *CurrentCount : 0;

	// Check if we're under the limit
	bool bCanPlay = Current < *MaxConcurrent;

	return bCanPlay;
}

void UDialogueQueue::MarkDialogueActive(const FString& DialogueID, const FDialogueItem& Item)
{
	// Validate input
	if (DialogueID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueQueue: MarkDialogueActive called with empty DialogueID"));
		return;
	}

	// Check for duplicate
	if (ActiveDialogues.Contains(DialogueID))
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueQueue: Dialogue %s is already active"), *DialogueID);
		return;
	}

	// Add to active dialogues map
	ActiveDialogues.Add(DialogueID, Item);

	// Update active count by priority (incremental)
	int32 Priority = FMath::Clamp(Item.Priority, 0, 3);
	int32* Count = ActiveCountByPriority.Find(Priority);
	if (Count)
	{
		(*Count)++;
	}
	else
	{
		// Initialize if missing (shouldn't happen after Initialize())
		ActiveCountByPriority.Add(Priority, 1);
	}

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueQueue: Marked dialogue %s as active (priority %d, total active: %d)"),
		*DialogueID, Item.Priority, ActiveDialogues.Num());
}

void UDialogueQueue::MarkDialogueInactive(const FString& DialogueID)
{
	// Validate input
	if (DialogueID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueQueue: MarkDialogueInactive called with empty DialogueID"));
		return;
	}

	// Check if dialogue exists and get priority before removal
	const FDialogueItem* Item = ActiveDialogues.Find(DialogueID);
	if (!Item)
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueQueue: Attempted to mark inactive dialogue %s that is not active"),
			*DialogueID);
		return;
	}

	// Get priority before removal
	int32 Priority = FMath::Clamp(Item->Priority, 0, 3);

	// Remove from active dialogues
	ActiveDialogues.Remove(DialogueID);

	// Update active count by priority (incremental)
	int32* Count = ActiveCountByPriority.Find(Priority);
	if (Count)
	{
		(*Count) = FMath::Max(0, (*Count) - 1);
	}
	else
	{
		// Shouldn't happen, but ensure count doesn't go negative
		ActiveCountByPriority.Add(Priority, 0);
	}

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueQueue: Marked dialogue %s as inactive (remaining active: %d)"),
		*DialogueID, ActiveDialogues.Num());
}

FDialogueQueueStatus UDialogueQueue::GetQueueStatus() const
{
	FDialogueQueueStatus Status;

	Status.CriticalQueueSize = CriticalQueue.Num();
	Status.HighQueueSize = HighQueue.Num();
	Status.MediumQueueSize = MediumQueue.Num();
	Status.LowQueueSize = LowQueue.Num();
	Status.ActiveDialogueCount = ActiveDialogues.Num();
	Status.ActiveCountByPriority = ActiveCountByPriority;

	return Status;
}

bool UDialogueQueue::IsDialogueActive(const FString& DialogueID) const
{
	return ActiveDialogues.Contains(DialogueID);
}

void UDialogueQueue::ClearAll()
{
	CriticalQueue.Empty();
	HighQueue.Empty();
	MediumQueue.Empty();
	LowQueue.Empty();
	ActiveDialogues.Empty();

	// Reset active counts
	ActiveCountByPriority.Empty();
	ActiveCountByPriority.Add(0, 0);
	ActiveCountByPriority.Add(1, 0);
	ActiveCountByPriority.Add(2, 0);
	ActiveCountByPriority.Add(3, 0);

	UE_LOG(LogTemp, Log, TEXT("DialogueQueue: Cleared all queues and active dialogues"));
}

TArray<FDialogueItem>* UDialogueQueue::GetQueueForPriority(int32 Priority)
{
	switch (Priority)
	{
	case 0: return &CriticalQueue;
	case 1: return &HighQueue;
	case 2: return &MediumQueue;
	case 3: return &LowQueue;
	default: return nullptr;
	}
}

const TArray<FDialogueItem>* UDialogueQueue::GetQueueForPriority(int32 Priority) const
{
	switch (Priority)
	{
	case 0: return &CriticalQueue;
	case 1: return &HighQueue;
	case 2: return &MediumQueue;
	case 3: return &LowQueue;
	default: return nullptr;
	}
}

void UDialogueQueue::UpdateActiveCountByPriority()
{
	// Full rebuild of active counts (used as fallback or validation)
	// Reset all counts
	for (auto& Pair : ActiveCountByPriority)
	{
		Pair.Value = 0;
	}

	// Count active dialogues by priority
	for (const auto& Pair : ActiveDialogues)
	{
		const FDialogueItem& Item = Pair.Value;
		int32 Priority = FMath::Clamp(Item.Priority, 0, 3);

		int32* Count = ActiveCountByPriority.Find(Priority);
		if (Count)
		{
			(*Count)++;
		}
		else
		{
			// Initialize if missing
			ActiveCountByPriority.Add(Priority, 1);
		}
	}
}

