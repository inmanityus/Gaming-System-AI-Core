// Veil-Sight Component Implementation
// Dual World rendering system for The Body Broker

#include "VeilSightComponent.h"
#include "GameFramework/Actor.h"
#include "Components/PostProcessComponent.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Kismet/GameplayStatics.h"

UVeilSightComponent::UVeilSightComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	CurrentFocus = EVeilFocus::Both;
	DarkWorldOpacity = 0.5f;
	HumanWorldOpacity = 1.0f;
}

void UVeilSightComponent::SetFocus(EVeilFocus NewFocus)
{
	if (CurrentFocus == NewFocus)
	{
		return;
	}
	
	CurrentFocus = NewFocus;
	
	FString FocusName;
	switch (CurrentFocus)
	{
		case EVeilFocus::HumanWorld:
			FocusName = TEXT("Human World");
			HumanWorldOpacity = 1.0f;
			DarkWorldOpacity = 0.0f;
			break;
			
		case EVeilFocus::DarkWorld:
			FocusName = TEXT("Dark World");
			HumanWorldOpacity = 0.0f;
			DarkWorldOpacity = 1.0f;
			break;
			
		case EVeilFocus::Both:
			FocusName = TEXT("Both Worlds (Veil-Sight)");
			HumanWorldOpacity = 0.7f;
			DarkWorldOpacity = 0.7f;
			break;
	}
	
	UE_LOG(LogTemp, Warning, TEXT("[VeilSight] Focus changed to: %s"), *FocusName);
	
	UpdatePostProcessEffects();
}

bool UVeilSightComponent::CanSeeCreature(AActor* Creature)
{
	if (!Creature)
	{
		return false;
	}
	
	// Check creature's world affiliation via tags
	bool bIsDarkWorldCreature = Creature->ActorHasTag(TEXT("DarkWorld"));
	bool bIsHumanWorldCreature = Creature->ActorHasTag(TEXT("HumanWorld"));
	
	bool bCanSee = false;
	
	switch (CurrentFocus)
	{
		case EVeilFocus::HumanWorld:
			bCanSee = bIsHumanWorldCreature;
			break;
			
		case EVeilFocus::DarkWorld:
			bCanSee = bIsDarkWorldCreature;
			break;
			
		case EVeilFocus::Both:
			bCanSee = true; // Can see everything with Veil-Sight
			break;
	}
	
	if (bCanSee && bIsDarkWorldCreature)
	{
		UE_LOG(LogTemp, Log, TEXT("[VeilSight] Dark World creature visible: %s"), *Creature->GetName());
	}
	
	return bCanSee;
}

void UVeilSightComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	
	// Smooth opacity transitions for visual comfort
	// In a full implementation, this would lerp post-process parameters
	// and handle dynamic creature visibility updates
	
	// Example: Query nearby creatures and update visibility
	if (UWorld* World = GetWorld())
	{
		// Periodic updates to creature visibility based on current focus
		// This prevents sudden pop-in/pop-out effects
	}
}

void UVeilSightComponent::UpdatePostProcessEffects()
{
	// Update post-process effects for world visibility
	// In a full implementation, this would:
	// 1. Access Material Parameter Collection for world opacity
	// 2. Update shader parameters for Dark World overlay
	// 3. Adjust fog, lighting, and particle effects
	// 4. Trigger Blueprint events for visual transitions
	
	UE_LOG(LogTemp, Log, TEXT("[VeilSight] Post-process updated - Human: %.2f, Dark: %.2f"),
		HumanWorldOpacity, DarkWorldOpacity);
	
	// Example: Find and update Material Parameter Collection
	if (UWorld* World = GetWorld())
	{
		// Material parameters would be updated here for shader-based world blending
		// This enables the dual-world visual effect
	}
}

