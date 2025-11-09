// Veil-Sight - Dual World Rendering System

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "VeilSightComponent.generated.h"

UENUM(BlueprintType)
enum class EVeilFocus : uint8
{
    HumanWorld,
    DarkWorld,
    Both
};

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UVeilSightComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    UVeilSightComponent();
    
    UFUNCTION(BlueprintCallable, Category = "VeilSight")
    void SetFocus(EVeilFocus NewFocus);
    
    UFUNCTION(BlueprintCallable, Category = "VeilSight")
    EVeilFocus GetCurrentFocus() const { return CurrentFocus; }
    
    UFUNCTION(BlueprintCallable, Category = "VeilSight")
    bool CanSeeCreature(AActor* Creature);
    
    // Post-process effects for Dark World visibility
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VeilSight")
    float DarkWorldOpacity = 0.5f;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VeilSight")
    float HumanWorldOpacity = 1.0f;

protected:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    EVeilFocus CurrentFocus = EVeilFocus::Both;
    void UpdatePostProcessEffects();
};

