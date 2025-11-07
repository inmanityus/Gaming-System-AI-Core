// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyLanguageComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "ExpressionManagerComponent.h"
#include "Engine/World.h"
#include "Engine/DataTable.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/UnrealType.h"

UBodyLanguageComponent::UBodyLanguageComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, CurrentIdleVariation(0)
	, LeftHandPosition(FVector::ZeroVector)
	, RightHandPosition(FVector::ZeroVector)
	, LeftHandIKBoneName(TEXT("hand_l"))
	, RightHandIKBoneName(TEXT("hand_r"))
{
	PrimaryComponentTick.bCanEverTick = true;
	bTickInEditor = false;
}

void UBodyLanguageComponent::BeginPlay()
{
	Super::BeginPlay();

	// Find ExpressionManagerComponent
	if (AActor* Owner = GetOwner())
	{
		ExpressionManager = Owner->FindComponentByClass<UExpressionManagerComponent>();
	}

	FindSkeletalMeshComponent();
	LoadGestureMontages();
	CreateIKTargets();

	UE_LOG(LogTemp, Log, TEXT("BodyLanguageComponent: BeginPlay"));
}

void UBodyLanguageComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Update procedural hand positioning if needed
	UpdateIKTargets();
}

void UBodyLanguageComponent::PlayGesture(FName GestureName, float BlendInTime, float BlendOutTime)
{
	if (!SkeletalMeshComponent || !AnimInstance)
	{
		return;
	}

	// Stop current gesture if playing
	StopGesture();

	// Find gesture montage
	if (TObjectPtr<UAnimMontage>* GestureMontage = GestureMontages.Find(GestureName))
	{
		if (*GestureMontage)
		{
			CurrentGestureMontage = *GestureMontage;

			// Play montage
			if (UAnimInstance* AnimInst = SkeletalMeshComponent->GetAnimInstance())
			{
				AnimInst->Montage_Play(CurrentGestureMontage, 1.0f, EMontagePlayReturnType::MontageLength, 0.0f, true);
				UE_LOG(LogTemp, Log, TEXT("BodyLanguageComponent: Playing gesture %s"), *GestureName.ToString());
			}
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("BodyLanguageComponent: Gesture %s not found"), *GestureName.ToString());
	}
}

void UBodyLanguageComponent::StopGesture()
{
	if (CurrentGestureMontage && SkeletalMeshComponent && SkeletalMeshComponent->GetAnimInstance())
	{
		SkeletalMeshComponent->GetAnimInstance()->Montage_Stop(0.2f, CurrentGestureMontage);
		CurrentGestureMontage = nullptr;
	}
}

void UBodyLanguageComponent::SetIdleVariation(int32 VariationIndex)
{
	CurrentIdleVariation = VariationIndex;

	// Update idle animation variation via animation blueprint parameter
	if (AnimInstance)
	{
		SetAnimBlueprintParameter(TEXT("IdleVariation"), VariationIndex);
	}

	UE_LOG(LogTemp, Verbose, TEXT("BodyLanguageComponent: Set idle variation to %d"), VariationIndex);
}

void UBodyLanguageComponent::SetHandPosition(const FVector& LeftHandPos, const FVector& RightHandPos)
{
	LeftHandPosition = LeftHandPos;
	RightHandPosition = RightHandPos;

	// Update procedural hand positioning via IK targets
	UpdateIKTargets();
}

void UBodyLanguageComponent::UpdateBodyLanguageFromEmotion(EEmotionType Emotion, float Intensity)
{
	// Map emotions to gestures/body language
	// In production, this would trigger appropriate gestures or posture changes
	switch (Emotion)
	{
	case EEmotionType::Happy:
		// Play positive gesture
		PlayGesture(TEXT("Happy_Gesture"), 0.2f, 0.2f);
		break;
	case EEmotionType::Sad:
		// Play subdued gesture
		PlayGesture(TEXT("Sad_Gesture"), 0.2f, 0.2f);
		break;
	case EEmotionType::Angry:
		// Play aggressive gesture
		PlayGesture(TEXT("Angry_Gesture"), 0.2f, 0.2f);
		break;
	default:
		// Default body language
		break;
	}
}

void UBodyLanguageComponent::FindSkeletalMeshComponent()
{
	if (AActor* Owner = GetOwner())
	{
		SkeletalMeshComponent = Owner->FindComponentByClass<USkeletalMeshComponent>();
		if (SkeletalMeshComponent)
		{
			AnimInstance = SkeletalMeshComponent->GetAnimInstance();
			UE_LOG(LogTemp, Log, TEXT("BodyLanguageComponent: Found skeletal mesh component"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("BodyLanguageComponent: No skeletal mesh component found"));
		}
	}
}

void UBodyLanguageComponent::LoadGestureMontages()
{
	// Load gesture montages from data table if available
	if (GestureDataTable)
	{
		// Iterate through data table rows
		// Note: This requires a data table structure with gesture name and montage asset
		// For now, log that data table is available
		UE_LOG(LogTemp, Log, TEXT("BodyLanguageComponent: Gesture data table available: %s"), *GestureDataTable->GetName());
		
		// TODO: Implement data table row iteration when gesture data table structure is defined
		// Example structure would be:
		// struct FGestureData : public FTableRowBase
		// {
		//     FName GestureName;
		//     TSoftObjectPtr<UAnimMontage> GestureMontage;
		// };
	}
	else
	{
		// Try to load from asset registry by naming convention
		// This is a fallback if data table is not provided
		UE_LOG(LogTemp, Verbose, TEXT("BodyLanguageComponent: No gesture data table provided, using asset registry fallback"));
		
		// Asset registry loading would go here
		// For now, gesture montages must be manually assigned or loaded via data table
	}
	
	UE_LOG(LogTemp, Log, TEXT("BodyLanguageComponent: Loaded %d gesture montages"), GestureMontages.Num());
}

void UBodyLanguageComponent::CreateIKTargets()
{
	if (!SkeletalMeshComponent || !GetOwner())
	{
		return;
	}

	// Create IK target components for hand positioning
	// Left hand IK target
	if (!LeftHandIKTarget)
	{
		LeftHandIKTarget = NewObject<USceneComponent>(GetOwner(), USceneComponent::StaticClass(), TEXT("LeftHandIKTarget"));
		if (LeftHandIKTarget)
		{
			LeftHandIKTarget->SetupAttachment(SkeletalMeshComponent);
			LeftHandIKTarget->RegisterComponent();
			LeftHandIKTarget->SetWorldLocation(LeftHandPosition);
		}
	}

	// Right hand IK target
	if (!RightHandIKTarget)
	{
		RightHandIKTarget = NewObject<USceneComponent>(GetOwner(), USceneComponent::StaticClass(), TEXT("RightHandIKTarget"));
		if (RightHandIKTarget)
		{
			RightHandIKTarget->SetupAttachment(SkeletalMeshComponent);
			RightHandIKTarget->RegisterComponent();
			RightHandIKTarget->SetWorldLocation(RightHandPosition);
		}
	}

	UE_LOG(LogTemp, Verbose, TEXT("BodyLanguageComponent: Created IK targets"));
}

void UBodyLanguageComponent::UpdateIKTargets()
{
	// Update IK target positions
	if (LeftHandIKTarget)
	{
		LeftHandIKTarget->SetWorldLocation(LeftHandPosition);
	}

	if (RightHandIKTarget)
	{
		RightHandIKTarget->SetWorldLocation(RightHandPosition);
	}

	// Note: Actual IK solving is handled by the animation blueprint or IK Rig system
	// This component provides the target positions, the animation system drives the bones
}

void UBodyLanguageComponent::SetAnimBlueprintParameter(const FName& ParameterName, float Value)
{
	if (!AnimInstance)
	{
		return;
	}

	// Try to set float parameter via reflection
	// This requires the animation blueprint to have the parameter defined
	UClass* AnimClass = AnimInstance->GetClass();
	if (AnimClass)
	{
		FProperty* Property = AnimClass->FindPropertyByName(ParameterName);
		if (Property && Property->IsA<FFloatProperty>())
		{
			FFloatProperty* FloatProp = CastField<FFloatProperty>(Property);
			if (FloatProp)
			{
				FloatProp->SetPropertyValue_InContainer(AnimInstance, Value);
			}
		}
	}
}

void UBodyLanguageComponent::SetAnimBlueprintParameter(const FName& ParameterName, int32 Value)
{
	if (!AnimInstance)
	{
		return;
	}

	// Try to set int32 parameter via reflection
	UClass* AnimClass = AnimInstance->GetClass();
	if (AnimClass)
	{
		FProperty* Property = AnimClass->FindPropertyByName(ParameterName);
		if (Property && Property->IsA<FIntProperty>())
		{
			FIntProperty* IntProp = CastField<FIntProperty>(Property);
			if (IntProp)
			{
				IntProp->SetPropertyValue_InContainer(AnimInstance, Value);
			}
		}
	}
}

