# Flora Management System Architecture
**Date**: 2025-01-29  
**Task**: TE-002 - Flora Management System  
**Status**: Design Complete

---

## OVERVIEW

Complete flora management system architecture using HISM pooling, chunk-based streaming, PCG graphs, LOD, wind animation, and seasonal appearance changes.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **Biome System** (TE-001)
   - Biome detection
   - Registry system
   - Environment parameters

2. **Weather System** (WS-001, WS-002)
   - Wind data
   - Season tracking
   - Material parameters

3. **Unreal Engine 5**
   - HISM (Hierarchical Instanced Static Mesh)
   - PCG Framework
   - World Partition streaming

---

## FLORA MANAGER WITH HISM POOLING

### FloraManager Architecture

```cpp
UCLASS()
class AFLoraManager : public AActor
{
    GENERATED_BODY()

public:
    // Initialize flora system
    UFUNCTION(BlueprintCallable, Category = "Flora")
    void InitializeFloraSystem();
    
    // Spawn flora in chunk
    UFUNCTION(BlueprintCallable, Category = "Flora")
    void SpawnFloraInChunk(UWorldPartitionCell* Cell);
    
    // Remove flora from chunk
    UFUNCTION(BlueprintCallable, Category = "Flora")
    void RemoveFloraFromChunk(UWorldPartitionCell* Cell);

private:
    // Flora types
    UPROPERTY()
    TArray<FFloraType> FloraTypes;
    
    // HISM component pools (by type)
    UPROPERTY()
    TMap<FString, TArray<UHierarchicalInstancedStaticMeshComponent*>> HISMPool;
    
    // Active flora instances
    UPROPERTY()
    TMap<UWorldPartitionCell*, TArray<FFloraInstance>> ActiveFlora;
    
    // Pool management
    UHierarchicalInstancedStaticMeshComponent* AcquireHISMComponent(const FString& FloraType);
    void ReleaseHISMComponent(UHierarchicalInstancedStaticMeshComponent* Component);
};
```

### Flora Data Structure

```cpp
USTRUCT(BlueprintType)
struct FFloraType
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly)
    FString TypeID;
    
    UPROPERTY(EditDefaultsOnly)
    UStaticMesh* Mesh;
    
    UPROPERTY(EditDefaultsOnly)
    TArray<UMaterialInstance*> MaterialVariations;
    
    // Density per 100m²
    UPROPERTY(EditDefaultsOnly)
    float Density;
    
    // Biome suitability
    UPROPERTY(EditDefaultsOnly)
    TArray<FString> SuitableBiomes;
};

USTRUCT()
struct FFloraInstance
{
    GENERATED_BODY()

    FString TypeID;
    FTransform Transform;
    UHierarchicalInstancedStaticMeshComponent* HISMComponent;
    int32 InstanceIndex;
    float SpawnTime;
};
```

### HISM Pool Management

```cpp
UHierarchicalInstancedStaticMeshComponent* AcquireHISMComponent(const FString& FloraType)
{
    TArray<UHierarchicalInstancedStaticMeshComponent*>* Pool = HISMPool.Find(FloraType);
    
    if (!Pool)
    {
        // Create new pool
        HISMPool.Add(FloraType, TArray<UHierarchicalInstancedStaticMeshComponent*>());
        Pool = HISMPool.Find(FloraType);
        
        // Create initial pool components
        for (int32 i = 0; i < InitialPoolSize; i++)
        {
            UHierarchicalInstancedStaticMeshComponent* HISM = NewObject<UHierarchicalInstancedStaticMeshComponent>(this);
            Pool->Add(HISM);
        }
    }
    
    // Find available component
    for (auto* Component : *Pool)
    {
        if (Component && Component->GetInstanceCount() < MaxInstancesPerComponent)
        {
            return Component;
        }
    }
    
    // Create new if pool exhausted
    UHierarchicalInstancedStaticMeshComponent* NewHISM = NewObject<UHierarchicalInstancedStaticMeshComponent>(this);
    Pool->Add(NewHISM);
    return NewHISM;
}
```

---

## CHUNK-BASED STREAMING LOGIC

### World Partition Integration

```cpp
void SpawnFloraInChunk(UWorldPartitionCell* Cell)
{
    // Get biome for chunk
    UBiomeDataAsset* Biome = BiomeDetectionManager->DetectBiomeAtLocation(Cell->GetBounds().GetCenter());
    
    // Filter flora types for this biome
    TArray<FFloraType> SuitableFlora;
    for (auto& FloraType : FloraTypes)
    {
        if (FloraType.SuitableBiomes.Contains(Biome->BiomeID))
        {
            SuitableFlora.Add(FloraType);
        }
    }
    
    // Generate PCG distribution
    TArray<FTransform> SpawnTransforms = PCGGenerator->GenerateDistribution(Cell->GetBounds(), SuitableFlora);
    
    // Spawn instances
    for (auto& Transform : SpawnTransforms)
    {
        FFloraInstance Instance;
        Instance.TypeID = SelectFloraType(SuitableFlora);
        Instance.Transform = Transform;
        Instance.HISMComponent = AcquireHISMComponent(Instance.TypeID);
        Instance.SpawnTime = GetGameTime();
        
        // Add to HISM
        int32 InstanceIndex = Instance.HISMComponent->AddInstance(Transform);
        Instance.InstanceIndex = InstanceIndex;
        
        ActiveFlora[Cell].Add(Instance);
    }
}
```

### Load/Unload System

```cpp
void RemoveFloraFromChunk(UWorldPartitionCell* Cell)
{
    TArray<FFloraInstance>* Instances = ActiveFlora.Find(Cell);
    if (!Instances) return;
    
    // Remove all instances
    for (auto& Instance : *Instances)
    {
        Instance.HISMComponent->RemoveInstance(Instance.InstanceIndex);
        ReleaseHISMComponent(Instance.HISMComponent);
    }
    
    ActiveFlora.Remove(Cell);
}
```

---

## PCG GRAPHS FOR DISTRIBUTION

### PCG System Integration

```cpp
class UFloraPCGGenerator : public UObject
{
    GENERATED_BODY()

public:
    TArray<FTransform> GenerateDistribution(const FBox& Bounds, const TArray<FFloraType>& FloraTypes);

private:
    // Noise-based clustering
    FVector ComputeNoisePosition(const FVector& Position, float Scale);
    
    // Density variation
    float ComputeDensityMultiplier(const FVector& Position);
    
    // Avoidance zones
    bool IsPositionValid(const FVector& Position, const TArray<FVector>& ExistingPositions);
};

TArray<FTransform> GenerateDistribution(const FBox& Bounds, const TArray<FFloraType>& FloraTypes)
{
    TArray<FTransform> Transforms;
    
    for (auto& FloraType : FloraTypes)
    {
        // Calculate target count
        float Area = ComputeArea(Bounds);
        int32 TargetCount = FMath::FloorToInt((Area / 10000.0f) * FloraType.Density);
        
        // Generate positions
        for (int32 i = 0; i < TargetCount; i++)
        {
            FVector RandomPos = FMath::RandPointInBox(Bounds);
            
            // Apply noise clustering
            RandomPos = ComputeNoisePosition(RandomPos, 200.0f);
            
            // Check validity
            if (IsPositionValid(RandomPos, CollectPositions(Transforms)))
            {
                // Create transform with random rotation & scale
                FTransform Transform;
                Transform.SetLocation(RandomPos);
                Transform.SetRotation(FQuat::MakeFromEuler(FVector(0, 0, FMath::RandRange(0, 360))));
                Transform.SetScale3D(FVector(FMath::RandRange(0.8f, 1.2f)));
                
                Transforms.Add(Transform);
            }
        }
    }
    
    return Transforms;
}
```

---

## LOD SYSTEM

### Distance-Based Quality

```cpp
enum class EFloraLOD
{
    Full,        // 0-50m: Full detail mesh
    Medium,      // 50-200m: Reduced detail
    Low,         // 200-500m: Simplified mesh
    Billboard    // 500m+: Impostor billboard
};

class UFloraLODManager : public UObject
{
    GENERATED_BODY()

public:
    EFloraLOD GetLODForDistance(float Distance);
    void UpdateLODForInstances(TArray<FFloraInstance>& Instances, FVector PlayerLocation);

private:
    UPROPERTY()
    TMap<FString, TArray<UStaticMesh*>> LODMeshes;
};

void UpdateLODForInstances(TArray<FFloraInstance>& Instances, FVector PlayerLocation)
{
    for (auto& Instance : Instances)
    {
        float Distance = FVector::Dist(Instance.Transform.GetLocation(), PlayerLocation);
        EFloraLOD TargetLOD = GetLODForDistance(Distance);
        
        // Select appropriate mesh
        UStaticMesh* TargetMesh = GetLODMesh(Instance.TypeID, TargetLOD);
        
        if (TargetMesh != Instance.HISMComponent->GetStaticMesh())
        {
            Instance.HISMComponent->SetStaticMesh(TargetMesh);
        }
    }
}
```

---

## WIND ANIMATION INTEGRATION

### Wind Response System

```cpp
class UFloraWindController : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    UPROPERTY()
    UWeatherManager* WeatherManager;
    
    // Wind parameters from weather
    FVector WindDirection;
    float WindStrength;
    
    // Per-instance wind data
    struct FWindInstance
    {
        FVector PerlinOffset;
        float Phase;
        float Amplitude;
    };
    TMap<int32, FWindInstance> WindInstances;
};

void TickComponent(float DeltaTime)
{
    // Get wind data from WeatherManager
    WindDirection = WeatherManager->GetWindDirection();
    WindStrength = WeatherManager->GetWindStrength();
    
    // Apply wind to all flora instances
    for (auto& Pair : WindInstances)
    {
        int32 InstanceID = Pair.Key;
        FWindInstance& WindData = Pair.Value;
        
        // Compute wind offset using Perlin noise
        float Time = GetGameTime() + WindData.Phase;
        float WindX = FMath::PerlinNoise1D(Time * 0.5f) * WindStrength * WindData.Amplitude;
        float WindY = FMath::PerlinNoise1D(Time * 0.5f + 1000.0f) * WindStrength * WindData.Amplitude;
        
        FVector WindOffset = FVector(WindX, WindY, 0.0f);
        
        // Update instance transform
        UpdateInstancePosition(InstanceID, WindOffset);
    }
}
```

---

## SEASONAL APPEARANCE CHANGES

### Seasonal Material System

```cpp
class UFloraSeasonController : public UActorComponent
{
    GENERATED_BODY()

public:
    void UpdateSeasonalAppearance(ESeason Season);

private:
    UPROPERTY()
    TMap<FString, TMap<ESeason, UMaterialInstance*>> SeasonalMaterials;
    
    // Load seasonal materials
    void LoadSeasonalMaterials();
};

void UpdateSeasonalAppearance(ESeason Season)
{
    for (auto& FloraType : FloraTypes)
    {
        auto* SeasonalMap = SeasonalMaterials.Find(FloraType.TypeID);
        if (!SeasonalMap) continue;
        
        UMaterialInstance* SeasonMaterial = SeasonalMap->Find(Season);
        if (!SeasonMaterial) continue;
        
        // Apply to all HISM components of this type
        TArray<UHierarchicalInstancedStaticMeshComponent*>* Pool = HISMPool.Find(FloraType.TypeID);
        if (Pool)
        {
            for (auto* HISM : *Pool)
            {
                HISM->SetMaterial(0, SeasonMaterial);
            }
        }
    }
}

// Material mapping
void LoadSeasonalMaterials()
{
    // Example: Trees
    TMap<ESeason, UMaterialInstance*> TreeMaterials = {
        {ESeason::Spring, LoadObject<UMaterialInstance>("Trees_Spring")},
        {ESeason::Summer, LoadObject<UMaterialInstance>("Trees_Summer")},
        {ESeason::Fall, LoadObject<UMaterialInstance>("Trees_Fall")},
        {ESeason::Winter, LoadObject<UMaterialInstance>("Trees_Winter")}
    };
    SeasonalMaterials.Add("tree", TreeMaterials);
    
    // ... other flora types
}
```

---

## PERFORMANCE BUDGET

### Flora System Budget

**Target**: 2ms CPU, 4ms GPU per frame

**Breakdown**:
- HISM management: 0.5ms CPU
- Streaming: 0.5ms CPU
- LOD updates: 0.5ms CPU
- Wind calculation: 0.5ms CPU
- Seasonal updates: 0.0ms CPU (event-driven)

**Instancing**: Up to 10,000 instances per HISM component

---

## BLUEPRINT API

### Designer Functions

```cpp
// Flora management
UFUNCTION(BlueprintCallable, Category = "Flora")
void SpawnFloraInChunk(UWorldPartitionCell* Cell);

UFUNCTION(BlueprintCallable, Category = "Flora")
void RemoveFloraFromChunk(UWorldPartitionCell* Cell);

// Wind
UFUNCTION(BlueprintCallable, Category = "Flora")
void UpdateWindAnimation();

// Seasons
UFUNCTION(BlueprintCallable, Category = "Flora")
void UpdateSeasonalAppearance(ESeason Season);

// LOD
UFUNCTION(BlueprintCallable, Category = "Flora")
void UpdateLODForAllInstances();
```

---

**Status**: ✅ **FLORA MANAGEMENT SYSTEM ARCHITECTURE COMPLETE**



