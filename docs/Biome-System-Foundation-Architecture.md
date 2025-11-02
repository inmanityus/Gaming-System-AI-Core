# Biome System Foundation Architecture
**Date**: 2025-01-29  
**Task**: TE-001 - Biome System Foundation  
**Status**: Design Complete

---

## OVERVIEW

Complete biome system foundation architecture for dynamic terrain ecosystems, biome detection, transitions, and World Partition integration.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **Weather System** (WS-001, WS-002)
   - Weather state management
   - Material parameters
   - Season tracking

2. **Unreal Engine 5**
   - World Partition (streaming)
   - PCG framework
   - Material systems

---

## BIOME DATA ASSET

### BiomeDataAsset Structure

```cpp
UCLASS()
class UBiomeDataAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FString BiomeID;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FText BiomeName;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Environment")
    float Temperature;          // -50 to 50 Celsius
    float Humidity;             // 0.0 to 1.0
    float Precipitation;        // mm/year
    float Windiness;            // 0.0 to 1.0
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
    UMaterialInterface* GroundMaterial;
    UMaterialInterface* WaterMaterial;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
    FLinearColor BaseAmbientColor;
    FLinearColor SkyColor;
    FLinearColor FogColor;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Audio")
    USoundBase* AmbientSound;
    float AmbientVolume;
};

// Predefined biomes
static TMap<FString, UBiomeDataAsset*> BiomeDefinitions = {
    {"urban", {
        .Temperature = 20.0f,
        .Humidity = 0.5f,
        .Precipitation = 800.0f
    }},
    {"forest", {
        .Temperature = 15.0f,
        .Humidity = 0.8f,
        .Precipitation = 1200.0f
    }},
    {"cemetery", {
        .Temperature = 10.0f,
        .Humidity = 0.7f,
        .Precipitation = 600.0f
    }}
};
```

---

## BIOME DETECTION SYSTEM

### Detection Manager

```cpp
UCLASS()
class UBiomeDetectionManager : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    // Detect biome at location
    UFUNCTION(BlueprintCallable, Category = "Biome")
    UBiomeDataAsset* DetectBiomeAtLocation(FVector Location);
    
    // Get current biome
    UFUNCTION(BlueprintCallable, Category = "Biome")
    UBiomeDataAsset* GetCurrentBiome() const;

private:
    UPROPERTY()
    UBiomeDataAsset* CurrentBiome;
    
    // Detection based on location tags
    UBiomeDataAsset* DetectByLocationTags(FVector Location);
};
```

### Detection Methods

**Location Tag Detection**:
```cpp
UBiomeDataAsset* DetectByLocationTags(FVector Location)
{
    // Query World Partition cells
    UWorldPartitionSubsystem* WP = GetWorld()->GetSubsystem<UWorldPartitionSubsystem>();
    
    // Check for biome tags in cell
    TArray<FString> Tags = WP->GetCellTagsAtLocation(Location);
    
    for (auto& Tag : Tags)
    {
        if (Tag.StartsWith("Biome_"))
        {
            FString BiomeID = Tag.Replace("Biome_", "");
            return BiomeRegistry->FindBiome(BiomeID);
        }
    }
    
    return DefaultBiome;
}
```

---

## BIOME TRANSITIONS

### Transition System

```cpp
struct FBiomeTransition
{
    UBiomeDataAsset* FromBiome;
    UBiomeDataAsset* ToBiome;
    float BlendAlpha;      // 0.0 to 1.0
    
    FLinearColor GetBlendedAmbientColor() const
    {
        return FMath::Lerp(FromBiome->BaseAmbientColor, ToBiome->BaseAmbientColor, BlendAlpha);
    }
    
    UMaterialInterface* GetBlendedGroundMaterial() const
    {
        if (BlendAlpha < 0.5f)
            return FromBiome->GroundMaterial;
        return ToBiome->GroundMaterial;
    }
};
```

**Smooth Transitions**:
```cpp
class UBiomeTransitionManager : public UActorComponent
{
    UPROPERTY()
    TArray<FBiomeTransition> ActiveTransitions;
    
    void UpdateTransition(FVector Location)
    {
        UBiomeDataAsset* DetectedBiome = DetectBiomeAtLocation(Location);
        
        // Start new transition
        if (CurrentBiome != DetectedBiome)
        {
            FBiomeTransition Transition;
            Transition.FromBiome = CurrentBiome;
            Transition.ToBiome = DetectedBiome;
            Transition.BlendAlpha = 0.0f;
            
            ActiveTransitions.Add(Transition);
        }
        
        // Update existing transitions
        for (auto& Transition : ActiveTransitions)
        {
            Transition.BlendAlpha += DeltaTime / TransitionDuration;
            
            if (Transition.BlendAlpha >= 1.0f)
            {
                CurrentBiome = Transition.ToBiome;
                ActiveTransitions.Remove(Transition);
            }
        }
    }
};
```

---

## BIOME REGISTRY

### Registry System

```cpp
UCLASS()
class UBiomeRegistry : public UObject
{
    GENERATED_BODY()

public:
    // Register biome
    UFUNCTION(BlueprintCallable, Category = "Biome Registry")
    void RegisterBiome(UBiomeDataAsset* Biome);
    
    // Find biome by ID
    UFUNCTION(BlueprintCallable, Category = "Biome Registry")
    UBiomeDataAsset* FindBiome(const FString& BiomeID);
    
    // Get all registered biomes
    UFUNCTION(BlueprintCallable, Category = "Biome Registry")
    TArray<UBiomeDataAsset*> GetAllBiomes();

private:
    UPROPERTY()
    TMap<FString, UBiomeDataAsset*> RegisteredBiomes;
};
```

**Runtime Loading**:
```cpp
void LoadBiomesFromAssets()
{
    // Load all biome data assets
    TArray<FString> BiomePaths = {
        "/Game/Biomes/Urban",
        "/Game/Biomes/Forest",
        "/Game/Biomes/Cemetery"
    };
    
    for (auto& Path : BiomePaths)
    {
        UBiomeDataAsset* Biome = LoadObject<UBiomeDataAsset>(nullptr, *Path);
        if (Biome)
        {
            RegisterBiome(Biome);
        }
    }
}
```

---

## WORLD PARTITION INTEGRATION

### Streaming Integration

```cpp
class UBiomeWorldPartitionIntegration : public UWorldPartitionSubsystem
{
    void OnCellLoaded(UWorldPartitionCell* Cell)
    {
        // Extract biome tags
        TArray<FString> BiomeTags = Cell->GetBiomeTags();
        
        if (BiomeTags.Num() > 0)
        {
            // Register cell with biome
            FString BiomeID = BiomeTags[0];
            UBiomeDataAsset* Biome = BiomeRegistry->FindBiome(BiomeID);
            
            if (Biome)
            {
                Cell->SetAssociatedBiome(Biome);
            }
        }
    }
    
    UBiomeDataAsset* QueryBiomeAtLocation(FVector Location)
    {
        // Query loaded cells at location
        TArray<UWorldPartitionCell*> Cells = GetLoadedCellsAtLocation(Location);
        
        for (auto* Cell : Cells)
        {
            UBiomeDataAsset* Biome = Cell->GetAssociatedBiome();
            if (Biome)
            {
                return Biome;
            }
        }
        
        return DefaultBiome;
    }
};
```

---

## BLUEPRINT API

### Designer Functions

```cpp
// Detection
UFUNCTION(BlueprintCallable, Category = "Biome")
UBiomeDataAsset* DetectBiomeAtLocation(FVector Location);

UFUNCTION(BlueprintCallable, Category = "Biome")
UBiomeDataAsset* GetCurrentBiome() const;

// Registry
UFUNCTION(BlueprintCallable, Category = "Biome")
void RegisterBiome(UBiomeDataAsset* Biome);

UFUNCTION(BlueprintCallable, Category = "Biome")
UBiomeDataAsset* FindBiome(const FString& BiomeID);

// Transitions
UFUNCTION(BlueprintCallable, Category = "Biome")
FBiomeTransition GetTransitionData() const;
```

---

## PERFORMANCE BUDGET

### Detection Budget

**Target**: 0.1ms per detection query

**Approach**:
- Cache biome per World Partition cell
- Query only on cell loads
- Minimal runtime overhead

---

**Status**: ✅ **BIOME SYSTEM FOUNDATION ARCHITECTURE COMPLETE**



