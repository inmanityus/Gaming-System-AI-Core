// Copyright Body Broker - Gaming System AI Core

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FVocalSynthesisModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};

