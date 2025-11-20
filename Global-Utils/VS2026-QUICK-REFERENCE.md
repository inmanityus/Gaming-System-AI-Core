# Visual Studio 2026 Quick Reference Card

## 🎯 Key Facts
- **Released**: November 11, 2025 (8 days ago!)
- **Version**: 18.0
- **MSVC**: v14.50
- **Toolset**: v145
- **Status**: Generally Available (GA)

## 📍 Installation Paths
```
Build Tools: C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\
MSBuild:     C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe
```

## 🔧 Version Check Commands
```powershell
# Check if VS2026 installed
Test-Path "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18"

# Get MSBuild version (should show 18.0.x)
& "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe" -version
```

## 📦 Required Components
- [ ] Desktop development with C++
- [ ] Windows 11 SDK (10.0.26100.0+)
- [ ] Windows Driver Kit
- [ ] Spectre-mitigated libraries

## 🏗️ Project Configuration
```xml
<PropertyGroup>
    <VCToolsVersion>14.50</VCToolsVersion>
    <PlatformToolset>v145</PlatformToolset>
    <!-- For drivers: -->
    <PlatformToolset>WindowsKernelModeDriver10.0</PlatformToolset>
</PropertyGroup>
```

## 🔄 Migration from VS2022
1. Can install side-by-side
2. Update `.vcxproj` files with new version
3. Rebuild all projects
4. Binary compatible with VS2015+

## 🚀 New Features
- C++20 default (was C++17)
- C++23 preview
- Enhanced Copilot
- 6% faster builds
- ARM64 AddressSanitizer

## ⚠️ Breaking Changes
- No Windows 7/8 support
- No ARM32 toolchain
- No C++AMP
- Mobile C++ deprecated

## 🔗 Download Links
- **IDE**: https://visualstudio.microsoft.com/downloads/
- **Build Tools**: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2026
- **WDK**: https://go.microsoft.com/fwlink/?linkid=2284158

## 🆘 Common Issues
1. **WDK not integrating**: Use VS Installer → Individual Components
2. **AI says VS2026 doesn't exist**: Show them Global-Docs/CRITICAL-VS2026-UPDATE.md
3. **Build errors**: Ensure VCToolsVersion is 14.50
