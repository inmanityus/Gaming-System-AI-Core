```markdown
# ETHELRED-COMPREHENSIVE-REQUIREMENTS

**Date**: November 14, 2025  
**Version**: 2.0.0 (requirements rewritten from scratch)  
**Status**: Phase 2 – Requirements Definition (Architecture‑Complete)  
**Collaborators (peer models)**: GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5  

---

## 0. Document Purpose & Scope

- **R‑0.1 (Purpose)**  
  This document defines the **WHAT** for Ethelred – the AI “game perfection” system for *The Body Broker* – across vision, audio, emotional analytics, content governance, story coherence, multi‑language QA, and (later) website/social AI.

- **R‑0.2 (Non‑Goals)**  
  This document does **not** prescribe specific model architectures, libraries, or algorithms. All requirements are stated in terms of **inputs, outputs, metrics, contracts, and constraints**.

- **R‑0.3 (System Context)**  
  Ethelred operates in the context of:
  - UE 5.6.1 game client (player view, cameras, audio, gameplay events).  
  - 22 Python microservices connected via NATS (Story Teller, Model Management + Guardrails Monitor, Language System, NPC Behavior, Quest System, Settings, etc.).  
  - Archetype Model Chain System (adapter‑based personality/behavior) and Vocal Synthesis system.  
  - Existing **Red Alert** AI Testing System (ai‑testing‑system/) for report generation.

- **R‑0.4 (Traceability)**  
  Every requirement in this document SHALL be:
  - uniquely identified (e.g., `R‑4D‑DET‑003`), and  
  - traceable to at least one game goal:  
    - `G‑IMMERSION` – deep, believable horror immersion  
    - `G‑HORROR` – sustained tension, dread, unease  
    - `G‑MORAL` – meaningful moral complexity  
    - `G‑LONGTERM` – long‑term engagement without predatory mechanics  

---

## 1. System‑Wide Requirements

### 1.1 Architectural Principles

- **R‑SYS‑ARCH‑001 (Microservice & Message First)**  
  Ethelred SHALL expose domain‑specific functionality via **dedicated services** (4D Vision, Audio, Engagement, Content, Story, Language, Website/Social) communicating over NATS subjects and/or HTTP/gRPC APIs. No domain logic may be hard‑coded in UE5.

- **R‑SYS‑ARCH‑002 (Coordinator Role)**  
  A central **Ethelred Coordinator** service SHALL:
  - subscribe to gameplay/telemetry streams,  
  - route work to domain processors,  
  - aggregate results into reports and metrics, and  
  - forward enforcement‑relevant signals to **Guardrails Monitor**.

- **R‑SYS‑ARCH‑003 (Guardrails as Enforcement Authority)**  
  Guardrails Monitor in Model Management SHALL remain the **sole authority** for real‑time safety/content enforcement.  
  Ethelred:
  - provides evidence, scores, and recommendations;  
  - MUST NOT directly force‑kill sessions, censor content, or change player settings.

### 1.2 Data, Privacy & Governance

- **R‑SYS‑DATA‑001 (Pseudonymous Identifiers)**  
  All Ethelred events involving real players SHALL use pseudonymous game identifiers (`session_id`, `player_id`) and **MUST NOT** contain real‑world PII.

- **R‑SYS‑DATA‑002 (AI vs Real Separation)**  
  All events SHALL distinguish **AI Player** runs from **real player** sessions using an explicit `actor_type` field (`ai_player`, `real_player`, `test_rig`).

- **R‑SYS‑DATA‑003 (Retention & Deletion)**  
  Ethelred SHALL support configurable retention windows per environment (e.g., 30/90/365 days) and MUST be able to delete all stored evidence and derived metrics for a given `player_id` to satisfy deletion/opt‑out requests.

- **R‑SYS‑DATA‑004 (Media Handling)**  
  When full media (video, depth, audio) is stored, Ethelred SHALL:
  - store media in Red Alert / media storage with versioned keys,  
  - store only references + metadata in its own event logs,  
  - respect environment‑specific retention and encryption policies.

### 1.3 Observability & Telemetry

- **R‑SYS‑OBS‑001 (Canonical Event Envelope)**  
  All domain processors SHALL emit events in a shared envelope shape:
  - `trace_id`, `session_id`, `player_id?`, `build_id`, `timestamp_range`,  
  - `domain` (4D, Audio, Engagement, Content, Story, Lang, Social),  
  - `issue_type` or `metric_type`, `severity`, `confidence`,  
  - `evidence_refs[]` (URIs into Red Alert/media systems),  
  - `goal_tags[]` (subset of `G‑IMMERSION`, `G‑HORROR`, `G‑MORAL`, `G‑LONGTERM`).

- **R‑SYS‑OBS‑002 (Structured Logging & Metrics)**  
  Each service SHALL expose:
  - structured logs (JSON) with correlation IDs;  
  - metrics for latency, throughput, error rates, and model confidence distributions;  
  - health endpoints (`/healthz`, `/metrics`) for Prometheus/Grafana.

- **R‑SYS‑OBS‑003 (Traceability to Builds)**  
  Every event and report SHALL include `build_id` and `config_version` so regressions can be tracked per build/config combination.

### 1.4 Safety, Ethics & Failure Modes

- **R‑SYS‑SAFE‑001 (No Predatory Optimization)**  
  Ethelred SHALL NOT:
  - optimize for engagement metrics that are explicitly marked as **addiction indicators**;  
  - adjust live content per‑player in order to exploit those indicators (§3).

- **R‑SYS‑SAFE‑002 (Graceful Degradation)**  
  If a domain processor is unavailable or timing out:
  - the Coordinator SHALL label that domain as `degraded`,  
  - game runtime SHALL continue using conservative defaults (e.g., strict content policy) rather than failing hard,  
  - a `SYS.HEALTH` event SHALL be emitted instead of mis‑labelling the issue as a game bug.

- **R‑SYS‑SAFE‑003 (Kill Switch & Feature Flags)**  
  Operators MUST be able to:
  - disable any domain processor (4D, Audio, etc.) via configuration,  
  - globally disable Ethelred analysis while leaving Guardrails safety active.

- **R‑SYS‑SAFE‑004 (Explainability)**  
  For every Red Alert / UI‑visible issue produced by Ethelred, a human‑readable explanation MUST be persisted indicating **which signals** and **which thresholds** triggered the verdict.

---

## 2. 4D Vision QA (Video + Depth + Time)

### 2.1 Objectives

- **R‑4D‑OBJ‑001**  
  Replace screenshot‑based checks with **multi‑camera, time‑based** analysis that detects issues in:
  - animation and rigging,  
  - physics and collisions,  
  - rendering and lighting,  
  - performance (FPS, frame pacing),  
  - character presence and staging,  
  - environment and navigation,  
  - gameplay flow and soft‑locks,  
  to support `G‑IMMERSION` and `G‑HORROR`.

### 2.2 Inputs & Instrumentation

- **R‑4D‑IN‑001 (Multi‑Camera Feeds)**  
  UE5 SHALL provide:
  - at least one **player POV** camera feed,  
  - at least one **debug/overview** camera,  
  - optional additional test cameras for specific scenes,  
  each with RGB frames and associated **depth** (Z‑buffer or equivalent).

- **R‑4D‑IN‑002 (Synchronization & Metadata)**  
  Each frame bundle MUST include:
  - `timestamp`, `camera_id`, `scene_id`, `build_id`,  
  - camera pose + FOV,  
  - per‑frame performance metrics (frame time, FPS, GPU/CPU markers),  
  - key gameplay events (damage, deaths, dialogue triggers) aligned within ≤20 ms.

- **R‑4D‑IN‑003 (Sampling Modes)**  
  The 4D Vision service SHALL support:
  - **Frame‑level** sampling (every frame; dev/QA only),  
  - **Window‑based** sampling (e.g., 5–10s clips at intervals),  
  - **Event‑based** sampling (pre/post critical events, deaths, scares, boss fights).

### 2.3 Detection Requirements

The 4D Vision service SHALL emit issue events including (non‑exhaustive):

- **R‑4D‑DET‑001 (Animation & Rigging)**  
  Detect:
  - T‑pose/A‑pose in gameplay,  
  - foot sliding and ground penetration,  
  - frozen or popping animations,  
  - gross skeleton mis‑alignments breaking realism.

- **R‑4D‑DET‑002 (Physics & Collisions)**  
  Detect:
  - intersection/clipping between characters and geometry,  
  - ragdoll instability (jitter, infinite spinning),  
  - bodies/props penetrating or stuck in walls/floors.

- **R‑4D‑DET‑003 (Rendering & Visual Artifacts)**  
  Detect:
  - missing textures / fallback materials,  
  - Z‑fighting, severe LOD popping in the player’s focus area,  
  - abnormal brightness/contrast flicker unrelated to scripted effects.

- **R‑4D‑DET‑004 (Lighting & Horror Atmosphere)**  
  Detect:
  - key horror scenes that are unexpectedly bright/dim vs. level metadata,  
  - missing key lights or flicker effects,  
  - shadows detached from casters in visible areas.

- **R‑4D‑DET‑005 (Performance & Frame Pacing)**  
  Detect:
  - sustained FPS below configured thresholds in critical scenes,  
  - severe frame time spikes and micro‑stutter even at nominal FPS.

- **R‑4D‑DET‑006 (Gameplay Flow & Soft‑Locks)**  
  Detect:
  - repeated back‑and‑forth motion without progress,  
  - player stuck states (no valid navigation paths, blocked doors),  
  - camera occlusion of player/NPC in interactive moments.

### 2.4 Outputs & Metrics

- **R‑4D‑OUT‑001 (Issue Records)**  
  For each issue, the service SHALL emit a `VISION.ISSUE` event with:
  - issue type & subtype (from a controlled vocabulary),  
  - severity (configurable scale), confidence score,  
  - time range and camera IDs,  
  - relevant entity IDs (player, NPCs, actors),  
  - performance metrics around the issue,  
  - `evidence_refs` to stored clips.

- **R‑4D‑OUT‑002 (Scene‑Level Summaries)**  
  For each analyzed scene/segment, the service SHALL emit quality scores for:
  - animation, physics, rendering, lighting, performance, flow,  
  plus a short summary string for use in Red Alert.

- **R‑4D‑OUT‑003 (Coverage Metrics)**  
  Per build, Ethelred SHALL compute:
  - fraction of main horror scenes covered by 4D analysis,  
  - counts of issues per level/scene,  
  - trend reports across builds (improving/regressing areas).

---

## 3. Audio Authentication & Vocal Simulator QA

> **Design stance**: Requirements are expressed in terms of **measured capabilities** (prosody, formants, spectral characteristics, alignment with archetype profiles). Implementations MAY use classical DSP, ML discriminators, or hybrids, as long as they satisfy these outputs.

### 3.1 Objectives

- **R‑AUD‑OBJ‑001**  
  Evaluate and report on:
  - human voice **intelligibility** and **naturalness**,  
  - archetype voice **conformity** (vampire, werewolf, zombie, etc.),  
  - **stability** and **fidelity** of the physical vocal cord simulator.

- **R‑AUD‑OBJ‑002**  
  Use corpora such as **LibriSpeech**, **Common Voice**, and **VCTK** as baseline reference distributions for human speech metrics (not necessarily training data).

### 3.2 Inputs & Capture

- **R‑AUD‑IN‑001 (Virtual Routing Only)**  
  All analyzed audio MUST be captured via **virtual audio routing** (loopback) from the game mix or channel buses; no physical microphones are required.

- **R‑AUD‑IN‑002 (Segment Metadata)**  
  Each audio segment SHALL include:
  - `timestamp_range`,  
  - speaker identifier (`npc_id` / archetype / narrator / player),  
  - language code,  
  - context (line ID, scene ID, emotional tag, environment type),  
  - indicator whether audio passed through the vocal cord simulator.

### 3.3 Evaluation Dimensions & Metrics

- **R‑AUD‑MET‑001 (Human Intelligibility)**  
  For human‑voiced lines, compute an **intelligibility score** (0–1) based on:
  - lexical recognition/ASR proxy,  
  - SNR and distortion measures,  
  and classify into bands: `acceptable`, `degraded`, `unacceptable`.

- **R‑AUD‑MET‑002 (Human Naturalness & Prosody)**  
  Compute a **naturalness score** using:
  - pitch contour variability,  
  - speech rate vs language norms,  
  - prosodic variability (stress/rhythm),  
  and flag segments with robotic or repetitive prosody.

- **R‑AUD‑MET‑003 (Archetype Conformity)**  
  For each monster archetype, maintain target bands for:
  - F0 range & variability,  
  - formant distribution (timbre),  
  - roughness/breathiness or “corruption” measures,  
  and compute an **archetype conformity score** (0–1).

- **R‑AUD‑MET‑004 (Simulator Stability)**  
  For simulator‑produced/modified audio, compute:
  - jitter, shimmer, onset/offset stability,  
  - artifact counts (clicks, pops, loops),  
  and track per‑archetype stability metrics across builds.

- **R‑AUD‑MET‑005 (Mix/Recording Quality)**  
  Compute a **mix quality score** including:
  - clipping/distortion detection,  
  - noise floor,  
  - dynamic range,  
  - environment‑appropriate reverb/FX given scene metadata.

### 3.4 Outputs & Reports

- **R‑AUD‑OUT‑001 (Per‑Segment Scores)**  
  For each segment, emit `AUDIO.SCORES` event with:
  - intelligibility, naturalness, archetype conformity, mix quality (0–1),  
  - classification bands and confidence,  
  - `evidence_refs` to WAV/OGG snippets.

- **R‑AUD‑OUT‑002 (Archetype Batch Reports)**  
  Per build, generate aggregate reports per archetype:
  - score distributions,  
  - most common deviations (too clean, too flat, not monstrous enough),  
  - comparison vs previous builds to highlight regressions/improvements.

- **R‑AUD‑OUT‑003 (Red Alerts – Audio)**  
  Emit high‑severity alerts when:
  - key narrative lines fall below a configured intelligibility threshold,  
  - major artifacts occur in marked “hero scenes”,  
  - archetype conformity drops sharply vs previous build.

### 3.5 Feedback to Vocal Synthesis & Archetype Chain

- **R‑AUD‑FB‑001 (Simulator Feedback)**  
  Where simulator parameters are available, Ethelred SHALL:
  - correlate systematic deviations (e.g., insufficient roughness) with parameter deltas,  
  - export structured recommendations for offline tuning (no auto‑tuning in live builds).

- **R‑AUD‑FB‑002 (Archetype Chain Feedback)**  
  Emit metrics consumable by Archetype Chain system:
  - per‑archetype voice quality scores,  
  - out‑of‑profile examples for potential training data.

---

## 4. Emotional Engagement & Addiction Analytics

### 4.1 Objectives

- **R‑EMO‑OBJ‑001**  
  Quantify **emotional engagement** and **moral connection** to NPCs and story arcs using in‑game telemetry and optional AI Player simulations.

- **R‑EMO‑OBJ‑002**  
  Identify **addiction‑like patterns** at cohort level (not per‑player exploitation) and surface them to design/production as **warnings**, not optimization targets.

### 4.2 Data Collection

- **R‑EMO‑DATA‑001 (NPC Interaction Telemetry)**  
  Capture, per session and NPC:
  - dialogue choices (help/harm/neutral),  
  - protective vs abusive actions,  
  - time spent in proximity,  
  - optional gifts or resource allocations.

- **R‑EMO‑DATA‑002 (Session Metrics)**  
  Capture:
  - session start/end time,  
  - duration,  
  - number of sessions per day/week,  
  - return intervals.

- **R‑EMO‑DATA‑003 (AI Player Personality Runs)**  
  For AI Player runs, tag sessions with personality archetypes (e.g., empathetic, ruthless, risk‑averse) and store their behavior as **synthetic baselines**.

### 4.3 Engagement Metrics

- **R‑EMO‑MET‑001 (NPC Attachment Index)**  
  For each key NPC, compute per‑player and aggregate metrics:
  - protection/harm ratio,  
  - attention score (time + number of voluntary interactions),  
  - abandonment frequency (ignored calls, dropped quests).

- **R‑EMO‑MET‑002 (Moral Tension Index)**  
  Compute:
  - hesitation time on key moral choices,  
  - reload/retry frequency around those points (if allowed),  
  - divergence between “safe” vs “extreme” options chosen.

- **R‑EMO‑MET‑003 (Engagement Profiles)**  
  Derive non‑identifying profiles (e.g., “lore‑driven explorer”, “combat‑focused”) from behavior patterns to understand which systems drive engagement.

### 4.4 Addiction Indicators (Non‑Predatory Use)

- **R‑EMO‑ADD‑001 (Indicators)**  
  At cohort level (e.g., per age region/segment), compute:
  - rapid escalation in average daily session time,  
  - proportion of play at biologically unusual hours,  
  - high‑frequency, short “one more run” behavior triggered by specific systems.

- **R‑EMO‑ADD‑002 (Constraints)**  
  Ethelred MUST NOT:
  - adjust session content live based on an individual’s addiction indicators,  
  - optimize for maximizing any addiction metric.

- **R‑EMO‑ADD‑003 (Reporting)**  
  Addiction indicators SHALL be surfaced only:
  - in aggregated form,  
  - to design/production/security stakeholders,  
  with explicit labels that they are **risk indicators**, not KPIs.

### 4.5 Feedback to Story Teller & Design

- **R‑EMO‑FB‑001 (Offline Recommendations)**  
  Provide periodic reports:
  - which NPCs arcs generate strong attachment,  
  - which moral choices are ignored or trivially solved,  
  - where players churn or quit in frustration.

- **R‑EMO‑FB‑002 (Slow‑Changing Bias Only)**  
  Any influence Ethelred has on Story Teller MUST:
  - operate via configuration/build‑level parameters (e.g., “increase presence of under‑engaged NPC C”),  
  - NOT personalize story progression to maximize individual play time.

---

## 5. Content Level Enforcement & Validation

### 5.1 Objectives

- **R‑CONT‑OBJ‑001**  
  Ensure that all text, audio, and visual content delivered to a player respects their configured **content level policy** (violence, sex, language, horror, drugs, themes, moral complexity).

### 5.2 Content Categories & Levels

- **R‑CONT‑CAT‑001 (Categories)**  
  At minimum, Ethelred SHALL classify content into:
  - Violence & Gore,  
  - Sexual Content & Nudity,  
  - Language/Profanity,  
  - Horror/Fear intensity,  
  - Drugs & Substance Use,  
  - Sensitive Themes (suicide, self‑harm, abuse, mental illness),  
  - Moral Complexity.

- **R‑CONT‑CAT‑002 (Levels per Category)**  
  For each category, support at least a 4–5 level scale (e.g., `none`, `mild`, `moderate`, `strong`, `extreme`) with documented semantics.

- **R‑CONT‑CAT‑003 (Composite Profiles)**  
  Player content profiles (e.g., Teen, Mature, Custom) SHALL map to allowed levels per category and be stored in the **Settings** service.

### 5.3 Policy Flow & Integration

- **R‑CONT‑FLOW‑001 (Settings as Source of Truth)**  
  Settings service SHALL:
  - store per‑player content policy,  
  - expose this via NATS/API to Model Management, Story Teller, UE5, and Ethelred.

- **R‑CONT‑FLOW‑002 (Guardrails + Model Management)**  
  Model Management + Guardrails Monitor SHALL:
  - receive the content policy,  
  - configure generative models (Story Teller, Language System) to respect allowed levels,  
  - apply safety filters in line with policy.

- **R‑CONT‑FLOW‑003 (Runtime Validation by Ethelred)**  
  Ethelred SHALL:
  - monitor generated text, images, scenes, and audio,  
  - classify observed content levels per category,  
  - compare against policy, and  
  - emit violations (`CONTENT.VIOLATION`) when observed > allowed.

### 5.4 Modalities: Text, Vision, Audio, Context

- **R‑CONT‑MOD‑001 (Text Analysis)**  
  Analyze:
  - Story Teller outputs, NPC dialogue, UI strings, item descriptions,  
  to assign category/level scores (violence, language, etc.).

- **R‑CONT‑MOD‑002 (Vision Analysis)**  
  Use 4D Vision to detect:
  - gore and dismemberment,  
  - nudity or sexualized imagery,  
  - drug apparatus usage,  
  and map to category/level.

- **R‑CONT‑MOD‑003 (Audio Analysis)**  
  Analyze:
  - spoken profanity, slurs, sexual terms, horror screams and torture sounds,  
  to assign relevant category/level values.

- **R‑CONT‑MOD‑004 (Contextual Cross‑Check)**  
  Ethelred SHALL correlate text, vision, and audio labels and flag inconsistencies (e.g., sanitized text but extreme visual gore).

### 5.5 Violations, Metrics, & Overrides

- **R‑CONT‑VIOL‑001 (Violation Logging)**  
  For each violation, log:
  - expected vs observed category/level,  
  - associated content IDs (asset IDs, line IDs, scene IDs),  
  - player policy snapshot,  
  - recommended action (substitute, block, log‑only).

- **R‑CONT‑VIOL‑002 (Real‑Time Behavior)**  
  In production, Ethelred SHALL:
  - **not** crash or halt gameplay,  
  - attempt substitution where a lower‑intensity variant exists,  
  - otherwise, log and raise Red Alerts for severe/repeated violations,  
  deferring any enforcement decision to Guardrails Monitor.

- **R‑CONT‑VIOL‑003 (Coverage & Drift Metrics)**  
  Report per build:
  - % of content with valid category annotations,  
  - number and rate of violations per profile type,  
  - build‑to‑build drift in baseline intensity distributions.

---

## 6. Story Coherence & Drift Prevention

### 6.1 Objectives

- **R‑STORY‑OBJ‑001**  
  Maintain coherence and primacy of main arcs (Dark World client families, Human crime empire, Broker’s Book, Debt of Flesh) while allowing rich Experiences and side content **without letting them become the game**.

### 6.2 Story Memory System

- **R‑STORY‑MEM‑001 (Per‑Player Story State)**  
  Ethelred SHALL use or maintain a structured story memory per player including:
  - main arc progress for each core storyline,  
  - active/completed side arcs and Experiences (with thematic tags),  
  - key irreversible choices and consequences,  
  - NPC relationship states.

- **R‑STORY‑MEM‑002 (Content Tagging)**  
  All quests, scenes, and Experiences MUST be tagged as:
  - `main_arc:<id>`,  
  - `side_arc:<id>` + theme tags (love, addiction, parenthood, etc.),  
  - `ambient` or `filler`.

### 6.3 Time Allocation & Drift Detection

- **R‑STORY‑MET‑001 (Time Budget Tracking)**  
  Track per player and per cohort:
  - time spent in each main arc,  
  - time in side arcs by theme,  
  - time in non‑narrative/filler activities.

- **R‑STORY‑MET‑002 (Drift Indicators)**  
  Detect:
  - prolonged periods (configurable hours) with **zero main arc progress**,  
  - sessions dominated by non‑horror, non‑narrative mini‑games,  
  - side‑content loops repeatedly diverting players from core arcs.

- **R‑STORY‑MET‑003 (Narrative Inconsistency)**  
  Cross‑check story memory with world state:
  - NPCs flagged as dead vs appearing alive with no narrative explanation,  
  - locations described as destroyed vs intact,  
  - broken quest chains (unreachable states).

### 6.4 Correction Mechanisms

- **R‑STORY‑CORR‑001 (Soft Steering)**  
  Recommend non‑intrusive actions (for Story Teller/UE5 to implement):
  - NPC reminders,  
  - environmental hints,  
  - new entry points back to main arcs.

- **R‑STORY‑CORR‑002 (Medium Constraints)**  
  For severe drift patterns, recommend:
  - reduced availability/frequency of low‑value side content,  
  - prioritized surfacing of main arc hooks.

- **R‑STORY‑CORR‑003 (QA‑Only Hard Constraints)**  
  In QA/dev builds, Ethelred MAY:
  - block or warn when new content is untagged or out‑of‑genre for extended durations,  
  so designers can fix drift before shipping.

### 6.5 Story Dashboards

- **R‑STORY‑OBS‑001**  
  Provide dashboards showing:
  - distribution of main arc completion,  
  - time allocation between main, side, and filler content,  
  - frequency/severity of drift flags per build.

---

## 7. Multi‑Language Experience Parity

### 7.1 Objectives

- **R‑LANG‑OBJ‑001**  
  Ensure that localized players (Chinese, Japanese, French, Spanish (ES/MX), Thai, etc.) receive **functionally and emotionally equivalent** experiences, not degraded translations.

### 7.2 Language Preferences & Propagation

- **R‑LANG‑SET‑001 (Preferences)**  
  Settings service SHALL store, per player:
  - UI language,  
  - subtitle language,  
  - spoken dialogue language,  
  which MAY differ.

- **R‑LANG‑SET‑002 (Propagation)**  
  Language settings SHALL be propagated to:
  - Language System service,  
  - Story Teller,  
  - audio/TTS subsystems,  
  - UE5 client,  
  and included in Ethelred event metadata.

### 7.3 Consistency & Quality Checks

- **R‑LANG‑CHK‑001 (UI & Subtitle Consistency)**  
  Ethelred SHALL:
  - capture UI screenshots across languages,  
  - check for text overflow, broken characters, truncated labels,  
  - verify all UI text appears in the configured language (no stray English, etc.).

- **R‑LANG‑CHK‑002 (Dialogue & Subtitles)**  
  For each voiced line:
  - ensure spoken language matches configured audio language or documented fallback,  
  - ensure subtitles accurately reflect spoken content (no missing/placeholder text).

- **R‑LANG‑CHK‑003 (Coverage)**  
  Track per language:
  - % of main story lines localized,  
  - % of UI strings localized,  
  - count of fallback or untranslated tokens.

- **R‑LANG‑CHK‑004 (Basic Linguistic Quality)**  
  Use automated checks to flag:
  - obviously machine‑translated or placeholder strings,  
  - common template artifacts (`TODO_TRANSLATE`, raw keys),  
  for human review.

### 7.4 Reports

- **R‑LANG‑OUT‑001**  
  Per build, generate a **Localization QA Report** summarizing:
  - coverage per language,  
  - major issues (overflow, wrong language, low‑quality segments),  
  - impact on main arcs vs side content.

---

## 8. Website / Social AI (Placeholder Requirements)

> Detailed design to be completed after Phase 6 in consultation with the user. This section captures minimum scaffolding required now.

- **R‑SOC‑OBJ‑001 (Feedback Ingestion)**  
  Future Ethelred versions SHALL ingest community feedback from selected surfaces (official site comments, wiki edits, forums, curated social channels) into a separate pipeline, **distinct from in‑game telemetry**.

- **R‑SOC‑SAFE‑001 (Guardrails & Moderation)**  
  All analysis of user‑generated web/social content MUST pass through Guardrails Monitor or equivalent to filter illegal, hateful, or abusive material before further processing.

- **R‑SOC‑PRIV‑001 (Separation of Identities)**  
  Web/social identities MUST NOT be automatically linked to in‑game player identities without explicit consent.

- **R‑SOC‑FB‑001 (Design Feedback)**  
  Community analytics SHALL produce **theme‑level** summaries (e.g., “Arc X confusing”, “Monster Y not scary”) and correlate them with in‑game metrics; they MUST NOT be used to micro‑target individual players.

---

## 9. Traceability, Testing & Change Management

- **R‑TEST‑001 (Testability)**  
  Each requirement in this document MUST have at least one associated test case or scenario in the QA test plan (unit, integration, scenario, or regression) with clear acceptance criteria.

- **R‑TEST‑002 (Golden Scenarios)**  
  Ethelred SHALL be validated using:
  - curated **golden‑path playthroughs**,  
  - synthetic adversarial scenarios for each domain (4D, Audio, Content, Story, Lang),  
  replayed via the Red Alert system to check Ethelred outputs vs ground truth.

- **R‑TEST‑003 (Model & Policy Versioning)**  
  All model/policy changes affecting Ethelred MUST:
  - be versioned,  
  - record rationale and impacted requirements,  
  - trigger re‑execution of relevant golden scenarios prior to deployment.

- **R‑CHANGE‑001 (Document Evolution)**  
  This requirements document SHALL be treated as a living artifact. Material changes (add/remove/relax requirements) MUST:
  - go through architecture + design review,  
  - update traceability matrices and test plans,  
  - be recorded in a change log at the bottom of the file.

---

**End of ETHELRED‑COMPREHENSIVE‑REQUIREMENTS v2.0.0**
```
- **Audio-Visual Sync**: Footsteps match foot placement
- **Event Timing**: Quest triggers fire at correct moments

#### 1.4.5 Gameplay Flow
- **Confusing UI**: Player stuck on menu, unclear objective markers
- **Stuck Players**: Player walking into walls, unable to progress
- **Tutorial Effectiveness**: Player understands controls
- **Pacing Issues**: Boring sections, overwhelming difficulty spikes

#### 1.4.6 Realism Assessment
- **Core Question**: Does it feel real or fake?
- **Subjective Factors**: Lighting believability, material accuracy, physics plausibility
- **Uncanny Valley**: Detect creepy/off-putting character interactions
- **Immersion Breaks**: Anything that reminds player "this is a game"

### 1.5 Adaptive Sampling Strategy

#### 1.5.1 Phase 1: Initial (Frame-by-Frame)
- **When**: First playthrough of new content
- **Sampling**: Every frame at 30-60 FPS
- **Purpose**: Establish baseline, catch rare issues
- **Duration**: Until 95% of game content seen once
- **Storage**: Full video with depth

#### 1.5.2 Phase 2: Solidifying (Seconds Sampling)
- **When**: Content seen 2-5 times
- **Sampling**: 1-second samples every 5-10 seconds
- **Purpose**: Verify issues fixed, monitor regressions
- **Duration**: Until 3 clean passes through area
- **Storage**: Sampled frames + issue zones

#### 1.5.3 Phase 3: Events (Trigger-Based)
- **When**: Content known to be stable
- **Sampling**: Triggered by events (combat start, dialogue, quest complete)
- **Purpose**: Focus on dynamic content where issues emerge
- **Duration**: Ongoing during development
- **Storage**: Event clips (10s before + 30s after)

#### 1.5.4 Phase 4: Mature (Intelligent Summary)
- **When**: Content production-ready
- **Sampling**: Continuous with AI-driven summary
- **Purpose**: Long-term regression detection
- **Duration**: Pre-release and post-release monitoring
- **Storage**: Aggregated metrics + flagged issues only

#### 1.5.5 Tester AI Control
- **Requirement**: Tester AI (Ethelred itself) determines phase transitions
- **Criteria**: Issue density, stability metrics, developer input
- **Override**: Developers can force higher sampling for specific areas

### 1.6 4D Model Requirements

#### 1.6.1 Depth + Temporal Analysis
- **Depth**: Use Z-buffers to understand 3D scene geometry
- **Temporal**: Track motion over time (not just individual frames)
- **4D Representation**: Scene evolves through time with full geometry

#### 1.6.2 Model Research Required
- **Task**: Research state-of-art 4D vision models
- **Candidates** (GPT-5.1-Codex recommendations):
  - Tiny-NeRF / NVIDIA Instant NGP (real-time)
  - Gaussian Splatting (high fidelity, async)
  - Multi-view pose estimators (VIBE, ROMP)
- **Evaluation Criteria**: Real-time capability, accuracy, GPU cost
- **Decision**: Choose models in Phase 3 (Solutions)

### 1.7 Storage & Infrastructure

#### 1.7.1 Video Storage
- **Location**: AWS S3 Standard-IA (in-region)
- **Retention**: 30 days default (configurable per test run via Settings Service)
- **Format**: MP4/H.264 for RGB + EXR sidecar for depth
- **Size Estimate**: 1.5 GB per 2-minute clip (1080p RGB+depth)
- **Monthly Estimate**: 10 TB for 50 test runs/day
- **Lifecycle**: Archive to Glacier after 90 days if flagged important

#### 1.7.2 Derived Data
- **Point Clouds**: S3 binaries
- **Skeletal Tracks**: PostgreSQL JSONB
- **Feature Vectors**: Redis cache (1hr TTL) + PostgreSQL
- **Issue Reports**: PostgreSQL with full metadata

### 1.8 Pipeline Architecture

#### 1.8.1 Capture Agent (UE5 Plugin)
- **Function**: Publishes per-camera frame bundles via gRPC streaming
- **Data**: RGB, depth, camera pose, scene metadata
- **Performance**: Must not impact game FPS (<5% overhead)

#### 1.8.2 Ingress Service (ECS)
- **Function**: Convert frames to standardized container
- **Output**: Push to S3, emit NATS `vision.frame_ready` messages
- **Scaling**: Auto-scale on NATS queue depth (>500 msgs → +2 tasks)

#### 1.8.3 4D Processing Service
- **Real-Time Mode**: ≤250ms end-to-end for live guardrails
  - Uses Tiny-NeRF/Gaussian Splatting on GPU (RTX A10G 24GB)
  - Purpose: Immediate feedback for critical issues
- **Async Batch Mode**: Within 5 minutes of test end
  - Uses NeRFStudio/NVIDIA Instant NGP on GPU (A100 40GB)
  - Purpose: High-fidelity reconstruction for detailed analysis

### 1.9 API Contracts

```
POST /vision/streams/{sessionId}
  Purpose: Start capture
  Response: { ingestEndpoint, authToken }

STREAM /vision/frames (gRPC)
  Message: FrameBundle {
    rgbFrame: bytes,
    depthFrame: bytes,
    cameraParams: CameraParams,
    metadata: Metadata
  }

GET /vision/sessions/{id}/artifacts
  Response: {
    nerf_volumes: [S3 URLs],
    pose_logs: [S3 URLs],
    issue_reports: [Report IDs]
  }
```

### 1.10 Performance Requirements

#### 1.10.1 Real-Time SLA
- **P95 Processing Latency**: <250ms per frame
- **GPU Utilization Alert**: When >80% for >5 minutes
- **Frame Loss**: <1% acceptable

#### 1.10.2 Scaling
- **Auto-Scale Trigger**: NATS queue depth
- **GPU Pool**:
  - Real-time: ~$8/hr (A10G managed via ECS capacity providers)
  - Batch: ~$20/hr (A100)

---

## 2. AUDIO AUTHENTICATION SYSTEM

### 2.1 Core Purpose

Distinguish authentic human voices from synthetic voices to ensure vocal chord simulator produces world-first authentic monster voices.

### 2.2 Authentic Baselines

#### 2.2.1 Required Datasets
- **LibriSpeech**: 1000 hours (establish human voice characteristics)
- **Common Voice**: Crowdsourced multi-accent data
- **VCTK**: 109 professional speakers (high-quality baseline)
- **Purpose**: Define "authentic human" voice profile

#### 2.2.2 Reference Implementation
- **Hosting**: Already hosted for training
- **Usage**: Distributional shift detection
- **Embeddings**: wav2vec2.0 base for feature extraction

### 2.3 Vocal Emulators Required

#### 2.3.1 Human Emulator
- **Purpose**: Perfect baseline (what human voice should sound like)
- **Source**: Professional voice actor recordings
- **Coverage**: All phonemes, emotions, speaking styles

#### 2.3.2 Archetype Emulators (~25 total)
- **Working Now**: Vampire, Zombie, Werewolf (vocal-chord-research/cpp-implementation/)
- **Status**: 62/62 tests passing
- **Remaining**: ~22 more Archetypes (see Archetype Chain Registry)

**Known Archetypes**:
- Vampire (Volkh language, uncanny stillness)
- Zombie (broken larynx, Glottal Incoherence)
- Werewolf (subharmonic beast chaos, transformation surges)
- Ghoul
- Lich
- Additional 20+ (find in Archetype Chain Registry)

#### 2.3.3 Emulator Architecture
- **Location**: vocal-chord-research/cpp-implementation/
- **Technology**: C++20 DSP, real-time audio processing
- **Components**: Glottal Incoherence, Subharmonic Generator, Pitch Stabilizer, Corporeal Noise
- **Performance**: 111-365μs per voice (1.4-4.5x better than 500μs target)

### 2.4 Virtual Audio Routing

#### 2.4.1 NO Physical Setup
- **Requirement**: Software-only audio routing
- **Purpose**: Avoid "sound room" physical infrastructure
- **Tools**: VoiceMeeter, Virtual Audio Cable (Windows/Mac)

#### 2.4.2 Audio Loop Architecture
- **Game Audio Out** → Virtual Audio Cable → **Ethelred Audio In**
- **Emulator Out** → Virtual Audio Cable → **Ethelred Audio In**
- **Isolation**: Separate virtual devices per test stream

### 2.5 Analysis Approach

#### 2.5.1 Decision Required: Advanced vs ML-Based
**YOU (Ethelred enhancement team) must choose in Phase 3 (Solutions).**

**Option A: Advanced Audio Analysis**
- **Components**: Formants, prosody, spectral analysis
- **Pros**: Explainable, deterministic, lightweight
- **Cons**: May miss subtle synthetic artifacts
- **Use Cases**: Real-time validation, low-latency feedback

**Option B: ML-Based Discriminator**
- **Architecture**: Deep learning classifier (real vs synthetic)
- **Training**: LibriSpeech (real) vs Emulator outputs (synthetic)
- **Pros**: Catches subtle patterns humans miss
- **Cons**: Requires GPU, less explainable
- **Use Cases**: High-accuracy validation, post-processing

**Recommendation from Gemini 2.5 Pro**: Hybrid approach
- Use Advanced for real-time (<150ms latency requirement)
- Use ML-Based for deep analysis (async, high confidence)

#### 2.5.2 Frequency Analysis
- **Core Question**: What makes voices authentic?
- **Analysis Required**:
  - Formant structure (vocal tract resonances)
  - Prosody patterns (rhythm, intonation, stress)
  - Spectral envelope (energy distribution across frequencies)
  - Temporal dynamics (voice onset time, transitions)

#### 2.5.3 Matching to Emulators
- **Validation**: Vocal chord simulator outputs match authentic characteristics
- **World-First**: No existing reference for "authentic monster voices"
- **Approach**: Define authenticity criteria from human voice science, apply to monster archetypes

### 2.6 Peer Review Requirements

#### 2.6.1 Minimum 3 Models with Audio Capabilities
- **Purpose**: Validate audio analysis approach
- **Candidates**:
  - OpenAI Whisper (speech understanding)
  - Google Speech-to-Text (audio analysis)
  - Deepgram (audio intelligence)
  - Custom audio-trained models

### 2.7 Autonomous Testing Loop

#### 2.7.1 Primary Use Case
- **Duration**: Days to weeks continuous
- **Process**:
  1. AI Player plays game
  2. NPCs speak (using vocal emulators)
  3. Ethelred captures audio via virtual routing
  4. Analyzes against baselines
  5. Flags issues (too synthetic, artifacts, glitches)
  6. Reports to developers
- **No Human Intervention**: Fully autonomous

### 2.8 Audio Pipeline Architecture

#### 2.8.1 Audio Capture Agent
- **Transport**: WebRTC or gRPC streaming
- **Format**: 48 kHz, 16-bit PCM
- **Metadata**: Speaker ID, archetype, line ID
- **Performance**: <5% CPU overhead on test rig

#### 2.8.2 Audio Ingest Service
- **Function**: Write FLAC segments (10s windows) to S3
- **Embeddings**: Generate MFCC/SSL embeddings (wav2vec2.0)
- **Storage**: Embeddings in PostgreSQL + Redis cache

#### 2.8.3 Baseline Comparators
- **Reference**: LibriSpeech corpus
- **Voice Profiles**: 25+ Archetype embeddings in Feature Store (Redis + S3)
- **Comparison**: Real-time cosine similarity, distributional shift detection

#### 2.8.4 Real-Time Validation
- **Latency Budget**: <150ms capture → pass/fail verdict
- **Light Checks**: CPU-based (voice match, profanity, emotion)
- **Heavy Checks**: GPU inference (Tacotron2, HiFi-GAN) for fidelity audits (async)

### 2.9 Storage Requirements

#### 2.9.1 Short-Term Clips
- **Location**: S3 Standard
- **Retention**: 7 days default
- **Lifecycle**: Glacier after 90 days if flagged

#### 2.9.2 Database Schema (PostgreSQL)
```sql
CREATE TABLE audio_segments (
  segment_id UUID PRIMARY KEY,
  session_id UUID NOT NULL,
  start_ts TIMESTAMPTZ NOT NULL,
  duration_ms INT NOT NULL,
  speaker_archetype TEXT,
  storage_uri TEXT NOT NULL,
  embedding VECTOR(512),
  guardrail_status JSONB,
  authenticity_score FLOAT,
  issues_detected JSONB,
  baseline_comparison JSONB
);

CREATE INDEX idx_audio_session ON audio_segments(session_id);
CREATE INDEX idx_audio_archetype ON audio_segments(speaker_archetype);
```

### 2.10 API Contracts

```
POST /audio/sessions/{id}/start
  Response: { streamingToken }

STREAM /audio/segments (bi-directional)
  Client→Server: AudioChunk { pcmData, metadata }
  Server→Client: ValidationResult { authentic, score, issues }

GET /audio/emulators/{archetype}/baseline
  Response: { embedding[512], stats }
```

### 2.11 Performance Requirements

#### 2.11.1 Throughput
- **Concurrent Streams**: 200 expected
- **Provision**: 4 ECS tasks (c5.4xlarge) + 1 GPU task (g4dn.xlarge) for emulator audits

#### 2.11.2 Latency
- **P95 RTT**: <150ms
- **Alert**: When RTT >150ms or packet loss >1%

#### 2.11.3 Scaling
- **Trigger**: Redis pub/sub for guardrail alerts
- **Auto-Scale**: On concurrent stream count

---

## 3. EMOTIONAL ENGAGEMENT & ADDICTION MONITORING

### 3.1 Core Purpose

Measure game's emotional impact on players to ensure deep engagement WITHOUT harmful addiction. Train AI Brain on morality through player-NPC interactions.

### 3.2 Measurement Metrics

#### 3.2.1 Decision Patterns (Primary Metric)
- **Core Insight**: How players treat NPCs reveals emotional connection
- **Patterns to Track**:
  - **Protect**: Player shields NPC, avoids putting in danger
  - **Mistreat**: Player ignores NPC needs, callous choices
  - **Ignore**: Player doesn't engage with NPC
  - **Abuse**: Player actively harms NPC (test for sadism)
- **Purpose**: Train AI Brain on morality ("What is right/wrong?")

#### 3.2.2 Behavioral Indicators
- **Time with NPCs**: More time = stronger emotional bond
- **Choices to Help/Harm**: Frequency of altruistic vs selfish actions
- **Resource Allocation**: Do they give valuable items to NPCs?
- **Return Frequency**: Do they revisit favorite NPCs?

#### 3.2.3 Session Metrics
- **Play Duration**: Length of sessions (longer = more engaged)
- **Return Frequency**: Days between sessions (higher = more addicted)
- **Session Start/End**: When do they log in/out? (binge patterns)
- **Total Time**: Weekly/monthly playtime totals

#### 3.2.4 Meta Indicators
- **What Worked**: Which content keeps players engaged?
- **What Didn't**: Where do players get bored and quit?
- **Feedback for Story Teller**: "Players love Family X, dislike Mechanic Y"

### 3.3 Example Failure Case

#### 3.3.1 Protection NPC Design Flaw
- **Scenario**: Protection NPC thrown at enemies by all male players
- **Interpretation**: NPC design FAILED to evoke protective instinct
- **Correct Response**: Story Teller redesigns NPC (more sympathetic, better AI, clearer vulnerability)
- **Lesson**: Behavioral patterns reveal design quality

### 3.4 Adaptation Strategy

#### 3.4.1 Analyze First, Adapt Later
- **Mandate**: NOT reactive (don't change game in real-time)
- **Process**:
  1. Collect data across sessions
  2. Identify patterns (e.g., "90% of players ignore Mechanic X")
  3. Analyze why (boring? confusing? too punishing?)
  4. Make gradual adjustments
  5. Test adjustments with new players

#### 3.4.2 Pattern Recognition
- **Aggregate**: Look across 100+ players, not individuals
- **Time Windows**: Weekly/monthly trends
- **Segmentation**: Analyze by player type (cautious vs aggressive)

#### 3.4.3 Gradual Adjustments
- **NO Instant Changes**: Prevents whiplash, maintains consistency
- **Versioning**: Track which version of content player experiences
- **A/B Testing**: Try variations, measure engagement differences

#### 3.4.4 Player-Specific Tuning
- **Individual Rhythms**: Some prefer slow pacing, others fast
- **Difficulty Curves**: Adjust challenge based on player skill
- **Content Preferences**: More combat vs more dialogue
- **Ethical Boundaries**: Some players squeamish, others not

### 3.5 Testing Approach

#### 3.5.1 Multiple AI Player Personalities
- **Requirement**: Create Player AI with different personality types
- **Types**:
  - **Cautious**: Avoids risks, protects NPCs
  - **Aggressive**: Rushes into combat, harsh choices
  - **Completionist**: Explores everything, talks to everyone
  - **Speedrunner**: Skips content, finds exploits
  - **Roleplayer**: Deep character immersion
- **Purpose**: Test engagement across player types

### 3.6 Ethics: Measure Addiction, Don't Interfere

#### 3.6.1 Core Principle
**"Make game so immersive players WANT to play, not HAVE to play."**

#### 3.6.2 What to Measure
- **Engagement Intensity**: How absorbed are players?
- **Withdrawal Symptoms**: Do they exhibit compulsive behavior?
- **Real-Life Impact**: Self-reported (optional surveys)
- **Binge Patterns**: 10+ hour sessions without breaks

#### 3.6.3 What NOT to Do
- **NO FOMO Mechanics**: No "daily login bonuses," "time-limited events"
- **NO Predatory Patterns**: No "energy systems," "wait-or-pay" mechanics
- **NO Interference**: Don't manipulate players into playing more
- **NO Dark Patterns**: No fake urgency, social pressure

#### 3.6.4 What TO Do
- **Make it Incredible**: Deep storytelling, meaningful choices
- **Respectful Design**: Let players leave gracefully
- **Healthy Breaks**: Optional reminders for long sessions (player can disable)
- **Transparency**: If using data, tell players what and why

### 3.7 Engagement Drivers (ALL Critical)

#### 3.7.1 Power Fantasy
- **Implementation**: Building criminal empire, climbing Dark World ladder
- **Measure**: Does player feel powerful? Progression rate?

#### 3.7.2 Moral Complexity
- **Implementation**: Surgeon vs Butcher paths, ambiguous choices
- **Measure**: Choice distribution, regret patterns

#### 3.7.3 Strategic Gameplay
- **Implementation**: Negotiation with Dark clients, resource management
- **Measure**: Strategic vs random choices, learning curves

#### 3.7.4 Dark Fantasy Immersion
- **Implementation**: Vampire/werewolf lore, Dark World trading
- **Measure**: Time in lore documents, NPC conversation depth

#### 3.7.5 Sensory Detail
- **Implementation**: Putrid green makes you gag, flesh cuts make you flinch
- **Measure**: Player reactions (surveys), visceral response indicators

### 3.8 Evolution Over Time

#### 3.8.1 Early Game: Immediate Survival
- **Focus**: Learn mechanics, survive, establish base
- **Engagement**: Action-driven, short feedback loops

#### 3.8.2 Mid Game: Long-Term Strategy
- **Focus**: Build empire, negotiate with families, complex choices
- **Engagement**: Strategic planning, delayed gratification

#### 3.8.3 Late Game: World-Scale Impact
- **Focus**: Control territories, influence Dark World politics
- **Engagement**: Grand strategy, emergent gameplay

#### 3.8.4 Endgame: Multiverse (Years to Build)
- **Vision**: Not in initial release, long-term expansion
- **Engagement**: Infinite replayability, community-driven content

### 3.9 Data Collection Architecture

#### 3.9.1 Telemetry Events
```json
{
  "event_type": "npc_interaction",
  "session_id": "uuid",
  "player_id": "uuid",
  "timestamp": "iso8601",
  "npc_id": "uuid",
  "action": "protect|mistreat|ignore|abuse",
  "context": {
    "npc_health": 0.3,
    "player_resources": {"health": 100, "items": [...]},
    "situation": "combat|dialogue|quest"
  }
}
```

#### 3.9.2 Storage
- **Hot Data**: Redis (last 24hrs)
- **Warm Data**: PostgreSQL (90 days)
- **Cold Data**: S3 (long-term analytics)

#### 3.9.3 Privacy
- **Anonymization**: Player ID hashed, no PII
- **Opt-Out**: Players can disable telemetry (with warning about reduced experience)
- **Transparency**: Privacy policy explains data use

### 3.10 Performance Requirements

#### 3.10.1 Event Ingestion
- **Volume**: 1000+ events/second per active player
- **Latency**: Fire-and-forget (<10ms impact on game)
- **Reliability**: Events queued locally if network fails

#### 3.10.2 Analysis
- **Real-Time**: Player-specific adaptations (<1 second)
- **Batch**: Aggregate analytics (hourly/daily jobs)
- **Reporting**: Developer dashboard (5-minute refresh)

---

## 4. INTEGRATION WITH EXISTING INFRASTRUCTURE

### 4.1 NATS Microservices

#### 4.1.1 New Services Required
- **Vision Processing Service** (handles 4D vision pipeline)
- **Audio Analysis Service** (handles audio authentication)
- **Engagement Analytics Service** (processes emotional engagement data)

#### 4.1.2 Existing Services to Integrate
- **Model Management**: Guardrails Monitor (content safety)
- **Settings Service**: Content Level Manager (to be added)
- **Story Teller**: Receives engagement feedback
- **State Manager**: Stores player behavioral patterns

### 4.2 NATS Subject Structure

```
ethelred.vision.frame_ready
ethelred.vision.issue_detected
ethelred.audio.segment_ready
ethelred.audio.authenticity_check
ethelred.engagement.event
ethelred.engagement.pattern_detected
```

### 4.3 Redis Cluster Usage

- **Vision**: Feature vector cache (1hr TTL)
- **Audio**: Embedding cache, voice profile cache
- **Engagement**: Hot session data (24hr TTL)

### 4.4 PostgreSQL Schema Extensions

See individual system sections for detailed schemas.

---

## 5. CROSS-CUTTING REQUIREMENTS

### 5.1 Security

- **mTLS**: All service-to-service communication
- **IAM Roles**: S3 access controlled via AWS IAM
- **Encryption**: At rest (S3 AES256) and in transit (TLS 1.3)
- **PII Protection**: Player data anonymized

### 5.2 Observability

- **Traces**: OpenTelemetry spans for all operations
- **Metrics**: CloudWatch + Prometheus (custom metrics)
- **Logs**: CloudWatch Logs + S3 archival
- **Dashboards**: Grafana for developer visibility

### 5.3 Cost Management

- **Tagging**: All resources tagged with `Service=ethelred-vision/audio/engagement`
- **Budgets**: Monthly caps per subsystem
- **Alerts**: When cost exceeds 80% of budget
- **Optimization**: Auto-scaling based on demand

### 5.4 Disaster Recovery

- **Backups**: PostgreSQL daily snapshots, Redis persistence
- **S3 Versioning**: Enabled for critical data
- **Multi-AZ**: All services deployed across multiple availability zones

---

## 6. SUCCESS CRITERIA

### 6.1 4D Vision System
- ✅ Detects 95% of visual issues before human QA
- ✅ <5% false positive rate
- ✅ Real-time mode <250ms P95 latency
- ✅ Adaptive sampling works across all 4 phases

### 6.2 Audio Authentication
- ✅ Distinguishes real vs synthetic voices with 98% accuracy
- ✅ Vocal emulators pass authenticity tests (subjectively "feel real")
- ✅ <150ms real-time validation latency
- ✅ Autonomous testing loop runs for 7+ days without intervention

### 6.3 Emotional Engagement
- ✅ Accurately predicts player retention (±10%)
- ✅ Identifies failed NPC designs before wide release
- ✅ Story Teller adapts content based on engagement patterns
- ✅ NO harmful addiction patterns introduced

---

**Next Phase**: Solutions (Research & Design)  
**Document Status**: Complete for peer review

