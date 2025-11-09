// Body Broker Game Mode - Main game controller

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "Http.h"
#include "BodyBrokerGameMode.generated.h"

UCLASS()
class BODYBROKER_API ABodyBrokerGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ABodyBrokerGameMode();

    virtual void BeginPlay() override;

    // Connect to Python backend services
    UFUNCTION(BlueprintCallable, Category = "Body Broker")
    void ConnectToBackend();
    
    UFUNCTION(BlueprintCallable, Category = "Body Broker")
    bool IsBackendConnected() const { return bBackendConnected; }
    
    // Initialize Body Broker systems
    UFUNCTION(BlueprintCallable, Category = "Body Broker")
    void InitializeBrokerSystems();

protected:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Body Broker")
    FString BackendURL = TEXT("http://localhost:4100");
    
    UPROPERTY(BlueprintReadOnly, Category = "Body Broker")
    bool bBackendConnected = false;

private:
    void OnConnectionTestResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    FTimerHandle ConnectionRetryTimer;
};
