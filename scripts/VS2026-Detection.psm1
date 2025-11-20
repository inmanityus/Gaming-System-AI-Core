# VS2026 Detection Helper
function Get-VS2026Path {
    $paths = @(
        "${env:ProgramFiles}\Microsoft Visual Studio\18\BuildTools",
        "${env:ProgramFiles}\Microsoft Visual Studio\18\Enterprise",
        "${env:ProgramFiles}\Microsoft Visual Studio\18\Professional",
        "${env:ProgramFiles}\Microsoft Visual Studio\18\Community",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\Enterprise",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\Professional",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\Community"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

function Test-VS2026 {
    $vsPath = Get-VS2026Path
    if ($vsPath) {
        Write-Host "VS2026 found at: $vsPath" -ForegroundColor Green
        return $true
    }
    Write-Host "VS2026 not found" -ForegroundColor Red
    return $false
}

function Get-VS2026MSBuild {
    $vsPath = Get-VS2026Path
    if ($vsPath) {
        return Join-Path $vsPath "MSBuild\Current\Bin\MSBuild.exe"
    }
    return $null
}

# Export functions
Export-ModuleMember -Function Get-VS2026Path, Test-VS2026, Get-VS2026MSBuild
