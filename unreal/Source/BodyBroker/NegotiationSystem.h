// Negotiation/Dialogue System for Dark World Deals

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Http.h"
#include "NegotiationSystem.generated.h"

UENUM(BlueprintType)
enum class ENegotiationTactic : uint8
{
    Intimidate,
    Charm,
    Logic,
    AppealToGreed,
    Riddle
};

UCLASS()
class BODYBROKER_API ANegotiationSystem : public AActor
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Negotiation")
    void StartNegotiation(FString ClientID, float BasePrice, FString ItemQuality);
    
    UFUNCTION(BlueprintCallable, Category = "Negotiation")
    void UseTactic(ENegotiationTactic Tactic);
    
    UFUNCTION(BlueprintCallable, Category = "Negotiation")
    void CompleteNegotiation();
    
    UPROPERTY(BlueprintReadOnly, Category = "Negotiation")
    FString CurrentClientResponse;
    
    UPROPERTY(BlueprintReadOnly, Category = "Negotiation")
    float CurrentOffer = 0.0f;

private:
    TArray<ENegotiationTactic> UsedTactics;
    FString CurrentClientID;
};

