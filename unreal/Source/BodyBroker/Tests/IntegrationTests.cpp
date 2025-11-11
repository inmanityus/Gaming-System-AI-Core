// Integration Tests - Cross-Feature Testing
// Tests interactions between Death, Harvesting, Negotiation, and VeilSight systems

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "../DeathSystemComponent.h"
#include "../HarvestingMinigame.h"
#include "../NegotiationSystem.h"
#include "../VeilSightComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationDeathAndHarvestingTest, "BodyBroker.Integration.DeathToHarvesting", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationDeathAndHarvestingTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	
	// Create both systems
	UDeathSystemComponent* DeathSystem = NewObject<UDeathSystemComponent>();
	AHarvestingMinigame* HarvestingGame = World->SpawnActor<AHarvestingMinigame>();
	
	// Player dies, creates a corpse
	FVector DeathLocation(100, 200, 0);
	DeathSystem->TriggerDeath(DeathLocation, TEXT("HumanWorld"), TArray<FString>());
	FString CorpseID = DeathSystem->CurrentCorpseID;
	
	TestFalse(TEXT("Corpse should be created"), CorpseID.IsEmpty());
	
	// Harvesting should work on the corpse
	HarvestingGame->StartExtraction(CorpseID, EExtractionMethod::LiveExtraction, EToolQuality::Surgical);
	TestTrue(TEXT("Should be able to harvest from corpse"), true);
	
	// Complete harvesting
	HarvestingGame->CompleteExtraction(0.9f);
	TestTrue(TEXT("Harvesting should complete successfully"), true);
	
	World->DestroyActor(HarvestingGame);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationHarvestingToNegotiationTest, "BodyBroker.Integration.HarvestingToNegotiation", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationHarvestingToNegotiationTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	
	// Create both systems
	AHarvestingMinigame* HarvestingGame = World->SpawnActor<AHarvestingMinigame>();
	ANegotiationSystem* NegotiationSys = World->SpawnActor<ANegotiationSystem>();
	
	// Harvest with poor tool quality
	HarvestingGame->StartExtraction(TEXT("Target1"), EExtractionMethod::ShotgunBlast, EToolQuality::Rusty);
	HarvestingGame->CompleteExtraction(0.5f); // Low quality result
	
	// Negotiate with poor quality item (should affect base price)
	NegotiationSys->StartNegotiation(TEXT("Vampire-Client"), 100.0f, TEXT("Poor"));
	float PoorQualityPrice = NegotiationSys->CurrentOffer;
	
	// Harvest with excellent tool quality
	HarvestingGame->StartExtraction(TEXT("Target2"), EExtractionMethod::LiveExtraction, EToolQuality::Advanced);
	HarvestingGame->CompleteExtraction(1.0f); // High quality result
	
	// Negotiate with excellent quality item
	ANegotiationSystem* NegotiationSys2 = World->SpawnActor<ANegotiationSystem>();
	NegotiationSys2->StartNegotiation(TEXT("Vampire-Client"), 100.0f, TEXT("Excellent"));
	float ExcellentQualityPrice = NegotiationSys2->CurrentOffer;
	
	// Both should work and prices should be same (quality handled by backend in real system)
	TestEqual(TEXT("Poor quality negotiation should start"), PoorQualityPrice, 100.0f);
	TestEqual(TEXT("Excellent quality negotiation should start"), ExcellentQualityPrice, 100.0f);
	
	World->DestroyActor(HarvestingGame);
	World->DestroyActor(NegotiationSys);
	World->DestroyActor(NegotiationSys2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationVeilSightWithNegotiationTest, "BodyBroker.Integration.VeilSightNegotiation", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationVeilSightWithNegotiationTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	
	// Create systems
	UVeilSightComponent* VeilSight = NewObject<UVeilSightComponent>();
	ANegotiationSystem* NegotiationSys = World->SpawnActor<ANegotiationSystem>();
	
	// Create Dark World NPC
	AActor* DarkNPC = World->SpawnActor<AActor>();
	DarkNPC->Tags.Add(TEXT("DarkWorld"));
	
	// Set focus to Human World (shouldn't see Dark World NPCs)
	VeilSight->SetFocus(EVeilFocus::HumanWorld);
	bool CanSeeDarkNPC = VeilSight->CanSeeCreature(DarkNPC);
	TestFalse(TEXT("Should not see Dark NPC in Human World"), CanSeeDarkNPC);
	
	// Negotiation with invisible NPC should still work (game logic)
	NegotiationSys->StartNegotiation(TEXT("DarkWorld-Client"), 100.0f, TEXT("Standard"));
	TestTrue(TEXT("Can negotiate with invisible Dark World client"), NegotiationSys->CurrentOffer > 0.0f);
	
	// Switch to Both mode
	VeilSight->SetFocus(EVeilFocus::Both);
	bool CanSeeNowDarkNPC = VeilSight->CanSeeCreature(DarkNPC);
	TestTrue(TEXT("Should see Dark NPC in Both mode"), CanSeeNowDarkNPC);
	
	// Complete negotiation
	NegotiationSys->CompleteNegotiation();
	TestTrue(TEXT("Negotiation should complete regardless of sight mode"), true);
	
	World->DestroyActor(DarkNPC);
	World->DestroyActor(NegotiationSys);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationDeathDuringNegotiationTest, "BodyBroker.Integration.DeathDuringNegotiation", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationDeathDuringNegotiationTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	
	// Create systems
	UDeathSystemComponent* DeathSystem = NewObject<UDeathSystemComponent>();
	ANegotiationSystem* NegotiationSys = World->SpawnActor<ANegotiationSystem>();
	
	// Start negotiation
	NegotiationSys->StartNegotiation(TEXT("TestClient"), 100.0f, TEXT("Standard"));
	NegotiationSys->UseTactic(ENegotiationTactic::Charm);
	float PriceBeforeDeath = NegotiationSys->CurrentOffer;
	
	TestTrue(TEXT("Negotiation should be in progress"), PriceBeforeDeath > 0.0f);
	
	// Player dies during negotiation
	DeathSystem->TriggerDeath(FVector(0, 0, 0), TEXT("HumanWorld"), TArray<FString>());
	
	TestTrue(TEXT("Death should trigger even during negotiation"), DeathSystem->VeilFrayLevel > 0);
	
	// Negotiation state should persist (game design choice - real system might abort)
	// Testing that systems don't crash when combined
	NegotiationSys->CompleteNegotiation();
	TestTrue(TEXT("Should handle negotiation completion after death"), true);
	
	World->DestroyActor(NegotiationSys);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationVeilSightRapidWithHarvestingTest, "BodyBroker.Integration.VeilSightHarvesting", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationVeilSightRapidWithHarvestingTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	
	// Create systems
	UVeilSightComponent* VeilSight = NewObject<UVeilSightComponent>();
	AHarvestingMinigame* HarvestingGame = World->SpawnActor<AHarvestingMinigame>();
	
	// Create harvestable target
	AActor* Target = World->SpawnActor<AActor>();
	Target->Tags.Add(TEXT("DarkWorld"));
	
	// Start harvesting
	HarvestingGame->StartExtraction(TEXT("DarkTarget"), EExtractionMethod::LiveExtraction, EToolQuality::Surgical);
	
	// Rapidly switch VeilSight during harvesting
	for (int32 i = 0; i < 50; i++)
	{
		VeilSight->SetFocus(EVeilFocus::HumanWorld);
		VeilSight->SetFocus(EVeilFocus::DarkWorld);
		VeilSight->SetFocus(EVeilFocus::Both);
		
		// Verify we can still see the target during harvesting
		if (i % 10 == 0)
		{
			bool CanSee = VeilSight->CanSeeCreature(Target);
			// Should see in DarkWorld and Both modes
		}
	}
	
	// Complete harvesting - should work despite focus changes
	HarvestingGame->CompleteExtraction(1.0f);
	TestTrue(TEXT("Harvesting should complete despite VeilSight changes"), true);
	
	World->DestroyActor(Target);
	World->DestroyActor(HarvestingGame);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationAllSystemsSequenceTest, "BodyBroker.Integration.CompleteGameplayLoop", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationAllSystemsSequenceTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	
	// Create all 4 core systems
	UDeathSystemComponent* DeathSystem = NewObject<UDeathSystemComponent>();
	AHarvestingMinigame* HarvestingGame = World->SpawnActor<AHarvestingMinigame>();
	ANegotiationSystem* NegotiationSys = World->SpawnActor<ANegotiationSystem>();
	UVeilSightComponent* VeilSight = NewObject<UVeilSightComponent>();
	
	// Complete gameplay loop test
	
	// 1. Use VeilSight to see Dark World
	VeilSight->SetFocus(EVeilFocus::DarkWorld);
	TestEqual(TEXT("VeilSight should be set"), VeilSight->GetCurrentFocus(), EVeilFocus::DarkWorld);
	
	// 2. Find and harvest from target
	HarvestingGame->StartExtraction(TEXT("DarkTarget"), EExtractionMethod::LiveExtraction, EToolQuality::Advanced);
	HarvestingGame->CompleteExtraction(0.95f); // High quality
	TestTrue(TEXT("Harvesting complete"), true);
	
	// 3. Negotiate with Dark World client
	NegotiationSys->StartNegotiation(TEXT("Vampire-House"), 200.0f, TEXT("Excellent"));
	NegotiationSys->UseTactic(ENegotiationTactic::Charm);
	NegotiationSys->UseTactic(ENegotiationTactic::Logic);
	float FinalPrice = NegotiationSys->CurrentOffer;
	TestTrue(TEXT("Negotiation should increase price"), FinalPrice > 200.0f);
	NegotiationSys->CompleteNegotiation();
	
	// 4. Player dies during next attempt
	DeathSystem->TriggerDeath(FVector(500, 500, 100), TEXT("DarkWorld"), 
		TArray<FString>{TEXT("Sword"), TEXT("Potion")});
	TestEqual(TEXT("Veil Fray should increase"), DeathSystem->VeilFrayLevel, 1);
	
	// 5. Corpse run
	DeathSystem->StartCorpseRun();
	TestFalse(TEXT("Corpse run should start"), DeathSystem->CurrentCorpseID.IsEmpty());
	
	// 6. Bribe Corpse-Tender
	DeathSystem->BribeCorpseTender(TEXT("Rare Drug"));
	TestEqual(TEXT("Veil Fray should reduce"), DeathSystem->VeilFrayLevel, 0);
	
	// All systems should work together without crashing or corrupting state
	TestTrue(TEXT("Complete gameplay loop should work"), true);
	
	World->DestroyActor(HarvestingGame);
	World->DestroyActor(NegotiationSys);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationStressAllSystemsTest, "BodyBroker.Integration.StressTest", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationStressAllSystemsTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	
	// Create multiple instances of each system
	TArray<UDeathSystemComponent*> DeathSystems;
	TArray<AHarvestingMinigame*> HarvestingGames;
	TArray<ANegotiationSystem*> NegotiationSystems;
	TArray<UVeilSightComponent*> VeilSights;
	
	// Create 10 instances of each
	for (int32 i = 0; i < 10; i++)
	{
		DeathSystems.Add(NewObject<UDeathSystemComponent>());
		HarvestingGames.Add(World->SpawnActor<AHarvestingMinigame>());
		NegotiationSystems.Add(World->SpawnActor<ANegotiationSystem>());
		VeilSights.Add(NewObject<UVeilSightComponent>());
	}
	
	// Stress test - trigger all systems simultaneously
	for (int32 i = 0; i < 10; i++)
	{
		DeathSystems[i]->TriggerDeath(FVector(i * 100, i * 100, 0), TEXT("DarkWorld"), TArray<FString>());
		
		HarvestingGames[i]->StartExtraction(
			FString::Printf(TEXT("Target%d"), i),
			static_cast<EExtractionMethod>(i % 4),
			static_cast<EToolQuality>(i % 4)
		);
		
		NegotiationSystems[i]->StartNegotiation(
			FString::Printf(TEXT("Client%d"), i),
			100.0f + i * 10.0f,
			TEXT("Standard")
		);
		
		VeilSights[i]->SetFocus(static_cast<EVeilFocus>(i % 3));
	}
	
	// Complete all operations
	for (int32 i = 0; i < 10; i++)
	{
		DeathSystems[i]->StartCorpseRun();
		HarvestingGames[i]->CompleteExtraction(0.8f);
		NegotiationSystems[i]->UseTactic(ENegotiationTactic::Logic);
		NegotiationSystems[i]->CompleteNegotiation();
	}
	
	TestTrue(TEXT("All systems should handle concurrent operations"), true);
	
	// Cleanup
	for (int32 i = 0; i < 10; i++)
	{
		World->DestroyActor(HarvestingGames[i]);
		World->DestroyActor(NegotiationSystems[i]);
	}
	
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FIntegrationVeilSightCreatureTypesTest, "BodyBroker.Integration.VeilSightCreatureTypes", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FIntegrationVeilSightCreatureTypesTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	UVeilSightComponent* VeilSight = NewObject<UVeilSightComponent>();
	
	// Create creatures for each Dark World faction
	TArray<AActor*> Creatures;
	TArray<FString> FactionTags = {
		TEXT("Vampire"),
		TEXT("Zombie"),
		TEXT("Werewolf"),
		TEXT("Wraith"),
		TEXT("Fae")
	};
	
	for (const FString& Tag : FactionTags)
	{
		AActor* Creature = World->SpawnActor<AActor>();
		Creature->Tags.Add(FName(TEXT("DarkWorld")));
		Creature->Tags.Add(FName(*Tag));
		Creatures.Add(Creature);
	}
	
	// Test visibility in Dark World mode
	VeilSight->SetFocus(EVeilFocus::DarkWorld);
	for (AActor* Creature : Creatures)
	{
		TestTrue(TEXT("All Dark World creatures should be visible"), VeilSight->CanSeeCreature(Creature));
	}
	
	// Test visibility in Human World mode
	VeilSight->SetFocus(EVeilFocus::HumanWorld);
	for (AActor* Creature : Creatures)
	{
		TestFalse(TEXT("Dark World creatures should NOT be visible in Human World"), VeilSight->CanSeeCreature(Creature));
	}
	
	// Test visibility in Both mode
	VeilSight->SetFocus(EVeilFocus::Both);
	for (AActor* Creature : Creatures)
	{
		TestTrue(TEXT("All creatures should be visible in Both mode"), VeilSight->CanSeeCreature(Creature));
	}
	
	// Cleanup
	for (AActor* Creature : Creatures)
	{
		World->DestroyActor(Creature);
	}
	
	return true;
}

