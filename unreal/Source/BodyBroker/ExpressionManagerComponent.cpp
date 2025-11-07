// Copyright Epic Games, Inc. All Rights Reserved.

#include "ExpressionManagerComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/DataTable.h"
#include "Engine/World.h"
#include "TimerManager.h"

UExpressionManagerComponent::UExpressionManagerComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, TransitionProgress(1.0f)
	, CurrentTransitionDuration(0.0f)
{
	PrimaryComponentTick.bCanEverTick = true;
	bTickInEditor = false;
}

void UExpressionManagerComponent::BeginPlay()
{
	Super::BeginPlay();

	// Initialize to neutral expression
	CurrentExpression.PrimaryEmotion = EEmotionType::Neutral;
	CurrentExpression.SecondaryEmotion = EEmotionType::Neutral;
	CurrentExpression.PrimaryWeight = 1.0f;
	CurrentExpression.SecondaryWeight = 0.0f;
	TargetExpression = CurrentExpression;
	TransitionProgress = 1.0f;

	// Find skeletal mesh component
	FindSkeletalMeshComponent();

	UE_LOG(LogTemp, Log, TEXT("ExpressionManagerComponent: BeginPlay"));
}

void UExpressionManagerComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Update expression interpolation
	if (TransitionProgress < 1.0f)
	{
		InterpolateExpressionWeights(DeltaTime);
	}

	// Apply blend shape weights to skeletal mesh
	if (SkeletalMeshComponent.IsValid())
	{
		ApplyBlendShapeWeights(CurrentExpression);
	}
}

void UExpressionManagerComponent::SetEmotionalState(EEmotionType Emotion, float Intensity, float TransitionDuration)
{
	Intensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
	TransitionDuration = FMath::Max(0.0f, TransitionDuration);

	EEmotionType OldEmotion = CurrentExpression.PrimaryEmotion;

	// Set target expression
	TargetExpression.PrimaryEmotion = Emotion;
	TargetExpression.SecondaryEmotion = EEmotionType::Neutral;
	TargetExpression.PrimaryWeight = Intensity;
	TargetExpression.SecondaryWeight = 0.0f;

	// Start transition
	CurrentTransitionDuration = TransitionDuration;
	TransitionProgress = 0.0f;

	// Broadcast emotion change event
	if (OldEmotion != Emotion)
	{
		OnExpressionChanged.Broadcast(OldEmotion, Emotion);
	}

	UE_LOG(LogTemp, Log, TEXT("ExpressionManagerComponent: Setting emotion to %d with intensity %f"), (int32)Emotion, Intensity);
}

void UExpressionManagerComponent::BlendEmotions(EEmotionType PrimaryEmotion, EEmotionType SecondaryEmotion, float BlendAmount, float TransitionDuration)
{
	BlendAmount = FMath::Clamp(BlendAmount, 0.0f, 1.0f);
	TransitionDuration = FMath::Max(0.0f, TransitionDuration);

	EEmotionType OldEmotion = CurrentExpression.PrimaryEmotion;

	// Set target expression with blending
	TargetExpression.PrimaryEmotion = PrimaryEmotion;
	TargetExpression.SecondaryEmotion = SecondaryEmotion;
	TargetExpression.PrimaryWeight = 1.0f - BlendAmount;
	TargetExpression.SecondaryWeight = BlendAmount;

	// Start transition
	CurrentTransitionDuration = TransitionDuration;
	TransitionProgress = 0.0f;

	// Broadcast emotion change event if primary changed
	if (OldEmotion != PrimaryEmotion)
	{
		OnExpressionChanged.Broadcast(OldEmotion, PrimaryEmotion);
	}

	UE_LOG(LogTemp, Log, TEXT("ExpressionManagerComponent: Blending emotions %d and %d with blend %f"), 
		(int32)PrimaryEmotion, (int32)SecondaryEmotion, BlendAmount);
}

void UExpressionManagerComponent::SetExpressionPresetTable(UDataTable* PresetTable)
{
	ExpressionPresetTable = PresetTable;
	UE_LOG(LogTemp, Log, TEXT("ExpressionManagerComponent: Expression preset table set"));
}

bool UExpressionManagerComponent::LoadExpressionPreset(EEmotionType Emotion)
{
	if (!ExpressionPresetTable)
	{
		UE_LOG(LogTemp, Warning, TEXT("ExpressionManagerComponent: No expression preset table set"));
		return false;
	}

	FString EmotionName;
	switch (Emotion)
	{
	case EEmotionType::Neutral: EmotionName = TEXT("Neutral"); break;
	case EEmotionType::Happy: EmotionName = TEXT("Happy"); break;
	case EEmotionType::Sad: EmotionName = TEXT("Sad"); break;
	case EEmotionType::Angry: EmotionName = TEXT("Angry"); break;
	case EEmotionType::Surprised: EmotionName = TEXT("Surprised"); break;
	case EEmotionType::Fearful: EmotionName = TEXT("Fearful"); break;
	case EEmotionType::Disgusted: EmotionName = TEXT("Disgusted"); break;
	case EEmotionType::Contempt: EmotionName = TEXT("Contempt"); break;
	case EEmotionType::Excited: EmotionName = TEXT("Excited"); break;
	case EEmotionType::Calm: EmotionName = TEXT("Calm"); break;
	default: EmotionName = TEXT("Neutral"); break;
	}

	FExpressionPresetRow* PresetRow = ExpressionPresetTable->FindRow<FExpressionPresetRow>(FName(*EmotionName), TEXT("LoadExpressionPreset"));
	if (PresetRow)
	{
		// Apply preset blend shapes directly
		if (SkeletalMeshComponent.IsValid() && PresetRow->BlendShapeWeights.Num() > 0)
		{
			// Apply blend shape weights from preset data table
			for (const auto& Pair : PresetRow->BlendShapeWeights)
			{
				SkeletalMeshComponent->SetMorphTarget(FName(*Pair.Key), Pair.Value, false);
			}
		}
		UE_LOG(LogTemp, Log, TEXT("ExpressionManagerComponent: Loaded preset for emotion %s"), *EmotionName);
		return true;
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("ExpressionManagerComponent: Preset not found for emotion %s"), *EmotionName);
		return false;
	}
}

void UExpressionManagerComponent::InterpolateExpressionWeights(float DeltaTime)
{
	if (TransitionProgress >= 1.0f)
	{
		TransitionProgress = 1.0f;
		CurrentExpression = TargetExpression;
		OnExpressionWeightsChanged.Broadcast(CurrentExpression);
		return;
	}

	// Advance transition
	if (CurrentTransitionDuration > 0.0f)
	{
		TransitionProgress += DeltaTime / CurrentTransitionDuration;
		TransitionProgress = FMath::Min(TransitionProgress, 1.0f);
	}
	else
	{
		TransitionProgress = 1.0f;
	}

	// Interpolate weights
	float Alpha = TransitionProgress;
	CurrentExpression.PrimaryWeight = FMath::Lerp(
		CurrentExpression.PrimaryWeight,
		TargetExpression.PrimaryWeight,
		Alpha
	);
	CurrentExpression.SecondaryWeight = FMath::Lerp(
		CurrentExpression.SecondaryWeight,
		TargetExpression.SecondaryWeight,
		Alpha
	);

	// Update emotions if transition complete
	if (TransitionProgress >= 1.0f)
	{
		CurrentExpression.PrimaryEmotion = TargetExpression.PrimaryEmotion;
		CurrentExpression.SecondaryEmotion = TargetExpression.SecondaryEmotion;
	}

	// Broadcast weight changes
	OnExpressionWeightsChanged.Broadcast(CurrentExpression);
}

void UExpressionManagerComponent::ApplyBlendShapeWeights(const FExpressionBlendWeights& Weights)
{
	if (!SkeletalMeshComponent.IsValid())
	{
		return;
	}

	// Get blend shape weights for primary and secondary emotions
	TMap<FString, float> PrimaryWeights = GetBlendShapeWeightsForEmotion(Weights.PrimaryEmotion);
	TMap<FString, float> SecondaryWeights = GetBlendShapeWeightsForEmotion(Weights.SecondaryEmotion);

	// Blend the two weight maps
	TMap<FString, float> FinalWeights = BlendWeightMaps(PrimaryWeights, SecondaryWeights, Weights.SecondaryWeight);

	// Apply to skeletal mesh (blend shapes)
	// SetMorphTarget will handle non-existent morph targets gracefully
	for (const auto& Pair : FinalWeights)
	{
		// SetMorphTarget will return false if the morph target doesn't exist, but won't crash
		SkeletalMeshComponent->SetMorphTarget(FName(*Pair.Key), Pair.Value, false);
	}
}

TMap<FString, float> UExpressionManagerComponent::GetBlendShapeWeightsForEmotion(EEmotionType Emotion) const
{
	TMap<FString, float> Weights;

	// Default weights based on emotion (simplified - in production, load from data table)
	switch (Emotion)
	{
	case EEmotionType::Neutral:
		Weights.Add(TEXT("jaw_open"), 0.0f);
		Weights.Add(TEXT("lip_pucker"), 0.0f);
		break;
	case EEmotionType::Happy:
		Weights.Add(TEXT("jaw_open"), 0.2f);
		Weights.Add(TEXT("lip_pucker"), 0.3f);
		Weights.Add(TEXT("cheek_raise"), 0.5f);
		break;
	case EEmotionType::Sad:
		Weights.Add(TEXT("jaw_open"), 0.1f);
		Weights.Add(TEXT("lip_pucker"), 0.1f);
		Weights.Add(TEXT("brow_lower"), 0.4f);
		break;
	case EEmotionType::Angry:
		Weights.Add(TEXT("jaw_open"), 0.3f);
		Weights.Add(TEXT("lip_pucker"), 0.2f);
		Weights.Add(TEXT("brow_lower"), 0.6f);
		break;
	case EEmotionType::Surprised:
		Weights.Add(TEXT("jaw_open"), 0.5f);
		Weights.Add(TEXT("brow_raise"), 0.6f);
		break;
	default:
		break;
	}

	return Weights;
}

TMap<FString, float> UExpressionManagerComponent::BlendWeightMaps(const TMap<FString, float>& Map1, const TMap<FString, float>& Map2, float BlendAmount) const
{
	TMap<FString, float> Result;

	// Add all keys from Map1
	for (const auto& Pair : Map1)
	{
		float Value2 = Map2.FindRef(Pair.Key);
		Result.Add(Pair.Key, FMath::Lerp(Pair.Value, Value2, BlendAmount));
	}

	// Add keys from Map2 that aren't in Map1
	for (const auto& Pair : Map2)
	{
		if (!Result.Contains(Pair.Key))
		{
			float Value1 = Map1.FindRef(Pair.Key);
			Result.Add(Pair.Key, FMath::Lerp(Value1, Pair.Value, BlendAmount));
		}
	}

	return Result;
}

void UExpressionManagerComponent::FindSkeletalMeshComponent()
{
	if (AActor* Owner = GetOwner())
	{
		SkeletalMeshComponent = Owner->FindComponentByClass<USkeletalMeshComponent>();
		if (SkeletalMeshComponent.IsValid())
		{
			UE_LOG(LogTemp, Log, TEXT("ExpressionManagerComponent: Found skeletal mesh component"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("ExpressionManagerComponent: No skeletal mesh component found on owner"));
		}
	}
}

