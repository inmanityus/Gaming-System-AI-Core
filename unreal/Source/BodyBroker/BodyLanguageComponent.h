// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ExpressionManagerComponent.h"
#include "BodyLanguageComponent.generated.h"

class UAnimInstance;
class UAnimMontage;

/**
 * BodyLanguageComponent - Manages body language animations and gestures
 * FE-004: Body Language System
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UBodyLanguageComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UBodyLanguageComponent(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Play gesture animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "Body Language|FE-004")
	void PlayGesture(FName GestureName, float BlendInTime = 0.2f, float BlendOutTime = 0.2f);

	/**
	 * Stop current gesture.
	 */
	UFUNCTION(BlueprintCallable, Category = "Body Language|FE-004")
	void StopGesture();

	/**
	 * Set idle animation variation based on personality.
	 */
	UFUNCTION(BlueprintCallable, Category = "Body Language|FE-004")
	void SetIdleVariation(int32 VariationIndex);

	/**
	 * Set hand positioning (procedural).
	 */
	UFUNCTION(BlueprintCallable, Category = "Body Language|FE-004")
	void SetHandPosition(const FVector& LeftHandPosition, const FVector& RightHandPosition);

	/**
	 * Update body language based on emotional state.
	 */
	UFUNCTION(BlueprintCallable, Category = "Body Language|FE-004")
	void UpdateBodyLanguageFromEmotion(EEmotionType Emotion, float Intensity);

private:
	// Reference to ExpressionManagerComponent
	UPROPERTY()
	TObjectPtr<UExpressionManagerComponent> ExpressionManager;

	// Skeletal mesh component
	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> SkeletalMeshComponent;

	// Anim instance
	UPROPERTY()
	TObjectPtr<UAnimInstance> AnimInstance;

	// Current gesture montage
	UPROPERTY()
	TObjectPtr<UAnimMontage> CurrentGestureMontage;

	// Gesture montage map
	UPROPERTY()
	TMap<FName, TObjectPtr<UAnimMontage>> GestureMontages;

	// Current idle variation
	UPROPERTY()
	int32 CurrentIdleVariation;

	// Hand positions (for procedural positioning)
	UPROPERTY()
	FVector LeftHandPosition;

	UPROPERTY()
	FVector RightHandPosition;

	// IK bone names (configurable)
	UPROPERTY(EditAnywhere, Category = "Body Language|IK")
	FName LeftHandIKBoneName;

	UPROPERTY(EditAnywhere, Category = "Body Language|IK")
	FName RightHandIKBoneName;

	// IK targets (for procedural positioning)
	UPROPERTY()
	TObjectPtr<USceneComponent> LeftHandIKTarget;

	UPROPERTY()
	TObjectPtr<USceneComponent> RightHandIKTarget;

	// Data table for gesture montages
	UPROPERTY(EditAnywhere, Category = "Body Language|Data")
	TObjectPtr<UDataTable> GestureDataTable;

	// Find skeletal mesh and anim instance
	void FindSkeletalMeshComponent();

	// Load gesture montages from data table or asset registry
	void LoadGestureMontages();

	// Create IK targets for hand positioning
	void CreateIKTargets();

	// Update IK targets with hand positions
	void UpdateIKTargets();

	// Set animation blueprint parameter (if available)
	void SetAnimBlueprintParameter(const FName& ParameterName, float Value);
	void SetAnimBlueprintParameter(const FName& ParameterName, int32 Value);
};

