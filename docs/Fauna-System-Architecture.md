# Fauna System Architecture
**Date**: 2025-01-29  
**Task**: TE-003 - Fauna System  
**Status**: Design Complete

---

## OVERVIEW

Complete fauna system architecture with population management, behavior trees, flocking, predator-prey interactions, and time/weather response systems.

---

## SYSTEM INTEGRATION

### Existing Systems

1. **Biome System** (TE-001)
   - Biome detection
   - Environment parameters

2. **Time Manager** (DN-001)
   - Time-of-day progression
   - Day/night cycles

3. **Weather System** (WS-001)
   - Weather state
   - Season tracking

4. **Unreal Engine 5**
   - Behavior Tree framework
   - AI Perception system
   - Navigation system

---

## FAUNA SPAWNER & POPULATION MANAGEMENT

### FaunaSpawner Architecture

```cpp
UCLASS()
class AFaunaSpawner : public AActor
{
    GENERATED_BODY()

public:
    // Initialize fauna system
    UFUNCTION(BlueprintCallable, Category = "Fauna")
    void InitializeFaunaSystem();
    
    // Spawn fauna in region
    UFUNCTION(BlueprintCallable, Category = "Fauna")
    void SpawnFaunaInRegion(const FBox& Region);
    
    // Update population management
    UFUNCTION(BlueprintCallable, Category = "Fauna")
    void UpdatePopulationManagement();

private:
    // Population tracking
    UPROPERTY()
    TMap<FString, int32> CurrentPopulations;
    
    // Population limits per biome
    UPROPERTY()
    TMap<FString, int32> PopulationLimits;
    
    // Spawned creatures
    UPROPERTY()
    TArray<AFloraCreature*> ActiveCreatures;
    
    // Spawn logic
    void SpawnCreature(FFaunaType Type, FVector Location);
    void DespawnCreature(AFloraCreature* Creature);
    
    // Population validation
    bool IsPopulationAtLimit(const FString& CreatureType, UBiomeDataAsset* Biome);
};
```

### Fauna Data Structure

```cpp
USTRUCT(BlueprintType)
struct FFaunaType
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly)
    FString TypeID;
    
    UPROPERTY(EditDefaultsOnly)
    TSubclassOf<AFloraCreature> CreatureClass;
    
    // Population
    UPROPERTY(EditDefaultsOnly)
    int32 MaxPopulationPerBiome;
    
    UPROPERTY(EditDefaultsOnly)
    float SpawnRate;  // Per hour
    
    // Biome suitability
    UPROPERTY(EditDefaultsOnly)
    TArray<FString> SuitableBiomes;
    
    // Grouping
    UPROPERTY(EditDefaultsOnly)
    int32 MinGroupSize;
    
    UPROPERTY(EditDefaultsOnly)
    int32 MaxGroupSize;
    
    // Diet
    UPROPERTY(EditDefaultsOnly)
    EFaunaDiet Diet;
    
    // Predator/Prey relationships
    UPROPERTY(EditDefaultsOnly)
    TArray<FString> PreyTypes;
    
    UPROPERTY(EditDefaultsOnly)
    TArray<FString> PredatorTypes;
};

enum class EFaunaDiet
{
    Herbivore,
    Carnivore,
    Omnivore
};
```

### Population Management

```cpp
void UpdatePopulationManagement()
{
    // Count current populations
    for (auto& Creature : ActiveCreatures)
    {
        if (Creature && IsValid(Creature))
        {
            FString TypeID = Creature->GetTypeID();
            CurrentPopulations.FindOrAdd(TypeID, 0)++;
        }
    }
    
    // Clean up invalid creatures
    ActiveCreatures.RemoveAll([](AFloraCreature* Creature)
    {
        return !IsValid(Creature);
    });
    
    // Check for new spawns
    for (auto& FloraType : FaunaTypes)
    {
        int32 CurrentCount = CurrentPopulations.FindRef(FloraType.TypeID);
        int32 Limit = FloraType.MaxPopulationPerBiome;
        
        if (CurrentCount < Limit)
        {
            // Calculate spawn probability
            float TimeDelta = GetGameDeltaTime();
            float SpawnChance = FloraType.SpawnRate * (TimeDelta / 3600.0f);
            
            if (FMath::RandRange(0.0f, 1.0f) < SpawnChance)
            {
                SpawnFaunaGroup(FloraType);
            }
        }
    }
}

void SpawnFaunaGroup(const FFaunaType& Type)
{
    // Determine group size
    int32 GroupSize = FMath::RandRange(Type.MinGroupSize, Type.MaxGroupSize);
    
    // Find spawn location
    FVector SpawnLocation = FindSpawnLocation(Type);
    
    // Spawn group members
    for (int32 i = 0; i < GroupSize; i++)
    {
        // Offset position for group clustering
        FVector Offset = FMath::VRand() * FMath::RandRange(50.0f, 200.0f);
        FVector Location = SpawnLocation + Offset;
        
        SpawnCreature(Type, Location);
    }
}
```

---

## CREATURE AI BEHAVIOR TREES

### Behavior Tree Architecture

```cpp
UCLASS()
class AFaunaCreature : public APawn
{
    GENERATED_BODY()

public:
    // Behavior system
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "AI")
    class UBehaviorTreeComponent* BehaviorTree;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "AI")
    class UBlackboardComponent* Blackboard;
    
    // Initialize AI
    virtual void BeginPlay() override;

private:
    // Behavior tree asset
    UPROPERTY(EditDefaultsOnly, Category = "AI")
    class UBehaviorTree* BehaviorTreeAsset;
    
    // Blackboard asset
    UPROPERTY(EditDefaultsOnly, Category = "AI")
    class UBlackboardData* BlackboardAsset;
};

void BeginPlay()
{
    Super::BeginPlay();
    
    // Initialize blackboard
    if (BlackboardAsset)
    {
        Blackboard->InitializeBlackboard(*BlackboardAsset);
    }
    
    // Start behavior tree
    if (BehaviorTreeAsset && BehaviorTree)
    {
        BehaviorTree->StartTree(*BehaviorTreeAsset);
    }
}
```

### Behavior States

```cpp
enum class ECreatureState
{
    Idle,           // Resting, grazing
    Wandering,      // Random movement
    Feeding,        // Eating behavior
    Fleeing,        // Escape from predator
    Hunting,        // Pursue prey
    Socializing,    // Group interactions
    Sleeping,       // Nighttime rest
    SeekingShelter  // Weather response
};

enum class ECreatureActivity
{
    Active,         // Full activity
    Moderate,       // Reduced activity
    Inactive,       // Minimal activity
    Sleeping        // Nocturnal sleep
};
```

### Decision Making

```cpp
class UCreatureDecisionManager : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    // Current state
    UPROPERTY()
    ECreatureState CurrentState;
    
    // Decision factors
    struct FDecisionFactors
    {
        float Hunger;
        float Thirst;
        float Fatigue;
        float Fear;
        float Social;
        float Health;
    };
    FDecisionFactors Factors;
    
    // Evaluate decisions
    ECreatureState EvaluateNextState();
    void UpdateFactors(float DeltaTime);
};

ECreatureState EvaluateNextState()
{
    // Check for threats
    if (IsThreatDetected())
    {
        return ECreatureState::Fleeing;
    }
    
    // Check for prey (if carnivore)
    if (Diet == EFaunaDiet::Carnivore && IsPreyDetected())
    {
        if (Factors.Hunger > 0.5f)
        {
            return ECreatureState::Hunting;
        }
    }
    
    // Check hunger
    if (Factors.Hunger > 0.7f && HasFoodNearby())
    {
        return ECreatureState::Feeding;
    }
    
    // Check fatigue
    if (Factors.Fatigue > 0.8f)
    {
        if (ShouldSleep())
        {
            return ECreatureState::Sleeping;
        }
    }
    
    // Default behavior
    if (FMath::RandBool())
    {
        return ECreatureState::Wandering;
    }
    else
    {
        return ECreatureState::Idle;
    }
}
```

---

## FLOCKING & BEHAVIOR SYSTEMS

### Flocking Algorithm

```cpp
class UFlockingBehavior : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    // Flocking parameters
    UPROPERTY(EditDefaultsOnly)
    float SeparationRadius;
    
    UPROPERTY(EditDefaultsOnly)
    float AlignmentRadius;
    
    UPROPERTY(EditDefaultsOnly)
    float CohesionRadius;
    
    UPROPERTY(EditDefaultsOnly)
    float SeparationWeight;
    
    UPROPERTY(EditDefaultsOnly)
    float AlignmentWeight;
    
    UPROPERTY(EditDefaultsOnly)
    float CohesionWeight;
    
    // Get nearby flock members
    TArray<AFaunaCreature*> GetNearbyFlockMembers();
    
    // Compute flocking force
    FVector ComputeFlockingForce();
};

FVector ComputeFlockingForce()
{
    FVector Separation = FVector::ZeroVector;
    FVector Alignment = FVector::ZeroVector;
    FVector Cohesion = FVector::ZeroVector;
    
    TArray<AFaunaCreature*> NearbyMembers = GetNearbyFlockMembers();
    int32 Count = 0;
    
    FVector CenterOfMass = FVector::ZeroVector;
    
    for (auto* Member : NearbyMembers)
    {
        float Distance = FVector::Dist(GetOwner()->GetActorLocation(), Member->GetActorLocation());
        
        // Separation: avoid too close neighbors
        if (Distance < SeparationRadius)
        {
            FVector Offset = GetOwner()->GetActorLocation() - Member->GetActorLocation();
            Separation += Offset.GetSafeNormal() / (Distance + 0.1f);
        }
        
        // Alignment: match velocity
        if (Distance < AlignmentRadius)
        {
            Alignment += Member->GetVelocity();
        }
        
        // Cohesion: move toward center
        if (Distance < CohesionRadius)
        {
            CenterOfMass += Member->GetActorLocation();
            Count++;
        }
    }
    
    // Normalize
    if (NearbyMembers.Num() > 0)
    {
        Separation.Normalize();
        Alignment.Normalize();
        
        if (Count > 0)
        {
            CenterOfMass /= Count;
            Cohesion = (CenterOfMass - GetOwner()->GetActorLocation()).GetSafeNormal();
        }
    }
    
    // Combine forces
    FVector FlockingForce = (Separation * SeparationWeight) +
                           (Alignment * AlignmentWeight) +
                           (Cohesion * CohesionWeight);
    
    return FlockingForce.GetSafeNormal();
}
```

### Predator-Prey Interactions

```cpp
class UPredatorBehavior : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    // Hunt prey
    void HuntPrey(AFaunaCreature* Prey);
    
    // Chase behavior
    void ChaseTarget(AFaunaCreature* Target);
    
    // Attack behavior
    void AttackPrey(AFaunaCreature* Prey);
    
    // Current hunt target
    UPROPERTY()
    AFloraCreature* HuntTarget;
};

void TickComponent(float DeltaTime)
{
    if (!HuntTarget || !IsValid(HuntTarget))
    {
        // Look for prey
        TArray<AFaunaCreature*> NearbyCreatures = GetNearbyCreatures();
        
        for (auto* Creature : NearbyCreatures)
        {
            if (IsValidPrey(Creature))
            {
                HuntTarget = Creature;
                ChaseTarget(Creature);
                break;
            }
        }
    }
    else
    {
        // Continue chase or attack
        float Distance = FVector::Dist(GetOwner()->GetActorLocation(), HuntTarget->GetActorLocation());
        
        if (Distance < AttackRange)
        {
            AttackPrey(HuntTarget);
        }
        else
        {
            ChaseTarget(HuntTarget);
        }
    }
}
```

---

## TIME & WEATHER RESPONSE

### Time-of-Day Activity Patterns

```cpp
class UTimeActivityPattern : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;

private:
    // Time manager reference
    UPROPERTY()
    UTimeOfDayManager* TimeManager;
    
    // Activity pattern
    UPROPERTY(EditDefaultsOnly)
    TMap<ETimeOfDay, ECreatureActivity> ActivityPattern;
    
    // Update activity based on time
    void UpdateActivityFromTime();
};

void UpdateActivityFromTime()
{
    if (!TimeManager) return;
    
    ETimeOfDay TimeOfDay = TimeManager->GetCurrentTimeOfDay();
    ECreatureActivity* Activity = ActivityPattern.Find(TimeOfDay);
    
    if (Activity)
    {
        AFloraCreature* Creature = Cast<AFloraCreature>(GetOwner());
        if (Creature)
        {
            Creature->SetActivityLevel(*Activity);
        }
    }
}

// Example patterns
void InitializeActivityPatterns()
{
    // Diurnal animals (active during day)
    ActivityPattern.Add(ETimeOfDay::Dawn, ECreatureActivity::Moderate);
    ActivityPattern.Add(ETimeOfDay::Day, ECreatureActivity::Active);
    ActivityPattern.Add(ETimeOfDay::Dusk, ECreatureActivity::Moderate);
    ActivityPattern.Add(ETimeOfDay::Night, ECreatureActivity::Sleeping);
    
    // Nocturnal animals (active during night)
    ActivityPattern.Add(ETimeOfDay::Dawn, ECreatureActivity::Sleeping);
    ActivityPattern.Add(ETimeOfDay::Day, ECreatureActivity::Sleeping);
    ActivityPattern.Add(ETimeOfDay::Dusk, ECreatureActivity::Moderate);
    ActivityPattern.Add(ETimeOfDay::Night, ECreatureActivity::Active);
}
```

### Weather Response

```cpp
class UWeatherResponse : public UActorComponent
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;

private:
    // Weather manager reference
    UPROPERTY()
    UWeatherManager* WeatherManager;
    
    // Weather response behaviors
    UPROPERTY(EditDefaultsOnly)
    TMap<EWeatherState, ECreatureBehavior> WeatherResponses;
    
    // Update behavior based on weather
    void UpdateBehaviorFromWeather();
};

void UpdateBehaviorFromWeather()
{
    if (!WeatherManager) return;
    
    EWeatherState Weather = WeatherManager->GetCurrentWeather();
    ECreatureBehavior* Behavior = WeatherResponses.Find(Weather);
    
    if (Behavior)
    {
        AFloraCreature* Creature = Cast<AFloraCreature>(GetOwner());
        if (Creature)
        {
            Creature->SetBehavior(*Behavior);
        }
    }
}

// Example responses
void InitializeWeatherResponses()
{
    // Seek shelter in rain
    WeatherResponses.Add(EWeatherState::LightRain, ECreatureBehavior::SeekShelter);
    WeatherResponses.Add(EWeatherState::HeavyRain, ECreatureBehavior::SeekShelter);
    
    // Hide during storms
    WeatherResponses.Add(EWeatherState::Thunderstorm, ECreatureBehavior::SeekShelter);
    
    // Reduce activity in extreme heat
    WeatherResponses.Add(EWeatherState::Heatwave, ECreatureBehavior::ReduceActivity);
}
```

---

## PERFORMANCE BUDGET

### Fauna System Budget

**Target**: 3ms CPU per frame

**Breakdown**:
- Population management: 0.5ms
- Behavior tree updates: 1.0ms
- Flocking calculations: 1.0ms
- AI perception: 0.5ms

**Limits**:
- 50 active creatures per biome
- 5 flocks max simultaneously
- 10 predators active

---

## BLUEPRINT API

### Designer Functions

```cpp
// Spawning
UFUNCTION(BlueprintCallable, Category = "Fauna")
void SpawnFaunaInRegion(const FBox& Region);

UFUNCTION(BlueprintCallable, Category = "Fauna")
void UpdatePopulationManagement();

// Behavior
UFUNCTION(BlueprintCallable, Category = "Fauna")
void SetCreatureActivityLevel(ECreatureActivity Activity);

UFUNCTION(BlueprintCallable, Category = "Fauna")
void SetCreatureBehavior(ECreatureBehavior Behavior);
```

---

**Status**: ✅ **FAUNA SYSTEM ARCHITECTURE COMPLETE**



