# Game Engine Service Solution
**Service**: Unreal Engine 5 Integration & Core Gameplay  
**Date**: January 29, 2025  
**Phase**: 2 - Solution Architecture

---

## SERVICE OVERVIEW

This service handles all Unreal Engine 5 client/server functionality, core gameplay mechanics, user interface, and game logic for "The Body Broker."

---

## ARCHITECTURE

### Technology Stack
- **Engine**: Unreal Engine 5.6+ (required for PCG Framework)
- **Languages**: C++ (core systems), Blueprints (gameplay scripts)
- **Platform**: Windows 10/11, Steam deployment
- **Networking**: Steam Online Subsystem, HTTP/gRPC API for AI integration
- **Optimization**: World Partition, LOD systems, async loading, material instancing ⭐ **NEW**

### Key Components

#### 1. Dual-World System (Day/Night)
```cpp
UCLASS()
class ABodyBrokerGameMode : public AGameModeBase
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite)
    bool bIsDayWorld = true;

    UFUNCTION(BlueprintCallable)
    void SwitchToNightWorld();

    UFUNCTION(BlueprintCallable)
    void SwitchToDayWorld();
};
```

**Implementation**:
- Global state flag (day/night)
- World switching with fade transitions
- Context-specific gameplay systems
- Lighting/shader adjustments

#### 2. AI Dialogue System Integration
```cpp
UCLASS()
class UDialogueManager : public UGameInstanceSubsystem
{
    GENERATED_BODY()

    void RequestNPCDialogue(
        ANPCCharacter* NPC,
        const FString& PlayerPrompt,
        const FDialogueResponseDelegate& Callback
    );

private:
    TSharedPtr<IHttpRequest> CreateInferenceRequest(
        const FString& ModelName,
        const FString& Prompt,
        const FDialogueContext& Context
    );
};
```

**HTTP Integration** (MVP - Non-Blocking):
```cpp
#include "Http.h"
#include "Async/Async.h"

// Non-blocking HTTP request on background thread
void UDialogueManager::RequestNPCDialogue_Async(
    ANPCCharacter* NPC,
    const FString& PlayerPrompt
) {
    AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask, [this, NPC, PlayerPrompt]() {
        TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
        
        Request->OnProcessRequestComplete().BindLambda([this, NPC](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful) {
            // Callback on game thread
            AsyncTask(ENamedThreads::GameThread, [this, NPC, Response]() {
                if (bWasSuccessful && Response.IsValid()) {
                    FString JsonString = Response->GetContentAsString();
                    // Parse and display dialogue
                    OnDialogueReceived(NPC, JsonString);
                } else {
                    // Fallback to cached response
                    OnDialogueReceived(NPC, GetCachedDialogue(NPC));
                }
            });
        });
        
        Request->SetURL(TEXT("https://ai-inference:8000/v1/dialogue"));
        Request->SetVerb(TEXT("POST"));
        Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
        
        // Build JSON body
        TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
        JsonObject->SetStringField(TEXT("npc_id"), NPC->GetNPCID());
        JsonObject->SetStringField(TEXT("prompt"), PlayerPrompt);
        
        FString OutputString;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
        FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
        Request->SetContentAsString(OutputString);
        
        Request->ProcessRequest();
    });
}
```

**gRPC Integration** (Production - Streaming Support):
```cpp
// gRPC-Web via TurboLink or custom plugin
// Streaming dialogue responses
void UDialogueManager::RequestNPCDialogue_Streaming(
    ANPCCharacter* NPC,
    const FString& PlayerPrompt
) {
    // Create gRPC client with connection pooling
    auto Client = MakeShared<FGrpcDialogueClient>();
    
    // Stream response (token-by-token)
    Client->StreamDialogue(PlayerPrompt, [NPC](const FString& Token) {
        // Update UI incrementally as tokens arrive
        AsyncTask(ENamedThreads::GameThread, [NPC, Token]() {
            NPC->UpdateDialogueText(Token);
        });
    });
}
```

#### 3. Settings System
```cpp
UCLASS(Config=Game)
class UGameSettings : public USaveGame
{
    GENERATED_BODY()

    // Audio
    UPROPERTY(Config)
    float MasterVolume = 1.0f;

    UPROPERTY(Config)
    float MusicVolume = 0.8f;

    // Video
    UPROPERTY(Config)
    int32 ResolutionX = 1920;

    UPROPERTY(Config)
    int32 ResolutionY = 1080;

    UPROPERTY(Config)
    int32 QualityPreset = 2; // Medium

    // Controls
    UPROPERTY(Config)
    float MouseSensitivity = 1.0f;

    UFUNCTION(BlueprintCallable)
    void SaveSettings();

    UFUNCTION(BlueprintCallable)
    void LoadSettings();
};
```

**UI Implementation**:
- Settings widget (UMG)
- Real-time preview
- Persistent storage (config files)
- Steam Cloud sync (optional)

#### 4. Helpful Indicators System
```cpp
UCLASS()
class AHelpfulIndicatorManager : public AActor
{
    GENERATED_BODY()

    UFUNCTION(BlueprintCallable)
    void ShowIndicatorForActor(AActor* TargetActor);

    UFUNCTION(BlueprintCallable)
    void HideIndicator(AActor* TargetActor);

    // Subtle visual effects
    UPROPERTY(EditDefaultsOnly)
    UParticleSystem* SubtleGlowEffect;

    UPROPERTY(EditDefaultsOnly)
    UMaterialParameterCollection* EdgeGlowParams;
};
```

**Design Principles**:
- NO massive arrows
- Subtle edge glows
- Screen-edge indicators for off-screen objects
- Contextual minion NPC for complex actions
- Smooth fade in/out

---

## INTEGRATION WITH AI INFERENCE SERVICE

### API Contract

**Request Format**:
```cpp
struct FDialogueRequest
{
    FString NPCID;
    FString PlayerMessage;
    FDialogueContext Context; // Relationship, recent events, etc.
    int32 Tier = 3; // NPC tier for model selection
};
```

**Response Format**:
```cpp
struct FDialogueResponse
{
    FString ResponseText;
    TArray<FString> AvailableActions; // Tool-calling outputs
    float Confidence = 1.0f;
    bool bStreaming = false;
};
```

**Endpoints**:
- MVP: `POST http://inference-server:8000/v1/dialogue`
- Production: `gRPC DialogueService.GenerateDialogue`

---

## CORE GAMEPLAY SYSTEMS

### 1. Acquisition System (Day World)
- Morgue robbery mechanics
- Player combat system
- Cop avoidance/stealth
- Inventory management
- Lab equipment interaction

### 2. Processing System
- Lab equipment UI
- Body part processing
- Ingredient mixing for monster types
- Upgrade paths

### 3. Selling System (Night World)
- NPC interaction system
- Transaction mechanics
- Reputation/faction tracking
- Customer tier progression

### 4. Progression System
- Empire building (labs, morgues)
- Supernatural power acquisition
- House politics integration
- Player progression tracking

---

## PERFORMANCE REQUIREMENTS

### Target Metrics
- **Frame Rate**: 60fps at 1080p Medium (mid-range PC)
- **AI Latency**: <200ms for Tier 3 dialogue (perceived)
- **Loading**: <3 seconds for world transitions
- **Memory**: <8GB RAM usage

### Optimization Strategies (Enhanced - Based on Research) ⭐ **UPDATED**

#### LOD Systems (Critical)
```cpp
// Always use 2-4 LOD levels per mesh
USTRUCT()
struct FLODSettings
{
    UPROPERTY(EditAnywhere)
    float LOD0_Distance = 1000.0f;  // Full detail
    
    UPROPERTY(EditAnywhere)
    float LOD1_Distance = 2000.0f;  // Reduced polys
    
    UPROPERTY(EditAnywhere)
    float LOD2_Distance = 5000.0f;   // Minimal polys
    
    // Target: <10,000 polygons per player/asset
    UPROPERTY(EditAnywhere)
    int32 MaxPolygons_LOD0 = 10000;
    int32 MaxPolygons_LOD1 = 5000;
    int32 MaxPolygons_LOD2 = 2000;
};

// Hierarchical LOD (HLOD) for environment
void BuildHLODForLevel()
{
    // Combine meshes for distance rendering
    // Reduces draw calls from 1000+ to <100
}
```

**Performance Target**: <700 draw calls (high-end), <500 (mid-range)

#### Material Optimization
```cpp
// Use Material Instances (not unique materials)
// Reduce instruction counts (<200 instructions target)

// Material instance example
UMaterialInstanceDynamic* CreateDynamicMaterial()
{
    UMaterialInstanceDynamic* MaterialInstance = UMaterialInstanceDynamic::Create(
        BaseMaterial,
        this
    );
    
    // Set parameters without creating new material
    MaterialInstance->SetScalarParameterValue(TEXT("Roughness"), 0.5f);
    MaterialInstance->SetVectorParameterValue(TEXT("BaseColor"), FLinearColor::Red);
    
    return MaterialInstance;
}

// Vertex color masking for procedural materials
// More efficient than texture masking
```

#### Texture Optimization
```cpp
// Use Virtual Texturing for large textures
void ConfigureVirtualTexturing()
{
    // Enable in Project Settings
    // Use mipmap debug texture to determine optimal resolution
    // Compress textures appropriately (BC compression)
}

// Texture streaming
void SetupTextureStreaming()
{
    // Stream off-screen assets
    // Use texture groups for memory management
}
```

#### Lighting & Shadows
```cpp
// Use Virtual Shadow Maps with Nanite
void ConfigureShadows()
{
    // For high-poly scenes: Virtual Shadow Maps
    // For low-poly: Traditional shadow maps
    // Adjust shadow distance based on performance budget
    // Disable shadows on dynamic actors where possible
}

// Light optimization
void OptimizeLights()
{
    // Set proper attenuation radius
    // Avoid overlapping light radii
    // Use Light Functions sparingly
}
```

#### World Partition & Async Loading ⭐ **NEW**
```cpp
// Enable World Partition for large levels
// Stream chunks based on player location

#include "WorldPartition/WorldPartition.h"
#include "Engine/StreamableManager.h"

void LoadLevelChunkAsync(const FVector& PlayerLocation)
{
    FStreamableManager StreamableManager;
    
    // Load chunk containing player location
    TSoftObjectPtr<UWorld> ChunkToLoad = GetChunkForLocation(PlayerLocation);
    
    StreamableManager.RequestAsyncLoad(
        ChunkToLoad.ToSoftObjectPath(),
        FStreamableDelegate::CreateLambda([this]() {
            OnChunkLoaded();
        })
    );
}

// Async asset loading (AI models, NPCs)
void LoadAIAssetsAsync()
{
    AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask, [this]() {
        // Load AI context, models, NPCs
        // Update game thread when complete
        AsyncTask(ENamedThreads::GameThread, [this]() {
            OnAIAssetsLoaded();
        });
    });
}
```

#### Draw Call Reduction
```cpp
// Combine meshes using HLOD
void CombineMeshes()
{
    // Manually combine in DCC tool
    // Or use UE5 HLOD generation
}

// Instanced Static Meshes for repeated objects
UInstancedStaticMeshComponent* CreateInstancedMesh(UStaticMesh* Mesh)
{
    UInstancedStaticMeshComponent* InstancedMesh = NewObject<UInstancedStaticMeshComponent>(this);
    InstancedMesh->SetStaticMesh(Mesh);
    InstancedMesh->SetFlags(RF_Transactional);
    
    // Add multiple instances with transforms
    for (int32 i = 0; i < Count; i++)
    {
        InstancedMesh->AddInstance(FTransform(Location));
    }
    
    return InstancedMesh;
}
```

#### Profiling & Debugging ⭐ **NEW**
```cpp
// Use Unreal Insights for profiling
// Console commands for performance stats:
// - stat unit (CPU/GPU times)
// - stat fps (Frame rate)
// - stat gpu (GPU breakdown)
// - stat net (Network stats)
// - stat rhi (Draw calls)

// Performance monitoring
void CheckPerformance()
{
    if (FPlatformMisc::GetFrameCount() % 300 == 0)  // Every 5 seconds at 60fps
    {
        float AvgFrameTime = FPlatformTime::GetAverageFrameTime();
        float AvgFPS = 1.0f / AvgFrameTime;
        
        if (AvgFPS < 55.0f)  // Below 60fps threshold
        {
            UE_LOG(LogGame, Warning, TEXT("Performance below target: %f FPS"), AvgFPS);
            // Trigger optimization routines
        }
    }
}
```

#### Package Size & Boot Time Optimization ⭐ **NEW**
```ini
; DefaultEngine.ini
[/Script/Engine.StreamingSettings]
s.PriorityAsyncLoadingExtraTime=275.0
s.LevelStreamingActorsUpdateTimeLimit=250.0
s.PriorityLevelStreamingActorsUpdateExtraTime=250.0

[/Script/UnrealEd.ProjectPackagingSettings]
bCompressed=False
BuildConfiguration=PPBC_Development
bShareMaterialShaderCode=True
bSharedMaterialNativeLibraries=True
bSkipEditorContent=True
```

#### Network Optimization
```cpp
// Monitor network usage
void MonitorNetwork()
{
    // Use 'stat net' command output
    // Batch network updates
    // Compress network data
    // Use relevance/interest systems
}

// Server-authoritative for critical logic
void UpdateServerState()
{
    // Server controls core game logic
    // Clients predict for responsiveness
    // Server corrects if needed
}
```

#### Cached Dialogue Responses ⭐ **NEW**
```cpp
// Client-side cache for common NPC responses
UPROPERTY()
TMap<FString, FDialogueResponse> DialogueCache;

FDialogueResponse* GetCachedDialogue(const FString& NPCID, const FString& Prompt)
{
    FString CacheKey = FString::Printf(TEXT("%s_%s"), *NPCID, *Prompt);
    
    // Check cache (5 minute TTL)
    if (DialogueCache.Contains(CacheKey))
    {
        FDialogueResponse* Cached = DialogueCache.Find(CacheKey);
        if (Cached->CacheTime > FDateTime::Now() - FTimespan(0, 0, 5, 0))
        {
            return Cached;
        }
    }
    
    return nullptr;
}
```

#### Predictive Content Loading ⭐ **NEW**
```cpp
// Pre-generate likely NPC responses based on player history
void PreloadLikelyResponses(APlayerController* Player)
{
    // Analyze player behavior
    TArray<FString> LikelyPrompts = PredictPlayerPrompts(Player);
    
    // Pre-generate responses
    for (const FString& Prompt : LikelyPrompts)
    {
        PreloadDialogueResponse(Prompt);
    }
}
```

---

## DEPLOYMENT

### Steam Integration
- Steam SDK integration
- Achievement system
- Workshop support (optional, future)
- Steam Cloud save (optional)

### Build Configuration
- Development builds (with debug tools)
- Shipping builds (optimized)
- Steam deployment pipeline
- Auto-update system

---

## SECURITY & SAFETY

### Content Moderation
- Client-side input sanitization
- Response validation
- Rating enforcement (M-rated)
- Player reporting system

---

## NEXT: Integration with Orchestration Service

See `ORCHESTRATION-SERVICE.md` for how game requests are routed through the hierarchical pipeline.

