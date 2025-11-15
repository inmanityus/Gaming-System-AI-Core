```markdown
# ETHELRED – Multi‑Language Experience Solutions Architecture

**Date**: 2025-11-14  
**Version**: 0.1.0 (Phase 3 – Solutions draft)  
**Status**: Draft – requires peer review (GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5)  

---

## 0. Purpose, Scope, and Traceability

- **S‑ML‑PURPOSE‑001**  
  Define the implementation‑aware architecture for **multi‑language support** in *The Body Broker*, based on  
  `MULTI-LANGUAGE-EXPANSION-REQUIREMENTS.md` and Ethelred requirements for localization QA.

- **S‑ML‑SCOPE‑001**  
  Scope includes:
  - centralized localization store and APIs,  
  - Language System responsibilities for text and TTS in multiple languages,  
  - timing and lip‑sync integration with UE5 and Audio QA,  
  - propagation of player language preferences,  
  - signals for Ethelred and Content Governance to validate parity and policy compliance.

- **S‑ML‑OUT‑OF‑SCOPE‑001**  
  Out of scope:
  - choice of specific TTS vendors or engines,  
  - detailed font and UI layout implementation,  
  - specific translation workflows/tools (CAT tools, vendor APIs).

- **S‑ML‑TRACE‑001 (Traceability Approach)**  
  A traceability matrix will map `ML‑*` requirements to the services, schemas, and tests outlined here.

---

## 1. High‑Level Component Decomposition

### 1.1 Localization Store & Service (`svc.localization`)

1. **Localization Data Store**  
   - Single source of truth for localizable strings (**ML‑2.1**):  
     - `key`, `language_code`, `text`, `category`, `context`, `description`, `tags[]`, version/audit fields.  
   - Supports pluralization and gender variants via structured templates (**ML‑2.2**).

2. **Localization API Layer**  
   - Provides APIs/NATS subjects for:
     - string lookup by key + language,  
     - bulk export/import for translation,  
     - validation of completeness and placeholder correctness.  
   - Reports missing, outdated, or fallback strings explicitly (**ML‑3.1.2**, **ML‑5.4**).

### 1.2 Language System (`svc.language_system`)

1. **Text Localization Gateway**  
   - Fronts the localization store for gameplay services (UE5, Story Teller, backend).  
   - Applies language preference resolution (e.g., per session) and fallback logic.

2. **TTS & Voice Configuration Manager**  
   - Manages per‑language voice configurations for NPCs/archetypes (**ML‑3.2.2**, **ML‑3.2.3**).  
   - Exposes a TTS interface:
     - input: `text`, `language_code`, `speaker_id`/`archetype_id`, optional emotion tags (**ML‑3.2.1**),  
     - output: audio data plus duration and optional phoneme timing.

3. **Timing & Lip‑Sync Bridge**  
   - Provides timing metadata for voiced lines (**ML‑3.3.1**):  
     - line duration, optional phoneme timings,  
     - derived subtitle timecodes (**ML‑3.3.2**).  
   - Exposes this metadata to UE5 and Ethelred for alignment checks.

### 1.3 Settings & Ethelred

1. **Language Preferences Manager (Settings)**  
   - Stores per‑player UI, subtitle, and spoken language preferences (**ML‑4.1**).  
   - Produces session‑level language snapshots for Ethelred and Content Governance (**ML‑4.3**).

2. **Ethelred Localization QA View**  
   - Consumes localization coverage and quality metrics, plus language snapshots, to:
     - verify parity of horror experience across languages,  
     - detect localization‑related defects (overflow, wrong language, misaligned subtitles, audio mismatch).

---

## 2. Data Flow & Preference Propagation

### 2.1 Player Preferences

1. **Preference Storage**  
   - Settings service stores:
     - `ui_language`, `subtitle_language`, `voice_language` per player (**ML‑4.1**).  
   - Exposes APIs and NATS subjects for reading/updating preferences.

2. **Session Snapshot**  
   - On session start:
     - Settings computes effective language configuration:  
       - falls back where specific preferences are missing,  
       - resolves conflicts (e.g., unsupported combinations).  
     - Writes a session snapshot and publishes `settings.language.session_started` with `session_id`, `player_id`, and effective languages (**ML‑4.3**).

3. **Propagation**  
   - Language System, Story Teller, UE5 client, and Ethelred subscribe to session language snapshots (**ML‑4.2, ML‑7.1**).  
   - All subsequent localization and TTS requests for that session include `language_code` consistent with the snapshot.

### 2.2 Text & Audio Localization Flow

1. **Canonical Content & Keys**  
   - Narrative content (quests, dialogue, lore, items) is authored with stable `line_id`s and localization keys (**ML‑2.3**).  
   - Canonical language (e.g., English) serves as the reference for Ethelred comparisons.

2. **Translation & Storage**  
   - Localization pipeline processes new/updated canonical lines and updates the localization store for each target language (**ML‑5.4**).  
   - Localization service validates completeness and plural/gender correctness.

3. **Runtime String Resolution**  
   - At runtime, UE5, Story Teller, and backend services call Language System or Localization APIs to fetch text by key and language.  
   - Fallbacks are explicit and recorded (e.g., fallback to English).

4. **TTS & Audio Generation**  
   - For voiced lines, game services request TTS or play pre‑recorded audio:  
     - Language System returns audio and timing metadata, tracking the mode (human vs TTS vs mixed) per line (**ML‑3.2.3**).  
   - Audio QA and Ethelred use this metadata to check sync and performance parity (**ML‑5.3**, **ML‑6.2**).

---

## 3. Ethelred Localization QA Integration

### 3.1 Signals to Ethelred

Localization and Language System emit signals enabling Ethelred to:

- know which languages are active per session for UI, subtitles, and voice (**ML‑7.1**);  
- identify machine‑translated vs human‑reviewed content;  
- correlate localization state with engagement and bug metrics.

Subjects (indicative):

- `events.localization.v1.coverage` – per build/language coverage metrics (**ML‑6.1**).  
- `events.localization.v1.issues` – overflow, broken glyphs, wrong language, missing strings (**ML‑5.1, ML‑5.4**).  
- `events.localization.v1.audio_sync` – audio/subtitle sync deviations per language (**ML‑5.3**, **ML‑3.3.2**).

### 3.2 Parity & Policy Checks

Ethelred uses these signals to:

- compare localized text and audio against canonical content level policies (**ML‑7.2**):  
  - no language may silently relax or intensify content beyond allowed levels, unless configured.  
- track:
  - counts of localization‑related bugs and Ethelred‑detected issues per language (**ML‑6.2**),  
  - coverage of localized strings and voiced lines (**ML‑6.1**).

---

## 4. UI & Narrative QA Processes

### 4.1 UI Snapshot Tests

- Build pipeline generates UI snapshots for each Tier‑1 language (**ML‑5.1**):  
  - automated tools capture screens for key menus and HUD scenes,  
  - checks for overflow/truncation, missing glyphs, and layout breakage.  
- Failures are logged and mapped to localization keys for targeted fixes.

### 4.2 Narrative Playthroughs

- Scripted or AI Player playthroughs run per language (**ML‑5.2**):  
  - verify comprehension of key story beats,  
  - ensure horror tone and moral nuance are preserved, not unintentionally comedic or diluted.  
- Ethelred collects playthrough telemetry and reports localization issues back to writers/localization teams.

### 4.3 Audio QA per Language

- Audio QA and Ethelred check per language/character:  
  - pronunciation of important lore terms,  
  - emotional performance parity with canonical reference,  
  - audio/subtitle sync within configured thresholds (**ML‑5.3**).  
- Issues are reported with references to `line_id`, `language_code`, and asset IDs.

---

## 5. Storage & Metrics (Conceptual)

Key conceptual tables:

- `localization_entries` – central store for all localizable strings.  
- `language_preferences` – per‑player language settings.  
- `localization_coverage` – per build/language coverage stats.  
- `localization_issues` – records of QA findings (overflow, missing translations, wrong language, sync problems).

Metrics:

- `localization_coverage_ratio{language,category}`,  
- `localization_fallback_count{language}`,  
- `localization_issues_count{language,type}`,  
- TTS latency per language and cache hit rates (**ML‑6.3**).

---

## 6. SLAs, Safety, and Open Questions

### 6.1 SLAs

- Localization lookup:
  - Target: ≤ 5ms P95 from cache; ≤ 15ms P95 from DB.  
- TTS requests:
  - Latency targets per language tracked and tuned using metrics (**ML‑6.3**); exact numbers depend on chosen providers.

### 6.2 Safety & Content Governance

- Localization MUST not circumvent content policies:  
  - localized text and audio must respect the same content level rules as canonical content (**ML‑7.2**).  
  - Ethelred and Content Governance use consistent category/level mappings across languages.

### 6.3 Open Questions

- **Q‑ML‑001**: Strategy for supporting RTL languages once engine/UI support arrives (data model is ready, but UI path needs design).  
- **Q‑ML‑002**: How to balance machine translation vs human review for different content classes (e.g., hero lines vs UI).  
- **Q‑ML‑003**: Definition of “parity” for horror tone across languages and how Ethelred will measure it.  
- **Q‑ML‑004**: Rollout plan for additional Tier‑2 languages and regional variants.

This architecture remains technology‑agnostic while satisfying v2 requirements. It MUST be peer‑reviewed by GPT‑5.1 / GPT‑5.1‑Codex, Gemini 2.5 Pro, and Claude Sonnet 4.5 before Phase 4 task breakdown.
```


