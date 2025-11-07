// Copyright Epic Games, Inc. All Rights Reserved.

#include "DialogueManager.h"
#include "AudioManager.h"
#include "VoicePool.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Delegates/Delegate.h"
#include "Http.h"
#include "Json.h"
#include "JsonUtilities.h"
#include "Misc/Base64.h"

void UDialogueManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// GE-003: Set default inference server URL
	InferenceServerURL = TEXT("http://localhost:8000");  // vLLM default port

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

	// Create VoicePool
	VoicePool = NewObject<UVoicePool>(this);
	if (ensure(VoicePool))
	{
		VoicePool->Initialize(8);  // Max 8 concurrent voices per architecture
		
		// Try to set player pawn reference
		if (UWorld* World = GetWorld())
		{
			if (APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(World, 0))
			{
				VoicePool->SetPlayerPawn(PlayerPawn);
			}
		}

		UE_LOG(LogTemp, Log, TEXT("DialogueManager: VoicePool initialized"));
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: Failed to create VoicePool"));
	}

	// Initialize reentrancy flag
	bProcessingQueue = false;

	// Register world cleanup delegate
	// World cleanup delegate (removed - not available in UE5.6.1)
	// FWorldDelegates::OnWorldCleanup.AddUObject(this, &UDialogueManager::OnWorldCleanup);

	UE_LOG(LogTemp, Log, TEXT("DialogueManager: Subsystem initialized"));
}

void UDialogueManager::Deinitialize()
{
	// Unregister world cleanup delegate
	// World cleanup delegate (removed - not available in UE5.6.1)
	// FWorldDelegates::OnWorldCleanup.RemoveAll(this);

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

	// Release all voice pool components
	if (VoicePool)
	{
		// Release any remaining components
		for (auto& Pair : ActiveDialogueComponents)
		{
			if (UAudioComponent* AC = Pair.Value.Get())
			{
				VoicePool->ReleaseVoiceComponent(AC);
			}
		}
		VoicePool = nullptr;
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

	FString DialogueNPCKey = DialogueID;
	if (const FDialogueItem* ExistingItem = ActiveDialogueItems.Find(DialogueID))
	{
		DialogueNPCKey = ExistingItem->NPCID;
	}

	// Stop audio component
	if (TWeakObjectPtr<UAudioComponent>* FoundPtr = ActiveDialogueComponents.Find(DialogueNPCKey))
	{
		if (UAudioComponent* AudioComp = FoundPtr->Get())
		{
			if (IsValid(AudioComp))
			{
				AudioComp->Stop();
				AudioComp->DestroyComponent();
				AudioComponentToDialogueID.Remove(AudioComp);
			}
		}
		ActiveDialogueComponents.Remove(DialogueNPCKey);
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
		UAudioComponent* AC = Found->Get();
		if (IsValid(AC))
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
		UAudioComponent* AudioComp = AudioManager->PlayAudioFromBackendAndGetComponent(Item.DialogueID, EAudioCategory::Voice, 1.0f);
		
		// Store audio component reference
		if (AudioComp)
		{
			ActiveDialogueComponents.Add(Item.NPCID, AudioComp);
			AudioComponentToDialogueID.Add(AudioComp, Item.DialogueID);
			
			// Bind completion callback (dynamic delegate - no parameters)
			AudioComp->OnAudioFinished.AddDynamic(this, &UDialogueManager::OnAudioFinishedCallback);
		}
		else
		{
			// Component not yet available (still loading) - will be set when audio loads
			// Store DialogueID for later callback
			PendingDialogueComponents.Add(Item.DialogueID, Item.NPCID);
			
			// Bind to AudioManager completion event
			if (!AudioManager->OnAudioPlaybackComplete.IsAlreadyBound(this, &UDialogueManager::OnAudioManagerPlaybackComplete))
			{
				AudioManager->OnAudioPlaybackComplete.AddDynamic(this, &UDialogueManager::OnAudioManagerPlaybackComplete);
			}
		}
		
		UE_LOG(LogTemp, Log, TEXT("DialogueManager: Started playback for dialogue %s"), *Item.DialogueID);
		
		// Broadcast dialogue started event
		OnDialogueStarted.Broadcast(Item.DialogueID, Item.SpeakerName);

		// Broadcast subtitle show event
		BroadcastSubtitleShow(Item);

		// Generate and store lip-sync data
		FLipSyncData LipSyncData = GenerateLipSyncData(Item);
		// Store lip-sync data for facial system access
		ActiveLipSyncData.Add(Item.DialogueID, LipSyncData);
		
		// Broadcast lip-sync data to facial system when integration ready
		// (Integration point for ExpressionManagerComponent)
	}
	else
	{
		// Request TTS from backend
		RequestTTSFromBackend(Item, [this](const FDialogueItem& GeneratedItem)
		{
			// Cache generated item for lookup
			ActiveDialogueItems.Add(GeneratedItem.DialogueID, GeneratedItem);

			// Play the audio
			if (AudioManager.IsValid())
			{
				AudioManager->PlayAudioFromBackend(GeneratedItem.DialogueID, EAudioCategory::Voice, 1.0f);
				
				UE_LOG(LogTemp, Log, TEXT("DialogueManager: Started playback for dialogue %s (from TTS)"), *GeneratedItem.DialogueID);
				
				// Broadcast dialogue started event
				OnDialogueStarted.Broadcast(GeneratedItem.DialogueID, GeneratedItem.SpeakerName);

				// Broadcast subtitle show event
				BroadcastSubtitleShow(GeneratedItem);
			}

			// Store lip-sync data generated from TTS metadata
			FLipSyncData LipSyncData = GenerateLipSyncData(GeneratedItem);
			ActiveLipSyncData.Add(GeneratedItem.DialogueID, LipSyncData);
		});
	}
}

void UDialogueManager::RequestTTSFromBackend(const FDialogueItem& Item, TFunction<void(const FDialogueItem&)> OnComplete)
{
	if (!AudioManager.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: RequestTTSFromBackend - AudioManager not available"));
		FDialogueItem FailureItem = Item;
		FailureItem.AudioData.Reset();
		FailureItem.Duration = 0.0f;
		OnComplete(FailureItem);
		return;
	}

	// Get backend URL from AudioManager or use default
	FString BackendURL = TEXT("http://localhost:4000");  // Default TTS backend URL
	if (AudioManager.IsValid())
	{
		FString AudioBackendURL = AudioManager->GetBackendURL();
		if (!AudioBackendURL.IsEmpty())
		{
			// Use AudioManager's backend URL (TTS service typically on same backend)
			BackendURL = AudioBackendURL;
		}
	}
	
	// Build API endpoint
	FString RequestURL = FString::Printf(TEXT("%s/api/tts/generate"), *BackendURL);

	// Create HTTP request
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
	
	// Store completion callback and item data for response handling
	// Note: In production, use proper async callback pattern with member variables
	struct FTTSRequestContext
	{
		FDialogueItem Item;
		TFunction<void(const FDialogueItem&)> OnComplete;
	};
	
	TSharedPtr<FTTSRequestContext> Context = MakeShareable(new FTTSRequestContext);
	Context->Item = Item;
	Context->OnComplete = OnComplete;

	// Bind response handler (using lambda with shared context)
	HttpRequest->OnProcessRequestComplete().BindLambda([this, Context](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
	{
		if (!bWasSuccessful || !Response.IsValid())
		{
			UE_LOG(LogTemp, Error, TEXT("DialogueManager: TTS request failed for dialogue %s"), *Context->Item.DialogueID);
			FDialogueItem FailureItem = Context->Item;
			FailureItem.AudioData.Reset();
			FailureItem.Duration = 0.0f;
			Context->OnComplete(FailureItem);
			return;
		}

		// Parse JSON response
		FString ResponseString = Response->GetContentAsString();
		TSharedPtr<FJsonObject> JsonObject;
		TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

		if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
		{
			UE_LOG(LogTemp, Error, TEXT("DialogueManager: Failed to parse TTS response JSON for dialogue %s"), *Context->Item.DialogueID);
			FDialogueItem FailureItem = Context->Item;
			FailureItem.AudioData.Reset();
			FailureItem.Duration = 0.0f;
			Context->OnComplete(FailureItem);
			return;
		}

		// Extract audio data (base64)
		FString AudioBase64;
		if (!JsonObject->TryGetStringField(TEXT("audio"), AudioBase64))
		{
			UE_LOG(LogTemp, Error, TEXT("DialogueManager: TTS response missing 'audio' field for dialogue %s"), *Context->Item.DialogueID);
			FDialogueItem FailureItem = Context->Item;
			FailureItem.AudioData.Reset();
			FailureItem.Duration = 0.0f;
			Context->OnComplete(FailureItem);
			return;
		}

		// Decode base64 audio
		TArray<uint8> AudioData;
		if (!FBase64::Decode(AudioBase64, AudioData))
		{
			UE_LOG(LogTemp, Error, TEXT("DialogueManager: Failed to decode base64 audio for dialogue %s"), *Context->Item.DialogueID);
			FDialogueItem FailureItem = Context->Item;
			FailureItem.AudioData.Reset();
			FailureItem.Duration = 0.0f;
			Context->OnComplete(FailureItem);
			return;
		}

		// Extract duration
		float Duration = 0.0f;
		JsonObject->TryGetNumberField(TEXT("duration"), Duration);
		if (Duration <= 0.0f)
		{
			// Default duration if missing
			Duration = 3.0f;
		}

		// Extract word timings (optional)
		const TArray<TSharedPtr<FJsonValue>>* WordTimingsArray = nullptr;
		if (JsonObject->TryGetArrayField(TEXT("word_timings"), WordTimingsArray) && WordTimingsArray)
		{
			// Parse word timings - store in Context->Item (mutable)
			for (const TSharedPtr<FJsonValue>& WordTimingValue : *WordTimingsArray)
			{
				if (WordTimingValue->Type == EJson::Object)
				{
					TSharedPtr<FJsonObject> WordTimingObject = WordTimingValue->AsObject();
					if (WordTimingObject.IsValid())
					{
						FWordTiming WordTiming;
						WordTimingObject->TryGetStringField(TEXT("word"), WordTiming.Word);
						WordTimingObject->TryGetNumberField(TEXT("start_time"), WordTiming.StartTime);
						
						// Try to get duration or calculate from end_time
						float EndTime = 0.0f;
						if (WordTimingObject->TryGetNumberField(TEXT("duration"), WordTiming.Duration))
						{
							// Duration provided directly
						}
						else if (WordTimingObject->TryGetNumberField(TEXT("end_time"), EndTime))
						{
							// Calculate duration from end_time
							WordTiming.Duration = FMath::Max(0.0f, EndTime - WordTiming.StartTime);
						}
						else
						{
							// Default duration if neither provided
							WordTiming.Duration = 0.2f; // 200ms default
						}
						
						if (!WordTiming.Word.IsEmpty())
						{
							Context->Item.WordTimings.Add(WordTiming);
						}
					}
				}
			}
		}

		// Extract lip-sync data (optional)
		const TSharedPtr<FJsonObject>* LipSyncObject = nullptr;
		if (JsonObject->TryGetObjectField(TEXT("lipsync"), LipSyncObject) && LipSyncObject && (*LipSyncObject).IsValid())
		{
			// Parse lip-sync data
			TSharedPtr<FJsonObject> LipSyncData = *LipSyncObject;
			
			// Parse phoneme frames
			const TArray<TSharedPtr<FJsonValue>>* PhonemeFramesArray = nullptr;
			if (LipSyncData->TryGetArrayField(TEXT("phonemes"), PhonemeFramesArray) && PhonemeFramesArray)
			{
				for (const TSharedPtr<FJsonValue>& FrameValue : *PhonemeFramesArray)
				{
					if (FrameValue->Type == EJson::Object)
					{
						TSharedPtr<FJsonObject> FrameObject = FrameValue->AsObject();
						if (FrameObject.IsValid())
						{
							FPhonemeFrame PhonemeFrame;
							FrameObject->TryGetStringField(TEXT("phoneme"), PhonemeFrame.Phoneme);
							float PhonemeStartTime = 0.0f;
							float PhonemeDuration = 0.0f;
							FrameObject->TryGetNumberField(TEXT("start_time"), PhonemeStartTime);
							FrameObject->TryGetNumberField(TEXT("duration"), PhonemeDuration);
							PhonemeFrame.StartTime = PhonemeStartTime;
							PhonemeFrame.Duration = PhonemeDuration;
							PhonemeFrame.Time = PhonemeStartTime;  // For backward compatibility
							
							if (!PhonemeFrame.Phoneme.IsEmpty())
							{
								// Store in lip-sync data (will be used when generating FLipSyncData)
								// For now, we store it in the dialogue item for later use
								UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Parsed phoneme frame - %s at %.2fs"), 
									*PhonemeFrame.Phoneme, PhonemeFrame.StartTime);
							}
						}
					}
				}
			}
		}

		UE_LOG(LogTemp, Log, TEXT("DialogueManager: TTS request successful for dialogue %s (duration: %.2fs)"), 
			*Context->Item.DialogueID, Duration);

		// Call completion with audio data
		// Store generated data on context item
		Context->Item.AudioData = AudioData;
		Context->Item.Duration = Duration;

		// Invoke completion with enriched dialogue item
		Context->OnComplete(Context->Item);
	});

	// Build JSON request body
	TSharedPtr<FJsonObject> RequestJson = MakeShareable(new FJsonObject);
	RequestJson->SetStringField(TEXT("text"), Item.Text);
	RequestJson->SetStringField(TEXT("voice_id"), Item.NPCID);  // Use NPCID as voice_id for now
	RequestJson->SetStringField(TEXT("format"), TEXT("wav"));  // Default format
	RequestJson->SetNumberField(TEXT("sample_rate"), 44100);  // Default sample rate

	if (Item.PersonalityTraits.Num() > 0)
	{
		TArray<TSharedPtr<FJsonValue>> PersonalityArray;
		PersonalityArray.Reserve(Item.PersonalityTraits.Num());
		for (const FString& Trait : Item.PersonalityTraits)
		{
			PersonalityArray.Add(MakeShared<FJsonValueString>(Trait));
		}
		RequestJson->SetArrayField(TEXT("personality_traits"), PersonalityArray);
	}

	if (!Item.Emotion.IsEmpty())
	{
		RequestJson->SetStringField(TEXT("emotion"), Item.Emotion);
	}

	// Serialize JSON
	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	FJsonSerializer::Serialize(RequestJson.ToSharedRef(), Writer);

	// Set request properties
	HttpRequest->SetURL(RequestURL);
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	HttpRequest->SetContentAsString(OutputString);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Sending TTS request for dialogue %s"), *Item.DialogueID);

	// Process request
	HttpRequest->ProcessRequest();
}

void UDialogueManager::OnAudioFinishedCallback()
{
	// Identify the dialogue associated with the finished audio component.
	for (auto It = AudioComponentToDialogueID.CreateIterator(); It; ++It)
	{
		const TWeakObjectPtr<UAudioComponent> AudioComp = It.Key();
		if (!AudioComp.IsValid() || !AudioComp->IsPlaying())
		{
			const FString DialogueID = It.Value();
			It.RemoveCurrent();
			HandleDialogueFinished(DialogueID);
			return;
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("DialogueManager: OnAudioFinishedCallback could not resolve finished component"));
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

	// Remove reverse lookup for audio component
	if (TWeakObjectPtr<UAudioComponent>* ComponentPtr = ActiveDialogueComponents.Find(Item->NPCID))
	{
		if (ComponentPtr->IsValid())
		{
			AudioComponentToDialogueID.Remove(*ComponentPtr);
		}
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

	// Remove lip-sync data
	ActiveLipSyncData.Remove(DialogueID);

	// Broadcast completion event
	OnDialogueComplete.Broadcast(DialogueID);

	// Broadcast subtitle hide event
	BroadcastSubtitleHide(DialogueID);

	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Dialogue %s completed"), *DialogueID);

	// Check if there are paused dialogues to resume
	if (PausedDialogues.Num() > 0)
	{
		// Resume the most recently paused dialogue (FIFO - first paused, first resumed)
		FString DialogueIDToResume;
		FDialogueItem DialogueToResume;
		for (auto& Pair : PausedDialogues)
		{
			DialogueIDToResume = Pair.Key;
			DialogueToResume = Pair.Value;
			break; // Resume first paused dialogue
		}

		if (!DialogueIDToResume.IsEmpty() && AudioManager.IsValid())
		{
			// Resume paused dialogue
			AudioManager->ResumeAudio(DialogueIDToResume);
			
			// Mark as active again
			if (DialogueQueue)
			{
				DialogueQueue->MarkDialogueActive(DialogueIDToResume, DialogueToResume);
			}
			ActiveDialogueItems.Add(DialogueIDToResume, DialogueToResume);
			
			// Get audio component and restore reference
			UAudioComponent* AudioComp = AudioManager->GetAudioComponent(DialogueIDToResume);
			if (AudioComp)
			{
				ActiveDialogueComponents.Add(DialogueToResume.NPCID, AudioComp);
				AudioComponentToDialogueID.Add(AudioComp, DialogueIDToResume);
				AudioComp->OnAudioFinished.AddDynamic(this, &UDialogueManager::OnAudioFinishedCallback);
			}

			PausedDialogues.Remove(DialogueIDToResume);
			UE_LOG(LogTemp, Log, TEXT("DialogueManager: Resumed paused dialogue %s"), *DialogueIDToResume);
		}
	}

	// Process next dialogue in queue
	if (!bProcessingQueue)
	{
		ProcessNextDialogue();
	}
}

void UDialogueManager::OnAudioManagerPlaybackComplete(const FString& AudioID, UAudioComponent* AudioComponent)
{
	// Check if this is a pending dialogue component
	FString* NPCIDPtr = PendingDialogueComponents.Find(AudioID);
	if (NPCIDPtr && AudioComponent)
	{
		// Store audio component reference
		ActiveDialogueComponents.Add(*NPCIDPtr, AudioComponent);
		AudioComponentToDialogueID.Add(AudioComponent, AudioID);
		
		// Bind completion callback
		AudioComponent->OnAudioFinished.AddDynamic(this, &UDialogueManager::OnAudioFinishedCallback);
		
		// Remove from pending
		PendingDialogueComponents.Remove(AudioID);
		
		UE_LOG(LogTemp, Log, TEXT("DialogueManager: Audio component loaded for dialogue %s"), *AudioID);
	}

	// If no more pending components, remove delegate binding
	if (PendingDialogueComponents.Num() == 0 && AudioManager.IsValid())
	{
		AudioManager->OnAudioPlaybackComplete.RemoveDynamic(this, &UDialogueManager::OnAudioManagerPlaybackComplete);
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
			AudioComponentToDialogueID.Remove(AC);
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
	if (!AudioManager.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: ExecuteCrossfadeInterrupt - AudioManager not available"));
		ExecuteImmediateInterrupt(NewDialogue, CurrentDialogue);
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("DialogueManager: Crossfade interrupt - %s -> %s"),
		*CurrentDialogue.DialogueID, *NewDialogue.DialogueID);

	// Mark current for crossfade
	CrossfadeProgress.Add(CurrentDialogue.DialogueID, 0.0f);

	// Start fade out for CurrentDialogue (0.5s to 0.0)
	AudioManager->SetVolumeOverTime(CurrentDialogue.DialogueID, 0.0f, CROSSFADE_DURATION);

	// Enqueue and start new dialogue
	DialogueQueue->EnqueueDialogue(NewDialogue);
	DialogueQueue->MarkDialogueActive(NewDialogue.DialogueID, NewDialogue);
	StartDialoguePlayback(NewDialogue);

	// Start fade in for NewDialogue (0.5s from 0.0 to 1.0)
	// Note: AudioManager will handle the fade, but we need to set initial volume to 0
	UAudioComponent* NewAudioComp = AudioManager->GetAudioComponent(NewDialogue.DialogueID);
	if (NewAudioComp)
	{
		NewAudioComp->SetVolumeMultiplier(0.0f);
		AudioManager->SetVolumeOverTime(NewDialogue.DialogueID, 1.0f, CROSSFADE_DURATION);
	}

	// Schedule stop of CurrentDialogue after fade completes
	if (UWorld* World = GetWorld())
	{
		FTimerHandle StopTimerHandle;
		FTimerDelegate StopDelegate;
		FString DialogueIDToStop = CurrentDialogue.DialogueID;  // Capture by value
		StopDelegate.BindLambda([this, DialogueIDToStop]()
		{
			StopDialogue(DialogueIDToStop);
		});
		World->GetTimerManager().SetTimer(StopTimerHandle, StopDelegate, CROSSFADE_DURATION, false);
	}
}

void UDialogueManager::ExecutePauseAndResumeInterrupt(const FDialogueItem& NewDialogue, const FDialogueItem& CurrentDialogue)
{
	if (!AudioManager.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: ExecutePauseAndResumeInterrupt - AudioManager not available"));
		ExecuteImmediateInterrupt(NewDialogue, CurrentDialogue);
		return;
	}

	// Pause current dialogue (store state for resume)
	PausedDialogues.Add(CurrentDialogue.DialogueID, CurrentDialogue);

	// Pause current playback using AudioManager
	AudioManager->PauseAudio(CurrentDialogue.DialogueID);

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

	// When NewDialogue completes, check PausedDialogues and resume CurrentDialogue
	// This will be handled in HandleDialogueFinished
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

FString UDialogueManager::PhonemeToViseme(const FString& Phoneme) const
{
	// Phoneme-to-Viseme Mapping (from architecture doc - ARPAbet to viseme)
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

	const FString* Viseme = PhonemeToVisemeMap.Find(Phoneme.ToUpper());
	if (Viseme)
	{
		return *Viseme;
	}

	// Default to silence if unknown phoneme
	return TEXT("silence");
}

TMap<FString, float> UDialogueManager::GetBlendshapeWeightsForViseme(const FString& Viseme) const
{
	// Viseme-to-Blendshape Mapping (from architecture doc)
	static const TMap<FString, TMap<FString, float>> VisemeToBlendshapes = {
		{"silence", {{TEXT("jaw_open"), 0.0f}, {TEXT("lip_pucker"), 0.0f}}},
		{"a", {{TEXT("jaw_open"), 0.8f}, {TEXT("mouth_wide"), 0.6f}}},
		{"p", {{TEXT("lip_pucker"), 0.9f}, {TEXT("jaw_open"), 0.2f}}},
		{"f", {{TEXT("lip_stretch"), 0.7f}, {TEXT("jaw_open"), 0.3f}}},
		{"th", {{TEXT("lip_stretch"), 0.8f}, {TEXT("jaw_open"), 0.4f}}},
		{"i", {{TEXT("jaw_open"), 0.4f}, {TEXT("mouth_wide"), 0.5f}}},
		{"u", {{TEXT("lip_pucker"), 0.6f}, {TEXT("jaw_open"), 0.5f}}},
		{"o", {{TEXT("lip_pucker"), 0.4f}, {TEXT("jaw_open"), 0.6f}}},
		{"r", {{TEXT("lip_stretch"), 0.3f}, {TEXT("jaw_open"), 0.3f}}},
		{"s", {{TEXT("lip_stretch"), 0.5f}, {TEXT("jaw_open"), 0.2f}}},
		{"sh", {{TEXT("lip_pucker"), 0.7f}, {TEXT("jaw_open"), 0.2f}}},
		{"j", {{TEXT("lip_pucker"), 0.6f}, {TEXT("jaw_open"), 0.3f}}},
		{"t", {{TEXT("lip_stretch"), 0.4f}, {TEXT("jaw_open"), 0.3f}}},
		{"k", {{TEXT("jaw_open"), 0.5f}, {TEXT("lip_stretch"), 0.2f}}}
	};

	const TMap<FString, float>* Blendshapes = VisemeToBlendshapes.Find(Viseme);
	if (Blendshapes)
	{
		return *Blendshapes;
	}

	// Default to silence blendshapes
	return TMap<FString, float>{{TEXT("jaw_open"), 0.0f}, {TEXT("lip_pucker"), 0.0f}};
}

FLipSyncData UDialogueManager::GenerateLipSyncData(const FDialogueItem& Item) const
{
	FLipSyncData LipSyncData;
	LipSyncData.AudioID = Item.DialogueID;
	LipSyncData.DialogueID = Item.DialogueID;

	// Generate phoneme frames from word timings if available
	if (Item.WordTimings.Num() > 0)
	{
		// NOTE: Approximate phoneme frames are generated from word timings when backend data is unavailable
		float CurrentTime = 0.0f;
		for (const FWordTiming& WordTiming : Item.WordTimings)
		{
			// Create frames for this word (approximate - 1 frame per word for now)
			// In future, this will be replaced with phoneme-level data from backend
			FPhonemeFrame Frame;
			Frame.Time = WordTiming.StartTime;
			// Convert word to phonemes (simplified - uses first letter as phoneme approximation)
			// In production, use phoneme analysis library or backend service
			// For now, use simplified mapping based on first letter
			FString FirstChar = WordTiming.Word.Left(1).ToUpper();
			if (FirstChar == TEXT("A") || FirstChar == TEXT("E") || FirstChar == TEXT("I") || FirstChar == TEXT("O") || FirstChar == TEXT("U"))
			{
				Frame.Phoneme = TEXT("AA");  // Vowel approximation
			}
			else
			{
				Frame.Phoneme = TEXT("M");  // Consonant approximation
			}
			Frame.Viseme = PhonemeToViseme(Frame.Phoneme);
			LipSyncData.Frames.Add(Frame);

			CurrentTime = WordTiming.StartTime + WordTiming.Duration;
		}
	}
	else
	{
		// No word timings - create default frame for entire dialogue
		FPhonemeFrame Frame;
		Frame.Time = 0.0f;
		Frame.Phoneme = TEXT("SIL");  // Silence
		Frame.Viseme = TEXT("silence");
		LipSyncData.Frames.Add(Frame);
	}

	// Calculate blendshape weights from current viseme (first frame)
	if (LipSyncData.Frames.Num() > 0)
	{
		LipSyncData.BlendshapeWeights = GetBlendshapeWeightsForViseme(LipSyncData.Frames[0].Viseme);
	}
	else
	{
		// Default to silence
		LipSyncData.BlendshapeWeights = GetBlendshapeWeightsForViseme(TEXT("silence"));
	}
	
	return LipSyncData;
}

// GE-003: Request NPC dialogue from AI inference server
void UDialogueManager::RequestNPCDialogue(
	const FString& NPCID,
	const FString& PlayerPrompt,
	const FString& ContextJSON,
	int32 Tier,
	const FString& LoRAAdapter
)
{
	FDialogueInferenceRequest Request;
	Request.NPCID = NPCID;
	Request.PlayerPrompt = PlayerPrompt;
	Request.ContextJSON = ContextJSON;
	Request.Tier = Tier;
	Request.LoRAAdapter = LoRAAdapter;
	
	RequestNPCDialogueWithRequest(Request);
}

// GE-003: Request NPC dialogue with full request structure
void UDialogueManager::RequestNPCDialogueWithRequest(const FDialogueInferenceRequest& Request)
{
	// Create HTTP request
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = CreateInferenceRequest(
		Request.NPCID,
		Request.PlayerPrompt,
		Request.ContextJSON,
		Request.Tier,
		Request.LoRAAdapter
	);
	
	// Store context for response handling
	struct FInferenceRequestContext
	{
		FString NPCID;
		FString PlayerPrompt;
		float StartTime;
	};
	
	TSharedPtr<FInferenceRequestContext> Context = MakeShareable(new FInferenceRequestContext);
	Context->NPCID = Request.NPCID;
	Context->PlayerPrompt = Request.PlayerPrompt;
	Context->StartTime = FPlatformTime::Seconds();
	
	// Bind response handler
	HttpRequest->OnProcessRequestComplete().BindLambda([this, Context](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
	{
		OnInferenceResponseReceived(Request, Response, bWasSuccessful, Context->NPCID, Context->PlayerPrompt);
	});
	
	// Process request
	HttpRequest->ProcessRequest();
}

// GE-003: Handle HTTP response from inference server
void UDialogueManager::OnInferenceResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful, FString NPCID, FString PlayerPrompt)
{
	FDialogueInferenceResponse InferenceResponse;
	
	if (!bWasSuccessful || !Response.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: Inference request failed for NPC %s"), *NPCID);
		InferenceResponse.bSuccess = false;
		InferenceResponse.ErrorMessage = TEXT("HTTP request failed");
		OnDialogueInferenceComplete.Broadcast(NPCID, InferenceResponse);
		return;
	}
	
	int32 ResponseCode = Response->GetResponseCode();
	if (ResponseCode != 200)
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: Inference request returned error code: %d"), ResponseCode);
		InferenceResponse.bSuccess = false;
		InferenceResponse.ErrorMessage = FString::Printf(TEXT("HTTP %d"), ResponseCode);
		OnDialogueInferenceComplete.Broadcast(NPCID, InferenceResponse);
		return;
	}
	
	// Parse JSON response
	FString ResponseContent = Response->GetContentAsString();
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseContent);
	
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("DialogueManager: Failed to parse inference response JSON"));
		InferenceResponse.bSuccess = false;
		InferenceResponse.ErrorMessage = TEXT("Invalid JSON response");
		OnDialogueInferenceComplete.Broadcast(NPCID, InferenceResponse);
		return;
	}
	
	// Extract dialogue text from response
	FString DialogueText;
	
	const TArray<TSharedPtr<FJsonValue>>* ChoicesArray;
	if (JsonObject->TryGetArrayField(TEXT("choices"), ChoicesArray) && ChoicesArray->Num() > 0)
	{
		TSharedPtr<FJsonObject> ChoiceObject = (*ChoicesArray)[0]->AsObject();
		
		// Try chat completion format first
		const TSharedPtr<FJsonObject>* MessageObjectPtr = nullptr;
		if (ChoiceObject->TryGetObjectField(TEXT("message"), MessageObjectPtr) && MessageObjectPtr && MessageObjectPtr->IsValid())
		{
			TSharedPtr<FJsonObject> MessageObject = *MessageObjectPtr;
			MessageObject->TryGetStringField(TEXT("content"), DialogueText);
		}
		// Fallback to completion format
		else
		{
			ChoiceObject->TryGetStringField(TEXT("text"), DialogueText);
		}
	}
	
	if (DialogueText.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("DialogueManager: No dialogue text found in inference response"));
		InferenceResponse.bSuccess = false;
		InferenceResponse.ErrorMessage = TEXT("Empty response");
	}
	else
	{
		InferenceResponse.bSuccess = true;
		InferenceResponse.DialogueText = DialogueText;
		UE_LOG(LogTemp, Log, TEXT("DialogueManager: Inference successful for NPC %s"), *NPCID);
	}
	
	// Broadcast completion event
	OnDialogueInferenceComplete.Broadcast(NPCID, InferenceResponse);
}

// GE-003: Create HTTP request for inference
TSharedRef<IHttpRequest, ESPMode::ThreadSafe> UDialogueManager::CreateInferenceRequest(
	const FString& NPCID,
	const FString& PlayerPrompt,
	const FString& ContextJSON,
	int32 Tier,
	const FString& LoRAAdapter
)
{
	// Build API endpoint URL
	FString RequestURL = FString::Printf(TEXT("%s/v1/chat/completions"), *InferenceServerURL);
	
	// Create HTTP request
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(RequestURL);
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	// Build JSON payload
	TSharedPtr<FJsonObject> RequestJson = MakeShareable(new FJsonObject);
	
	// Model selection based on tier
	FString ModelName;
	switch (Tier)
	{
		case 1:
			ModelName = TEXT("phi3:mini");
			break;
		case 2:
			ModelName = TEXT("llama3.1:8b");
			break;
		case 3:
			ModelName = TEXT("llama3.1:8b");
			break;
		default:
			ModelName = TEXT("llama3.1:8b");
	}
	RequestJson->SetStringField(TEXT("model"), ModelName);
	
	// Messages array (chat completion format)
	TArray<TSharedPtr<FJsonValue>> MessagesArray;
	
	// System message with context
	TSharedPtr<FJsonObject> SystemMessage = MakeShareable(new FJsonObject);
	SystemMessage->SetStringField(TEXT("role"), TEXT("system"));
	
	FString SystemPrompt = FString::Printf(
		TEXT("You are an NPC in a game. NPC ID: %s. Context: %s. Respond naturally to the player's question."),
		*NPCID,
		*ContextJSON
	);
	SystemMessage->SetStringField(TEXT("content"), SystemPrompt);
	MessagesArray.Add(MakeShareable(new FJsonValueObject(SystemMessage)));
	
	// User message
	TSharedPtr<FJsonObject> UserMessage = MakeShareable(new FJsonObject);
	UserMessage->SetStringField(TEXT("role"), TEXT("user"));
	UserMessage->SetStringField(TEXT("content"), PlayerPrompt);
	MessagesArray.Add(MakeShareable(new FJsonValueObject(UserMessage)));
	
	RequestJson->SetArrayField(TEXT("messages"), MessagesArray);
	
	// Generation parameters
	RequestJson->SetNumberField(TEXT("max_tokens"), 512);
	RequestJson->SetNumberField(TEXT("temperature"), 0.7);
	
	// LoRA adapter (if specified)
	if (!LoRAAdapter.IsEmpty())
	{
		RequestJson->SetStringField(TEXT("lora_request"), LoRAAdapter);
	}
	
	// Serialize to string
	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	FJsonSerializer::Serialize(RequestJson.ToSharedRef(), Writer);
	
	HttpRequest->SetContentAsString(OutputString);
	
	UE_LOG(LogTemp, VeryVerbose, TEXT("DialogueManager: Sending inference request for NPC %s to %s"), 
		*NPCID, *RequestURL);
	
	return HttpRequest;
}

FLipSyncData UDialogueManager::GetLipSyncData(const FString& DialogueID) const
{
	// Find dialogue item
	const FDialogueItem* Item = ActiveDialogueItems.Find(DialogueID);
	if (!Item)
	{
		// Try to find in all active dialogues
		for (const auto& Pair : ActiveDialogueItems)
		{
			if (Pair.Value.DialogueID == DialogueID)
			{
				return GenerateLipSyncData(Pair.Value);
			}
		}

		// Return empty lip-sync data if not found
		return FLipSyncData();
	}

	return GenerateLipSyncData(*Item);
}

