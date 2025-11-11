# VOCAL CHORD EMULATION - PHASE 2 IMPLEMENTATION ROADMAP

**Document Version**: 1.0  
**Date**: 2025-11-09  
**Based On**: Research Phase completion + GPT-5 Pro peer review  
**Timeline**: 8-12 months with engineering team  
**Status**: READY TO BEGIN

---

## EXECUTIVE SUMMARY

**Phase 1 (Research)**: ✅ **COMPLETE**
- Multi-model feasibility confirmed (4 AI models)
- 3 working prototypes validated
- Decision: PROCEED with 95% confidence
- Critical peer review completed (GPT-5 Pro)

**Phase 2 (Core Implementation)**: **READY TO BEGIN**
- Timeline: 8-12 months
- Team: 5-8 engineers (DSP, engine, integration)
- Budget: ~$200K development, $0 ongoing
- Approach: Anchor & Aberration + Spectral Seed

---

## CRITICAL FINDINGS FROM PEER REVIEW (GPT-5 Pro)

### What Changed After Peer Review

**Original Plan**: 
- Simple "<1ms per voice" latency
- 840 independent Far LOD voices
- AVX-512 optimization

**Updated Plan** (incorporating feedback):
- **Precise budgets**: 20µs/voice (Near), 5µs/voice (Mid), 10µs/bus (Far)
- **Collapsed Far LOD**: 12-24 cluster buses (not 840 independent synths)
- **Portable SIMD**: AVX2 baseline, Neon for ARM, AVX-512 optional only
- **Real-time safety**: Lock-free, pre-allocated, no allocs in audio callback
- **Anchor Feature Envelope**: Defined format (F0, cepstra, phonemes, prosody)

**Risk Assessment**: MODERATE → LOW (after addressing peer review items)

---

## PHASE 2 TIMELINE & MILESTONES

### Month 1-2: Foundations (Weeks 1-8)

**Week 1-2: Platform & Architecture Setup**
- [ ] Finalize performance budgets
  - Sample rate: 48kHz
  - Buffer sizes: Near=64, Mid/Far=128 samples
  - CPU targets: 20µs/voice (Near), 5µs/voice (Mid), 10µs/bus (Far)
- [ ] Design Anchor Feature Envelope format
  - F0 contour (240Hz control rate)
  - 24-40 Bark cepstra
  - Phoneme timings
  - V/UV flags
  - Prosody tags
- [ ] Choose SIMD strategy
  - ISPC vs custom abstraction
  - Support AVX2, SSE4.1, Neon
  - Runtime CPU dispatch
- [ ] Set up performance telemetry
  - Real-time counters (µs/buffer, underruns, voice counts)
  - In-editor dashboard
  - Logging infrastructure
- [ ] Enable FTZ/DAZ (flush-to-zero, denormals-are-zero)
- [ ] Implement fixed-size memory pools
- [ ] Implement lock-free queues (game → audio threads)

**Deliverables**:
- Platform requirements document
- Anchor Feature Envelope specification
- SIMD abstraction layer
- Real-time memory management system
- Telemetry framework

**Team**: 2 senior engineers + 1 architect

---

**Week 3-4: Mid LOD Prototype**
- [ ] Implement Mid LOD DSP kernel (C++)
  - 3-5 formant bandpass filters
  - Shaped noise for fricatives
  - SoA (Structure-of-Arrays) layout
  - SIMD optimized (AVX2 baseline)
- [ ] Integrate as UE5 SourceEffect
  - Real-time safe audio callback
  - Lock-free parameter updates
  - Pre-allocated buffers
- [ ] Microbench per-voice performance
  - Target: ≤5µs per voice per buffer
  - Test on AVX2 baseline hardware
- [ ] Build 1000-agent UE5 test level
  - Scripted voice activity
  - LOD transitions
  - Performance monitoring

**Deliverables**:
- Working Mid LOD kernel (C++ + SIMD)
- UE5 SourceEffect integration
- Performance benchmarks
- 1000-agent test level

**Team**: 2 DSP engineers + 1 UE5 engineer

---

**Week 5-6: Far LOD & Clustering**
- [ ] Implement Far LOD crowd synthesis
  - Granular/noise-band resynthesis
  - 12-24 cluster buses
  - Spatial/attribute clustering algorithm
- [ ] Implement clustering system
  - k-means or grid-based clustering
  - Updated at 10-20Hz (not per-sample)
  - Per-agent amplitude/pan control only
- [ ] Hit performance targets
  - ≤10µs per bus per buffer
  - 840 agents → 12-24 buses
  - Verify total Far LOD budget ≤0.16ms
- [ ] Implement LOD governor
  - Feedback control system
  - Keeps total audio work ≤70% buffer time
  - Dynamic Near→Mid, Mid→Far demotion
- [ ] Implement LOD transitions
  - Sample-accurate crossfades
  - Phase-consistent transitions
  - No clicks or pops

**Deliverables**:
- Working Far LOD crowd synthesis
- Clustering algorithm
- LOD governor system
- Smooth LOD transitions

**Team**: 2 DSP engineers + 1 algorithm specialist

---

**Week 7-8: Near LOD & Stability**
- [ ] Implement Near LOD kernel
  - LF glottal source (Liljencrants-Fant)
  - Time-varying IIR vocal tract filters
  - Stable parameterization (pole radii/angles)
  - Per-sample coefficient interpolation
  - Anti-zipper smoothing
  - Nasal branches
  - Lip radiation filter
- [ ] Add stability guards
  - FTZ/DAZ enabled
  - Denormal detection and suppression
  - IIR stability bounds
  - Coefficient interpolation limits
- [ ] Run initial quality tests
  - MUSHRA with small corpus
  - ViSQOL objective measurement
  - Target: MOS ≥4.0
- [ ] Run overnight soak tests
  - 8-24 hours continuous
  - Zero underruns target
  - Stability validation

**Deliverables**:
- Working Near LOD kernel
- Stability safeguards
- Initial quality validation
- Soak test results

**Team**: 2 DSP engineers + 1 quality engineer

---

### Month 3-4: Archetype System (Weeks 9-16)

**Week 9-10: Archetype Voice Profiles**
- [ ] Implement all archetype profiles
  - Human (male/female)
  - Vampire
  - Zombie
  - Werewolf (human/beast)
  - Lich
  - Ghoul
  - Wraith
- [ ] Create parameter databases
  - Base aberration params per archetype
  - Variation ranges for individuality
  - Performance hints
- [ ] Implement emotion mapping
  - Arousal → tension, F0, breathiness
  - Valence → formant shift, spectral tilt
  - Dominance → tension, pressure
- [ ] Test archetype recognition
  - Blind classification tests
  - Target: ≥80% recognition rate
- [ ] Voice design approval
  - Story Teller (Gemini 2.5 Pro) review
  - Iterate based on feedback

**Deliverables**:
- Complete archetype profile system
- Emotion mapping implementation
- Archetype recognition validation
- Story Teller approval

**Team**: 1 DSP engineer + 1 voice designer + Story Teller consultant

---

**Week 11-12: NPC Voice Manager**
- [ ] Build voice assignment system
  - Voice handle management
  - Archetype → aberration param mapping
  - Individual variation per NPC
- [ ] Implement voice lifecycle
  - Spawn/despawn
  - LOD assignment
  - Voice stealing
- [ ] Add real-time parameter control
  - Emotion updates
  - State changes
  - Dynamic modulation
- [ ] Implement voice caching
  - Anchor audio cache
  - Feature envelope cache
  - LRU eviction policy

**Deliverables**:
- NPC Voice Manager system
- Voice lifecycle management
- Parameter control API
- Caching system

**Team**: 2 engine engineers

---

**Week 13-14: Anchor Pipeline**
- [ ] TTS anchor generation system
  - Integration with TTS APIs (OpenAI, Azure, Google, or Coqui)
  - Batch generation workflow
  - Quality validation
- [ ] OR: Voice recording pipeline
  - Professional voice actor workflow
  - Recording guidelines
  - Quality assurance
- [ ] Phoneme library creation
  - All archetypes
  - Multiple variations
  - Comprehensive coverage
- [ ] Anchor Feature Envelope extraction
  - F0 extraction
  - Cepstral analysis
  - Phoneme alignment
  - Prosody analysis
- [ ] UE5 asset integration
  - Custom UAnchorFeatureEnvelope asset type
  - Cooker integration
  - Streaming support
  - Platform compression

**Deliverables**:
- Working anchor generation pipeline
- Phoneme library (all archetypes)
- Feature extraction tools
- UE5 asset pipeline

**Team**: 1 tools engineer + 1 UE5 engineer + 1 voice engineer

---

**Week 15-16: Spectral Seed Synthesizer**
- [ ] Implement ethereal voice synthesis
  - Seed generation (whisper, wind, chains, dust, echo)
  - Granular synthesis
  - Spectral shaping
  - Effect processing
- [ ] Create presets for ethereal beings
  - Wraith (standard, ancient, vengeful)
  - Spirit (benevolent)
- [ ] Integrate with NPC system
  - Same API as physical modeling
  - Separate synthesis path
- [ ] Quality validation
  - "Otherworldly" aesthetic evaluation
  - Story Teller approval

**Deliverables**:
- Spectral seed synthesizer
- Ethereal being presets
- Integration with main system
- Quality validation

**Team**: 1 DSP engineer + Story Teller consultant

---

### Month 5-6: Optimization & Integration (Weeks 17-24)

**Week 17-18: Performance Optimization**
- [ ] SIMD optimization pass
  - Vectorize hot loops
  - SoA layout optimization
  - Cache optimization
- [ ] Multi-threading optimization
  - Worker thread pre-rendering (Mid/Far)
  - Job system integration
  - Lock-free synchronization
- [ ] Memory optimization
  - Pool allocation tuning
  - Cache hit rate optimization
  - Memory footprint reduction
- [ ] Platform-specific tuning
  - Windows (AVX2)
  - Linux
  - PS5/XSX (console optimization)
  - ARM Neon (Switch/mobile)

**Deliverables**:
- Optimized codebase meeting all perf targets
- Platform-specific builds
- Performance report per platform

**Team**: 2 optimization engineers + 1 platform specialist

---

**Week 19-20: UE5 Plugin Development**
- [ ] Create UE5 audio plugin structure
  - Game thread component
  - Audio render component
  - Worker job system integration
- [ ] Implement Blueprint API
  - Assign Voice to NPC
  - Release NPC Voice
  - Speak with Emotion
  - Update Voice Emotion
  - Get Performance Stats
- [ ] Integrate with UE5 Audio Mixer
  - Near: SourceEffect
  - Mid: SourceEffect (lighter)
  - Far: SubmixEffect (crowd synth)
- [ ] Add spatialization support
  - UE spatializer integration
  - Distance attenuation
  - Occlusion support
- [ ] Create in-editor tools
  - Voice preview tool
  - Performance monitor
  - Archetype editor
  - Debug visualizations

**Deliverables**:
- Complete UE5 plugin
- Blueprint API
- Audio Mixer integration
- Editor tools

**Team**: 2 UE5 engineers + 1 tools engineer

---

**Week 21-22: Content Pipeline**
- [ ] Anchor generation tools
  - Batch processing
  - Quality validation
  - Asset cooking
- [ ] Asset management
  - Versioning system
  - Streaming support
  - Platform compression
- [ ] Determinism verification
  - Cross-platform consistency
  - Reproducible builds
  - Hash verification
- [ ] Content workflow documentation
  - Voice designer guide
  - Sound designer guide
  - Integration guide

**Deliverables**:
- Complete content pipeline
- Asset management system
- Workflow documentation

**Team**: 2 tools engineers

---

**Week 23-24: Integration Testing**
- [ ] Full game integration test
  - 1000-agent scene
  - All LOD tiers active
  - All archetypes represented
- [ ] Performance validation
  - Meet all µs/buffer targets
  - Zero underruns in 30-min soak
  - 60fps maintained
- [ ] Quality validation
  - All archetypes audible and distinct
  - Emotion changes perceptible
  - LOD transitions smooth
- [ ] Stress testing
  - LOD churn scenarios
  - Voice spawn/despawn storms
  - Worst-case loads

**Deliverables**:
- Integration test results
- Performance validation report
- Quality validation report
- Stress test results

**Team**: 2 test engineers + all team members

---

### Month 7-8: Testing & Polish (Weeks 25-32)

**Week 25-26: Quality Testing**
- [ ] Intelligibility tests
  - 100 sentences per archetype
  - Speech recognition API validation
  - Target: ≥95% word accuracy (WER <5%)
- [ ] MOS (Mean Opinion Score) tests
  - MUSHRA methodology
  - 24+ human listeners
  - Anchors: Original TTS, hidden reference
  - Target: MOS ≥4.0
- [ ] ViSQOL objective testing
  - Automated quality measurement
  - Target: ≥3.8 vs anchors
- [ ] Archetype recognition tests
  - 20 samples per archetype
  - Blind classification
  - Target: ≥80% accuracy
- [ ] Emotion recognition tests
  - 5 emotions per archetype
  - Blind identification
  - Target: ≥70% accuracy

**Deliverables**:
- Complete quality test results
- Statistical validation
- Comparison to neural TTS
- User acceptance validation

**Team**: 2 quality engineers + test participants

---

**Week 27-28: Performance Optimization Pass 2**
- [ ] Address performance bottlenecks
  - Profile-guided optimization
  - Hot path refinement
  - Cache optimization
- [ ] Platform-specific tuning
  - Console certification prep
  - Mobile optimization (if applicable)
  - Low-end hardware support
- [ ] Load-shedding refinement
  - LOD governor tuning
  - Voice stealing policy
  - Graceful degradation
- [ ] Telemetry refinement
  - Dashboard polish
  - Alert thresholds
  - Logging optimization

**Deliverables**:
- Optimized performance across all platforms
- Tuned load-shedding system
- Production-ready telemetry

**Team**: 2 optimization engineers

---

**Week 29-30: Bug Fixes & Edge Cases**
- [ ] Fix all critical bugs
  - Audio glitches
  - Crashes
  - Memory leaks
- [ ] Address edge cases
  - Boundary conditions
  - Parameter extremes
  - Rare scenarios
- [ ] Stability improvements
  - IIR filter stability
  - Denormal handling
  - Numerical precision
- [ ] Code review & cleanup
  - Peer review all code
  - Remove debug code
  - Code documentation

**Deliverables**:
- Zero critical bugs
- All edge cases handled
- Production-ready codebase

**Team**: All engineers

---

**Week 31-32: Documentation & Training**
- [ ] Technical documentation
  - API reference
  - Architecture guide
  - Performance guide
  - Troubleshooting guide
- [ ] User documentation
  - Voice designer guide
  - Sound designer guide
  - Integration guide
  - Best practices
- [ ] Training materials
  - Video tutorials
  - Example projects
  - Workflow guides
- [ ] Handoff preparation
  - Code review
  - Knowledge transfer
  - Support plan

**Deliverables**:
- Complete documentation suite
- Training materials
- Handoff package

**Team**: 1 technical writer + all engineers

---

## TEAM STRUCTURE

### Core Team (Months 1-8)

**DSP/Audio Engineers** (3):
- Senior DSP Engineer #1: Lead, Near LOD kernel
- Senior DSP Engineer #2: Mid/Far LOD, clustering
- DSP Engineer #3: Spectral seed, optimization

**Engine Engineers** (3):
- Senior UE5 Engineer #1: Plugin architecture, Audio Mixer
- UE5 Engineer #2: Blueprint API, editor tools
- Engine Engineer #3: NPC Voice Manager, integration

**Tools/Pipeline Engineers** (2):
- Tools Engineer #1: Anchor pipeline, content tools
- Tools Engineer #2: Asset pipeline, UE5 integration

**Quality/Test Engineers** (2):
- Quality Engineer #1: MOS testing, validation
- Test Engineer #2: Performance testing, automation

**Specialists (Consultants)**:
- Algorithm Specialist: Clustering, optimization (part-time)
- Platform Specialist: Console optimization (part-time)
- Story Teller (Gemini 2.5 Pro): Voice design approval
- Technical Writer: Documentation (last 2 months)

**Total Core Team**: 8 engineers + 3-4 specialists

---

## BUDGET ESTIMATE

### Development Costs

**Engineering Team** (8 months):
- 3 Senior Engineers × $150K/year × 8/12 = $300K
- 5 Mid-level Engineers × $120K/year × 8/12 = $400K
- **Subtotal**: $700K

**Specialists/Consultants**:
- Algorithm Specialist: $50K
- Platform Specialist: $40K
- Story Teller (API costs): $5K
- Technical Writer: $30K
- **Subtotal**: $125K

**Infrastructure**:
- Development hardware: $50K
- Console devkits (PS5/XSX): $20K
- Cloud compute (TTS, testing): $20K
- Tools/licenses: $10K
- **Subtotal**: $100K

**Testing**:
- User testing participants: $15K
- Quality testing (MOS, etc.): $20K
- Performance testing: $10K
- **Subtotal**: $45K

**Contingency** (20%): $194K

**TOTAL ESTIMATED BUDGET**: **~$1,164K** ($1.16M)

*Note: Original estimate was $200K - updated based on realistic team size and timeline for production quality*

### Ongoing Costs

**ZERO** - All synthesis runs locally, no API calls at runtime

---

## RISK MANAGEMENT

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Performance targets not met | Medium | High | Early prototyping, continuous profiling, fallback LOD strategies |
| Quality below 4.0 MOS | Low | High | Anchor & Aberration approach proven, Story Teller oversight |
| Platform compatibility issues | Medium | Medium | Multi-platform testing from Week 2, runtime SIMD dispatch |
| UE5 integration challenges | Medium | Medium | Experienced UE5 engineers, early integration testing |
| Real-time safety violations | Low | High | Strict code review, real-time safety guidelines, automated checks |
| Clustering algorithm complexity | Medium | Medium | Algorithm specialist, fallback to simpler clustering |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Feature creep | High | High | Strict scope control, change review process |
| Engineer availability | Medium | High | Backup engineers identified, cross-training |
| Dependencies on external tools | Low | Medium | Evaluate early, have fallback options |
| Quality issues requiring rework | Medium | High | Continuous testing, early validation |

### Mitigation Strategies

1. **Weekly Progress Reviews**: Track milestones, identify blockers early
2. **Continuous Integration**: Automated testing, performance tracking
3. **Regular Peer Review**: Code review, design review, quality review
4. **Early Prototyping**: Validate risky components first
5. **Fallback Plans**: Alternative approaches for high-risk items

---

## SUCCESS CRITERIA

### Technical Acceptance

- [ ] **Performance**: All µs/buffer targets met on all platforms
- [ ] **Quality**: MOS ≥4.0 (Near LOD), ViSQOL ≥3.8
- [ ] **Stability**: Zero underruns in 30-minute soak per platform
- [ ] **Intelligibility**: ≥95% word accuracy
- [ ] **Archetype Recognition**: ≥80% accuracy
- [ ] **Emotion Recognition**: ≥70% accuracy
- [ ] **Scale**: 1000 concurrent voices at 60fps

### Production Readiness

- [ ] **Code Quality**: All peer-reviewed, no critical bugs
- [ ] **Documentation**: Complete technical and user docs
- [ ] **Testing**: Comprehensive test coverage, automated CI
- [ ] **Platform Support**: Windows, Linux, PS5, XSX validated
- [ ] **Content Pipeline**: Working end-to-end workflow
- [ ] **Telemetry**: Production monitoring ready

### User Acceptance

- [ ] **Story Teller Approval**: All archetype voices approved
- [ ] **Sound Designer Approval**: Workflow and tools approved
- [ ] **Integration Testing**: Successfully integrated in test game
- [ ] **User Testing**: Positive feedback from focus groups

---

## DELIVERABLES CHECKLIST

### Core Technology
- [ ] Near LOD DSP kernel (C++, SIMD optimized)
- [ ] Mid LOD DSP kernel (C++, SIMD optimized)
- [ ] Far LOD crowd synthesis (clustering algorithm)
- [ ] LOD Manager & Governor
- [ ] NPC Voice Manager
- [ ] Spectral Seed Synthesizer
- [ ] Anchor Feature Envelope system
- [ ] Emotion mapping system

### Integration
- [ ] UE5 Audio Plugin (complete)
- [ ] Blueprint API
- [ ] Audio Mixer integration
- [ ] Spatialization support
- [ ] Editor tools & dashboard

### Content Pipeline
- [ ] Anchor generation tools
- [ ] Feature extraction tools
- [ ] Asset cooking & streaming
- [ ] Versioning system
- [ ] UE5 asset types

### Testing & Quality
- [ ] Unit test suite (comprehensive)
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Quality tests (MOS, ViSQOL, etc.)
- [ ] Soak tests (8-24 hours)
- [ ] Platform CI pipeline

### Documentation
- [ ] Technical specifications (complete)
- [ ] API reference
- [ ] Architecture guide
- [ ] Performance guide
- [ ] User guides (voice designer, sound designer)
- [ ] Integration guide
- [ ] Training materials

---

## PHASE 3 PREVIEW (Months 9-11)

**After Phase 2 completion, Phase 3 focuses on**:
- Production deployment
- Platform certification (console)
- Performance tuning at scale
- Real-world game integration
- Post-launch support planning
- Content library expansion

**Timeline**: 2-3 months  
**Team**: Reduced to 3-4 engineers + support

---

## CONCLUSION

**Status**: Phase 2 is fully specified and ready to begin

**Next Immediate Steps**:
1. Assemble engineering team
2. Week 1 kickoff: Finalize budgets and platform setup
3. Week 2: Begin Mid LOD prototype
4. Continuous progress tracking and peer review

**Confidence Level**: HIGH - Research validated, peer-reviewed, team structure clear

**Expected Outcome**: Production-ready vocal synthesis system in 8-12 months

---

**Roadmap Version**: 1.0  
**Date**: 2025-11-09  
**Status**: APPROVED  
**Next Action**: Team Assembly

---

**END OF PHASE 2 IMPLEMENTATION ROADMAP**

