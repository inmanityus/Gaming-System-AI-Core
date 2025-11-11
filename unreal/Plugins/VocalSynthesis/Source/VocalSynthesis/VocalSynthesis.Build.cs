// Copyright Body Broker - Gaming System AI Core

using UnrealBuildTool;
using System.IO;

public class VocalSynthesis : ModuleRules
{
	public VocalSynthesis(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		
		PublicIncludePaths.AddRange(
			new string[] {
				Path.Combine(ModuleDirectory, "Public")
			}
		);
				
		
		PrivateIncludePaths.AddRange(
			new string[] {
				Path.Combine(ModuleDirectory, "Private")
			}
		);
			
		
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"AudioMixer",
				"SignalProcessing"
			}
		);
			
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Engine",
				"Slate",
				"SlateCore",
				"AudioExtensions"
			}
		);
		
		// Link to vocal_synthesis C++ library
		string VocalSynthLibPath = Path.Combine(ModuleDirectory, "..", "..", "..", "..", "..", "vocal-chord-research", "cpp-implementation", "build", "Release");
		string VocalSynthIncludePath = Path.Combine(ModuleDirectory, "..", "..", "..", "..", "..", "vocal-chord-research", "cpp-implementation", "include");
		
		PublicAdditionalLibraries.Add(Path.Combine(VocalSynthLibPath, "vocal_synthesis.lib"));
		PublicIncludePaths.Add(VocalSynthIncludePath);
	}
}

