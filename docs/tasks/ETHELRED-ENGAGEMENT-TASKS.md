# ETHELRED – Emotional Engagement & Addiction Analytics Phase 4 Task Breakdown

**Domain**: Emotional Engagement & Addiction Analytics  
**Source Requirements**: `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §4 + system-wide §1  
**Source Solutions**: `docs/solutions/ETHELRED-ENGAGEMENT-ADDICTION-SOLUTIONS.md`  

All tasks below must be implemented with **peer coding**, **pairwise testing**, and real test runs (no mock-only paths), following `/all-rules` and `/test-comprehensive`, and respecting `R‑SYS‑SAFE‑001` (no predatory optimization).

---

## Milestone 1 – Telemetry Schema & Ingestion

### TEMO-01 – Define Engagement Telemetry Event Contracts
- **Description**: Specify canonical schemas and NATS subjects for engagement telemetry (`telemetry.raw.*`, `telemetry.emo.normalized.*`) covering NPC interactions, moral choices, session metrics, and AI Player runs.
- **Dependencies**: Requirements §4.1–4.2, existing telemetry patterns, `docs/NATS-SYSTEM-ARCHITECTURE.md`.
- **Acceptance Criteria**:
  - Event contracts for `telemetry.emo.npc_interaction`, `telemetry.emo.moral_choice`, `telemetry.emo.session_metrics`, and `telemetry.emo.ai_run` are documented and implemented.
  - All events have required fields (`session_id`, `actor_type`, IDs, timestamps, basic context) and align with the canonical envelope when transformed into domain events.
  - At least one sample payload per event type is captured in documentation for QA reference.
- **Tests**:
  - **Unit**: Schema validation tests for each event type.
  - **Integration**: NATS send/receive tests for telemetry subjects using the Python SDK.

### TEMO-02 – Implement `engagement_events` Storage Schema & Migrations
- **Description**: Implement PostgreSQL schema and migrations for the `engagement_events` and related tables, following the conceptual model in the solutions doc.
- **Dependencies**: DB migration tooling, TEMO-01.
- **Acceptance Criteria**:
  - Migrations create `engagement_events` with typed columns and indexes suitable for analytics (by `session_id`, `npc_id`, `arc_id`, `event_type`, `build_id`).
  - Migrations apply and rollback cleanly on dev/test databases.
  - Basic data retention/deletion strategy is documented with respect to `R‑SYS‑DATA‑001…004`.
- **Tests**:
  - **Unit**: Migration apply/rollback tests.
  - **Integration**: Repository tests that insert/query events using the new schema.

### TEMO-03 – Scaffold `svc.ethelred.emo.telemetry` Ingestion Service
- **Description**: Create the telemetry ingestion service that subscribes to raw telemetry subjects, validates and normalizes events, stores them in `engagement_events`, and republishes on `telemetry.emo.normalized.*`.
- **Dependencies**: TEMO-01–02, existing service scaffolding patterns.
- **Acceptance Criteria**:
  - Service successfully processes synthetic telemetry events and writes normalized rows to the DB.
  - Normalization logic enforces canonical IDs and fills derived fields (e.g., `cohort_id` where available).
  - Invalid or malformed events are rejected with structured logs and metrics, not crashes.
- **Tests**:
  - **Unit**: Validation and normalization tests at handler level.
  - **Integration**: Pipeline tests from NATS raw events to DB rows and normalized NATS events.

---

## Milestone 2 – Engagement Metrics & Profiles

### TEMO-04 – Implement NPC Attachment Index Computation
- **Description**: Implement analytics in `svc.ethelred.emo.analytics` to compute NPC Attachment Index metrics (`R‑EMO‑MET‑001`) from normalized NPC interaction events.
- **Dependencies**: TEMO-03, requirements §4.3, conceptual `engagement_aggregates` table.
- **Acceptance Criteria**:
  - Analytics job computes attachment indices per NPC and per cohort for test datasets (e.g., controlled playthroughs).
  - Results are stored in `engagement_aggregates` and emitted via `events.ethelred.emo.v1.engagement_metrics`.
  - Indices behave sensibly on curated examples (e.g., high attachment for often-helpful NPCs; low for rarely engaged ones).
- **Tests**:
  - **Unit**: Metrics calculation tests on small synthetic datasets.
  - **Integration**: Tests running analytics on seeded `engagement_events` and asserting expected aggregated metrics.

### TEMO-05 – Implement Moral Tension Index Computation
- **Description**: Implement computation of Moral Tension Index (`R‑EMO‑MET‑002`) based on moral choice events, including option tagging and decision latency.
- **Dependencies**: TEMO-03, moral choice tagging from design, `engagement_aggregates` table.
- **Acceptance Criteria**:
  - Moral tension indices are computed per arc/scene and per cohort, reflecting the spread and difficulty of moral choices.
  - Metrics capture both choice distribution and decision latency, and are persisted along with NPC attachment indices where appropriate.
  - At least one test scenario demonstrates highly skewed vs balanced moral decisions and resulting tension metrics.
- **Tests**:
  - **Unit**: Calculation tests using scripted moral choice logs.
  - **Integration**: Pipeline tests from `telemetry.emo.moral_choice` events to persisted tension metrics.

### TEMO-06 – Implement Engagement Profile Clustering
- **Description**: Implement non-identifying engagement profile clustering (`R‑EMO‑MET‑003`) that groups sessions/cohorts into behavioral profiles (e.g., lore-focused, power-gamer, explorer).
- **Dependencies**: TEMO-04–05, clustering/analytics library selection, data sampling strategy.
- **Acceptance Criteria**:
  - Profiles are defined and documented, with clear criteria and example sessions for each type.
  - Clustering runs on test datasets and produces stable, interpretable profiles (no per-player tuning).
  - Profile assignments are stored in `engagement_aggregates` or a related table and surfaced via `ENGAGEMENT.METRICS`.
- **Tests**:
  - **Analytics/Validation**: Offline validation comparing profile assignments to human-labelled examples.
  - **Integration**: Job-level tests verifying cluster assignments and metrics persistence.

---

## Milestone 3 – Addiction Risk Analytics (Cohort-Level Only)

### TEMO-07 – Implement `addiction_risk_reports` Schema & Job Skeleton
- **Description**: Implement `addiction_risk_reports` table and a skeleton for `svc.ethelred.emo.addiction-job` that runs on schedule and prepares cohort-level aggregates.
- **Dependencies**: TEMO-02, TEMO-03, requirements §4.4.
- **Acceptance Criteria**:
  - `addiction_risk_reports` schema supports cohort identifiers (region, age_band, platform, etc.) and indicator fields.
  - Scheduled job runs without errors and writes placeholder reports into the DB for seeded test data.
  - No per-player identifiers are stored in risk reports.
- **Tests**:
  - **Unit**: Migration tests for the new table.
  - **Integration**: Job scheduling and basic report-writing tests on seeded data.

### TEMO-08 – Compute Cohort-Level Addiction Indicators
- **Description**: Implement computation of cohort-level addiction indicators (`R‑EMO‑ADD‑001…003`) such as night-time play fraction, “one more run” loops, and long-session distributions.
- **Dependencies**: TEMO-07, session metrics events, cohort definition logic.
- **Acceptance Criteria**:
  - For scripted test datasets, indicators correctly flag cohorts with intentionally unhealthy patterns and ignore balanced patterns.
  - Indicators are stored in `addiction_risk_reports` and emitted via `events.ethelred.emo.v1.addiction_risk`.
  - No per-player or session-level actions are derived directly from these indicators.
- **Tests**:
  - **Unit**: Indicator computation tests on synthetic session metrics.
  - **Integration**: End-to-end tests from `telemetry.emo.session_metrics` to risk reports and events.
  - **Adversarial**: Datasets designed to resemble but not actually reflect unhealthy patterns to check for over-sensitivity.

### TEMO-09 – Implement Design-Facing Addiction Risk Reports
- **Description**: Extend `svc.ethelred.emo.addiction-job` to generate human-readable, cohort-level reports and structured notes for designers and ethics reviewers.
- **Dependencies**: TEMO-08, Red Alert / reporting integration.
- **Acceptance Criteria**:
  - Reports clearly highlight systems/minigames associated with elevated indicators, with caveats about causality and uncertainty.
  - Reports are accessible via dashboards or Red Alert views without exposing PII.
  - At least one sample report is created for a seeded dataset and reviewed by a design/ethics stakeholder.
- **Tests**:
  - **Analytics/Validation**: Manual review of example reports for clarity and non-predatory framing.
  - **Integration**: Tests verifying report artifacts are written to the correct storage locations and referenced in dashboards.

---

## Milestone 4 – Safety, Integration & Readiness

### TEMO-10 – Enforce Non-Predatory Engagement & Addiction Usage
- **Description**: Codify and enforce architectural constraints ensuring engagement/addiction metrics are used only for cohort-level analysis and slow configuration changes, never real-time per-player optimization.
- **Dependencies**: TEMO-04–09, Guardrails Monitor policies, Content Governance, Story Memory.
- **Acceptance Criteria**:
  - Documentation and configuration explicitly forbid wiring metrics into real-time personalization loops or reward schedules.
  - Architecture review confirms all integrations with Story Teller, Quest System, and Content Governance respect these constraints.
  - Any attempt to add per-player tuning based on these metrics is blocked by design (e.g., config checks, code guardrails).
- **Tests**:
  - **Analytics/Validation**: Formal architecture review checklist signed off by at least one safety reviewer model.
  - **Integration**: Tests verifying that attempts to call non-existent “per-player tuning” endpoints fail and are logged.

### TEMO-11 – Integrate Engagement Metrics into Ethelred Coordinator & Red Alert
- **Description**: Wire `events.ethelred.emo.v1.engagement_metrics` and `events.ethelred.emo.v1.addiction_risk` into Ethelred Coordinator and Red Alert dashboards for cross-domain analysis.
- **Dependencies**: TEMO-06, TEMO-08–09, Coordinator implementation.
- **Acceptance Criteria**:
  - Coordinator can correlate engagement/addiction signals with 4D, audio, content, and story metrics via `trace_id`, `session_id`, and `build_id`.
  - Red Alert dashboards show engagement health views (NPC attachment, moral tension, addiction indicators) per build/cohort.
  - At least one cross-domain scenario (e.g., low engagement coinciding with specific 4D issues) is demonstrably visible.
- **Tests**:
  - **Integration/E2E**: Pipeline tests from telemetry through Coordinator to dashboards using seeded scenarios.

### TEMO-12 – Engagement Domain Traceability & Readiness Summary
- **Description**: Create a traceability matrix mapping `R‑EMO‑*` and relevant `R‑SYS‑*` requirements to services, schemas, events, and tests, plus a readiness summary feeding into `GAME-READINESS-ASSESSMENT.md`.
- **Dependencies**: Completion of TEMO-01–11, Master Test Registry.
- **Acceptance Criteria**:
  - Every engagement/addiction requirement is linked to at least one implementation and test, with gaps explicitly called out.
  - Readiness summary clearly states what is implemented, what remains design-only, and major ethical/safety risks.
  - Peer review (external model) confirms coverage and identifies any missing tasks or constraints.
- **Tests**:
  - **Analytics/Validation**: Peer review of the matrix and readiness summary; cross-check against requirements/solutions docs.



