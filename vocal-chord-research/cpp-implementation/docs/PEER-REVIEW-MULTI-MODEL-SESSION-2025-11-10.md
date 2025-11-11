# PEER REVIEW - MULTI-MODEL SESSION

**Date**: 2025-11-10  
**Primary Coder**: Claude Sonnet 4.5  
**Peer Reviewers**: GPT-5 Pro, GPT-5 Codex, Gemini 2.5 Pro (Story Teller)  
**Components Reviewed**: AberrationParams, FormantFilter (Initial Implementation v1.0)  
**Review Method**: Parallel review by 3 models with different expertise

---

## EXECUTIVE SUMMARY

**Overall Verdict**: **ARCHITECTURE NEEDS SIGNIFICANT REVISION**

All three reviewers identified critical issues that would compromise the system:
- **GPT-5 Pro**: DSP topology unstable, will break under real-time use
- **GPT-5 Codex**: Code quality issues will create maintenance nightmare
- **Gemini 2.5 Pro**: Creative vision not achieved - "digital effects" not "corrupted flesh"

**Positive**: Foundation is solid, approach (raw audio) validated, parameters well-documented  
**Critical**: Filter implementation wrong, missing key creative parameters, code structure fragile

---

## REVIEWER 1: GPT-5 PRO (DSP EXPERT)

**Expertise**: Signal processing theory, real-time audio, numerical stability  
**Verdict**: **FIX** - Critical DSP issues

### CRITICAL ISSUES

1. **Direct Form I Instability**
   - Problem: DF-I numerically fragile for time-varying coefficients
   - Impact: Limit-cycle noise, state blow-ups, denormal sensitivity
   - Solution: Use Transposed Direct Form II (TDF-II) or TPT/SVF

2. **Coefficient Smoothing Method Wrong**
   - Problem: Linear coefficient lerp can temporarily violate stability (|poles| ≥ 1)
   - Impact: Filters blow up during transitions, especially near Nyquist or high Q
   - Solution: Smooth underlying *parameters* (f0, Q, gain) with one-pole filter, THEN recompute coefficients

3. **Real-Time Safety Missing**
   - Problem: No lock-free parameter updates, potential allocations/locks in audio thread
   - Impact: Audio glitches, priority inversion, non-deterministic latency
   - Solution: Lock-free double-buffering with atomic pointer swap at block boundaries

4. **Denormal Handling Insufficient**
   - Problem: Adding DC offset costs CPU, doesn't prevent all denormals
   - Impact: 100x slowdown on denormal values
   - Solution: Enable FTZ/DAZ at audio thread start (_MM_SET_FLUSH_ZERO_MODE/_MM_SET_DENORMALS_ZERO_MODE)

5. **Cascade Stability Not Guaranteed**
   - Problem: 3-5 high-Q peaking stages can clip or blow up
   - Impact: Audio explosions, NaN/Inf propagation
   - Solution: Per-filter and overall makeup gain, soft limiting, NaN detection with state reset

### HIGH PRIORITY

- Filter design: Use BLT with prewarp, not direct Q→alpha
- Coefficient precision: Compute in double, process in float
- Parameter smoothing: Sample-rate aware exponential (alpha = exp(-1/(tau * fs)))
- Bank topology: Series accumulates gain, need normalization
- State management: Crossfade on preset changes (1-3ms)

### MEDIUM PRIORITY

- SIMD optimization: TDF-II with FMA, restrict pointers, SoA layout
- AberrationParams: Lerp in perceptual domain (log Hz, dB, log Q)
- Testing: Stability fuzzer, denormal CPU spike measurement

### Missing for <0.5ms Target

- Stable time-varying topology (TPT/SVF)
- RT-safe parameter pipeline
- FTZ/DAZ enablement
- SIMD across voices
- Headroom management
- Micro-benchmark harness

**Quote**: *"With these changes, <0.5 ms/voice is readily achievable."*

---

## REVIEWER 2: GPT-5 CODEX (CODE QUALITY EXPERT)

**Expertise**: Software engineering, maintainability, API design, C++ best practices  
**Verdict**: **P0 Issues Block Production**

### P0 – STRUCTURAL INSTABILITY

1. **No Type Safety**
   - Problem: 12 raw floats accessed by index/magic strings
   - Impact: Silent breakage when adding parameters, no compile-time validation
   - Solution: Explicit fields, enums, strong typedefs, validation helpers

2. **No RAII**
   - Problem: Raw pointers, manual malloc/free, no copy/move semantics
   - Impact: Memory leaks on exceptions, impossible to reason about lifetime
   - Solution: std::vector/std::array/std::unique_ptr<T[]>

3. **Thread Safety Undefined**
   - Problem: Public member mutations, no immutable snapshots
   - Impact: Race conditions with 1000 voices
   - Solution: Immutable POD "coeff set", atomic handoff (double buffering, std::atomic<std::shared_ptr<>>)

### P1 – API / INTEGRATION FRICTION

- `process()` signature: No view types (span), poor const-ness
- Parameter smoothing: Embedded in filter, can't reuse or bypass
- Error reporting: Asserts only, no Status/expected return

### P2 – MAINTAINABILITY

- Numeric literals scattered (no named constants)
- No unit/perf test scaffolding
- No logging/tracing hooks for debugging

### P3 – PERFORMANCE

- AoS layout (cache-unfriendly for multiple voices)
- Per-sample branches and powf in smoothing
- Hoist invariant math out of loops

### P4 – C++17 VIOLATIONS

- Macros instead of constexpr
- No [[nodiscard]] on functions returning status
- Incomplete namespace hygiene

**Quote**: *"Addressing these raises long-term maintainability, integration safety, and keeps performance headroom for 1000+ voices."*

---

## REVIEWER 3: GEMINI 2.5 PRO / STORY TELLER (CREATIVE VISION)

**Expertise**: Narrative design, horror aesthetics, archetype authenticity  
**Verdict**: **"Leans toward digital effect, not corrupted flesh"**

### CORE INSIGHT

> *"Your current architecture is a sophisticated EQ. A powerful one, to be sure, but it primarily reshapes the existing signal. It carves the marble. Aberration, in its truest form, is not just about reshaping. It's about introducing **rot, chaos, and physicality.** It's about simulating the very things that are breaking within the creature's body. Formant filtering alone is too clean, too predictable. It changes the character of the room the voice is in, but not the decay of the throat that produces it."*

> *"We need to simulate the termites, not just repaint the walls."*

### CRITICAL MISSING PARAMETERS

1. **Glottal Incoherence / "Broken Larynx"** (Zombie)
   - Current: "Breathiness" (too generic)
   - Needed: Stuttering vocal folds, jitter, shimmer, random amplitude modulation
   - Why: Sound of the signal source itself failing, not just filtering

2. **Subharmonic Instability / "Bestial Undercurrent"** (Werewolf)
   - Current: "Growl harmonics" (static layer)
   - Needed: Non-linear effect where F0 periodically/chaotically drops an octave
   - Why: Beast asserting control beneath human voice, dynamic transformation

3. **Unnatural Resonance/Stillness** (Vampire)
   - Current: "Hollow resonance" (reverb-like)
   - Needed: Sharp synthetic resonant peaks OR hyper-stabilized pitch (no vibrato)
   - Why: "Too-perfect" quality, uncanny valley, humanity hollowed out

4. **Corporeal Noise Layers** (All archetypes)
   - Current: Only filtering of anchor audio
   - Needed: **Additive synthesis** - dedicated noise generators triggered by anchor
   - Examples:
     - Wet Clicks & Pops (Zombie mouth sounds)
     - Raspy Inhalation (dry/empty or fluid-filled lungs)
     - Bone Creaks (Werewolf jaw distension)
   - Why: Physical reality of failing bodies, not just tonal coloration

### ARCHETYPE ASSESSMENT

**Current Parameters:**
- Create "generic monster"
- Highly dependent on actor performance
- Effects add "thin veneer"

**What's Needed:**
- Zombie: Voice **fighting against entropy** (mechanical failure, not just texture)
- Werewolf: **Battle between two natures** (dynamic transformation, not static growl)
- Vampire: **Humanity hollowed out** (unnatural control and stillness, not just echo)

### CREATIVE CONSTRAINTS IDENTIFIED

Primary constraint: **"Formant filtering alone is too clean."**

The processing itself needs to embody the archetype's core narrative. We're describing audio effects, not simulating physical realities.

**Quote**: *"To get recognizable archetypes, the processing itself needs to embody their core narrative. A Zombie's voice should sound like it's fighting against entropy. A Werewolf's should sound like a battle between two natures. A Vampire's should sound like humanity has been hollowed out and replaced with something ancient and cold."*

---

## SYNTHESIS: CROSS-CUTTING THEMES

All three reviewers identified a common pattern: **The architecture is incomplete.**

### TECHNICAL (GPT-5 Pro + Codex)
- Foundation exists but implementation details wrong
- Real-time safety not production-ready
- Maintainability will degrade over 8-12 months

### CREATIVE (Story Teller)
- Technical capability insufficient for creative vision
- Missing entire dimension: **additive synthesis** for physical failures
- Formant filtering = necessary but not sufficient

### WHAT WORKS
✅ Raw audio approach validated  
✅ Parameter documentation excellent  
✅ Overall architecture sound  
✅ Direction correct (just needs more depth)

### WHAT NEEDS FIXING
❌ Filter topology (DF-I → TPT/SVF)  
❌ Parameter smoothing (coeffs → params)  
❌ Type safety and RAII  
❌ Real-time safety guarantees  
❌ Missing creative parameters (glottal, subharmonic, noise layers)  

---

## REVISED ARCHITECTURE v2.0 REQUIREMENTS

### TIER 1: CRITICAL (Must Fix Before Continuing)

1. **Replace Direct Form I with TPT/SVF or TDF-II**
   - Numerically stable for time-varying parameters
   - Sample-rate parameter smoothing (not coefficient smoothing)
   - Guaranteed stability across parameter ranges

2. **Implement RT-Safe Parameter Pipeline**
   - Lock-free double buffering
   - Atomic pointer swap at block boundaries
   - No allocations in audio thread
   - FTZ/DAZ enabled at thread start

3. **Add Type Safety and RAII**
   - Strong typedefs for parameters
   - std::array/vector for memory management
   - Proper copy/move/noexcept semantics
   - [[nodiscard]] on error returns

### TIER 2: HIGH PRIORITY (Before Quality Testing)

4. **Add Glottal Incoherence Module** (Zombie)
   - Jitter (pitch irregularity)
   - Shimmer (amplitude irregularity)
   - Non-periodic pulses

5. **Add Subharmonic Generator** (Werewolf)
   - Non-linear F0 modulation
   - Octave-down bursts (controlled chaos)
   - Dynamic blending with clean signal

6. **Add Pitch Stabilization** (Vampire)
   - Remove natural vibrato
   - Hyper-stable F0 tracking
   - Unnaturally controlled resonances

7. **Implement Corporeal Noise Layers**
   - Additive noise synthesis (not just filtering!)
   - Multiple noise types (clicks, pops, rasps, creaks)
   - Triggered/synchronized with anchor audio

### TIER 3: BEFORE PRODUCTION

8. **Benchmarking Infrastructure**
   - Microbenchmark harness
   - Golden render tests
   - Performance regression detection

9. **API Refinement**
   - AudioBlock/span types
   - Status/expected error handling
   - Const correctness throughout

---

## IMPLEMENTATION ROADMAP (REVISED)

### Week 1: Core Architecture Fixes (CRITICAL)
- [ ] Implement TPT/SVF filter topology
- [ ] Parameter smoothing system
- [ ] RT-safe parameter pipeline
- [ ] Type safety refactor
- [ ] FTZ/DAZ support

### Week 2: Creative Parameters (HIGH)
- [ ] Glottal incoherence module
- [ ] Subharmonic generator
- [ ] Pitch stabilization
- [ ] Corporeal noise layers
- [ ] Mid LOD kernel integration

### Week 3: Testing & Validation
- [ ] Benchmark infrastructure
- [ ] Stability testing (parameter sweeps)
- [ ] Story Teller re-review (creative validation)
- [ ] Quality testing with audio samples

### Week 4: Near & Far LOD
- [ ] Near LOD full implementation
- [ ] Far LOD clustering
- [ ] LOD manager
- [ ] Performance optimization

---

## KEY QUOTES

**GPT-5 Pro**: *"With these changes, <0.5 ms/voice is readily achievable."*

**GPT-5 Codex**: *"Addressing these raises long-term maintainability, integration safety, and keeps performance headroom for 1000+ voices."*

**Story Teller**: *"We need to simulate the termites, not just repaint the walls. [...] A Zombie's voice should sound like it's fighting against entropy. A Werewolf's should sound like a battle between two natures. A Vampire's should sound like humanity has been hollowed out and replaced with something ancient and cold."*

---

## CONCLUSION

**Status**: Architecture v1.0 → v2.0 revision required

**Good News**: Foundation is solid, direction validated, issues caught early (not after 1000 hours)

**Critical Work**: ~2 weeks to address CRITICAL + HIGH issues before continuing to full implementation

**Recommendation**: Fix filter topology and creative parameters FIRST, then proceed with confidence

**Next Step**: Implement TPT/SVF filter as replacement for Direct Form I biquad

---

**END OF PEER REVIEW**

This document represents the combined wisdom of:
- GPT-5 Pro (DSP mastery)
- GPT-5 Codex (Engineering excellence)
- Gemini 2.5 Pro / Story Teller (Creative authenticity)

Primary coder (Claude Sonnet 4.5) will implement fixes and re-submit for validation.

