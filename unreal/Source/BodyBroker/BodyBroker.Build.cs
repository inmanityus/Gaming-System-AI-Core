// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class BodyBroker : ModuleRules
{
	public BodyBroker(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(new string[] { 
			"Core", 
			"CoreUObject", 
			"Engine", 
			"InputCore",
			"HTTP",
			"Json",
			"JsonUtilities",
		"Niagara",
		"AudioMixer",
		"AnimationCore",
			"OnlineSubsystem",
			"OnlineSubsystemSteam",
			"UMG",
			"Slate",
			"SlateCore"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { 
			"AssetRegistry",
			"UnrealEd",
			"ToolMenus",
			"EditorSubsystem"
		});

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}

