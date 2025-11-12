// Game Observer Plugin - AI-Driven Game Testing System
// Copyright Gaming System AI Core

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FGameObserverModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};

