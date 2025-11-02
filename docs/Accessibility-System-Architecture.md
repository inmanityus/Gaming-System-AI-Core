# Accessibility System Architecture
**Date**: 2025-01-29  
**Task**: IM-003 - Accessibility Features  
**Status**: Design Complete

---

## OVERVIEW

Complete accessibility system including enhanced subtitles, color-blind shaders, alternative audio cues, and automatic performance scaling for inclusive gaming experience.

---

## ENHANCED SUBTITLE SYSTEM

### Subtitle Architecture

```cpp
UCLASS()
class USubtitleManager : public UObject
{
    GENERATED_BODY()

public:
    // Display subtitle
    UFUNCTION(BlueprintCallable, Category = "Subtitles")
    void ShowSubtitle(const FString& Text, float Duration = 5.0f);
    
    // Customize subtitle appearance
    UFUNCTION(BlueprintCallable, Category = "Subtitles")
    void SetSubtitleCustomization(const FSubtitleSettings& Settings);

private:
    // Subtitle widget reference
    UPROPERTY()
    class USubtitleWidget* SubtitleWidget;
    
    // Current settings
    UPROPERTY()
    FSubtitleSettings CurrentSettings;
};

USTRUCT(BlueprintType)
struct FSubtitleSettings
{
    GENERATED_BODY()

    // Appearance
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float FontSize;  // 0.5x to 2.0x
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FColor TextColor;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FColor BackgroundColor;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float BackgroundOpacity;
    
    // Position
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    ESubtitlePosition Position;  // Bottom, Middle, Top
    
    // Options
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bShowSpeakerName;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bShowBackground;
    
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bShowOutline;
};

enum class ESubtitlePosition
{
    Bottom,
    BottomMiddle,
    Middle,
    TopMiddle,
    Top
};

void ShowSubtitle(const FString& Text, float Duration)
{
    if (SubtitleWidget)
    {
        SubtitleWidget->DisplaySubtitle(Text, Duration, CurrentSettings);
    }
}
```

### Subtitle Widget

```cpp
UCLASS()
class USubtitleWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    void DisplaySubtitle(const FString& Text, float Duration, const FSubtitleSettings& Settings);

private:
    // UI bindings
    UPROPERTY(meta = (BindWidget))
    class UTextBlock* TextBlock_Subtitle;
    
    UPROPERTY(meta = (BindWidget))
    class UBorder* Border_Background;
    
    // Apply settings
    void ApplySettings(const FSubtitleSettings& Settings);
};
```

---

## COLOR-BLIND SHADER SYSTEM

### Color Correction Architecture

```cpp
class UColorBlindCorrecter : public UObject
{
    GENERATED_BODY()

public:
    // Apply color blind correction
    UFUNCTION(BlueprintCallable, Category = "Accessibility")
    void ApplyColorBlindMode(EColorBlindType Type);

private:
    // Color correction shader
    UPROPERTY()
    UMaterialInterface* CorrectionShader;
    
    // Correction matrices
    FMatrix44f ProtanopiaMatrix;
    FMatrix44f DeuteranopiaMatrix;
    FMatrix44f TritanopiaMatrix;
};

enum class EColorBlindType
{
    None,
    Protanopia,     // Red-blind
    Deuteranopia,   // Green-blind
    Tritanopia      // Blue-blind
};

void ApplyColorBlindMode(EColorBlindType Type)
{
    if (!CorrectionShader) return;
    
    // Create dynamic material instance
    UMaterialInstanceDynamic* DynamicMat = UMaterialInstanceDynamic::Create(CorrectionShader, this);
    
    // Set correction matrix based on type
    FMatrix44f CorrectionMatrix;
    switch (Type)
    {
        case EColorBlindType::Protanopia:
            CorrectionMatrix = ProtanopiaMatrix;
            break;
        case EColorBlindType::Deuteranopia:
            CorrectionMatrix = DeuteranopiaMatrix;
            break;
        case EColorBlindType::Tritanopia:
            CorrectionMatrix = TritanopiaMatrix;
            break;
        default:
            // Identity matrix for no correction
            CorrectionMatrix = FMatrix44f::Identity;
            break;
    }
    
    // Apply to post-process
    ApplyToPostProcess(DynamicMat, CorrectionMatrix);
}
```

### Shader Matrix Setup

```cpp
void InitializeCorrectionMatrices()
{
    // Protanopia (Red-blind) correction matrix
    ProtanopiaMatrix = FMatrix44f(
        0.56667f, 0.43333f, 0.0f,
        0.55833f, 0.44167f, 0.0f,
        0.0f, 0.24167f, 0.75833f
    );
    
    // Deuteranopia (Green-blind) correction matrix
    DeuteranopiaMatrix = FMatrix44f(
        0.6250f, 0.3750f, 0.0f,
        0.7f, 0.3f, 0.0f,
        0.0f, 0.3f, 0.7f
    );
    
    // Tritanopia (Blue-blind) correction matrix
    TritanopiaMatrix = FMatrix44f(
        0.95f, 0.05f, 0.0f,
        0.0f, 0.43333f, 0.56667f,
        0.0f, 0.475f, 0.525f
    );
}
```

---

## ALTERNATIVE AUDIO CUES

### Visual/Haptic Alternatives

```cpp
class UAlternativeCueManager : public UObject
{
    GENERATED_BODY()

public:
    // Trigger audio cue with alternatives
    UFUNCTION(BlueprintCallable, Category = "Accessibility")
    void TriggerCueWithAlternatives(const FAudioCueEvent& CueEvent);

private:
    // Visual cue data
    struct FVisualCue
    {
        FColor IndicatorColor;
        FVector2D ScreenPosition;
        float Duration;
        float PulseFrequency;
    };
    
    // Haptic cue data
    struct FHapticCue
    {
        FHapticPattern Pattern;
    };
    
    // Cue mappings
    TMap<FString, FVisualCue> VisualCueLibrary;
    TMap<FString, FHapticCue> HapticCueLibrary;
    
    // Display visual cue
    void DisplayVisualCue(const FVisualCue& Cue);
    
    // Trigger haptic cue
    void TriggerHapticCue(const FHapticCue& Cue);
};

USTRUCT()
struct FAudioCueEvent
{
    GENERATED_BODY()

    FString EventType;  // "enemy_alert", "item_pickup", etc.
    FVector Location;
    float Intensity;
    
    // Accessibility preferences
    bool bUseVisualAlternative;
    bool bUseHapticAlternative;
};

void TriggerCueWithAlternatives(const FAudioCueEvent& CueEvent)
{
    // Play original audio (if enabled)
    PlayAudioCue(CueEvent.EventType, CueEvent.Location, CueEvent.Intensity);
    
    // Visual alternative
    if (CueEvent.bUseVisualAlternative)
    {
        FVisualCue* VisualCue = VisualCueLibrary.Find(CueEvent.EventType);
        if (VisualCue)
        {
            DisplayVisualCue(*VisualCue);
        }
    }
    
    // Haptic alternative
    if (CueEvent.bUseHapticAlternative)
    {
        FHapticCue* HapticCue = HapticCueLibrary.Find(CueEvent.EventType);
        if (HapticCue)
        {
            TriggerHapticCue(HapticCue->Pattern);
        }
    }
}

void DisplayVisualCue(const FVisualCue& Cue)
{
    // Create visual indicator widget
    UVisualIndicatorWidget* Indicator = CreateWidget<UVisualIndicatorWidget>(GetWorld());
    
    if (Indicator)
    {
        Indicator->SetIndicatorColor(Cue.IndicatorColor);
        Indicator->SetPosition(Cue.ScreenPosition);
        Indicator->SetDuration(Cue.Duration);
        Indicator->SetPulseFrequency(Cue.PulseFrequency);
        
        Indicator->AddToViewport();
    }
}
```

---

## PERFORMANCE SCALING SYSTEM

### Quality Scaling Architecture

```cpp
class UPerformanceScaler : public UObject
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;
    
    virtual void Tick(float DeltaTime) override;

private:
    // Quality levels
    enum class EQualityLevel
    {
        Low,
        Medium,
        High,
        Ultra
    };
    
    UPROPERTY(VisibleAnywhere)
    EQualityLevel CurrentQuality;
    
    // Target FPS
    UPROPERTY(EditDefaultsOnly)
    int32 TargetFPS;
    
    // FPS thresholds
    UPROPERTY(EditDefaultsOnly)
    float FPSDropThreshold;  // % below target to trigger scale-down
    
    UPROPERTY(EditDefaultsOnly)
    float FPSRecoveryThreshold;  // % above target to trigger scale-up
    
    // Current FPS
    float CurrentFPS;
    
    // Scale quality up
    void ScaleQualityUp();
    
    // Scale quality down
    void ScaleQualityDown();
    
    // Apply quality settings
    void ApplyQualitySettings(EQualityLevel Quality);
};

void Tick(float DeltaTime)
{
    // Measure current FPS
    CurrentFPS = 1.0f / DeltaTime;
    
    // Check if scaling needed
    float FPSTarget = static_cast<float>(TargetFPS);
    float FPSRatio = CurrentFPS / FPSTarget;
    
    if (FPSRatio < (1.0f - FPSDropThreshold) && CurrentQuality > EQualityLevel::Low)
    {
        // FPS too low, scale down
        ScaleQualityDown();
    }
    else if (FPSRatio > (1.0f + FPSRecoveryThreshold) && CurrentQuality < EQualityLevel::Ultra)
    {
        // FPS recovered, scale up
        ScaleQualityUp();
    }
}

void ApplyQualitySettings(EQualityLevel Quality)
{
    CurrentQuality = Quality;
    
    // Adjust graphics settings
    switch (Quality)
    {
        case EQualityLevel::Low:
            // Reduce resolution, disable effects
            SetResolutionScale(0.75f);
            DisablePostProcessEffects();
            SetShadowQuality("low");
            SetTextureQuality("low");
            break;
            
        case EQualityLevel::Medium:
            SetResolutionScale(0.9f);
            EnableEssentialEffects();
            SetShadowQuality("medium");
            SetTextureQuality("medium");
            break;
            
        case EQualityLevel::High:
            SetResolutionScale(1.0f);
            EnableAllEffects();
            SetShadowQuality("high");
            SetTextureQuality("high");
            break;
            
        case EQualityLevel::Ultra:
            SetResolutionScale(1.0f);
            EnableAllEffects();
            SetShadowQuality("ultra");
            SetTextureQuality("ultra");
            break;
    }
}
```

---

## BLUEPRINT API

### Designer Functions

```cpp
// Subtitles
UFUNCTION(BlueprintCallable, Category = "Accessibility")
void ShowSubtitle(const FString& Text, float Duration);

UFUNCTION(BlueprintCallable, Category = "Accessibility")
void SetSubtitleCustomization(const FSubtitleSettings& Settings);

// Color blind
UFUNCTION(BlueprintCallable, Category = "Accessibility")
void ApplyColorBlindMode(EColorBlindType Type);

// Alternative cues
UFUNCTION(BlueprintCallable, Category = "Accessibility")
void TriggerCueWithAlternatives(const FAudioCueEvent& CueEvent);

// Performance
UFUNCTION(BlueprintCallable, Category = "Accessibility")
void SetTargetFPS(int32 FPS);

UFUNCTION(BlueprintCallable, Category = "Accessibility")
void EnableAutomaticPerformanceScaling(bool bEnabled);
```

---

## PERFORMANCE BUDGET

### Accessibility System Budget

**Target**: 0.3ms CPU per frame

**Breakdown**:
- Subtitle rendering: 0.1ms
- Color correction: 0.1ms
- Visual cues: 0.05ms
- Performance scaling: 0.05ms

---

**Status**: ✅ **ACCESSIBILITY SYSTEM ARCHITECTURE COMPLETE**



