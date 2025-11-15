```markdown
# ETHELRED – Content Governance & Content Level Solutions Architecture

**Date**: 2025-11-14  
**Version**: 0.1.0 (Phase 3 – Solutions draft)  
**Status**: Draft – requires peer review (GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5)  

---

## 0. Purpose, Scope, and Traceability

- **S‑CG‑PURPOSE‑001**  
  Define the implementation‑aware architecture for **Content Governance & Content Levels**, mapping requirements from  
  `CONTENT-GOVERNANCE-REQUIREMENTS.md` and `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §5 into concrete services, data flows, and contracts.

- **S‑CG‑SCOPE‑001**  
  Scope includes:
  - Content Level Manager module in Settings (profile registry, per‑player policy, per‑session snapshot),  
  - Ethelred Content Validator domain (multi‑modal classification & validation),  
  - integration with Guardrails Monitor, 4D Vision, Audio QA, Story Teller, and Language System,  
  - observability and auditing for content policies and violations.

- **S‑CG‑OUT‑OF‑SCOPE‑001**  
  Out of scope:
  - specific classifier models or vendors for text/vision/audio safety,  
  - age‑rating policy details (ESRB/PEGI mappings),  
  - UE5 rendering implementation specifics.

- **S‑CG‑TRACE‑001 (Traceability Approach)**  
  A companion matrix will link `CG‑*` and `R‑CONT‑*` requirements to the services, schemas, and tests described here.

---

## 1. High‑Level Component Decomposition

### 1.1 Content Level Manager (Settings Service)

1. **Content Profile Registry**  
   - Manages system default and custom profiles (`TeenSafe`, `MatureFullExperience`, regional variants).  
   - Stores per‑category allowed levels (violence, sexual content, language, horror, drugs, sensitive themes, moral complexity).  
   - Provides admin APIs for creation, update, and listing, per **CG‑3.2.1**.

2. **Per‑Player Content Policy Manager**  
   - Associates each player with an active base profile plus optional per‑category overrides (**CG‑3.2.2**).  
   - Exposes effective per‑player policies to internal callers via HTTP/NATS.

3. **Per‑Session Policy Snapshotter**  
   - On session start, computes a frozen **session content policy snapshot**:  
     - `session_id`, `player_id`, allowed levels per category, enabled/disabled themes, `policy_version` (**CG‑3.2.3**, **R‑CONT‑FLOW‑001**).  
   - Publishes the snapshot to downstream consumers (Guardrails, Ethelred, UE5, Story Teller, Language System).

### 1.2 Ethelred Content Validator

1. **Text Content Classifier (`svc.ethelred.content.text`)**  
   - Analyzes Story Teller outputs, NPC dialogue, UI text, item descriptions, etc. (**R‑CONT‑MOD‑001**).  
   - Assigns category/level scores per content category.

2. **Visual Content Classifier (`svc.ethelred.content.vision`)**  
   - Leverages 4D Vision QA outputs to derive per‑scene content labels (**R‑CONT‑MOD‑002**).  
   - Maps 4D Vision detections (gore, nudity, drug use) into the same category/level scale.

3. **Audio Content Classifier (`svc.ethelred.content.audio`)**  
   - Consumes Audio QA metrics and additional audio‑specific classifiers to detect profanity, slurs, disturbing soundscapes (**R‑CONT‑MOD‑003**).  
   - Produces category/level labels consistent with text and vision.

4. **Contextual Cross‑Checker (`svc.ethelred.content.context`)**  
   - Correlates text, vision, and audio labels to detect inconsistencies (**R‑CONT‑MOD‑004**):  
     - e.g., sanitized text but extreme visual gore.  
   - Produces unified content observations for a scene or line.

5. **Violation Engine & Logger (`svc.ethelred.content.violation`)**  
   - Compares observed category/levels with session content policy snapshots.  
   - Emits `CONTENT.VIOLATION` events and writes to the `content_violations` table (**CG‑3.3.4**, **R‑CONT‑VIOL‑001…003**).  
   - Provides evidence references (media URIs, text excerpts) for Red Alerts and Guardrails.

---

## 2. Policy & Validation Data Flow

### 2.1 Policy Flow

1. **Profile Creation & Management**  
   - Admins manage profiles via Settings service APIs: create/update/delete content profiles.  
   - Profiles stored in `content_levels` table with category levels, flags, and audit info (**CG‑3.3.1**).

2. **Per‑Player Policy**  
   - When a player selects or updates preferences, Settings updates `player_content_profiles` (**CG‑3.3.2**).  
   - Exposes `GET/PUT /players/{player_id}/content-policy` endpoints for UI and management tools (**CG‑4.1.2**).

3. **Session Snapshot**  
   - On session start, Settings computes effective per‑session policy and writes `session_content_policy` (**CG‑3.3.3**).  
   - Publishes `settings.content_policy.session_started` on NATS with snapshot and `policy_version` (**CG‑4.1.3**, **R‑CONT‑FLOW‑001**).

4. **Guardrails & Model Management**  
   - Guardrails Monitor subscribes to policy snapshots, caches them, and applies them in model filtering (**CG‑4.2.1**, **R‑CONT‑FLOW‑002**).  
   - Model Management uses these policies to configure generative models (Story Teller, Language System).

### 2.2 Runtime Content Validation by Ethelred

1. **Content Observation**  
   - As content is generated and rendered:
     - Text: captured from Story Teller outputs, UI text channels.  
     - Vision: 4D Vision QA emits scene issues & labels.  
     - Audio: Audio QA emits audio scores and categorizations.

2. **Domain‑Specific Classification**  
   - Each content classifier service maps observations into category/level scores.  
   - Outputs normalized `CONTENT.OBSERVATION` events with canonical envelope and per‑modality payload.

3. **Cross‑Modal Fusion**  
   - Contextual Cross‑Checker combines text, vision, and audio observations per scene/segment:  
     - resolves conflicts,  
     - flags suspicious mismatches (e.g., text implies mild horror but visuals are extreme).

4. **Policy Comparison & Violation Logging**  
   - Violation Engine fetches the session’s policy snapshot (cache) using `session_id` and `policy_version`.  
   - Compares observed vs allowed levels:
     - if observed ≤ allowed → no violation; metrics logged only.  
     - if observed > allowed → `CONTENT.VIOLATION` event emitted and row inserted into `content_violations`.  
   - For severe/repeated violations, Red Alerts are raised and Guardrails can request evidence.

5. **Real‑Time Behavior**  
   - Ethelred **does not** directly block gameplay; instead, per **R‑CONT‑VIOL‑002**:  
     - attempts substitution where lower‑intensity variants exist,  
     - otherwise logs and raises Red Alerts, deferring enforcement choices to Guardrails Monitor.

---

## 3. Event Contracts & NATS Subjects

### 3.1 Policy Events

- `settings.content_policy.session_started`  
  - Payload: `session_id`, `player_id`, `policy_snapshot` (per‑category levels, enabled themes), `policy_version`, `build_id`.  
  - Used by Guardrails, Ethelred Content Validator, UE5, Story Teller, Language System.

- `settings.content_policy.updated`  
  - Emitted when per‑player or profile policies change; triggers cache invalidation downstream.

### 3.2 Content Observation & Violation Events

- `events.ethelred.content.v1.observation.text`  
- `events.ethelred.content.v1.observation.vision`  
- `events.ethelred.content.v1.observation.audio`  
- `events.ethelred.content.v1.observation.fused` – cross‑modal view per scene/segment.  

Payload (simplified) under canonical envelope:

```jsonc
{
  "session_id": "sess-123",
  "scene_id": "scene-hospital-02",
  "content_ids": ["line-123", "asset-456"],
  "category_scores": {
    "violence_gore": 3,
    "horror_intensity": 4,
    "language_profanity": 1
  },
  "modality": "text | vision | audio | fused"
}
```

- `events.ethelred.content.v1.violation`  
  - Emitted when observed > allowed per category:

```jsonc
{
  "violation_id": "uuid",
  "session_id": "sess-123",
  "player_id": "pseudonymous-player-id?",
  "scene_id": "scene-hospital-02",
  "content_type": "story_output | npc_dialogue | visual_scene | audio_segment",
  "category": "violence_gore",
  "expected_level": 2,
  "observed_level": 4,
  "severity": "high",
  "detected_by": "ethelred_content_validator",
  "evidence_refs": ["redalert://media/4d/..."],
  "recommended_action": "substitute | log_only | review_required"
}
```

---

## 4. Storage & Schema Concepts

Conceptual tables (detailed shapes in `CONTENT-GOVERNANCE-REQUIREMENTS.md`):

- `content_levels` – profile registry (system defaults and custom profiles).  
- `player_content_profiles` – per‑player base profile and overrides.  
- `session_content_policy` – frozen session‑level policy snapshots with `policy_version`.  
- `content_violations` – detailed violation records with indices for category, severity, profile, and build.

Retention and erasure MUST respect global data rules (`R‑SYS‑DATA‑001…004`), and all content references use game‑internal IDs, not real‑world PII.

---

## 5. SLAs, Observability, and Governance

### 5.1 Performance Targets

- Content policy lookup:
  - From Ethelred or Guardrails caches: ≤ 5ms P95.  
  - Database lookups: ≤ 10ms P95 (with caching).

- Content observation classification:
  - Text: additional ≤ 10–30ms per chunk (depending on classifier).  
  - Vision: asynchronous, not on player hot path (leveraging 4D Vision outputs).  
  - Audio: asynchronous, leveraging Audio QA pipeline.

### 5.2 Observability

- Metrics:
  - `content_violation_count{category,profile,severity}`,  
  - `policy_snapshot_coverage`,  
  - `content_policy_lookup_latency`,  
  - modality‑specific classification latency.  
- Logs:
  - structured violation logs with correlation IDs and evidence references.  
- Dashboards reflecting:
  - violation rates per build and profile,  
  - drift in baseline intensity distributions,  
  - coverage of content annotations.

### 5.3 Governance & Audit

- All profile changes and policy overrides are audit‑logged (who/when/what) and traceable per **CG‑5.3**.  
- Violation data enables:
  - ESRB/PEGI/legal audits,  
  - design reviews of content intensity and regional variants.  
- Any change that materially alters content intensity or enforcement rules must go through a documented review process.

---

## 6. Integration with Other Domains

### 6.1 4D Vision & Audio QA

- 4D Vision and Audio Authentication services provide modality‑specific content labels that feed `svc.ethelred.content.vision` and `.audio`.  
- Integration ensures:
  - consistent category/level scales across text, vision, and audio,  
  - ability to detect multimodal inconsistencies (e.g., mild text but extreme visuals).

### 6.2 Story Memory & Engagement

- Story Memory tags arcs, quests, and Experiences with content themes; Content Governance can:
  - tie violations back to narrative structures,  
  - evaluate how content intensity interacts with engagement and moral tension metrics.

### 6.3 Guardrails Monitor

- Guardrails Monitor remains the **enforcement authority** per **R‑SYS‑ARCH‑003**:  
  - Ethelred validates and logs; Guardrails decides filter/block/escation behaviors.  
- Ethelred provides structured evidence so Guardrails can refine classifiers and thresholds.

---

## 7. Open Questions & Next Steps

- **Q‑CG‑001**: Finalize exact semantics of each category/level for design, art, and QA teams to use consistently.  
- **Q‑CG‑002**: Determine which violations should trigger automatic substitution vs log‑only vs escalation.  
- **Q‑CG‑003**: Define thresholds for build‑to‑build content intensity drift that require formal review.  
- **Q‑CG‑004**: Clarify how regional builds with different base policies interact with profile system (e.g., region‑locked presets).

This solutions architecture focuses on **WHAT with implementation awareness** and avoids vendor‑specifics. It MUST be peer‑reviewed by GPT‑5.1 / GPT‑5.1‑Codex, Gemini 2.5 Pro, and Claude Sonnet 4.5 before Phase 4 task breakdown.
```


