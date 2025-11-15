```markdown
# Multi‑Language Expansion Requirements

**Date**: November 14, 2025  
**Version**: 2.0.0 (requirements rewritten from scratch)  
**Status**: Phase 2 – Requirements Definition  
**Collaborators (peer models)**: GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5  

---

## 0. Purpose & Scope

- **ML‑0.1 (Purpose)**  
  Define **WHAT** the multi‑language subsystem must provide so that *The Body Broker* delivers an equally powerful horror experience in multiple human languages across:
  - UI and HUD text,  
  - subtitles and captions,  
  - spoken dialogue and narration,  
  - AI‑generated content (Story Teller, Language System).

- **ML‑0.2 (Scope)**  
  Covers:
  - supported languages and expansion model,  
  - centralized localization data model,  
  - Language System responsibilities (text + TTS),  
  - timing and lip‑sync constraints,  
  - QA/testing and metrics,  
  - integration points with Ethelred and Content Governance.

---

## 1. Supported Languages & Extensibility

- **ML‑1.1 (Tier‑1 Launch Languages)**  
  The system SHALL fully support, at minimum:
  1. English (default)  
  2. Chinese (Mandarin, Simplified)  
  3. Japanese  
  4. French  
  5. Spanish (Spain)  
  6. Spanish (Latin American/Mexican)  
  7. Thai

- **ML‑1.2 (Extensible Language Set)**  
  It MUST be possible to add additional languages (e.g., German, Russian, Brazilian Portuguese, Korean) by:
  - adding configuration/metadata and content,  
  - without changing Language System core code.

- **ML‑1.3 (RTL Readiness)**  
  The localization data model and APIs MUST be text‑direction agnostic, so that when the engine/UI supports right‑to‑left languages, those languages can be added without redesigning the language subsystem.

---

## 2. Central Localization Data Model

- **ML‑2.1 (Single Source of Truth)**  
  All localizable text MUST be stored in a centralized localization store with, at minimum:
  - `key` (stable identifier),  
  - `language_code` (BCP‑47),  
  - `text`,  
  - `category` (`ui`, `dialogue`, `quest`, `lore`, `system`),  
  - `context` and `description` for translators,  
  - optional `tags[]`,  
  - version and audit timestamps.

- **ML‑2.2 (Pluralization & Gender)**  
  The data model MUST support plural forms and gendered variants per language via a structured pattern (e.g., ICU‑style templates) rather than manual concatenation.

- **ML‑2.3 (Canonical Line IDs)**  
  Narrative/dialogue lines MUST have canonical `line_id`s that:
  - remain stable across languages,  
  - allow Ethelred to compare localized lines back to their canonical version.

---

## 3. Language System Service Responsibilities

### 3.1 Text Localization

- **ML‑3.1.1 (Coverage)**  
  Language System SHALL provide localized text for:
  - all UI/HUD elements,  
  - all narrative text (quests, lore, item descriptions, tips),  
  - error/system messages and tutorial prompts,  
  for every supported language.

- **ML‑3.1.2 (Lookup & Fallback)**  
  It SHALL expose APIs and/or NATS subjects to:
  - look up localized strings by `key` + `language_code`,  
  - return explicit indications when falling back to a default language.

- **ML‑3.1.3 (Story Teller Integration)**  
  Story Teller MUST either:
  - generate localized text directly for a requested `language_code`, **or**  
  - generate canonical language text and use Language System to translate it;  
  in both cases, the resulting lines MUST carry the canonical `line_id` for QA and traceability.

### 3.2 Speech / Text‑to‑Speech

- **ML‑3.2.1 (TTS Interface)**  
  Language System SHALL provide a TTS interface that accepts:
  - `text`, `language_code`, `speaker_id`/`archetype_id`, optional emotion tags,  
  and returns:
  - audio data (format agreed per build),  
  - accurate duration metadata.

- **ML‑3.2.2 (Character Consistency Across Languages)**  
  For each NPC or archetype, voice configurations MUST be defined per language such that:
  - the character’s perceived personality and vocal identity remain consistent (tone, energy, “feel”),  
  even when different actors/voices are used across languages.

- **ML‑3.2.3 (Hybrid Human/TTS Support)**  
  The system MUST support:
  - pre‑recorded human performances,  
  - neural TTS,  
  - mixed setups (e.g., TTS for low‑priority lines, human for hero scenes),  
  and MUST track, per line, which mode was used.

### 3.3 Timing & Lip‑Sync

- **ML‑3.3.1 (Duration Contracts)**  
  For each voiced line, Language System MUST provide:
  - line duration,  
  - optional per‑phoneme timing (if available),  
  so UE5 and Ethelred can verify lip‑sync and subtitle alignment within configured tolerances.

- **ML‑3.3.2 (Subtitle Alignment)**  
  Subtitle timecodes MUST be derived from, or validated against, the same timing metadata as the audio, so that:
  - Ethelred can detect misalignment (e.g., subtitles leading/lagging audio by more than allowed threshold).

---

## 4. Player Language Preferences & Propagation

- **ML‑4.1 (Preference Storage)**  
  The Settings service MUST store, per player:
  - UI language,  
  - subtitle language,  
  - spoken dialogue language,  
  allowing these to differ if desired.

- **ML‑4.2 (Propagation)**  
  Language preferences MUST be propagated via NATS/API to:
  - Language System,  
  - Story Teller,  
  - UE5 client,  
  and MUST be included in relevant Ethelred events for analysis.

- **ML‑4.3 (Session‑Level Snapshot)**  
  At session start, an effective language configuration snapshot MUST be created and associated with the session so that:
  - Ethelred and Content Governance can reason over language choices consistently for the entire session.

---

## 5. QA, Testing & Tooling

- **ML‑5.1 (UI Snapshot Testing)**  
  The build pipeline MUST support automated UI snapshot tests for each supported language that:
  - detect text overflow and truncation,  
  - detect broken glyphs/missing fonts,  
  - detect obvious layout breakage caused by longer strings.

- **ML‑5.2 (Narrative Playthrough Testing)**  
  Scripted or AI Player playthroughs MUST be run in each language to verify:
  - comprehension of critical story beats,  
  - preservation of horror tone and moral nuance (no unintentional comedy or trivialization),  
  with issues surfaced to writers/localization.

- **ML‑5.3 (Audio QA)**  
  For each language and key character, QA MUST verify:
  - pronunciation of important lore terms and names,  
  - emotional performance parity with canonical reference,  
  - audio/subtitle synchronization within acceptable limits.

- **ML‑5.4 (Localization Pipeline)**  
  Tooling MUST exist to:
  - extract localizable keys from code/content,  
  - export them for translation,  
  - re‑import translations with validation checks (missing strings, placeholder artifacts, formatting issues).

---

## 6. Metrics & Monitoring

- **ML‑6.1 (Coverage Metrics)**  
  Per build and per language, the system SHALL compute:
  - percentage of localized strings present,  
  - percentage of voiced lines localized (via TTS or recording),  
  - number of fallbacks to default language.

- **ML‑6.2 (Quality Metrics)**  
  Metrics MUST include:
  - count and rate of localization‑related bugs,  
  - counts of Ethelred‑detected localization issues (wrong language, overflow, mis‑timed subtitles),  
  - optional player satisfaction indicators per language (where available).

- **ML‑6.3 (Performance & Cost Metrics)**  
  Track:
  - TTS request latency per language,  
  - cache hit rates for localized assets,  
  to guide caching and performance tuning.

---

## 7. Integration with Ethelred & Content Governance

- **ML‑7.1 (Signals to Ethelred)**  
  Language System and localization tooling MUST emit signals that enable Ethelred to:
  - know which languages are in use for UI, subtitles, and voice,  
  - identify machine‑translated vs human‑reviewed content,  
  - correlate localization state with engagement/bug data.

- **ML‑7.2 (Content Policy Alignment)**  
  Ethelred’s content governance checks MUST verify that:
  - localized text and audio respect the same content level policy as the canonical version,  
  - no locale silently weakens or intensifies horror/explicitness beyond what Content Level Manager allows, unless explicitly configured.

---

**End of Multi‑Language Expansion Requirements v2.0.0**
```



