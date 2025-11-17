# ETHELRED – Multi-Language Experience Phase 4 Task Breakdown

**Domain**: Multi-Language Experience (Localization & Language System)  
**Source Requirements**: `MULTI-LANGUAGE-EXPANSION-REQUIREMENTS.md` + system-wide §1  
**Source Solutions**: `docs/solutions/ETHELRED-MULTI-LANGUAGE-SOLUTIONS.md`  

All tasks require **peer coding**, **pairwise testing**, and real test runs, ensuring parity of horror tone and content policy alignment across languages.

---

## Milestone 1 – Localization Store & APIs (`svc.localization`)

### TML-01 – Implement Localization Core Schema & Migrations
- **Description**: Implement migrations for `localization_entries`, `language_preferences`, `localization_coverage`, and `localization_issues` tables as outlined in requirements and solutions docs.
- **Dependencies**: DB migration tooling, `MULTI-LANGUAGE-EXPANSION-REQUIREMENTS.md` §2, §5–6.
- **Acceptance Criteria**:
  - `localization_entries` stores `key`, `language_code`, `text`, `category`, `context`, `description`, `tags[]`, version/audit fields.
  - `language_preferences`, `localization_coverage`, and `localization_issues` schemas support required queries and metrics (by language, category, build).
  - Migrations apply/rollback cleanly and accept seeded sample data.
- **Tests**:
  - **Unit**: Migration tests on disposable DBs.
  - **Integration**: Repository tests for reading/writing localization entries and preferences.

### TML-02 – Implement Localization Service (`svc.localization`) APIs
- **Description**: Implement lookup, bulk export/import, and validation APIs/NATS subjects for the localization store.
- **Dependencies**: TML-01, existing service scaffolding patterns.
- **Acceptance Criteria**:
  - APIs exist to retrieve strings by `key` + `language_code`, export sets for translation, and import translations with validation.
  - Validation detects missing strings, placeholder mismatches, and malformed plural/gender templates.
  - API contracts are documented with examples and error conditions.
- **Tests**:
  - **Unit**: Handler-level tests for lookup, export, import, and validation logic.
  - **Integration**: End-to-end tests for a small set of strings through export → modify → import → validation cycle.

---

## Milestone 2 – Language System & TTS (`svc.language_system`)

### TML-03 – Implement Text Localization Gateway
- **Description**: Implement the Language System text localization gateway that fronts `svc.localization`, applies preference-based resolution, and handles explicit fallbacks.
- **Dependencies**: TML-02, Settings service for language preferences.
- **Acceptance Criteria**:
  - Gateway can serve localized strings for UI, narrative, and system text for Tier-1 languages.
  - Fallback behavior (e.g., missing localized string → default language) is explicit and logged.
  - Gateway is accessible from UE5, Story Teller, and backend services via consistent APIs/NATS subjects.
- **Tests**:
  - **Unit**: Preference resolution and fallback tests.
  - **Integration**: Tests from a calling service (e.g., Story Teller or UI) through Language System to localization store.

### TML-04 – Implement TTS & Voice Configuration Manager
- **Description**: Implement TTS interface and per-language voice configuration management as described in the solutions doc (`ML‑3.2.*`).
- **Dependencies**: TML-03, chosen TTS backend(s), archetype/character voice definitions.
- **Acceptance Criteria**:
  - TTS interface accepts `text`, `language_code`, `speaker_id`/`archetype_id`, emotion tags, and returns audio plus duration metadata.
  - Voice configurations exist for key characters/archetypes in at least one non-English language.
  - Mode selection (recorded vs TTS vs mixed) is tracked per line.
- **Tests**:
  - **Unit**: Tests for configuration resolution and request building.
  - **Integration**: Tests against a TTS backend (or controlled stub) verifying request/response flow and metadata correctness.

### TML-05 – Implement Timing & Lip-Sync Bridge
- **Description**: Implement timing metadata generation/propagation (line duration, optional phoneme timings) and subtitle alignment functions (`ML‑3.3.*`).
- **Dependencies**: TML-04, UE5 integration for lip-sync and subtitles, Audio QA domain.
- **Acceptance Criteria**:
  - For voiced lines, timing metadata is produced and accessible to UE5 and Ethelred.
  - Subtitle timecodes are derived from or validated against the same timing data; misalignments beyond thresholds can be detected.
  - Timing APIs are documented and stable for UE5 integration.
- **Tests**:
  - **Unit**: Timing metadata construction and alignment tests.
  - **Integration**: Tests verifying subtitle/audio alignment on a small set of sample lines per language.

---

## Milestone 3 – Preferences, Session Snapshots & QA

### TML-06 – Implement Player Language Preferences Management
- **Description**: Extend Settings service to store `ui_language`, `subtitle_language`, and `voice_language` per player and expose APIs for managing them.
- **Dependencies**: TML-01, existing Settings service, Auth/identity.
- **Acceptance Criteria**:
  - Preferences can be created/updated/read for test players via APIs/NATS subjects.
  - Constraints around allowed combinations (e.g., fallback options) are documented and enforced.
  - Preferences are synced with any existing profile/region settings as needed.
- **Tests**:
  - **Unit**: Preference storage and validation tests.
  - **Integration**: API tests verifying preference changes and retrieval for authenticated players.

### TML-07 – Implement Session Language Snapshot Flow
- **Description**: Implement computation of effective language configuration at session start and emission of `settings.language.session_started` events with session-level snapshots.
- **Dependencies**: TML-06, NATS infrastructure, ETHELRED-MULTI-LANGUAGE-SOLUTIONS.
- **Acceptance Criteria**:
  - On session start, snapshot with effective UI/subtitle/voice languages is written and emitted on NATS.
  - Language System, Story Teller, UE5, and Ethelred can subscribe to the snapshots and see consistent configuration for test sessions.
  - Idempotency and error handling (e.g., missing preferences) are defined and implemented.
- **Tests**:
  - **Unit**: Snapshot computation tests for different preference scenarios.
  - **Integration**: End-to-end tests from session start to snapshot consumption by at least one downstream service.

### TML-08 – Implement UI Snapshot Testing for Tier-1 Languages
- **Description**: Implement automated UI snapshot tests per Tier-1 language to detect text overflow, missing glyphs, and layout issues (`ML‑5.1`).
- **Dependencies**: TML-03, UI build pipeline, testing harness (e.g., Playwright or engine-specific tooling).
- **Acceptance Criteria**:
  - Snapshot generation runs as part of CI or a dedicated pipeline for each Tier-1 language.
  - Failures (overflow, glyph issues) are logged with references to language, screen, and localization keys.
  - At least one example snapshot run exists with documented failures fixed.
- **Tests**:
  - **E2E**: Snapshot test pipeline that renders key UI views in multiple languages and checks for layout violations.

### TML-09 – Implement Narrative & Audio QA Flows per Language
- **Description**: Implement scripted or AI Player narrative playthroughs and audio QA checks per language as described in `ML‑5.2–5.3`.
- **Dependencies**: TML-04–05, AI Testing System, Story Teller integration, Audio QA domain.
- **Acceptance Criteria**:
  - For at least one scene per Tier-1 language, QA flows verify comprehension of key beats, horror tone parity, and audio/subtitle synchronization.
  - Issues are recorded in `localization_issues` with references to `line_id`, `language_code`, and asset IDs.
  - Runbooks exist for extending QA to additional scenes/languages.
- **Tests**:
  - **Integration/E2E**: Playthrough tests (human or AI Player) with automated checks where possible and documented manual checks.

---

## Milestone 4 – Metrics, Ethelred Integration & Readiness

### TML-10 – Implement Localization Coverage & Quality Metrics
- **Description**: Compute and expose coverage and quality metrics per build/language/category as required by `ML‑6.*`.
- **Dependencies**: TML-01–02, Master Test Registry, observability stack.
- **Acceptance Criteria**:
  - Metrics include localization coverage ratio, fallback counts, issue counts, and TTS latency per language.
  - `events.localization.v1.coverage` and `events.localization.v1.issues` are emitted and consumed by Ethelred localization QA view.
  - Dashboards present coverage and issue trends per language and build.
- **Tests**:
  - **Unit**: Metric aggregation logic tests.
  - **Integration**: End-to-end metrics pipeline tests with seeded data and dashboard checks.

### TML-11 – Integrate Localization Signals with Ethelred & Content Governance
- **Description**: Integrate localization coverage/issue and audio sync signals with Ethelred and Content Governance for parity and policy checks (`ML‑7.*`).
- **Dependencies**: TML-07–10, Content Governance domain, Ethelred Coordinator.
- **Acceptance Criteria**:
  - Ethelred can correlate localization issues with engagement, content violations, and story drift via shared IDs.
  - Content Governance checks verify that localized content respects the same content level policies as canonical content.
  - At least one scenario demonstrates detection of mislocalized horror intensity (too weak/strong) in a specific language.
- **Tests**:
  - **Integration/E2E**: Pipeline tests from localization events through Ethelred and Content Governance checks.

### TML-12 – Multi-Language Traceability & Readiness Summary
- **Description**: Build a traceability matrix mapping `ML‑*` requirements to implementations and tests, plus a readiness summary for `GAME-READINESS-ASSESSMENT.md`.
- **Dependencies**: Completion of TML-01–11, Master Test Registry.
- **Acceptance Criteria**:
  - Each multi-language requirement is linked to at least one implementation and test, or explicitly marked as deferred with rationale.
  - Readiness summary identifies current language coverage, parity status, and open risks (e.g., missing RTL support).
  - Peer review (external model) confirms adequacy and completeness.
- **Tests**:
  - **Analytics/Validation**: Peer review and cross-checking against requirements and solutions docs.




