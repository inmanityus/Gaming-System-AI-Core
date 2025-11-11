# Benchmarks CMakeLists

add_executable(vocal_benchmarks
    bench_tpt_svf.cpp
    bench_parameter_smoother.cpp
    bench_mid_lod_kernel.cpp
)

target_link_libraries(vocal_benchmarks
    PRIVATE
        vocal_synthesis
        benchmark::benchmark
        benchmark::benchmark_main
)

target_include_directories(vocal_benchmarks
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../include
)

