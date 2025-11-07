// Copyright Epic Games, Inc. All Rights Reserved.

#include "ExpressionIntegrationManager.h"
#include "ExpressionManagerComponent.h"
#include "MetaHumanExpressionComponent.h"
#include "BodyLanguageComponent.h"
#include "DialogueManager.h"
#include "Engine/World.h"

UExpressionIntegrationManager::UExpressionIntegrationManager(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, PersonalityAgreeableness(0.5f)
	, PersonalityOpenness(0.5f)
	, PersonalityConscientiousness(0.5f)
	, PersonalityExtraversion(0.5f)
	, PersonalityNeuroticism(0.5f)
	, bDebugVisualizationEnabled(false)
{
	PrimaryComponentTick.bCanEverTick = true;
	bTickInEditor = false;
}

void UExpressionIntegrationManager::BeginPlay()
{
	Super::BeginPlay();
	FindComponentReferences();
	UE_LOG(LogTemp, Log, TEXT("ExpressionIntegrationManager: BeginPlay"));
}

void UExpressionIntegrationManager::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bDebugVisualizationEnabled)
	{
		UpdateDebugVisualization();
	}
}

void UExpressionIntegrationManager::OnDialogueEvent(const FString& DialogueID, const FString& EventType, const FString& EmotionHint)
{
	// Parse emotion from hint
	EEmotionType Emotion = ParseEmotionFromHint(EmotionHint);
	float Intensity = 1.0f;

	// Apply personality influence
	Emotion = ApplyPersonalityInfluence(Emotion, Intensity);

	// Apply to expression systems
	if (ExpressionManager)
	{
		ExpressionManager->SetEmotionalState(Emotion, Intensity, 0.5f);
	}

	if (MetaHumanExpression)
	{
		MetaHumanExpression->SetEmotionalState(Emotion, Intensity, 0.5f);
	}

	if (BodyLanguage)
	{
		BodyLanguage->UpdateBodyLanguageFromEmotion(Emotion, Intensity);
	}

	UE_LOG(LogTemp, Verbose, TEXT("ExpressionIntegrationManager: Applied emotion %d from dialogue event"), (int32)Emotion);
}

void UExpressionIntegrationManager::SetPersonalityInfluence(float Agreeableness, float Openness, float Conscientiousness, float Extraversion, float Neuroticism)
{
	PersonalityAgreeableness = FMath::Clamp(Agreeableness, 0.0f, 1.0f);
	PersonalityOpenness = FMath::Clamp(Openness, 0.0f, 1.0f);
	PersonalityConscientiousness = FMath::Clamp(Conscientiousness, 0.0f, 1.0f);
	PersonalityExtraversion = FMath::Clamp(Extraversion, 0.0f, 1.0f);
	PersonalityNeuroticism = FMath::Clamp(Neuroticism, 0.0f, 1.0f);

	UE_LOG(LogTemp, Log, TEXT("ExpressionIntegrationManager: Personality influence updated"));
}

void UExpressionIntegrationManager::SetDebugVisualizationEnabled(bool bEnabled)
{
	bDebugVisualizationEnabled = bEnabled;
	UE_LOG(LogTemp, Log, TEXT("ExpressionIntegrationManager: Debug visualization %s"), bEnabled ? TEXT("enabled") : TEXT("disabled"));
}

void UExpressionIntegrationManager::GetCurrentExpressionState(EEmotionType& OutPrimaryEmotion, float& OutIntensity, FString& OutStateString) const
{
	if (ExpressionManager)
	{
		FExpressionBlendWeights Weights = ExpressionManager->GetCurrentExpressionWeights();
		OutPrimaryEmotion = Weights.PrimaryEmotion;
		OutIntensity = Weights.PrimaryWeight;
		OutStateString = FString::Printf(TEXT("Emotion: %d, Intensity: %.2f"), (int32)OutPrimaryEmotion, OutIntensity);
	}
	else
	{
		OutPrimaryEmotion = EEmotionType::Neutral;
		OutIntensity = 0.0f;
		OutStateString = TEXT("No ExpressionManager");
	}
}

void UExpressionIntegrationManager::FindComponentReferences()
{
	if (AActor* Owner = GetOwner())
	{
		ExpressionManager = Owner->FindComponentByClass<UExpressionManagerComponent>();
		MetaHumanExpression = Owner->FindComponentByClass<UMetaHumanExpressionComponent>();
		BodyLanguage = Owner->FindComponentByClass<UBodyLanguageComponent>();

		// DialogueManager is a subsystem, get it via GameInstance
		if (UWorld* World = GetWorld())
		{
			if (UGameInstance* GameInstance = World->GetGameInstance())
			{
				DialogueManager = GameInstance->GetSubsystem<UDialogueManager>();
			}
		}

		UE_LOG(LogTemp, Log, TEXT("ExpressionIntegrationManager: Component references found"));
	}
}

EEmotionType UExpressionIntegrationManager::ParseEmotionFromHint(const FString& EmotionHint) const
{
	// Parse emotion hint string to emotion type
	FString LowerHint = EmotionHint.ToLower();

	if (LowerHint.Contains(TEXT("happy")) || LowerHint.Contains(TEXT("joy")) || LowerHint.Contains(TEXT("smile")))
	{
		return EEmotionType::Happy;
	}
	else if (LowerHint.Contains(TEXT("sad")) || LowerHint.Contains(TEXT("sorrow")) || LowerHint.Contains(TEXT("depressed")))
	{
		return EEmotionType::Sad;
	}
	else if (LowerHint.Contains(TEXT("angry")) || LowerHint.Contains(TEXT("rage")) || LowerHint.Contains(TEXT("mad")))
	{
		return EEmotionType::Angry;
	}
	else if (LowerHint.Contains(TEXT("surprised")) || LowerHint.Contains(TEXT("shocked")) || LowerHint.Contains(TEXT("amazed")))
	{
		return EEmotionType::Surprised;
	}
	else if (LowerHint.Contains(TEXT("fear")) || LowerHint.Contains(TEXT("afraid")) || LowerHint.Contains(TEXT("scared")))
	{
		return EEmotionType::Fearful;
	}
	else if (LowerHint.Contains(TEXT("disgust")) || LowerHint.Contains(TEXT("revulsion")))
	{
		return EEmotionType::Disgusted;
	}
	else if (LowerHint.Contains(TEXT("excited")) || LowerHint.Contains(TEXT("enthusiastic")))
	{
		return EEmotionType::Excited;
	}
	else if (LowerHint.Contains(TEXT("calm")) || LowerHint.Contains(TEXT("peaceful")) || LowerHint.Contains(TEXT("relaxed")))
	{
		return EEmotionType::Calm;
	}

	return EEmotionType::Neutral;
}

EEmotionType UExpressionIntegrationManager::ApplyPersonalityInfluence(EEmotionType BaseEmotion, float& OutIntensity) const
{
	EEmotionType ModifiedEmotion = BaseEmotion;
	float ModifiedIntensity = OutIntensity;

	// Apply personality traits to emotion expression
	switch (BaseEmotion)
	{
	case EEmotionType::Happy:
		// Extraverts express happiness more intensely
		ModifiedIntensity *= (0.5f + PersonalityExtraversion);
		break;

	case EEmotionType::Sad:
		// Neurotic individuals express sadness more intensely
		ModifiedIntensity *= (0.5f + PersonalityNeuroticism);
		break;

	case EEmotionType::Angry:
		// Low agreeableness and high neuroticism increase anger expression
		ModifiedIntensity *= (0.3f + (1.0f - PersonalityAgreeableness) * 0.5f + PersonalityNeuroticism * 0.2f);
		break;

	case EEmotionType::Surprised:
		// Open individuals show more surprise
		ModifiedIntensity *= (0.5f + PersonalityOpenness);
		break;

	case EEmotionType::Excited:
		// Extraverts show more excitement
		ModifiedIntensity *= (0.5f + PersonalityExtraversion * 0.5f);
		break;

	case EEmotionType::Calm:
		// Conscientious individuals show more calm
		ModifiedIntensity *= (0.5f + PersonalityConscientiousness);
		break;

	default:
		break;
	}

	OutIntensity = FMath::Clamp(ModifiedIntensity, 0.0f, 1.0f);
	return ModifiedEmotion;
}

void UExpressionIntegrationManager::UpdateDebugVisualization() const
{
	// In production, this would draw debug information on screen
	// For now, just log the current state
	if (ExpressionManager)
	{
		EEmotionType Emotion;
		float Intensity;
		FString StateString;
		GetCurrentExpressionState(Emotion, Intensity, StateString);
		UE_LOG(LogTemp, VeryVerbose, TEXT("ExpressionIntegrationManager: %s"), *StateString);
	}
}

