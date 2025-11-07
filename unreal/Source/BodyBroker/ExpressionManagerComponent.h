// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/DataTable.h"
#include "ExpressionManagerComponent.generated.h"

class UDataTable;
class USkeletalMeshComponent;

/**
 * Emotion types for facial expressions
 */
UENUM(BlueprintType)
enum class EEmotionType : uint8
{
	Neutral		UMETA(DisplayName = "Neutral"),
	Happy		UMETA(DisplayName = "Happy"),
	Sad			UMETA(DisplayName = "Sad"),
	Angry		UMETA(DisplayName = "Angry"),
	Surprised	UMETA(DisplayName = "Surprised"),
	Fearful		UMETA(DisplayName = "Fearful"),
	Disgusted	UMETA(DisplayName = "Disgusted"),
	Contempt	UMETA(DisplayName = "Contempt"),
	Excited		UMETA(DisplayName = "Excited"),
	Calm			UMETA(DisplayName = "Calm"),
	NUM			UMETA(Hidden)
};

/**
 * Expression blend weights structure
 */
USTRUCT(BlueprintType)
struct FExpressionBlendWeights
{
	GENERATED_BODY()

	// Primary emotion weight
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Expression")
	float PrimaryWeight;

	// Secondary emotion weight (for blending)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Expression")
	float SecondaryWeight;

	// Emotion type
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Expression")
	EEmotionType PrimaryEmotion;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Expression")
	EEmotionType SecondaryEmotion;

	FExpressionBlendWeights()
		: PrimaryWeight(1.0f)
		, SecondaryWeight(0.0f)
		, PrimaryEmotion(EEmotionType::Neutral)
		, SecondaryEmotion(EEmotionType::Neutral)
	{}
};

/**
 * Expression preset data table row
 */
USTRUCT(BlueprintType)
struct FExpressionPresetRow : public FTableRowBase
{
	GENERATED_BODY()

	// Emotion type
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Expression")
	EEmotionType EmotionType;

	// Blend shape weights (viseme name -> weight)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Expression")
	TMap<FString, float> BlendShapeWeights;

	// Transition duration (seconds)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Expression")
	float TransitionDuration;

	FExpressionPresetRow()
		: EmotionType(EEmotionType::Neutral)
		, TransitionDuration(0.5f)
	{}
};

/**
 * ExpressionManagerComponent - Manages facial expressions and emotional state
 * FE-001: Core Emotion System
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UExpressionManagerComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UExpressionManagerComponent(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Set emotional state with blending.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Manager|FE-001")
	void SetEmotionalState(EEmotionType Emotion, float Intensity = 1.0f, float TransitionDuration = 0.5f);

	/**
	 * Blend between two emotions.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Manager|FE-001")
	void BlendEmotions(EEmotionType PrimaryEmotion, EEmotionType SecondaryEmotion, float BlendAmount, float TransitionDuration = 0.5f);

	/**
	 * Get current emotional state.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Manager|FE-001")
	EEmotionType GetCurrentEmotion() const { return CurrentExpression.PrimaryEmotion; }

	/**
	 * Get current expression blend weights.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Manager|FE-001")
	FExpressionBlendWeights GetCurrentExpressionWeights() const { return CurrentExpression; }

	/**
	 * Set expression preset data table.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Manager|FE-001")
	void SetExpressionPresetTable(UDataTable* PresetTable);

	/**
	 * Load expression preset by emotion type.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Manager|FE-001")
	bool LoadExpressionPreset(EEmotionType Emotion);

	/**
	 * Event broadcasted when expression changes.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnExpressionChanged, EEmotionType, OldEmotion, EEmotionType, NewEmotion);
	UPROPERTY(BlueprintAssignable, Category = "Expression Manager|FE-001|Events")
	FOnExpressionChanged OnExpressionChanged;

	/**
	 * Event broadcasted when expression blend weights change.
	 */
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnExpressionWeightsChanged, const FExpressionBlendWeights&, Weights);
	UPROPERTY(BlueprintAssignable, Category = "Expression Manager|FE-001|Events")
	FOnExpressionWeightsChanged OnExpressionWeightsChanged;

private:
	// Current expression blend weights
	UPROPERTY()
	FExpressionBlendWeights CurrentExpression;

	// Target expression blend weights (for interpolation)
	UPROPERTY()
	FExpressionBlendWeights TargetExpression;

	// Transition progress (0.0 to 1.0)
	UPROPERTY()
	float TransitionProgress;

	// Current transition duration
	UPROPERTY()
	float CurrentTransitionDuration;

	// Expression preset data table
	UPROPERTY()
	TObjectPtr<UDataTable> ExpressionPresetTable;

	// Skeletal mesh component reference (for blend shape control)
	UPROPERTY()
	TWeakObjectPtr<USkeletalMeshComponent> SkeletalMeshComponent;

	// Interpolate expression weights
	void InterpolateExpressionWeights(float DeltaTime);

	// Apply blend shape weights to skeletal mesh
	void ApplyBlendShapeWeights(const FExpressionBlendWeights& Weights);

	// Get blend shape weights for emotion from preset table
	TMap<FString, float> GetBlendShapeWeightsForEmotion(EEmotionType Emotion) const;

	// Blend two emotion weight maps
	TMap<FString, float> BlendWeightMaps(const TMap<FString, float>& Map1, const TMap<FString, float>& Map2, float BlendAmount) const;

	// Find skeletal mesh component on owner
	void FindSkeletalMeshComponent();
};

