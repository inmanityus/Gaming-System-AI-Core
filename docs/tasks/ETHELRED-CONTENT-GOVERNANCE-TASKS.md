# ETHELRED – Content Governance & Content Levels Phase 4 Task Breakdown

**Domain**: Content Governance & Content Levels  
**Source Requirements**: `CONTENT-GOVERNANCE-REQUIREMENTS.md`, `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §5 + system-wide §1  
**Source Solutions**: `docs/solutions/ETHELRED-CONTENT-GOVERNANCE-SOLUTIONS.md`  

All tasks must follow **peer coding**, **pairwise testing**, and real test runs (no mock-only paths), and respect the core constraint that Guardrails Monitor remains the enforcement authority.

---

## Milestone 1 – Content Level Manager in Settings

### TCG-01 – Implement Core Content Governance Schemas & Migrations
- **Description**: Implement migrations for `content_levels`, `player_content_profiles`, `session_content_policy`, and `content_violations` tables as described in the requirements doc.
- **Dependencies**: DB migration tooling, `CONTENT-GOVERNANCE-REQUIREMENTS.md` §3.3, existing Settings DB schema.
- **Acceptance Criteria**:
  - All four tables are created with appropriate columns, constraints, and indexes (e.g., on `player_id`, `session_id`, `category`, `severity`).
  - Migrations apply and rollback cleanly, including on seeded test data.
  - Sample rows can be inserted for system default profiles and test violations without constraint errors.
- **Tests**:
  - **Unit**: Migration apply/rollback tests.
  - **Integration**: Repository tests that create/read/update/delete profiles, player policies, session snapshots, and violations.

### TCG-02 – Implement `content_level_manager` Module in Settings
- **Description**: Implement `content_level_manager.py` and `content_schemas.py` in the Settings service to manage content profiles, per-player policies, and effective policy resolution.
- **Dependencies**: TCG-01, existing Settings service architecture, Pydantic/dataclass patterns.
- **Acceptance Criteria**:
  - Module can create and retrieve system default profiles and custom profiles.
  - Effective per-player policy resolution (base profile + overrides) behaves as specified in `CG‑3.2.1…3.2.3`.
  - Error handling for invalid levels, conflicting overrides, and missing profiles is well-defined and logged.
- **Tests**:
  - **Unit**: Profile creation, policy resolution, and edge-case tests in `tests/test_content_levels.py`.
  - **Integration**: Tests exercising Settings service endpoints using the module.

### TCG-03 – Expose Content Profile & Player Policy APIs
- **Description**: Add HTTP/NATS APIs for profile management and per-player policy read/write (`CG‑4.1.1–4.1.2`), enforcing appropriate authentication and authorization.
- **Dependencies**: TCG-02, Auth/Settings existing API infrastructure.
- **Acceptance Criteria**:
  - Endpoints/subjects exist for listing, creating, updating profiles, and getting/setting per-player policies.
  - Admin-only operations are properly restricted; per-player operations are scoped to the current player or privileged tools.
  - API contracts are documented and include examples for automated tools.
- **Tests**:
  - **Unit**: Handler-level tests for each endpoint/subject.
  - **Integration**: API tests that exercise profile and policy flows end-to-end against a test database.

### TCG-04 – Implement Session Content Policy Snapshot Flow
- **Description**: Implement logic in Settings to compute per-session content policy snapshots on session start, persist them in `session_content_policy`, and publish `settings.content_policy.session_started` on NATS.
- **Dependencies**: TCG-01–03, session lifecycle events, `NATS-SYSTEM-ARCHITECTURE.md`.
- **Acceptance Criteria**:
  - On session start, a snapshot row is written with correct levels, enabled themes, and `policy_version`.
  - A `settings.content_policy.session_started` message is emitted containing `session_id`, `player_id`, snapshot, and `policy_version`.
  - Idempotent behavior for repeated/duplicate session start events is defined and implemented.
- **Tests**:
  - **Unit**: Snapshot computation tests given various player/profile combinations.
  - **Integration**: End-to-end tests from session start event to DB row + NATS message.

---

## Milestone 2 – Ethelred Content Validator Domain

### TCG-05 – Define Content Observation & Violation Event Contracts
- **Description**: Define schemas and NATS subjects for content observation events (`events.ethelred.content.v1.observation.*`) and `events.ethelred.content.v1.violation`, aligned with the canonical envelope.
- **Dependencies**: Content requirements §4–5, solutions doc §3, canonical envelope spec, `ETHELRED-4D-VISION-SOLUTIONS` and `ETHELRED-AUDIO-AUTH-SOLUTIONS`.
- **Acceptance Criteria**:
  - Event payloads support per-scene `category_scores` and include IDs (`scene_id`, `content_ids`, `session_id`) and modality info.
  - Violation events include required fields (`expected_level`, `observed_level`, `detected_by`, `evidence_refs`, `recommended_action`).
  - Event contracts are documented with example payloads for each modality and fused observations.
- **Tests**:
  - **Unit**: Schema validation tests for observation and violation messages.
  - **Integration**: NATS send/receive tests using the Python SDK.

### TCG-06 – Scaffold Text, Vision, and Audio Content Classifiers
- **Description**: Create service skeletons for `svc.ethelred.content.text`, `.vision`, and `.audio` that consume relevant inputs and produce normalized `CONTENT.OBSERVATION` events.
- **Dependencies**: TCG-05, existing 4D Vision and Audio QA outputs, Story Teller text channels.
- **Acceptance Criteria**:
  - Each classifier service can consume incoming events (text, 4D outputs, audio metrics) and emit observation events on the appropriate subjects.
  - Classifier interfaces support pluggable model implementations and threshold configuration.
  - Basic stub implementations exist that pass through test data and emit synthetic category scores.
- **Tests**:
  - **Unit**: Handler/interface tests for each classifier service.
  - **Integration**: Pipeline tests that feed simple test content through text/vision/audio classifier stubs to observation events.

### TCG-07 – Implement Contextual Cross-Checker Service
- **Description**: Implement `svc.ethelred.content.context` that fuses modality-specific observations into a unified `observation.fused` event and flags cross-modal inconsistencies.
- **Dependencies**: TCG-06, event contracts (TCG-05), access to policy snapshots for context if needed.
- **Acceptance Criteria**:
  - Service can receive text, vision, and audio observations for a scene and produce a fused view with aggregated category scores.
  - In test scenarios with intentionally mismatched modalities (e.g., mild text, extreme visuals), cross-checker flags inconsistencies.
  - Fused observations are written to logs/DB where appropriate and emitted on `events.ethelred.content.v1.observation.fused`.
- **Tests**:
  - **Unit**: Fusion logic tests given sets of modality-specific inputs.
  - **Integration**: Scenario tests with synthetic mismatches and expected fused outputs.

### TCG-08 – Implement Violation Engine & Logger
- **Description**: Implement `svc.ethelred.content.violation` that compares fused content observations against session content policy snapshots and writes to `content_violations` while emitting `CONTENT.VIOLATION` events.
- **Dependencies**: TCG-01, TCG-04–07, Settings policy APIs.
- **Acceptance Criteria**:
  - For test scenarios where observed levels exceed allowed levels, violation rows and events are produced with correct fields.
  - For allowed content, no violations are produced while metrics are still logged.
  - Severe/repeated violations can be flagged with elevated severity and optional Red Alert hooks.
- **Tests**:
  - **Unit**: Policy comparison and violation construction tests.
  - **Integration/E2E**: End-to-end tests from session start and content observations through violation logging and events.

---

## Milestone 3 – Integration with Guardrails, Ethelred & Other Domains

### TCG-09 – Integrate Content Policy Snapshots into Guardrails Monitor
- **Description**: Wire `settings.content_policy.session_started` events into Guardrails Monitor so that content policies influence model safety filters and caches.
- **Dependencies**: TCG-04, Guardrails Monitor implementation, Model Management service.
- **Acceptance Criteria**:
  - Guardrails Monitor consumes policy snapshots and updates internal caches keyed by `session_id` and `policy_version`.
  - Safety filters respect content levels per category (e.g., more strict filtering for low-violence profiles).
  - Integration is documented with example flows and troubleshooting notes.
- **Tests**:
  - **Integration**: Tests that simulate session starts and verify Guardrails uses the correct policy in downstream filtering behaviors (e.g., via controlled test prompts).

### TCG-10 – Integrate Content Validator with Ethelred Coordinator & Red Alert
- **Description**: Connect content observation/violation events into Ethelred Coordinator and Red Alert dashboards for multi-domain analysis.
- **Dependencies**: TCG-06–08, Coordinator, Red Alert integration.
- **Acceptance Criteria**:
  - Coordinator correlates content violations with other domain signals (4D issues, audio problems, engagement metrics) via shared IDs.
  - Red Alert dashboards show content violation counts by category/profile/build, with direct links to evidence.
  - At least one cross-domain test scenario (e.g., extreme horror content with low-profile players) is visible in dashboards.
- **Tests**:
  - **Integration/E2E**: Pipeline tests that generate violations and verify they appear in Coordinator aggregates and Red Alert views.

### TCG-11 – End-to-End Scenario Tests for Content Governance Flows
- **Description**: Define and automate key end-to-end scenarios (e.g., TeenSafe vs Mature profiles) that exercise Settings → Guardrails → Ethelred content validation flows.
- **Dependencies**: TCG-02–10, Master Test Registry.
- **Acceptance Criteria**:
  - Scenario where a TeenSafe player encounters over-level content triggers violations and Red Alerts, while a Mature profile does not.
  - Scenario where content is correctly tuned for both profiles results in no violations and stable metrics.
  - Scenarios are documented and included in `/test-comprehensive` runs after major content changes.
- **Tests**:
  - **E2E**: Automated or semi-automated flows using test harnesses and curated content; results logged and tracked in the Master Test Registry.

---

## Milestone 4 – Observability, Governance & Readiness

### TCG-12 – Implement Content Governance Observability & Dashboards
- **Description**: Add metrics, logs, and dashboards for Content Level Manager, Content Validator, and violation flows, as required by `CG‑5.*` and system-wide observability rules.
- **Dependencies**: TCG-01–11, observability stack, Master Test Registry.
- **Acceptance Criteria**:
  - Metrics cover policy snapshot coverage, violation counts by category/profile/severity, and content policy lookup latency.
  - Dashboards present a clear at-a-glance view of content policy coverage and violation trends per build/environment.
  - Logs include correlation IDs and evidence references sufficient for compliance and audit investigations.
- **Tests**:
  - **Integration**: Health and metrics endpoint tests for relevant services.
  - **Analytics/Validation**: Manual dashboard inspection and sanity checks on metrics trends with seeded data.

### TCG-13 – Governance & Audit Trail Validation
- **Description**: Validate that all profile changes, policy overrides, and violations are audit-logged in a way that satisfies `CG‑5.3` and legal/compliance needs.
- **Dependencies**: TCG-01–03, TCG-08–10.
- **Acceptance Criteria**:
  - Audit logs capture who/when/what for profile and policy changes and can be reconstructed for compliance audits.
  - Violation data can be filtered and exported per build/profile/category for external review (e.g., ESRB/PEGI).
  - At least one dry-run compliance review is performed using synthetic but realistic data.
- **Tests**:
  - **Analytics/Validation**: Manual or scripted inspection of audit logs and exported reports.

### TCG-14 – Content Governance Traceability & Readiness Summary
- **Description**: Build a traceability matrix mapping `CG‑*`, `R‑CONT‑*`, and relevant `R‑SYS‑*` requirements to implementations and tests, plus a readiness summary for `GAME-READINESS-ASSESSMENT.md`.
- **Dependencies**: Completion of core content governance tasks, Master Test Registry.
- **Acceptance Criteria**:
  - All content governance requirements are mapped to at least one implementation and one test, or explicitly marked as planned/deferred.
  - Readiness summary clearly states implementation status, risks, and open design questions (e.g., category semantics still to be finalized).
  - Peer review (external model) confirms the matrix and summary are accurate and sufficiently complete.
- **Tests**:
  - **Analytics/Validation**: Peer review against requirements and solutions docs; gaps documented and fed back into future task lists.



