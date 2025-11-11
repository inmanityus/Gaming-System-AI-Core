#include "vocal_synthesis/dsp/tpt_svf.hpp"
#include <benchmark/benchmark.h>
#include <vector>

using namespace vocal_synthesis::dsp;

static void BM_TPT_SVF_ProcessBuffer(benchmark::State& state) {
    TPT_SVF filter(48000.0f, TPT_SVF::Mode::BANDPASS);
    filter.setParameters(1000.0f, 5.0f, 0.0f);
    
    std::vector<float> input(2400, 0.5f);
    std::vector<float> output(2400);
    
    for (auto _ : state) {
        filter.processBuffer(output.data(), input.data(), input.size());
        benchmark::DoNotOptimize(output.data());
        benchmark::ClobberMemory();
    }
    
    state.SetItemsProcessed(state.iterations() * input.size());
}
BENCHMARK(BM_TPT_SVF_ProcessBuffer);

static void BM_TPT_FormantBank_3Formants(benchmark::State& state) {
    TPT_FormantBank bank(48000.0f);
    
    TPT_FormantBank::Formant formants[3] = {
        {800.0f, 80.0f, 1.0f},
        {1200.0f, 100.0f, 1.0f},
        {2500.0f, 120.0f, 1.0f}
    };
    bank.setFormants(formants, 3);
    
    std::vector<float> input(2400, 0.5f);
    std::vector<float> output(2400);
    
    for (auto _ : state) {
        bank.processBuffer(output.data(), input.data(), input.size());
        benchmark::DoNotOptimize(output.data());
        benchmark::ClobberMemory();
    }
    
    state.SetItemsProcessed(state.iterations() * input.size());
}
BENCHMARK(BM_TPT_FormantBank_3Formants);

// main() provided by benchmark::benchmark_main library

