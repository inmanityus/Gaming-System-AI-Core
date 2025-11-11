# Vocal Synthesis System - CMake Build Configuration
# Version: 1.0.0
# Date: 2025-11-09

cmake_minimum_required(VERSION 3.20)
project(VocalSynthesis 
    VERSION 1.0.0
    DESCRIPTION "Physical Vocal Tract Emulation for Game Audio"
    LANGUAGES CXX
)

# C++ Standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build Options
option(VOCAL_BUILD_TESTS "Build unit and integration tests" ON)
option(VOCAL_BUILD_BENCHMARKS "Build performance benchmarks" ON)
option(VOCAL_BUILD_PYTHON_BINDINGS "Build Python bindings via pybind11" OFF)
option(VOCAL_ENABLE_SIMD "Enable SIMD optimizations (AVX2/SSE4.1/Neon)" ON)
option(VOCAL_ENABLE_GPU "Enable GPU acceleration (CUDA)" OFF)
option(VOCAL_BUILD_SHARED "Build shared library" OFF)
option(VOCAL_ENABLE_FILE_IO "Enable WAV file I/O (requires libsndfile)" OFF)

# Platform Detection
if(WIN32)
    set(VOCAL_PLATFORM "Windows")
elseif(UNIX AND NOT APPLE)
    set(VOCAL_PLATFORM "Linux")
elseif(APPLE)
    set(VOCAL_PLATFORM "macOS")
else()
    set(VOCAL_PLATFORM "Unknown")
endif()

message(STATUS "Building for platform: ${VOCAL_PLATFORM}")

# Compiler Warnings
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# SIMD Configuration
if(VOCAL_ENABLE_SIMD)
    message(STATUS "SIMD optimizations enabled")
    
    # Runtime SIMD dispatch - build multiple variants
    if(MSVC)
        # AVX2 target
        add_compile_options(/arch:AVX2)
    else()
        # GCC/Clang
        add_compile_options(-mavx2 -mfma)
        
        # Also support SSE4.1 fallback
        set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -msse4.1")
        
        # ARM Neon support (for ARM64/Switch)
        if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64|ARM64")
            add_compile_options(-march=armv8-a+simd)
        endif()
    endif()
else()
    message(STATUS "SIMD optimizations disabled")
endif()

# Dependencies
include(cmake/dependencies.cmake)

# Main Library
set(VOCAL_SOURCES
    # Core
    src/core/audio_buffer.cpp
    src/core/aberration_params_v2.cpp
    src/core/mid_lod_kernel.cpp
    
    # DSP
    src/dsp/tpt_svf.cpp
    src/dsp/subliminal_audio.cpp
    src/dsp/parameter_smoother.cpp
    src/dsp/denormal_handling.cpp
    src/dsp/breathiness.cpp
    src/dsp/roughness.cpp
    src/dsp/glottal_incoherence.cpp
    src/dsp/subharmonic_generator.cpp
    src/dsp/pitch_stabilizer.cpp
    src/dsp/corporeal_noise.cpp
)

set(VOCAL_HEADERS
    include/vocal_synthesis/audio_buffer.hpp
    include/vocal_synthesis/types.hpp
    include/vocal_synthesis/aberration_params_v2.hpp
    include/vocal_synthesis/mid_lod_kernel.hpp
    include/vocal_synthesis/types/strong_types.hpp
    include/vocal_synthesis/dsp/tpt_svf.hpp
    include/vocal_synthesis/dsp/parameter_smoother.hpp
    include/vocal_synthesis/dsp/denormal_handling.hpp
    include/vocal_synthesis/dsp/breathiness.hpp
    include/vocal_synthesis/dsp/roughness.hpp
    include/vocal_synthesis/dsp/glottal_incoherence.hpp
    include/vocal_synthesis/dsp/subharmonic_generator.hpp
    include/vocal_synthesis/dsp/pitch_stabilizer.hpp
    include/vocal_synthesis/dsp/corporeal_noise.hpp
    include/vocal_synthesis/rt_safe/parameter_pipeline.hpp
)

# Build library
if(VOCAL_BUILD_SHARED)
    add_library(vocal_synthesis SHARED ${VOCAL_SOURCES} ${VOCAL_HEADERS})
else()
    add_library(vocal_synthesis STATIC ${VOCAL_SOURCES} ${VOCAL_HEADERS})
endif()

# Include directories
target_include_directories(vocal_synthesis 
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Link dependencies
target_link_libraries(vocal_synthesis
    PUBLIC
        Eigen3::Eigen
)

if(VOCAL_ENABLE_FILE_IO)
    target_link_libraries(vocal_synthesis PRIVATE sndfile::sndfile)
    target_compile_definitions(vocal_synthesis PUBLIC VOCAL_ENABLE_FILE_IO)
endif()

# GPU Support
if(VOCAL_ENABLE_GPU)
    find_package(CUDA 12.0 REQUIRED)
    target_link_libraries(vocal_synthesis PRIVATE ${CUDA_LIBRARIES})
    target_compile_definitions(vocal_synthesis PRIVATE VOCAL_ENABLE_GPU)
endif()

# Platform-specific libraries
if(WIN32)
    target_link_libraries(vocal_synthesis PRIVATE winmm)
elseif(UNIX)
    target_link_libraries(vocal_synthesis PRIVATE pthread)
endif()

# Compile definitions
target_compile_definitions(vocal_synthesis
    PRIVATE
        VOCAL_VERSION_MAJOR=${PROJECT_VERSION_MAJOR}
        VOCAL_VERSION_MINOR=${PROJECT_VERSION_MINOR}
        VOCAL_VERSION_PATCH=${PROJECT_VERSION_PATCH}
)

if(VOCAL_ENABLE_SIMD)
    target_compile_definitions(vocal_synthesis PUBLIC VOCAL_ENABLE_SIMD)
endif()

# Apply fast-math ONLY to vocal_synthesis library (not to test dependencies)
# This enables FTZ/DAZ (flush-to-zero, denormals-are-zero) for audio performance
if(MSVC)
    target_compile_options(vocal_synthesis PRIVATE /fp:fast)
else()
    target_compile_options(vocal_synthesis PRIVATE -ffast-math)
endif()

# Python Bindings
if(VOCAL_BUILD_PYTHON_BINDINGS)
    find_package(pybind11 REQUIRED)
    
    pybind11_add_module(vocal_synthesis_py
        bindings/python/vocal_synthesis.cpp
    )
    
    target_link_libraries(vocal_synthesis_py PRIVATE vocal_synthesis)
    
    # Install Python module
    install(TARGETS vocal_synthesis_py
        LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/python
    )
endif()

# Tests
if(VOCAL_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Benchmarks
if(VOCAL_BUILD_BENCHMARKS)
    add_subdirectory(benchmarks)
endif()

# Installation
install(TARGETS vocal_synthesis
    EXPORT VocalSynthesisTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    INCLUDES DESTINATION include
)

install(DIRECTORY include/vocal_synthesis
    DESTINATION include
    FILES_MATCHING PATTERN "*.hpp"
)

# Export targets
install(EXPORT VocalSynthesisTargets
    FILE VocalSynthesisTargets.cmake
    NAMESPACE VocalSynthesis::
    DESTINATION lib/cmake/VocalSynthesis
)

# Package configuration
include(CMakePackageConfigHelpers)

configure_package_config_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/VocalSynthesisConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/VocalSynthesisConfig.cmake"
    INSTALL_DESTINATION lib/cmake/VocalSynthesis
)

write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/VocalSynthesisConfigVersion.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/VocalSynthesisConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/VocalSynthesisConfigVersion.cmake"
    DESTINATION lib/cmake/VocalSynthesis
)

# Summary
message(STATUS "")
message(STATUS "Vocal Synthesis Build Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Platform: ${VOCAL_PLATFORM}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Shared Library: ${VOCAL_BUILD_SHARED}")
message(STATUS "  SIMD: ${VOCAL_ENABLE_SIMD}")
message(STATUS "  GPU: ${VOCAL_ENABLE_GPU}")
message(STATUS "  Tests: ${VOCAL_BUILD_TESTS}")
message(STATUS "  Benchmarks: ${VOCAL_BUILD_BENCHMARKS}")
message(STATUS "  Python Bindings: ${VOCAL_BUILD_PYTHON_BINDINGS}")
message(STATUS "")

