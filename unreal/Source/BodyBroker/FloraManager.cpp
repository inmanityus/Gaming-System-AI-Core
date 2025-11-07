// Copyright Epic Games, Inc. All Rights Reserved.

#include "FloraManager.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "BiomeManager.h"
#include "Materials/MaterialInstanceDynamic.h"

void UFloraManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	CurrentWindStrength = 0.0f;
	CurrentWindDirection = FVector::ForwardVector;
	CurrentSeasonProgress = 0.25f; // Default to summer
	UE_LOG(LogTemp, Log, TEXT("FloraManager: Initialized"));
}

void UFloraManager::Deinitialize()
{
	HISMComponents.Empty();
	FloraDataByBiome.Empty();
	Super::Deinitialize();
}

UFloraManager* UFloraManager::Get(const UObject* WorldContext)
{
	if (!WorldContext)
	{
		return nullptr;
	}

	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UFloraManager>();
		}
	}

	return nullptr;
}

void UFloraManager::RegisterFloraType(EBiomeType BiomeType, UStaticMesh* Mesh, UMaterialInterface* Material, float Density)
{
	if (!Mesh)
	{
		UE_LOG(LogTemp, Warning, TEXT("FloraManager: Attempted to register null mesh"));
		return;
	}

	FFloraTypeData FloraData;
	FloraData.Mesh = Mesh;
	FloraData.Material = Material;
	FloraData.Density = FMath::Clamp(Density, 0.0f, 1.0f);

	TArray<FFloraTypeData>& FloraList = FloraDataByBiome.FindOrAdd(BiomeType);
	FloraList.Add(FloraData);

	UE_LOG(LogTemp, Log, TEXT("FloraManager: Registered flora type for biome %d"), (int32)BiomeType);
}

void UFloraManager::SpawnFloraInArea(const FVector& Center, float Radius, EBiomeType BiomeType)
{
	if (const TArray<FFloraTypeData>* FloraList = FloraDataByBiome.Find(BiomeType))
	{
		for (const FFloraTypeData& FloraData : *FloraList)
		{
			// Calculate number of instances based on density and area
			float Area = PI * Radius * Radius;
			int32 InstanceCount = FMath::RoundToInt(Area * FloraData.Density * 0.01f); // Scale factor

			// Get or create HISM component
			UHierarchicalInstancedStaticMeshComponent* HISMComponent = GetOrCreateHISMComponent(FloraData.Mesh, FloraData.Material);

			if (HISMComponent)
			{
				// Spawn instances in area
				for (int32 i = 0; i < InstanceCount; ++i)
				{
					FVector RandomLocation = Center + FVector(
						FMath::RandRange(-Radius, Radius),
						FMath::RandRange(-Radius, Radius),
						0.0f
					);

					FRotator RandomRotation(0.0f, FMath::RandRange(0.0f, 360.0f), 0.0f);
					FVector RandomScale = FVector::OneVector * FMath::RandRange(0.8f, 1.2f);

					FTransform InstanceTransform(RandomRotation, RandomLocation, RandomScale);
					HISMComponent->AddInstance(InstanceTransform);
				}

				UE_LOG(LogTemp, Verbose, TEXT("FloraManager: Spawned %d instances of flora in area"), InstanceCount);
			}
		}
	}
}

void UFloraManager::SetWindStrength(float WindStrength)
{
	CurrentWindStrength = FMath::Clamp(WindStrength, 0.0f, 1.0f);
	UpdateHISMWindParameters();
}

void UFloraManager::SetWindDirection(const FVector& WindDirection)
{
	CurrentWindDirection = WindDirection.GetSafeNormal();
	UpdateHISMWindParameters();
}

void UFloraManager::UpdateSeasonalAppearance(float SeasonProgress)
{
	CurrentSeasonProgress = FMath::Clamp(SeasonProgress, 0.0f, 1.0f);

	// Update material parameters for seasonal changes
	// Update material instances with seasonal color variations
	for (TObjectPtr<UHierarchicalInstancedStaticMeshComponent> HISMComponent : HISMComponents)
	{
		if (HISMComponent)
		{
			// Update material parameter for season
			// Note: This requires material instances with SeasonProgress parameter
			// HISM components use shared materials, so we need to create material instances
			int32 MaterialCount = HISMComponent->GetNumMaterials();
			for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
			{
				UMaterialInterface* Material = HISMComponent->GetMaterial(MaterialIndex);
				if (Material)
				{
					// Create or get material instance dynamic
					UMaterialInstanceDynamic* MID = HISMComponent->CreateDynamicMaterialInstance(MaterialIndex, Material);
					if (MID)
					{
						// Set seasonal parameter
						MID->SetScalarParameterValue(TEXT("SeasonProgress"), CurrentSeasonProgress);
					}
				}
			}
		}
	}
}

UHierarchicalInstancedStaticMeshComponent* UFloraManager::GetOrCreateHISMComponent(UStaticMesh* Mesh, UMaterialInterface* Material)
{
	// Find existing HISM component for this mesh
	for (TObjectPtr<UHierarchicalInstancedStaticMeshComponent> HISMComponent : HISMComponents)
	{
		if (HISMComponent && HISMComponent->GetStaticMesh() == Mesh)
		{
			return HISMComponent;
		}
	}

	// Create new HISM component
	if (UWorld* World = GetWorld())
	{
		UHierarchicalInstancedStaticMeshComponent* NewHISMComponent = NewObject<UHierarchicalInstancedStaticMeshComponent>(World);
		if (NewHISMComponent)
		{
			NewHISMComponent->SetStaticMesh(Mesh);
			if (Material)
			{
				NewHISMComponent->SetMaterial(0, Material);
			}
			NewHISMComponent->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
			NewHISMComponent->RegisterComponent();

			HISMComponents.Add(NewHISMComponent);
			return NewHISMComponent;
		}
	}

	return nullptr;
}

void UFloraManager::UpdateHISMWindParameters()
{
	// Update wind parameters on all HISM components
	// Set material parameters for wind animation
	for (TObjectPtr<UHierarchicalInstancedStaticMeshComponent> HISMComponent : HISMComponents)
	{
		if (HISMComponent)
		{
			// Set wind parameters via material instances
			// Create or get material instance dynamic for wind parameters
			int32 MaterialCount = HISMComponent->GetNumMaterials();
			for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
			{
				UMaterialInterface* Material = HISMComponent->GetMaterial(MaterialIndex);
				if (Material)
				{
					UMaterialInstanceDynamic* MID = HISMComponent->CreateDynamicMaterialInstance(MaterialIndex, Material);
					if (MID)
					{
						// Set wind strength and direction parameters
						MID->SetScalarParameterValue(TEXT("WindStrength"), CurrentWindStrength);
						MID->SetVectorParameterValue(TEXT("WindDirection"), FLinearColor(CurrentWindDirection.X, CurrentWindDirection.Y, CurrentWindDirection.Z, 0.0f));
					}
				}
			}
		}
	}
}

