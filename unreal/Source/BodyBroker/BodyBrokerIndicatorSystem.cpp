// Copyright Epic Games, Inc. All Rights Reserved.

#include "BodyBrokerIndicatorSystem.h"
#include "Components/WidgetComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"

UBodyBrokerIndicatorSystem::UBodyBrokerIndicatorSystem(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, NextIndicatorID(1)
	, EdgeGlowIntensity(0.3f)
	, EdgeGlowColor(1.0f, 0.8f, 0.2f, 1.0f)  // Subtle yellow-orange
	, ScreenEdgeIndicatorSize(20.0f)
	, MaxIndicatorDistance(5000.0f)
	, bEnableEdgeGlow(true)
	, bEnableScreenEdge(true)
	, bEnableMinionNPC(false)
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UBodyBrokerIndicatorSystem::BeginPlay()
{
	Super::BeginPlay();

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerIndicatorSystem: Initialized"));
}

void UBodyBrokerIndicatorSystem::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Update all indicator types
	if (bEnableEdgeGlow)
	{
		UpdateEdgeGlowIndicators(DeltaTime);
	}

	if (bEnableScreenEdge)
	{
		UpdateScreenEdgeIndicators(DeltaTime);
	}

	if (bEnableMinionNPC)
	{
		UpdateMinionNPCIndicator(DeltaTime);
	}

	// Update timers and remove expired indicators
	TArray<int32> IndicatorsToRemove;
	for (auto& Pair : IndicatorTimers)
	{
		int32 IndicatorID = Pair.Key;
		float& Timer = Pair.Value;

		if (Timer > 0.0f)
		{
			Timer -= DeltaTime;
			if (Timer <= 0.0f)
			{
				IndicatorsToRemove.Add(IndicatorID);
			}
		}
	}

	for (int32 IndicatorID : IndicatorsToRemove)
	{
		RemoveIndicator(IndicatorID);
	}
}

void UBodyBrokerIndicatorSystem::AddIndicator(const FIndicatorData& IndicatorData, int32& OutIndicatorID)
{
	OutIndicatorID = NextIndicatorID++;
	ActiveIndicators.Add(OutIndicatorID, IndicatorData);

	// Set timer if duration specified
	if (IndicatorData.Duration > 0.0f)
	{
		IndicatorTimers.Add(OutIndicatorID, IndicatorData.Duration);
	}

	// Create visual representation based on type
	switch (IndicatorData.IndicatorType)
	{
		case EIndicatorType::EdgeGlow:
			if (bEnableEdgeGlow)
			{
				CreateEdgeGlowEffect(OutIndicatorID, IndicatorData);
			}
			break;

		case EIndicatorType::ScreenEdge:
			if (bEnableScreenEdge)
			{
				CreateScreenEdgeIndicator(OutIndicatorID, IndicatorData);
			}
			break;

		case EIndicatorType::MinionNPC:
			if (bEnableMinionNPC)
			{
				// TODO: Spawn or update minion NPC
				UE_LOG(LogTemp, Log, TEXT("BodyBrokerIndicatorSystem: Minion NPC indicator added (ID: %d)"), OutIndicatorID);
			}
			break;

		case EIndicatorType::Contextual:
			// Contextual indicators adapt based on situation
			if (IsLocationOnScreen(IndicatorData.TargetLocation))
			{
				// On screen - use subtle edge glow
				if (bEnableEdgeGlow)
				{
					CreateEdgeGlowEffect(OutIndicatorID, IndicatorData);
				}
			}
			else
			{
				// Off screen - use screen edge indicator
				if (bEnableScreenEdge)
				{
					CreateScreenEdgeIndicator(OutIndicatorID, IndicatorData);
				}
			}
			break;
	}

	UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerIndicatorSystem: Added indicator (ID: %d, Type: %d)"), 
		OutIndicatorID, (int32)IndicatorData.IndicatorType);
}

void UBodyBrokerIndicatorSystem::RemoveIndicator(int32 IndicatorID)
{
	if (!ActiveIndicators.Contains(IndicatorID))
	{
		return;
	}

	FIndicatorData IndicatorData = ActiveIndicators[IndicatorID];

	// Remove visual representation based on type
	switch (IndicatorData.IndicatorType)
	{
		case EIndicatorType::EdgeGlow:
			RemoveEdgeGlowEffect(IndicatorID);
			break;

		case EIndicatorType::ScreenEdge:
			RemoveScreenEdgeIndicator(IndicatorID);
			break;

		case EIndicatorType::MinionNPC:
			// TODO: Remove minion NPC
			break;

		case EIndicatorType::Contextual:
			RemoveEdgeGlowEffect(IndicatorID);
			RemoveScreenEdgeIndicator(IndicatorID);
			break;
	}

	ActiveIndicators.Remove(IndicatorID);
	IndicatorTimers.Remove(IndicatorID);

	UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerIndicatorSystem: Removed indicator (ID: %d)"), IndicatorID);
}

void UBodyBrokerIndicatorSystem::UpdateIndicatorLocation(int32 IndicatorID, const FVector& NewLocation)
{
	if (ActiveIndicators.Contains(IndicatorID))
	{
		ActiveIndicators[IndicatorID].TargetLocation = NewLocation;
	}
}

void UBodyBrokerIndicatorSystem::ClearAllIndicators()
{
	TArray<int32> IndicatorIDs;
	ActiveIndicators.GetKeys(IndicatorIDs);

	for (int32 IndicatorID : IndicatorIDs)
	{
		RemoveIndicator(IndicatorID);
	}

	UE_LOG(LogTemp, Log, TEXT("BodyBrokerIndicatorSystem: Cleared all indicators"));
}

void UBodyBrokerIndicatorSystem::UpdateEdgeGlowIndicators(float DeltaTime)
{
	// Update edge glow material parameters based on active indicators
	// This creates subtle edge glows pointing toward off-screen targets
	
	if (!EdgeGlowMaterial)
	{
		// Create material instance if needed
		// TODO: Load edge glow material and create dynamic instance
		return;
	}

	// Calculate edge glow direction and intensity for each indicator
	for (auto& Pair : ActiveIndicators)
	{
		int32 IndicatorID = Pair.Key;
		FIndicatorData& IndicatorData = Pair.Value;

		if (IndicatorData.IndicatorType == EIndicatorType::EdgeGlow || 
			IndicatorData.IndicatorType == EIndicatorType::Contextual)
		{
			// Calculate direction from camera to target
			FVector CameraLocation;
			FRotator CameraRotation;
			if (UWorld* World = GetWorld())
			{
				if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
				{
					PC->GetPlayerViewPoint(CameraLocation, CameraRotation);
				}
			}

			FVector Direction = (IndicatorData.TargetLocation - CameraLocation).GetSafeNormal();
			
			// Update material parameters for edge glow
			// Edge glow intensity based on distance and priority
			float Distance = FVector::Dist(CameraLocation, IndicatorData.TargetLocation);
			float NormalizedDistance = FMath::Clamp(Distance / MaxIndicatorDistance, 0.0f, 1.0f);
			float Intensity = EdgeGlowIntensity * (1.0f - NormalizedDistance) * IndicatorData.Priority;

			// Set material parameters (if material supports it)
			// EdgeGlowMaterial->SetVectorParameterValue(TEXT("GlowDirection"), FLinearColor(Direction.X, Direction.Y, Direction.Z, 0.0f));
			// EdgeGlowMaterial->SetScalarParameterValue(TEXT("GlowIntensity"), Intensity);
		}
	}
}

void UBodyBrokerIndicatorSystem::UpdateScreenEdgeIndicators(float DeltaTime)
{
	// Update screen edge indicator positions
	// These appear at screen edges when targets are off-screen

	if (!GetWorld())
	{
		return;
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC)
	{
		return;
	}

	// Update each screen edge indicator
	for (auto& Pair : ActiveIndicators)
	{
		int32 IndicatorID = Pair.Key;
		FIndicatorData& IndicatorData = Pair.Value;

		if (IndicatorData.IndicatorType == EIndicatorType::ScreenEdge ||
			(IndicatorData.IndicatorType == EIndicatorType::Contextual && !IsLocationOnScreen(IndicatorData.TargetLocation)))
		{
			// Calculate screen position
			FVector2D ScreenPosition = WorldToScreenPosition(IndicatorData.TargetLocation);

			// Clamp to screen edges if off-screen
			FVector2D ViewportSize;
			if (GEngine && GEngine->GameViewport)
			{
				GEngine->GameViewport->GetViewportSize(ViewportSize);
			}
			else
			{
				int32 ViewportSizeX = 0;
				int32 ViewportSizeY = 0;
				PC->GetViewportSize(ViewportSizeX, ViewportSizeY);
				ViewportSize.X = ViewportSizeX;
				ViewportSize.Y = ViewportSizeY;
			}

			// Calculate edge position
			FVector2D EdgePosition;
			if (ScreenPosition.X < 0 || ScreenPosition.X > ViewportSize.X ||
				ScreenPosition.Y < 0 || ScreenPosition.Y > ViewportSize.Y)
			{
				// Target is off-screen, calculate edge position
				FVector CameraLocation;
				FRotator CameraRotation;
				PC->GetPlayerViewPoint(CameraLocation, CameraRotation);

				FVector Direction = (IndicatorData.TargetLocation - CameraLocation).GetSafeNormal();
				FVector RightVector = FRotationMatrix(CameraRotation).GetUnitAxis(EAxis::Y);
				FVector UpVector = FRotationMatrix(CameraRotation).GetUnitAxis(EAxis::Z);

				// Project direction onto screen plane
				float RightDot = FVector::DotProduct(Direction, RightVector);
				float UpDot = FVector::DotProduct(Direction, UpVector);

				// Calculate edge position
				EdgePosition.X = FMath::Clamp((RightDot + 1.0f) * 0.5f * ViewportSize.X, 0.0f, ViewportSize.X);
				EdgePosition.Y = FMath::Clamp((UpDot + 1.0f) * 0.5f * ViewportSize.Y, 0.0f, ViewportSize.Y);

				// Clamp to edges
				if (EdgePosition.X < ScreenEdgeIndicatorSize)
				{
					EdgePosition.X = ScreenEdgeIndicatorSize;
				}
				else if (EdgePosition.X > ViewportSize.X - ScreenEdgeIndicatorSize)
				{
					EdgePosition.X = ViewportSize.X - ScreenEdgeIndicatorSize;
				}

				if (EdgePosition.Y < ScreenEdgeIndicatorSize)
				{
					EdgePosition.Y = ScreenEdgeIndicatorSize;
				}
				else if (EdgePosition.Y > ViewportSize.Y - ScreenEdgeIndicatorSize)
				{
					EdgePosition.Y = ViewportSize.Y - ScreenEdgeIndicatorSize;
				}

				// Update widget position (if widget exists)
				// TODO: Update widget component position
			}
		}
	}
}

void UBodyBrokerIndicatorSystem::UpdateMinionNPCIndicator(float DeltaTime)
{
	// Update minion NPC position and behavior
	// Minion NPC provides contextual guidance without breaking immersion

	if (!bEnableMinionNPC || !MinionNPC)
	{
		return;
	}

	// Find highest priority indicator for minion NPC to follow
	int32 HighestPriority = 0;
	FVector TargetLocation = FVector::ZeroVector;

	for (auto& Pair : ActiveIndicators)
	{
		const FIndicatorData& IndicatorData = Pair.Value;
		if (IndicatorData.Priority > HighestPriority)
		{
			HighestPriority = IndicatorData.Priority;
			TargetLocation = IndicatorData.TargetLocation;
		}
	}

	if (HighestPriority > 0)
	{
		// Move minion NPC toward target (subtle, not aggressive)
		FVector CurrentLocation = MinionNPC->GetActorLocation();
		FVector Direction = (TargetLocation - CurrentLocation).GetSafeNormal();
		FVector NewLocation = CurrentLocation + Direction * 100.0f * DeltaTime;  // Slow movement

		MinionNPC->SetActorLocation(NewLocation);
	}
}

FVector2D UBodyBrokerIndicatorSystem::WorldToScreenPosition(const FVector& WorldLocation) const
{
	FVector2D ScreenPosition;

	if (UWorld* World = GetWorld())
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
		{
			PC->ProjectWorldLocationToScreen(WorldLocation, ScreenPosition);
		}
	}

	return ScreenPosition;
}

bool UBodyBrokerIndicatorSystem::IsLocationOnScreen(const FVector& WorldLocation) const
{
	FVector2D ScreenPosition = WorldToScreenPosition(WorldLocation);

	FVector2D ViewportSize;
	if (UWorld* World = GetWorld())
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
		{
			int32 ViewportSizeX = 0;
			int32 ViewportSizeY = 0;
			PC->GetViewportSize(ViewportSizeX, ViewportSizeY);
			ViewportSize.X = ViewportSizeX;
			ViewportSize.Y = ViewportSizeY;
		}
	}

	return ScreenPosition.X >= 0 && ScreenPosition.X <= ViewportSize.X &&
		   ScreenPosition.Y >= 0 && ScreenPosition.Y <= ViewportSize.Y;
}

void UBodyBrokerIndicatorSystem::CreateEdgeGlowEffect(int32 IndicatorID, const FIndicatorData& IndicatorData)
{
	// Create subtle edge glow effect
	// Uses post-process material or screen-space effect
	// NO massive arrows - subtle edge highlighting only

	UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerIndicatorSystem: Created edge glow effect (ID: %d)"), IndicatorID);
}

void UBodyBrokerIndicatorSystem::CreateScreenEdgeIndicator(int32 IndicatorID, const FIndicatorData& IndicatorData)
{
	// Create screen edge indicator widget
	// Small, subtle indicator at screen edge pointing toward off-screen target

	UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerIndicatorSystem: Created screen edge indicator (ID: %d)"), IndicatorID);
}

void UBodyBrokerIndicatorSystem::RemoveEdgeGlowEffect(int32 IndicatorID)
{
	UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerIndicatorSystem: Removed edge glow effect (ID: %d)"), IndicatorID);
}

void UBodyBrokerIndicatorSystem::RemoveScreenEdgeIndicator(int32 IndicatorID)
{
	UE_LOG(LogTemp, VeryVerbose, TEXT("BodyBrokerIndicatorSystem: Removed screen edge indicator (ID: %d)"), IndicatorID);
}

void UBodyBrokerIndicatorSystem::UpdateIndicatorFade(int32 IndicatorID, float DeltaTime, bool bFadingOut)
{
	// Update fade in/out for smooth transitions
	if (ActiveIndicators.Contains(IndicatorID))
	{
		FIndicatorData& IndicatorData = ActiveIndicators[IndicatorID];
		// TODO: Implement fade logic
	}
}

