// Negotiation System Implementation
// Dark World client negotiations for The Body Broker

#include "NegotiationSystem.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"

ANegotiationSystem::ANegotiationSystem(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	PrimaryActorTick.bCanEverTick = false;
}

void ANegotiationSystem::StartNegotiation(FString ClientID, float BasePrice, FString ItemQuality)
{
	CurrentClientID = ClientID;
	CurrentOffer = BasePrice;
	UsedTactics.Empty();
	
	UE_LOG(LogTemp, Warning, TEXT("[Negotiation] Starting negotiation with client: %s"), *ClientID);
	UE_LOG(LogTemp, Log, TEXT("[Negotiation] Base price: %.2f, Item quality: %s"), BasePrice, *ItemQuality);
	
	// Different clients respond to different tactics
	// Vampires: Logic, Riddles
	// Zombies: Simple, direct
	// Werewolves: Intimidation, strength
	// Wraiths: Riddles, whispers
	
	FString ClientType = TEXT("Unknown");
	if (ClientID.Contains(TEXT("Vampire"))) ClientType = TEXT("Vampiric Houses");
	else if (ClientID.Contains(TEXT("Zombie"))) ClientType = TEXT("Carrion Kin");
	else if (ClientID.Contains(TEXT("Werewolf"))) ClientType = TEXT("Moon-Clans");
	else if (ClientID.Contains(TEXT("Wraith"))) ClientType = TEXT("Silent Court");
	
	CurrentClientResponse = FString::Printf(TEXT("Dealing with %s..."), *ClientType);
	
	// Send to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/negotiate/start"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	FString Payload = FString::Printf(TEXT("{\"client_id\":\"%s\",\"base_price\":%f,\"quality\":\"%s\"}"),
		*ClientID, BasePrice, *ItemQuality);
	
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->ProcessRequest();
}

void ANegotiationSystem::UseTactic(ENegotiationTactic Tactic)
{
	// Check if tactic already used (some clients penalize repetition)
	if (UsedTactics.Contains(Tactic))
	{
		UE_LOG(LogTemp, Warning, TEXT("[Negotiation] Tactic already used - may be less effective"));
	}
	
	UsedTactics.Add(Tactic);
	
	// Modify offer based on tactic effectiveness
	float Modifier = 1.0f;
	FString TacticName;
	
	switch (Tactic)
	{
		case ENegotiationTactic::Intimidate:
			TacticName = TEXT("Intimidation");
			Modifier = 1.15f; // 15% increase
			CurrentClientResponse = TEXT("You bare your teeth. They step back.");
			break;
			
		case ENegotiationTactic::Charm:
			TacticName = TEXT("Charm");
			Modifier = 1.10f; // 10% increase
			CurrentClientResponse = TEXT("Your words drip honey. They soften.");
			break;
			
		case ENegotiationTactic::Logic:
			TacticName = TEXT("Logic");
			Modifier = 1.08f; // 8% increase
			CurrentClientResponse = TEXT("Cold reasoning. They nod slowly.");
			break;
			
		case ENegotiationTactic::AppealToGreed:
			TacticName = TEXT("Greed");
			Modifier = 1.12f; // 12% increase
			CurrentClientResponse = TEXT("You speak of profit. Their eyes gleam.");
			break;
			
		case ENegotiationTactic::Riddle:
			TacticName = TEXT("Riddle");
			Modifier = 1.20f; // 20% increase (high risk/reward)
			CurrentClientResponse = TEXT("A riddle offered. They lean in, intrigued.");
			break;
	}
	
	CurrentOffer *= Modifier;
	
	UE_LOG(LogTemp, Warning, TEXT("[Negotiation] Used tactic: %s"), *TacticName);
	UE_LOG(LogTemp, Log, TEXT("[Negotiation] New offer: %.2f"), CurrentOffer);
	
	// Send to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/negotiate/tactic"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	FString Payload = FString::Printf(TEXT("{\"client_id\":\"%s\",\"tactic\":%d,\"new_offer\":%f}"),
		*CurrentClientID, static_cast<int32>(Tactic), CurrentOffer);
	
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->ProcessRequest();
}

void ANegotiationSystem::CompleteNegotiation()
{
	UE_LOG(LogTemp, Warning, TEXT("[Negotiation] Negotiation complete with %s"), *CurrentClientID);
	UE_LOG(LogTemp, Warning, TEXT("[Negotiation] Final price: %.2f"), CurrentOffer);
	UE_LOG(LogTemp, Log, TEXT("[Negotiation] Tactics used: %d"), UsedTactics.Num());
	
	// Send completion to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/negotiate/complete"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	FString Payload = FString::Printf(TEXT("{\"client_id\":\"%s\",\"final_price\":%f,\"tactics_used\":%d}"),
		*CurrentClientID, CurrentOffer, UsedTactics.Num());
	
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->ProcessRequest();
	
	// Reset state
	CurrentClientID.Empty();
	CurrentOffer = 0.0f;
	UsedTactics.Empty();
	CurrentClientResponse = TEXT("Deal closed.");
}

