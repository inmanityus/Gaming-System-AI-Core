// Veil-Sight Component Tests
// Comprehensive test suite for dual world vision system

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "../VeilSightComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVeilSightBasicTest, "BodyBroker.VeilSight.BasicFunctionality", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FVeilSightBasicTest::RunTest(const FString& Parameters)
{
	UVeilSightComponent* Component = NewObject<UVeilSightComponent>();
	
	TestNotNull(TEXT("Component should be created"), Component);
	TestEqual(TEXT("Initial focus should be Both"), Component->GetCurrentFocus(), EVeilFocus::Both);
	TestEqual(TEXT("Dark World opacity should be 0.5"), Component->DarkWorldOpacity, 0.5f);
	TestEqual(TEXT("Human World opacity should be 1.0"), Component->HumanWorldOpacity, 1.0f);
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVeilSightFocusSwitchingTest, "BodyBroker.VeilSight.FocusSwitching", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FVeilSightFocusSwitchingTest::RunTest(const FString& Parameters)
{
	UVeilSightComponent* Component = NewObject<UVeilSightComponent>();
	
	// Test switching to Human World
	Component->SetFocus(EVeilFocus::HumanWorld);
	TestEqual(TEXT("Focus should be Human World"), Component->GetCurrentFocus(), EVeilFocus::HumanWorld);
	TestEqual(TEXT("Human World opacity should be 1.0"), Component->HumanWorldOpacity, 1.0f);
	TestEqual(TEXT("Dark World opacity should be 0.0"), Component->DarkWorldOpacity, 0.0f);
	
	// Test switching to Dark World
	Component->SetFocus(EVeilFocus::DarkWorld);
	TestEqual(TEXT("Focus should be Dark World"), Component->GetCurrentFocus(), EVeilFocus::DarkWorld);
	TestEqual(TEXT("Human World opacity should be 0.0"), Component->HumanWorldOpacity, 0.0f);
	TestEqual(TEXT("Dark World opacity should be 1.0"), Component->DarkWorldOpacity, 1.0f);
	
	// Test switching to Both
	Component->SetFocus(EVeilFocus::Both);
	TestEqual(TEXT("Focus should be Both"), Component->GetCurrentFocus(), EVeilFocus::Both);
	TestEqual(TEXT("Human World opacity should be 0.7"), Component->HumanWorldOpacity, 0.7f);
	TestEqual(TEXT("Dark World opacity should be 0.7"), Component->DarkWorldOpacity, 0.7f);
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVeilSightCreatureVisibilityTest, "BodyBroker.VeilSight.CreatureVisibility", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FVeilSightCreatureVisibilityTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	UVeilSightComponent* Component = NewObject<UVeilSightComponent>();
	
	// Create test actors
	AActor* HumanCreature = World->SpawnActor<AActor>();
	HumanCreature->Tags.Add(TEXT("HumanWorld"));
	
	AActor* DarkCreature = World->SpawnActor<AActor>();
	DarkCreature->Tags.Add(TEXT("DarkWorld"));
	
	AActor* UntaggedCreature = World->SpawnActor<AActor>();
	
	// Test Human World focus
	Component->SetFocus(EVeilFocus::HumanWorld);
	TestTrue(TEXT("Human creature should be visible in Human World"), Component->CanSeeCreature(HumanCreature));
	TestFalse(TEXT("Dark creature should NOT be visible in Human World"), Component->CanSeeCreature(DarkCreature));
	TestFalse(TEXT("Untagged creature should NOT be visible in Human World"), Component->CanSeeCreature(UntaggedCreature));
	
	// Test Dark World focus
	Component->SetFocus(EVeilFocus::DarkWorld);
	TestFalse(TEXT("Human creature should NOT be visible in Dark World"), Component->CanSeeCreature(HumanCreature));
	TestTrue(TEXT("Dark creature should be visible in Dark World"), Component->CanSeeCreature(DarkCreature));
	TestFalse(TEXT("Untagged creature should NOT be visible in Dark World"), Component->CanSeeCreature(UntaggedCreature));
	
	// Test Both mode (Veil-Sight)
	Component->SetFocus(EVeilFocus::Both);
	TestTrue(TEXT("Human creature should be visible in Both mode"), Component->CanSeeCreature(HumanCreature));
	TestTrue(TEXT("Dark creature should be visible in Both mode"), Component->CanSeeCreature(DarkCreature));
	TestTrue(TEXT("Untagged creature should be visible in Both mode"), Component->CanSeeCreature(UntaggedCreature));
	
	World->DestroyActor(HumanCreature);
	World->DestroyActor(DarkCreature);
	World->DestroyActor(UntaggedCreature);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVeilSightNullCreatureTest, "BodyBroker.VeilSight.NullCreature", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FVeilSightNullCreatureTest::RunTest(const FString& Parameters)
{
	UVeilSightComponent* Component = NewObject<UVeilSightComponent>();
	
	// Test with null actor
	bool bCanSee = Component->CanSeeCreature(nullptr);
	TestFalse(TEXT("Null creature should return false"), bCanSee);
	TestTrue(TEXT("Should not crash on null creature"), true);
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVeilSightMultipleTagsTest, "BodyBroker.VeilSight.MultipleTags", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FVeilSightMultipleTagsTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	UVeilSightComponent* Component = NewObject<UVeilSightComponent>();
	
	// Create creature with both tags (edge case)
	AActor* DualCreature = World->SpawnActor<AActor>();
	DualCreature->Tags.Add(TEXT("HumanWorld"));
	DualCreature->Tags.Add(TEXT("DarkWorld"));
	
	// Test in Human World focus
	Component->SetFocus(EVeilFocus::HumanWorld);
	TestTrue(TEXT("Dual-tagged creature should be visible in Human World"), Component->CanSeeCreature(DualCreature));
	
	// Test in Dark World focus
	Component->SetFocus(EVeilFocus::DarkWorld);
	TestTrue(TEXT("Dual-tagged creature should be visible in Dark World"), Component->CanSeeCreature(DualCreature));
	
	// Test in Both mode
	Component->SetFocus(EVeilFocus::Both);
	TestTrue(TEXT("Dual-tagged creature should be visible in Both mode"), Component->CanSeeCreature(DualCreature));
	
	World->DestroyActor(DualCreature);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVeilSightFocusIdempotencyTest, "BodyBroker.VeilSight.FocusIdempotency", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FVeilSightFocusIdempotencyTest::RunTest(const FString& Parameters)
{
	UVeilSightComponent* Component = NewObject<UVeilSightComponent>();
	
	// Set focus to same value multiple times
	Component->SetFocus(EVeilFocus::DarkWorld);
	float Opacity1 = Component->DarkWorldOpacity;
	
	Component->SetFocus(EVeilFocus::DarkWorld);
	float Opacity2 = Component->DarkWorldOpacity;
	
	Component->SetFocus(EVeilFocus::DarkWorld);
	float Opacity3 = Component->DarkWorldOpacity;
	
	TestEqual(TEXT("Opacity should remain stable"), Opacity1, Opacity2);
	TestEqual(TEXT("Opacity should remain stable"), Opacity2, Opacity3);
	TestTrue(TEXT("Should handle redundant focus changes"), true);
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVeilSightRapidSwitchingTest, "BodyBroker.VeilSight.RapidSwitching", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FVeilSightRapidSwitchingTest::RunTest(const FString& Parameters)
{
	UVeilSightComponent* Component = NewObject<UVeilSightComponent>();
	
	// Rapidly switch between all three modes
	for (int32 i = 0; i < 100; i++)
	{
		Component->SetFocus(EVeilFocus::HumanWorld);
		Component->SetFocus(EVeilFocus::DarkWorld);
		Component->SetFocus(EVeilFocus::Both);
	}
	
	TestTrue(TEXT("Should handle rapid focus switching"), true);
	TestEqual(TEXT("Final focus should be Both"), Component->GetCurrentFocus(), EVeilFocus::Both);
	
	return true;
}

