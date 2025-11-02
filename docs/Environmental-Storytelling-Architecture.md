# Environmental Storytelling Architecture
**Date**: 2025-01-29  
**Task**: IM-002 - Environmental Storytelling  
**Status**: Design Complete

---

## OVERVIEW

Complete environmental storytelling system including detail actors, weather-reactive props, time-based object states, creature tracks, and designer placement tools.

---

## ENVIRONMENTAL DETAIL ACTOR SYSTEM

### Detail Actor Architecture

```cpp
UCLASS()
class AEnvironmentalDetailActor : public AActor
{
    GENERATED_BODY()

public:
    AEnvironmentalDetailActor();
    
    virtual void BeginPlay() override;

private:
    // Static mesh component
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
    class UStaticMeshComponent* DetailMesh;
    
    // Mesh variations
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Variation")
    TArray<UStaticMesh*> MeshVariations;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Variation")
    TArray<UMaterialInstance*> MaterialVariations;
    
    // Random scale range
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Variation")
    FVector2D ScaleRange;
    
    // Rotation variance
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Variation")
    bool bRandomRotation;
};

void BeginPlay()
{
    Super::BeginPlay();
    
    // Apply random variation
    if (MeshVariations.Num() > 0)
    {
        int32 RandomIndex = FMath::RandRange(0, MeshVariations.Num() - 1);
        DetailMesh->SetStaticMesh(MeshVariations[RandomIndex]);
    }
    
    // Apply random material
    if (MaterialVariations.Num() > 0)
    {
        int32 RandomIndex = FMath::RandRange(0, MaterialVariations.Num() - 1);
        DetailMesh->SetMaterial(0, MaterialVariations[RandomIndex]);
    }
    
    // Apply random scale
    float RandomScale = FMath::RandRange(ScaleRange.X, ScaleRange.Y);
    DetailMesh->SetWorldScale3D(FVector(RandomScale));
    
    // Apply random rotation
    if (bRandomRotation)
    {
        FRotator RandomRotation = FRotator(0, FMath::RandRange(0, 360), 0);
        DetailMesh->SetWorldRotation(RandomRotation);
    }
}
```

### Detail Placement System

```cpp
class UEnvironmentalDetailSpawner : public UObject
{
    GENERATED_BODY()

public:
    // Spawn detail actors in region
    UFUNCTION(BlueprintCallable, Category = "Detail")
    void SpawnDetailActors(const FBox& Region, int32 Count, TSubclassOf<AEnvironmentalDetailActor> ActorClass);

private:
    // Find placement location
    FVector FindPlacementLocation(const FBox& Region);
    
    // Check placement validity
    bool IsValidPlacementLocation(const FVector& Location);
};

void SpawnDetailActors(const FBox& Region, int32 Count, TSubclassOf<AEnvironmentalDetailActor> ActorClass)
{
    for (int32 i = 0; i < Count; i++)
    {
        // Find valid placement location
        FVector Location = FindPlacementLocation(Region);
        
        if (!IsValidPlacementLocation(Location)) continue;
        
        // Spawn actor
        AEnvironmentalDetailActor* DetailActor = GetWorld()->SpawnActor<AEnvironmentalDetailActor>(
            ActorClass,
            Location,
            FRotator::ZeroRotator
        );
        
        if (DetailActor)
        {
            DetailActor->BeginPlay();
        }
    }
}
```

---

## WEATHER-REACTIVE PROPS

### Reactive Prop Architecture

```cpp
UCLASS()
class AWeatherReactiveProp : public AActor
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;
    
    virtual void Tick(float DeltaTime) override;

private:
    // Static mesh
    UPROPERTY(VisibleAnywhere)
    UStaticMeshComponent* PropMesh;
    
    // Weather materials
    UPROPERTY(EditDefaultsOnly)
    TMap<EWeatherState, UMaterialInstance*> WeatherMaterials;
    
    // Weather manager reference
    UPROPERTY()
    class UWeatherManager* WeatherManager;
    
    // Current weather
    EWeatherState CurrentWeather;
    
    // Material blend
    void BlendToWeatherMaterial(EWeatherState TargetWeather, float BlendAlpha);
};

void Tick(float DeltaTime)
{
    if (!WeatherManager) return;
    
    EWeatherState NewWeather = WeatherManager->GetCurrentWeather();
    
    if (NewWeather != CurrentWeather)
    {
        // Transition to new weather material
        BlendToWeatherMaterial(NewWeather, 0.0f);
        CurrentWeather = NewWeather;
    }
}

void BlendToWeatherMaterial(EWeatherState TargetWeather, float BlendAlpha)
{
    UMaterialInstance* TargetMaterial = WeatherMaterials.Find(TargetWeather);
    if (!TargetMaterial) return;
    
    if (BlendAlpha <= 0.0f)
    {
        PropMesh->SetMaterial(0, TargetMaterial);
    }
    else
    {
        // Smooth transition over time
        // Implementation depends on material system
        UMaterialInstanceDynamic* DynamicMat = Cast<UMaterialInstanceDynamic>(PropMesh->GetMaterial(0));
        if (DynamicMat)
        {
            // Blend material parameters
            // Set blend alpha parameter
        }
    }
}
```

---

## TIME-BASED OBJECT STATES

### Object State System

```cpp
UCLASS()
class ATimeBasedObject : public AActor
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;
    
    virtual void Tick(float DeltaTime) override;

private:
    // Object states
    enum class EObjectState
    {
        Pristine,
        SlightlyWorn,
        Weathered,
        Dilapidated,
        Ruined
    };
    
    UPROPERTY(VisibleAnywhere)
    EObjectState CurrentState;
    
    // State thresholds (0.0 to 1.0)
    UPROPERTY(EditDefaultsOnly)
    float PristineThreshold;
    float SlightlyWornThreshold;
    float WeatheredThreshold;
    float DilapidatedThreshold;
    
    // Time manager reference
    UPROPERTY()
    class UTimeOfDayManager* TimeManager;
    
    // Time elapsed
    float TimeElapsed;
    
    // Update state
    void UpdateObjectState();
    
    // Apply state visuals
    void ApplyStateVisuals(EObjectState State);
};

void Tick(float DeltaTime)
{
    if (!TimeManager) return;
    
    // Accumulate time
    float GameDeltaTime = TimeManager->GetDeltaTime();
    TimeElapsed += GameDeltaTime;
    
    // Check state change
    UpdateObjectState();
}

void UpdateObjectState()
{
    // Normalize elapsed time (0.0 to 1.0)
    float NormalizedTime = FMath::Clamp(TimeElapsed / MaxAge, 0.0f, 1.0f);
    
    EObjectState NewState = CurrentState;
    
    if (NormalizedTime >= DilapidatedThreshold)
    {
        NewState = EObjectState::Ruined;
    }
    else if (NormalizedTime >= WeatheredThreshold)
    {
        NewState = EObjectState::Dilapidated;
    }
    else if (NormalizedTime >= SlightlyWornThreshold)
    {
        NewState = EObjectState::Weathered;
    }
    else if (NormalizedTime >= PristineThreshold)
    {
        NewState = EObjectState::SlightlyWorn;
    }
    
    if (NewState != CurrentState)
    {
        ApplyStateVisuals(NewState);
        CurrentState = NewState;
    }
}

void ApplyStateVisuals(EObjectState State)
{
    UMaterialInstance* StateMaterial = StateMaterials.Find(State);
    if (StateMaterial)
    {
        PropMesh->SetMaterial(0, StateMaterial);
    }
    
    // Additional visual effects
    if (State == EObjectState::Dilapidated)
    {
        // Add dust particle effect
        SpawnDustParticle();
    }
}
```

---

## CREATURE TRACKS & TRAILS

### Track System Architecture

```cpp
UCLASS()
class ACreatureTrack : public AActor
{
    GENERATED_BODY()

public:
    ACreatureTrack();
    
    virtual void BeginPlay() override;

private:
    // Spline component
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
    class USplineComponent* TrackSpline;
    
    // Decal component
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
    class UDecalComponent* TrackDecal;
    
    // Track age (affects fade)
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    float Age;
    
    // Max age before removal
    UPROPERTY(EditDefaultsOnly)
    float MaxAge;
};

void Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    
    // Age track
    Age += DeltaTime;
    
    // Update fade
    float FadeAlpha = FMath::Clamp(1.0f - (Age / MaxAge), 0.0f, 1.0f);
    UpdateDecalOpacity(FadeAlpha);
    
    // Remove if too old
    if (Age >= MaxAge)
    {
        Destroy();
    }
}
```

### Track Generator

```cpp
class UCreatureTrackGenerator : public UObject
{
    GENERATED_BODY()

public:
    // Generate track from creature movement
    UFUNCTION(BlueprintCallable, Category = "Tracks")
    ACreatureTrack* GenerateTrack(TArray<FVector> MovementPath, const FString& CreatureType);

private:
    // Track decals by creature type
    UPROPERTY()
    TMap<FString, UMaterialInterface*> TrackDecalMaterials;
    
    // Setup decal
    void SetupTrackDecal(ACreatureTrack* Track, const FString& CreatureType);
};

ACreatureTrack* GenerateTrack(TArray<FVector> MovementPath, const FString& CreatureType)
{
    if (MovementPath.Num() < 2) return nullptr;
    
    // Spawn track actor
    ACreatureTrack* Track = GetWorld()->SpawnActor<ACreatureTrack>();
    
    if (!Track) return nullptr;
    
    // Set up spline points
    for (const FVector& Point : MovementPath)
    {
        Track->TrackSpline->AddSplinePoint(Point, ESplineCoordinateSpace::World);
    }
    
    // Setup decal
    SetupTrackDecal(Track, CreatureType);
    
    return Track;
}
```

---

## PLACEMENT TOOLS

### Designer Tool Architecture

```cpp
UCLASS()
class AEnvironmentalPlacementTool : public AEditorUtilityActor
{
    GENERATED_BODY()

public:
    // Place detail actor
    UFUNCTION(CallInEditor, Category = "Placement")
    void PlaceDetailActor(TSubclassOf<AEnvironmentalDetailActor> ActorClass, const FVector& Location);
    
    // Generate random cluster
    UFUNCTION(CallInEditor, Category = "Placement")
    void GenerateRandomCluster(TSubclassOf<AEnvironmentalDetailActor> ActorClass, const FBox& Region, int32 Count);
    
    // Paint mode
    UFUNCTION(CallInEditor, Category = "Placement")
    void EnablePaintMode(TSubclassOf<AEnvironmentalDetailActor> ActorClass);
    
    UFUNCTION(CallInEditor, Category = "Placement")
    void DisablePaintMode();

private:
    // Paint mode active
    bool bPaintModeActive;
    
    // Current paint actor class
    TSubclassOf<AEnvironmentalDetailActor> PaintActorClass;
};

void GenerateRandomCluster(TSubclassOf<AEnvironmentalDetailActor> ActorClass, const FBox& Region, int32 Count)
{
    UEnvironmentalDetailSpawner* Spawner = NewObject<UEnvironmentalDetailSpawner>(this);
    Spawner->SpawnDetailActors(Region, Count, ActorClass);
}
```

---

## BLUEPRINT API

### Designer Functions

```cpp
// Detail placement
UFUNCTION(BlueprintCallable, Category = "Placement")
void PlaceDetailActor(TSubclassOf<AEnvironmentalDetailActor> ActorClass, const FVector& Location);

UFUNCTION(BlueprintCallable, Category = "Placement")
void GenerateRandomCluster(TSubclassOf<AEnvironmentalDetailActor> ActorClass, const FBox& Region, int32 Count);

// Track generation
UFUNCTION(BlueprintCallable, Category = "Tracks")
ACreatureTrack* GenerateTrack(TArray<FVector> MovementPath, const FString& CreatureType);
```

---

## PERFORMANCE BUDGET

### Storytelling System Budget

**Target**: 1.0ms CPU per frame

**Breakdown**:
- Detail actor updates: 0.3ms
- Weather-reactive props: 0.3ms
- Time-based objects: 0.2ms
- Track generation: 0.2ms

---

**Status**: ✅ **ENVIRONMENTAL STORYTELLING ARCHITECTURE COMPLETE**



