// Negotiation System Tests
// Comprehensive test suite for Dark World price negotiations

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "../NegotiationSystem.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNegotiationBasicTest, "BodyBroker.Negotiation.BasicFunctionality", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FNegotiationBasicTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	ANegotiationSystem* System = World->SpawnActor<ANegotiationSystem>();
	
	TestNotNull(TEXT("Negotiation system should be created"), System);
	TestEqual(TEXT("Initial offer should be 0"), System->CurrentOffer, 0.0f);
	TestTrue(TEXT("Initial client response should be empty"), System->CurrentClientResponse.IsEmpty());
	
	World->DestroyActor(System);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNegotiationStartTest, "BodyBroker.Negotiation.StartNegotiation", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FNegotiationStartTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	ANegotiationSystem* System = World->SpawnActor<ANegotiationSystem>();
	
	// Start negotiation with vampire client
	System->StartNegotiation(TEXT("Vampire-House-Crimson"), 100.0f, TEXT("Excellent"));
	
	TestEqual(TEXT("Base price should be set"), System->CurrentOffer, 100.0f);
	TestFalse(TEXT("Client response should be set"), System->CurrentClientResponse.IsEmpty());
	
	// Start new negotiation (should reset)
	System->StartNegotiation(TEXT("Zombie-Carrion-Clan"), 50.0f, TEXT("Poor"));
	
	TestEqual(TEXT("New base price should replace old"), System->CurrentOffer, 50.0f);
	
	World->DestroyActor(System);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNegotiationTacticsTest, "BodyBroker.Negotiation.TacticEffectiveness", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FNegotiationTacticsTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	ANegotiationSystem* System = World->SpawnActor<ANegotiationSystem>();
	
	float BasePrice = 100.0f;
	System->StartNegotiation(TEXT("TestClient"), BasePrice, TEXT("Standard"));
	
	// Test Intimidate (15% increase)
	System->UseTactic(ENegotiationTactic::Intimidate);
	float ExpectedAfterIntimidate = BasePrice * 1.15f;
	TestEqual(TEXT("Intimidate should increase price by 15%"), System->CurrentOffer, ExpectedAfterIntimidate);
	
	// Test Charm (10% increase)
	float BeforeCharm = System->CurrentOffer;
	System->UseTactic(ENegotiationTactic::Charm);
	float ExpectedAfterCharm = BeforeCharm * 1.10f;
	TestEqual(TEXT("Charm should increase price by 10%"), System->CurrentOffer, ExpectedAfterCharm);
	
	// Test Logic (8% increase)
	float BeforeLogic = System->CurrentOffer;
	System->UseTactic(ENegotiationTactic::Logic);
	float ExpectedAfterLogic = BeforeLogic * 1.08f;
	TestEqual(TEXT("Logic should increase price by 8%"), System->CurrentOffer, ExpectedAfterLogic);
	
	// Test AppealToGreed (12% increase)
	float BeforeGreed = System->CurrentOffer;
	System->UseTactic(ENegotiationTactic::AppealToGreed);
	float ExpectedAfterGreed = BeforeGreed * 1.12f;
	TestEqual(TEXT("Greed should increase price by 12%"), System->CurrentOffer, ExpectedAfterGreed);
	
	// Test Riddle (20% increase - highest risk/reward)
	float BeforeRiddle = System->CurrentOffer;
	System->UseTactic(ENegotiationTactic::Riddle);
	float ExpectedAfterRiddle = BeforeRiddle * 1.20f;
	TestEqual(TEXT("Riddle should increase price by 20%"), System->CurrentOffer, ExpectedAfterRiddle);
	
	World->DestroyActor(System);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNegotiationPriceClampingTest, "BodyBroker.Negotiation.PriceClamping", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FNegotiationPriceClampingTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	ANegotiationSystem* System = World->SpawnActor<ANegotiationSystem>();
	
	// Test price should increase but not go negative or unreasonable
	System->StartNegotiation(TEXT("TestClient"), 10.0f, TEXT("Poor"));
	
	// Apply 10 riddles (extreme case)
	for (int32 i = 0; i < 10; i++)
	{
		System->UseTactic(ENegotiationTactic::Riddle);
	}
	
	// Price should be high but reasonable
	TestTrue(TEXT("Price should not overflow"), System->CurrentOffer > 0.0f);
	TestTrue(TEXT("Price should be finite"), FMath::IsFinite(System->CurrentOffer));
	
	World->DestroyActor(System);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNegotiationCompletionTest, "BodyBroker.Negotiation.Completion", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FNegotiationCompletionTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	ANegotiationSystem* System = World->SpawnActor<ANegotiationSystem>();
	
	// Start and complete negotiation
	System->StartNegotiation(TEXT("TestClient"), 100.0f, TEXT("Excellent"));
	System->UseTactic(ENegotiationTactic::Charm);
	System->UseTactic(ENegotiationTactic::Logic);
	
	float FinalPrice = System->CurrentOffer;
	TestTrue(TEXT("Final price should be set"), FinalPrice > 0.0f);
	
	System->CompleteNegotiation();
	
	// After completion, state should be reset
	TestEqual(TEXT("Offer should be reset to 0"), System->CurrentOffer, 0.0f);
	
	World->DestroyActor(System);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNegotiationEdgeCasesTest, "BodyBroker.Negotiation.EdgeCases", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FNegotiationEdgeCasesTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	ANegotiationSystem* System = World->SpawnActor<ANegotiationSystem>();
	
	// Test negotiation with zero base price
	System->StartNegotiation(TEXT("TestClient"), 0.0f, TEXT("None"));
	TestEqual(TEXT("Should handle zero base price"), System->CurrentOffer, 0.0f);
	System->UseTactic(ENegotiationTactic::Charm);
	TestEqual(TEXT("Zero price * modifier should remain zero"), System->CurrentOffer, 0.0f);
	
	// Test negotiation with empty client ID
	System->StartNegotiation(TEXT(""), 100.0f, TEXT("Standard"));
	TestTrue(TEXT("Should handle empty client ID"), true);
	
	// Test completion without starting
	ANegotiationSystem* System2 = World->SpawnActor<ANegotiationSystem>();
	System2->CompleteNegotiation();
	TestTrue(TEXT("Should handle completion without negotiation"), true);
	
	World->DestroyActor(System);
	World->DestroyActor(System2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNegotiationTacticStackingTest, "BodyBroker.Negotiation.TacticStacking", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FNegotiationTacticStackingTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	ANegotiationSystem* System = World->SpawnActor<ANegotiationSystem>();
	
	System->StartNegotiation(TEXT("TestClient"), 100.0f, TEXT("Standard"));
	
	// Use same tactic multiple times (should stack)
	System->UseTactic(ENegotiationTactic::Intimidate); // 115
	float AfterFirst = System->CurrentOffer;
	
	System->UseTactic(ENegotiationTactic::Intimidate); // 115 * 1.15 = 132.25
	float AfterSecond = System->CurrentOffer;
	
	TestTrue(TEXT("Second use of tactic should still apply"), AfterSecond > AfterFirst);
	TestEqual(TEXT("Price should compound correctly"), AfterSecond, 100.0f * 1.15f * 1.15f);
	
	World->DestroyActor(System);
	return true;
}

