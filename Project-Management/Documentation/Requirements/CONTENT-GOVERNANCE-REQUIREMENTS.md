```markdown
# Content Governance & Content Level Requirements

**Date**: November 14, 2025  
**Version**: 2.0.0 (rewritten from scratch)  
**Status**: Phase 2 – Requirements Definition  
**Collaborators (peer models)**: GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5  

---

## 0. Purpose & Scope

- **CG‑0.1 (Purpose)**  
  Define requirements for a **Content Governance System** that ensures all generated and authored content respects:
  - player‑configured content levels,  
  - legal/ratings constraints, and  
  - the creative vision of *The Body Broker* (mature horror with body harvesting as a core mechanic).

- **CG‑0.2 (Scope)**  
  This document covers:
  - **Content Level Manager** inside the Settings service,  
  - data models and DB schema for content policies and violations,  
  - APIs and NATS subjects for policy distribution and enforcement,  
  - integration with Guardrails Monitor and Ethelred domain processors,  
  - testing and observability requirements.

- **CG‑0.3 (Non‑Goals)**  
  We do **not** specify Guardrails classifiers, ESRB/PEGI mapping policies, or UE5 rendering implementation details.

---

## 1. Existing Infrastructure & Gaps

- **CG‑1.1 (Guardrails Monitor – Existing)**  
  - Location: `services/model_management/guardrails_monitor.py`  
  - Responsibilities:
    - content safety checking (text and model outputs),  
    - addiction/safety monitoring,  
    - violation logging for AI outputs.  
  - Limitation: understands **safety** and **global policies**, but lacks per‑player content preferences.

- **CG‑1.2 (Settings Service – Existing)**  
  - Location: `services/settings/`  
  - Responsibilities:
    - user settings, feature flags, tier management.  
  - Gap: no structured **Content Level Manager** to model violence/sex/language/horror, etc.

- **CG‑1.3 (Ethelred – New)**  
  - Ethelred will:
    - classify observed content (text, audio, visuals) by category/level,  
    - validate that runtime content matches configured policy,  
    - emit `CONTENT.VIOLATION` events and Red Alerts,  
    - provide evidence back to Guardrails Monitor.

---

## 2. Content Levels & Categories

### 2.1 Category Model

- **CG‑2.1.1 (Categories)**  
  The Content Level Manager SHALL support, at minimum, the following categories:
  - `violence_gore`  
  - `sexual_content_nudity`  
  - `language_profanity`  
  - `horror_intensity`  
  - `drugs_substances`  
  - `sensitive_themes` (suicide, self‑harm, abuse, mental illness)  
  - `moral_complexity`

- **CG‑2.1.2 (Levels per Category)**  
  Each category SHALL be represented by a discrete level scale, e.g.:
  - `0 = none`,  
  - `1 = mild`,  
  - `2 = moderate`,  
  - `3 = strong`,  
  - `4 = extreme`  
  (exact meanings documented in design docs; values stored as small integers).

- **CG‑2.1.3 (Composite Profiles)**  
  A **content profile** SHALL be defined as:
  - a named set of per‑category allowed levels (e.g., `TeenSafe`, `MatureFullExperience`, `Custom`),  
  - optional boolean flags enabling/disabling sensitive themes individually.

### 2.2 Smart/Contextual Control

- **CG‑2.2.1 (Core Constraint)**  
  The game’s core mechanic (body harvesting) MAY NOT be removed. Content governance SHALL focus on **how graphic** and **how explicit** the presentation is, not whether the underlying event exists.

- **CG‑2.2.2 (Narrative Sensitivity)**  
  Requirements for violence levels (illustrative examples—non‑normative):
  - Level 2 (`moderate`): off‑screen gore, minimal descriptive detail.  
  - Level 3 (`strong`): clinical descriptions, controlled visuals, no gratuitous focus.  
  - Level 4 (`extreme`): full detail, visceral descriptions, explicit horror.  
  Exact mapping to camera angles and text tone SHALL be defined in implementation docs; Content Governance only specifies **that such mappings must exist**.

- **CG‑2.2.3 (Context Awareness)**  
  The Content Level Manager SHALL support:
  - main‑story critical scenes where content cannot be skipped but can be toned down,  
  - optional side content that may be fully omitted for low‑level profiles,  
  while preserving overall narrative coherence.

---

## 3. Content Level Manager (Settings Service)

### 3.1 Location & Components

- **CG‑3.1.1 (Module Layout)**  
  The Settings service SHALL add:
  - `content_level_manager.py` – core logic, policy evaluation, caching, and API binding,  
  - `content_schemas.py` – Pydantic models / dataclasses for content profiles and per‑session policy,  
  - `tests/test_content_levels.py` – unit tests and contract tests.

### 3.2 Core Responsibilities

- **CG‑3.2.1 (Profile Registry)**  
  Manage a registry of **system default** profiles (e.g., `TeenSafe`, `MatureFullExperience`) and allow creation of **custom profiles** per account or parental control.

- **CG‑3.2.2 (Per‑Player Policy)**  
  For each player, the manager SHALL:
  - associate an active content profile,  
  - allow per‑category overrides where permitted (e.g., allow strong language but mild gore),  
  - expose an **effective policy snapshot** to downstream services.

- **CG‑3.2.3 (Per‑Session Policy Snapshot)**  
  On session start, the manager SHALL:
  - compute the effective content policy (profile + overrides),  
  - store a per‑session snapshot with a `policy_version`,  
  - expose this snapshot to Guardrails Monitor, Story Teller, Language System, UE5, and Ethelred.

### 3.3 Database Schema Requirements

> SQL below is illustrative; actual DDL to be finalized in migrations. Requirements focus on shape and constraints.

- **CG‑3.3.1 (`content_levels` table)**  
  Must support:
  - unique `name` per profile,  
  - description field,  
  - numeric columns for each category level (`violence_level`, `sexual_level`, etc.) with CHECK constraints matching allowed ranges,  
  - flags like `is_system_default`, `target_age_rating`, timestamps, and `created_by`.

- **CG‑3.3.2 (`player_content_profiles` table)**  
  Must store:
  - `player_id`,  
  - `base_level_id` (FK to `content_levels`),  
  - optional per‑category overrides,  
  - optional JSONB `custom_rules`,  
  - audit columns (`updated_at`, `updated_by`).

- **CG‑3.3.3 (`session_content_policy` table)**  
  Must store:
  - `session_id` (FK to sessions),  
  - frozen `level_id` or inlined per‑category levels,  
  - optional overrides,  
  - `policy_version` for cache invalidation,  
  - timestamps for when policy was applied.

- **CG‑3.3.4 (`content_violations` table)**  
  Must store:
  - `violation_id` (UUID),  
  - `session_id`, `player_id?`,  
  - `content_type` (e.g., `story_output`, `npc_dialogue`, `visual_scene`),  
  - `category`, `expected_level`, `observed_level`,  
  - `severity`, `action_taken`,  
  - `detected_by` (`guardrails_monitor`, `ethelred_content_validator`),  
  - optional `flagged_excerpt` and JSONB `context`,  
  - indexes on `session_id`, `category`, `severity`.

---

## 4. APIs & Messaging

### 4.1 Settings Service HTTP / NATS API

- **CG‑4.1.1 (Profile Management API)**  
  The Settings service SHALL expose admin‑only endpoints (and/or NATS subjects) for:
  - creating/updating content profiles,  
  - listing profiles and their category levels,  
  - marking profiles as system defaults.

- **CG‑4.1.2 (Player Policy API)**  
  Provide endpoints / subjects:
  - `GET /players/{player_id}/content-policy` → current effective policy,  
  - `PUT /players/{player_id}/content-policy` → change base profile/overrides (with validation and audit).

- **CG‑4.1.3 (Session Snapshot Messaging)**  
  On session start, Settings SHALL publish on NATS:
  - `settings.content_policy.session_started` with payload containing `session_id`, `player_id`, `policy_snapshot`, `policy_version`.

### 4.2 Guardrails & Ethelred Integration

- **CG‑4.2.1 (Guardrails Input)**  
  Guardrails Monitor SHALL subscribe to policy snapshots and:
  - apply them to model safety filters,  
  - include `policy_version` in its internal caches.

- **CG‑4.2.2 (Ethelred Validation)**  
  Ethelred’s Content Validation subsystem SHALL:
  - retrieve the effective policy for a session,  
  - compare observed category/levels from text/vision/audio analysis with allowed levels,  
  - emit `CONTENT.VIOLATION` events and write to `content_violations`.

- **CG‑4.2.3 (Violation Feedback Loop)**  
  Guardrails Monitor MAY request evidence for violations from Ethelred via dedicated subjects (e.g., `guardrails.content_violation.request_evidence`), and Ethelred SHALL respond with references to the relevant media and logs.

---

## 5. Observability & Governance Metrics

- **CG‑5.1 (Coverage Metrics)**  
  The system SHALL report, per build and environment:
  - % of assets/dialogue/scenes with explicit content annotations,  
  - % of player sessions with a valid policy snapshot,  
  - count and rate of content violations by category and profile.

- **CG‑5.2 (Drift & Regression)**  
  Report build‑to‑build changes in:
  - distribution of observed category levels,  
  - distribution of player profile choices,  
  - violation rates.  
  Large unexplained shifts MUST trigger alerts for design/production review.

- **CG‑5.3 (Auditability)**  
  All profile changes and policy overrides MUST:
  - be audit logged (who, when, what changed),  
  - be reconstructible for compliance audits (ESRB/PEGI/legal).

---

## 6. Testing & Validation

- **CG‑6.1 (Unit & Contract Tests)**  
  `content_level_manager` and its schemas MUST have tests covering:
  - profile creation and validation,  
  - per‑player and per‑session policy resolution,  
  - edge cases (missing values, invalid levels, conflicting overrides).

- **CG‑6.2 (Scenario Tests)**  
  Define scenario suites where:
  - a player with `TeenSafe` profile plays curated content; Ethelred must flag any over‑level scenes,  
  - a `MatureFullExperience` profile sees full game content with **no false violations**.

- **CG‑6.3 (Integration Tests)**  
  For each environment:
  - verify Settings → Guardrails → Ethelred flow end‑to‑end using test profiles and scripted content,  
  - confirm that violations appear both in application logs and `content_violations` table.

- **CG‑6.4 (Manual Review Hooks)**  
  Provide tooling for QA/designers to:
  - review violations by category/scene,  
  - mark false positives/negatives,  
  feeding back into classifier/threshold tuning (outside scope of this doc).

---

**End of Content Governance & Content Level Requirements v2.0.0**
```

Response:
{
  "level_id": "uuid",
  "name": "Teen Safe",
  "created_at": "2025-11-14T12:00:00Z"
}
```

#### 4.1.2 Get Content Level
```
GET /content-levels/{level_id}

Response:
{
  "level_id": "uuid",
  "name": "Teen Safe",
  "description": "Reduced violence and horror",
  "violence_score": 2,
  "sexual_content_score": 0,
  "language_score": 1,
  "horror_score": 1,
  "target_age_rating": "T",
  "version": 1
}
```

#### 4.1.3 Update Content Level
```
PATCH /content-levels/{level_id}
Authorization: Bearer <admin_token>

Request:
{
  "violence_score": 3,
  "description": "Updated description"
}

Response:
{
  "level_id": "uuid",
  "version": 2,
  "updated_at": "2025-11-14T12:05:00Z"
}
```

#### 4.1.4 Set Session Content Policy
```
PUT /sessions/{session_id}/content-policy
Authorization: Bearer <player_token>

Request:
{
  "level_id": "uuid",
  "violence_override": 4, // Optional: override specific category
  "custom_rules": {
    "skip_torture_scenes": true
  }
}

Response:
{
  "session_id": "uuid",
  "level_id": "uuid",
  "effective_policy": {
    "violence_score": 4, // Override applied
    "sexual_content_score": 0,
    "language_score": 1,
    "horror_score": 1
  },
  "version": 1
}
```

#### 4.1.5 Get Session Content Policy
```
GET /sessions/{session_id}/content-policy

Response:
{
  "session_id": "uuid",
  "level_id": "uuid",
  "level_name": "Teen Safe",
  "effective_policy": {
    "violence_score": 2,
    "sexual_content_score": 0,
    "language_score": 1,
    "horror_score": 1,
    "allow_crime_themes": true
  },
  "version": 1
}
```

### 4.2 Integration with Guardrails Monitor

#### 4.2.1 Content Check Request
```
POST /model-management/guardrails/check
Authorization: Bearer <service_token>

Request:
{
  "session_id": "uuid",
  "content_type": "story_output",
  "content": "The liver is putrid green, reeking of rot...",
  "model_id": "story_teller_v1"
}

Response:
{
  "passed": true,
  "content_policy": {
    "violence_score": 5, // Player allows extreme
    "version": 1
  },
  "issues": [],
  "filtered_content": null // No filtering needed
}
```

#### 4.2.2 Content Policy Cache Invalidation
**NATS Topic**: `content.level.changed`

```json
{
  "event": "session_policy_updated",
  "session_id": "uuid",
  "old_version": 1,
  "new_version": 2,
  "timestamp": "2025-11-14T12:00:00Z"
}
```

**Guardrails Monitor subscribes to this topic, invalidates cache.**

---

## 5. ENFORCEMENT ARCHITECTURE

### 5.1 Enforcement Points

#### 5.1.1 Story Teller Service
- **When**: Before generating quest text, NPC dialogue, narrative descriptions
- **How**: Checks player's content policy, adjusts generation parameters
- **Example**: Violence Level 3 → prompt includes "Use clinical language, avoid graphic details"

#### 5.1.2 Model Management / Guardrails Monitor
- **When**: After content generation, before sending to player
- **How**: Analyzes generated text, compares against player's content policy
- **Action**: Filter, block, or replace violating content

#### 5.1.3 AI Integration Service
- **When**: LLM inference time
- **How**: Applies content-aware system prompts
- **Example**: "Player is 16 years old. Keep language appropriate."

#### 5.1.4 Quest System Service
- **When**: Quest generation
- **How**: Filters quest templates by content level
- **Example**: Violence Level 2 → exclude "torture victim" quests

#### 5.1.5 Environmental Narrative Service
- **When**: Ambient storytelling
- **How**: Adjusts atmosphere, descriptions
- **Example**: Horror Level 1 → "eerie" not "terrifying"

### 5.2 Validation Methods

#### 5.2.1 Automated Text Analysis
- **Technology**: Keyword matching, sentiment analysis, violence classifiers
- **Pros**: Fast, deterministic
- **Cons**: Misses context, false positives
- **Use**: Real-time filtering

#### 5.2.2 Vision Analysis
- **Technology**: 4D Vision System analyzes rendered scenes
- **Detection**: Blood/gore levels, nudity, disturbing imagery
- **Pros**: Catches visual violations text analysis misses
- **Cons**: Requires GPU, slower
- **Use**: Post-render validation

#### 5.2.3 Contextual Analysis
- **Technology**: LLM-based understanding of themes and context
- **Detection**: Understands nuance (e.g., violence in self-defense vs sadism)
- **Pros**: High accuracy, understands intent
- **Cons**: Expensive, slower
- **Use**: Complex cases, appeals

### 5.3 Enforcement Modes

#### 5.3.1 Real-Time Filtering
- **When**: Story Teller, Audio, NPC Dialogue
- **Latency**: <30ms overhead
- **Method**: Pre-generation (adjust prompts) + post-generation (filter output)

#### 5.3.2 Post-Generation Validation
- **When**: 4D video summaries, transcripts
- **Latency**: Async, not time-critical
- **Method**: Full Guardrails Monitor analysis with contextual understanding

---

## 6. PERFORMANCE REQUIREMENTS

### 6.1 Content Level Manager

#### 6.1.1 Read Performance
- **Volume**: ~2000 queries per second (one per AI request)
- **Latency**: <5ms database lookup
- **Caching**: Redis cache with 5-minute TTL
- **Scaling**: 1 PostgreSQL read replica

#### 6.1.2 Write Performance
- **Volume**: Rare (player changes settings, admin updates levels)
- **Latency**: <50ms acceptable
- **Cache Invalidation**: NATS event triggers immediate cache clear

### 6.2 Guardrails Monitor Integration

#### 6.2.1 Overhead
- **Lookup**: <5ms (cached policy fetch)
- **Analysis**: Depends on method
  - Text: <10ms (keyword/classifier)
  - Vision: <200ms (GPU-based)
  - Contextual: <500ms (LLM-based)

#### 6.2.2 Scaling
- **Stateless**: Guardrails Monitor runs in ECS, scales horizontally
- **Cache**: Redis shared across instances

---

## 7. CONTENT ADAPTATION EXAMPLES

### 7.1 Violence Adaptation

**Scene**: Player harvests organs from corpse

| Level | Text Description | Visual Presentation | Audio |
|-------|------------------|---------------------|-------|
| 0 | "You gather the required items." | Camera cuts away entirely | Silence |
| 1 | "You carefully extract the organs." | Camera zooms out, silhouette | Ambient only |
| 2 | "You perform the extraction with surgical precision." | Medical diagram overlay | Clinical sounds |
| 3 | "You retrieve the liver, noting its unusual size." | Camera pulls back, implies action | Muffled surgical sounds |
| 4 | "The liver is discolored and swollen." | Close-up, clinical detail | Surgical sounds, breathing |
| 5 | "The putrid green liver reeks of rot. Bile rises in your throat." | Full detail, blood, viscera | Wet sounds, gagging |

### 7.2 Horror Adaptation

**Scene**: Encountering a vampire NPC

| Level | Atmosphere | Description | Behavior |
|-------|-----------|-------------|----------|
| 0 | None | "A pale figure approaches." | Friendly, non-threatening |
| 1 | Mild | "An unnaturally pale figure with piercing eyes." | Unsettling but calm |
| 2 | Moderate | "A corpse-pale vampire, eyes gleaming with hunger." | Tense dialogue, sudden movements |
| 3 | Intense | "The vampire's stillness is uncanny. No breath, no heartbeat." | Psychological tension, implied threat |
| 4 | Extreme | "Its eyes are empty voids. Your hindbrain screams to run." | Full horror, body horror details |

### 7.3 Language Adaptation

**Scene**: NPC reacts to player's betrayal

| Level | Dialogue |
|-------|----------|
| 0 | "You betrayed me! I trusted you!" |
| 1 | "Damn you! I trusted you!" |
| 2 | "You bastard! I trusted you!" |
| 3 | "You fucking traitor! I trusted you!" |
| 4 | "You fucking piece of shit! I trusted you!" |

---

## 8. AGE RATING COMPLIANCE

### 8.1 ESRB Ratings

**The Body Broker Default**: Mature (M) 17+

**Content Descriptors**:
- Blood and Gore
- Intense Violence
- Strong Language
- Use of Drugs
- Mature Humor
- Suggestive Themes

### 8.2 PEGI Ratings

**The Body Broker Default**: PEGI 18

**Content Descriptors**:
- Extreme Violence
- Bad Language
- Horror
- Discrimination (moral choices)

### 8.3 Regional Variations

#### 8.3.1 Germany (USK)
- **Challenge**: Stricter violence regulations
- **Adaptation**: Offer Violence Level 3 as "German Safe" preset

#### 8.3.2 Australia (ACB)
- **Challenge**: Banned content (realistic violence against realistic humans)
- **Adaptation**: Emphasize Dark World (supernatural) vs Human World (realistic)

#### 8.3.3 China
- **Challenge**: No skulls, blood, ghosts
- **Adaptation**: Extensive visual replacements (may require separate build)

---

## 9. USER EXPERIENCE

### 9.1 First-Time Setup

**On First Launch**:
1. Show age gate: "How old are you?"
2. Based on age, recommend content level:
   - <13: "This game is not suitable for you."
   - 13-16: Recommend "Teen Safe"
   - 17+: Recommend "Mature" (default experience)
3. Allow player to preview/customize before starting

### 9.2 In-Game Settings

**Settings Menu**:
```
Content Settings
├── Preset: [Teen Safe | Mature | Custom]
├── Violence: [0 ─────●── 5] (slider)
├── Sexual Content: [0 ──●────── 3]
├── Language: [0 ────●─── 4]
├── Horror: [0 ─────●── 4]
├── Themes:
│   ├── [ ] Suicide/Self-Harm
│   ├── [ ] Addiction
│   └── [✓] Crime (cannot disable - core mechanic)
└── [Apply] [Reset to Default]
```

### 9.3 Dynamic Warnings

**When Player About to Enter High-Content Area**:
```
WARNING: This quest contains extreme violence and horror.
Your settings: Violence 3, Horror 2

Options:
1. Continue (content will be adapted to your settings)
2. Increase settings temporarily for this quest
3. Skip this quest (miss rewards)
```

---

## 10. TESTING REQUIREMENTS

### 10.1 Validation Testing

#### 10.1.1 Automated Tests
- **Test Each Content Level**: Generate 1000 outputs per level
- **Measure Compliance**: <1% violations per level
- **False Positive Rate**: <5%

#### 10.1.2 Human Review
- **Sample**: 100 outputs per content level
- **Review**: Does adapted content match intent?
- **Adjust**: Refine filtering rules based on feedback

### 10.2 Edge Cases

#### 10.2.1 Context-Dependent Content
- **Example**: "Fuck" as exclamation (high language) vs sexual act (sexual content)
- **Requirement**: Contextual analysis must distinguish

#### 10.2.2 Cultural Sensitivity
- **Example**: Nudity acceptable in European markets, not in US
- **Requirement**: Regional content levels

#### 10.2.3 Player Maturity Mismatch
- **Example**: 12-year-old claims to be 18
- **Response**: Cannot prevent technically, but violates ToS

---

## 11. PRIORITY & PHASING

### 11.1 Phase 1: Foundation (Week 1-2)
- ✅ Create Content Level Manager module
- ✅ Define database schema
- ✅ Implement basic CRUD API
- ✅ Create system default levels (Teen Safe, Mature)

### 11.2 Phase 2: Integration (Week 3-4)
- ✅ Integrate with Settings Service
- ✅ Connect Guardrails Monitor to Content Level Manager
- ✅ Implement cache + NATS event system
- ✅ Add session content policy endpoints

### 11.3 Phase 3: Enforcement (Week 5-6)
- ✅ Implement text analysis filters
- ✅ Integrate with Story Teller (pre-generation prompts)
- ✅ Integrate with Model Management (post-generation filtering)
- ✅ Add vision analysis integration

### 11.4 Phase 4: Polish (Week 7-8)
- ✅ Contextual analysis (LLM-based)
- ✅ UI for player content settings
- ✅ Dynamic warnings
- ✅ Regional variations

---

## 12. DEPENDENCIES

### 12.1 Internal
- **Settings Service**: Must be operational
- **Guardrails Monitor**: Must be operational (CONFIRMED ✅)
- **Model Management**: For LLM-based contextual analysis
- **Story Teller**: For pre-generation adaptation
- **4D Vision System**: For visual content validation

### 12.2 External
- **OpenAI Moderation API**: Used by Guardrails Monitor
- **Content classification models**: For automated analysis

---

## 13. SUCCESS CRITERIA

### 13.1 Functionality
- ✅ Content Level Manager operational in Settings Service
- ✅ Guardrails Monitor checks player settings before filtering
- ✅ All 3 validation methods working (text, vision, contextual)
- ✅ Player can set and change content preferences

### 13.2 Performance
- ✅ <5ms content policy lookup (P95)
- ✅ <30ms real-time filtering overhead (P95)
- ✅ Cache hit rate >95%

### 13.3 Compliance
- ✅ <1% content violations per level
- ✅ <5% false positive rate
- ✅ Regional age rating compliance

### 13.4 User Experience
- ✅ Settings clear and intuitive
- ✅ Adaptations maintain immersion
- ✅ NO complaints about censorship breaking game

---

**Next Phase**: Solutions (Design enforcement architecture)  
**Document Status**: Complete for peer review

