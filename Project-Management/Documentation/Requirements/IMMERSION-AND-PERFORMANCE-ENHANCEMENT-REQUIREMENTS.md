# Immersion and Performance Enhancement Requirements
**Date**: 2025-11-05  
**Status**: Requirements Analysis Complete  
**Collaboration**: GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro

---

## EXECUTIVE SUMMARY

After comprehensive analysis of the current system architecture and research into AAA game standards, **critical gaps have been identified** in three key areas:

1. **NPC Individuality**: Current system has foundation but lacks true individuality
2. **Environment Immersion**: Good foundation but missing AAA-level detail density
3. **Framerate Performance**: Current architecture cannot achieve 300+ FPS as designed

This document provides detailed requirements and solutions to address these gaps and exceed AAA standards.

---

## TABLE OF CONTENTS

1. [NPC Individuality Requirements](#1-npc-individuality-requirements)
2. [Environment Immersion Requirements](#2-environment-immersion-requirements)
3. [Framerate Performance Requirements](#3-framerate-performance-requirements)
4. [Implementation Roadmap](#4-implementation-roadmap)
5. [Performance Budgets](#5-performance-budgets)

---

## 1. NPC INDIVIDUALITY REQUIREMENTS

### 1.1 Current State Assessment

**✅ What Exists:**
- 50-dimensional personality_vector (JSONB array)
- Big Five personality traits (openness, conscientiousness, extraversion, agreeableness, neuroticism)
- Additional traits: aggression, social, curiosity
- Basic personality scoring for actions (combat, social, explore, help, plan)
- NPC type modifiers (merchant, guard, civilian, criminal)
- Basic voice selection system

**❌ Critical Gaps Identified:**
- **No explicit speaking style generation** (syntax preferences, verbosity, vocabulary, dialect)
- **No mannerism/animation layer** (gestures, gaze behavior, idle variations, locomotion style)
- **No social memory/relationship system** (persistent memory of interactions)
- **No daily schedules/routines** (dynamic NPC behaviors tied to time/weather)
- **No linguistic style mapping** (personality → speech patterns)
- **No voice prosody control** (emotion contours, SSML, idiolect markers)
- **Basic behavior architecture** (trait vector not connected to robust utility AI/GOAP/BT)

### 1.2 Requirements

#### REQ-NPC-001: Dialogue Style Profile System

**Priority**: CRITICAL  
**Estimated Time**: 40 hours

**Description:**
Implement a comprehensive DialogueStyle profile system that generates unique speaking patterns for each NPC based on their personality vector.

**Requirements:**
- **Style Parameters**:
  - Verbosity (0.0-1.0): How much NPC talks
  - Sentence Length: Average words per sentence
  - Formality (0.0-1.0): Formal vs. casual language
  - Dialect/Phonology Map: Regional accents, speech patterns
  - Filler/Disfluency Rates: "um", "uh", stuttering frequency
  - Hedging/Intensity: Use of qualifiers, certainty level
  - Emotional Valence/Activation: How emotions affect speech
  - Topic Preferences: What subjects NPC prefers
  - Taboo Filters: What language NPC avoids

- **Lexical Layer System**:
  - Synonym sets (personality-driven word choice)
  - Slang vocabulary (generation/selection)
  - Profession jargon (merchant, guard, etc.)
  - Catchphrases and idiolect markers

- **SSML/Prosody API**:
  - Emotion curves tied to state (arousal/valence from personality + situation)
  - TTS integration with prosody parameters
  - Real-time voice modulation based on emotional state

**Acceptance Criteria:**
- [ ] Each NPC has unique DialogueStyle profile
- [ ] Speaking patterns vary based on personality_vector
- [ ] TTS integration supports prosody modulation
- [ ] Dialogue generation uses style parameters
- [ ] Player can distinguish NPCs by speech patterns alone

**Technical Implementation:**
```python
class DialogueStyleProfile:
    verbosity: float  # 0.0-1.0
    sentence_length_avg: int
    formality: float  # 0.0-1.0
    dialect_map: Dict[str, float]
    filler_rate: float
    hedging_intensity: float
    emotional_activation: float
    topic_preferences: List[str]
    taboo_filters: List[str]
    catchphrases: List[str]
    slang_vocabulary: Dict[str, str]
    
    def generate_dialogue(self, personality: Dict, context: Dict) -> str:
        # Generate dialogue based on style profile
        pass
```

---

#### REQ-NPC-002: Mannerism & Movement Profile System

**Priority**: HIGH  
**Estimated Time**: 60 hours

**Description:**
Implement a MannerismProfile system that maps personality traits to unique movement, gesture, and behavioral patterns.

**Requirements:**
- **Gaze Behavior**:
  - Fixation duration (how long NPC looks at something)
  - Saccade frequency (eye movement patterns)
  - Eye contact rules (cultural/comfort-based)
  - Gaze target preferences

- **Interpersonal Distance**:
  - Preferred spacing from others
  - Approach speed/comfort zones
  - Personal space boundaries

- **Idle/Gesture System**:
  - Hand/shoulder/head fidgets
  - Frequency and amplitude of gestures
  - Personality → animation parameter mapping
  - Idle animation variations

- **Locomotion Style**:
  - Stride variability
  - Posture (upright, slouched, confident)
  - Turn aggression (how quickly NPC changes direction)
  - Walking speed variability

- **Animation Integration**:
  - Motion matching with personality-driven parameters
  - Procedural noise for micro-movements
  - Animation layers for personality expression

**Acceptance Criteria:**
- [ ] Each NPC has unique MannerismProfile
- [ ] Movement patterns reflect personality
- [ ] Gestures and idle behaviors vary by NPC
- [ ] Animation system supports personality-driven variations
- [ ] Player can identify NPCs by movement style

**Technical Implementation:**
```python
class MannerismProfile:
    gaze_fixation_duration: float
    gaze_saccade_frequency: float
    eye_contact_comfort: float
    preferred_interpersonal_distance: float
    gesture_frequency: float
    gesture_amplitude: float
    stride_variability: float
    posture_confidence: float
    locomotion_style: str
    
    def apply_to_npc(self, npc_actor: AActor) -> None:
        # Apply mannerism parameters to NPC actor
        pass
```

---

#### REQ-NPC-003: Social Memory & Relationship Graph

**Priority**: HIGH  
**Estimated Time**: 50 hours

**Description:**
Implement a persistent memory system that tracks NPC relationships with players and other NPCs, influencing dialogue and behavior.

**Requirements:**
- **Memory Graph Structure**:
  - Entity relationships (player/NPCs)
  - Sentiment scores (trust, fear, respect, etc.)
  - Interaction history (timestamped events)
  - Notable events (memorable encounters)
  - Relationship scores (numerical values)

- **Memory-Driven Dialogue**:
  - Topic selection based on relationship
  - Tone adjustment based on sentiment
  - Callbacks to previous interactions
  - Contextual dialogue unlocks

- **Behavioral Influence**:
  - NPC reactions based on relationship
  - Trust-based actions (helping, betraying)
  - Fear-based avoidance
  - Respect-based deference

- **Persistence**:
  - Memory stored in PostgreSQL (canonical)
  - Cached in Redis for performance
  - Vector DB for semantic memory search

**Acceptance Criteria:**
- [ ] NPCs remember player interactions
- [ ] Relationships affect dialogue and behavior
- [ ] Memory persists across sessions
- [ ] NPCs reference past events in dialogue
- [ ] Relationship changes affect gameplay

**Technical Implementation:**
```python
class SocialMemoryGraph:
    entity_id: UUID
    relationships: Dict[UUID, Relationship]
    memory_events: List[MemoryEvent]
    
    def update_relationship(self, target: UUID, event: MemoryEvent) -> None:
        # Update relationship based on event
        pass
    
    def get_dialogue_context(self) -> Dict:
        # Get dialogue context based on relationships
        pass

class Relationship:
    trust: float
    fear: float
    respect: float
    last_interaction: datetime
    notable_events: List[str]
```

---

#### REQ-NPC-004: Daily Routines & Role-Based Schedules

**Priority**: MEDIUM  
**Estimated Time**: 40 hours

**Description:**
Implement dynamic daily/weekly schedules for NPCs based on their roles and personality, with weather/event-driven overrides.

**Requirements:**
- **Schedule Generation**:
  - Role-based templates (merchant, guard, civilian, etc.)
  - Time-based activities (morning, afternoon, evening, night)
  - Location-based activities (home, work, market, etc.)
  - Variability windows (randomization within schedule)

- **Dynamic Adaptation**:
  - Weather overrides (stay inside during storms)
  - Event-driven changes (festivals, crimes, etc.)
  - Emergency responses (break from schedule)
  - Player interaction interrupts

- **Schedule Integration**:
  - Available barks based on schedule state
  - Behavior sets tied to current activity
  - Animation sets based on activity
  - Location-based dialogue

**Acceptance Criteria:**
- [ ] NPCs follow daily schedules
- [ ] Schedules adapt to weather/events
- [ ] Players can observe NPC routines
- [ ] NPCs have contextual behaviors based on schedule
- [ ] Schedules feel natural and varied

---

#### REQ-NPC-005: Enhanced Behavior Architecture

**Priority**: HIGH  
**Estimated Time**: 80 hours

**Description:**
Replace basic personality scoring with a robust utility AI/GOAP/BT system that translates personality vectors into sophisticated decision-making.

**Requirements:**
- **Utility AI System**:
  - Tunable curves from 50D vector to decision weights
  - Extraversion → social action utility
  - Neuroticism → threat sensitivity
  - Conscientiousness → rule-following
  - Multiple action evaluators with personality weighting

- **Decision Decoupling**:
  - Behavior updates at 2-10 Hz (not every frame)
  - Async decision-making
  - Cached decisions for performance

- **GOAP/BT Integration**:
  - Goal-oriented action planning
  - Behavior trees with personality-driven parameters
  - Hierarchical task networks

- **Performance Budget**:
  - Per-NPC budget: <0.1ms per update
  - Total AI budget: <0.3ms per frame
  - Async processing for complex decisions

**Acceptance Criteria:**
- [ ] NPCs make complex decisions based on personality
- [ ] Behavior system decoupled from frame loop
- [ ] Performance targets met
- [ ] NPCs exhibit personality-driven behaviors
- [ ] System supports 100+ NPCs simultaneously

---

#### REQ-NPC-006: Content Pre-Baking & Caching System

**Priority**: MEDIUM  
**Estimated Time**: 30 hours

**Description:**
Implement a system to pre-bake dialogue lexicons, TTS clips, and style profiles to reduce runtime costs.

**Requirements:**
- **Pre-Baking Pipeline**:
  - Dialogue lexicons generated during build
  - TTS clips pre-generated for common lines
  - Style profiles cached
  - Personality → style mapping pre-computed

- **Runtime Caching**:
  - TTS cache for frequently used phrases
  - Dialogue template cache
  - Style profile cache

- **Asset Management**:
  - Streaming for large audio assets
  - Per-NPC budget caps
  - Memory management for cached assets

**Acceptance Criteria:**
- [ ] Pre-baking pipeline reduces runtime costs
- [ ] TTS caching reduces generation time
- [ ] Memory usage within budget
- [ ] Asset streaming works correctly

---

## 2. ENVIRONMENT IMMERSION REQUIREMENTS

### 2.1 Current State Assessment

**✅ What Exists:**
- Terrain system tasks (TE-001 through TE-004)
- Weather system planned (WS-001 through WS-004)
- Day/Night world system (DN-001 through DN-003)
- Audio system with MetaSounds (VA-001 through VA-004)
- Orchestration Layer 2 customization

**❌ Critical Gaps Identified (Claude 4.5 Sonnet Analysis):**
- **No Environmental Narrative Service** (story scenes, object metadata, discovery framework)
- **No Multi-Resolution Detail System** (macro/meso/micro/nano scale details)
- **No Environmental Reactivity Matrix** (cross-system cascading effects)
- **No NPC-Environment Integration** (contextual interactions, weather responses, environmental traces)
- **No Procedural Set Dressing/Weathering System** (debris, decals, grime, wear, accumulation)
- **No World State Persistence** (temporal object states, player modification tracking)
- **No Unnoticed Detail Generation Framework** (99% detail density system)
- **Limited audio depth** (no geometry-aware occlusion, dynamic reverb, surface-specific sounds, HRTF)
- **No haptics/feedback system** (controller rumble, terrain feedback, weather haptics)
- **Missing "99% unnoticed" detail density** (Red Dead Redemption 2 standard)

**Current System Rating**: 4/10 for AAA immersion (Claude 4.5 Sonnet assessment)

### 2.2 Requirements

#### REQ-ENV-001: Environmental Narrative Service (ENS)

**Priority**: CRITICAL  
**Estimated Time**: 100 hours

**Description:**
Implement a comprehensive environmental storytelling system that places narrative-driven details throughout the world, creating stories through object placement and environmental context.

**Requirements:**
- **ENS-001: Story Scene System**:
  - Template-based narrative scenes (abandoned camp, battle aftermath, recent departure, long-term settlement)
  - Procedural detail generator with story-appropriate props
  - Contextual clutter density (5-50 objects per scene)
  - Environmental "reading" markers for players
  - Discovery reward framework

- **ENS-002: Object Story Metadata**:
  - Each placeable object has narrative weight tags
  - Relationship rules (whiskey bottle + medical supplies = desperation story)
  - Wear/damage state affects narrative interpretation
  - Temporal decay simulation

- **ENS-003: Environmental History System**:
  - Track player actions affecting environment
  - Persistent damage/modification to world
  - NPC behavioral traces (footprints, disturbances)
  - Weather erosion of player/NPC changes over time

- **ENS-004: Discovery Reward Framework**:
  - 99% details metric tracking
  - Analytics for "noticed vs. unnoticed" content
  - Dynamic detail spawning in player peripheral vision
  - Reward curves for environmental observation

**Acceptance Criteria:**
- [ ] Story scenes generate procedurally
- [ ] Objects tell stories through placement
- [ ] Environmental history persists
- [ ] Discovery system tracks player engagement
- [ ] System integrates with terrain, weather, and audio

---

#### REQ-ENV-002: Multi-Resolution Detail System (MRDS)

**Priority**: HIGH  
**Estimated Time**: 120 hours

**Description:**
Implement a multi-scale detail system that provides detail density at macro, meso, micro, and nano scales to match AAA standards.

**Requirements:**
- **MRDS-001: Macro Environment Theming**:
  - Biome-level art direction rules
  - Climate zone influence on asset selection
  - Cultural/narrative zone definitions
  - Color palette enforcement per region

- **MRDS-002: Procedural Meso-Detail Population**:
  - Rule-based clutter placement (100-500 objects per city block)
  - Decal systems for surface variation (graffiti, posters, stains)
  - Cable/pipe procedural generation for urban density
  - Vegetation micro-variation (weeds, moss, vines)

- **MRDS-003: Texture Detail Layering**:
  - 4K base + procedural wear overlays
  - Tri-planar projection for seamless detail
  - Wetness/snow/mud accumulation masks
  - Time-of-day texture variation (wet at dawn, dry midday)

- **MRDS-004: Atmospheric Particle Density**:
  - Volumetric fog with localized density
  - Weather-specific particles (rain bounce, snow accumulation)
  - Environmental disturbance (player movement creates dust)
  - Light shaft interaction with particles

**Performance Requirements:**
- LOD system: 6 levels minimum (RDR2 uses 8)
- Draw distance: 5km for macro detail visibility
- Occlusion culling for dense environments
- Streaming system for detail loading

**Acceptance Criteria:**
- [ ] Detail density matches AAA standards (100+ objects per 100m²)
- [ ] Multiple LOD levels work correctly
- [ ] Performance within budget
- [ ] Details enhance immersion

---

#### REQ-ENV-003: Environmental Reactivity Matrix (ERM)

**Priority**: CRITICAL  
**Estimated Time**: 100 hours

**Description:**
Implement a comprehensive cross-system reactivity framework where weather, time, and player actions cascade through all environmental systems.

**Requirements:**
- **ERM-001: Weather-Driven Cascades**:
  Weather System →
  - Terrain (mud/puddle formation, snow accumulation)
  - Audio (rain reverb, thunder echoes, wind intensity)
  - NPCs (seek shelter, change clothing, adjust pathing)
  - Lighting (cloud shadows, wet surface reflections)
  - Particles (splash effects, mist generation)
  - Player (clothing wetness, movement speed in mud)

- **ERM-002: Time-of-Day Cascades**:
  Day/Night →
  - Lighting (sun angle, color temperature, shadow length)
  - Audio (cricket chirps, bird songs, city ambience shifts)
  - NPCs (sleep/wake cycles, job schedules, social behaviors)
  - Wildlife (nocturnal vs diurnal species)
  - Vegetation (flower opening/closing, bioluminescence)
  - Atmosphere (fog density, temperature, wind patterns)

- **ERM-003: Player Action Persistence**:
  Player Actions →
  - Terrain deformation (footprints, vehicle tracks)
  - Object displacement (knocked items stay moved)
  - Environmental damage (bullet holes, fire scarring)
  - NPC memory (locations of disturbances)
  - Audio (broken glass crunch, disturbed wildlife silence)

- **ERM-004: Compounding Effects System**:
  - Multiple systems affect single elements (e.g., footprints affected by terrain + weather + time)
  - Degradation over time (tracks fade, blood washes away)
  - Restoration thresholds (when environments reset)

**Orchestration Enhancement:**
- Layer 3: Reactive Coordinator
- Event bus for environmental state changes
- Priority queue for cascading effects
- Performance budget manager
- State synchronization for multiplayer

**Acceptance Criteria:**
- [ ] Weather affects all systems correctly
- [ ] Time-of-day drives comprehensive changes
- [ ] Player actions persist in environment
- [ ] Compounding effects work naturally
- [ ] Performance within budget

---

#### REQ-ENV-004: Procedural Set Dressing & Weathering System

**Priority**: HIGH  
**Estimated Time**: 80 hours

**Description:**
Implement a comprehensive procedural system for generating environmental details that create immersion through density and variety.

**Requirements:**
- **Biome-Specific Scatterers**:
  - Density fields per biome type
  - Slope/altitude masks for placement
  - Vegetation variety (grasses, shrubs, trees)
  - Debris generation (rocks, logs, natural clutter)
  - Seasonal variation

- **Weathering Pass**:
  - Decals system (grime, stains, wear)
  - Edge wear patterns
  - Puddle generation (weather-driven)
  - Material Parameter Collections driven by weather state
  - Dynamic roughness/darkening
  - Normal map blending for wear

- **Wetness/Snow Accumulation**:
  - Dynamic wetness system
  - Snow accumulation during storms
  - Drip systems for wet surfaces
  - Material transitions (dry → wet → frozen)

**Acceptance Criteria:**
- [ ] Environments show realistic weathering
- [ ] Weather affects material appearance
- [ ] Set dressing varies by biome
- [ ] Details enhance immersion without performance impact
- [ ] System supports streaming and LOD

---

#### REQ-ENV-003: Audio Psychoacoustics & Advanced Mixing

**Priority**: HIGH  
**Estimated Time**: 70 hours

**Description:**
Implement advanced audio systems that provide spatial accuracy, environmental acoustics, and dynamic mixing.

**Requirements:**
- **Geometry-Aware Audio**:
  - Occlusion/diffraction calculations
  - Portal/room system with impulse responses
  - Convolution reverb for realistic spaces
  - Parametric reverb for dynamic environments

- **Dynamic Reverb Zones**:
  - Early reflections calculation
  - Wetness filters for weather effects
  - Wind/foliage/bird layers by biome/time
  - Distance-based filtering (LPF/HPF)

- **Surface-Aware Audio**:
  - Footsteps vary by surface material
  - Weather variants for foley
  - Material-based sound generation
  - Impact sounds based on material properties

- **Adaptive Mix States**:
  - Combat mix (emphasize action sounds)
  - Interior mix (reverb, muffled exterior)
  - Storm mix (wind, rain, thunder)
  - Crowd mix (layered ambient voices)
  - Sidechain ducking for voice-over

**Acceptance Criteria:**
- [ ] Audio provides spatial accuracy
  - [ ] Reverb matches environment
  - [ ] Weather affects audio mix
  - [ ] Surface materials affect sounds
  - [ ] Mix states adapt to gameplay

---

#### REQ-ENV-004: Atmospherics & Foliage Reactivity

**Priority**: MEDIUM  
**Estimated Time**: 50 hours

**Description:**
Implement volumetric effects, atmospheric layers, and wind-responsive vegetation for enhanced immersion.

**Requirements:**
- **Volumetric Fog Layers**:
  - Weather/time-of-day coloration
  - Light shafts tuned for day/night cycle
  - Density variation by biome
  - Performance-optimized rendering

- **Wind Field Simulation**:
  - Affects foliage, particles, cloth
  - Weather-driven wind intensity
  - Directional wind patterns
  - Real-time wind updates

- **Micro-Ambient Particles**:
  - Dust motes by biome/time
  - Insects (bees, butterflies, etc.)
  - Pollen during spring
  - Seasonal particle variety

**Acceptance Criteria:**
- [ ] Volumetric effects enhance atmosphere
- [ ] Wind affects vegetation realistically
- [ ] Micro-particles add detail without performance cost
- [ ] System integrates with weather system

---

#### REQ-ENV-005: Ambient Life System

**Priority**: MEDIUM  
**Estimated Time**: 60 hours

**Description:**
Implement wildlife and ambient NPC systems that bring environments to life.

**Requirements:**
- **Wildlife Spawners**:
  - Low-frequency brain updates (2-10 Hz)
  - Simple flocking behavior
  - Seasonal presence (birds migrate, etc.)
  - Biome-specific wildlife

- **Civilian Ambient Routines**:
  - Sit, gossip, repair, sweep activities
  - Tied to time, weather, and location tags
  - Background NPC behaviors
  - Non-interactive but visible

- **Performance Optimization**:
  - LOD system for distant wildlife
  - Simplified behaviors for background NPCs
  - Culling for off-screen entities
  - Budget per ambient entity

**Acceptance Criteria:**
- [ ] Environments feel alive with wildlife
- [ ] Ambient NPCs enhance immersion
- [ ] Performance within budget
- [ ] Behaviors feel natural

---

#### REQ-ENV-006: NPC-Environment Integration (NEA)

**Priority**: HIGH  
**Estimated Time**: 80 hours

**Description:**
Implement NPC environmental awareness system where NPCs react to and interact with the environment contextually.

**Requirements:**
- **NEA-001: Contextual Interaction Framework**:
  - 200+ interaction types (sit, lean, smoke, read, shelter, work)
  - Proximity-based behavior triggers
  - Environmental affordance detection (sittable surfaces, coverable spaces)
  - Animation blending for seamless interactions

- **NEA-002: Weather Response Behaviors**:
  - Per-NPC weather tolerance thresholds
  - Clothing change system (dynamic outfit swaps)
  - Pathfinding adjusted for rain/snow (prefer covered routes)
  - Idle animation sets per weather state

- **NEA-003: Environmental Trace Generation**:
  - NPC footprints in mud/snow (with degradation)
  - Item usage residue (cigarette butts, trash)
  - Worn paths in grass from repeated NPC routes
  - Environmental damage from NPC actions (scuff marks, wear)

- **NEA-004: Crowd Density Dynamics**:
  - Time-based crowd spawning (rush hour, night quiet)
  - Event-driven crowd behavior (markets, celebrations)
  - Performance-aware LOD for distant NPCs
  - Audio contribution from crowd density

**Acceptance Criteria:**
- [ ] NPCs interact with environment contextually
- [ ] NPCs react to weather appropriately
- [ ] NPCs leave environmental traces
- [ ] Crowd dynamics feel natural
- [ ] Performance within budget

---

#### REQ-ENV-007: World State Persistence (WSP)

**Priority**: HIGH  
**Estimated Time**: 70 hours

**Description:**
Implement a system for tracking and persisting environmental changes over time, including player modifications and natural decay.

**Requirements:**
- **WSP-001: Temporal Object States**:
  - Object lifecycle tracking (pristine → worn → broken → decayed)
  - Time-based degradation (corpses rot, blood dries)
  - Weather influence on decay (rain speeds rot, sun dries)
  - Restoration events (street cleaning, natural regrowth)

- **WSP-002: Player Modification Tracking**:
  - Database of player-altered objects (10,000+ simultaneous)
  - Position, rotation, damage state per object
  - Networked state synchronization (if multiplayer)
  - Spatial partitioning for efficient queries

- **WSP-003: Dynamic Event Persistence**:
  - World events leave lasting marks (fire scarring, battle debris)
  - NPC-driven changes (construction progress, settlements)
  - Seasonal variations (fall leaves, winter snow coverage)
  - Reset thresholds to prevent world clutter

- **WSP-004: Save State Optimization**:
  - Differential saving (only changed data)
  - Compression for large-scale persistence
  - Priority system (critical changes vs. minor details)

**Acceptance Criteria:**
- [ ] Objects degrade over time realistically
- [ ] Player modifications persist
- [ ] World events leave lasting marks
- [ ] Save system optimized for performance
- [ ] System supports 10,000+ tracked objects

---

#### REQ-ENV-008: Unnoticed Detail Generation Framework (UDG)

**Priority**: MEDIUM  
**Estimated Time**: 60 hours

**Description:**
Implement the RDR2 "99% unnoticed detail" philosophy through systematic detail generation that most players won't consciously notice but creates immersion.

**Requirements:**
- **UDG-001: Procedural Detail Budget**:
  - Target density: 50-200 detail objects per 100m²
  - LOD budget: 30% for unseen details
  - Performance headroom: 20% GPU/CPU for "invisible" work
  - Artist-directed randomization (controlled chaos)

- **UDG-002: Detail Discovery Metrics**:
  - Heatmap tracking: what players actually look at
  - A/B testing: high vs. low detail zones
  - Retention correlation: detail density vs. engagement
  - "Wow moment" triggers from environmental discovery

- **UDG-003: Systemic Detail Generators**:
  Procedural systems for:
  - Interior clutter (books, bottles, tools - contextual to location)
  - Exterior wear (rust, cracks, vegetation overgrowth)
  - Micro-fauna (insects, small birds, rodents)
  - Atmospheric details (dust in light shafts, pollen, ash)
  - Sound details (distant dogs, creaking wood, dripping water)

- **UDG-004: Narrative Detail Injection**:
  - Algorithm scatters "story nodes" (90% of players miss)
  - Detail placement follows narrative logic (medical supplies near injury site)
  - Discoverable secrets reward exploration (hidden notes, environmental puzzles)
  - Dynamic difficulty: show more hints if player struggles

**Content Creation Pipeline**:
1. Artist Creates "Hero" Detail Set (50-100 high-quality assets per environment type)
2. Procedural Variation Generator (creates 500-1000 variants per hero asset)
3. Placement Rule Engine (context-aware spawning, density maps)
4. Performance Validation (automated LOD, draw call batching, occlusion baking)
5. Playtesting & Heatmapping (track what players notice, adjust detail placement)

**Acceptance Criteria:**
- [ ] Detail density matches RDR2 standards (99% unnoticed)
- [ ] Discovery metrics track player engagement
- [ ] Procedural generators create variety
- [ ] Narrative details reward exploration
- [ ] Performance within budget

---

#### REQ-ENV-009: Multi-Sensory Feedback System (MSFS)

**Priority**: MEDIUM  
**Estimated Time**: 50 hours

**Description:**
Implement comprehensive haptic and advanced audio systems for enhanced multi-sensory immersion.

**Requirements:**
- **MSFS-001: Haptic Terrain Response**:
  - Texture-based vibration patterns (grass, gravel, wood, metal)
  - Resistance feedback for mud, water, snow
  - Impact intensity for falls, collisions
  - Subtle ambient vibration (heartbeat, vehicle rumble)

- **MSFS-002: Weather Haptics**:
  - Raindrop patter intensity
  - Wind gust pulses
  - Thunder rumble (low-frequency)
  - Temperature sensation (cold=slow pulse, heat=rapid)

- **MSFS-003: Advanced Spatial Audio**:
  Integration with VA-001 to VA-004:
  - HRTF head-tracking integration
  - Occlusion/obstruction reverb (behind walls, in forests)
  - Environmental reverb presets (cave, cathedral, forest, city)
  - Distance attenuation curves per material type
  - Doppler effect for moving sources

- **MSFS-004: Audio Detail Layering**:
  5-layer ambience system:
  1. Macro (wind, distant city hum)
  2. Mid (nearby activity, animals)
  3. Micro (footsteps, clothing rustle)
  4. Reactive (player action responses)
  5. Narrative (musical cues, emotional underscore)

**Acceptance Criteria:**
- [ ] Haptics enhance immersion across terrain and weather
- [ ] Advanced spatial audio provides accurate directionality
- [ ] 5-layer audio system creates depth
- [ ] System supports multiple controller types
- [ ] Performance impact minimal

---

## 3. FRAMERATE PERFORMANCE REQUIREMENTS

### 3.1 Current State Assessment

**✅ What Exists:**
- Target: 300+ FPS mentioned in requirements
- Multi-tier architecture: Gold (3B-8B, sub-16ms), Silver (7B-13B, 80-250ms), Bronze (671B MoE, async)
- UE5 engine with Nanite, Lumen, VSM mentioned
- Game loop: 300+ FPS requirement

**❌ Critical Gaps Identified:**
- **Frame budget mismatch**: 300 FPS = 3.33ms/frame, but Gold-tier AI targets sub-16ms (too slow)
- **No defined performance budgets** per subsystem
- **No "competitive mode" rendering profile**
- **Synchronous AI in game loop** (blocks frame processing)
- **No concrete UE5 optimization plan** (Lumen/Nanite/VSM settings)
- **No decoupled tick rates** for simulation vs. render
- **No frame generation strategy** (DLSS/FSR/XeSS)

### 3.2 Strategic Requirements

#### REQ-PERF-001: Dual-Mode Performance Architecture

**Priority**: CRITICAL  
**Estimated Time**: 100 hours

**Description:**
Implement two distinct performance modes: Immersive Mode (60-120 FPS) and Competitive Mode (300+ FPS).

**Requirements:**
- **Immersive Mode (60-120 FPS Target)**:
  - Lumen global illumination enabled
  - Nanite virtualized geometry enabled
  - Rich atmospherics and volumetrics
  - Full audio layers
  - Higher-density AI and NPCs
  - Environmental storytelling enabled
  - Full detail density

- **Competitive Mode (300+ FPS Target)**:
  - Lumen disabled (use baked/static lighting)
  - Nanite enabled with conservative settings
  - Volumetrics off or very low
  - Simplified post-processing
  - Minimal dynamic shadows
  - Reduced audio virtualization
  - Tight AI update rates
  - Aggressive culling and LOD

- **Mode Switching**:
  - Player-selectable in settings
  - Automatic switching based on hardware
  - Real-time mode switching (with brief loading)
  - Performance presets (Low, Medium, High, Ultra, Competitive)

**Acceptance Criteria:**
- [ ] Two distinct modes work correctly
- [ ] Immersive mode achieves 60-120 FPS
- [ ] Competitive mode achieves 300+ FPS
- [ ] Mode switching works smoothly
- [ ] Visual quality appropriate for each mode

---

#### REQ-PERF-002: Performance Budget System

**Priority**: CRITICAL  
**Estimated Time**: 40 hours

**Description:**
Define strict performance budgets for each subsystem to ensure 300+ FPS target.

**Requirements:**
- **300 FPS Budget (3.33ms total per frame)**:
  - **CPU Total**: ~1.1ms
    - AI+Gameplay: ≤0.3ms
    - Physics: ≤0.3ms
    - Animation: ≤0.3ms
    - Other CPU: ≤0.2ms
  - **GPU Total**: ~2.0ms
    - Base pass: ≤0.6ms
    - Lighting: ≤0.5ms
    - Post-processing: ≤0.3ms
    - UI: ≤0.1ms
    - Overhead: ≤0.5ms
  - **Audio**: ≤0.15ms
  - **OS/Driver/Network**: remainder

- **Budget Enforcement**:
  - CI performance harness (Unreal Insights, RenderDoc, PIX)
  - Automated captures on every commit
  - Frame time and spike detection
  - Merge gating on performance regressions
  - Per-subsystem budget tracking

- **Performance Profiling**:
  - Real-time budget visualization
  - Budget warnings in development
  - Performance regression detection
  - Automated performance reports

**Acceptance Criteria:**
- [ ] Budgets defined for all subsystems
- [ ] CI enforces performance budgets
- [ ] Performance regressions caught automatically
- [ ] Real-time budget visualization works
- [ ] 300+ FPS maintained under budget

---

#### REQ-PERF-003: Async AI Architecture (CRITICAL)

**Priority**: CRITICAL  
**Estimated Time**: 120 hours

**Description:**
Completely decouple AI inference from the game loop using a "Behavioral Proxy" architecture.

**Requirements:**
- **Proxy Model (Runs Every Frame)**:
  - Extremely simple, fast, "dumb" system
  - Behavior Tree, State Machine, or utility-based rules
  - Budget: <0.5ms per frame
  - Handles immediate, real-time actions
  - Examples: "Dodge wall", "Shoot visible enemy", "Find cover"

- **Cognitive Layer (Async)**:
  - Gold/Silver/Bronze AI runs on separate thread pool
  - Never blocks game thread
  - Updates strategy of Proxy Model (not immediate actions)
  - Operates at 0.2-2 Hz (much slower than frame rate)
  - Sends strategic directives to Proxy Model

- **Workflow Example**:
  ```
  Frame 1 (0ms): Proxy uses "Aggressive" strategy → shoots at player (0.2ms)
  Frame 1-150 (~500ms): Async Gold AI analyzes game state
  Frame 151 (~503ms): Gold AI finishes → "Change to Defensive Retreat"
  Frame 152 (~506ms): Proxy sees new directive → transitions BT to defensive
  ```

- **Implementation**:
  - Separate thread pool for AI inference
  - Message queue for strategy updates
  - Non-blocking communication
  - Caching for repeated decisions

**Acceptance Criteria:**
- [ ] AI never blocks game thread
- [ ] Proxy model runs in <0.5ms
- [ ] Async AI updates strategy correctly
- [ ] System supports 100+ NPCs
- [ ] 300+ FPS maintained with AI active

---

#### REQ-PERF-004: AI Model Optimization

**Priority**: HIGH  
**Estimated Time**: 80 hours

**Description:**
Aggressively optimize AI models for minimal latency while maintaining quality.

**Requirements:**
- **Aggressive Quantization**:
  - INT8 quantization (2× speedup)
  - INT4 quantization for proxy models (4× speedup)
  - Leverage specialized hardware (Tensor Cores)

- **Inference Engine**:
  - NVIDIA TensorRT (via DirectML plugin in UE5)
  - Model compilation for target GPU
  - Optimized memory access patterns
  - Batch processing where possible

- **Model Pruning & Distillation**:
  - Gold model: Distilled version of Silver model
  - Structured pruning (remove neurons/filters)
  - For 300 FPS: Sub-1B parameter models for proxy
  - Maintain quality through distillation

- **Modern Attention**:
  - Flash Attention / Paged Attention
  - Optimized memory access
  - Reduced memory bandwidth

**Acceptance Criteria:**
- [ ] Models quantized to INT8/INT4
- [ ] TensorRT integration working
- [ ] Model size reduced by 50%+
- [ ] Latency reduced by 2-4×
- [ ] Quality maintained

---

#### REQ-PERF-005: UE5 Rendering Optimizations

**Priority**: HIGH  
**Estimated Time**: 100 hours

**Description:**
Implement aggressive UE5 optimizations for Competitive Mode (300+ FPS).

**Requirements:**
- **Lumen Optimization (Immersive Mode Only)**:
  - Disable in Competitive Mode
  - Use baked GI + limited dynamic key lights
  - Lightmass for static lighting
  - Distance Field AO without GI component

- **VSM Optimization**:
  - Traditional CSMs in Competitive Mode
  - Tight cascade distances
  - Low resolution (512-1024)
  - Limit shadow-casting lights

- **Nanite Tuning**:
  - `r.Nanite.MaxPixelsPerEdge = 2 or 4` (reduce triangle density)
  - Simplify materials on Nanite meshes
  - Check for overdraw (shader complexity viewmode)
  - Conservative settings for Competitive Mode

- **Upscaling (MANDATORY)**:
  - DLSS/FSR/XeSS Ultra Performance mode
  - Run at lower internal resolution (720p/540p)
  - Upscale to target resolution (1080p)
  - Frame generation for "displayed" FPS > render FPS

- **GPU-Driven Pipeline**:
  - GPU-driven instancing
  - HZB occlusion culling
  - Frustum/portal culling
  - Distance/coverage-based culling
  - Conservative bounds

- **LOD & Streaming**:
  - Aggressive LOD/HLOD
  - Instance merging
  - Streaming granularity tuned for 300 FPS
  - World Partition optimization

**Acceptance Criteria:**
- [ ] Competitive Mode achieves 300+ FPS
- [ ] Upscaling provides significant performance gain
- [ ] Culling reduces draw calls by 70%+
- [ ] LOD system maintains quality at distance
- [ ] GPU utilization optimized

---

#### REQ-PERF-006: CPU Optimizations

**Priority**: HIGH  
**Estimated Time**: 60 hours

**Description:**
Optimize CPU game thread for 300+ FPS performance.

**Requirements:**
- **C++ Over Blueprints**:
  - All critical per-frame logic in C++
  - Blueprints for high-level scripting only
  - No Blueprint tick for 300 FPS systems

- **Actor Tick Management**:
  - Aggressively disable ticking on non-critical actors
  - Update Rate Optimizations (URO)
  - Distant actors: 10Hz, 2Hz, or frozen
  - Near actors: 60Hz, 120Hz, or 300Hz based on importance

- **Physics Optimization**:
  - Asynchronous scene physics
  - Simplified collision geometry
  - Reduced simulating bodies
  - Lower solver iterations

- **Culling**:
  - Push culling distances close
  - Precomputed Visibility
  - Occlusion Culling enabled
  - Aggressive frustum culling

**Acceptance Criteria:**
- [ ] CPU budget <1.1ms per frame
- [ ] Tick management reduces CPU load by 50%+
  - [ ] Physics runs asynchronously
- [ ] Culling reduces CPU work significantly

---

#### REQ-PERF-007: Frame Generation & Latency

**Priority**: MEDIUM  
**Estimated Time**: 40 hours

**Description:**
Implement frame generation technologies with latency management.

**Requirements:**
- **Frame Generation**:
  - DLSS Frame Generation (NVIDIA)
  - FSR Frame Generation (AMD)
  - XeSS Frame Generation (Intel)
  - Clarify "displayed" FPS vs. "render" FPS

- **Latency Management**:
  - NVIDIA Reflex integration
  - AMD Anti-Lag support
  - Input latency measurement
  - Competitive integrity verification

- **Settings**:
  - Toggle for frame generation
  - Latency display option
  - Performance vs. latency tradeoff settings

**Acceptance Criteria:**
- [ ] Frame generation works correctly
- [ ] Latency within acceptable range (<20ms)
- [ ] Competitive integrity maintained
- [ ] Settings provide clear options

---

## 4. IMPLEMENTATION ROADMAP

### Phase 1: Critical Foundations (Weeks 1-8)

**Priority**: CRITICAL  
**Estimated Time**: 320 hours

1. **REQ-PERF-003: Async AI Architecture** (120h)
   - Implement Behavioral Proxy system
   - Separate thread pool for AI inference
   - Message queue for strategy updates
   - Decouple AI from game loop

2. **REQ-PERF-001: Dual-Mode Performance Architecture** (100h)
   - Implement Immersive Mode
   - Implement Competitive Mode
   - Mode switching system
   - Performance presets

3. **REQ-PERF-002: Performance Budget System** (40h)
   - Define budgets for all subsystems
   - CI performance harness
   - Budget tracking and visualization

4. **REQ-PERF-004: AI Model Optimization** (60h)
   - Quantization pipeline
   - TensorRT integration
   - Model distillation

### Phase 2: NPC Individuality (Weeks 9-16)

**Priority**: HIGH  
**Estimated Time**: 300 hours

1. **REQ-NPC-001: Dialogue Style Profile System** (40h)
2. **REQ-NPC-002: Mannerism & Movement Profile** (60h)
3. **REQ-NPC-003: Social Memory & Relationship Graph** (50h)
4. **REQ-NPC-004: Daily Routines & Schedules** (40h)
5. **REQ-NPC-005: Enhanced Behavior Architecture** (80h)
6. **REQ-NPC-006: Content Pre-Baking & Caching** (30h)

### Phase 3: Environment Immersion (Weeks 17-28)

**Priority**: HIGH  
**Estimated Time**: 680 hours

1. **REQ-ENV-001: Environmental Narrative Service (ENS)** (100h)
2. **REQ-ENV-002: Multi-Resolution Detail System (MRDS)** (120h)
3. **REQ-ENV-003: Environmental Reactivity Matrix (ERM)** (100h)
4. **REQ-ENV-004: Procedural Set Dressing & Weathering** (80h)
5. **REQ-ENV-005: Audio Psychoacoustics & Advanced Mixing** (70h)
6. **REQ-ENV-006: NPC-Environment Integration (NEA)** (80h)
7. **REQ-ENV-007: World State Persistence (WSP)** (70h)
8. **REQ-ENV-008: Unnoticed Detail Generation Framework (UDG)** (60h)
9. **REQ-ENV-009: Multi-Sensory Feedback System (MSFS)** (50h)

### Phase 4: Performance Polish (Weeks 29-32)

**Priority**: HIGH  
**Estimated Time**: 200 hours

1. **REQ-PERF-005: UE5 Rendering Optimizations** (100h)
2. **REQ-PERF-006: CPU Optimizations** (60h)
3. **REQ-PERF-007: Frame Generation & Latency** (40h)

### Total Estimated Time: 1500 hours (~37.5 weeks with 40h/week)

---

## 5. PERFORMANCE BUDGETS

### 5.1 Competitive Mode (300+ FPS Target)

**Frame Budget: 3.33ms total**

| Subsystem | Budget | Notes |
|-----------|--------|-------|
| **CPU Total** | 1.1ms | |
| AI Proxy | 0.1ms | Fast behavior trees/state machines |
| Gameplay | 0.2ms | Core game logic |
| Physics | 0.3ms | Async physics, simplified |
| Animation | 0.3ms | Motion matching, LOD |
| Other CPU | 0.2ms | Audio, streaming, etc. |
| **GPU Total** | 2.0ms | |
| Base Pass | 0.6ms | Nanite optimized |
| Lighting | 0.5ms | Baked + limited dynamic |
| Post-Process | 0.3ms | Minimal effects |
| UI | 0.1ms | Optimized HUD |
| Overhead | 0.5ms | Driver, sync, etc. |
| **Audio** | 0.15ms | Reduced virtualization |
| **OS/Driver/Network** | 0.08ms | Remaining budget |

### 5.2 Immersive Mode (60-120 FPS Target)

**Frame Budget: 8.33-16.67ms total**

| Subsystem | Budget | Notes |
|-----------|--------|-------|
| **CPU Total** | 2.5ms | |
| AI (Full) | 1.0ms | Full AI system |
| Gameplay | 0.5ms | |
| Physics | 0.5ms | |
| Animation | 0.3ms | |
| Other CPU | 0.2ms | |
| **GPU Total** | 5.0ms | |
| Base Pass | 1.5ms | Full Nanite |
| Lighting (Lumen) | 2.0ms | Global illumination |
| Post-Process | 0.8ms | Full effects |
| UI | 0.2ms | |
| Overhead | 0.5ms | |
| **Audio** | 0.5ms | Full audio layers |
| **OS/Driver/Network** | 0.33ms | |

---

## 6. SUCCESS CRITERIA

### 6.1 NPC Individuality

- [ ] Players can distinguish NPCs by speech patterns alone
- [ ] NPCs have unique movement and gesture styles
- [ ] NPCs remember and reference past interactions
- [ ] NPCs follow dynamic schedules that feel natural
- [ ] Personality drives meaningful behavioral differences
- [ ] System supports 100+ unique NPCs simultaneously

### 6.2 Environment Immersion

- [ ] Environments match or exceed Red Dead Redemption 2 detail density
- [ ] Players discover stories through environmental exploration
- [ ] Audio provides accurate spatial information
- [ ] Weather and time affect all environmental systems
- [ ] Environments feel alive with ambient life
- [ ] Multi-sensory engagement (visual, audio, haptic)

### 6.3 Framerate Performance

- [ ] Competitive Mode achieves sustained 300+ FPS on high-end hardware
- [ ] Immersive Mode achieves 60-120 FPS on mid-range hardware
- [ ] Performance budgets enforced via CI
- [ ] No frame time spikes >10ms
- [ ] Frame generation works correctly
- [ ] Input latency <20ms in Competitive Mode

---

## 7. RISKS AND MITIGATIONS

### 7.1 Performance Risks

**Risk**: AI inference cannot be optimized enough for 300 FPS  
**Mitigation**: Behavioral Proxy architecture decouples AI from frame loop

**Risk**: UE5 features too expensive for 300 FPS  
**Mitigation**: Dual-mode architecture, Competitive Mode uses simplified rendering

**Risk**: Performance budgets too aggressive  
**Mitigation**: Iterative optimization, CI performance testing, budget adjustments

### 7.2 Quality Risks

**Risk**: NPC individuality reduces to repetitive patterns  
**Mitigation**: Large personality space, pre-baked content variety, caching system

**Risk**: Environmental detail impacts performance  
**Mitigation**: LOD system, streaming, performance budgets per detail type

**Risk**: Immersion features conflict with performance  
**Mitigation**: Separate modes, feature toggles, performance vs. quality tradeoffs

---

## 8. CONCLUSION

This document outlines comprehensive requirements to address critical gaps in NPC individuality, environment immersion, and framerate performance. The system has a solid foundation but requires significant enhancements to match or exceed AAA standards.

**Key Takeaways:**
1. **NPC Individuality**: Requires style profiles, mannerisms, social memory, and routines beyond basic personality vectors
2. **Environment Immersion**: Needs procedural detail, environmental storytelling, advanced audio, and ambient life systems
3. **Framerate Performance**: Requires complete architectural redesign (async AI) and aggressive optimization for 300+ FPS

**Implementation Priority:**
1. **Phase 1 (Critical)**: Async AI architecture and performance modes
2. **Phase 2 (High)**: NPC individuality enhancements
3. **Phase 3 (High)**: Environment immersion systems
4. **Phase 4 (High)**: Performance polish and optimization

With these enhancements, the system will not only match but potentially exceed current AAA game standards in immersion and performance.

---

**Document Status**: Requirements Complete (Updated with Claude 4.5 Sonnet Analysis)  
**Collaboration Models**: GPT-5, Claude 4.5 Sonnet, Gemini 2.5 Pro  
**Next Steps**: Begin Phase 1 implementation (Async AI Architecture)  
**Estimated Completion**: 37.5 weeks (with 40h/week development)

---

## ADDENDUM: Claude 4.5 Sonnet Enhanced Analysis

Claude 4.5 Sonnet provided additional depth analysis identifying:

### New Critical Systems Identified:
1. **Environmental Narrative Service (ENS)** - Critical for storytelling depth
2. **Multi-Resolution Detail System (MRDS)** - Multi-scale detail density
3. **Environmental Reactivity Matrix (ERM)** - Cross-system cascading effects
4. **NPC-Environment Integration (NEA)** - Living world interactions
5. **World State Persistence (WSP)** - Long-term consequences
6. **Unnoticed Detail Generation Framework (UDG)** - RDR2 "99% detail" philosophy

### System Rating Progression:
- **Current System**: 4/10 for AAA immersion
- **With Phase 1 Complete**: 7/10 (Matches current AAA)
- **With Phase 2 Complete**: 9/10 (Exceeds most AAA)
- **With Phase 3 Complete**: 10+/10 (Industry-defining)

### Key Innovation Opportunities:
1. **AI-Driven Environmental Storytelling** - Narrative Intelligence System
2. **Hyperrealistic Material Interactions** - Advanced Material Reactivity
3. **Living Soundscape** - Ecological Audio System
4. **Environmental Memory System** - Persistent Impact Network

