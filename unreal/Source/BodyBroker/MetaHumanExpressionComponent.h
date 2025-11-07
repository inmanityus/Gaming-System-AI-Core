// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ExpressionManagerComponent.h"
#include "MetaHumanExpressionComponent.generated.h"

class UAnimInstance;
// Control Rig is accessed via AnimInstance in UE5, not as a separate component

/**
 * MetaHumanExpressionComponent - MetaHuman-specific expression management
 * FE-002: MetaHuman Integration
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UMetaHumanExpressionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMetaHumanExpressionComponent(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Set emotional state for MetaHuman.
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaHuman Expressions|FE-002")
	void SetEmotionalState(EEmotionType Emotion, float Intensity, float TransitionDuration);

	/**
	 * Set eye target for gaze tracking.
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaHuman Expressions|FE-002")
	void SetEyeTarget(const FVector& TargetLocation);

	/**
	 * Enable/disable eye tracking.
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaHuman Expressions|FE-002")
	void SetEyeTrackingEnabled(bool bEnabled);

	/**
	 * Trigger blink animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaHuman Expressions|FE-002")
	void TriggerBlink();

	/**
	 * Set blink frequency (blinks per minute).
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaHuman Expressions|FE-002")
	void SetBlinkFrequency(float BlinksPerMinute);

	/**
	 * Set micro-expression intensity.
	 */
	UFUNCTION(BlueprintCallable, Category = "MetaHuman Expressions|FE-002")
	void SetMicroExpressionIntensity(float Intensity);

private:
	// Reference to ExpressionManagerComponent
	UPROPERTY()
	TObjectPtr<UExpressionManagerComponent> ExpressionManager;

	// Control Rig is accessed via AnimInstance
	// Note: In production, use UAnimInstance::GetControlRig() or AnimControlRigInstance

	// Skeletal mesh component (MetaHuman)
	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> SkeletalMeshComponent;

	// Eye target location
	UPROPERTY()
	FVector EyeTargetLocation;

	// Eye tracking enabled
	UPROPERTY()
	bool bEyeTrackingEnabled;

	// Blink timer
	UPROPERTY()
	float BlinkTimer;

	// Blink frequency (seconds between blinks)
	UPROPERTY()
	float BlinkInterval;

	// Micro-expression intensity
	UPROPERTY()
	float MicroExpressionIntensity;

	// Last blink time
	UPROPERTY()
	float LastBlinkTime;

	// Find Control Rig component
	void FindControlRigComponent();

	// Update eye tracking
	void UpdateEyeTracking(float DeltaTime);

	// Update blink system
	void UpdateBlinkSystem(float DeltaTime);

	// Map emotion to Control Rig values
	void ApplyEmotionToControlRig(EEmotionType Emotion, float Intensity);

	// Set animation blueprint parameter (if available)
	bool SetAnimBlueprintParameter(const FName& ParameterName, float Value);
};

