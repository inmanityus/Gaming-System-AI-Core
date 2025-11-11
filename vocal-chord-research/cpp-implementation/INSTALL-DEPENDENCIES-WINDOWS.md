# Install Dependencies on Windows

## Option 1: vcpkg (RECOMMENDED - Easy)

### Step 1: Install vcpkg (if not already installed)
```powershell
cd C:\
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
```

### Step 2: Install dependencies
```powershell
cd C:\vcpkg
.\vcpkg install libsndfile:x64-windows eigen3:x64-windows
```

### Step 3: Set environment variable for CMake
```powershell
$env:CMAKE_TOOLCHAIN_FILE="C:\vcpkg\scripts\buildsystems\vcpkg.cmake"

# Or set permanently:
[System.Environment]::SetEnvironmentVariable('CMAKE_TOOLCHAIN_FILE', 'C:\vcpkg\scripts\buildsystems\vcpkg.cmake', 'User')
```

---

## Option 2: Pre-built Binaries (Manual)

### libsndfile
1. Download from: http://www.mega-nerd.com/libsndfile/
2. Extract to `C:\libs\libsndfile`
3. Set CMake variable: `-DSNDFILE_ROOT=C:\libs\libsndfile`

### Eigen3
1. Download from: https://eigen.tuxfamily.org/
2. Extract to `C:\libs\eigen3`
3. Set CMake variable: `-DEigen3_DIR=C:\libs\eigen3`

---

## Option 3: Skip Audio File I/O (Testing Only)

Modify CMakeLists.txt to make libsndfile optional:
```cmake
option(VOCAL_ENABLE_FILE_IO "Enable WAV file I/O" OFF)
```

Then work with in-memory audio buffers only (no loading/saving WAV files).

---

## Verification

After installation, verify:
```powershell
# Check if vcpkg installed correctly
C:\vcpkg\vcpkg list libsndfile
C:\vcpkg\vcpkg list eigen3

# Should show:
# libsndfile:x64-windows
# eigen3:x64-windows
```

---

## Build Project

```powershell
cd "E:\Vibe Code\Gaming System\AI Core\vocal-chord-research\cpp-implementation"

mkdir build
cd build

# If using vcpkg:
cmake .. -DCMAKE_TOOLCHAIN_FILE="C:\vcpkg\scripts\buildsystems\vcpkg.cmake" -DCMAKE_BUILD_TYPE=Release

# Or if using manual installs:
cmake .. -DSNDFILE_ROOT="C:\libs\libsndfile" -DEigen3_DIR="C:\libs\eigen3" -DCMAKE_BUILD_TYPE=Release

# Build:
cmake --build . --config Release -j8

# Run tests:
ctest -C Release --output-on-failure
```

---

## Recommended: Option 1 (vcpkg)

**Why**: Automatic dependency management, easy updates, widely used.

**Estimated time**: 10-15 minutes (download + compile)

**Disk space**: ~2 GB for vcpkg + packages

