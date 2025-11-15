# Website / Social AI – Phase 4 Scope-Level Task Breakdown

**Domain**: Website / Social AI (Scoping Only)  
**Source Requirements**: `WEBSITE-SOCIAL-AI-REQUIREMENTS.md` v0.2.0 (placeholder), `ETHELRED-COMPREHENSIVE-REQUIREMENTS.md` references  
**Source Solutions**: `docs/solutions/WEBSITE-SOCIAL-AI-SOLUTIONS.md`  

This domain is intentionally **implementation-blocked** until Phase 6 user decisions are made. Tasks below are scope-level and focus on policy, safety, and integration boundaries; no production code or external platform integration should ship until a v1 requirements document is written and approved.

---

## Milestone 1 – Policy & Scope Definition (Phase 6 Inputs)

### TWS-01 – Consolidate Website/Social AI Policy Questions for Phase 6
- **Description**: Extract and refine all open questions from `WEBSITE-SOCIAL-AI-REQUIREMENTS.md` §4 into a structured decision brief to be answered in Phase 6.
- **Dependencies**: Requirements and solutions docs, brand and legal guidelines if available.
- **Acceptance Criteria**:
  - Decision brief clearly lists questions by theme: brand voice/persona, scope of autonomy, depth of game integration, platform priorities, moderation authority, success metrics.
  - For each question, proposed options and implications are documented to support user decision making.
  - Brief is stored under `Project-Management/` and referenced in future Phase 6 handoffs.
- **Validation**:
  - **Review**: User-facing review to confirm completeness and clarity of questions and options.

### TWS-02 – Define Non-Negotiable Safety & Moderation Baseline
- **Description**: Translate `WS‑3.*` safety, moderation, and privacy requirements into a concrete baseline policy that any future Website/Social AI implementation must obey.
- **Dependencies**: Guardrails Monitor policies, legal/privacy requirements, `ABSOLUTE-PEER-CODING-MANDATORY`, `/all-rules`.
- **Acceptance Criteria**:
  - Baseline policy explicitly covers Guardrails fronting, human-in-the-loop moderation, audit logging, and privacy/identity separation.
  - Policy specifies prohibited behaviors (e.g., no real-time game control, no PII linkage without consent).
  - Policy is approved as a gating document for any future design/implementation.
- **Validation**:
  - **Review**: Safety/legal review (via external model and/or human) confirms the baseline is sufficient and aligned with existing Guardrails.

---

## Milestone 2 – Integration Boundaries & Data Mapping (Design-Only)

### TWS-03 – Define Integration Boundaries with Ethelred & Story Systems
- **Description**: Document allowed information flows between Website/Social AI components and Ethelred, Story Teller, and Story Memory, strictly following “feedback only, no real-time control” constraints.
- **Dependencies**: WEBSITE-SOCIAL-AI-SOLUTIONS, Ethelred architecture docs, Story Memory solutions.
- **Acceptance Criteria**:
  - Data flow diagrams and descriptions clarify which signals can flow from Website/Social AI into Ethelred/Story systems (e.g., aggregated feedback, not raw user posts).
  - Document explicitly forbids direct game state changes or tuning from website interactions in initial phases.
  - Integration boundaries are cross-referenced in both Website/Social and Ethelred docs.
- **Validation**:
  - **Review**: Architecture review confirms boundaries are consistent with safety baseline and Ethelred’s role.

### TWS-04 – Map Allowed Data Types & Privacy Constraints
- **Description**: Define which data fields (feedback categories, sentiment, lore queries, etc.) may be ingested or emitted by Website/Social AI, along with privacy constraints and pseudonymization rules.
- **Dependencies**: TWS-02, data governance rules, existing Guardrails data policies.
- **Acceptance Criteria**:
  - A table or spec exists listing each allowed data type, its purpose, retention, and privacy constraints.
  - Explicit rules prohibit automatic linking of external identities to in-game identities without explicit, revocable consent.
  - Guidance is provided for how pseudonymous identifiers should be handled in future implementations.
- **Validation**:
  - **Review**: Data governance and privacy review (via external model) confirms mappings respect global rules and legal expectations.

---

## Milestone 3 – Future Service Design Skeletons (No Production Code Yet)

### TWS-05 – Draft Service Design Skeletons for Website AI Gateway & Moderation
- **Description**: Draft high-level service design skeletons (not full implementations) for `svc.website_ai_gateway` and `svc.website_moderation`, focusing on endpoints, high-level workflows, and Guardrails integration.
- **Dependencies**: TWS-02–04, NATS/HTTP gateway patterns, Guardrails Monitor integration patterns.
- **Acceptance Criteria**:
  - Skeleton designs specify conceptual endpoints and flows (e.g., comment triage, lore queries) without concrete external platform connectors.
  - Guardrails and moderation steps are explicitly embedded in every flow.
  - Designs are clearly labeled as “non-binding skeletons” pending Phase 6 decisions.
- **Validation**:
  - **Review**: Architecture review to ensure designs are consistent with safety baseline and integration boundaries.

### TWS-06 – Draft Lore Assistant Design Constraints
- **Description**: Define design constraints and responsibilities for `svc.lore_assistant` so that it can serve canonical lore/wiki answers without leaking internal implementation details or violating canon.
- **Dependencies**: Story Memory baselines, lore documentation, Story Teller requirements.
- **Acceptance Criteria**:
  - Responsibilities and non-responsibilities for lore assistant are documented (what it may and may not answer).
  - Source-of-truth data sources (story bibles, SMS baselines) and caching strategies are outlined.
  - Constraints ensure that lore assistant does not modify Story Memory or Story Teller state directly.
- **Validation**:
  - **Review**: Narrative design review (via external model) confirms constraints align with canon protection goals.

### TWS-07 – Define Gating Conditions for Social Persona Implementation
- **Description**: Define explicit gating conditions for implementing `svc.social_persona` (future), tying them to answered policy questions and safety readiness.
- **Dependencies**: TWS-01–02, brand voice decisions, moderation authority decisions.
- **Acceptance Criteria**:
  - Documented conditions list which policy decisions and infrastructure pieces must be in place before any persona work begins.
  - Conditions include requirements for brand voice spec, moderation tools, rollback/kill-switch mechanisms, and risk appetite.
  - These conditions are referenced from `WEBSITE-SOCIAL-AI-REQUIREMENTS.md` as blockers.
- **Validation**:
  - **Review**: Safety and brand reviews agree conditions are strong enough to prevent premature persona deployment.

---

## Milestone 4 – Readiness & Traceability (Planning Only)

### TWS-08 – Website/Social AI Traceability & Readiness Notes
- **Description**: Create a traceability note mapping current placeholder requirements (`WS‑*`) to planned components and clearly stating that implementation is deferred pending Phase 6.
- **Dependencies**: TWS-01–07, requirements and solutions docs.
- **Acceptance Criteria**:
  - Each `WS‑*` requirement is mapped either to a planned component or explicitly flagged as “requires Phase 6 decision” with a link to the decision brief.
  - A concise readiness section for Website/Social AI is prepared for `GAME-READINESS-ASSESSMENT.md`, stating its status as scoped but intentionally unimplemented.
  - Peer review (external model) confirms that no implicit commitments to implementation have slipped into the plan.
- **Validation**:
  - **Analytics/Validation**: Peer review of traceability and readiness notes; gaps and ambiguities recorded for Phase 6.



