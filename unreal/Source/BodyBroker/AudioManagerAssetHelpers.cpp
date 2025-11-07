#include "AudioManagerAssetHelpers.h"
#include "Sound/ReverbEffect.h"
#include "Engine/Engine.h"

#if WITH_EDITOR
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
#include "Editor.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "PackageTools.h"
#include "Misc/PackageName.h"
#endif

UReverbEffect* UAudioManagerAssetHelpers::CreateReverbEffectAsset(
	const FString& AssetName,
	const FString& PackagePath,
	float Density,
	float Diffusion,
	float Gain,
	float GainHF,
	float DecayTime,
	float DecayHFRatio,
	float ReflectionsGain,
	float ReflectionsDelay,
	float LateGain,
	float LateDelay,
	float AirAbsorptionGainHF
)
{
#if WITH_EDITOR
	// Create package name
	FString PackageName = PackagePath + "/" + AssetName;
	UPackage* Package = CreatePackage(*PackageName);
	if (!Package)
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to create package: %s"), *PackageName);
		return nullptr;
	}
	
	Package->FullyLoad();
	
	// Create ReverbEffect object
	UReverbEffect* ReverbEffect = NewObject<UReverbEffect>(
		Package, 
		*AssetName, 
		RF_Public | RF_Standalone | RF_MarkAsRootSet
	);
	if (!ReverbEffect)
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to create ReverbEffect: %s"), *AssetName);
		return nullptr;
	}
	
	// Set reverb properties DIRECTLY (UReverbEffect has direct properties, not Settings struct)
	ReverbEffect->Density = Density;
	ReverbEffect->Diffusion = Diffusion;
	ReverbEffect->Gain = Gain;
	ReverbEffect->GainHF = GainHF;
	ReverbEffect->DecayTime = DecayTime;
	ReverbEffect->DecayHFRatio = DecayHFRatio;
	ReverbEffect->ReflectionsGain = ReflectionsGain;
	ReverbEffect->ReflectionsDelay = ReflectionsDelay;
	ReverbEffect->LateGain = LateGain;
	ReverbEffect->LateDelay = LateDelay;
	ReverbEffect->AirAbsorptionGainHF = AirAbsorptionGainHF;
	// Note: RoomRolloffFactor is deprecated in UE5.6.1
	// Note: Volume is not a property of UReverbEffect
	
	// Post edit change to apply properties
	ReverbEffect->PostEditChange();
	
	// Mark package as dirty
	Package->MarkPackageDirty();
	
	// Notify asset registry BEFORE saving
	FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	AssetRegistryModule.AssetCreated(ReverbEffect);
	
	// Save the package using UPackage::SavePackage (UE5.0+ method)
	FString PackageFileName = FPackageName::LongPackageNameToFilename(
		PackageName, 
		FPackageName::GetAssetPackageExtension()
	);
	
	FSavePackageArgs SaveArgs;
	SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
	SaveArgs.SaveFlags = SAVE_NoError;
	
	bool bSaved = UPackage::SavePackage(
		Package, 
		ReverbEffect, 
		*PackageFileName, 
		SaveArgs
	);
	
	if (bSaved)
	{
		UE_LOG(LogTemp, Log, TEXT("Successfully created and saved ReverbEffect: %s"), *PackageName);
		
		// Force registry to scan
		AssetRegistryModule.Get().ScanPathsSynchronous({ PackagePath }, true);
		
		return ReverbEffect;
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to save ReverbEffect: %s"), *PackageName);
		
		// Fallback: Try using EditorAssetSubsystem
		if (GEditor)
		{
			UEditorAssetSubsystem* EditorAssetSubsystem = GEditor->GetEditorSubsystem<UEditorAssetSubsystem>();
			if (EditorAssetSubsystem)
			{
				FString AssetPath = PackageName + "." + AssetName;
				bool bSavedAlt = EditorAssetSubsystem->SaveAsset(AssetPath, false);
				if (bSavedAlt)
				{
					UE_LOG(LogTemp, Log, TEXT("Saved using EditorAssetSubsystem: %s"), *AssetPath);
					return ReverbEffect;
				}
			}
		}
		
		return nullptr;
	}
#else
	UE_LOG(LogTemp, Warning, TEXT("CreateReverbEffectAsset only available in editor"));
	return nullptr;
#endif
}

