// Game Observer Plugin - AI-Driven Game Testing System
// Copyright Gaming System AI Core

#include "GameObserverModule.h"

#define LOCTEXT_NAMESPACE "FGameObserverModule"

void FGameObserverModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	UE_LOG(LogTemp, Log, TEXT("GameObserver module started - AI-driven testing system active"));
}

void FGameObserverModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
	UE_LOG(LogTemp, Log, TEXT("GameObserver module shutdown"));
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FGameObserverModule, GameObserver)

