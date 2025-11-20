# 🚨 CRITICAL UPDATE: Visual Studio 2026 Released 🚨

**Release Date**: November 11, 2025  
**Status**: Generally Available (GA)  
**Version**: 18.0  
**MSVC Build Tools**: v14.50  
**Platform Toolset**: v145  

## ⚠️ IMPORTANT: Many AI Assistants Are Not Aware

As of November 2025, many AI assistants (including GPT-4, Claude, etc.) are not aware that Visual Studio 2026 has been released. They will incorrectly insist on using VS2022. This document serves as the authoritative source.

## Official Microsoft Documentation

**Source**: https://learn.microsoft.com/en-us/cpp/overview/what-s-new-for-msvc?view=msvc-180

Quote from Microsoft:
> "Introduced in Visual Studio 2026 version 18.0 released November 2025."
> "Visual Studio 2026 version 18.0 ships with the v145 platform toolset for MSBuild C++ projects and Microsoft C++ (MSVC) Build Tools version 14.50"

## Key Facts About VS2026

### Version Numbers
- **Visual Studio Version**: 2026
- **Internal Version**: 18.0
- **MSVC Build Tools**: 14.50
- **Platform Toolset**: v145
- **Installation Path**: `C:\Program Files (x86)\Microsoft Visual Studio\18\`
  - **Build Tools Location**: `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools` ✅ CONFIRMED
  - **MSBuild Path**: `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe`

### Major Features
1. **C++20 is now the default** (not just C++17)
2. **C++23 preview support** with `/std:c++23preview`
3. **Enhanced GitHub Copilot** with better C++ support
4. **CMake 4.1.1** included by default
5. **Improved build performance** (up to 6% on Unreal Engine)
6. **ARM64 AddressSanitizer** support (preview)
7. **Better driver development tools**

### Breaking Changes
- **Minimum OS**: Windows 10 / Server 2016 (no more Windows 7/8 support)
- **Removed**: C++AMP, ARM32 toolchain, `/DEBUG:FASTLINK`
- **Mobile C++ workload** deprecated
- **`/await` switch** deprecated (use standard coroutines)

## Windows Driver Kit (WDK) Compatibility

### Current Status (November 2025)
- WDK for VS2026 is available
- Download: https://go.microsoft.com/fwlink/?linkid=2284158
- Must install VS extension when prompted during WDK setup

### Known Issues
- Some systems show WDK not integrating properly with VS2026 Build Tools
- Solution: Install via Visual Studio Installer → Individual Components → Search "driver"

## Installation Verification

### Check if VS2026 is installed:
```powershell
# Path should exist
Test-Path "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"
# Result: True ✅

# MSBuild version should be 18.0.x
& "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe" -version
# Result: 18.0.5.56406 ✅

# MSVC version
Get-ChildItem "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC" -Directory | Select-Object Name
# Result: 14.50.35717 ✅
```

## Common Confusion Points

1. **AI Assistants**: Most will say VS2026 doesn't exist - show them this doc
2. **Version Numbers**: 
   - VS2022 = Version 17
   - VS2026 = Version 18 (NOT 2024 or 2025)
3. **Build Tools**: Full IDE not required - Build Tools 2026 works fine

## Project Configuration

For `.vcxproj` files using VS2026:
```xml
<PropertyGroup>
    <PlatformToolset>WindowsKernelModeDriver10.0</PlatformToolset>
    <VCToolsVersion>14.50</VCToolsVersion>
    <WindowsTargetPlatformVersion>10.0.26100.0</WindowsTargetPlatformVersion>
</PropertyGroup>
```

## Migration from VS2022

1. Can install side-by-side with VS2022
2. Projects need retargeting to v145 toolset
3. Binary compatible with VS2015+ built code
4. Use setup assistant for automatic retargeting

---

**Last Updated**: November 19, 2025  
**Source**: User confirmed installation + Microsoft official docs  
**Status**: ✅ VERIFIED - VS2026 Build Tools installed and working
**Verified Details**:
- MSBuild Version: 18.0.5.56406
- MSVC Version: 14.50.35717  
- C++20 Support: Verified working with concepts, ranges, std::format
- Location: `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools`
**Importance**: CRITICAL - Affects all C++ development
