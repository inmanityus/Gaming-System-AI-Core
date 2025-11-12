# Create Minimal UE5 Test Project for AI Testing System Validation
# Generates first-person project with GameObserver plugin integrated

param(
    [string]$ProjectName = "QATestProject",
    [string]$ProjectPath = "E:\Vibe Code\Gaming System\AI Core\qa-test-project"
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Creating UE5 Test Project for QA System Validation" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$UE5Editor = "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe"
$UnrealVersionSelector = "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\DotNET\UnrealVersionSelector\UnrealVersionSelector.exe"

# Verify UE5 installation
if (-not (Test-Path $UE5Editor)) {
    Write-Error "UE5 5.6.1 not found. Please verify installation."
    exit 1
}

Write-Host "✓ UE5 5.6.1 found" -ForegroundColor Green
Write-Host ""

# Create project directory
Write-Host "Creating project directory..." -NoNewline
New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
Write-Host " ✓" -ForegroundColor Green

# Create basic .uproject file
Write-Host "Creating project file..." -NoNewline
$UProjectContent = @"
{
	"FileVersion": 3,
	"EngineAssociation": "5.6",
	"Category": "",
	"Description": "QA Test Project for AI-Driven Game Testing System",
	"Modules": [
		{
			"Name": "QATestProject",
			"Type": "Runtime",
			"LoadingPhase": "Default"
		}
	],
	"Plugins": [
		{
			"Name": "GameObserver",
			"Enabled": true
		}
	]
}
"@

$UProjectPath = Join-Path $ProjectPath "$ProjectName.uproject"
$UProjectContent | Out-File $UProjectPath -Encoding UTF8
Write-Host " ✓" -ForegroundColor Green

# Copy GameObserver plugin
Write-Host "Copying GameObserver plugin..." -NoNewline
$PluginsDir = Join-Path $ProjectPath "Plugins"
$GameObserverDest = Join-Path $PluginsDir "GameObserver"
Copy-Item -Path "E:\Vibe Code\Gaming System\AI Core\unreal\Plugins\GameObserver" -Destination $GameObserverDest -Recurse -Force
Write-Host " ✓" -ForegroundColor Green

# Create basic source structure
Write-Host "Creating source structure..." -NoNewline
$SourceDir = Join-Path $ProjectPath "Source\QATestProject"
New-Item -ItemType Directory -Path $SourceDir -Force | Out-Null

# Create Build.cs
$BuildCS = @"
using UnrealBuildTool;

public class QATestProject : ModuleRules
{
	public QATestProject(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore" });
		PrivateDependencyModuleNames.AddRange(new string[] { });
	}
}
"@
Set-Content -Path (Join-Path $SourceDir "QATestProject.Build.cs") -Value $BuildCS
Write-Host " ✓" -ForegroundColor Green

# Create Target files
Write-Host "Creating target files..." -NoNewline
$EditorTarget = @"
using UnrealBuildTool;
using System.Collections.Generic;

public class QATestProjectEditorTarget : TargetRules
{
	public QATestProjectEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V5;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_5;
		ExtraModuleNames.Add("QATestProject");
	}
}
"@
Set-Content -Path (Join-Path $ProjectPath "Source\QATestProjectEditor.Target.cs") -Value $EditorTarget

$GameTarget = @"
using UnrealBuildTool;
using System.Collections.Generic;

public class QATestProjectTarget : TargetRules
{
	public QATestProjectTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V5;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_5;
		ExtraModuleNames.Add("QATestProject");
	}
}
"@
Set-Content -Path (Join-Path $ProjectPath "Source\QATestProject.Target.cs") -Value $GameTarget
Write-Host " ✓" -ForegroundColor Green

# Generate Visual Studio files
Write-Host "Generating Visual Studio solution..." -ForegroundColor Yellow
& $UnrealVersionSelector -projectfiles -project=$UProjectPath -game -rocket -progress

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ Test Project Created Successfully!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Project Location: $ProjectPath" -ForegroundColor Cyan
Write-Host "Project File: $UProjectPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Build the project:" -ForegroundColor White
Write-Host "   & 'C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\Build.bat' QATestProjectEditor Win64 Development '$UProjectPath'" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Open in UE5 Editor:" -ForegroundColor White
Write-Host "   & '$UE5Editor' '$UProjectPath'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Add GameObserver to PlayerController and test capture!" -ForegroundColor White

