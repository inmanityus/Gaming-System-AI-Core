# TurboLink Installation Guide
**Date**: January 29, 2025  
**Status**: Installation Instructions

---

## What is TurboLink?

TurboLink is a third-party Unreal Engine plugin that provides gRPC (Google Remote Procedure Call) integration for UE5. It allows you to:
- Use gRPC clients and servers in C++ and Blueprints
- Generate UE5 code from Protocol Buffer (`.proto`) files
- Handle streaming and unary gRPC calls
- Communicate efficiently with backend services

---

## Installation Methods

### Method 1: GitHub Download (Recommended)

1. **Download TurboLink**:
   ```powershell
   # Navigate to project root
   cd "E:\Vibe Code\Gaming System\AI Core"
   
   # Create Plugins directory if it doesn't exist
   New-Item -ItemType Directory -Force -Path "unreal\Plugins"
   
   # Download from GitHub (CORRECT REPOSITORY)
   $url = "https://github.com/thejinchao/turbolink/archive/refs/heads/main.zip"
   Invoke-WebRequest -Uri $url -OutFile "unreal\Plugins\turbolink.zip"
   
   # Extract
   Expand-Archive -Path "unreal\Plugins\turbolink.zip" -DestinationPath "unreal\Plugins" -Force
   
   # Rename to TurboLink
   $extracted = Get-ChildItem "unreal\Plugins" -Directory | Where-Object { $_.Name -like "turbolink*" } | Select-Object -First 1
   if ($extracted) {
       Move-Item -Path $extracted.FullName -Destination "unreal\Plugins\TurboLink" -Force
   }
   
   # Clean up
   Remove-Item "unreal\Plugins\turbolink.zip" -Force
   ```

2. **Enable Plugin in Project**:
   - Open `unreal/BodyBroker.uproject` in a text editor
   - Add TurboLink to the Plugins array (already done if you ran the installation script)
   - Or enable it in UE5 Editor: `Edit` → `Plugins` → Search "TurboLink" → Enable

3. **Regenerate Project Files**:
   ```powershell
   # Right-click BodyBroker.uproject → Generate Visual Studio project files
   # Or use UE5's "Refresh Visual Studio Project" option
   ```

### Method 2: Epic Games Marketplace

1. Open Epic Games Launcher
2. Go to `Unreal Engine` → `Marketplace`
3. Search for "TurboLink"
4. Click "Add to Project" → Select your project
5. Enable the plugin in UE5 Editor

### Method 3: Manual Git Clone

```powershell
cd "unreal\Plugins"
git clone https://github.com/thejinchao/turbolink.git TurboLink
```

---

## Post-Installation Steps

### 1. Generate gRPC Code from Proto File

After TurboLink is installed, you need to generate C++ code from the `.proto` file:

1. **Install Protocol Buffers Compiler (protoc)**:
   - Download from: https://github.com/protocolbuffers/protobuf/releases
   - Or use package manager: `choco install protoc` (Windows)

2. **Generate C++ Code**:
   ```powershell
   # Navigate to project
   cd "unreal\Source\BodyBroker"
   
   # Generate C++ code (basic protoc)
   protoc --cpp_out=. bodybroker.proto
   
   # TurboLink will generate UE5-specific code when you compile the project
   ```

3. **Use TurboLink Code Generator**:
   - TurboLink includes its own code generator
   - It will automatically process `.proto` files in your project
   - Check TurboLink documentation for specific generator commands

### 2. Uncomment TurboLink Code

After installation, uncomment the TurboLink code in:
- `unreal/Source/BodyBroker/BodyBrokerGRPCClient.cpp`
- `unreal/Source/BodyBroker/BodyBrokerGRPCClient.h`

### 3. Compile Project

1. Open project in UE5 Editor
2. It will prompt to rebuild modules - click "Yes"
3. Or compile from Visual Studio/your IDE

### 4. Verify Installation

1. Open UE5 Editor
2. Go to `Edit` → `Plugins`
3. Search for "TurboLink"
4. Verify it's enabled and shows version info

---

## Troubleshooting

### Plugin Not Found
- Ensure `TurboLink.uplugin` exists in `unreal/Plugins/TurboLink/`
- Check that plugin is enabled in `.uproject` file
- Regenerate project files

### Compilation Errors
- Ensure TurboLink is compatible with UE5.6
- Check that all TurboLink dependencies are installed
- Verify `.proto` files are in correct location

### gRPC Code Not Generated
- Run TurboLink code generator manually
- Check TurboLink documentation for generator usage
- Ensure `protoc` is installed and in PATH

---

## Files Modified

- `unreal/BodyBroker.uproject` - Added TurboLink plugin entry
- `unreal/Source/BodyBroker/BodyBrokerGRPCClient.h/cpp` - Ready for TurboLink (commented code)

---

## Next Steps

1. ✅ Install TurboLink plugin
2. ✅ Enable plugin in project
3. ⏳ Generate gRPC code from `.proto` file
4. ⏳ Uncomment TurboLink code in `BodyBrokerGRPCClient.cpp`
5. ⏳ Compile project
6. ⏳ Test gRPC connection

---

## References

- TurboLink GitHub: https://github.com/thejinchao/turbolink
- TurboLink Documentation: Check GitHub repository README
- Protocol Buffers: https://protobuf.dev/
- gRPC Documentation: https://grpc.io/docs/

