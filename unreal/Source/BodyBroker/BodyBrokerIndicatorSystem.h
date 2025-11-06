// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "BodyBrokerIndicatorSystem.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UWidgetComponent;

// Indicator type enum
UENUM(BlueprintType)
enum class EIndicatorType : uint8
{
	EdgeGlow		UMETA(DisplayName = "Edge Glow"),
	ScreenEdge		UMETA(DisplayName = "Screen Edge"),
	MinionNPC		UMETA(DisplayName = "Minion NPC"),
	Contextual		UMETA(DisplayName = "Contextual")
};

// Indicator data structure
USTRUCT(BlueprintType)
struct FIndicatorData
{
	GENERATED_BODY()

	// Target location in world space
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicator")
	FVector TargetLocation;

	// Indicator type
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicator")
	EIndicatorType IndicatorType;

	// Priority (higher = more important)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicator")
	int32 Priority;

	// Duration (0 = permanent until removed)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicator")
	float Duration;

	// Fade in/out duration
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicator")
	float FadeDuration;

	FIndicatorData()
		: TargetLocation(FVector::ZeroVector)
		, IndicatorType(EIndicatorType::EdgeGlow)
		, Priority(1)
		, Duration(0.0f)
		, FadeDuration(0.5f)
	{
	}
};

/**
 * BodyBrokerIndicatorSystem - Subtle visual indicator system
 * GE-006: Helpful Indicators System
 * NO massive arrows - uses subtle edge glows and screen-edge indicators
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UBodyBrokerIndicatorSystem : public UActorComponent
{
	GENERATED_BODY()

public:
	UBodyBrokerIndicatorSystem(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	// Add indicator
	UFUNCTION(BlueprintCallable, Category = "Indicators")
	void AddIndicator(const FIndicatorData& IndicatorData, int32& OutIndicatorID);

	// Remove indicator
	UFUNCTION(BlueprintCallable, Category = "Indicators")
	void RemoveIndicator(int32 IndicatorID);

	// Update indicator target location
	UFUNCTION(BlueprintCallable, Category = "Indicators")
	void UpdateIndicatorLocation(int32 IndicatorID, const FVector& NewLocation);

	// Clear all indicators
	UFUNCTION(BlueprintCallable, Category = "Indicators")
	void ClearAllIndicators();

	// Get indicator count
	UFUNCTION(BlueprintCallable, Category = "Indicators")
	int32 GetIndicatorCount() const { return ActiveIndicators.Num(); }

	// Configuration
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicators|Config")
	float EdgeGlowIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicators|Config")
	FLinearColor EdgeGlowColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicators|Config")
	float ScreenEdgeIndicatorSize;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicators|Config")
	float MaxIndicatorDistance;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicators|Config")
	bool bEnableEdgeGlow;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicators|Config")
	bool bEnableScreenEdge;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Indicators|Config")
	bool bEnableMinionNPC;

private:
	// Active indicators
	UPROPERTY()
	TMap<int32, FIndicatorData> ActiveIndicators;

	// Indicator timers (for duration-based indicators)
	UPROPERTY()
	TMap<int32, float> IndicatorTimers;

	// Next indicator ID
	int32 NextIndicatorID;

	// Edge glow material instance
	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> EdgeGlowMaterial;

	// Screen edge indicator widgets
	UPROPERTY()
	TArray<TObjectPtr<UWidgetComponent>> ScreenEdgeIndicators;

	// Minion NPC reference (if enabled)
	UPROPERTY()
	TObjectPtr<AActor> MinionNPC;

	// Helper functions
	void UpdateEdgeGlowIndicators(float DeltaTime);
	void UpdateScreenEdgeIndicators(float DeltaTime);
	void UpdateMinionNPCIndicator(float DeltaTime);

	// Calculate screen position from world location
	FVector2D WorldToScreenPosition(const FVector& WorldLocation) const;

	// Check if location is on screen
	bool IsLocationOnScreen(const FVector& WorldLocation) const;

	// Create edge glow effect
	void CreateEdgeGlowEffect(int32 IndicatorID, const FIndicatorData& IndicatorData);

	// Create screen edge indicator
	void CreateScreenEdgeIndicator(int32 IndicatorID, const FIndicatorData& IndicatorData);

	// Remove edge glow effect
	void RemoveEdgeGlowEffect(int32 IndicatorID);

	// Remove screen edge indicator
	void RemoveScreenEdgeIndicator(int32 IndicatorID);

	// Fade in/out helpers
	void UpdateIndicatorFade(int32 IndicatorID, float DeltaTime, bool bFadingOut);
};

