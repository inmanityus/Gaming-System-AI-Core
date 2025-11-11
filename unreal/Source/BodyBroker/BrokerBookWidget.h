// Broker's Book UI Widget for Unreal Engine
// Coder: Claude Sonnet 4.5

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Http.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "BrokerBookWidget.generated.h"

UCLASS()
class BODYBROKER_API UBrokerBookWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;
    
    // Book sections
    UFUNCTION(BlueprintCallable, Category = "Broker Book")
    void OpenSection(FString SectionName);
    
    UFUNCTION(BlueprintCallable, Category = "Broker Book")
    void QueryDrugPrice(FString DrugID);
    
    UFUNCTION(BlueprintCallable, Category = "Broker Book")
    void QueryPartPrice(FString PartID);
    
    UFUNCTION(BlueprintCallable, Category = "Broker Book")
    void GetClientInfo(FString ClientID);
    
    // API communication
    void OnDrugPriceResponse(TSharedPtr<IHttpRequest> Request, TSharedPtr<IHttpResponse> Response, bool bWasSuccessful);
    
private:
    FString APIBaseURL = TEXT("http://localhost:4100/body-broker");
    TSharedPtr<IHttpRequest> CurrentRequest;
};

