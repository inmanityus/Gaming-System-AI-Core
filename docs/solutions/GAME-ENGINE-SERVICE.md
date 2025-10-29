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
- **Networking**: Steam Online Subsystem, HTTP API for AI integration

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

**HTTP Integration** (MVP):
- Uses UE5 HTTP Module (`HttpModule.h`)
- REST API calls to inference servers
- Async callbacks for responses
- Error handling & fallbacks

**gRPC Integration** (Production):
- TurboLink plugin for gRPC
- Binary protocol for performance
- Streaming support for dialogue

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

### Optimization Strategies
- Nanite for geometry
- Lumen for lighting (with quality presets)
- Aggressive LOD for NPCs
- Cached dialogue responses
- Predictive content loading

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

