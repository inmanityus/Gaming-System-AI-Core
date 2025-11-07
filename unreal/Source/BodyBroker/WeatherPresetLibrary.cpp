// Copyright Epic Games, Inc. All Rights Reserved.

#include "WeatherPresetLibrary.h"
#include "WeatherPresetLibrary.h"

UWeatherPreset* UWeatherPresetLibrary::GetRandomWeatherPreset(float SeasonProgress, const FString& TimeOfDayState) const
{
	TArray<UWeatherPreset*> ValidPresets;

	// Filter presets by season and time of day
	for (TObjectPtr<UWeatherPreset> Preset : WeatherPresets)
	{
		if (!Preset)
		{
			continue;
		}

		// Check season preference (within 0.25 range)
		float SeasonDiff = FMath::Abs(Preset->PreferredSeason - SeasonProgress);
		if (SeasonDiff > 0.25f && SeasonDiff < 0.75f) // Wrap around check
		{
			SeasonDiff = 1.0f - SeasonDiff;
		}

		if (SeasonDiff > 0.25f)
		{
			continue; // Too far from preferred season
		}

		// Check time of day preference
		if (!Preset->PreferredTimeOfDay.IsEmpty() && Preset->PreferredTimeOfDay != TimeOfDayState)
		{
			continue;
		}

		// Apply seasonal probability adjustments if available
		float AdjustedWeight = Preset->ProbabilityWeight;
		for (const FSeasonalProbabilityData& SeasonData : SeasonalProbabilities)
		{
			if (FMath::Abs(SeasonData.SeasonKey - SeasonProgress) < 0.25f)
			{
				if (const float* SeasonProb = SeasonData.Probabilities.Find(Preset->WeatherState))
				{
					AdjustedWeight *= *SeasonProb;
				}
			}
		}

		// Only add if weight is significant
		if (AdjustedWeight > 0.01f)
		{
			ValidPresets.Add(Preset);
		}
	}

	// If no valid presets, use all presets
	if (ValidPresets.Num() == 0)
	{
		for (TObjectPtr<UWeatherPreset> Preset : WeatherPresets)
		{
			if (Preset)
			{
				ValidPresets.Add(Preset);
			}
		}
	}

	// Select random preset weighted by probability
	if (ValidPresets.Num() > 0)
	{
		float TotalWeight = 0.0f;
		for (UWeatherPreset* Preset : ValidPresets)
		{
			TotalWeight += Preset->ProbabilityWeight;
		}

		float RandomValue = FMath::RandRange(0.0f, TotalWeight);
		float AccumulatedWeight = 0.0f;

		for (UWeatherPreset* Preset : ValidPresets)
		{
			AccumulatedWeight += Preset->ProbabilityWeight;
			if (RandomValue <= AccumulatedWeight)
			{
				return Preset;
			}
		}

		return ValidPresets[0]; // Fallback
	}

	return nullptr;
}

UWeatherPreset* UWeatherPresetLibrary::GetWeatherPresetByName(const FString& PresetName) const
{
	for (TObjectPtr<UWeatherPreset> Preset : WeatherPresets)
	{
		if (Preset && Preset->PresetName == PresetName)
		{
			return Preset;
		}
	}
	return nullptr;
}

