// Copyright Epic Games, Inc. All Rights Reserved.

#include "WeatherMaterialManager.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/World.h"
#include "WeatherManager.h"

UWeatherMaterialManager::UWeatherMaterialManager(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, CurrentWeatherState(EWeatherState::CLEAR)
	, CurrentWetness(0.0f)
	, CurrentSnowAccumulation(0.0f)
	, CurrentWindStrength(0.0f)
	, CurrentWindDirection(FVector::ForwardVector)
{
	PrimaryComponentTick.bCanEverTick = true;
	bTickInEditor = false;
}

void UWeatherMaterialManager::BeginPlay()
{
	Super::BeginPlay();
	LoadMaterialParameterCollection();
	UpdateMPCParameters();
	UE_LOG(LogTemp, Log, TEXT("WeatherMaterialManager: BeginPlay"));
}

void UWeatherMaterialManager::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Update puddle evaporation
	UpdatePuddles(DeltaTime);

	// Update material parameters if needed
	UpdateMaterialInstances();
}

void UWeatherMaterialManager::SetWeatherState(EWeatherState WeatherState, float Intensity)
{
	CurrentWeatherState = WeatherState;

	// Update wetness based on weather
	switch (WeatherState)
	{
	case EWeatherState::RAIN:
	case EWeatherState::HEAVY_RAIN:
	case EWeatherState::STORM:
		SetWetnessLevel(Intensity);
		SetSnowAccumulation(0.0f);
		break;

	case EWeatherState::SNOW:
	case EWeatherState::HEAVY_SNOW:
	case EWeatherState::BLIZZARD:
		SetSnowAccumulation(Intensity);
		SetWetnessLevel(0.0f);
		break;

	case EWeatherState::FOG:
	case EWeatherState::MIST:
		SetWetnessLevel(Intensity * 0.3f); // Light wetness from fog
		break;

	case EWeatherState::CLEAR:
	case EWeatherState::PARTLY_CLOUDY:
	case EWeatherState::CLOUDY:
	default:
		// Let wetness dry naturally, don't add more
		break;
	}

	UpdateMPCParameters();
	UpdateMaterialInstances();
}

void UWeatherMaterialManager::SetWetnessLevel(float Wetness)
{
	CurrentWetness = FMath::Clamp(Wetness, 0.0f, 1.0f);
	UpdateMPCParameters();
}

void UWeatherMaterialManager::SetSnowAccumulation(float Accumulation)
{
	CurrentSnowAccumulation = FMath::Clamp(Accumulation, 0.0f, 1.0f);
	UpdateMPCParameters();
}

void UWeatherMaterialManager::SetWindStrength(float WindStrength)
{
	CurrentWindStrength = FMath::Clamp(WindStrength, 0.0f, 1.0f);
	UpdateMPCParameters();
}

void UWeatherMaterialManager::SetWindDirection(const FVector& WindDirection)
{
	CurrentWindDirection = WindDirection.GetSafeNormal();
	UpdateMPCParameters();
}

void UWeatherMaterialManager::RegisterMaterial(UMaterialInterface* Material, UMaterialInstanceDynamic*& OutMaterialInstance)
{
	if (!Material)
	{
		OutMaterialInstance = nullptr;
		return;
	}

	// Check if already registered
	if (TObjectPtr<UMaterialInstanceDynamic>* ExistingInstance = RegisteredMaterials.Find(Material))
	{
		OutMaterialInstance = *ExistingInstance;
		return;
	}

	// Create new dynamic material instance
	OutMaterialInstance = UMaterialInstanceDynamic::Create(Material, this);
	if (OutMaterialInstance)
	{
		RegisteredMaterials.Add(Material, OutMaterialInstance);
		UE_LOG(LogTemp, Log, TEXT("WeatherMaterialManager: Registered material %s"), *Material->GetName());
	}
}

void UWeatherMaterialManager::CreatePuddle(const FVector& Location, float Size, float Depth)
{
	FPuddleData NewPuddle;
	NewPuddle.Location = Location;
	NewPuddle.Size = Size;
	NewPuddle.Depth = Depth;
	NewPuddle.Age = 0.0f;
	NewPuddle.EvaporationRate = 0.1f; // Evaporate over 10 seconds at base rate

	ActivePuddles.Add(NewPuddle);
	UE_LOG(LogTemp, Verbose, TEXT("WeatherMaterialManager: Created puddle at %s"), *Location.ToString());
}

void UWeatherMaterialManager::UpdateCloudMaterial(float CloudDensity, float CloudCoverage)
{
	if (WeatherMPCInstance)
	{
		WeatherMPCInstance->SetScalarParameterValue(TEXT("CloudDensity"), CloudDensity);
		WeatherMPCInstance->SetScalarParameterValue(TEXT("CloudCoverage"), CloudCoverage);
	}
}

void UWeatherMaterialManager::LoadMaterialParameterCollection()
{
	// Load the Material Parameter Collection
	FString MPCPath = TEXT("/Game/Materials/MPC_WeatherMaterials.MPC_WeatherMaterials");
	WeatherMPC = LoadObject<UMaterialParameterCollection>(nullptr, *MPCPath);

	if (WeatherMPC && GetWorld())
	{
		WeatherMPCInstance = GetWorld()->GetParameterCollectionInstance(WeatherMPC);
		UE_LOG(LogTemp, Log, TEXT("WeatherMaterialManager: Loaded Material Parameter Collection"));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("WeatherMaterialManager: Failed to load Material Parameter Collection at %s"), *MPCPath);
	}
}

void UWeatherMaterialManager::UpdateMPCParameters()
{
	if (!WeatherMPCInstance)
	{
		return;
	}

	// Update global weather parameters
	WeatherMPCInstance->SetScalarParameterValue(TEXT("Wetness"), CurrentWetness);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("SnowAccumulation"), CurrentSnowAccumulation);
	WeatherMPCInstance->SetScalarParameterValue(TEXT("WindStrength"), CurrentWindStrength);
	WeatherMPCInstance->SetVectorParameterValue(TEXT("WindDirection"), FLinearColor(CurrentWindDirection.X, CurrentWindDirection.Y, CurrentWindDirection.Z, 0.0f));
}

void UWeatherMaterialManager::UpdateMaterialInstances()
{
	// Update all registered material instances
	for (const auto& Pair : RegisteredMaterials)
	{
		if (UMaterialInstanceDynamic* MaterialInstance = Pair.Value)
		{
			MaterialInstance->SetScalarParameterValue(TEXT("Wetness"), CurrentWetness);
			MaterialInstance->SetScalarParameterValue(TEXT("SnowAccumulation"), CurrentSnowAccumulation);
			MaterialInstance->SetScalarParameterValue(TEXT("WindStrength"), CurrentWindStrength);
			MaterialInstance->SetVectorParameterValue(TEXT("WindDirection"), FLinearColor(CurrentWindDirection.X, CurrentWindDirection.Y, CurrentWindDirection.Z, 0.0f));
		}
	}
}

void UWeatherMaterialManager::UpdatePuddles(float DeltaTime)
{
	// Update puddle evaporation
	for (int32 i = ActivePuddles.Num() - 1; i >= 0; --i)
	{
		FPuddleData& Puddle = ActivePuddles[i];
		Puddle.Age += DeltaTime;

		// Evaporate based on weather conditions
		float EvaporationMultiplier = 1.0f;
		if (CurrentWeatherState == EWeatherState::RAIN || CurrentWeatherState == EWeatherState::HEAVY_RAIN)
		{
			EvaporationMultiplier = 0.0f; // No evaporation during rain
		}
		else if (CurrentWeatherState == EWeatherState::CLEAR)
		{
			EvaporationMultiplier = 2.0f; // Faster evaporation in clear weather
		}

		Puddle.Depth -= Puddle.EvaporationRate * EvaporationMultiplier * DeltaTime;

		// Remove evaporated puddles
		if (Puddle.Depth <= 0.0f)
		{
			ActivePuddles.RemoveAt(i);
		}
	}
}

