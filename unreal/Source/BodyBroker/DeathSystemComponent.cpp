// Death System - Soul-Echo and Corpse-Tender Implementation
// Implements Death of Flesh mechanic for The Body Broker

#include "DeathSystemComponent.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "JsonObjectConverter.h"
#include "Kismet/GameplayStatics.h"

UDeathSystemComponent::UDeathSystemComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	VeilFrayLevel = 0;
}

void UDeathSystemComponent::TriggerDeath(FVector DeathLocation, FString World, TArray<FString> GearItems)
{
	// Store death information
	CorpseLocation = DeathLocation;
	VeilFrayLevel++;
	
	UE_LOG(LogTemp, Warning, TEXT("[Death] Player died in %s at location %s"), *World, *DeathLocation.ToString());
	UE_LOG(LogTemp, Warning, TEXT("[Death] Veil Fray Level increased to: %d"), VeilFrayLevel);
	UE_LOG(LogTemp, Warning, TEXT("[Death] Lost %d gear items"), GearItems.Num());
	
	// Create HTTP request to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/death/trigger"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	// Build JSON payload
	FString Payload = FString::Printf(TEXT("{\"location\":{\"x\":%f,\"y\":%f,\"z\":%f},\"world\":\"%s\",\"gear_items\":["),
		DeathLocation.X, DeathLocation.Y, DeathLocation.Z, *World);
	
	for (int32 i = 0; i < GearItems.Num(); i++)
	{
		Payload += FString::Printf(TEXT("\"%s\""), *GearItems[i]);
		if (i < GearItems.Num() - 1) Payload += TEXT(",");
	}
	Payload += TEXT("]}");
	
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->OnProcessRequestComplete().BindUObject(this, &UDeathSystemComponent::OnDeathResponse);
	HttpRequest->ProcessRequest();
	
	// Generate corpse ID
	CurrentCorpseID = FGuid::NewGuid().ToString();
	
	UE_LOG(LogTemp, Log, TEXT("[Death] Corpse ID: %s"), *CurrentCorpseID);
}

void UDeathSystemComponent::StartCorpseRun()
{
	if (CurrentCorpseID.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("[Death] Cannot start corpse run - no active corpse"));
		return;
	}
	
	UE_LOG(LogTemp, Warning, TEXT("[Death] Starting corpse run for: %s"), *CurrentCorpseID);
	UE_LOG(LogTemp, Warning, TEXT("[Death] Corpse location: %s"), *CorpseLocation.ToString());
	UE_LOG(LogTemp, Warning, TEXT("[Death] You are NAKED - running without gear"));
	
	// Create HTTP request to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/death/corpse-run"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	FString Payload = FString::Printf(TEXT("{\"corpse_id\":\"%s\"}"), *CurrentCorpseID);
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->ProcessRequest();
}

void UDeathSystemComponent::BribeCorpseTender(FString TitheItem)
{
	UE_LOG(LogTemp, Warning, TEXT("[Death] Bribing Corpse-Tender with: %s"), *TitheItem);
	UE_LOG(LogTemp, Warning, TEXT("[Death] Veil Fray Level: %d"), VeilFrayLevel);
	
	// Expensive items reduce Veil Fray
	if (TitheItem.Contains(TEXT("Drug")) || TitheItem.Contains(TEXT("Rare")))
	{
		if (VeilFrayLevel > 0)
		{
			VeilFrayLevel--;
			UE_LOG(LogTemp, Log, TEXT("[Death] Corpse-Tender appeased! Veil Fray reduced to: %d"), VeilFrayLevel);
		}
	}
	
	// Create HTTP request to backend
	TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
	HttpRequest->SetURL(TEXT("http://localhost:4100/body-broker/death/bribe"));
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	
	FString Payload = FString::Printf(TEXT("{\"item\":\"%s\",\"veil_fray\":%d}"), *TitheItem, VeilFrayLevel);
	HttpRequest->SetContentAsString(Payload);
	HttpRequest->ProcessRequest();
}

void UDeathSystemComponent::OnDeathResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
	if (!bWasSuccessful || !Response.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("[Death] Failed to communicate with backend"));
		return;
	}
	
	UE_LOG(LogTemp, Log, TEXT("[Death] Backend response: %s"), *Response->GetContentAsString());
}

