// Copyright Epic Games, Inc. All Rights Reserved.

#include "MetaHumanExpressionComponent.h"
#include "Components/SkeletalMeshComponent.h"
// Control Rig is accessed via AnimInstance, not as a separate component
#include "ExpressionManagerComponent.h"
#include "Engine/World.h"
#include "UObject/UnrealType.h"

UMetaHumanExpressionComponent::UMetaHumanExpressionComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, EyeTargetLocation(FVector::ZeroVector)
	, bEyeTrackingEnabled(true)
	, BlinkTimer(0.0f)
	, BlinkInterval(4.0f) // Default: 15 blinks per minute
	, MicroExpressionIntensity(0.1f)
	, LastBlinkTime(0.0f)
{
	PrimaryComponentTick.bCanEverTick = true;
	bTickInEditor = false;
}

void UMetaHumanExpressionComponent::BeginPlay()
{
	Super::BeginPlay();

	// Find ExpressionManagerComponent
	if (AActor* Owner = GetOwner())
	{
		ExpressionManager = Owner->FindComponentByClass<UExpressionManagerComponent>();
		SkeletalMeshComponent = Owner->FindComponentByClass<USkeletalMeshComponent>();
	}

	FindControlRigComponent();

	UE_LOG(LogTemp, Log, TEXT("MetaHumanExpressionComponent: BeginPlay"));
}

void UMetaHumanExpressionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bEyeTrackingEnabled)
	{
		UpdateEyeTracking(DeltaTime);
	}

	UpdateBlinkSystem(DeltaTime);
}

void UMetaHumanExpressionComponent::SetEmotionalState(EEmotionType Emotion, float Intensity, float TransitionDuration)
{
	if (ExpressionManager)
	{
		ExpressionManager->SetEmotionalState(Emotion, Intensity, TransitionDuration);
	}

	// Apply to Control Rig as well
	ApplyEmotionToControlRig(Emotion, Intensity);
}

void UMetaHumanExpressionComponent::SetEyeTarget(const FVector& TargetLocation)
{
	EyeTargetLocation = TargetLocation;
}

void UMetaHumanExpressionComponent::SetEyeTrackingEnabled(bool bEnabled)
{
	bEyeTrackingEnabled = bEnabled;
}

void UMetaHumanExpressionComponent::TriggerBlink()
{
	// Control Rig is accessed via AnimInstance in UE5
	// In production, use: AnimInstance->GetControlRig()->SetControlValue() or similar
	// For now, use blend shapes or anim blueprint parameters
	if (SkeletalMeshComponent)
	{
		// Trigger blink via blend shapes or anim parameters
		SkeletalMeshComponent->SetMorphTarget(FName(TEXT("EyeBlinkLeft")), 1.0f, false);
		SkeletalMeshComponent->SetMorphTarget(FName(TEXT("EyeBlinkRight")), 1.0f, false);

		// Reset after blink duration
		if (UWorld* World = GetWorld())
		{
			FTimerHandle TimerHandle;
			FTimerDelegate Delegate;
			Delegate.BindLambda([this]()
			{
				if (SkeletalMeshComponent)
				{
					SkeletalMeshComponent->SetMorphTarget(FName(TEXT("EyeBlinkLeft")), 0.0f, false);
					SkeletalMeshComponent->SetMorphTarget(FName(TEXT("EyeBlinkRight")), 0.0f, false);
				}
			});
			World->GetTimerManager().SetTimer(TimerHandle, Delegate, 0.15f, false); // 150ms blink
		}

		LastBlinkTime = GetWorld()->GetTimeSeconds();
	}
}

void UMetaHumanExpressionComponent::SetBlinkFrequency(float BlinksPerMinute)
{
	if (BlinksPerMinute > 0.0f)
	{
		BlinkInterval = 60.0f / BlinksPerMinute;
	}
}

void UMetaHumanExpressionComponent::SetMicroExpressionIntensity(float Intensity)
{
	MicroExpressionIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
}

void UMetaHumanExpressionComponent::FindControlRigComponent()
{
	// Control Rig is accessed via AnimInstance in UE5
	if (SkeletalMeshComponent)
	{
		UAnimInstance* AnimInst = SkeletalMeshComponent->GetAnimInstance();
		if (AnimInst)
		{
			// Try to access Control Rig via AnimInstance
			// Note: This requires the animation blueprint to have Control Rig nodes
			// The actual Control Rig instance is created by the animation blueprint
			UE_LOG(LogTemp, Log, TEXT("MetaHumanExpressionComponent: AnimInstance found (Control Rig accessible via AnimInstance)"));
			
			// Control Rig access is done through anim blueprint parameters or direct Control Rig API
			// For now, we use blend shapes as fallback, but the structure is ready for Control Rig
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("MetaHumanExpressionComponent: No AnimInstance found for Control Rig access"));
		}
	}
}

void UMetaHumanExpressionComponent::UpdateEyeTracking(float DeltaTime)
{
	if (!SkeletalMeshComponent || EyeTargetLocation.IsZero() || !bEyeTrackingEnabled)
	{
		return;
	}

	// Calculate eye rotation to look at target
	FVector EyeLocation = SkeletalMeshComponent->GetSocketLocation(FName(TEXT("Eye_Left")));
	FVector DirectionToTarget = (EyeTargetLocation - EyeLocation).GetSafeNormal();

	// Convert direction to rotation
	FRotator EyeRotation = DirectionToTarget.Rotation();

	// Apply eye rotation via Control Rig or anim blueprint parameters
	// Try to set anim blueprint parameters for eye tracking
	if (UAnimInstance* AnimInst = SkeletalMeshComponent->GetAnimInstance())
	{
		// Set eye rotation parameters (requires anim blueprint to have these parameters)
		SetAnimBlueprintParameter(TEXT("EyeRotationX"), EyeRotation.Pitch);
		SetAnimBlueprintParameter(TEXT("EyeRotationY"), EyeRotation.Yaw);
		SetAnimBlueprintParameter(TEXT("EyeRotationZ"), EyeRotation.Roll);
		
		// Alternative: Use Control Rig API if available
		// This requires the animation blueprint to have Control Rig nodes set up
		// UClass* AnimClass = AnimInst->GetClass();
		// if (AnimClass)
		// {
		//     // Access Control Rig through reflection or direct API
		//     // The exact API depends on UE5 version and Control Rig setup
		// }
	}
}

void UMetaHumanExpressionComponent::UpdateBlinkSystem(float DeltaTime)
{
	if (!SkeletalMeshComponent)
	{
		return;
	}

	BlinkTimer += DeltaTime;

	// Check if it's time to blink
	if (BlinkTimer >= BlinkInterval)
	{
		TriggerBlink();
		BlinkTimer = 0.0f;

		// Add some randomness to blink interval
		float RandomVariation = FMath::RandRange(-0.5f, 0.5f);
		BlinkTimer = -RandomVariation; // Negative to account for variation
	}
}

void UMetaHumanExpressionComponent::ApplyEmotionToControlRig(EEmotionType Emotion, float Intensity)
{
	if (!SkeletalMeshComponent)
	{
		return;
	}

	// Map emotions to blend shapes or Control Rig (via AnimInstance)
	// Try Control Rig first via anim blueprint parameters, fallback to blend shapes
	bool bControlRigApplied = false;
	
	if (UAnimInstance* AnimInst = SkeletalMeshComponent->GetAnimInstance())
	{
		// Try to set Control Rig values via anim blueprint parameters
		switch (Emotion)
		{
		case EEmotionType::Happy:
			bControlRigApplied = SetAnimBlueprintParameter(TEXT("Emotion_Happy"), Intensity);
			if (!bControlRigApplied)
			{
				SkeletalMeshComponent->SetMorphTarget(FName(TEXT("MouthSmile")), Intensity, false);
			}
			break;
		case EEmotionType::Sad:
			bControlRigApplied = SetAnimBlueprintParameter(TEXT("Emotion_Sad"), Intensity);
			if (!bControlRigApplied)
			{
				SkeletalMeshComponent->SetMorphTarget(FName(TEXT("MouthFrown")), Intensity, false);
			}
			break;
		case EEmotionType::Angry:
			bControlRigApplied = SetAnimBlueprintParameter(TEXT("Emotion_Angry"), Intensity);
			if (!bControlRigApplied)
			{
				SkeletalMeshComponent->SetMorphTarget(FName(TEXT("BrowFurrow")), Intensity, false);
			}
			break;
		case EEmotionType::Surprised:
			bControlRigApplied = SetAnimBlueprintParameter(TEXT("Emotion_Surprised"), Intensity);
			if (!bControlRigApplied)
			{
				SkeletalMeshComponent->SetMorphTarget(FName(TEXT("BrowRaise")), Intensity, false);
			}
			break;
		default:
			break;
		}
	}
	else
	{
		// No anim instance - use blend shapes directly
		switch (Emotion)
		{
		case EEmotionType::Happy:
			SkeletalMeshComponent->SetMorphTarget(FName(TEXT("MouthSmile")), Intensity, false);
			break;
		case EEmotionType::Sad:
			SkeletalMeshComponent->SetMorphTarget(FName(TEXT("MouthFrown")), Intensity, false);
			break;
		case EEmotionType::Angry:
			SkeletalMeshComponent->SetMorphTarget(FName(TEXT("BrowFurrow")), Intensity, false);
			break;
		case EEmotionType::Surprised:
			SkeletalMeshComponent->SetMorphTarget(FName(TEXT("BrowRaise")), Intensity, false);
			break;
		default:
			break;
		}
	}
}

bool UMetaHumanExpressionComponent::SetAnimBlueprintParameter(const FName& ParameterName, float Value)
{
	if (!SkeletalMeshComponent)
	{
		return false;
	}

	UAnimInstance* AnimInst = SkeletalMeshComponent->GetAnimInstance();
	if (!AnimInst)
	{
		return false;
	}

	// Try to set float parameter via reflection
	UClass* AnimClass = AnimInst->GetClass();
	if (AnimClass)
	{
		FProperty* Property = AnimClass->FindPropertyByName(ParameterName);
		if (Property && Property->IsA<FFloatProperty>())
		{
			FFloatProperty* FloatProp = CastField<FFloatProperty>(Property);
			if (FloatProp)
			{
				FloatProp->SetPropertyValue_InContainer(AnimInst, Value);
				return true;
			}
		}
	}

	return false;
}

