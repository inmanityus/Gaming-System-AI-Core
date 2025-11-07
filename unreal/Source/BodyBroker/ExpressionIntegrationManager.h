// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ExpressionManagerComponent.h"
#include "MetaHumanExpressionComponent.h"
#include "BodyLanguageComponent.h"
#include "DialogueManager.h"
#include "ExpressionIntegrationManager.generated.h"

/**
 * ExpressionIntegrationManager - Integrates all expression systems with dialogue and personality
 * FE-005: Expression Integration & Polish
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UExpressionIntegrationManager : public UActorComponent
{
	GENERATED_BODY()

public:
	UExpressionIntegrationManager(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Trigger expression from dialogue event.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Integration|FE-005")
	void OnDialogueEvent(const FString& DialogueID, const FString& EventType, const FString& EmotionHint);

	/**
	 * Set personality influence on expressions.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Integration|FE-005")
	void SetPersonalityInfluence(float Agreeableness, float Openness, float Conscientiousness, float Extraversion, float Neuroticism);

	/**
	 * Enable/disable debug visualization.
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Integration|FE-005")
	void SetDebugVisualizationEnabled(bool bEnabled);

	/**
	 * Get current expression state (for debug).
	 */
	UFUNCTION(BlueprintCallable, Category = "Expression Integration|FE-005")
	void GetCurrentExpressionState(EEmotionType& OutPrimaryEmotion, float& OutIntensity, FString& OutStateString) const;

private:
	// Component references
	UPROPERTY()
	TObjectPtr<UExpressionManagerComponent> ExpressionManager;

	UPROPERTY()
	TObjectPtr<UMetaHumanExpressionComponent> MetaHumanExpression;

	UPROPERTY()
	TObjectPtr<UBodyLanguageComponent> BodyLanguage;

	UPROPERTY()
	TObjectPtr<UDialogueManager> DialogueManager;

	// Personality traits (Big Five)
	UPROPERTY()
	float PersonalityAgreeableness;

	UPROPERTY()
	float PersonalityOpenness;

	UPROPERTY()
	float PersonalityConscientiousness;

	UPROPERTY()
	float PersonalityExtraversion;

	UPROPERTY()
	float PersonalityNeuroticism;

	// Debug visualization enabled
	UPROPERTY()
	bool bDebugVisualizationEnabled;

	// Find component references
	void FindComponentReferences();

	// Map emotion hint string to emotion type
	EEmotionType ParseEmotionFromHint(const FString& EmotionHint) const;

	// Apply personality influence to emotion
	EEmotionType ApplyPersonalityInfluence(EEmotionType BaseEmotion, float& OutIntensity) const;

	// Update debug visualization
	void UpdateDebugVisualization() const;
};

