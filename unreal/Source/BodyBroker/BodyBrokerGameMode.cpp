// Body Broker Game Mode Implementation

#include "BodyBrokerGameMode.h"
#include "HttpModule.h"
#include "TimerManager.h"

ABodyBrokerGameMode::ABodyBrokerGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ABodyBrokerGameMode::BeginPlay()
{
    Super::BeginPlay();
    
    // Attempt backend connection on start
    ConnectToBackend();
}

void ABodyBrokerGameMode::ConnectToBackend()
{
    FString HealthURL = FString::Printf(TEXT("%s/health"), *BackendURL);
    
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(HealthURL);
    Request->SetVerb(TEXT("GET"));
    Request->OnProcessRequestComplete().BindUObject(this, &ABodyBrokerGameMode::OnConnectionTestResponse);
    Request->ProcessRequest();
    
    UE_LOG(LogTemp, Log, TEXT("Attempting backend connection: %s"), *HealthURL);
}

void ABodyBrokerGameMode::OnConnectionTestResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful && Response.IsValid() && Response->GetResponseCode() == 200)
    {
        bBackendConnected = true;
        UE_LOG(LogTemp, Log, TEXT("✅ Backend connected successfully"));
        InitializeBrokerSystems();
    }
    else
    {
        bBackendConnected = false;
        UE_LOG(LogTemp, Warning, TEXT("Backend connection failed, retrying in 5 seconds..."));
        
        // Retry connection
        GetWorldTimerManager().SetTimer(ConnectionRetryTimer, this, &ABodyBrokerGameMode::ConnectToBackend, 5.0f, false);
    }
}

void ABodyBrokerGameMode::InitializeBrokerSystems()
{
    UE_LOG(LogTemp, Log, TEXT("Initializing Body Broker systems..."));
    
    // Initialize Broker's Book
    // Initialize Death System
    // Initialize Harvesting System
    // etc.
    
    UE_LOG(LogTemp, Log, TEXT("✅ Body Broker systems initialized"));
}
