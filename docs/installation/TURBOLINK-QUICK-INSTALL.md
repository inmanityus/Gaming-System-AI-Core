# TurboLink Quick Installation Guide

## Quick Install (Manual Steps)

Since automated download failed, here's the manual process:

### Step 1: Download TurboLink

**Option A: Git Clone (if you have Git)**
```powershell
cd "E:\Vibe Code\Gaming System\AI Core\unreal\Plugins"
git clone https://github.com/thejinchao/turbolink.git TurboLink
```

**Option B: Manual Download**
1. Go to: https://github.com/thejinchao/turbolink
2. Click "Code" → "Download ZIP"
3. Extract ZIP file
4. Copy extracted folder to: `unreal\Plugins\TurboLink\`
5. Ensure `TurboLink.uplugin` file exists in that folder

### Step 2: Verify Installation

The plugin folder structure should be:
```
unreal/
  Plugins/
    TurboLink/
      TurboLink.uplugin  ← Must exist
      Source/
      Content/
      ...
```

### Step 3: Enable Plugin

✅ **Already Done**: I've added TurboLink to `BodyBroker.uproject` file.

**Or enable manually in UE5**:
1. Open UE5 Editor
2. Go to `Edit` → `Plugins`
3. Search for "TurboLink"
4. Check the box to enable
5. Restart UE5 Editor

### Step 4: Regenerate Project Files

1. Right-click `BodyBroker.uproject`
2. Select "Generate Visual Studio project files"
3. Or use UE5's "Refresh Visual Studio Project" option

### Step 5: Generate gRPC Code

After TurboLink is installed and project is compiled:

1. **Install Protocol Buffers Compiler**:
   ```powershell
   # Using Chocolatey (if installed)
   choco install protoc
   
   # Or download from: https://github.com/protocolbuffers/protobuf/releases
   ```

2. **Generate Code**:
   - TurboLink will automatically process `.proto` files during compilation
   - Or use TurboLink's code generator tool
   - Check TurboLink documentation for specific commands

### Step 6: Uncomment Code

After TurboLink is installed and compiled:
1. Open `unreal/Source/BodyBroker/BodyBrokerGRPCClient.cpp`
2. Uncomment all the TurboLink code (remove `/* */` comments)
3. Uncomment includes in `BodyBrokerGRPCClient.h`
4. Recompile project

---

## Verification Checklist

- [ ] TurboLink folder exists in `unreal/Plugins/TurboLink/`
- [ ] `TurboLink.uplugin` file exists
- [ ] Plugin enabled in `BodyBroker.uproject` (already done ✅)
- [ ] Project files regenerated
- [ ] UE5 Editor shows TurboLink as enabled
- [ ] Project compiles without errors
- [ ] gRPC code generated from `.proto` file
- [ ] TurboLink code uncommented in `BodyBrokerGRPCClient.cpp`

---

## Current Status

✅ **Completed**:
- Created Plugins directory
- Added TurboLink entry to `.uproject` file
- Created installation documentation

⏳ **Pending**:
- Download TurboLink plugin (manual step required)
- Enable plugin in UE5 Editor
- Generate gRPC code
- Uncomment TurboLink code

---

## Troubleshooting

**Plugin Not Found**:
- Ensure folder is named exactly `TurboLink` (case-sensitive)
- Check that `TurboLink.uplugin` exists in the folder

**Compilation Errors**:
- Verify TurboLink is compatible with UE5.6
- Check TurboLink GitHub for version compatibility
- Ensure all dependencies are installed

**gRPC Code Not Generated**:
- TurboLink generates code during compilation
- Check TurboLink documentation for manual generation steps
- Verify `.proto` file is in correct location

