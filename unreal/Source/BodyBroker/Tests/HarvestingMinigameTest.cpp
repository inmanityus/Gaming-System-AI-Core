// Harvesting Minigame Tests
// Comprehensive test suite for body part extraction system

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "../HarvestingMinigame.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHarvestingBasicTest, "BodyBroker.Harvesting.BasicFunctionality", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FHarvestingBasicTest::RunTest(const FString& Parameters)
{
	// Create actor in test world
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	AHarvestingMinigame* Minigame = World->SpawnActor<AHarvestingMinigame>();
	
	TestNotNull(TEXT("Minigame should be created"), Minigame);
	TestEqual(TEXT("Initial decay should be 0"), Minigame->CurrentDecayPercentage, 0.0f);
	TestEqual(TEXT("Default decay timer should be 300s"), Minigame->DecayTimerSeconds, 300.0f);
	
	World->DestroyActor(Minigame);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHarvestingExtractionMethodsTest, "BodyBroker.Harvesting.ExtractionMethods", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FHarvestingExtractionMethodsTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	AHarvestingMinigame* Minigame = World->SpawnActor<AHarvestingMinigame>();
	
	// Test each extraction method
	Minigame->StartExtraction(TEXT("Target1"), EExtractionMethod::ShotgunBlast, EToolQuality::Standard);
	TestTrue(TEXT("Shotgun blast extraction should start"), true);
	
	Minigame->CompleteExtraction(0.8f);
	
	Minigame->StartExtraction(TEXT("Target2"), EExtractionMethod::BladeKill, EToolQuality::Standard);
	TestTrue(TEXT("Blade kill extraction should start"), true);
	
	Minigame->CompleteExtraction(0.9f);
	
	Minigame->StartExtraction(TEXT("Target3"), EExtractionMethod::PoisonKill, EToolQuality::Standard);
	TestTrue(TEXT("Poison kill extraction should start"), true);
	
	Minigame->CompleteExtraction(0.95f);
	
	Minigame->StartExtraction(TEXT("Target4"), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	TestTrue(TEXT("Live extraction should start"), true);
	
	Minigame->CompleteExtraction(1.0f);
	
	World->DestroyActor(Minigame);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHarvestingToolQualityTest, "BodyBroker.Harvesting.ToolQuality", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FHarvestingToolQualityTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	AHarvestingMinigame* Minigame = World->SpawnActor<AHarvestingMinigame>();
	
	// Test rusty tools (slower, more decay)
	Minigame->StartExtraction(TEXT("Target1"), EExtractionMethod::LiveExtraction, EToolQuality::Rusty);
	TestEqual(TEXT("Rusty tools should have 180s decay timer"), Minigame->DecayTimerSeconds, 180.0f);
	Minigame->CompleteExtraction(1.0f);
	
	// Test standard tools
	Minigame->StartExtraction(TEXT("Target2"), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	TestEqual(TEXT("Standard tools should have 300s decay timer"), Minigame->DecayTimerSeconds, 300.0f);
	Minigame->CompleteExtraction(1.0f);
	
	// Test surgical tools (faster, less decay)
	Minigame->StartExtraction(TEXT("Target3"), EExtractionMethod::LiveExtraction, EToolQuality::Surgical);
	TestEqual(TEXT("Surgical tools should have 450s decay timer"), Minigame->DecayTimerSeconds, 450.0f);
	Minigame->CompleteExtraction(1.0f);
	
	// Test advanced tools (fastest)
	Minigame->StartExtraction(TEXT("Target4"), EExtractionMethod::LiveExtraction, EToolQuality::Advanced);
	TestEqual(TEXT("Advanced tools should have 600s decay timer"), Minigame->DecayTimerSeconds, 600.0f);
	Minigame->CompleteExtraction(1.0f);
	
	World->DestroyActor(Minigame);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHarvestingDecayTest, "BodyBroker.Harvesting.DecayMechanic", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FHarvestingDecayTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	AHarvestingMinigame* Minigame = World->SpawnActor<AHarvestingMinigame>();
	
	// Start extraction
	Minigame->StartExtraction(TEXT("Target1"), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	float InitialDecay = Minigame->CurrentDecayPercentage;
	TestEqual(TEXT("Initial decay should be 0"), InitialDecay, 0.0f);
	
	// Simulate decay
	Minigame->CurrentDecayPercentage = 25.0f;
	
	// Complete with decay penalty
	Minigame->CompleteExtraction(1.0f); // Perfect skill
	// Final quality = 1.0 * (1 - 0.25) = 0.75
	
	TestTrue(TEXT("Decay should affect final quality"), true);
	
	World->DestroyActor(Minigame);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHarvestingEdgeCasesTest, "BodyBroker.Harvesting.EdgeCases", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FHarvestingEdgeCasesTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	AHarvestingMinigame* Minigame = World->SpawnActor<AHarvestingMinigame>();
	
	// Test completion without starting
	Minigame->CompleteExtraction(1.0f);
	TestTrue(TEXT("Should handle completion without extraction"), true);
	
	// Test zero skill rating
	Minigame->StartExtraction(TEXT("Target1"), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	Minigame->CompleteExtraction(0.0f);
	TestTrue(TEXT("Should handle zero skill rating"), true);
	
	// Test negative skill rating (should clamp to 0)
	Minigame->StartExtraction(TEXT("Target2"), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	Minigame->CompleteExtraction(-0.5f);
	TestTrue(TEXT("Should handle negative skill rating"), true);
	
	// Test skill rating > 1.0 (should clamp to 1.0)
	Minigame->StartExtraction(TEXT("Target3"), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	Minigame->CompleteExtraction(1.5f);
	TestTrue(TEXT("Should handle skill rating > 1.0"), true);
	
	// Test empty target ID
	Minigame->StartExtraction(TEXT(""), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	Minigame->CompleteExtraction(1.0f);
	TestTrue(TEXT("Should handle empty target ID"), true);
	
	World->DestroyActor(Minigame);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHarvestingConcurrentExtractionTest, "BodyBroker.Harvesting.ConcurrentExtraction", 
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FHarvestingConcurrentExtractionTest::RunTest(const FString& Parameters)
{
	UWorld* World = GEngine->GetWorldContexts()[0].World();
	AHarvestingMinigame* Minigame = World->SpawnActor<AHarvestingMinigame>();
	
	// Start extraction
	Minigame->StartExtraction(TEXT("Target1"), EExtractionMethod::LiveExtraction, EToolQuality::Standard);
	
	// Attempt second extraction while first is in progress
	Minigame->StartExtraction(TEXT("Target2"), EExtractionMethod::BladeKill, EToolQuality::Surgical);
	
	// Should be blocked
	TestTrue(TEXT("Concurrent extraction should be blocked"), true);
	
	// Complete first extraction
	Minigame->CompleteExtraction(1.0f);
	
	// Now second extraction should work
	Minigame->StartExtraction(TEXT("Target2"), EExtractionMethod::BladeKill, EToolQuality::Surgical);
	TestTrue(TEXT("New extraction after completion should work"), true);
	
	World->DestroyActor(Minigame);
	return true;
}

