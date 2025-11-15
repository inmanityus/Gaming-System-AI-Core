```markdown
# ETHELRED – Story Memory System Solutions Architecture

**Date**: 2025-11-14  
**Version**: 0.1.0 (Phase 3 – Solutions draft)  
**Status**: Draft – requires peer review (GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5)  

---

## 0. Purpose, Scope, and Traceability

- **S‑SMS‑PURPOSE‑001**  
  Define the implementation‑aware architecture for the **Story Memory System (SMS)** that supports Story Teller and Ethelred, based on  
  `STORY-MEMORY-SYSTEM-REQUIREMENTS.md` and story‑related sections of `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md`.

- **S‑SMS‑SCOPE‑001**  
  Scope includes:
  - a dedicated Story Memory service managing per‑player story state,  
  - APIs and event flows for Story Teller, Quest System, World State, and Ethelred,  
  - drift and conflict detection mechanisms,  
  - storage and caching strategies for long‑term narrative memory.

- **S‑SMS‑OUT‑OF‑SCOPE‑001**  
  Out of scope:
  - low‑level prompt‑engineering for Story Teller,  
  - concrete schema DDL and index definitions (requirements doc already sketches conceptual DDL),  
  - specific embedding/vector search implementations.

- **S‑SMS‑TRACE‑001 (Traceability Approach)**  
  A traceability matrix will map `SM‑*` and `R‑STORY‑*` requirements to the components and flows defined here.

---

## 1. High‑Level Component Decomposition

### 1.1 Story Memory Service (`svc.story_memory`)

1. **Story State Manager**  
   - Maintains structured per‑player story state (**SM‑2.1.1**, **R‑STORY‑MEM‑001**):  
     - main/side arc progress,  
     - active/completed Experiences,  
     - key decisions and their consequences,  
     - NPC/faction relationship states,  
     - Broker’s Book and Debt of Flesh state.  
   - Provides APIs to read/write story state in compact, structured form.

2. **Event Ingestor**  
   - Subscribes to story‑relevant events from Quest System, Story Teller, World State, and other services:  
     - `story.arc_beat_reached`, `quest.completed`, `experience.completed`, `relationship.changed`, etc.  
   - Transforms events into updates to the story state, keeping canonical IDs and tags aligned.

3. **Drift & Conflict Detector**  
   - Periodically analyzes story state and recent activity (**SM‑4.*, R‑STORY‑MET‑001…**):  
     - time allocation across arcs/Experiences vs canonical expectations,  
     - genre/thematic alignment vs baselines,  
     - contradictions between story memory and world state.  
   - Emits `STORY.DRIFT` and `STORY.CONFLICT_ALERT` events with structured remediation hints.

4. **Snapshot & Reporting Engine**  
   - Produces **story snapshots** for Ethelred and dashboards:  
     - per‑player snapshot for QA sessions,  
     - aggregate metrics across cohorts (arc completion rates, drift patterns, conflict counts).

### 1.2 Clients and Integrations

- **Story Teller** – primary consumer/producer of story state; uses SMS to drive context, writes back key outcomes.  
- **Quest System** – reports quest progress/completion and reads arc progress for gating.  
- **World State / State Manager** – cross‑validates objective world facts with narrative memory.  
- **Ethelred** – requests snapshots and receives drift/conflict events for quality analysis.

---

## 2. Data Model & Storage (Conceptual)

Story Memory uses a **tiered storage model** (fast cache + durable store) as required by **SM‑2.1.2**:

1. **Durable Store (e.g., PostgreSQL)**  
   - Core tables (conceptual):  
     - `story_players` – per‑player story metadata.  
     - `story_arc_progress` – per `player_id` and `arc_id` progress states and last beats.  
     - `story_decisions` – key decisions with tags (mercy/cruelty, loyalty/betrayal, etc.).  
     - `story_relationships` – NPC and faction relationships.  
     - `story_experiences` – completed and active Experiences with tags.  
   - Optional supporting tables for canonical lore baselines and drift alerts (requirements doc already sketches DDL).

2. **Fast Cache (e.g., Redis / in‑memory)**  
   - Stores hot story snapshots per session to keep Story Teller and Ethelred read paths fast.  
   - Uses session‑scoped keys with TTL; durable store remains source of truth.

3. **Cold Archive (S3 or equivalent)**  
   - Periodic JSONL snapshots of story state for long‑term analytics and recovery, per requirements.

---

## 3. APIs & Event Contracts

### 3.1 HTTP/gRPC APIs (Conceptual)

- `GET /story/{player_id}/snapshot`  
  - Returns compact story snapshot including arc progress, Experiences, key decisions, and relationships.  
  - Used by Story Teller and Ethelred to obtain current context.

- `POST /story/{player_id}/events`  
  - Accepts structured story events from services that cannot publish directly to NATS.  
  - Example payload: `{"event_type": "quest_completed", "quest_id": "...", "arc_id": "...", "tags": [...]}`.

These APIs are thin wrappers over the event‑driven model; NATS is the primary integration channel for most services.

### 3.2 NATS Subjects

Indicative subjects (names may be refined during implementation):

- **Inbound Story Events** (from Quest System, Story Teller, World State):  
  - `story.events.arc_beat_reached`  
  - `story.events.quest_completed`  
  - `story.events.experience_completed`  
  - `story.events.relationship_changed`  
  - `story.events.world_state_changed` (for cross‑checking world and story).

- **Drift & Conflict Outputs**:  
  - `events.story.v1.drift` – story drift metrics and recommended corrections.  
  - `events.story.v1.conflict_alert` – state conflicts with involved IDs and suggested fixes (**SM‑4.3.2**).

All events use the canonical envelope (`R‑SYS‑OBS‑001`) with `domain = "Story"`.

---

## 4. Drift & Conflict Detection

Drift detection logic (outlined in the requirements doc) is implemented as **background jobs** or scheduled analyzers inside `svc.story_memory`:

1. **Time & Attention Drift**  
   - Analyzes time spent in main arcs vs Experiences vs side content (**SM‑4.1.1…4.1.2**, **R‑STORY‑MET‑001**).  
   - Flags when players (or cohorts) spend disproportionate time in off‑theme activities or stalled main arcs.

2. **Genre & Theme Drift**  
   - Uses arc/experience tags to monitor ratios of horror‑aligned vs non‑horror content (**SM‑4.2.1…4.2.2**).  
   - Emits drift events when configured thresholds are crossed (e.g., tangential content >30% of quests).

3. **Narrative Incoherence & Conflicts**  
   - Cross‑checks story memory vs world state and quest definitions (**SM‑4.3.1…4.3.2**):  
     - NPC dead vs alive contradictions,  
     - repeated introductions,  
     - impossible quest availability.  
   - Emits `STORY.CONFLICT_ALERT` events with enough detail for designers to reproduce and fix.

Drift and conflict events contain remediation fields (e.g., suggested soft steering or content fixes) to support Ethelred’s correction strategies.

---

## 5. Integration with Ethelred & Other Domains

### 5.1 Ethelred

- Ethelred uses Story Memory for:
  - **Story Coherence QA** – verifying that narrative flows align with design, not just moment‑to‑moment quality.  
  - **Drift Analysis** – combining story drift metrics with engagement/addiction and content governance signals.  
  - **Red Alert Reporting** – including story state context in game QA reports.

### 5.2 Story Teller

- Story Teller integrations:
  - reads snapshots at the start of generation to ground content in actual player state,  
  - pushes key events back into SMS (quest completions, relationship shifts, major beats),  
  - may use drift signals (softly) to adjust emphasis (e.g., propose more main arc opportunities).

### 5.3 Quest System & World State

- Quest System:
  - uses SMS data to gate quests based on arc progress and decisions,  
  - sends structured events when quests change state.  
- World State:
  - ensures persistence of world changes triggered by story events,  
  - provides authoritative facts for conflict detection (e.g., destroyed locations).

---

## 6. SLAs, Observability, and Safety

### 6.1 Performance Targets

- Real‑time story snapshot read:
  - Target: ≤ 50ms P99 for typical sessions (fast cache + DB).  
- Event ingestion:
  - Target: ≤ 10ms P95 from NATS receipt to durable write for individual events.  
- Drift checks:
  - Background jobs; not on hot path; ≤ 500ms per analysis window is acceptable.

### 6.2 Observability

- Metrics:
  - `story_snapshot_latency`, `story_events_ingested_total`,  
  - `story_drift_alerts_total{severity}`, `story_conflict_alerts_total`.  
- Dashboards show:
  - arc completion distributions,  
  - time allocation across arcs/Experiences,  
  - drift and conflict trends per build and environment (**SM‑6.1.1**).

### 6.3 Safety & Non‑Predatory Use

- Story drift corrections must respect **G‑MORAL** and **G‑LONGTERM** goals:
  - no manipulative use of narrative to maximize play time at the expense of player well‑being.  
- Corrections are implemented as:
  - soft steering and design adjustments,  
  - not as hard per‑player optimization loops.

---

## 7. Open Questions & Next Steps

- **Q‑SMS‑001**: Exact boundaries between Story Memory and World State services (what belongs where, and how to resolve conflicts).  
- **Q‑SMS‑002**: How much story detail to store vs summarize to keep memory size manageable while supporting Ethelred’s needs.  
- **Q‑SMS‑003**: Final selection of drift thresholds and severity levels per arc and activity type.  
- **Q‑SMS‑004**: Governance for manual overrides when designers intentionally break canonical patterns for special events.

This solutions architecture respects the v2 requirements while staying implementation‑agnostic. It MUST be peer‑reviewed by GPT‑5.1 / GPT‑5.1‑Codex, Gemini 2.5 Pro, and Claude Sonnet 4.5 before Phase 4 task breakdown.
```


