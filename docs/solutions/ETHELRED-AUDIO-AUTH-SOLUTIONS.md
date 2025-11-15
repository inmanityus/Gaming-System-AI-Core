```markdown
# ETHELRED – Audio Authentication & Vocal Simulator QA Solutions Architecture

**Date**: 2025-11-14  
**Version**: 0.2.0 (Phase 3 – Solutions, peer‑reviewed draft)  
**Status**: Draft – incorporates first‑round feedback (GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5)  

---

## 0. Purpose, Scope, and Traceability

- **S‑AUD‑PURPOSE‑001**  
  Define the **implementation‑aware architecture** for Ethelred’s Audio Authentication & Vocal Simulator QA domain, implementing requirements from  
  `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` §3 (Audio) and system‑wide requirements §1.

- **S‑AUD‑SCOPE‑001**  
  Scope includes:
  - capture of mixed game audio and isolated buses via **virtual routing** (**R‑AUD‑IN‑001**),  
  - segmentation and metadata enrichment for each audio segment (**R‑AUD‑IN‑002**),  
  - analytic pipelines for:
    - human intelligibility and naturalness (**R‑AUD‑MET‑001…002**),  
    - archetype voice conformity (**R‑AUD‑MET‑003**),  
    - simulator stability and artifact detection (**R‑AUD‑MET‑004**),  
    - mix/recording quality (**R‑AUD‑MET‑005**),  
  - emission of per‑segment and per‑build reports (**R‑AUD‑OUT‑001…003**),  
  - feedback flows to the physical vocal cord simulator and the Archetype Chain system (**R‑AUD‑FB‑001…002**).

- **S‑AUD‑OUT‑OF‑SCOPE‑001**  
  Out of scope:
  - choosing specific ASR engines or DSP/ML toolkits,  
  - implementation details of virtual audio routing drivers,  
  - concrete hyperparameters for models or metrics.

- **S‑AUD‑TRACE‑001 (Traceability Approach)**  
  A dedicated traceability matrix for `R‑AUD‑*` and relevant `R‑SYS‑*` requirements will map each requirement to services, events, schemas, and tests. This solutions document defines the architectural **targets** that matrix will reference.

---

## 1. High‑Level Component Decomposition

### 1.1 Domain Services

1. **Audio Capture & Segmentation Service (`svc.ethelred.audio.capture`)**  
   - Receives audio from the game via **virtual audio routing** only (**R‑AUD‑IN‑001**):  
     - full **game mix**,  
     - per‑bus captures (dialogue, vocals, ambient, effects) as configured.  
   - Segments continuous streams into analysis units (e.g., per line / utterance / short windows).  
   - Enriches each segment with metadata per **R‑AUD‑IN‑002**:
     - `timestamp_range`, `speaker_id` (`npc_id` / archetype / narrator / player),  
     - `language_code`,  
     - `context` (line ID, scene ID, emotional tag, environment type),  
     - `simulator_applied` flag (whether it passed through the vocal cord simulator).  
   - Stores WAV/OGG snippets in Red Alert / media storage and passes references + metadata downstream.

2. **Audio Metrics & Scoring Service (`svc.ethelred.audio.metrics`)**  
   - Consumes segment descriptors and media references from `svc.ethelred.audio.capture`.  
   - Runs independent **metric pipelines**:
     - intelligibility,  
     - naturalness/prosody,  
     - archetype conformity,  
     - simulator stability,  
     - mix quality.  
   - Combines metric outputs into a single `AUDIO.SCORES` structure per segment (**R‑AUD‑OUT‑001**).  
   - Emits events to NATS and persists scores to the Ethelred database.

3. **Audio Aggregation & Reporting Job (`svc.ethelred.audio.reports`)**  
   - Periodic job (e.g., per build or nightly) that:
     - aggregates scores per archetype, per language, per scene,  
     - computes distributions and trends over time,  
     - generates structured batch reports per **R‑AUD‑OUT‑002** and Red Alert’s needs.  
   - Emits summary events for Red Alert dashboards and archival.

4. **Audio Feedback Service (`svc.ethelred.audio.feedback`)**  
   - Consumes score events and aggregates and produces **actionable but non‑auto‑tuning** recommendations:  
     - to Vocal Simulator maintainers (**R‑AUD‑FB‑001**),  
     - to Archetype Chain system (**R‑AUD‑FB‑002**).  
   - Outputs structured feedback data sets, not imperative commands, ensuring tuning is **offline and human‑reviewed**.

5. **Ethelred Coordinator (`svc.ethelred.coordinator`) – Audio View**  
   - Subscribes to `AUDIO.SCORES` and audio Red Alert events.  
   - Correlates audio issues with other domains (vision, story, content levels).  
   - Forwards severe audio issues (e.g., unintelligible key lines) to Guardrails Monitor and Red Alert.

### 1.2 Reference Data & Profiles

To support archetype and language‑aware metrics and preserve technology flexibility:

- **Human Speech Baselines Store**  
  - Abstracts reference distributions derived from corpora such as **LibriSpeech**, **Common Voice**, **VCTK** (**R‑AUD‑OBJ‑002**).  
  - Stores language‑specific norms for:
    - speech rate,  
    - pitch distribution,  
    - prosodic variability,  
    - articulation clarity.  

- **Archetype Voice Profiles Store**  
  - Per archetype (vampire, zombie, werewolf, etc.), stores target bands for:
    - F0 range & variability,  
    - formant distributions (timbre),  
    - roughness/breathiness/“corruption” metrics,  
    - desired instability patterns (for monstrous voices) vs clarity requirements for key lines.  
  - Accessible by both scoring and feedback services.

---

## 2. Data Flow & Capture Strategy

### 2.1 Core Flow (Per Audio Segment)

1. **Game Audio Emission (UE5 Side)**  
   - UE5 routes:
     - main mix bus,  
     - optional per‑bus outputs (dialogue, vocal simulator pre/post, ambience, SFX)  
     via virtual audio devices into the Audio Capture service.  
   - For scripted dialogue, the game or Narrative system tags each line with:
     - `line_id`, `scene_id`, `experience_id`, `emotional_tag`,  
     - intended archetype (if applicable) and whether vocal simulator is enabled.

2. **Capture & Segmentation (`svc.ethelred.audio.capture`)**  
   - Receives PCM or compressed audio streams from virtual routing.  
   - Performs segmentation via:
     - explicit markers (start/end for dialogue lines),  
     - silence detection,  
     - fixed windows for ambient or non‑dialogue content.  
   - Writes each segment to Red Alert media storage, e.g. `redalert://media/audio/{build_id}/{segment_id}.ogg`.  
   - Emits `AUDIO.SEGMENT_CREATED` messages containing:
     - media URI,  
     - metadata from **R‑AUD‑IN‑002**,  
     - technical capture details (sample rate, bit depth, channels).

3. **Metrics & Scoring (`svc.ethelred.audio.metrics`)**  
   - Consumes `AUDIO.SEGMENT_CREATED` messages.  
   - Retrieves the audio snippet from media storage.  
   - For each segment:
     - computes intelligibility and naturalness,  
     - evaluates archetype conformity where applicable,  
     - assesses simulator stability if `simulator_applied = true`,  
     - estimates mix quality.  
   - Emits `AUDIO.SCORES` events with per‑segment metrics and classifications.

4. **Aggregation & Reporting (`svc.ethelred.audio.reports`)**  
   - Periodically scans stored per‑segment scores:  
     - groups by archetype, NPC, language, scene, experience, build,  
     - computes distributions and identifies common deviations,  
     - generates Red Alert‑friendly batch reports and high‑level `AUDIO.REPORT` events.

5. **Feedback (`svc.ethelred.audio.feedback`)**  
   - Consumes score and report events, plus reference profile data.  
   - Derives structured recommendations (examples in §5.3) for:
     - simulator parameter tuning,  
     - archetype profile adjustments,  
     - content or mix revisions.  
   - Exposes feedback via NATS events and persistent data structures, not automatic live changes.

### 2.2 Segment Types

To handle different analysis needs, segments are typed:

- **Dialogue Line Segments**  
  - Primary focus: intelligibility, naturalness, archetype conformity.  
  - Typically 1–8 seconds, aligned with story lines.  
  - Must include speaker identity, language, line ID, scene/experience context.

- **Monstrous Vocalization Segments**  
  - Screams, growls, breaths, transformation sounds.  
  - Focus: archetype conformity and simulator stability; intelligibility may be N/A.  
  - Flags: `segment_type = "monster_vocalization"`, `archetype_id` present.

- **Ambient / Environmental Segments**  
  - Background hums, environment loops, crowd noise.  
  - Focus: mix quality and horror atmosphere contribution.  
  - Captured in fixed windows; tied to scene IDs and environment tags.

- **Mixed Bus Segments**  
  - Short windows of the full mix around key events (e.g., scares, boss introductions).  
  - Used for verifying overall intelligibility and balance under full game load.

---

## 3. Event Contracts & NATS Subjects

### 3.1 Canonical Envelope

All audio events MUST embed the **canonical envelope** from **R‑SYS‑OBS‑001** with `domain = "Audio"`:

```jsonc
{
  "trace_id": "uuid",
  "session_id": "sess-123",
  "player_id": "pseudonymous-player-id?",
  "build_id": "build-2025-11-14",
  "timestamp_range": { "start": "...", "end": "..." },
  "domain": "Audio",
  "issue_type": "AUDIO.SCORES | AUDIO.REPORT | AUDIO.FEEDBACK",
  "severity": "info | warning | error | critical",
  "confidence": 0.0,
  "evidence_refs": ["redalert://media/audio/..."],
  "goal_tags": ["G-IMMERSION", "G-HORROR"]
}
```

The analytic payload is attached under `payload`.

### 3.2 NATS Subjects

Proposed subjects:

- Requests / internal messages:
  - `svc.ethelred.audio.v1.segment_created` – queue‑group subject consumed by `svc.ethelred.audio.metrics`.  
  - `svc.ethelred.audio.v1.describe_segment` – optional metadata query.

- Events:
  - `events.ethelred.audio.v1.scores` – per‑segment `AUDIO.SCORES` events.  
  - `events.ethelred.audio.v1.report` – per‑build or periodic batch reports.  
  - `events.ethelred.audio.v1.feedback` – simulator/archetype feedback events.

### 3.3 `AUDIO.SCORES` Payload

Satisfying **R‑AUD‑OUT‑001**:

```jsonc
{
  "segment_id": "seg-aud-123",
  "segment_type": "dialogue | monster_vocalization | ambient | mixed_bus",
  "speaker": {
    "speaker_id": "npc-032",
    "role": "npc | narrator | player",
    "archetype_id": "vampire_house_alpha"
  },
  "language_code": "en-US",
  "context": {
    "line_id": "line-bridge-warning",
    "scene_id": "scene-bridge-01",
    "experience_id": "exp-dungeon-diving",
    "emotional_tag": "panic",
    "environment_type": "storm_bridge"
  },
  "simulator_applied": true,
  "scores": {
    "intelligibility": 0.92,
    "naturalness": 0.88,
    "archetype_conformity": 0.80,
    "simulator_stability": 0.95,
    "mix_quality": 0.84
  },
  "bands": {
    "intelligibility": "acceptable | degraded | unacceptable",
    "naturalness": "ok | robotic | monotone",
    "archetype_conformity": "on_profile | too_clean | too_flat | misaligned",
    "simulator_stability": "stable | unstable",
    "mix_quality": "ok | noisy | clipping | unbalanced"
  },
  "evidence_refs": ["redalert://media/audio/build-2025-11-14/seg-aud-123.ogg"]
}
```

### 3.4 Archetype Batch Reports

Satisfying **R‑AUD‑OUT‑002**:

```jsonc
{
  "build_id": "build-2025-11-14",
  "archetype_id": "vampire_house_alpha",
  "language_code": "en-US",
  "summary": {
    "num_segments": 320,
    "intelligibility_distribution": { "acceptable": 0.93, "degraded": 0.06, "unacceptable": 0.01 },
    "naturalness_mean": 0.87,
    "archetype_conformity_mean": 0.81,
    "simulator_stability_mean": 0.96,
    "mix_quality_mean": 0.83
  },
  "common_deviations": [
    "lines in hospital wing slightly too clean (less corruption) vs archetype profile",
    "occasional clipping on boss intro roars in bridge scenes"
  ],
  "comparison_prev_build": {
    "build_id": "build-2025-11-07",
    "archetype_conformity_delta": 0.03,
    "simulator_stability_delta": -0.01,
    "notes": "Stability slightly decreased due to new FX; intelligibility improved."
  }
}
```

### 3.5 Red Alerts – Audio

Satisfying **R‑AUD‑OUT‑003**:

Red Alert integration is handled via Ethelred Coordinator subscribing to audio events and producing **UI‑oriented alerts** when:

- key narrative lines fall below configured intelligibility thresholds,  
- major artifacts occur in marked hero scenes,  
- archetype conformity or simulator stability drops sharply vs previous builds.

The Coordinator can map `AUDIO.SCORES` and `AUDIO.REPORT` data into Red Alert’s alert model without altering core audio contracts.

---

## 4. Metric Pipeline Concepts

The metric pipelines are conceptually independent stages; implementations can combine them but MUST preserve these outputs and invariants.

### 4.1 Human Intelligibility Pipeline

- **Inputs**: audio segment, language code, speaker role.  
- **Features**:
  - ASR proxy for word error rate or lexical match,  
  - SNR, distortion, clipping metrics.  
- **Outputs**:
  - scalar intelligibility score in [0, 1],  
  - band classification: `acceptable`, `degraded`, `unacceptable`.  
- **Constraints**:
  - MUST be robust to horror sound design (screams, reverb) and focus on **intelligibility of intended content**, not perfect studio clarity.

### 4.2 Naturalness & Prosody Pipeline

- **Inputs**: audio segment, language code.  
- **Features**:
  - pitch contour over time,  
  - speech rate vs per‑language norms,  
  - prosodic variability (stress patterns, pauses).  
- **Outputs**:
  - naturalness score in [0, 1],  
  - flags for “robotic” or “repetitive” prosody.  
- **Constraints**:
  - For monstrous archetypes, naturalness must respect their designed instability – the target is **convincing performance**, not standard human prosody.

### 4.3 Archetype Conformity Pipeline

- **Inputs**: audio segment, `archetype_id`, archetype profile.  
- **Features**:
  - F0 range and variability vs archetype bands,  
  - formant and spectral envelope comparisons,  
  - roughness/breathiness/“corruption” metrics.  
- **Outputs**:
  - archetype conformity score in [0, 1],  
  - classification labels (`on_profile`, `too_clean`, `too_flat`, `misaligned`).  
- **Constraints**:
  - MUST support multiple archetypes and evolution of profiles over time without hard‑coding implementation assumptions.

### 4.4 Simulator Stability Pipeline

- **Inputs**: audio segment with `simulator_applied = true`.  
- **Features**:
  - jitter, shimmer, onset/offset stability metrics,  
  - artifact counts (clicks, pops, loops).  
- **Outputs**:
  - simulator stability score in [0, 1],  
  - classification (`stable` vs `unstable`).  
- **Constraints**:
  - Where possible, separate simulator‑originated artifacts from mix or environment artifacts using bus routing and metadata.

### 4.5 Mix / Recording Quality Pipeline

- **Inputs**: audio segment (any type).  
- **Features**:
  - clipping, dynamic range, noise floor,  
  - reverb/FX characteristics vs environment metadata.  
- **Outputs**:
  - mix quality score in [0, 1],  
  - labels: `noisy`, `clipping`, `unbalanced`, etc.  
- **Constraints**:
  - Must tolerate horror‑intentional noise (e.g., gritty texture) while flagging **unintentional** technical flaws.

### 4.6 Security & Adversarial Testing (Conceptual)

- Define an **adversarial test suite** for the audio QA stack, including:  
  - replayed audio, pitch/time‑scale manipulation, extreme noise injection, codec artifacts, and simple adversarial perturbations;  
  - tests where vocal simulator outputs are intentionally pushed toward instability.  
- For any future **authentication‑style** checks (e.g., verifying a given archetype or voice actor identity), the architecture MUST support:  
  - tracking false‑accept / false‑reject rates (FAR/FRR) and EER at configuration‑defined thresholds,  
  - evaluating robustness against basic spoofing attempts or unauthorized voice cloning using synthetic voices from other archetypes.  
- These concerns extend the core QA metrics and are governed by global safety requirements (`R‑SYS‑SAFE‑*`), not by per‑player optimization.

---

## 5. Storage, Feedback, and Integration

### 5.1 Storage Concepts

Core tables (conceptual, likely in PostgreSQL):

- `audio_segments`  
  - `segment_id` (PK, UUID)  
  - `build_id`, `segment_type`, `speaker_id`, `archetype_id?`  
  - `language_code`, `scene_id`, `experience_id`, `line_id?`  
  - `timestamp_start`, `timestamp_end`  
  - `simulator_applied` (bool)  
  - `media_uri` (string)  
  - `capture_metadata` (JSONB)  

- `audio_scores`  
  - `segment_id` (FK → `audio_segments`)  
  - `scores` (JSONB) – intelligibility/naturalness/archetype/mix/stability  
  - `bands` (JSONB)  
  - `created_at`  

- `audio_archetype_reports`  
  - `build_id`, `archetype_id`, `language_code`, `metrics` (JSONB), `notes` (text).

### 5.2 Data Governance & Consent (Conceptual)

- All stored audio segments and scores MUST respect global data rules:  
  - pseudonymous identifiers only (**R‑SYS‑DATA‑001**),  
  - explicit `actor_type` flags for AI vs real players (**R‑SYS‑DATA‑002**),  
  - environment‑specific retention windows and deletion on request (**R‑SYS‑DATA‑003**).  
- For human voice actors or recorded sessions used in QA:  
  - consent type (e.g., in‑game usage, testing/training usage) SHOULD be tracked in metadata,  
  - any export of audio for offline analysis MUST pass through a data‑governance gate that enforces consent and retention policies.

### 5.3 Feedback to Vocal Simulator (R‑AUD‑FB‑001)

Feedback service produces **parameter‑level recommendations**, not direct updates:

```jsonc
{
  "build_id": "build-2025-11-14",
  "archetype_id": "vampire_house_alpha",
  "simulator_profile_id": "vampire_alpha_v1",
  "findings": [
    {
      "dimension": "roughness",
      "observed_mean": 0.45,
      "target_range": [0.55, 0.70],
      "recommendation": "Increase glottal roughness parameter by 10–15% for scenes tagged 'ritual'."
    }
  ],
  "notes": "Do not auto‑apply; requires sound designer review."
}
```

These recommendations are consumed by simulator maintainers via dashboards or offline tools.

### 5.4 Feedback to Archetype Chain (R‑AUD‑FB‑002)

For Archetype Chain, feedback focuses on **behavior and content generation**:

```jsonc
{
  "archetype_id": "zombie_horde",
  "language_code": "en-US",
  "voice_quality_summary": {
    "mean_archetype_conformity": 0.78,
    "weak_contexts": ["hospital", "prison_yard"]
  },
  "candidate_training_examples": [
    {
      "segment_id": "seg-aud-882",
      "media_uri": "redalert://media/audio/.../seg-aud-882.ogg",
      "labels": ["too_clean", "not_monster_like_enough"]
    }
  ]
}
```

Archetype Chain can use these as **offline training or evaluation data**, preserving the requirement that no auto‑tuning occurs in live builds.

### 5.5 Guardrails Monitor & Content Levels

- Audio domain signals feed Guardrails Monitor and Content Level enforcement when:
  - dialogue or screams exceed configured content levels (e.g., extreme violence audio),  
  - repeated exposure patterns could affect addiction indicators (e.g., loops around high‑intensity content).  
- Ethelred provides scores and evidence; Guardrails retains enforcement authority, consistent with **R‑SYS‑ARCH‑003**.

### 5.6 Multimodal Integration with 4D Vision

- Audio QA SHOULD align with 4D Vision via shared `trace_id`, `scene_id`, and `timestamp_range`, enabling:  
  - checks that key horror beats are both **seen** and **heard** as intended (e.g., scares not undercut by flat audio),  
  - correlation of intelligibility issues with camera movement, occlusion, or environmental effects,  
  - future multimodal detection of synthetic or inconsistent content (e.g., mismatched lip‑sync vs vocal archetype).

---

## 6. SLAs, Degradation, and Kill Switches

### 6.1 Latency Targets

- **Per‑segment scoring**:  
  - Target ≤ 3 seconds for typical dialogue segments in offline / build validation contexts.  
  - For interactive QA, short segments (≤ 2s) should be processed in ≤ 1–2 seconds where feasible.

- **Per‑build reports**:  
  - Batch jobs (reports, feedback generation) may run for several minutes, but should complete within CI/QA budgets.

Metrics such as `audio_segments_processed_per_minute` and `audio_scoring_latency_seconds` MUST be exported to observability per **R‑SYS‑OBS‑002**.

### 6.2 Degradation & Kill Switch

- If audio metrics service is degraded:
  - Coordinator marks the Audio domain as `degraded`,  
  - emits `SYS.HEALTH` events instead of silently failing,  
  - continues to capture segments for later analysis where storage permits.  

- Feature flags via Settings / Model Management can:
  - disable audio analysis entirely, or  
  - restrict it to subsets (e.g., only hero lines, only English).  

---

## 7. Open Questions & Next Steps

- **Q‑AUD‑001**: Choice of ASR / intelligibility proxy implementation and its latency/accuracy trade‑offs for horror‑style audio.  
- **Q‑AUD‑002**: How many language‑specific baseline profiles are needed at launch vs later expansion (ties into multi‑language requirements).  
- **Q‑AUD‑003**: Desired granularity of simulator parameters to expose for feedback (coarse preset vs fine‑grained DSP controls).  
- **Q‑AUD‑004**: How strongly to couple archetype voice profiles with narrative design (single profile per archetype vs per‑faction variants).  

This solutions architecture intentionally stays at the **WHAT‑with‑implementation‑awareness** level. It MUST undergo peer review by GPT‑5.1 / GPT‑5.1‑Codex, Gemini 2.5 Pro, and Claude Sonnet 4.5 before Phase 4 task breakdown.
```


