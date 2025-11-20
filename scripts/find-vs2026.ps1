# Find Visual Studio 2026 Build Tools Installation

Write-Host "=== Searching for Visual Studio 2026 Build Tools ===" -ForegroundColor Cyan

$foundLocations = @()

# Method 1: Check Windows Registry
Write-Host "`nChecking Windows Registry..." -ForegroundColor Yellow
$registryPaths = @(
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\18.0",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\18.0",
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\Setup",
    "HKCU:\SOFTWARE\Microsoft\VisualStudio\18.0_Config"
)

foreach ($regPath in $registryPaths) {
    if (Test-Path $regPath) {
        Write-Host "  Found registry key: $regPath" -ForegroundColor Green
        try {
            $installPath = (Get-ItemProperty -Path $regPath -Name "InstallDir" -ErrorAction SilentlyContinue).InstallDir
            if ($installPath -and (Test-Path $installPath)) {
                $foundLocations += $installPath
                Write-Host "  Install path: $installPath" -ForegroundColor Cyan
            }
        } catch {}
    }
}

# Method 2: Check Environment Variables
Write-Host "`nChecking Environment Variables..." -ForegroundColor Yellow
$envVars = @(
    "VS180COMNTOOLS",
    "VS2026_INSTALL_PATH",
    "VSINSTALLDIR",
    "VCToolsVersion"
)

foreach ($var in $envVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var, [System.EnvironmentVariableTarget]::Machine)
    if (-not $value) {
        $value = [System.Environment]::GetEnvironmentVariable($var, [System.EnvironmentVariableTarget]::User)
    }
    if ($value) {
        Write-Host "  $var = $value" -ForegroundColor Green
        if (Test-Path $value) {
            $foundLocations += $value
        }
    }
}

# Method 3: Search common paths
Write-Host "`nSearching common installation paths..." -ForegroundColor Yellow
$searchPaths = @(
    "${env:ProgramFiles}\Microsoft Visual Studio\18",
    "${env:ProgramFiles}\Microsoft Visual Studio\2026",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2026",
    "${env:ProgramFiles}\BuildTools",
    "${env:ProgramFiles(x86)}\BuildTools",
    "C:\BuildTools",
    "C:\VS2026",
    "C:\VisualStudio2026",
    "${env:LOCALAPPDATA}\Microsoft\VisualStudio\18.0"
)

foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        Write-Host "  Found: $path" -ForegroundColor Green
        $foundLocations += $path
    }
}

# Method 4: Search for MSBuild.exe
Write-Host "`nSearching for MSBuild.exe..." -ForegroundColor Yellow
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Free -gt 0 } | Select-Object -ExpandProperty Root

foreach ($drive in $drives) {
    Write-Host "  Searching $drive" -ForegroundColor Gray
    $msbuildPaths = Get-ChildItem -Path $drive -Filter "MSBuild.exe" -Recurse -ErrorAction SilentlyContinue -Depth 5 | 
                    Where-Object { $_.DirectoryName -like "*Visual Studio*" -or $_.DirectoryName -like "*BuildTools*" } |
                    Select-Object -First 5
    
    foreach ($msbuild in $msbuildPaths) {
        Write-Host "  Found MSBuild: $($msbuild.FullName)" -ForegroundColor Green
        
        # Check version
        try {
            $version = & $msbuild.FullName -version -nologo | Select-Object -First 1
            Write-Host "    Version: $version" -ForegroundColor Cyan
        } catch {}
    }
}

# Method 5: Check for Developer Command Prompt shortcuts
Write-Host "`nSearching for Developer Command Prompt shortcuts..." -ForegroundColor Yellow
$startMenuPaths = @(
    "${env:ProgramData}\Microsoft\Windows\Start Menu\Programs",
    "${env:APPDATA}\Microsoft\Windows\Start Menu\Programs"
)

foreach ($startPath in $startMenuPaths) {
    $shortcuts = Get-ChildItem -Path $startPath -Filter "*Developer*Command*2026*.lnk" -Recurse -ErrorAction SilentlyContinue
    $shortcuts += Get-ChildItem -Path $startPath -Filter "*VS*2026*.lnk" -Recurse -ErrorAction SilentlyContinue
    $shortcuts += Get-ChildItem -Path $startPath -Filter "*Build*Tools*18*.lnk" -Recurse -ErrorAction SilentlyContinue
    
    foreach ($shortcut in $shortcuts) {
        Write-Host "  Found shortcut: $($shortcut.Name)" -ForegroundColor Green
        
        # Parse shortcut target
        $shell = New-Object -ComObject WScript.Shell
        $lnk = $shell.CreateShortcut($shortcut.FullName)
        Write-Host "    Target: $($lnk.TargetPath)" -ForegroundColor Gray
        Write-Host "    Arguments: $($lnk.Arguments)" -ForegroundColor Gray
    }
}

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan

if ($foundLocations.Count -gt 0) {
    Write-Host "`nPossible VS2026 locations found:" -ForegroundColor Green
    $foundLocations | Select-Object -Unique | ForEach-Object {
        Write-Host "  $_" -ForegroundColor White
    }
} else {
    Write-Host "`n⚠️ VS2026 Build Tools installation not found in standard locations" -ForegroundColor Yellow
    Write-Host "`nTo manually specify the location, please:" -ForegroundColor Cyan
    Write-Host "1. Open the VS2026 Developer Command Prompt" -ForegroundColor White
    Write-Host "2. Run: echo %VSINSTALLDIR%" -ForegroundColor White
    Write-Host "3. Run: echo %VCToolsVersion%" -ForegroundColor White
    Write-Host "4. Share these paths so we can update the configuration" -ForegroundColor White
}

# Instructions for manual configuration
Write-Host "`n=== MANUAL CONFIGURATION ===" -ForegroundColor Cyan
Write-Host "If VS2026 is installed in a custom location, you can set it manually:" -ForegroundColor Yellow
Write-Host '$env:VS2026_PATH = "C:\Your\VS2026\Path"' -ForegroundColor Gray
Write-Host '[System.Environment]::SetEnvironmentVariable("VS2026_PATH", $env:VS2026_PATH, [System.EnvironmentVariableTarget]::User)' -ForegroundColor Gray
