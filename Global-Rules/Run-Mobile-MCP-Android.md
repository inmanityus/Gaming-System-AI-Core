# Run Mobile MCP Android Workflow

This workflow enables testing of mobile apps using the mobile-mcp-android MCP server with an Android emulator.

## Prerequisites Check

### 1. Verify Android Emulator is Running
```powershell
# First, add ADB to PATH (Windows-specific)
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\platform-tools"

# Check if Android emulator is running
adb devices
```
**Expected Output**: Should show at least one device with "device" status
**On Failure**: 
- Verify Android SDK is installed at expected location
- Add ADB to system PATH permanently
- Start Android Studio
- Launch AVD Manager
- Start an emulator
- If no emulators exist, create a new one (API Level 30+ recommended)

### 2. Verify ADB Connection
```powershell
# Test ADB connection
adb shell getprop ro.product.model
```
**Expected Output**: Device model name (e.g., "sdk_gphone64_x86_64")
**On Failure**:
- Restart ADB server: `adb kill-server && adb start-server`
- Check emulator is fully booted (wait 2-3 minutes after start)
- Verify emulator shows "Android" home screen

### 3. Check Mobile MCP Server
```powershell
# Navigate to mobile MCP directory
cd "E:\Vibe Code\Be Free Fitness\Mobile-App\mobile-mcp-android"

# Verify server files exist
Test-Path "server.js"
Test-Path "package.json"
```
**Expected Output**: Both should return `True`
**On Failure**: 
- Navigate to project root and verify mobile-mcp-android folder exists
- If missing, the MCP server needs to be set up first

## Setup Steps

### 1. Install Mobile MCP Dependencies
```powershell
# Navigate to mobile MCP directory
cd "E:\Vibe Code\Be Free Fitness\Mobile-App\mobile-mcp-android"

# Install dependencies
npm install
```
**Expected Output**: Dependencies installed successfully
**On Failure**: 
- Check internet connection
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and package-lock.json, then retry

### 2. Start Mobile MCP Server
```powershell
# Start the MCP server (run in background)
Start-Process -FilePath "node" -ArgumentList "server.js" -WindowStyle Hidden
```
**Expected Output**: Server starts without errors
**On Failure**:
- Check if port 5037 is available (ADB server port)
- Verify no other ADB processes are running
- Check server.js for syntax errors

### 3. Test MCP Connection
```powershell
# Test MCP tools availability
# This should be done through the MCP interface in your IDE
```
**Expected Tools Available**:
- `list_devices` - List connected Android devices
- `get_device_info` - Get device information
- `take_screenshot` - Capture device screen
- `shell_command` - Execute shell commands
- `install_apk` - Install APK files
- `uninstall_app` - Remove applications

## Mobile App Testing Workflow

### 1. Prepare Mobile App
```powershell
# Navigate to mobile app directory
cd "E:\Vibe Code\Be Free Fitness\Mobile-App\apps\trainer-mobile"

# Install dependencies
npm install
```
**Expected Output**: All dependencies installed
**On Failure**:
- Check package.json exists
- Verify Node.js version compatibility
- Clear npm cache and retry

### 2. Fix Common Issues

#### API URL Configuration
```powershell
# Check API configuration
Select-String -Path "src/services/apiClient.ts" -Pattern "API_BASE_URL"
```
**Expected**: Should show `http://localhost:3000/api`
**If Wrong**: Update the URL to match backend port

#### Database Reference
```powershell
# Check database reference in UI
Select-String -Path "App.tsx" -Pattern "PostgreSQL"
```
**Expected**: Should show correct database name
**If Wrong**: Update to match actual database configuration

### 3. Build and Deploy App

#### Option A: Using Expo Development Build
```powershell
# Start Expo development server
npx expo start --android
```
**Expected Output**: QR code and development server running
**On Failure**:
- Install Expo Go on emulator from Play Store
- Or build development APK: `npx expo build:android --type apk`

#### Option B: Using APK Installation
```powershell
# Build APK (if using EAS)
npx eas build --platform android --local
```
**Expected Output**: APK file generated
**On Failure**: 
- Check EAS CLI installation: `npm install -g @expo/eas-cli`
- Verify project configuration

### 4. Install App on Emulator
```powershell
# Install APK (replace with actual APK path)
adb install -r "path/to/app.apk"
```
**Expected Output**: "Success" message
**On Failure**:
- Check APK file exists and is valid
- Verify emulator has sufficient storage
- Check emulator architecture matches APK

## Testing Procedures

### 1. Device Verification
```powershell
# List connected devices
adb devices
```
**Expected**: At least one device showing "device" status
**On Failure**: Restart emulator and ADB server

### 2. App Installation Verification
```powershell
# Check if app is installed
adb shell pm list packages | findstr trainer
```
**Expected**: Package name containing "trainer" (may be empty if app not yet installed)
**On Failure**: App not installed, proceed with installation steps

### 3. App Launch Test
```powershell
# Launch app (replace with actual package name)
adb shell am start -n com.trainer.app/.MainActivity
```
**Expected**: App launches successfully
**On Failure**: 
- Check package name and activity name
- Verify app is properly installed
- Check app permissions

### 4. Screenshot Test
```powershell
# Take screenshot
adb shell screencap -p /sdcard/screenshot.png
adb pull /sdcard/screenshot.png
```
**Expected**: Screenshot file created locally
**On Failure**: 
- Check emulator storage permissions
- Verify emulator is responsive
- Try alternative screenshot methods

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. ADB Device Not Found
**Symptoms**: `adb devices` shows no devices or "unauthorized"
**Solutions**:
- Restart ADB server: `adb kill-server && adb start-server`
- Check emulator is fully booted
- Accept USB debugging prompt on emulator
- Restart emulator completely

#### 2. MCP Server Connection Failed
**Symptoms**: MCP tools not available or connection errors
**Solutions**:
- Verify server.js is running without errors
- Check ADB server is running on port 5037
- Restart MCP server process
- Check firewall settings

#### 3. App Installation Failed
**Symptoms**: APK installation fails or app crashes on launch
**Solutions**:
- Check APK is compatible with emulator architecture
- Verify emulator has sufficient storage (2GB+ free)
- Check app permissions in emulator settings
- Try installing with `-r` flag for reinstall

#### 4. Backend Connection Issues
**Symptoms**: App loads but can't connect to backend
**Solutions**:
- Verify backend server is running on correct port
- Check API_BASE_URL in mobile app configuration
- Ensure emulator can reach localhost (use 10.0.2.2 instead of localhost)
- Check backend CORS settings

#### 5. Database Connection Issues
**Symptoms**: Backend fails to start due to database errors
**Solutions**:
- Verify PostgreSQL is running
- Check database credentials in backend .env file
- Ensure database exists and is accessible
- Run database migrations if needed

### Environment-Specific Fixes

#### Windows-Specific Issues
```powershell
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# ADB PATH issues
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\platform-tools"
```

#### Network Configuration
```powershell
# Check local network connectivity
Test-NetConnection -ComputerName localhost -Port 3000
Test-NetConnection -ComputerName 10.0.2.2 -Port 3000
```

## Success Criteria

### ✅ Workflow Complete When:
1. Android emulator is running and connected via ADB
2. Mobile MCP server is running without errors
3. MCP tools are available and responsive
4. Mobile app is installed and launches successfully
5. App can take screenshots and execute shell commands
6. Backend connection is working (if applicable)

### 📋 Final Verification Checklist
- [ ] ADB devices shows connected emulator
- [ ] MCP server responds to tool calls
- [ ] Screenshot functionality works
- [ ] App launches and displays UI
- [ ] Backend API calls succeed (if backend running)
- [ ] All error handling works properly

### 🔍 Workflow Validation Test
Run these commands to verify the complete workflow:

```powershell
# 1. Test ADB connection
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\platform-tools"
adb devices

# 2. Test device info
adb shell getprop ro.product.model

# 3. Test MCP tools (via MCP interface)
# - list_devices
# - get_device_info  
# - take_screenshot
# - shell_command

# 4. Test app configuration
cd "E:\Vibe Code\Be Free Fitness\Mobile-App\apps\trainer-mobile"
Select-String -Path "src/services/apiClient.ts" -Pattern "API_BASE_URL"
Select-String -Path "App.tsx" -Pattern "PostgreSQL"
```

**Expected Results**:
- ADB shows connected device
- Device model returned (e.g., "sdk_gphone64_x86_64")
- MCP tools execute successfully
- API URL shows port 3000
- Database reference shows "trainer_db"

## Maintenance Notes

### Regular Maintenance
- Update Android emulator images monthly
- Keep ADB tools updated
- Monitor MCP server logs for issues
- Clean up old APK files and screenshots

### Performance Optimization
- Use hardware acceleration for emulator
- Allocate sufficient RAM (4GB+) to emulator
- Use SSD storage for better performance
- Close unnecessary applications during testing

## Emergency Recovery

### Complete Reset Procedure
1. Stop all processes (MCP server, emulator, backend)
2. Restart ADB server: `adb kill-server && adb start-server`
3. Restart Android emulator
4. Reinstall mobile app
5. Restart MCP server
6. Verify all connections

### Backup Important Files
- Mobile app source code
- MCP server configuration
- Screenshots and test results
- Backend database (if applicable)

---

**Note**: This workflow assumes the mobile-mcp-android MCP server is properly configured in your IDE. Adjust paths and commands as needed for your specific setup.
