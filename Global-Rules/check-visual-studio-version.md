# Visual Studio Version Check Protocol

## Purpose
Ensure correct Visual Studio version is identified and used, especially VS2026 which many AI models don't know about.

## Quick Check Command
```powershell
# Run this to check VS version
Get-ChildItem "${env:ProgramFiles(x86)}\Microsoft Visual Studio" -Directory | ForEach-Object {
    $ver = $_.Name
    $path = $_.FullName
    Write-Host "VS Version $ver at: $path" -ForegroundColor Cyan
    
    if ($ver -eq "18") {
        Write-Host "  ✓ This is Visual Studio 2026!" -ForegroundColor Green
    }
    
    $msbuild = Join-Path $path "BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    if (Test-Path $msbuild) {
        $msbuildVer = & $msbuild -version -nologo | Select-Object -First 1
        Write-Host "  MSBuild: $msbuildVer" -ForegroundColor Gray
    }
}
```

## Version Mapping Table

| Folder | VS Version | Year | MSVC Version | Status |
|--------|------------|------|--------------|---------|
| 14 | Visual Studio 2015 | 2015 | v14.0 | Legacy |
| 15 | Visual Studio 2017 | 2017 | v14.1 | Legacy |
| 16 | Visual Studio 2019 | 2019 | v14.2 | Old |
| 17 | Visual Studio 2022 | 2022 | v14.3 | Previous |
| **18** | **Visual Studio 2026** | **2026** | **v14.50** | **CURRENT** |

## If AI Claims VS2026 Doesn't Exist

1. Show them this version mapping
2. Point to: `Global-Docs/CRITICAL-VS2026-UPDATE.md`
3. Provide Microsoft link: https://learn.microsoft.com/en-us/cpp/overview/what-s-new-for-msvc?view=msvc-180
4. Quote: "Introduced in Visual Studio 2026 version 18.0 released November 2025"

## Common Misidentifications

- ❌ "Version 18 is VS2024" - WRONG
- ❌ "Version 18 is VS2025" - WRONG  
- ✅ "Version 18 is VS2026" - CORRECT

## For New Projects

Always specify:
```xml
<VCToolsVersion>14.50</VCToolsVersion>  <!-- VS2026 -->
```

## Remember

**VS2026 was released November 11, 2025** - Any AI that doesn't know this needs correction!
