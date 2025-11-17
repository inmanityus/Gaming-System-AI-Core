```markdown
# Website / Social AI Requirements (Placeholder v2)

**Date**: November 14, 2025  
**Version**: 0.2.0 (structured placeholder – detailed spec deferred to Phase 6)  
**Status**: Phase 2 – Requirements Skeleton (USER INPUT REQUIRED)  
**Collaborators (peer models)**: GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5  

---

## 0. Purpose & Scope

- **WS‑0.1 (Purpose)**  
  Define a **safe, minimal, and architecture‑compatible skeleton** for the Website/Social AI system that will later provide:
  - AI‑assisted comments/discussion,  
  - AI‑assisted lore wiki and documentation,  
  - high‑level integration with external community platforms,  
  while respecting strict safety, privacy, and brand constraints to be finalized with the user in Phase 6.

- **WS‑0.2 (Scope)**  
  This document:
  - specifies high‑level components and integration points,  
  - sets non‑negotiable moderation/safety requirements,  
  - enumerates open questions that **must** be answered before any implementation work begins.  
  It intentionally avoids concrete API designs and tool/vendor choices.

---

## 1. High‑Level Components

- **WS‑1.1 (Comments & Discussion Layer)**  
  A future Website/Social AI system SHALL support:
  - AI‑assisted replies to player comments on official channels (site, forums, etc.),  
  - triage of comments into structured categories (bugs, performance, balance, lore, praise, abuse),  
  - escalation of high‑priority threads to human moderators and Ethelred.

- **WS‑1.2 (Lore Wiki & Documentation)**  
  The system SHALL assist with:
  - maintaining a canonical lore/wiki (human‑approved),  
  - generating draft updates based on game patches and narrative changes,  
  - ensuring the wiki reflects in‑game canon and does not contradict Story Teller’s story bible.

- **WS‑1.3 (External Platform Bridges)**  
  Long‑term, the system MAY integrate with selected external platforms (e.g., forums, curated social feeds) to:
  - ingest feedback and sentiment,  
  - propose responses and posts,  
  subject to rate limits, platform policies, and human oversight.

- **WS‑1.4 (AI Persona Layer)**  
  A configurable AI persona (tone, humor, voice) WILL exist, but its detailed behavior, boundaries, and script **must be specified by the user** during Phase 6 before any deployment.

---

## 2. Integration with Ethelred & Story Teller

- **WS‑2.1 (Feedback into Ethelred)**  
  Website/Social AI MUST eventually be able to supply Ethelred with structured signals, such as:
  - recurring bug reports (e.g., crashes, soft‑locks),  
  - performance complaints (e.g., stutter in specific levels),  
  - UX pain points (e.g., “players confused by mechanic X”),  
  tagged with frequency, severity, and approximate affected platform/build when detectable.

- **WS‑2.2 (Feedback into Story Teller & Design)**  
  It MUST also be able to:
  - surface themes about story and characters (e.g., “NPC A is beloved”, “arc B is confusing”),  
  - separate feedback on **Dark World** vs **Human world** narratives,  
  so that Story Teller and designers can adjust narrative plans offline.

- **WS‑2.3 (No Direct Real‑Time Game Control Initially)**  
  In early phases, Website/Social AI SHALL NOT:
  - directly change in‑game state,  
  - trigger events or adjust live tuning parameters.  
  All influence on the game MUST go through human‑validated design/ops changes.

---

## 3. Safety, Moderation & Governance (Non‑Negotiable)

- **WS‑3.1 (Guardrails Integration)**  
  All Website/Social AI operations on user‑generated content MUST be fronted by the existing Guardrails Monitor (or an equivalent safety layer) to filter:
  - hate/harassment,  
  - self‑harm encouragement,  
  - content violating platform policies or game ratings.

- **WS‑3.2 (Human‑in‑the‑Loop Moderation)**  
  The system MUST:
  - allow human moderators to override, approve, or delete AI‑suggested actions,  
  - provide tools for banning or restricting abusive accounts,  
  - expose an emergency “kill switch” to halt AI posting/responding entirely.

- **WS‑3.3 (Audit Logging)**  
  Every AI‑initiated public action (posts, replies, edits) MUST be recorded with:
  - the action content,  
  - rationale/summary (e.g., “clustered as bug report about performance”),  
  - safety decisions made (blocked terms, redactions),  
  - timestamp and model/policy version.

- **WS‑3.4 (Privacy & Identity Separation)**  
  Website/Social AI MUST NOT:
  - automatically link external community identities to in‑game identities without explicit, revocable user consent,  
  - expose private in‑game data (e.g., player’s story state, inventory) in public replies unless the user has opted in and constraints are defined by the user.

---

## 4. Open Questions for Phase 6 (User‑Defined Policy)

The following questions define **policy boundaries** that must be answered before any concrete design or implementation:

1. **Brand Voice & Persona**  
   - How dark, sarcastic, formal, or playful should the AI be?  
   - Are there hard bans (e.g., no dark humor in public, no swearing from AI)?

2. **Scope of Autonomy**  
   - What actions can the AI perform without human review (e.g., simple thank‑you replies, bug‑report acknowledgements)?  
   - What actions must always be queued for approval (e.g., starting new threads, posting memes, announcing changes)?

3. **Depth of Game Integration**  
   - May the AI reference a player’s in‑game achievements or story arc in public replies? Under what consent model?  
   - Should community events (polls, votes) ever drive in‑game changes, or should they remain purely informative?

4. **Platform Priorities & Risk Appetite**  
   - Which platforms are in‑scope (official website, forums, store pages, others)?  
   - How conservative should the AI be on each platform (e.g., more strict on public platforms, more flexible on private community spaces)?

5. **Moderation Authority**  
   - Should AI be allowed to hide or down‑rank content on its own, or only to flag for human review?  
   - What is the escalation path for repeated offenders?

6. **Success Metrics**  
   - How will we measure success (reduced human moderator load, faster bug triage, sentiment improvement, community engagement)?  
   - How will we treat mistakes (AI posting incorrect info, mis‑classifying sarcasm, etc.) in terms of rollback and post‑mortem?

---

## 5. Implementation Status & Constraints

- **WS‑5.1 (Deferred Implementation)**  
  No concrete implementation work (APIs, agents, platform integrations) SHALL begin until:
  - the user answers the questions in §4 during Phase 6, and  
  - a full v1 requirements document is written and approved.

- **WS‑5.2 (Alignment with Core Systems)**  
  When implemented, Website/Social AI MUST:
  - re‑use existing monitoring, logging, and Guardrails infrastructure,  
  - integrate with Ethelred and Story Teller strictly through documented, auditable interfaces.

---

**End of Website / Social AI Requirements (Placeholder v0.2.0)**
```




