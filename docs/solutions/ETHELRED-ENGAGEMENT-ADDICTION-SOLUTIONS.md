```markdown
# ETHELRED – Emotional Engagement & Addiction Analytics Solutions Architecture

**Date**: 2025-11-14  
**Version**: 0.1.0 (Phase 3 – Solutions draft)  
**Status**: Draft – requires peer review (GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5)  

---

## 0. Purpose, Scope, and Traceability

- **S‑EMO‑PURPOSE‑001**  
  Define the implementation‑aware architecture for Ethelred’s **Emotional Engagement & Addiction Analytics** domain, translating requirements from  
  `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §4 and system‑wide requirements §1.

- **S‑EMO‑SCOPE‑001**  
  Scope includes:
  - telemetry capture for NPC interactions, moral choices, and session behavior (**R‑EMO‑DATA‑001…003**),  
  - computation of NPC attachment, moral tension, and engagement profiles (**R‑EMO‑MET‑001…003**),  
  - cohort‑level addiction‑risk indicators with strict non‑predatory constraints (**R‑EMO‑ADD‑001…003**, **R‑SYS‑SAFE‑001**),  
  - reporting and feedback to Story Teller, design, and production via slow‑changing parameters (**R‑EMO‑FB‑001…002**).

- **S‑EMO‑OUT‑OF‑SCOPE‑001**  
  Out of scope:
  - any real‑time personalization of stories to maximize individual engagement or play time,  
  - low‑level instrumentation code inside UE5 or AI Player simulators,  
  - exact statistical/ML techniques used to derive profiles (only their observable inputs/outputs).

- **S‑EMO‑TRACE‑001 (Traceability Approach)**  
  A separate traceability matrix will map each `R‑EMO‑*` and relevant `R‑SYS‑*` requirement to the services, schemas, and tests defined here.

---

## 1. High‑Level Component Decomposition

### 1.1 Domain Services

1. **Engagement Telemetry Service (`svc.ethelred.emo.telemetry`)**  
   - Ingests **player and AI Player** telemetry events from UE5 and backend services:
     - NPC interaction events,  
     - moral choice events,  
     - session start/end and session cadence,  
     - AI Player run metadata (personality archetypes).  
   - Normalizes and enriches events with canonical identifiers (`npc_id`, `arc_id`, `experience_id`).  
   - Writes normalized telemetry records to a durable store and publishes compact events for analytics.

2. **Engagement Analytics Service (`svc.ethelred.emo.analytics`)**  
   - Consumes normalized telemetry streams and batch windows.  
   - Computes:
     - NPC Attachment Index (**R‑EMO‑MET‑001**),  
     - Moral Tension Index (**R‑EMO‑MET‑002**),  
     - non‑identifying engagement profiles (**R‑EMO‑MET‑003**).  
   - Emits `ENGAGEMENT.METRICS` events and persists aggregated metrics for cohorts and scenarios.

3. **Addiction Risk Analytics Job (`svc.ethelred.emo.addiction-job`)**  
   - Scheduled batch job (e.g., daily or per build) that analyzes cohort‑level patterns:
     - session duration distributions, time‑of‑day patterns, “one more run” loops (**R‑EMO‑ADD‑001**).  
   - Produces **aggregated, non‑personal** risk indicators only, honoring:
     - no per‑player optimization,  
     - no real‑time content manipulation based on addiction signals (**R‑EMO‑ADD‑002…003**, **R‑SYS‑SAFE‑001**).  
   - Emits `ENGAGEMENT.ADDICTION_RISK` reports for design/production review.

4. **Ethelred Coordinator – Engagement View (`svc.ethelred.coordinator`)**  
   - Subscribes to engagement and addiction risk events.  
   - Correlates emotional metrics with other domains:
     - story drift, content violations, 4D Vision issues, audio quality.  
   - Surfaces combined findings to **Red Alert** and long‑term dashboards; does **not** directly change runtime behavior.

5. **Design Feedback & Configuration Bridge (`svc.ethelred.emo.feedback`)**  
   - Consumes analytics outputs and generates **slow‑changing configuration suggestions** for Story Teller and design systems:
     - e.g., “NPC X arc under‑engaging”, “Moral choice Y is rarely taken”.  
   - Writes human‑readable reports and structured suggestion objects that must be reviewed and curated before any changes are applied.

---

## 2. Telemetry & Data Flow

### 2.1 Telemetry Inputs

Key telemetry types (conceptual):

- **NPC Interaction Events** (`telemetry.emo.npc_interaction`)  
  - `session_id`, `player_id?`, `npc_id`, `interaction_type` (`dialogue`, `gift`, `assist`, `harm`),  
  - `choice_id?`, `choice_label`, `help_harm_flag`,  
  - `timestamp`, `location_id`, `arc_id?`, `experience_id?`.

- **Moral Choice Events** (`telemetry.emo.moral_choice`)  
  - `session_id`, `player_id?`, `choice_id`, `arc_id`,  
  - `options` (ids/labels, tagged `safe`/`extreme`),  
  - `selected_option_id`,  
  - `decision_latency_ms`, `num_retries` (if allowed),  
  - `timestamp`.

- **Session Metrics Events** (`telemetry.emo.session_metrics`)  
  - `session_id`, `player_id?`, `actor_type` (`real_player`, `ai_player`),  
  - `session_start`, `session_end`,  
  - `time_of_day_bucket`, `day_of_week`,  
  - `total_duration_minutes`, `num_sessions_last_7_days`.

- **AI Player Run Metadata** (`telemetry.emo.ai_run`)  
  - `ai_run_id`, `personality_profile` (e.g., empathetic, ruthless),  
  - summary metrics for that run, for use as synthetic baseline (**R‑EMO‑DATA‑003**).

### 2.2 Processing Flow

1. **Ingestion & Normalization**  
   - UE5 and backend services publish raw telemetry events to NATS subjects such as `telemetry.raw.npc_interaction`.  
   - `svc.ethelred.emo.telemetry` subscribes, validates, and normalizes the events into canonical forms, storing them in a `engagement_events` table (conceptual) and republishing to `telemetry.emo.normalized.*`.

2. **Windowing & Aggregation**  
   - `svc.ethelred.emo.analytics` consumes normalized events, organizing them into:
     - per‑session windows,  
     - per‑NPC and per‑arc aggregates,  
     - per‑cohort aggregates (age region, platform, etc., without PII).  
   - Periodically computes engagement metrics and publishes `ENGAGEMENT.METRICS` events.

3. **Addiction Risk Computation**  
   - `svc.ethelred.emo.addiction-job` runs on a schedule, reading from aggregated tables and recent engagement metrics:  
     - computes cohort‑level indicators (no raw player identifiers),  
     - flags systems associated with unusual patterns (e.g., specific minigames or reward loops).  
   - Emits `ENGAGEMENT.ADDICTION_RISK` events and writes them to an `addiction_risk_reports` table.

4. **Coordinator Correlation & Reporting**  
   - Ethelred Coordinator correlates engagement metrics with other domains via shared `trace_id`, `session_id`, and `build_id`:  
     - e.g., low engagement in scenes with repeated 4D Vision issues, or high addiction indicators overlapping with certain content categories.  
   - Red Alert consumes coordinator outputs to render dashboards for emotional health and risk.

---

## 3. Event Contracts & NATS Subjects

### 3.1 Canonical Envelope

All engagement domain events adhere to the canonical envelope (`R‑SYS‑OBS‑001`), with `domain = "Engagement"`:

```jsonc
{
  "trace_id": "uuid",
  "session_id": "sess-123",
  "player_id": "pseudonymous-player-id?",
  "build_id": "build-2025-11-14",
  "timestamp_range": { "start": "...", "end": "..." },
  "domain": "Engagement",
  "issue_type": "ENGAGEMENT.METRICS | ENGAGEMENT.ADDICTION_RISK",
  "severity": "info | warning | critical",
  "confidence": 0.0,
  "evidence_refs": [],
  "goal_tags": ["G-IMMERSION", "G-LONGTERM"]
}
```

### 3.2 NATS Subjects

Proposed subjects:

- Telemetry (inputs):
  - `telemetry.raw.npc_interaction`, `telemetry.raw.moral_choice`, `telemetry.raw.session_metrics`, `telemetry.raw.ai_run`.  
  - `telemetry.emo.normalized.*` for normalized forms.

- Analytics (outputs):
  - `events.ethelred.emo.v1.engagement_metrics` – NPC attachment, moral tension, engagement profiles.  
  - `events.ethelred.emo.v1.addiction_risk` – cohort‑level addiction indicators (non‑identifying).

Payloads include:

- For `engagement_metrics`: per‑NPC and per‑arc attachment scores, moral tension indices, profile cluster assignments.  
- For `addiction_risk`: cohort identifiers, indicator values, and recommended review notes (no player IDs).

---

## 4. Storage & Schema Concepts

Conceptual tables (PostgreSQL or equivalent) with privacy constraints:

- `engagement_events`  
  - `event_id` (PK), `session_id`, `player_id?`, `actor_type`,  
  - `event_type` (`npc_interaction`, `moral_choice`, `session_metrics`, `ai_run`),  
  - typed columns for each event type (see §2.1),  
  - `timestamp`, `build_id`, `environment`.

- `engagement_aggregates`  
  - aggregates per `npc_id`, `arc_id`, `experience_id`, `cohort_id`,  
  - metrics: attachment indices, moral tension scores, engagement profile tags,  
  - `build_id`, `period_start`, `period_end`.

- `addiction_risk_reports`  
  - `report_id` (PK),  
  - `cohort_id` (e.g., region + age_band + platform),  
  - indicator values (e.g., avg daily time, night‑time play fraction),  
  - `risk_level` (`low`, `medium`, `high`),  
  - `notes`, `build_id`, `computed_at`.

Data retention and erasure MUST align with global rules (`R‑SYS‑DATA‑001…004`); player‑identifying data is minimized and pseudonymized.

---

## 5. SLAs, Safety, and Failure Modes

### 5.1 Latency & Throughput

- Telemetry ingestion:  
  - Target ≤ 10ms P95 from NATS receipt to normalized storage for typical events.  
  - Sufficient capacity for thousands of events per minute (depends on player base).

- Analytics and addiction jobs:  
  - Engagement metrics computation: near real‑time or short‑batch (e.g., every few minutes).  
  - Addiction risk jobs: daily or per build; allowed to run for minutes as offline analysis.

Metrics such as `engagement_events_ingested_total`, `engagement_metrics_compute_latency`, and `addiction_risk_job_duration` are exposed via `/metrics` endpoints.

### 5.2 Safety Constraints

Per **R‑SYS‑SAFE‑001** and **R‑EMO‑ADD‑002…003**:

- No per‑player or session‑level optimization loops may be constructed using engagement/addiction metrics.  
- Ethelred’s engagement domain produces:
  - aggregated, cohort‑level signals for design and ethics review,  
  - slow‑changing configuration recommendations that must be human‑approved.  
- Any attempt to wire these metrics into real‑time personalization MUST be blocked at architecture review.

### 5.3 Degradation Behavior

- If analytics services are unavailable:
  - Telemetry continues to be ingested and stored;  
  - Coordinator marks engagement domain as `degraded` and relies on existing metrics.  
- If data volume exceeds current capacity:
  - Downsampling and sampling strategies can be applied (e.g., analyze subsets of sessions) with explicit **sampling metadata** attached to reports.

---

## 6. Integration Points

### 6.1 Story Teller & Narrative Design

- Story Teller may consume **aggregated, non‑personal** engagement profiles at build time to:
  - adjust how often under‑served arcs are made available,  
  - re‑balance moral choice framing to increase meaningful tension.  
- Any such adjustments MUST:
  - be encoded in configuration, not per‑player logic,  
  - be validated by design/ethics teams before deployment.

### 6.2 Content Governance & Guardrails

- Content Governance can correlate:
  - content level profiles with engagement and moral tension,  
  - addiction indicators with specific content categories or features.  
- Guardrails Monitor may use addiction risk reports to:
  - recommend changes to systems that unintentionally drive unhealthy patterns,  
  - **never** to amplify or exploit such patterns.

### 6.3 Story Memory System

- Story Memory and engagement analytics are linked via:
  - `arc_id`, `experience_id`, `npc_id` and theme tags.  
- This allows:
  - per‑arc assessments of emotional connection,  
  - identification of arcs that underperform or drive undesirable behavior.

---

## 7. Open Questions & Next Steps

- **Q‑EMO‑001**: Exact cohort definitions (age bands, regions, platforms) and minimum sizes to preserve privacy.  
- **Q‑EMO‑002**: Which engagement profiles are most useful for design without risking covert personalization.  
- **Q‑EMO‑003**: How frequently to recompute engagement profiles and addiction indicators to balance responsiveness vs stability.  
- **Q‑EMO‑004**: Governance process for reviewing and approving changes driven by engagement analytics (ethics review board, sign‑offs, etc.).

This document intentionally remains vendor‑agnostic and focuses on architecture and contracts. It MUST be peer‑reviewed by GPT‑5.1 / GPT‑5.1‑Codex, Gemini 2.5 Pro, and Claude Sonnet 4.5 before Phase 4 task breakdown.
```


