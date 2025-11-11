# PEER REVIEW: Technical Specifications v1.0

**Reviewer**: GPT-5 Pro (OpenRouter)  
**Review Date**: 2025-11-09  
**Specifications Version**: 1.0  
**Overall Assessment**: **VIABLE with CRITICAL GAPS** - Addressable but requires specification updates

---

## EXECUTIVE SUMMARY

**Verdict**: The concept is viable if:
1. Far-LOD synthesis collapses into 12-24 crowd buses (not 840 independent synths)
2. Vectorization across voices with SoA layout
3. Real-time constraints and platform targets are defined
4. DSP stability details are specified

**Major Risks Identified**:
- Missing platform plan beyond AVX2
- Lack of real-time-safe scheduling/allocators
- Unclear Anchor→Aberration feature interface
- Undefined crowd-bus algorithm for Far LOD
- No hard acceptance thresholds (cycles/sample, buffer size, underrun rate, MOS method)

**Critical Finding**: "<1 ms latency per voice" is ambiguous - likely means algorithmic delay, NOT CPU time per voice (which would be impossible for 1000+ voices).

---

## 1. ARCHITECTURE ISSUES & GAPS

### 1.1 Unclear Anchor→Aberration Interface

**Problem**: Missing definition of what Anchor produces

**Current State**: Specs say "audio" but don't define format

**Required**:
```
Anchor Feature Envelope (per-utterance binary):
- Control rate: 240 Hz (aligned, SoA frames)
- Phonemes with durations
- F0 contour (fundamental frequency)
- Energy envelope
- 24-40 Bark-cepstra or LPC coefficients
- V/UV flag (voiced/unvoiced)
- Noise mix ratio
- Prosody tags
- Quantization: 16-bit or mixed-precision
```

**Action**: Define this format in specs v2.0

---

### 1.2 Aberration Transform Under-Specified

**Problem**: Missing DSP kernels and LOD-specific models

**Required**:
```
Three LOD Kernels:

Near LOD:
- LF glottal source (Liljencrants-Fant model)
- Time-varying IIR vocal tract filters
- Stable parameterization (pole radii/angles, NOT raw a/z coefficients)
- Per-sample coefficient interpolation
- Anti-zipper smoothing
- Nasal branches
- Lip radiation filter

Mid LOD:
- Simplified 3-5 formant bandpass stack OR AR filter
- Shaped noise for fricatives
- Optional simple nasal zero
- Reduced computational cost

Far LOD:
- Crowd synthesis (granular/noise-band resynthesis)
- Driven by clustered feature envelopes
- NO per-agent sample-rate synthesis
- 12-24 cluster buses maximum
```

**Action**: Specify all three kernels with mathematical models

---

### 1.3 Missing Voice Manager & LOD Orchestrator

**Problem**: No central system for voice allocation, LOD migration, crossfading

**Required**:
```cpp
class VoiceManager {
    // Real-time safe voice scheduler
    - Predictive LOD assignment per tick (distance, occlusion, importance)
    - Sample-accurate crossfades when switching LODs
    - Hard caps: Near ≤32, Mid ≤128, Far aggregated into 12-24 buses
    - Voice stealing under load
    - Lock-free communication with audio thread
};
```

**Action**: Add to specs v2.0 as core component

---

### 1.4 Real-Time Graph & Memory Model Not Defined

**Problem**: No specification of real-time safe memory management

**Required**:
```
Fixed, Pre-allocated DSP Graph:
- Lock-free FIFOs between:
  - Game thread → Audio control thread → Audio render callback
- Real-time safe pools for per-voice states
- NO allocations/deallocations in audio callback
- Pre-allocated memory at level load
```

**Action**: Add real-time safety specifications

---

### 1.5 Platform Portability Gap

**Problem**: AVX-512 is rare and downclocks; ARM Neon missing; console requirements undefined

**Required**:
```
SIMD Strategy:
- Use ISPC or vector back-end abstraction
- Support: AVX2 (baseline), SSE4.1 (fallback), Neon (ARM/Switch)
- AVX-512: Opt-in only with downclock mitigation
- Runtime CPU detection and dispatch
```

**Action**: Revise SIMD section with portable strategy

---

### 1.6 Content Pipeline Gap

**Problem**: No plan for cooking Anchor features into UE assets

**Required**:
```
UE Asset Pipeline:
- Custom UAsset type: UAnchorFeatureEnvelope
- Cooking rules (compression, quantization)
- Streaming chunks for large dialogues
- Deterministic hash/versioning scheme
- Cross-platform consistency
```

**Action**: Add UE5 content pipeline specifications

---

### 1.7 Determinism & Stability

**Problem**: No guarantee against IIR instability, denormals, zipper noise

**Required**:
```
Stability Safeguards:
- Enable FTZ/DAZ (flush-to-zero, denormals-are-zero)
- Parameterize filters via stable transforms
- Constrain coefficient interpolation rates
- Add denormal guards (tiny DC offset or noise floor)
- Test for stability bounds across parameter ranges
```

**Action**: Add stability section to specs

---

## 2. PERFORMANCE CONCERNS

### 2.1 Ambiguous Latency Requirement

**Problem**: "<1 ms latency per voice" could mean CPU time OR algorithmic delay

**Clarification Needed**:
```
Algorithmic Latency (pipeline delay):
- Near LOD: ≤64 samples at 48kHz (1.33ms)
- Mid LOD: ≤128-256 samples
- Far LOD: Not latency-critical (clustered)

CPU Budget (per 128-sample buffer at 48kHz):
- Total: ≤70% of buffer time (≤1.9ms at 48kHz)
- Near: ≤20µs per voice × 32 = 0.64ms
- Mid: ≤5µs per voice × 128 = 0.64ms
- Far: ≤10µs per bus × 16 = 0.16ms
- Mixer/overhead: ≤0.35ms
- Total: 1.79ms (fits in 2.67ms buffer)
```

**Action**: Replace ambiguous requirement with precise budgets

---

### 2.2 Far LOD Must Be Collapsed

**CRITICAL**: 840 independent synths cannot run per-sample in 2.67ms buffers

**Solution**:
```
Spatial/Attribute Clustering:
- Group agents by position, F0, phoneme
- 12-24 cluster buses total
- One crowd synth per cluster
- Per-agent contributes amplitude/pan as control-rate events only
- Clustering updated at 10-20Hz (not per-sample)
```

**Action**: Rewrite Far LOD as cluster-based crowd synthesis

---

### 2.3 Concrete Per-Buffer Budgets

**Required Targets** (48kHz, 128-sample buffer):

| LOD | Budget | Count | Total |
|-----|---------|-------|-------|
| Near | 20µs/voice/buffer | 32 | 0.64ms |
| Mid | 5µs/voice/buffer | 128 | 0.64ms |
| Far | 10µs/bus/buffer | 16 | 0.16ms |
| Mixer | - | - | 0.35ms |
| **Total** | - | - | **1.79ms** |

**Target**: ≤70% of 2.67ms buffer time

**Action**: Codify these budgets in specs

---

### 2.4 Data Layout & Vectorization

**Requirements**:
```
SoA (Structure-of-Arrays) Layout:
- Per-kernel buffers
- Batch voices in 8/16 SIMD lanes
- Block process 64-128 samples
- Avoid per-voice branches
- Use FMA (fused multiply-add)
- Precompute tables for nonlinearities
- Keep hot coefficient paths in L1 cache
```

**Action**: Add SoA layout specifications with examples

---

### 2.5 Scheduling Strategy

**Required**:
```
Multi-threaded Scheduling:
- Pre-render Mid/Far blocks on worker threads
- One buffer ahead into ring buffers
- Keep Near on render thread (lowest latency)
- Lock-free communication
```

**Action**: Add threading architecture to specs

---

### 2.6 AVX-512 Risk

**Problem**: Downclocks on desktop CPUs; not available on consoles

**Recommendation**:
- Prefer AVX2 baseline
- Expose runtime dispatch
- Measure perf/thermals before committing
- Do NOT require AVX-512

**Action**: Downgrade AVX-512 to optional

---

### 2.7 Denormals, Cache, Branch Hazards

**Requirements**:
```
Performance Safeguards:
- FTZ/DAZ on startup
- Add tiny DC offset or noise floor
- Keep per-voice hot state compact (<4KB)
- Fits in L1 cache when batched
- Minimize branches in hot loops
```

**Action**: Add to optimization section

---

## 3. MISSING TECHNICAL DETAILS

### 3.1 DSP Specifics

**Missing**:
- Sample rate(s): 48kHz baseline, others?
- Buffer sizes: 64/128/256?
- Control rate: 240Hz?
- Oversampling strategy for glottal source
- Antialiasing filters
- Filter topology details
- Stability constraints
- V/UV handling
- Fricative noise synthesis
- Coarticulation smoothing
- LOD transition crossfade times
- Resynthesis alignment

**Action**: Add complete DSP specification section

---

### 3.2 Quality Definition

**Missing**:
- Which MOS method? (MUSHRA, ACR, DCR?)
- Target devices for testing
- Anchors for comparison
- Objective metrics (ViSQOL/PESQ/POLQA) thresholds
- Listener count for subjective tests

**Action**: Define complete quality evaluation methodology

---

### 3.3 Platform Targets

**Missing**:
- CPU SKUs (Intel, AMD generations)
- Consoles (PS5, Xbox Series X/S)
- Minimum instruction sets per platform
- GPU offload policy (if any)
- Mobile/Switch targets

**Action**: List supported platforms with requirements

---

### 3.4 Spatialization/Occlusion

**Missing**:
- Which UE spatializer integration
- Per-LOD spatialization choices
- HRTF costs in budget
- Occlusion pipeline
- Distance attenuation

**Action**: Add spatialization specifications

---

### 3.5 Memory Budgets

**Missing**:
- Per-voice state sizes
- Anchor feature memory per minute
- Streaming windows
- Total memory cap
- Fragmentation mitigation

**Action**: Add memory budget section

---

### 3.6 Content Pipeline

**Missing**:
- Tools to generate Anchor features
- Versioning scheme
- Re-cooking workflow
- Determinism across OS/compilers
- Asset compression

**Action**: Add content pipeline documentation

---

### 3.7 Telemetry

**Missing**:
- Real-time counters:
  - Buffer underruns
  - µs/buffer per kernel
  - Active voices per LOD
  - Voice steals
  - FTZ/DAZ status
  - Memory allocation failures
- Performance dashboards
- Logging strategy

**Action**: Add telemetry specifications

---

### 3.8 Failure/Degrade Modes

**Missing**:
- What drops first under load?
- Voice stealing strategy
- LOD demotion policy
- Muting strategy
- Graceful degradation

**Action**: Add load shedding specifications

---

## 4. INTEGRATION CHALLENGES

### 4.1 UE5 Audio Threading Model

**Critical**: Audio render callback is real-time; NO locks/allocations allowed

**Required**:
```
Split Plugin Architecture:
1. Game Thread Component
   - Control events
   - Parameter updates
   - Voice spawn/despawn

2. Audio Render Component
   - Pre-allocated pools
   - Lock-free queues
   - Real-time safe operations

3. Worker Job System
   - Pre-render Mid/Far blocks
   - Off render thread
```

**Action**: Add UE5 threading architecture diagram

---

### 4.2 UE Asset Pipeline

**Required**:
```
Custom UE Asset Type:
- UAnchorFeatureEnvelope
- Cooker integration
- Async streaming
- Platform compression
- Versioning
```

**Action**: Add UE asset specifications

---

### 4.3 UE Audio Mixer Integration

**Required**:
```
Integration Points:
- Near LOD: SourceEffect or custom Source generator
- Mid LOD: Lighter SourceEffect
- Far LOD: SubmixEffect "Crowd Synth"
  - Fed by clusters of agents
  - Control messages (not audio streams)
```

**Action**: Add integration architecture

---

### 4.4 Spatialization & Submix Routing

**Required**:
```
Routing Strategy:
- Near/Mid: Through regular spatializer
- Far: Through 1-few spatialized submixes with spread
- Document RTPCs (real-time parameter controls)
- Distance/panning automation
```

**Action**: Add audio routing diagram

---

### 4.5 Cross-Language Boundary

**Clarification**:
- Python via pybind11: TOOLING ONLY, not runtime
- Runtime plugin: Pure C++
- Python wheels: Per platform for editor tools
- GIL released for heavy ops

**Action**: Clarify Python is for tools, not game runtime

---

### 4.6 Build & SIMD Dispatch

**Required**:
```
Build System:
- CMake + UE Build.cs
- Runtime CPU feature detection
- Build variants: AVX2, SSE4.1, Neon
- No hard AVX-512 dependency
```

**Action**: Update build specifications

---

### 4.7 Console Cert & Determinism

**Required**:
```
Console Requirements:
- Remove ALL dynamic allocations in audio callback
- Implement watchdog logs (disabled in shipping)
- Ensure NO file I/O on audio threads
- Pass platform cert requirements
```

**Action**: Add console compliance section

---

## 5. TESTING STRATEGY GAPS

### 5.1 Define Acceptance Criteria

**Required**:
```
Hard Acceptance Thresholds:
- Audio underruns: 0 in 30-minute soak per target device
- Performance: Meet µs/buffer budgets above
- MOS: Near ≥4.0 on MUSHRA with 24 listeners
- ViSQOL: ≥3.8 vs anchors
- Intelligibility: ≥95% word accuracy
```

**Action**: Codify acceptance criteria

---

### 5.2 Automated DSP Correctness

**Required**:
```
Golden Reference Tests:
- Per-voice and per-LOD renders
- Tolerance-based spectral/level comparisons
- Property-based tests for parameter ranges
- Regression tests on check-in
```

**Action**: Add DSP test specifications

---

### 5.3 Stability/Fuzzing

**Required**:
```
Stability Tests:
- Randomized parameter sweeps within bounds
- Catch IIR instability and denormals
- Long soak tests (8-24 hours)
- No NaN/Inf/DC buildup
```

**Action**: Add stability test plan

---

### 5.4 Concurrency Tests

**Required**:
```
Scale Tests:
- 1000-agent scene in UE5
- Scripted LOD churn
- Occlusion changes
- Spawn/despawn storms
- Measure underruns and performance
```

**Action**: Create 1000-agent test level specification

---

### 5.5 Platform CI

**Required**:
```
Continuous Integration:
- Windows (AVX2)
- Linux
- PS5/XSX devkits
- ARM Neon target
- Capture counters and flamegraphs
- Automated perf regression detection
```

**Action**: Set up CI pipeline

---

### 5.6 Audio Glitch Detector

**Required**:
```
Real-time Detection:
- NaN/Inf in audio stream
- DC buildup (>-40dB)
- Clips (>0dBFS)
- Gate changes on alarms
```

**Action**: Implement glitch detector

---

### 5.7 Load-Shedding Tests

**Required**:
```
Validate:
- LOD demotion produces no clicks (crossfade works)
- Voice stealing is inaudible
- Degraded quality remains intelligible
- System recovers from overload
```

**Action**: Create load-shedding test scenarios

---

## 6. PRODUCTION READINESS CONCERNS

### 6.1 Ambiguous Latency Requirement

**Issue**: Specs say "<1ms per voice" but this is impossible for CPU time

**Fix**: Clarify as algorithmic latency, define CPU budgets

**Status**: CRITICAL - Must fix before implementation

---

### 6.2 Missing Degrade Strategy

**Issue**: Without explicit load shedding, worst-case spikes will underrun

**Fix**: Add governor that reduces Near→Mid and Mid→Far within 1-2 buffers when µs/buffer exceeds target

**Status**: CRITICAL - Will cause audio glitches without this

---

### 6.3 AVX-512 Dependency Risk

**Issue**: Cannot require AVX-512; must perform on AVX2 and Neon

**Fix**: Make AVX-512 optional, verify perf on AVX2 baseline

**Status**: HIGH - Console compatibility at risk

---

### 6.4 Content Rights & "Zero Ongoing Costs"

**Issue**: Verify TTS/vocoder licenses and voice IP rights

**Fix**: Review all TTS options for commercial use rights

**Status**: MEDIUM - Legal/financial risk

---

### 6.5 Memory Fragmentation/RT Safety

**Issue**: Specs don't guarantee real-time safe memory management

**Fix**: Introduce fixed-size pools and arenas initialized at level load; avoid vector growth in callback

**Status**: CRITICAL - Will cause stalls/crashes without this

---

### 6.6 LOD Transition Artifacts

**Issue**: Without sample-accurate phase alignment, switching Near↔Mid will click/phase

**Fix**: Implement phase-consistent crossfades and parameter interpolation

**Status**: HIGH - User experience impact

---

### 6.7 Telemetry & Tooling

**Issue**: Lack of profiler/visualizer will hinder tuning

**Fix**: Ship in-editor dashboard:
- Voice counts per LOD
- Per-kernel µs
- Underruns
- Cluster sizes
- FTZ/DAZ status

**Status**: HIGH - Development velocity impact

---

## 7. CRITICAL RECOMMENDATIONS

### Priority 1 (MUST HAVE for v2.0 specs)

1. **Define Hard Real-time Budgets**
   - Lock in: sample rate (48kHz), buffer sizes (64/128/256), per-buffer µs targets
   - Instrument from day 1

2. **Specify Anchor Feature Envelope**
   - F0, energy, 24-40 Bark cepstra or LPC, V/UV, phoneme timings, prosody
   - Quantized, stored as UE asset with cooker and streaming

3. **Implement Three LOD DSP Kernels**
   - Near: LF source + stable time-varying tract filters
   - Mid: 3-5 formants + noise
   - Far: Crowd synth with 12-24 cluster buses
   - Include denormal fixes and coefficient interpolation

4. **Build Voice Manager & LOD Governor**
   - Real-time safe scheduler
   - Crossfade transitions
   - Voice stealing
   - Feedback control to keep audio work ≤70% buffer time

5. **Collapse Far LOD into Clusters**
   - Spatial/attribute clustering (k-means or grid-based)
   - Updated at 10-20Hz
   - Per-cluster resynthesis
   - Agents contribute control-rate gains/pans only

### Priority 2 (SHOULD HAVE for production)

6. **Adopt Portable SIMD Strategy**
   - ISPC or custom SIMD back-end
   - Support AVX2/SSE4.1/Neon
   - Avoid relying on AVX-512
   - Runtime CPU dispatch
   - Per-platform perf tests

7. **Establish Stability & Quality Safeguards**
   - FTZ/DAZ
   - Stable filter parameterization
   - Anti-zipper smoothing
   - Objective (ViSQOL) and subjective (MUSHRA) quality gates in CI

8. **Make UE5 Plugin Real-time Safe**
   - No allocations/locks in render
   - Lock-free queues
   - Pre-allocated pools
   - Split game/control/render components
   - Integrate as Source/SourceEffect/SubmixEffect

### Priority 3 (NICE TO HAVE for robustness)

9. **Create Robust Perf & Soak Tests**
   - 1000-agent UE test level
   - Scripted LOD churn
   - 8-hour soaks
   - Collect underruns and µs/buffer histograms per kernel and platform

10. **Document Platform Targets & Fallbacks**
    - Windows/Linux + PS5/XSX + at least one ARM Neon system
    - List instruction sets, expected perf, feature flags, fallback quality levels

---

## 8. CONCRETE NEXT STEPS (2-4 Weeks)

### Week 1: Foundations
- [ ] Finalize budgets (sample rate, buffer size, µs targets)
- [ ] Design Anchor Feature Envelope format
- [ ] Choose SIMD strategy (ISPC vs custom)
- [ ] Set up perf telemetry
- [ ] Enable FTZ/DAZ
- [ ] Implement fixed-size pools and lock-free queues

### Week 2: Mid LOD Prototype
- [ ] Prototype Mid LOD kernel with SoA and SIMD
- [ ] Integrate as UE SourceEffect
- [ ] Microbench per-voice µs/buffer
- [ ] Build 1000-agent UE test level
- [ ] Verify perf targets

### Week 3: Far LOD & Clustering
- [ ] Implement Far crowd synth
- [ ] Implement clustering algorithm
- [ ] Hit perf targets by collapsing 840 agents to ≤16 buses
- [ ] Add LOD governor
- [ ] Implement LOD transitions with crossfades

### Week 4: Near LOD & Quality
- [ ] Implement Near LOD kernel
- [ ] Add stability guards (anti-zipper, denormal fixes)
- [ ] Run MUSHRA/ViSQOL on small corpus
- [ ] Run overnight soak tests
- [ ] Adjust parameters based on results

---

## CONCLUSION

**Overall Assessment**: The architecture is **viable but requires critical updates** before implementation.

**Key Takeaway**: If you deliver the Priority 1 items above, the architecture becomes sound, the 60fps/1000 agents goal is feasible on AVX2-class CPUs, and you have a credible path to MOS ≥4.0 with zero ongoing costs.

**Risk Level**: MODERATE → LOW (after addressing Priority 1 items)

**Recommendation**: **PROCEED** with specifications v2.0 incorporating this feedback

---

**Peer Review Complete**  
**Reviewer**: GPT-5 Pro  
**Date**: 2025-11-09  
**Next Action**: Create Technical Specifications v2.0

