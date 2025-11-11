# Build Instructions

## Prerequisites

### Windows
```powershell
# Install vcpkg (C++ package manager)
git clone https://github.com/Microsoft/vcpkg.git
.\vcpkg\bootstrap-vcpkg.bat

# Install dependencies
.\vcpkg\vcpkg install libsndfile:x64-windows eigen3:x64-windows gtest:x64-windows benchmark:x64-windows

# Set CMake toolchain
$env:CMAKE_TOOLCHAIN_FILE="path\to\vcpkg\scripts\buildsystems\vcpkg.cmake"
```

### Linux
```bash
sudo apt install libsndfile1-dev libeigen3-dev libgtest-dev libbenchmark-dev cmake build-essential
```

## Build

```bash
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j8
```

## Run Tests

```bash
cd build
ctest --output-on-failure
```

## Run Benchmarks

```bash
cd build
./benchmarks/vocal_benchmarks
```

## Expected Test Results

- 67 tests total
- 100% pass rate required
- All tests < 1 second execution

## Performance Targets

Mid LOD: <0.5ms per voice (500 microseconds)
- Vampire: <400us
- Zombie: <500us  
- Werewolf: <500us

