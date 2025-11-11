// Harvesting Mini-game System
// Skill-based body part extraction

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Http.h"
#include "HarvestingMinigame.generated.h"

UENUM(BlueprintType)
enum class EExtractionMethod : uint8
{
    ShotgunBlast,
    BladeKill,
    PoisonKill,
    LiveExtraction
};

UENUM(BlueprintType)
enum class EToolQuality : uint8
{
    Rusty,
    Standard,
    Surgical,
    Advanced
};

UCLASS()
class BODYBROKER_API AHarvestingMinigame : public AActor
{
    GENERATED_BODY()

public:
    AHarvestingMinigame(const FObjectInitializer& ObjectInitializer);
    
    UFUNCTION(BlueprintCallable, Category = "Harvesting")
    void StartExtraction(FString TargetID, EExtractionMethod Method, EToolQuality ToolQuality);
    
    UFUNCTION(BlueprintCallable, Category = "Harvesting")
    void CompleteExtraction(float PlayerSkillRating);
    
    // Decay timer
    UPROPERTY(BlueprintReadWrite, Category = "Harvesting")
    float DecayTimerSeconds = 300.0f; // 5 minutes for mini-game
    
    UPROPERTY(BlueprintReadWrite, Category = "Harvesting")
    float CurrentDecayPercentage = 0.0f;
    
protected:
    virtual void Tick(float DeltaTime) override;
    
private:
    void OnExtractionResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    
    FString CurrentTargetID;
    bool bExtractionInProgress = false;
    FTimerHandle DecayTimerHandle;
};

