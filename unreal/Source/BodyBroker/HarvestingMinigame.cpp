// Harvesting Mini-game Implementation
// Skill-based body part extraction for The Body Broker

#include "HarvestingMinigame.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "TimerManager.h"
#include "Engine/World.h"

AHarvestingMinigame::AHarvestingMinigame(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	PrimaryActorTick.bCanEverTick = true;
	bExtractionInProgress = false;
	CurrentDecayPercentage = 0.0f;
	DecayTimerSeconds = 300.0f; // 5 minutes default
}

void AHarvestingMinigame::StartExtraction(FString TargetID, EExtractionMethod Method, EToolQuality ToolQuality)
{
	if (bExtractionInProgress)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Harvest] Extraction already in progress"));
		return;
	}
	
	CurrentTargetID = TargetID;
	bExtractionInProgress = true;
	CurrentDecayPercentage = 0.0f;
	
	UE_LOG(LogTemp, Warning, TEXT("[Harvest] Starting extraction of %s"), *TargetID);
	UE_LOG(LogTemp, Log, TEXT("[Harvest] Method: %d, Tool Quality: %d"), 
		static_cast<int32>(Method), static_cast<int32>(ToolQuality));
	
	// Different extraction methods affect part quality
	float MethodModifier = 1.0f;
	switch (Method)
	{
		case EExtractionMethod::ShotgunBlast:
			MethodModifier = 0.3f; // Severe damage
			UE_LOG(LogTemp, Warning, TEXT("[Harvest] Shotgun blast - severe damage to parts"));
			break;
		case EExtractionMethod::BladeKill:
			MethodModifier = 0.7f; // Moderate damage
			UE_LOG(LogTemp, Log, TEXT("[Harvest] Blade kill - moderate damage"));
			break;
		case EExtractionMethod::PoisonKill:
			MethodModifier = 0.9f; // Minimal damage
			UE_LOG(LogTemp, Log, TEXT("[Harvest] Poison kill - parts mostly intact"));
			break;
		case EExtractionMethod::LiveExtraction:
			MethodModifier = 1.0f; // Perfect condition
			UE_LOG(LogTemp, Log, TEXT("[Harvest] Live extraction - highest quality"));
			break;
	}
	
	// Tool quality affects extraction speed and part integrity
	float ToolModifier = 1.0f;
	switch (ToolQuality)
	{
		case EToolQuality::Rusty:
			ToolModifier = 0.5f;
			DecayTimerSeconds = 180.0f; // Slower, more decay
			UE_LOG(LogTemp, Warning, TEXT("[Harvest] Rusty tools - slow extraction"));
			break;
		case EToolQuality::Standard:
			ToolModifier = 1.0f;
			DecayTimerSeconds = 300.0f;
			break;
		case EToolQuality::Surgical:
			ToolModifier = 1.5f;
			DecayTimerSeconds = 450.0f; // Faster, less decay
			UE_LOG(LogTemp, Log, TEXT("[Harvest] Surgical tools - efficient extraction"));
			break;
		case EToolQuality::Advanced:
			ToolModifier = 2.0f;
			DecayTimerSeconds = 600.0f; // Much faster
			UE_LOG(LogTemp, Log, TEXT("[Harvest] Advanced tools - rapid extraction"));
			break;
	}
	
	// Start decay timer
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(DecayTimerHandle, [this]()
		{
			CurrentDecayPercentage = FMath::Min(100.0f, CurrentDecayPercentage + 0.5f);
			if (CurrentDecayPercentage >= 100.0f)
			{
				UE_LOG(LogTemp, Error, TEXT("[Harvest] Parts fully decayed - extraction failed"));
				bExtractionInProgress = false;
			}
		}, 0.1f, true);
	}
	
	// Send to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/harvest/start"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	FString Payload = FString::Printf(TEXT("{\"target_id\":\"%s\",\"method\":%d,\"tool_quality\":%d,\"modifiers\":{\"method\":%f,\"tool\":%f}}"),
		*TargetID, static_cast<int32>(Method), static_cast<int32>(ToolQuality), MethodModifier, ToolModifier);
	
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->OnProcessRequestComplete().BindUObject(this, &AHarvestingMinigame::OnExtractionResponse);
	HttpRequest->ProcessRequest();
}

void AHarvestingMinigame::CompleteExtraction(float PlayerSkillRating)
{
	if (!bExtractionInProgress)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Harvest] No extraction in progress"));
		return;
	}
	
	// Clear decay timer
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(DecayTimerHandle);
	}
	
	// Calculate final part quality
	float DecayPenalty = CurrentDecayPercentage / 100.0f;
	float FinalQuality = PlayerSkillRating * (1.0f - DecayPenalty);
	FinalQuality = FMath::Clamp(FinalQuality, 0.0f, 1.0f);
	
	UE_LOG(LogTemp, Warning, TEXT("[Harvest] Extraction complete!"));
	UE_LOG(LogTemp, Log, TEXT("[Harvest] Player skill: %.2f, Decay penalty: %.2f%%, Final quality: %.2f"),
		PlayerSkillRating, CurrentDecayPercentage, FinalQuality);
	
	// Send completion to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/harvest/complete"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	FString Payload = FString::Printf(TEXT("{\"target_id\":\"%s\",\"quality\":%f,\"skill\":%f,\"decay\":%f}"),
		*CurrentTargetID, FinalQuality, PlayerSkillRating, CurrentDecayPercentage);
	
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->ProcessRequest();
	
	bExtractionInProgress = false;
	CurrentTargetID.Empty();
}

void AHarvestingMinigame::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	
	// Tick only runs during active extraction
	if (bExtractionInProgress)
	{
		// Visual feedback, UI updates, etc. would go here
		// Actual decay is handled by timer callback
	}
}

void AHarvestingMinigame::OnExtractionResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
	if (!bWasSuccessful || !Response.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("[Harvest] Failed to communicate with backend"));
		return;
	}
	
	UE_LOG(LogTemp, Log, TEXT("[Harvest] Backend response: %s"), *Response->GetContentAsString());
}

