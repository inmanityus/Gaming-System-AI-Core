// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "AudioManager.h"
#include "WeatherPresetLibrary.generated.h"

/**
 * Seasonal probability data structure
 */
USTRUCT(BlueprintType)
struct FSeasonalProbabilityData
{
	GENERATED_BODY()

	// Season key (0.0=Spring, 0.25=Summer, 0.5=Fall, 0.75=Winter)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seasonal Weather")
	float SeasonKey;

	// Weather state probabilities
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seasonal Weather")
	TMap<EWeatherState, float> Probabilities;

	FSeasonalProbabilityData()
		: SeasonKey(0.25f)
	{}
};

/**
 * Weather preset data asset
 * WS-004: Weather Integration & Polish
 */
UCLASS(BlueprintType)
class BODYBROKER_API UWeatherPreset : public UDataAsset
{
	GENERATED_BODY()

public:
	// Preset name
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Preset")
	FString PresetName;

	// Weather state
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Preset")
	EWeatherState WeatherState;

	// Weather intensity
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Preset")
	float Intensity;

	// Transition duration
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Preset")
	float TransitionDuration;

	// Time of day preference (empty = any time)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Preset")
	FString PreferredTimeOfDay;

	// Season preference (0.0 = Spring, 0.25 = Summer, 0.5 = Fall, 0.75 = Winter)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Preset")
	float PreferredSeason;

	// Probability weight (for random selection)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Preset")
	float ProbabilityWeight;

	UWeatherPreset()
		: Intensity(1.0f)
		, TransitionDuration(10.0f)
		, PreferredSeason(0.25f) // Default to summer
		, ProbabilityWeight(1.0f)
	{}
};

/**
 * WeatherPresetLibrary - Manages weather presets and seasonal weather system
 * WS-004: Weather Integration & Polish
 */
UCLASS(BlueprintType)
class BODYBROKER_API UWeatherPresetLibrary : public UDataAsset
{
	GENERATED_BODY()

public:
	// Weather presets
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Presets")
	TArray<TObjectPtr<UWeatherPreset>> WeatherPresets;

	// Seasonal weather probabilities (by season: 0.0=Spring, 0.25=Summer, 0.5=Fall, 0.75=Winter)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seasonal Weather")
	TArray<FSeasonalProbabilityData> SeasonalProbabilities;

	/**
	 * Get random weather preset based on current season and time of day.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Presets|WS-004")
	UWeatherPreset* GetRandomWeatherPreset(float SeasonProgress, const FString& TimeOfDayState) const;

	/**
	 * Get weather preset by name.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Presets|WS-004")
	UWeatherPreset* GetWeatherPresetByName(const FString& PresetName) const;
};

