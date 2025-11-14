# ETHELRED – 4D Vision QA Phase 4 Task Breakdown

**Domain**: 4D Vision QA (video + depth + time)  
**Source Requirements**: `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §2 + system-wide §1  
**Source Solutions**: `docs/solutions/ETHELRED-4D-VISION-SOLUTIONS.md`  

All tasks below must be implemented with **peer coding**, **pairwise testing**, and real test runs (no mock-only paths), following `/all-rules` and `/test-comprehensive`.

---

## Milestone 1 – Service Scaffolding & Contracts

### T4D-01 – Define 4D Vision Protobuf/NATS Contracts
- **Description**: Design and implement Protobuf messages and NATS subjects for `VISION.ANALYZE_REQUEST`, `VISION.ISSUE`, `VISION.SCENE_SUMMARY`, `VISION.COVERAGE`, and `VISION.TRENDS`, embedding the canonical envelope (`R‑SYS‑OBS‑001`).
- **Dependencies**: `docs/NATS-SYSTEM-ARCHITECTURE.md`, existing protobuf patterns in `proto/`, ETHELRED requirements §1–2.
- **Acceptance Criteria**:
  - Protos compile without warnings in the existing build.
  - All 4D Vision events share the canonical envelope fields and domains (`domain = "4D"`).
  - NATS subjects follow the patterns proposed in the 4D solutions doc.
  - Contracts are documented in `docs/solutions/ETHELRED-4D-VISION-SOLUTIONS.md` (or an adjacent schema appendix).
  - A basic security review has been performed for schemas and subjects (no sensitive fields in public events; subjects align with existing auth/authorization patterns).
- **Tests**:
  - **Unit**: Serialization/deserialization round‑trip tests for each message type.
  - **Integration**: End‑to‑end NATS send/receive tests using the SDK to ensure subjects and payloads work across at least one running worker.

### T4D-02 – Implement Segment & Issue Storage Schema
- **Description**: Design and migrate PostgreSQL schemas for 4D segments, issues, scene summaries, and coverage metrics, matching the conceptual tables in the solutions doc and `R‑4D‑OUT‑001…003`.
- **Dependencies**: Database migration tooling under `database/migrations/`, global data rules `R‑SYS‑DATA‑001…004`.
- **Acceptance Criteria**:
  - New migration files exist, apply cleanly against the dev database.
  - Tables store segment metadata (build, scene, camera set, sampling mode, media URIs) and normalized issues/summaries with appropriate indexes.
  - Retention and deletion policies for segments/issues are documented at least at a conceptual level.
  - Data classification and access controls are documented (what constitutes PII/telemetry, which roles/services can read what), including how right-to-forget/delete requests would be honored.
- **Tests**:
  - **Unit**: Migration smoke tests (apply/rollback on a test database).
  - **Integration**: CRUD tests from a minimal 4D repository module that read/write segments and issues using the new schema.
  - **Analytics/Validation**: Dry-run migration on a staging-like dataset with rollback verification and integrity checks.

### T4D-03 – Scaffold `svc.ethelred.4d.ingest` Service
- **Description**: Create the ingest service skeleton (`svc.ethelred.4d.ingest`) that receives 4D segment descriptors, normalizes metadata, writes records to the DB, and publishes `VISION.ANALYZE_REQUEST`.
- **Dependencies**: T4D-01 (contracts), T4D-02 (schema), existing service template patterns in `services/`.
- **Acceptance Criteria**:
  - Service boots successfully in local/dev environment and subscribes to the configured ingest subject or HTTP endpoint.
  - Segment descriptors are validated and persisted with all required fields, with errors logged but not crashing the worker.
  - For valid segments, a `VISION.ANALYZE_REQUEST` message is published with references (not media bytes).
- **Tests**:
  - **Unit**: Handler-level tests validating metadata normalization and error paths.
  - **Integration**: NATS-driven test that publishes a synthetic segment descriptor and asserts DB + outgoing message side effects.

### T4D-04 – Scaffold `svc.ethelred.4d.analyzer` Service
- **Description**: Create analyzer service skeleton with pluggable detector modules for animation, physics, rendering, lighting, performance, and flow, plus a pipeline that will later orchestrate detectors over segments.
- **Dependencies**: T4D-01 (contracts), T4D-02 (schema), ingest service events (T4D-03).
- **Acceptance Criteria**:
  - Service subscribes to `VISION.ANALYZE_REQUEST` and can fetch segment metadata.
  - Detector interfaces are defined (e.g., `analyze(segment) -> list[DetectorFinding]`) for all six detection categories.
  - Analyzer can emit stub `VISION.ISSUE` and `VISION.SCENE_SUMMARY` events with canned payloads for a known test segment.
- **Tests**:
  - **Unit**: Tests for detector interface contracts and basic pipeline orchestration (stubs).
  - **Integration**: End‑to‑end pipeline test with a synthetic segment going through ingest → analyzer → events.

---

## Milestone 2 – UE5 Capture & AI Testing Integration

### T4D-05 – Author UE5 4D Capture Instrumentation Spec
- **Description**: Write and agree on a UE5 instrumentation spec for 4D capture (cameras, sampling modes, metadata fields, event hooks) aligned with `R‑4D‑IN‑001…003` and the AI Testing gateway.
- **Dependencies**: UE5 architecture docs, ETHELRED 4D requirements §2, AI Testing System integration guide.
- **Acceptance Criteria**:
  - Spec doc exists (UE5‑facing) describing how to configure cameras, sampling modes (frame/window/event), and key gameplay events.
  - Spec maps required metadata fields to UE5 data sources (camera IDs, scene IDs, performance counters, gameplay events).
  - Spec is referenced from both the 4D solutions doc and UE5 technical documentation.
- **Tests**:
  - **Analytics/Validation**: Design review and walkthrough with at least one future UE5 implementer; trace a sample horror scene through the spec.

### T4D-06 – Wire AI Testing Gateway to 4D Ingest
- **Description**: Extend the AI Testing System / capture gateway to package UE5 4D capture into segments, store media in Red Alert (or equivalent), and post segment descriptors to `svc.ethelred.4d.ingest`.
- **Dependencies**: T4D-03 (ingest service), existing AI Testing System endpoints, Red Alert media storage contracts.
- **Acceptance Criteria**:
  - Gateway can accept mocked UE5 4D streams and emit properly formed segment descriptors referencing stored media URIs.
  - Ingest service receives and persists these descriptors, and publishes corresponding `VISION.ANALYZE_REQUEST` messages.
  - Failure modes (invalid metadata, storage failures) are logged and do not crash the gateway.
- **Tests**:
  - **Integration**: AI Testing System → NATS → ingest pipeline test using synthetic media URIs.
  - **E2E**: CLI or script that simulates a short 4D capture session and verifies that segments appear in the DB and analyzer queue.

### T4D-07 – Implement Basic End-to-End 4D Happy Path
- **Description**: Implement a minimal analysis pipeline that takes a simple test scene (e.g., one camera, short clip) from capture through ingest, analyzer stub, and into Red Alert/Ethelred Coordinator.
- **Dependencies**: T4D-04 (analyzer skeleton), T4D-06 (gateway wiring), existing Ethelred Coordinator subscriptions.
- **Acceptance Criteria**:
  - Running a scripted test captures at least one segment and produces at least one `VISION.ISSUE` and `VISION.SCENE_SUMMARY` event.
  - Ethelred Coordinator receives and logs the events, and they appear in a basic Red Alert 4D section/dashboard.
  - All steps are documented in a “4D Vision QA smoke test” runbook.
- **Tests**:
  - **E2E**: Automated or semi‑automated pipeline test verified in CI where possible; manual verification steps documented where automation is not yet possible.

---

## Milestone 3 – Detection Pipelines & Coverage Analytics

### T4D-08 – Implement Animation & Physics Detectors
- **Description**: Implement detection modules for animation/rigging (`R‑4D‑DET‑001`) and physics/collisions (`R‑4D‑DET‑002`), including signal extraction and thresholds, with clear explainability output.
- **Dependencies**: T4D-04 (detector interfaces), media access utilities from AI Testing/Red Alert, ETHELRED requirements §2.3.
- **Acceptance Criteria**:
  - Detector implementations can analyze test segments and produce findings for known defects (e.g., scripted T‑pose, deliberate collision bugs).
  - Explainability fields (signals, thresholds, notes) are populated in `VISION.ISSUE.explainability`.
  - Configuration supports toggling sensitivity thresholds per environment (dev/QA/staging).
- **Tests**:
  - **Unit**: Detector-level tests with synthetic feature inputs.
  - **Integration**: Tests that feed crafted 4D segments and assert `VISION.ISSUE` payloads for animation/physics issues.
  - **Adversarial**: Negative tests ensuring detectors do not over‑fire on clean segments.

### T4D-09 – Implement Rendering & Lighting Detectors
- **Description**: Implement detectors for rendering artifacts (`R‑4D‑DET‑003`) and lighting/horror atmosphere issues (`R‑4D‑DET‑004`), focusing on texture/LOD/Z‑fighting problems and horror lighting intent mismatches.
- **Dependencies**: T4D-04 (detector interfaces), horror intent metadata from level design where available.
- **Acceptance Criteria**:
  - Detectors identify known rendering errors and lighting misconfigurations in curated test scenes.
  - Severity and confidence fields map correctly to Red Alert expectations.
  - Configurable thresholds for what counts as “too bright/dim” per horror scene metadata.
- **Tests**:
  - **Unit**: Feature extraction and threshold logic tests.
  - **Integration**: Scene‑level test runs with expected `VISION.ISSUE` records for rendering/light issues.
  - **Adversarial**: Tests using stylistically unusual but acceptable scenes to verify that detectors can be tuned, not hard‑coded.

### T4D-10 – Implement Performance & Flow Detectors
- **Description**: Implement detectors for performance/frame pacing (`R‑4D‑DET‑005`) and gameplay flow/soft‑locks (`R‑4D‑DET‑006`) based on frame timing and movement/navigation telemetry.
- **Dependencies**: T4D-04 (detector interfaces), accurate performance counters from UE5 capture, movement/navigation event feeds.
- **Acceptance Criteria**:
  - Performance detector flags sustained FPS drops and frame time spikes in stress tests; flow detector flags scripted stuck/loop scenarios.
  - Detectors include configuration for thresholds per platform and build type.
  - Flow detector outputs clearly identify candidate soft‑lock locations and patterns.
- **Tests**:
  - **Unit**: Analytics logic tests for FPS and movement time series.
  - **Integration**: End‑to‑end tests that simulate slow performance and loops with expected `VISION.ISSUE` outputs.
  - **Analytics/Validation**: Offline analysis validating detector outputs against manually labeled sequences.

### T4D-11 – Implement Aggregation & Coverage Job
- **Description**: Implement `svc.ethelred.4d.coverage-job` that aggregates segment/issue data per build/scene and emits coverage/trend events (`R‑4D‑OUT‑003`).
- **Dependencies**: T4D-02 (schema), detectors (T4D‑08–10), NATS system.
- **Acceptance Criteria**:
  - Coverage job can run on a non‑trivial dataset and produce `VISION.COVERAGE` and `VISION.TRENDS` events with build‑level metrics.
  - Job is idempotent and can be safely rerun for the same build.
  - Emitted metrics are consumable by Red Alert for dashboards without manual reshaping.
- **Tests**:
  - **Unit**: Aggregation logic tests on in‑memory datasets.
  - **Integration**: Scheduled job tests using a seeded DB snapshot; verify emitted events, absence of duplicate records, and stable behavior under expected production-like volumes (load/performance test).

---

## Milestone 4 – Hardening, Observability & Readiness

### T4D-12 – Observability & Dashboards
- **Description**: Add structured logging, metrics, and basic dashboards for all 4D services (ingest, analyzer, coverage-job) consistent with system‑wide observability requirements.
- **Dependencies**: Existing logging/metrics stack (CloudWatch, Prometheus/Grafana or equivalent), Master Test Registry guidance.
- **Acceptance Criteria**:
  - Each 4D service exposes `/healthz` and `/metrics` endpoints with key KPIs (ingest/analysis latency, issues per build, coverage ratios).
  - At least one dashboard exists summarizing 4D coverage and issue counts by build/scene.
  - Logs include trace IDs and segment IDs sufficient to debug any reported issue.
  - SLOs/SLAs for the 4D domain (e.g., max ingest/analysis latency, minimum coverage per build) are defined and visualized in dashboards with alert thresholds.
- **Tests**:
  - **Integration**: Health/metrics endpoint tests.
  - **Analytics/Validation**: Manual dashboard review to confirm required signals are visible and correctly aggregated.

### T4D-13 – Data Quality & Ambiguous Input Handling
- **Description**: Implement robust handling for degraded/ambiguous inputs (missing depth, occluded cameras, corrupted media) so that they surface as `data_quality` issues rather than silent failures.
- **Dependencies**: Detectors (T4D‑08–10), ingest service validation, AI Testing media access.
- **Acceptance Criteria**:
  - Analyzer detects and labels segments with insufficient or corrupted data as `data_quality` issues with lowered confidence, per solutions doc.
  - No crash or undefined behavior occurs when media is missing/partial; errors are logged and surfaced via Red Alert.
  - Documentation describes how QA should interpret and act on data quality issues.
- **Tests**:
  - **Unit**: Tests for detector behavior under missing/partial inputs.
  - **Integration/Adversarial**: Tests feeding intentionally corrupted or partial segments and verifying the right `data_quality` issue events are emitted.

### T4D-14 – Degradation & Failure Mode Validation
- **Description**: Validate that the 4D domain degrades gracefully when services are unavailable or slow, complying with `R‑SYS‑SAFE‑002` (Coordinator marks domain `degraded` and uses conservative defaults).
- **Dependencies**: Ethelred Coordinator implementation, circuit breakers in NATS client layer.
- **Acceptance Criteria**:
  - When 4D services are down or timing out, Coordinator marks 4D as `degraded` and emits appropriate `SYS.HEALTH` events.
  - Game runtime can proceed with conservative defaults (no blocking on 4D) in representative test scenarios.
  - Failure scenarios and operator runbook are documented for production, including replay/backfill procedures and escalation paths for prolonged degradation.
- **Tests**:
  - **Integration/E2E**: Chaos tests where 4D services are intentionally stopped or delayed; verify Coordinator behavior and game resilience.

### T4D-15 – 4D Vision Readiness Review & Traceability Matrix
- **Description**: Create a traceability matrix linking `R‑4D‑*` + relevant `R‑SYS‑*` requirements to implemented services, events, schemas, and tests; perform a readiness review for the 4D domain.
- **Dependencies**: All prior 4D tasks, ETHELRED requirements §2, Master Test Registry.
- **Acceptance Criteria**:
  - Traceability matrix exists (markdown or spreadsheet) and covers every 4D requirement ID with at least one implementation and one test reference.
  - A short readiness summary for 4D is produced and can be dropped into `GAME-READINESS-ASSESSMENT.md`.
  - Cross-environment rollout strategy (dev/stage/prod, feature flags, contract/schema versioning) is documented and referenced from the matrix.
  - Peer review (at least one external model) confirms no major gaps in the 4D plan relative to requirements/solutions.
- **Tests**:
  - **Analytics/Validation**: Peer review of the matrix and readiness summary; cross‑check against requirements and solutions docs.


