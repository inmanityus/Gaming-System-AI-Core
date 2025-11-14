# ETHELRED – Story Memory System Phase 4 Task Breakdown

**Domain**: Story Memory System (SMS)  
**Source Requirements**: `STORY-MEMORY-SYSTEM-REQUIREMENTS.md`, `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` (story sections) + system-wide §1  
**Source Solutions**: `docs/solutions/ETHELRED-STORY-MEMORY-SOLUTIONS.md`  

All tasks must be implemented with **peer coding**, **pairwise testing**, and real tests, respecting non-predatory narrative use and integration constraints with Story Teller and Ethelred.

---

## Milestone 1 – Schema & Service Foundations

### TSM-01 – Implement Story Memory Core Schemas & Migrations
- **Description**: Implement migrations for core SMS tables (`story_players`, `story_arc_progress`, `story_decisions`, `story_relationships`, `story_experiences`) as described in the requirements and solutions docs.
- **Dependencies**: DB migration tooling, `STORY-MEMORY-SYSTEM-REQUIREMENTS.md` §2, existing game DB schemas.
- **Acceptance Criteria**:
  - Tables exist with appropriate primary keys, foreign keys, and indexes on `player_id`, `arc_id`, `npc_id`, `experience_id`.
  - Migrations apply and rollback cleanly in dev/test environments.
  - Sample test data can be inserted for at least one player with multiple arcs, decisions, and relationships.
- **Tests**:
  - **Unit**: Migration apply/rollback tests.
  - **Integration**: Repository tests for CRUD operations on core SMS tables.

### TSM-02 – Scaffold `svc.story_memory` Service & Story State Manager
- **Description**: Implement the base `svc.story_memory` service with a Story State Manager component for reading and writing structured per-player story state.
- **Dependencies**: TSM-01, existing service scaffolding patterns, canonical ID conventions.
- **Acceptance Criteria**:
  - Service can start, connect to the DB, and respond to basic health checks.
  - Story State Manager exposes internal APIs to load and persist a story snapshot for a test player.
  - Error handling and logging are in place for DB failures and invalid inputs.
- **Tests**:
  - **Unit**: State manager tests for reading/writing snapshots with in-memory or test DB.
  - **Integration**: Service-level tests verifying snapshot read/write over public interfaces (even if temporary).

---

## Milestone 2 – Event Ingestion & APIs

### TSM-03 – Define Story Event & Snapshot Contracts
- **Description**: Define schemas and NATS subjects for inbound story events (`story.events.*`) and outbound drift/conflict events (`events.story.v1.*`), plus HTTP/gRPC story snapshot APIs.
- **Dependencies**: Requirements §3–4, solutions doc §3.2–3.3, canonical envelope spec.
- **Acceptance Criteria**:
  - Schemas cover `arc_beat_reached`, `quest_completed`, `experience_completed`, `relationship_changed`, and `world_state_changed`.
  - Snapshot API contract (`GET /story/{player_id}/snapshot`) is documented and returns a compact but comprehensive view.
  - Example payloads are defined for all key event types and responses.
- **Tests**:
  - **Unit**: Schema validation and serialization tests for event and snapshot representations.
  - **Integration**: NATS send/receive tests plus API contract tests via HTTP/gRPC.

### TSM-04 – Implement Event Ingestor for Story Updates
- **Description**: Implement Event Ingestor component that subscribes to `story.events.*` (and optional HTTP events) and translates them into updates on the SMS tables.
- **Dependencies**: TSM-01–03, Quest System and Story Teller event designs.
- **Acceptance Criteria**:
  - For test events (quest completion, relationship change, etc.), SMS tables are updated consistently with canonical IDs.
  - Event handling is idempotent for duplicate events, and ordering guarantees are documented where necessary.
  - Invalid or out-of-order events are handled defensively and logged with enough context for debugging.
- **Tests**:
  - **Unit**: Event-to-update mapping tests for each event type.
  - **Integration/E2E**: Pipeline tests from synthetic `story.events.*` inputs to DB state changes.

### TSM-05 – Implement Story Snapshot API & Cache
- **Description**: Implement story snapshot read API and a fast cache layer (e.g., Redis/in-memory) that serves snapshots without hitting the DB hot path in normal operation.
- **Dependencies**: TSM-02–04, cache infrastructure (Redis or equivalent).
- **Acceptance Criteria**:
  - `GET /story/{player_id}/snapshot` returns the expected snapshot for test players with realistic story histories.
  - Snapshot read latency meets the targets in requirements (≤ 50ms P99 for typical sessions).
  - Cache invalidation behavior is well-defined and tested when new events arrive.
- **Tests**:
  - **Unit**: Snapshot assembly tests, including edge cases.
  - **Integration**: Cache vs DB behavior tests and latency measurements in a controlled environment.

---

## Milestone 3 – Drift & Conflict Detection

### TSM-06 – Implement Time & Attention Drift Metrics
- **Description**: Implement drift analyzers that compute time spent in main arcs vs Experiences vs side content, and golden path health metrics (`SM‑4.1.*`).
- **Dependencies**: TSM-01–05, telemetry on playtime per activity from other services, configuration for thresholds.
- **Acceptance Criteria**:
  - Drift analyzers can process test datasets and flag players/cohorts with no main-arc progress over configured time thresholds.
  - Metrics are persisted and emitted as `STORY.DRIFT` events with context on arcs, Experiences, and thresholds exceeded.
  - Configurable parameters (e.g., N hours without progress) are externalized for tuning.
- **Tests**:
  - **Unit**: Drift calculation tests using synthetic timelines.
  - **Integration/Analytics**: Offline runs against curated playthrough logs, validating expected drift flags and non-flags.

### TSM-07 – Implement Genre/Theme Drift & Narrative Incoherence Detection
- **Description**: Implement analyzers for genre/theme drift and state conflicts (`SM‑4.2.*`, `SM‑4.3.*`), cross-checking story memory against world state and content tags.
- **Dependencies**: Story content tagging (themes), World State APIs, TSM-06.
- **Acceptance Criteria**:
  - Genre drift events are emitted when recent playtime is predominantly in non-horror or off-theme content beyond configured thresholds.
  - Conflict detection identifies and emits `STORY.CONFLICT_ALERT` events for defined conflict scenarios (e.g., dead NPCs appearing alive).
  - Each drift/conflict event includes remediation hints for designers.
- **Tests**:
  - **Unit**: Tests for conflict rules and theme drift computations.
  - **Integration/E2E**: Scenario tests using scripted world/story inconsistencies and verifying alerts.

---

## Milestone 4 – Integration, Observability & Readiness

### TSM-08 – Integrate SMS with Story Teller, Quest System & Ethelred
- **Description**: Wire Story Teller, Quest System, World State, and Ethelred to use SMS snapshots and events according to the solutions architecture.
- **Dependencies**: TSM-02–07, Story Teller and Quest System integration points, Ethelred Coordinator.
- **Acceptance Criteria**:
  - Story Teller uses SMS snapshots for context when generating story content in at least one tested scenario.
  - Quest System gates quest availability using SMS data for arc/decision states.
  - Ethelred Coordinator consumes `STORY.DRIFT` and `STORY.CONFLICT_ALERT` events and correlates them with other domains in Red Alert.
- **Tests**:
  - **Integration/E2E**: Cross-service tests (Quest/Story Teller ↔ SMS ↔ Ethelred) using scripted playthroughs and QA scenarios.

### TSM-09 – Implement Story Memory Observability & Dashboards
- **Description**: Add metrics, logs, and dashboards for story state ingestion, drift/conflict events, and snapshot performance (`SM‑6.*`).
- **Dependencies**: TSM-01–08, observability stack, Master Test Registry.
- **Acceptance Criteria**:
  - Metrics such as `story_snapshot_latency`, `story_events_ingested_total`, `story_drift_alerts_total{severity}`, and `story_conflict_alerts_total` are available and scraped.
  - Dashboards show arc completion distributions, time allocation across arcs/Experiences, and drift/conflict trends per build/environment.
  - Logs contain sufficient context (IDs, timestamps, thresholds) for debugging narrative issues.
- **Tests**:
  - **Integration**: Health and metrics endpoint tests for SMS.
  - **Analytics/Validation**: Manual dashboard inspection with seeded data to verify signal correctness.

### TSM-10 – Story Memory Traceability & Readiness Summary
- **Description**: Create a traceability matrix mapping `SM‑*` and relevant `R‑STORY‑*` requirements to SMS implementations and tests, and produce a readiness summary for `GAME-READINESS-ASSESSMENT.md`.
- **Dependencies**: Completion of core SMS tasks, Master Test Registry, requirements/solutions docs.
- **Acceptance Criteria**:
  - Every SMS requirement has at least one linked implementation and test, or is explicitly marked as future work with rationale.
  - Readiness summary clearly states current implementation status, major risks (e.g., untagged content), and open questions (e.g., SMS vs World State boundaries).
  - Peer review (external model) confirms adequacy of traceability and readiness statements.
- **Tests**:
  - **Analytics/Validation**: Peer review of the matrix and summary; findings captured for future phases.


