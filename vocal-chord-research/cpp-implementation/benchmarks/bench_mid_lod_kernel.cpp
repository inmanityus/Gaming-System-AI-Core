#include "vocal_synthesis/mid_lod_kernel.hpp"
#include "vocal_synthesis/audio_buffer.hpp"
#include <benchmark/benchmark.h>

using namespace vocal_synthesis;

static void BM_MidLOD_Vampire(benchmark::State& state) {
    MidLODKernel kernel(48000.0f);
    
    // 50ms buffer (2400 samples at 48kHz)
    std::vector<float> input(2400, 0.5f);
    std::vector<float> output(2400);
    
    AberrationParams params = AberrationParams::createVampire();
    
    for (auto _ : state) {
        kernel.process(output.data(), input.data(), params, input.size());
        benchmark::DoNotOptimize(output.data());
        benchmark::ClobberMemory();
    }
    
    // Report microseconds per voice
    state.SetItemsProcessed(state.iterations());
    state.SetLabel("Vampire (50ms)");
}
BENCHMARK(BM_MidLOD_Vampire);

static void BM_MidLOD_Zombie(benchmark::State& state) {
    MidLODKernel kernel(48000.0f);
    
    std::vector<float> input(2400, 0.5f);
    std::vector<float> output(2400);
    
    AberrationParams params = AberrationParams::createZombie();
    
    for (auto _ : state) {
        kernel.process(output.data(), input.data(), params, input.size());
        benchmark::DoNotOptimize(output.data());
        benchmark::ClobberMemory();
    }
    
    state.SetItemsProcessed(state.iterations());
    state.SetLabel("Zombie (50ms)");
}
BENCHMARK(BM_MidLOD_Zombie);

static void BM_MidLOD_Werewolf(benchmark::State& state) {
    MidLODKernel kernel(48000.0f);
    
    std::vector<float> input(2400, 0.5f);
    std::vector<float> output(2400);
    
    AberrationParams params = AberrationParams::createWerewolf();
    
    for (auto _ : state) {
        kernel.process(output.data(), input.data(), params, input.size());
        benchmark::DoNotOptimize(output.data());
        benchmark::ClobberMemory();
    }
    
    state.SetItemsProcessed(state.iterations());
    state.SetLabel("Werewolf (50ms)");
}
BENCHMARK(BM_MidLOD_Werewolf);

// Target: <0.5ms per voice = <500 microseconds
// At 48kHz, 2400 samples = 50ms of audio
// Processing 50ms should take < 500us
// main() provided by benchmark::benchmark_main library

