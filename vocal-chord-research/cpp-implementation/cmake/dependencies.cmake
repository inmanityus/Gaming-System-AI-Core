# Vocal Synthesis Dependencies

# Eigen3 (Linear algebra)
find_package(Eigen3 3.4 QUIET)
if(NOT Eigen3_FOUND)
    message(STATUS "Eigen3 not found, using bundled version")
    include(FetchContent)
    FetchContent_Declare(
        eigen
        GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
        GIT_TAG 3.4.0
    )
    FetchContent_MakeAvailable(eigen)
endif()

# libsndfile (Audio file I/O) - OPTIONAL
if(VOCAL_ENABLE_FILE_IO)
    find_package(SndFile QUIET)
    if(NOT SndFile_FOUND)
        message(STATUS "libsndfile not found, attempting vcpkg or system install")
        find_library(SNDFILE_LIBRARY NAMES sndfile libsndfile)
        find_path(SNDFILE_INCLUDE_DIR sndfile.h)
        
        if(SNDFILE_LIBRARY AND SNDFILE_INCLUDE_DIR)
            add_library(sndfile::sndfile UNKNOWN IMPORTED)
            set_target_properties(sndfile::sndfile PROPERTIES
                IMPORTED_LOCATION "${SNDFILE_LIBRARY}"
                INTERFACE_INCLUDE_DIRECTORIES "${SNDFILE_INCLUDE_DIR}"
            )
        else()
            message(WARNING "libsndfile not found. File I/O will be disabled.")
            set(VOCAL_ENABLE_FILE_IO OFF CACHE BOOL "File I/O disabled" FORCE)
        endif()
    endif()
    
    if(VOCAL_ENABLE_FILE_IO)
        message(STATUS "WAV file I/O enabled (libsndfile)")
    endif()
else()
    message(STATUS "WAV file I/O disabled (build without libsndfile)")
endif()

# Google Test (Testing framework)
if(VOCAL_BUILD_TESTS)
    find_package(GTest QUIET)
    if(NOT GTest_FOUND)
        message(STATUS "GTest not found, fetching from GitHub")
        include(FetchContent)
        FetchContent_Declare(
            googletest
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.14.0
        )
        FetchContent_MakeAvailable(googletest)
    endif()
endif()

# Google Benchmark (Performance testing)
if(VOCAL_BUILD_BENCHMARKS)
    find_package(benchmark QUIET)
    if(NOT benchmark_FOUND)
        message(STATUS "Google Benchmark not found, fetching from GitHub")
        include(FetchContent)
        FetchContent_Declare(
            googlebenchmark
            GIT_REPOSITORY https://github.com/google/benchmark.git
            GIT_TAG v1.8.3
        )
        FetchContent_MakeAvailable(googlebenchmark)
    endif()
endif()

# pybind11 (Python bindings)
if(VOCAL_BUILD_PYTHON_BINDINGS)
    find_package(Python COMPONENTS Interpreter Development QUIET)
    if(NOT Python_FOUND)
        message(WARNING "Python not found - Python bindings disabled")
        set(VOCAL_BUILD_PYTHON_BINDINGS OFF CACHE BOOL "Python bindings disabled" FORCE)
    else()
        find_package(pybind11 QUIET)
        if(NOT pybind11_FOUND)
            message(STATUS "pybind11 not found, fetching from GitHub")
            include(FetchContent)
            FetchContent_Declare(
                pybind11
                GIT_REPOSITORY https://github.com/pybind/pybind11.git
                GIT_TAG v2.13.6
            )
            FetchContent_MakeAvailable(pybind11)
        endif()
    endif()
endif()
