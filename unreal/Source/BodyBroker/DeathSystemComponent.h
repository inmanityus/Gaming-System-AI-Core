// Death System - Soul-Echo and Corpse-Tender

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Http.h"
#include "DeathSystemComponent.generated.h"

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UDeathSystemComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UDeathSystemComponent();
    
    UFUNCTION(BlueprintCallable, Category = "Death")
    void TriggerDeath(FVector DeathLocation, FString World, TArray<FString> GearItems);
    
    UFUNCTION(BlueprintCallable, Category = "Death")
    void StartCorpseRun();
    
    UFUNCTION(BlueprintCallable, Category = "Death")
    void BribeCorpseTender(FString TitheItem);
    
    UPROPERTY(BlueprintReadOnly, Category = "Death")
    int32 VeilFrayLevel = 0;
    
    UPROPERTY(BlueprintReadOnly, Category = "Death")
    FString CurrentCorpseID;
    
    UPROPERTY(BlueprintReadOnly, Category = "Death")
    FVector CorpseLocation;

private:
    void OnDeathResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
};

