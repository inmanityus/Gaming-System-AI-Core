```markdown
# ETHELRED – 4D Vision QA Solutions Architecture

**Date**: 2025-11-14  
**Version**: 0.2.0 (Phase 3 – Solutions, peer‑reviewed draft)  
**Status**: Draft – incorporates first‑round feedback (GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5)  

---

## 0. Purpose, Scope, and Traceability

- **S‑4D‑PURPOSE‑001**  
  This document defines the **implementation‑aware architecture** for the 4D Vision QA domain of Ethelred, translating requirements from  
  `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §2 and system‑wide requirements §1 into concrete services, data flows, and contracts.

- **S‑4D‑SCOPE‑001**  
  Scope includes:
  - ingestion of multi‑camera RGB+depth streams and metadata from UE5 and test harnesses,  
  - construction and storage of 4D analysis segments (video + depth + time + gameplay events),  
  - analysis pipeline for the 6 detection areas in **R‑4D‑DET‑001…006**,  
  - emission of `VISION.ISSUE` and scene‑level summary events required by **R‑4D‑OUT‑001…003**,  
  - integration with the Ethelred Coordinator, Guardrails Monitor, Red Alert / media storage, and observability systems.

- **S‑4D‑OUT‑OF‑SCOPE‑001**  
  This document does **not**:
  - choose specific model architectures (e.g., CNN vs transformer) or libraries,  
  - define UE5 blueprint implementation details or editor tooling,  
  - prescribe specific deployment topologies (ECS task counts, instance types).

- **S‑4D‑TRACE‑001 (Traceability Approach)**  
  Detailed one‑to‑many mappings from each requirement ID (`R‑4D‑*`, relevant `R‑SYS‑*`) to services, events, schemas, and tests will be maintained in a companion traceability matrix (Phase 3.1). This solutions document defines the architectural **targets** that matrix will reference.

All design choices below must be traceable back to requirement IDs in the v2 requirements document and verifiable via the traceability matrix.

---

## 1. High‑Level Component Decomposition

### 1.1 Domain Services

1. **4D Vision Ingest Service (`svc.ethelred.4d.ingest`)**  
   - Accepts **frame bundles** and **segment descriptors** from UE5 test runs and automation.  
   - Normalizes metadata per **R‑4D‑IN‑001…003** (camera IDs, timestamps, build IDs, events, performance markers).  
   - Writes raw media (RGB+depth) into **Red Alert / media storage** per **R‑SYS‑DATA‑004** and persists **segment records**.  
   - Publishes `VISION.ANALYZE_REQUEST` messages to the 4D Vision Analyzer queue.

2. **4D Vision Analyzer Service (`svc.ethelred.4d.analyzer`)**  
   - Consumes `VISION.ANALYZE_REQUEST` messages (segment references, not raw media).  
   - Orchestrates detector modules for:
     - animation & rigging (**R‑4D‑DET‑001**),  
     - physics & collisions (**R‑4D‑DET‑002**),  
     - rendering artifacts (**R‑4D‑DET‑003**),  
     - lighting & horror atmosphere (**R‑4D‑DET‑004**),  
     - performance & frame pacing (**R‑4D‑DET‑005**),  
     - gameplay flow & soft‑locks (**R‑4D‑DET‑006**).  
   - Emits `VISION.ISSUE` and `VISION.SCENE_SUMMARY` events (section 3) in the **canonical envelope** required by **R‑SYS‑OBS‑001**.  
   - Pushes explainability details (signals + thresholds) required by **R‑SYS‑SAFE‑004**.

3. **4D Coverage & Trend Job (`svc.ethelred.4d.coverage-job`)**  
   - Batch/periodic job (e.g., per build or nightly) that computes coverage and trend metrics from stored segments + issues:  
     - fraction of horror scenes covered by 4D analysis (**R‑4D‑OUT‑003**),  
     - counts and distributions of issues per level/scene,  
     - regressions vs previous builds (scenes becoming worse over time).  
   - Emits `VISION.COVERAGE` and `VISION.TRENDS` events for Red Alert dashboards and Ethelred Coordinator aggregation.

4. **Ethelred Coordinator (`svc.ethelred.coordinator`) – 4D View**  
   - Already defined at system level (**R‑SYS‑ARCH‑002**), but here we clarify its 4D responsibilities:  
     - subscribes to `VISION.ISSUE`, `VISION.SCENE_SUMMARY`, and `VISION.COVERAGE` subjects,  
     - correlates 4D results with other domains (audio, content, story) via `trace_id` and `session_id`,  
     - forwards enforcement‑relevant summaries (not raw media) to **Guardrails Monitor** when content levels are implicated,  
     - feeds Red Alert report generation for 4D sections.

### 1.2 UE5 & Test Harness Integration (Conceptual)

- **UE5 Instrumentation Layer**  
  - Exposes configuration for:
    - which cameras participate in 4D capture (player POV, debug, test cameras),  
    - sampling mode (**frame‑level**, **window‑based**, **event‑based**) per **R‑4D‑IN‑003**,  
    - tagging of key gameplay events (damage, deaths, scares, boss fights).  
  - Streams encoded frames + depth + metadata to an **AI Testing Gateway** (existing Red Alert ingest or a dedicated 4D ingest endpoint).

- **AI Testing / Capture Gateway (`ai-testing-system`)**  
  - Receives 4D capture streams over HTTP/gRPC/WebSocket.  
  - Handles:
    - formation of **segments** (e.g., 5–10s windows or event‑centered clips),  
    - storing raw media in media storage (S3/Red Alert) with stable URIs,  
    - forwarding segment descriptors to `svc.ethelred.4d.ingest`.  
  - This keeps **media handling** concerns in the existing testing infra, and Ethelred works primarily on references + metadata.

---

## 2. Data Flow & Sampling Strategy

### 2.1 Core Flow (Per Segment)

1. **Capture**  
   - UE5 instrumentation sends frames + depth + per‑frame metadata and annotated events to the AI Testing / Capture Gateway.  
   - Capture Gateway constructs a **segment**:  
     - time‑bounded sequence of frames,  
     - multi‑camera views,  
     - associated gameplay events and performance metrics.

2. **Media Storage & Segment Record Creation**  
   - Gateway writes video + depth bundles to media storage:  
     - e.g., `redalert://media/4d/{build_id}/{scene_id}/{segment_id}`.  
   - Gateway posts a `VISION.SEGMENT_CREATED` message (or HTTP request) to `svc.ethelred.4d.ingest` containing only metadata + media references.

3. **4D Vision Ingest**  
   - Validates and normalizes segment metadata:  
     - ensures `build_id`, `scene_id`, `timestamp_range`, `camera_ids[]`, `sampling_mode`, `event_tags[]`, `performance_stats[]` are present (**R‑4D‑IN‑002**).  
   - Persists a **segment record** in Ethelred’s database (schema in §4).  
   - Publishes a `VISION.ANALYZE_REQUEST` NATS message to the 4D Vision Analyzer queue with reference IDs, not media bytes.

4. **4D Vision Analysis**  
   - Analyzer service pulls the segment’s media from Red Alert storage using the references.  
   - Runs the detection pipeline (animation, physics, rendering, lighting, performance, flow) in a configurable order, potentially in parallel.  
   - Handles **ambiguous or degraded inputs** explicitly:  
     - if cameras are occluded or depth is missing for a significant portion of the segment, the analyzer marks issues as `data_quality` with lowered confidence,  
     - if analysis cannot be trusted, the analyzer emits a `VISION.ISSUE` record with `issue_category = "data_quality"` and `severity = "warning"` instead of silently failing,  
     - all such cases are surfaced in Red Alert so human QA can confirm or override.
   - Collects detector outputs and merges overlapping findings into normalized `VISION.ISSUE` events and a single `VISION.SCENE_SUMMARY` for the segment.

5. **Issue & Summary Emission**  
   - Analyzer emits events on NATS using canonical envelope:  
     - `events.ethelred.4d.v1.issue` (for `VISION.ISSUE` records),  
     - `events.ethelred.4d.v1.scene_summary` (scene‑level quality metrics),  
     - optional `events.ethelred.4d.v1.debug` for internal QA only.  
   - Ethelred Coordinator ingests these events; Red Alert subscribes for building QA dashboards and reports.

6. **Coverage & Trend Computation**  
   - Coverage job periodically scans segment and issue tables per `build_id`:  
     - computes coverage metrics and trends,  
     - emits `events.ethelred.4d.v1.coverage` and `events.ethelred.4d.v1.trends`.  
   - These feed long‑term analysis in Red Alert and in game readiness assessments.

### 2.2 Sampling Modes in Practice

The **sampling strategy** must be configurable per environment (dev/QA/staging) and scenario, satisfying **R‑4D‑IN‑003**:

- **Frame‑Level Sampling (Dev/QA Only)**  
  - UE5 sends continuous frame streams for selected cameras.  
  - Capture Gateway buffers frames into rolling windows (e.g., 2–5s) to form segments; analysis is offline or near‑real‑time depending on resource budgets.  
  - Used primarily for low‑level rendering/animation debugging.

- **Window‑Based Sampling**  
  - UE5 instrumentation periodically requests segments (e.g., every N seconds or gameplay milestones).  
  - Gateway forms fixed‑length windows (e.g., 5–10s); each becomes a segment.  
  - Suitable for broad coverage across levels.

- **Event‑Based Sampling**  
  - UE5 annotates key events: scare triggers, boss introductions, player deaths, major story beats.  
  - Capture Gateway records pre/post windows around these events (e.g., 3s before, 7s after) and forms segments.  
  - Prioritized for high‑stakes horror scenes and soft‑lock detection.

Sampling configuration (camera sets, intervals, event triggers) is managed via Settings / Content Level configs and exposed to UE5 through existing configuration channels, maintaining consistency with content governance and environment profiles.

---

## 3. Event Contracts & NATS Subjects

### 3.1 Canonical Envelope

All 4D Vision events MUST embed the **canonical envelope** from **R‑SYS‑OBS‑001**:

```jsonc
{
  "trace_id": "uuid",
  "session_id": "sess-123",
  "player_id": "pseudonymous-player-id?",
  "build_id": "build-2025-11-14",
  "timestamp_range": { "start": "...", "end": "..." },
  "domain": "4D",
  "issue_type": "VISION.ISSUE | VISION.SCENE_SUMMARY | VISION.COVERAGE | VISION.TRENDS",
  "severity": "info | warning | error | critical",
  "confidence": 0.0,
  "evidence_refs": ["redalert://media/4d/..."],
  "goal_tags": ["G-IMMERSION", "G-HORROR"]
}
```

The **payload** fields below are embedded under a `payload` object.

### 3.2 NATS Subjects

Proposed subjects (aligned with existing patterns in `NATS-SYSTEM-ARCHITECTURE.md`):

- Requests:
  - `svc.ethelred.4d.v1.analyze_segment` – queue‑group subject consumed by `svc.ethelred.4d.analyzer`.  
  - `svc.ethelred.4d.v1.describe_segment` – optional, returns stored metadata for a segment (no re‑analysis).

- Events:
  - `events.ethelred.4d.v1.issue` – emitted per detected issue (`VISION.ISSUE`).  
  - `events.ethelred.4d.v1.scene_summary` – per segment/scene summary metrics.  
  - `events.ethelred.4d.v1.coverage` – per build coverage metrics.  
  - `events.ethelred.4d.v1.trends` – regression/improvement trends over multiple builds.

These subjects are integrated with Ethelred Coordinator’s subscriptions and Red Alert consumers.

### 3.3 `VISION.ISSUE` Payload

Satisfying **R‑4D‑OUT‑001**:

```jsonc
{
  "issue_id": "uuid",
  "segment_id": "seg-123",
  "scene_id": "scene-bridge-01",
  "cameras": ["player_pov", "debug_topdown"],
  "issue_category": "animation | physics | rendering | lighting | performance | flow",
  "issue_subtype": "FOOT_SLIDE | BODY_CLIP | Z_FIGHT | DARK_TOO_BRIGHT | FPS_DROPS | SOFT_LOCK | ...",
  "severity": "low | medium | high | critical",
  "confidence": 0.0,
  "time_range": { "start_frame": 120, "end_frame": 210 },
  "entities": {
    "player_id": "pseudonymous-player-id?",
    "npc_ids": ["npc-132", "npc-244"],
    "actor_ids": ["BP_Player", "BP_ZombieBoss"]
  },
  "performance_context": {
    "avg_fps": 45.0,
    "min_fps": 24.0,
    "max_frame_time_ms": 60.0
  },
  "explainability": {
    "signals": ["joint_angle_deviation", "frame_time_spike"],
    "thresholds": { "joint_angle_deviation": 0.35, "frame_time_spike_ms": 30.0 },
    "notes": "Detected repeated foot sliding over 2.5s; correlated with frame‑time spikes."
  }
}
```

### 3.4 `VISION.SCENE_SUMMARY` Payload

Satisfying **R‑4D‑OUT‑002**:

```jsonc
{
  "summary_id": "uuid",
  "segment_id": "seg-123",
  "scene_id": "scene-bridge-01",
  "scores": {
    "animation": 0.85,
    "physics": 0.92,
    "rendering": 0.88,
    "lighting": 0.70,
    "performance": 0.60,
    "flow": 0.75
  },
  "summary_text": "Lighting slightly too bright for horror intent; minor perf hitches near bridge collapse.",
  "issue_counts": {
    "animation": 1,
    "physics": 0,
    "rendering": 1,
    "lighting": 2,
    "performance": 3,
    "flow": 1
  }
}
```

### 3.5 Coverage & Trend Payloads

Satisfying **R‑4D‑OUT‑003**:

```jsonc
{
  "build_id": "build-2025-11-14",
  "scene_coverage": [
    { "scene_id": "scene-bridge-01", "coverage_fraction": 0.85 },
    { "scene_id": "scene-hospital-02", "coverage_fraction": 0.40 }
  ],
  "issue_density": [
    { "scene_id": "scene-bridge-01", "issues_per_minute": 1.2 },
    { "scene_id": "scene-hospital-02", "issues_per_minute": 0.3 }
  ],
  "goal_tags": ["G-IMMERSION", "G-HORROR"]
}
```

Trends events add comparisons vs previous builds:

```jsonc
{
  "build_id": "build-2025-11-14",
  "comparison_build_id": "build-2025-11-07",
  "regressions": [
    { "scene_id": "scene-bridge-01", "metric": "lighting", "delta": -0.10 },
    { "scene_id": "scene-bridge-01", "metric": "performance", "delta": -0.15 }
  ],
  "improvements": [
    { "scene_id": "scene-hospital-02", "metric": "animation", "delta": 0.08 }
  ]
}
```

---

## 4. Storage & Schema Concepts

Ethelred’s internal storage for 4D Vision SHOULD be relational (PostgreSQL) with optional time‑series extensions, but the key is **schema shape**, not technology.

### 4.1 `vision_segments` Table (Conceptual)

- `segment_id` (PK, UUID)  
- `build_id`  
- `scene_id`  
- `timestamp_start`, `timestamp_end`  
- `camera_ids` (array)  
- `sampling_mode` (`frame`, `window`, `event`)  
- `event_tags` (array, e.g., `["boss_intro", "player_death"]`)  
- `media_uri_rgb` (string)  
- `media_uri_depth` (string or structured field)  
- `performance_snapshot` (JSONB: avg/min/max FPS, frame times)  
- `created_at`, `updated_at`

### 4.2 `vision_issues` Table (Conceptual)

- `issue_id` (PK, UUID)  
- `segment_id` (FK → `vision_segments`)  
- `scene_id`  
- `issue_category`, `issue_subtype`  
- `severity`, `confidence`  
- `time_start_frame`, `time_end_frame`  
- `npc_ids` (array), `actor_ids` (array)  
- `performance_context` (JSONB)  
- `explainability` (JSONB)  
- `goal_tags` (array)  
- `created_at`

### 4.3 `vision_scene_summaries` Table (Conceptual)

- `summary_id` (PK, UUID)  
- `segment_id` (FK)  
- `scene_id`  
- `scores` (JSONB) – per‑dimension quality scores  
- `issue_counts` (JSONB)  
- `summary_text` (text)  
- `created_at`

Coverage and trend metrics can either be materialized into `vision_build_metrics` tables or computed on demand from these base tables, depending on performance requirements.

### 4.4 Versioning & Compatibility (Conceptual)

- Every persisted record MUST include:
  - `schema_version` (for the event/payload shape),  
  - `model_version` (for core 4D detectors),  
  - `config_version` (for thresholds and sampling policies).  
- Analyzer and coverage jobs MUST remain **backward‑compatible** with at least N previous schema versions when reading historical data.  
- Any breaking change to event or table schemas MUST be accompanied by:
  - migration scripts for existing records,  
  - updates to the traceability matrix and test suites,  
  - clearly documented version compatibility expectations in release notes.

---

## 5. SLAs, Performance, and Failure Modes

### 5.1 Latency & Throughput (Targets)

Given the heavy nature of 4D analysis, latency targets must differentiate **offline build analysis** from any near‑real‑time usage:

- **Offline Build Validation (Primary)**  
  - Target: process a 10s segment within **≤ 60 seconds** at typical resolution and camera count.  
  - Build‑level coverage jobs may run over several minutes but should complete within CI budgets.

- **Interactive QA Sessions (Optional)**  
  - For short segments (≤ 3s), aim for **≤ 10–15 seconds** end‑to‑end from capture to issue display in Red Alert.  
  - This supports iterative debugging without requiring real‑time guarantees.

These SLAs MUST be exposed as metrics (`analysis_latency_seconds`, `segments_processed_per_minute`) per **R‑SYS‑OBS‑002**.

### 5.2 Graceful Degradation

Per **R‑SYS‑SAFE‑002**:

- If `svc.ethelred.4d.analyzer` is unavailable or overloaded:
  - Coordinator marks the 4D domain as `degraded` in its own health outputs.  
  - A `SYS.HEALTH` event is emitted instead of mis‑labelling game bugs.  
  - UE5 and Guardrails rely on conservative defaults (e.g., assuming unknown 4D quality but **not** disabling safety).

- If media storage is unavailable:
  - Ingest service may still accept **metadata‑only** segments, flagging them as `media_missing`.  
  - Analyzer can skip these with explicit `VISION.ISSUE` events noting “analysis unavailable – media missing”.

In addition, Ethelred Coordinator SHOULD monitor **false‑positive rates** and sustained anomaly spikes from the 4D domain. If a detector configuration causes widespread, low‑confidence issues (e.g., after a model change), operators can:
- temporarily downgrade 4D findings to advisory severity in Red Alert,  
- roll back to a previous `model_version` / `config_version`,  
- or disable specific detectors via feature flags while keeping the rest of the pipeline active.

### 5.3 Kill Switches & Configuration

Per **R‑SYS‑SAFE‑003**:

- 4D Vision analysis can be disabled via:
  - feature flags in Settings / Model Management,  
  - environment variables passed to services.  
- When disabled:
  - Ingest service may bypass analysis and only record coverage placeholders,  
  - Coordinator clearly marks 4D status as `disabled` in Red Alert and admin dashboards.

---

## 6. Integration Points

### 6.1 Guardrails Monitor

- 4D Vision does **not** directly enforce player actions or content (per **R‑SYS‑ARCH‑003**).  
- It passes evidence to Guardrails Monitor only when:
  - issues involve content that might violate content levels (e.g., excessive gore visibility due to lighting changes),  
  - or repeated soft‑locks threaten player experience in ways that relate to addiction/compulsion loops.  
- Signals are provided as structured fields; Guardrails remains the enforcement authority.  
- The 4D pipeline itself MUST respect global data rules: pseudonymous IDs only (**R‑SYS‑DATA‑001**), explicit `actor_type` flags for AI vs real players (**R‑SYS‑DATA‑002**), and retention/erasure policies matching environment configuration (**R‑SYS‑DATA‑003**).

### 6.2 Content Level Manager & Settings

- Content Level Manager defines what is acceptable in terms of:
  - gore visibility,  
  - horror intensity,  
  - frequency of disturbing scenes.  
- 4D Vision uses content profiles to:
  - adjust thresholds for what counts as “too bright/dim” or “too explicit”,  
  - decide which scenes require mandatory 4D coverage (e.g., boss fights, ritual scenes).

### 6.3 Story Teller & Story Memory

- 4D Vision events reference `scene_id` and `experience_id` so that:
  - Story Memory System can attach visual quality metadata to story arcs,  
  - Red Alert can highlight when key arcs are visually broken (e.g., horror scenes not selling fear).

### 6.4 Multimodal Consistency (Vision + Audio)

- Ethelred Coordinator SHOULD support **joined views** where 4D Vision and Audio QA events share `trace_id`, `scene_id`, and `timestamp_range`, enabling:  
  - detection of multimodal regressions (e.g., visually terrifying but sonically flat scenes),  
  - correlation of audio intelligibility failures with visual occlusions or camera motion,  
  - future multimodal tests that check consistency between what is seen and what is heard in key horror moments.

---

## 7. Open Questions & Next Steps

- **Q‑4D‑001**: Exact encoding and transport format for RGB+depth segments (video container + depth channel vs separate streams) – to be decided during implementation, constrained only by media storage and UE5 capabilities.
- **Q‑4D‑002**: Thresholds and scales for per‑dimension scores (0–1 vs 0–100) – must align with Red Alert UI conventions.  
- **Q‑4D‑003**: Degree of near‑real‑time usage vs strictly offline operation – will affect hardware sizing and batching strategies.  
- **Q‑4D‑004**: Whether to split detectors into separate microservices vs in‑process modules – depends on model/runtime choices and deployment complexity.

This document is intentionally technology‑agnostic while being precise enough to implement and test. It MUST be peer‑reviewed by GPT‑5.1 / GPT‑5.1‑Codex, Gemini 2.5 Pro, and Claude Sonnet 4.5 before Phase 4 task breakdown.
```


