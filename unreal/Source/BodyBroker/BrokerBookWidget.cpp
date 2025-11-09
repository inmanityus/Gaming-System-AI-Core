// Broker's Book UI Widget Implementation

#include "BrokerBookWidget.h"
#include "HttpModule.h"
#include "JsonUtilities.h"

void UBrokerBookWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // Initialize book
}

void UBrokerBookWidget::OpenSection(FString SectionName)
{
    // Open book section (Terrors, Poisons, Accounts, Red Market)
    UE_LOG(LogTemp, Log, TEXT("Opening book section: %s"), *SectionName);
}

void UBrokerBookWidget::QueryDrugPrice(FString DrugID)
{
    FString URL = FString::Printf(TEXT("%s/book/drugs/%s"), *APIBaseURL, *DrugID);
    
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(URL);
    Request->SetVerb(TEXT("GET"));
    Request->OnProcessRequestComplete().BindUObject(this, &UBrokerBookWidget::OnDrugPriceResponse);
    Request->ProcessRequest();
}

void UBrokerBookWidget::OnDrugPriceResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful && Response.IsValid())
    {
        FString ResponseString = Response->GetContentAsString();
        UE_LOG(LogTemp, Log, TEXT("Drug price response: %s"), *ResponseString);
        
        // Parse JSON and update UI
        TSharedPtr<FJsonObject> JsonObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);
        
        if (FJsonSerializer::Deserialize(Reader, JsonObject))
        {
            FString Name = JsonObject->GetStringField(TEXT("name"));
            // Update UI with drug information
        }
    }
}

void UBrokerBookWidget::QueryPartPrice(FString PartID)
{
    // Similar to QueryDrugPrice but for body parts
}

void UBrokerBookWidget::GetClientInfo(FString ClientID)
{
    // Query client information from Book
}

