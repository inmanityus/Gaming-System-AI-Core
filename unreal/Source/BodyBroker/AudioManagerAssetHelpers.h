// AudioManager Asset Creation Helper
// Creates reverb effects programmatically via C++

#pragma once

#include "CoreMinimal.h"
#include "Engine/Engine.h"
#include "Sound/ReverbEffect.h"
#include "Kismet/GameplayStatics.h"
#include "AudioManagerAssetHelpers.generated.h"

/**
 * Helper class for creating audio assets programmatically
 */
UCLASS()
class BODYBROKER_API UAudioManagerAssetHelpers : public UObject
{
	GENERATED_BODY()

public:
	/**
	 * Helper function to create ReverbEffect assets programmatically
	 * Can be called from Python or Blueprint
	 * 
	 * Note: Settings are applied directly to UReverbEffect properties
	 */
	UFUNCTION(BlueprintCallable, Category = "Audio Manager|Asset Creation")
	static UReverbEffect* CreateReverbEffectAsset(
		const FString& AssetName,
		const FString& PackagePath,
		float Density = 1.0f,
		float Diffusion = 1.0f,
		float Gain = 0.32f,
		float GainHF = 0.89f,
		float DecayTime = 1.49f,
		float DecayHFRatio = 0.83f,
		float ReflectionsGain = 0.05f,
		float ReflectionsDelay = 0.007f,
		float LateGain = 1.26f,
		float LateDelay = 0.011f,
		float AirAbsorptionGainHF = 0.994f
	);
};

