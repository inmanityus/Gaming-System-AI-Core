// Death System Component Tests
// Comprehensive test suite for Death of Flesh mechanic

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "../DeathSystemComponent.h"
#include "GameFramework/Actor.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDeathSystemComponentBasicTest, "BodyBroker.DeathSystem.BasicFunctionality", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FDeathSystemComponentBasicTest::RunTest(const FString& Parameters)
{
	// Test component creation
	UDeathSystemComponent* Component = NewObject<UDeathSystemComponent>();
	TestNotNull(TEXT("Component should be created"), Component);
	
	// Test initial state
	TestEqual(TEXT("Initial Veil Fray should be 0"), Component->VeilFrayLevel, 0);
	TestTrue(TEXT("Initial Corpse ID should be empty"), Component->CurrentCorpseID.IsEmpty());
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDeathSystemTriggerDeathTest, "BodyBroker.DeathSystem.TriggerDeath", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FDeathSystemTriggerDeathTest::RunTest(const FString& Parameters)
{
	UDeathSystemComponent* Component = NewObject<UDeathSystemComponent>();
	
	// Test death trigger
	FVector DeathLocation(100.0f, 200.0f, 50.0f);
	FString World = TEXT("DarkWorld");
	TArray<FString> GearItems = {TEXT("Sword"), TEXT("Shield"), TEXT("Potion")};
	
	Component->TriggerDeath(DeathLocation, World, GearItems);
	
	// Verify state changes
	TestEqual(TEXT("Veil Fray should increase to 1"), Component->VeilFrayLevel, 1);
	TestEqual(TEXT("Corpse location should be set"), Component->CorpseLocation, DeathLocation);
	TestFalse(TEXT("Corpse ID should be generated"), Component->CurrentCorpseID.IsEmpty());
	
	// Test second death
	Component->TriggerDeath(FVector(0, 0, 0), TEXT("HumanWorld"), TArray<FString>());
	TestEqual(TEXT("Veil Fray should increase to 2"), Component->VeilFrayLevel, 2);
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDeathSystemCorpseRunTest, "BodyBroker.DeathSystem.CorpseRun", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FDeathSystemCorpseRunTest::RunTest(const FString& Parameters)
{
	UDeathSystemComponent* Component = NewObject<UDeathSystemComponent>();
	
	// Test corpse run without death (should fail gracefully)
	Component->StartCorpseRun();
	TestTrue(TEXT("Should not crash when no corpse exists"), true);
	
	// Trigger death first
	Component->TriggerDeath(FVector(100, 100, 0), TEXT("HumanWorld"), TArray<FString>());
	FString CorpseID = Component->CurrentCorpseID;
	
	// Now start corpse run
	Component->StartCorpseRun();
	TestFalse(TEXT("Corpse ID should still exist after run starts"), Component->CurrentCorpseID.IsEmpty());
	TestEqual(TEXT("Corpse ID should match"), Component->CurrentCorpseID, CorpseID);
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDeathSystemBriberyTest, "BodyBroker.DeathSystem.BribeCorpseTender", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FDeathSystemBriberyTest::RunTest(const FString& Parameters)
{
	UDeathSystemComponent* Component = NewObject<UDeathSystemComponent>();
	
	// Set Veil Fray level
	Component->TriggerDeath(FVector(0, 0, 0), TEXT("DarkWorld"), TArray<FString>());
	Component->TriggerDeath(FVector(0, 0, 0), TEXT("DarkWorld"), TArray<FString>());
	Component->TriggerDeath(FVector(0, 0, 0), TEXT("DarkWorld"), TArray<FString>());
	TestEqual(TEXT("Veil Fray should be 3"), Component->VeilFrayLevel, 3);
	
	// Bribe with regular item (no effect)
	Component->BribeCorpseTender(TEXT("Common Item"));
	TestEqual(TEXT("Veil Fray should remain 3"), Component->VeilFrayLevel, 3);
	
	// Bribe with drug (should reduce)
	Component->BribeCorpseTender(TEXT("Rare Drug"));
	TestEqual(TEXT("Veil Fray should reduce to 2"), Component->VeilFrayLevel, 2);
	
	// Bribe with rare item (should reduce)
	Component->BribeCorpseTender(TEXT("Rare Artifact"));
	TestEqual(TEXT("Veil Fray should reduce to 1"), Component->VeilFrayLevel, 1);
	
	// Test bribery at zero (should not go negative)
	Component->BribeCorpseTender(TEXT("Rare Drug"));
	Component->BribeCorpseTender(TEXT("Rare Drug"));
	TestTrue(TEXT("Veil Fray should not go negative"), Component->VeilFrayLevel >= 0);
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDeathSystemEdgeCasesTest, "BodyBroker.DeathSystem.EdgeCases", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FDeathSystemEdgeCasesTest::RunTest(const FString& Parameters)
{
	UDeathSystemComponent* Component = NewObject<UDeathSystemComponent>();
	
	// Test death with empty gear items
	Component->TriggerDeath(FVector(0, 0, 0), TEXT("HumanWorld"), TArray<FString>());
	TestTrue(TEXT("Should handle empty gear items"), true);
	
	// Test death with large gear array
	TArray<FString> LargeGear;
	for (int32 i = 0; i < 100; i++)
	{
		LargeGear.Add(FString::Printf(TEXT("Item%d"), i));
	}
	Component->TriggerDeath(FVector(0, 0, 0), TEXT("DarkWorld"), LargeGear);
	TestTrue(TEXT("Should handle large gear arrays"), true);
	
	// Test bribery with empty string
	Component->BribeCorpseTender(TEXT(""));
	TestTrue(TEXT("Should handle empty bribe item"), true);
	
	return true;
}

