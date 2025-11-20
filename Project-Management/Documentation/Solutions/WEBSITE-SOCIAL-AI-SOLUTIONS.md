```markdown
# WEBSITE & SOCIAL AI – Scoping Solutions Architecture (Placeholder)

**Date**: 2025-11-14  
**Version**: 0.1.0 (Phase 3 – Solutions scoping draft)  
**Status**: Scoped – detailed behavior deferred to Phase 6 (user inputs required)  

---

## 0. Purpose, Scope, and Constraints

- **S‑WS‑PURPOSE‑001**  
  Provide a **scoped architectural outline** for Website & Social AI that satisfies `WEBSITE-SOCIAL-AI-REQUIREMENTS.md` v0.2.0 without locking in specific frameworks or behaviors.

- **S‑WS‑SCOPE‑001**  
  Scope includes:
  - high‑level components for:
    - comments/discussion assistance,  
    - lore/wiki assistance,  
    - high‑level external platform integration,  
    - AI persona layer;  
  - strict safety/privacy constraints,  
  - integration hooks with Ethelred and Story Teller for feedback only (no real‑time game control initially).

- **S‑WS‑CONSTRAINTS‑001**  
  - Guardrails + human‑in‑the‑loop moderation are mandatory for all website/social interactions.  
  - Website/Social AI operates **outside** the live game loop and cannot directly manipulate in‑game state.  
  - Detailed behavior, brand voice, and autonomy level will be specified in Phase 6 once user answers the open questions in the requirements doc.

---

## 1. High‑Level Component Decomposition (Scoping)

### 1.1 Website AI Gateway (`svc.website_ai_gateway`)

- Front‑end agnostic gateway (REST/GraphQL) for website and social surfaces:  
  - receives user requests from site (comments, lore queries, documentation help),  
  - enforces authentication and rate limiting,  
  - ensures requests are pseudonymous and free of sensitive PII where possible.

### 1.2 Moderation & Guardrails Layer (`svc.website_moderation`)

- Applies **Guardrails Monitor** and additional social‑specific policies to all requests/responses:  
  - toxicity, harassment, hate content, self‑harm signals, etc.  
  - content level enforcement aligned with in‑game Content Level Manager where applicable.  
- Supports human review queues for flagged content.

### 1.3 Lore & Documentation Assistant (`svc.lore_assistant`)

- Provides:
  - lore/wiki Q&A for the game world,  
  - documentation assistance for game systems and updates.  
- Uses canonical lore sources (narrative docs, Story Memory baselines) and must not leak internal implementation details beyond allowed scope.

### 1.4 Social Persona Layer (`svc.social_persona`, future)

- Encapsulates game‑branded AI personas for:
  - social media interactions,  
  - site‑embedded assistants.  
- Behavior is constrained by:
  - brand voice guidelines (Phase 6),  
  - strict guardrails (no direct game control, no real‑world advice outside allowed topics).

---

## 2. Integration with Ethelred and Story Systems

### 2.1 Ethelred Feedback Hooks

- Website/Social AI may:
  - surface **aggregated** insights from Ethelred reports (e.g., “latest build improvements”, “known issues”) for community transparency,  
  - accept manually curated content derived from Ethelred dashboards (e.g., patch notes, QA narratives).  
- Ethelred does **not** consume live website/social interactions as core gameplay telemetry unless explicitly configured and anonymized.

### 2.2 Story Teller & Story Memory

- Lore assistant queries may use Story Memory baselines to provide consistent world information.  
- No direct writing back into Story Memory or Story Teller from website interactions in Phase 3:  
  - any future bidirectional bridges must go through explicit design and safety review.

---

## 3. Safety, Privacy, and Governance (Scoping)

- All Website/Social AI outputs pass through Guardrails Monitor with website‑specific policies.  
- Logging and audit:
  - all AI interactions are logged with pseudonymous identifiers and moderation outcomes,  
  - access controls ensure only authorized staff can review interaction histories.  
- Ethelred’s role is limited to:
  - providing validated, non‑sensitive QA and lore summaries as optional inputs,  
  - not using website interactions to adjust in‑game difficulty, rewards, or content in real time.

---

## 4. Open Questions for Phase 6

The following must be answered in Phase 6 before detailed design or implementation:

- **Q‑WS‑001**: Desired brand voice(s) and persona boundaries for Website/Social AI.  
- **Q‑WS‑002**: Which external platforms (if any) to support (Discord, X/Twitter, Reddit, etc.).  
- **Q‑WS‑003**: Level of autonomy allowed for AI in public communications (announcement drafts vs direct posting).  
- **Q‑WS‑004**: How tightly Website/Social AI should be coupled with in‑game events (real‑time vs delayed summaries).  
- **Q‑WS‑005**: Specific success metrics (community engagement, support deflection, lore discovery) and their relationship to Ethelred reports.

This document intentionally remains high‑level and non‑binding on implementation details. Once Phase 6 clarifies behavior and policy, a full solutions doc can be written using this outline as a starting point.
```


