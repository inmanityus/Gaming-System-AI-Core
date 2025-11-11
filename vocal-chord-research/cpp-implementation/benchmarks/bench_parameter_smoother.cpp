#include "vocal_synthesis/dsp/parameter_smoother.hpp"
#include <benchmark/benchmark.h>

using namespace vocal_synthesis::dsp;

static void BM_ParameterSmoother_ProcessSample(benchmark::State& state) {
    ParameterSmoother smoother(48000.0f, 5.0f);
    smoother.setTarget(1.0f);
    
    for (auto _ : state) {
        float value = smoother.processSample();
        benchmark::DoNotOptimize(value);
    }
    
    state.SetItemsProcessed(state.iterations());
}
BENCHMARK(BM_ParameterSmoother_ProcessSample);

static void BM_ParameterSmoother_ProcessBuffer(benchmark::State& state) {
    ParameterSmoother smoother(48000.0f, 5.0f);
    smoother.setTarget(1.0f);
    
    std::vector<float> buffer(2400);
    
    for (auto _ : state) {
        smoother.processBuffer(buffer.data(), buffer.size());
        benchmark::DoNotOptimize(buffer.data());
        benchmark::ClobberMemory();
    }
    
    state.SetItemsProcessed(state.iterations() * 2400);
}
BENCHMARK(BM_ParameterSmoother_ProcessBuffer);

// main() provided by benchmark::benchmark_main library

