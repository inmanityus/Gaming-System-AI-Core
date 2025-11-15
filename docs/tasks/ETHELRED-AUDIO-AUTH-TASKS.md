# ETHELRED – Audio Authentication & Vocal Simulator QA Phase 4 Task Breakdown

**Domain**: Audio Authentication & Vocal Simulator QA  
**Source Requirements**: `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §3 + system-wide §1  
**Source Solutions**: `docs/solutions/ETHELRED-AUDIO-AUTH-SOLUTIONS.md`  

All tasks below must follow **peer coding**, **pairwise testing**, and real test runs (no mock-only paths), aligned with `/all-rules` and `/test-comprehensive`.

---

## Milestone 1 – Service Foundations & Event Contracts

### TAUD-01 – Define Audio Protobuf Messages & NATS Subjects
- **Description**: Specify and implement Protobuf messages and NATS subjects for `AUDIO.SEGMENT_CREATED`, `AUDIO.SCORES`, `AUDIO.REPORT`, and `AUDIO.FEEDBACK`, embedding the canonical envelope with `domain = "Audio"`.
- **Dependencies**: Existing protobuf conventions in `proto/`, `docs/NATS-SYSTEM-ARCHITECTURE.md`, audio requirements §3.2–3.3.
- **Acceptance Criteria**:
  - Protos compile cleanly and are referenced by at least one Python client.
  - All audio events use the canonical envelope fields, with `issue_type` and `segment_type` enums covering required cases.
  - Event contracts are documented or cross-referenced from the audio solutions doc.
- **Tests**:
  - **Unit**: Protobuf round‑trip serialization tests for each audio message.
  - **Integration**: NATS send/receive tests ensuring subject names and payload shapes interoperate with the SDK.

### TAUD-02 – Implement Audio Segment & Score Storage Schema
- **Description**: Design and migrate database schemas for audio segments, per‑segment scores, and batch reports, matching the conceptual tables in the solutions doc and `R‑AUD‑OUT‑001…003`.
- **Dependencies**: DB migration system under `database/migrations/`, global data rules `R‑SYS‑DATA‑001…004`.
- **Acceptance Criteria**:
  - New migrations create tables for segments, scores, and reports with appropriate indexing on `segment_id`, `speaker_id`, `archetype_id`, `language_code`, and `build_id`.
  - Migrations apply and rollback cleanly in dev/test environments.
  - Retention strategy for raw segments vs aggregated scores is at least documented conceptually.
- **Tests**:
  - **Unit**: Migration smoke tests on a disposable database.
  - **Integration**: Repository-level tests that read/write segments and scores via the new schema.

### TAUD-03 – Scaffold `svc.ethelred.audio.capture` Service
- **Description**: Create the capture/segmentation service skeleton that receives audio streams via virtual routing, segments them into analysis units, enriches with metadata, stores media references, and emits `AUDIO.SEGMENT_CREATED`.
- **Dependencies**: TAUD-01 (contracts), TAUD-02 (schema), existing service scaffolding patterns in `services/`.
- **Acceptance Criteria**:
  - Service boots and subscribes to the configured audio input channel(s) or API endpoint(s).
  - Segmentation pipeline can process synthetic streams into segments with metadata fields required by `R‑AUD‑IN‑002`.
  - For each accepted segment, a `AUDIO.SEGMENT_CREATED` event is emitted referencing stored media URIs, not raw bytes.
- **Tests**:
  - **Unit**: Segmentation and metadata enrichment tests at handler level.
  - **Integration**: Pipeline test using a test audio fixture to verify DB writes and emitted events.

---

## Milestone 2 – Capture Integration & Basic Pipeline

### TAUD-04 – Define Virtual Audio Routing Integration Spec
- **Description**: Produce a UE5/audio-engine integration spec for virtual audio routing (buses, sample rates, channels), detailing how game audio (mix and per-bus) reaches `svc.ethelred.audio.capture` while satisfying `R‑AUD‑IN‑001`.
- **Dependencies**: UE5 audio architecture docs, prior vocal synthesis integration, audio requirements §3.2.
- **Acceptance Criteria**:
  - Spec describes exact routing of main mix and key buses (dialogue, simulator pre/post, ambience, SFX) into virtual devices.
  - Timing and metadata alignment with game events and Story Teller line IDs is clearly defined.
  - Spec is cross-linked from both the audio solutions doc and UE5 technical documentation.
- **Tests**:
  - **Analytics/Validation**: Design review walkthrough tracing a sample scene and confirming all required metadata is capturable.

### TAUD-05 – Implement Basic Capture Path from UE5 to Audio Service
- **Description**: Implement the minimal set of integration code and configuration so that test UE5 sessions can stream audio into `svc.ethelred.audio.capture` via virtual routing.
- **Dependencies**: TAUD-04 (integration spec), TAUD-03 (capture service).
- **Acceptance Criteria**:
  - In a dev test scenario, UE5 (or a simulator harness) can send audio that is segmented and stored with the correct metadata.
  - Latency and throughput are within acceptable initial bounds for offline/near‑real‑time analysis.
  - Failure cases (no device, misconfigured routing) are logged and surfaced without crashing the service.
- **Tests**:
  - **Integration**: UE5 (or mock) → virtual device → capture service → DB & `AUDIO.SEGMENT_CREATED` events.
  - **E2E**: Smoke test script that runs a short demo scene and confirms segments exist in storage and the DB.

### TAUD-06 – Wire `svc.ethelred.audio.metrics` and End-to-End Happy Path
- **Description**: Scaffold `svc.ethelred.audio.metrics`, subscribing to `AUDIO.SEGMENT_CREATED`, retrieving audio media, and emitting stub `AUDIO.SCORES` events to validate pipeline wiring.
- **Dependencies**: TAUD-01 (contracts), TAUD-02 (schema), TAUD-03–05.
- **Acceptance Criteria**:
  - Metrics service can consume `AUDIO.SEGMENT_CREATED` and fetch refs to media for at least one test segment.
  - Stub scoring pipeline emits `AUDIO.SCORES` events with placeholder metrics and bands, written to the DB.
  - A single scripted scenario demonstrates end‑to‑end flow: UE5/audio fixture → capture → metrics → DB & NATS.
- **Tests**:
  - **Unit**: Handler tests for metrics service stub.
  - **Integration/E2E**: Pipeline test from synthetic audio to persisted `AUDIO.SCORES` row and event.

---

## Milestone 3 – Metrics, Reports & Feedback

### TAUD-07 – Implement Intelligibility & Naturalness Metrics
- **Description**: Implement metric pipelines for human intelligibility (`R‑AUD‑MET‑001`) and naturalness/prosody (`R‑AUD‑MET‑002`), using reference distributions and capturing bands (`acceptable`, `degraded`, etc.).
- **Dependencies**: TAUD-06 (metrics skeleton), human speech baseline store from solutions doc.
- **Acceptance Criteria**:
  - For curated test clips, intelligibility and naturalness metrics differentiate clearly between clean vs degraded audio.
  - Metric outputs populate both scalar scores and band classifications, stored in `AUDIO.SCORES`.
  - Configuration allows environment‑specific thresholds and reference corpora settings.
- **Tests**:
  - **Unit**: Metrics calculations and thresholding on synthetic feature vectors.
  - **Integration**: Tests that run known “good” and “bad” clips through the pipeline and assert expected bands.
  - **Adversarial**: Clips with unusual speaking styles that should not be mis‑classified as failures.

### TAUD-08 – Implement Archetype Conformity & Simulator Stability Metrics
- **Description**: Implement metrics for archetype conformity (`R‑AUD‑MET‑003`) and simulator stability (`R‑AUD‑MET‑004`), leveraging archetype voice profiles and simulator metadata.
- **Dependencies**: Archetype voice profiles store, vocal simulator metadata, TAUD-06.
- **Acceptance Criteria**:
  - For each tested archetype, metrics capture expected F0/formant ranges and roughness/instability patterns, distinguishing on-profile vs clearly misaligned samples.
  - Simulator stability metric flags glitchy or unstable simulator behavior in stress scenarios.
  - Output is stored in `AUDIO.SCORES` and visible in batch reports per archetype and build.
- **Tests**:
  - **Unit**: Feature extraction and scoring logic tests.
  - **Integration**: Archetype-specific test runs using existing vocal synthesis fixtures.
  - **Adversarial**: Simulated failure modes (e.g., forced clipping, denormals) to verify stability detection.

### TAUD-09 – Implement Audio Aggregation & Batch Reporting
- **Description**: Implement `svc.ethelred.audio.reports` that aggregates per‑segment scores into per‑archetype, per‑language, and per‑scene distributions and emits `AUDIO.REPORT` events.
- **Dependencies**: TAUD-02 (schema), TAUD-07–08 (metrics), NATS infrastructure.
- **Acceptance Criteria**:
  - Reports can be generated for at least one build and include archetype and language‑level distributions as described in `R‑AUD‑OUT‑002`.
  - Reports are idempotent per build/time window and recorded in the DB.
  - Red Alert can consume and render these reports without additional transformation.
- **Tests**:
  - **Unit**: Aggregation logic tests over in‑memory datasets.
  - **Integration**: Scheduled job tests using seeded DB snapshots; verify `AUDIO.REPORT` events and DB rows.

### TAUD-10 – Implement Audio Feedback Service
- **Description**: Implement `svc.ethelred.audio.feedback` that consumes metrics and reports to generate structured, non‑auto‑tuning recommendations for simulator and archetype adjustments.
- **Dependencies**: TAUD-07–09, archetype profiles, simulator config store.
- **Acceptance Criteria**:
  - Feedback outputs reference archetypes/scenarios and propose specific offline tuning actions (e.g., “reduce instability band X for archetype Y in scene Z”).
  - Feedback is persisted and emitted via `AUDIO.FEEDBACK` events without any direct runtime parameter changes.
  - Designers and audio engineers can trace back each recommendation to underlying metric trends.
- **Tests**:
  - **Unit**: Feedback rule logic given synthetic metric inputs.
  - **Integration**: End‑to‑end test that ingests a set of metrics and confirms appropriate feedback artifacts are produced.

---

## Milestone 4 – Safety, Observability & Readiness

### TAUD-11 – Observability & Dashboards for Audio Domain
- **Description**: Add structured logging, metrics, and dashboards for all audio services (capture, metrics, reports, feedback), consistent with global observability standards.
- **Dependencies**: Logging/metrics stack (CloudWatch, Prometheus/Grafana), Master Test Registry.
- **Acceptance Criteria**:
  - Audio services expose `/healthz` and `/metrics` endpoints with key KPIs (segments ingested, scoring latency, error rates, archetype conformity distributions).
  - Dashboards exist summarizing audio QA health by build, language, and archetype.
  - Logs contain trace IDs, segment IDs, and archetype IDs sufficient for debugging.
- **Tests**:
  - **Integration**: Health and metrics endpoint tests.
  - **Analytics/Validation**: Manual verification that dashboards show required metrics with correct labels and breakdowns.

### TAUD-12 – Enforce Non-Predatory Use & Failure Modes
- **Description**: Validate that audio metrics and feedback comply with `R‑SYS‑SAFE‑001` and audio addiction/safety constraints, ensuring no per‑player optimization loops or manipulative tuning.
- **Dependencies**: TAUD-07–10, engagement/addiction analytics design, Guardrails Monitor policies.
- **Acceptance Criteria**:
  - Architecture review confirms audio signals are used only for offline, cohort‑level analysis and slow configuration changes, not real‑time per‑player tuning.
  - Failure scenarios (missing metrics services, degraded audio pipeline) degrade gracefully without harming game runtime or safety guarantees.
  - Documented runbook describes forbidden wiring patterns and how they are prevented (config or code).
- **Tests**:
  - **Analytics/Validation**: Design/security review with explicit checklists against requirements.
  - **Integration**: Tests that simulate service outages and confirm Coordinator marks audio domain as `degraded` without impacting core gameplay.

### TAUD-13 – Audio Domain Traceability & Readiness Summary
- **Description**: Build a traceability matrix linking `R‑AUD‑*` and relevant `R‑SYS‑*` requirements to services, events, schemas, and tests, and produce an audio readiness summary for inclusion in `GAME-READINESS-ASSESSMENT.md`.
- **Dependencies**: Completion of core audio tasks (TAUD‑01–12), Master Test Registry, Ethelred requirements.
- **Acceptance Criteria**:
  - Traceability matrix covers every audio requirement with at least one implementation and one test reference.
  - Readiness summary clearly indicates implemented vs planned capabilities and open risks for audio QA.
  - At least one external peer review (model) confirms coverage and highlights any remaining gaps.
- **Tests**:
  - **Analytics/Validation**: Peer review of the matrix and readiness summary; cross‑checked against requirements and solutions docs.



