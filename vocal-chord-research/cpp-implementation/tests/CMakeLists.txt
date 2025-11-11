# Tests CMakeLists
include(GoogleTest)

# Test executable
add_executable(vocal_tests
    test_parameter_smoother.cpp
    test_audio_buffer.cpp
    test_rt_parameter_pipeline.cpp
)

target_link_libraries(vocal_tests
    PRIVATE
        vocal_synthesis
        gtest
        gtest_main
)

target_include_directories(vocal_tests
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../include
)

# Discover tests
gtest_discover_tests(vocal_tests)

