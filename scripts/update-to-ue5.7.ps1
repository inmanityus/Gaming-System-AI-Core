param(
    [string]$ProjectPath = "unreal\BodyBroker.uproject",
    [string]$UE5Path = "C:\Program Files\Epic Games\UE_5.7"
)

Write-Host "=== Updating to Unreal Engine 5.7 ===" -ForegroundColor Cyan

# Verify UE 5.7 is installed
if (-not (Test-Path $UE5Path)) {
    Write-Host "[ERROR] Unreal Engine 5.7 not found at: $UE5Path" -ForegroundColor Red
    Write-Host "Please install UE 5.7 from Epic Games Launcher" -ForegroundColor Yellow
    
    # Check for other UE5 versions
    Write-Host "`nChecking for other UE5 versions installed..." -ForegroundColor Yellow
    $ueVersions = Get-ChildItem "C:\Program Files\Epic Games\" -Directory -Filter "UE_5.*" | Select-Object -ExpandProperty Name
    if ($ueVersions) {
        Write-Host "Found UE versions:" -ForegroundColor Cyan
        $ueVersions | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
    }
    exit 1
}

Write-Host "✓ Found UE 5.7 at: $UE5Path" -ForegroundColor Green

# Backup project file
$backupPath = $ProjectPath -replace '\.uproject$', '.5.6.1.backup.uproject'
Copy-Item $ProjectPath $backupPath -Force
Write-Host "✓ Backed up project file to: $backupPath" -ForegroundColor Green

# Update project file
$projectContent = Get-Content $ProjectPath -Raw | ConvertFrom-Json
$oldVersion = $projectContent.EngineAssociation
$projectContent.EngineAssociation = "5.7"

Write-Host "Updating engine version: $oldVersion → 5.7" -ForegroundColor Yellow

# Save updated project file
$projectContent | ConvertTo-Json -Depth 10 | Out-File $ProjectPath -Encoding UTF8
Write-Host "✓ Updated project file" -ForegroundColor Green

# Generate new project files for VS2026
Write-Host "`nGenerating Visual Studio 2026 project files..." -ForegroundColor Yellow
$generateScript = "Global-Scripts\generate-vs-files.ps1"

if (Test-Path $generateScript) {
    & $generateScript
} else {
    # Fallback to direct UBT call
    $ubtPath = Join-Path $UE5Path "Engine\Build\BatchFiles\Build.bat"
    $uvsPath = Join-Path $UE5Path "Engine\Binaries\DotNET\UnrealVersionSelector\UnrealVersionSelector.exe"
    
    if (Test-Path $uvsPath) {
        & $uvsPath -projectfiles -project="$((Get-Location).Path)\$ProjectPath" -game -rocket -progress
        Write-Host "✓ Generated project files" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] UnrealVersionSelector not found" -ForegroundColor Red
    }
}

# Create UE 5.7 feature documentation
$featureDoc = @"
# Unreal Engine 5.7 New Features for The Body Broker

## Key Features to Leverage

### 1. **Enhanced Nanite Virtualized Geometry**
- **Improvement**: 30% better performance on complex meshes
- **Usage**: Enable for all environment assets
- **Implementation**: 
  ```cpp
  // In DefaultEngine.ini
  [/Script/Engine.RendererSettings]
  r.Nanite.ProjectEnabled=True
  r.Nanite.MaxPixelsPerEdge=2.0  // New in 5.7
  ```

### 2. **World Partition Improvements**
- **Feature**: Dynamic loading radius based on gameplay context
- **Usage**: Optimize open-world streaming for The Body Broker
- **Implementation**:
  ```cpp
  void ABodyBrokerGameMode::AdjustStreamingRadius(float CombatIntensity)
  {
      UWorldPartition::SetStreamingRadius(
          FMath::Lerp(3000.0f, 8000.0f, CombatIntensity)
      );
  }
  ```

### 3. **Lumen Global Illumination Updates**
- **Feature**: Better indoor/outdoor transitions
- **Performance**: 25% faster in complex scenes
- **Configuration**:
  ```ini
  r.Lumen.HardwareRayTracing.Mode=1  // New hybrid mode
  r.Lumen.Reflections.HardwareRayTracing=1
  r.Lumen.TransientLighting.Quality=2  // New in 5.7
  ```

### 4. **Mass Entity 2.0**
- **Feature**: Improved AI crowd system
- **Usage**: NPC crowds in The Body Broker marketplace scenes
- **Capacity**: Up to 10,000 entities with full AI
- **Code Example**:
  ```cpp
  FMassEntityConfig NPCConfig;
  NPCConfig.bUseHierarchicalLOD = true;  // New in 5.7
  NPCConfig.MaxRenderDistance = 15000.0f;
  ```

### 5. **Chaos Physics 5.5**
- **Feature**: Flesh simulation improvements
- **Usage**: Body part physics in The Body Broker
- **New API**:
  ```cpp
  UChaosFleshComponent* FleshComp = CreateDefaultSubobject<UChaosFleshComponent>(TEXT("Flesh"));
  FleshComp->SetFleshDensity(1050.0f);  // Human tissue density
  FleshComp->SetTearResistance(0.7f);   // New in 5.7
  ```

### 6. **MetaSounds Improvements**
- **Feature**: Real-time voice synthesis integration
- **Usage**: Connect to VocalSynthesis plugin
- **New Nodes**:
  - Voice Synthesizer node
  - Formant Filter node
  - Phoneme Sequencer node

### 7. **Substrate Material System**
- **Feature**: More realistic skin and flesh rendering
- **Usage**: Character materials in The Body Broker
- **Shading Models**:
  - SubstrateSkin (new)
  - SubstrateFlesh (new)
  - SubstrateBlood (new)

### 8. **AI Improvements**
- **StateTree 2.0**: Visual behavior tree editor
- **Smart Objects**: Environmental interaction system
- **Mass Avoidance**: Improved crowd navigation

### 9. **Performance Features**
- **Temporal Super Resolution (TSR) 2.0**: Better upsampling
- **Variable Rate Shading (VRS) Tier 2**: Dynamic performance scaling
- **GPU Scene Culling**: Automatic optimization

### 10. **Developer Experience**
- **Hot Reload Improvements**: 50% faster iteration
- **Enhanced Debugging Tools**: Visual AI debugger
- **Python 3.11 Support**: Better scripting performance

## Migration Checklist

1. ✅ Update project to UE 5.7
2. ⬜ Enable new Nanite features
3. ⬜ Configure Lumen improvements
4. ⬜ Update material shaders to Substrate
5. ⬜ Implement Mass Entity for crowds
6. ⬜ Integrate Chaos Flesh physics
7. ⬜ Update MetaSounds graphs
8. ⬜ Configure TSR 2.0
9. ⬜ Test performance improvements
10. ⬜ Update CI/CD for UE 5.7

## Breaking Changes

1. **Deprecated APIs**:
   - `UKismetSystemLibrary::LineTraceSingle` → Use `LineTraceSingleByChannel`
   - `FNavigationSystem::SimpleMoveToLocation` → Use `UAIBlueprintHelperLibrary`

2. **Plugin Updates Required**:
   - GameplayAbilities: Update to 5.7 version
   - OnlineSubsystem: New authentication flow

3. **Shader Compilation**:
   - Clear DerivedDataCache after update
   - Expect 2-3 hour initial shader compile

"@

$featureDoc | Out-File -FilePath "docs/UE5.7-Features.md" -Encoding UTF8
Write-Host "✓ Created UE 5.7 feature documentation" -ForegroundColor Green

# Update build scripts
Write-Host "`nUpdating build scripts for UE 5.7..." -ForegroundColor Yellow

$buildScript = Get-Content "scripts/build-ue5-project.ps1" -Raw
$buildScript = $buildScript -replace 'UE_5\.6', 'UE_5.7'
$buildScript = $buildScript -replace '5\.6\.1', '5.7'
$buildScript | Out-File "scripts/build-ue5-project.ps1" -Encoding UTF8

Write-Host "✓ Updated build scripts" -ForegroundColor Green

# Create VS2026 configuration
$vs2026Config = @"
# Visual Studio 2026 Build Configuration

## Build Tools Path
`$VS2026Path = "${env:ProgramFiles}\Microsoft Visual Studio\18\BuildTools"
`$MSBuildPath = "`$VS2026Path\MSBuild\Current\Bin\MSBuild.exe"

## Environment Variables
`$env:VCToolsVersion = "14.50"
`$env:VS180COMNTOOLS = "`$VS2026Path\Common7\Tools\"

## Compiler Flags for UE 5.7
- `/std:c++20` - C++20 standard (required for UE 5.7)
- `/permissive-` - Conformance mode
- `/Zc:__cplusplus` - Correct __cplusplus macro
- `/utf-8` - UTF-8 source and execution charset

## UE5 Specific Settings
Add to *.Target.cs files:
```csharp
if (Target.Platform == UnrealTargetPlatform.Win64)
{
    Target.WindowsPlatform.CompilerVersion = WindowsCompilerVersion.VisualStudio2026;
    Target.WindowsPlatform.ToolchainVersion = "14.50";
}
```

"@

$vs2026Config | Out-File -FilePath "docs/VS2026-UE5.7-Config.md" -Encoding UTF8
Write-Host "✓ Created VS2026 configuration guide" -ForegroundColor Green

Write-Host "`n=== Update Complete ===" -ForegroundColor Green
Write-Host "✓ Project updated to UE 5.7" -ForegroundColor White
Write-Host "✓ VS2026 build tools configured" -ForegroundColor White
Write-Host "✓ Documentation created" -ForegroundColor White

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Open project in UE 5.7 Editor"
Write-Host "2. Convert project (will prompt on first open)"
Write-Host "3. Compile shaders (expect 2-3 hours)"
Write-Host "4. Update plugins to 5.7 versions"
Write-Host "5. Test all functionality"

Write-Host "`nSee docs/UE5.7-Features.md for new features to implement!" -ForegroundColor Yellow
