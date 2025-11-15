```markdown
# Story Memory System Requirements

**Date**: November 14, 2025  
**Version**: 2.0.0 (rewritten from scratch)  
**Status**: Phase 2 – Requirements Definition  
**Collaborators (peer models)**: GPT‑5.1, GPT‑5.1‑Codex, Gemini 2.5 Pro, Claude Sonnet 4.5  

---

## 0. Purpose & Scope

- **SM‑0.1 (Purpose)**  
  Define a **Story Memory System (SMS)** that manages long‑term narrative memory for Story Teller and Ethelred, ensuring:
  - coherence of main arcs and Experiences across hundreds of hours,  
  - accurate tracking of player‑specific world state,  
  - early detection and correction of narrative drift.

- **SM‑0.2 (Scope)**  
  SMS covers:
  - data model for per‑player story state,  
  - tracking of main arcs, side arcs, Experiences, relationships, and consequences,  
  - APIs for Story Teller, Ethelred, and other services to query/update story memory,  
  - drift detection metrics and correction recommendations.

---

## 1. Story Domains & Entities

### 1.1 Core Story Domains

- **SM‑1.1.1 (Dark World Arcs)**  
  SMS SHALL model:
  - the 8 Dark World client families (Carrion Kin, Chatter‑Swarm, Stitch‑Guild, Moon‑Clans, Vampiric Houses, Obsidian Synod, Silent Court/Fae, Leviathan Conclave),  
  - the player’s standing, favors, debts, and betrayals with each family,  
  - cross‑family relationships (alliances, conflicts).

- **SM‑1.1.2 (Light World Arcs)**  
  SMS SHALL model:
  - the player’s criminal empire (territories, operations, contacts),  
  - law‑enforcement heat and rival organizations,  
  - the Surgeon vs Butcher morality spectrum (who the player chooses to kill).

- **SM‑1.1.3 (Meta Systems)**  
  SMS SHALL include:
  - **Broker’s Book** state (pages unlocked, rituals known, personality traits),  
  - **Debt of Flesh** death system (deaths, reclaim runs, long‑term penalties),  
  - Experiences (e.g., falling in love, parenthood, addiction arcs).

### 1.2 Story Entities & IDs

- **SM‑1.2.1 (Canonical IDs)**  
  Every story entity MUST have a stable canonical ID:
  - `arc_id` (e.g., `dark.carrion_kin`, `light.crime_empire`),  
  - `quest_id`, `experience_id`,  
  - `npc_id`, `location_id`, etc.

- **SM‑1.2.2 (Tagging Requirements)**  
  Content in quest/story data MUST be tagged with:
  - `arc_role` (`main_arc`, `side_arc`, `experience`, `ambient`),  
  - `themes` (love, addiction, betrayal, etc.),  
  to support SMS indexing and Ethelred drift analysis.

---

## 2. Story Memory Architecture

### 2.1 Multi‑Layer Memory Model

- **SM‑2.1.1 (Per‑Player Story State Store)**  
  SMS SHALL maintain a structured per‑player story state including:
  - progress markers for each main arc and major side arcs,  
  - list of active and completed quests/Experiences,  
  - key decisions and their consequences,  
  - relationship scores and flags per key NPC/faction,  
  - current state of Broker’s Book and Debt of Flesh.

- **SM‑2.1.2 (Performance Tiers)**  
  Implementation SHOULD follow a tiered storage pattern (conceptual requirement):
  - fast cache (e.g., Redis / in‑memory) for recent sessions,  
  - durable store (PostgreSQL) for full history and analytics,  
  with clear guarantees that **read paths for Story Teller and Ethelred do not block on slow queries**.

### 2.2 Data Model Requirements

- **SM‑2.2.1 (Arc Progress Model)**  
  For each `arc_id`, store:
  - discrete `progress_state` (e.g., `not_started`, `early`, `mid`, `late`, `completed`),  
  - last significant `beat_id` reached,  
  - `last_update_at` timestamp.

- **SM‑2.2.2 (Decision Log)**  
  Maintain a compact log of **key decisions**:
  - `decision_id`, `arc_id`, `npc_id?`,  
  - `choice_label`, `outcome_tags` (mercy/cruelty, loyalty/betrayal, etc.),  
  - `timestamp`, optional numeric weights (used by moral alignment systems).

- **SM‑2.2.3 (Relationship Model)**  
  For each important NPC / faction, store:
  - `relationship_score` (bounded float or int),  
  - flags (e.g., `trusted`, `betrayed`, `oath_broken`),  
  - last interaction summary (short descriptor or ID).

---

## 3. APIs & Integration Points

### 3.1 Story Teller Integration

- **SM‑3.1.1 (Read API)**  
  Story Teller MUST be able to query SMS via:
  - “get story snapshot for player” (complete but compact view),  
  - “get arc summary” (for specific `arc_id`),  
  - “get NPC relationship summary” (per `npc_id`).

- **SM‑3.1.2 (Write API)**  
  Story Teller and quest systems MUST:
  - notify SMS when significant events occur (`arc_beat_reached`, `quest_completed`, `relationship_shift`),  
  - send **minimal structured messages**, not free‑form text, to keep memory compact and reliable.

### 3.2 Ethelred Integration

- **SM‑3.2.1 (Story Snapshot for QA)**  
  Ethelred SHALL be able to:
  - retrieve summarized story state for any QA session (AI Player or real player),  
  - use the snapshot to compute **drift metrics** (e.g., time since last main‑arc beat).

- **SM‑3.2.2 (Drift & Conflict Events)**  
  SMS SHALL expose events for Ethelred:
  - `STORY.CONFLICT_ALERT` – e.g., NPC dead vs alive contradiction,  
  - `STORY.DRIFT_SCORE` – numeric measure capturing deviation from balanced arc engagement.

### 3.3 Other Services

- **SM‑3.3.1 (State Manager & World State)**  
  SMS MUST integrate with State Manager / World State:
  - cross‑validating story memory against world facts (e.g., flags for destroyed locations),  
  - ensuring world changes triggered by story events are represented consistently.

---

## 4. Drift Detection Requirements

### 4.1 Time & Attention Metrics

- **SM‑4.1.1 (Time Budget Tracking)**  
  SMS SHALL track, per session and per player:
  - time spent advancing main arcs,  
  - time spent in side arcs, categorized by theme,  
  - time in ambient/non‑narrative activities.

- **SM‑4.1.2 (Golden Path Health)**  
  For each main arc, compute:
  - average time between significant beats,  
  - number of sessions since last main‑arc progression;  
  values exceeding configured thresholds MUST trigger drift flags.

### 4.2 Content Mix & Genre Drift

- **SM‑4.2.1 (Genre Alignment Metrics)**  
  Using arc/experience tags, compute per player and per cohort:
  - percentage of recent time in horror‑aligned content vs non‑horror content,  
  - dominance of non‑thematic activities (e.g., repeated non‑horror mini‑games).

- **SM‑4.2.2 (Drift Conditions)**  
  Conditions that MUST trigger a `STORY.DRIFT` event:
  - no main‑arc progress for N hours of play while side content loops repeat,  
  - majority of recent play time in content tagged as non‑horror for a horror‑focused profile.

### 4.3 Narrative Incoherence

- **SM‑4.3.1 (State Conflict Detection)**  
  SMS SHALL continuously cross‑check:
  - story memory vs world state (e.g., `npc_status = dead` vs appearing as quest giver),  
  - arc flags vs available quests (e.g., offering the same introduction multiple times).

- **SM‑4.3.2 (Consistency Events)**  
  When inconsistency is detected, emit `STORY.CONFLICT_ALERT` including:
  - involved IDs (NPC, quest, location),  
  - conflicting flags,  
  - first occurrence time,  
  - recommended remediation notes for designers.

---

## 5. Correction Strategies & Controls

### 5.1 Soft-Steering Recommendations

- **SM‑5.1.1 (Non‑Intrusive Nudges)**  
  For drift events, SMS/Ethelred SHALL provide recommended **soft nudges** such as:
  - spawn or schedule NPCs who remind the player of unresolved core arcs,  
  - inject hints or environmental cues pointing back to main storyline.

### 5.2 Medium Constraints

- **SM‑5.2.1 (Content Availability Adjustments)**  
  For sustained drift, SMS MAY recommend:
  - reducing frequency/availability of low‑value side activities,  
  - prioritizing spawn/offer of main‑arc opportunities once player exits current loop.

### 5.3 QA‑Only Hard Constraints

- **SM‑5.3.1 (Development Guardrails)**  
  In QA/dev builds, SMS SHALL:
  - flag content definitions that are untagged or mis‑tagged,  
  - warn when new systems introduce long sequences of off‑genre content without narrative justification,  
  enabling designers to correct drift before release.

---

## 6. Observability, Dashboards & Testing

### 6.1 Observability

- **SM‑6.1.1 (Story Dashboards)**  
  Provide dashboards that show:
  - arc completion distributions,  
  - time allocation across arcs/Experiences,  
  - drift/conflict events per build and environment.

- **SM‑6.1.2 (Audit Logs)**  
  Record:
  - all major story state transitions,  
  - all drift/conflict detections and corresponding corrections applied in QA,  
  enabling post‑mortems and regression analysis.

### 6.2 Testing

- **SM‑6.2.1 (Unit & Scenario Tests)**  
  SMS MUST have tests that:
  - verify correct story state updates given scripted quest completions and decisions,  
  - cover edge cases (branch reversals, retcons, resets).

- **SM‑6.2.2 (Golden Narrative Scenarios)**  
  Define golden playthroughs (AI Player scripts or recorded sessions) with known narrative outcomes. Ethelred + SMS MUST reproduce:
  - expected arc progress states,  
  - no false drift/conflict flags,  
  and MUST flag deliberate injected inconsistencies in adversarial scenarios.

---

**End of Story Memory System Requirements v2.0.0**
```
**Must Track**:
- Times died
- Soul-Echo encounters
- Corpse-Tender interactions
- Debts owed to Dark World

---

## 3. ALLOWED SIDE CONTENT

### 3.1 Experiences System

#### 3.1.1 What are Experiences?
**From Narrative Docs**: Major life events that can be replayed through Story Teller

**Examples**:
- Falling in love
- Becoming a parent
- Overcoming addiction
- Historical battles
- Dungeon diving
- Alternate reality portals

#### 3.1.2 Tracking Requirements
**Must Track**:
- Which Experiences player has completed
- Emotional impact of each Experience
- How Experiences influenced player's main story choices
- Cross-Experience connections (falling in love in one, losing them in another)

**CRITICAL**: Experiences are VERY IMPORTANT but must not become the main focus.

### 3.2 Side Quests from Clients

**Must Track**:
- Active side quests
- Completed side quests
- Failed side quests
- Quest chains (multi-part stories)

### 3.3 Local Challenges

**Must Track**:
- Environmental challenges (e.g., "Clear the abandoned hospital")
- Mini-games (e.g., Negotiation mini-game with vampires)
- Collectibles and lore items

---

## 4. DRIFT PREVENTION REQUIREMENTS

### 4.1 Off-Rails Example: Race Car Simulator

#### 4.1.1 The Problem
**Scenario**: Player does car chase side quest. Enjoys driving. Story Teller starts generating more driving content. Eventually, game focuses on racing instead of body brokering.

**This is DRIFT.**

#### 4.1.2 The Solution
**Detection**:
- Track time allocation across activity types
- If "Driving" >20% of playtime AND no main quest progress in 2 hours → flag drift

**Correction**:
- Story Teller receives memory reminder: "Core game loop: Kill → Harvest → Negotiate → Get Drugs → Build Empire"
- Soft steering: Reduce driving quest generation, increase body-brokering opportunities

### 4.2 Detection Methods

#### 4.2.1 Quest Categorization
**Classify Every Quest**:
- **Main Story**: Directly advances Dark World or Light World plotlines
- **Experience**: Major life event (falling in love, etc.)
- **Side Quest**: Client requests, local challenges
- **Tangential**: Fun but off-theme (racing, fishing, etc.)

**Alert Threshold**:
- If Tangential >30% of recent quests → drift warning

#### 4.2.2 Time Allocation Analysis
**Track Per Activity Type**:
- Body harvesting
- Negotiation with clients
- Empire management
- Combat
- Exploration
- Social/NPC interactions
- Off-theme activities

**Alert Threshold**:
- If any off-theme activity >25% for >3 sessions → drift warning

#### 4.2.3 Self-Assessment by Story Teller
**Periodic Check** (every 10 gameplay hours):
1. Story Teller reviews last 10 hours of generated content
2. Answers: "Is this consistent with game's core theme?"
3. If answer is "No" more than 20% → drift flagged

### 4.3 Correction Mechanisms

#### 4.3.1 Hard Block (Rare, Extreme Cases Only)
**When**: Drift is severe (>50% off-theme content)
**Action**: Disable generation of certain content types
**Example**: "No more racing quests can be generated until main quest progress"
**Risk**: Feels restrictive, breaks immersion

#### 4.3.2 Soft Steering (Preferred)
**When**: Mild to moderate drift (<50%)
**Action**: Adjust generation probabilities
**Example**: Increase main quest opportunities, decrease off-theme generation
**Benefit**: Feels natural, preserves player agency

#### 4.3.3 Memory Reminder (Most Common)
**When**: Story Teller generating next content
**Action**: Include context in Story Teller's prompt
**Example**: 
```
MEMORY CONTEXT:
- Core theme: Body brokering in dark fantasy world
- Player's main goals: Build empire, trade with Dark World
- Recent drift: Player spent 3 hours racing cars
- Correction: Steer back to core gameplay
```
**Benefit**: Non-intrusive, Story Teller self-corrects

---

## 5. ARCHITECTURE DECISION: SEPARATE SERVICE

### 5.1 Recommended: Story Memory Service (Separate Microservice)

#### 5.1.1 Rationale (from GPT-5.1-Codex)
**Pros**:
- Independent scaling (memory operations may be heavy)
- Language-model agnostic (can serve multiple Story Teller instances)
- Clear separation of concerns
- Can serve other services (Quest System, NPC Behavior)

**Cons**:
- Additional operational overhead
- Network latency (mitigated by caching)

#### 5.1.2 Service Name
`services/story_memory/`

#### 5.1.3 Technology Stack
- **Language**: Python 3.11+ (matches other services)
- **Framework**: FastAPI (matches Model Management)
- **Database**: PostgreSQL for structured data + pgvector for semantic search
- **Cache**: Redis (shared with other services)
- **Messaging**: NATS (existing infrastructure)

### 5.2 Alternative: Embedded Module (NOT Recommended)

**Cons**:
- Tight coupling with Story Teller
- Scaling difficulty
- Cannot serve other services
- Harder to maintain

**Only if**: Story Memory operations are extremely lightweight AND never needed by other services.

---

## 6. DATA STORAGE REQUIREMENTS

### 6.1 Primary Store: PostgreSQL

#### 6.1.1 Story Memories Table
```sql
CREATE TABLE story_memories (
  memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(session_id),
  player_id UUID NOT NULL,
  
  -- Sequence for ordering
  sequence INT NOT NULL,
  
  -- Memory classification
  memory_type TEXT NOT NULL CHECK (memory_type IN (
    'fact',           -- Objective truth (player killed Boss X)
    'character',      -- NPC state, relationships
    'quest',          -- Quest progress, outcomes
    'world_state',    -- World changes (territory conquered)
    'experience',     -- Major life events
    'theme_marker'    -- Content type tracking (for drift detection)
  )),
  
  -- Content
  content TEXT NOT NULL, -- Human-readable summary
  embedding VECTOR(1536), -- For semantic search (pgvector)
  
  -- Importance weighting
  importance FLOAT NOT NULL DEFAULT 0.5 CHECK (importance BETWEEN 0 AND 1),
  -- 0.0 = trivial, 0.5 = normal, 1.0 = critical
  
  -- Usage tracking
  last_referenced TIMESTAMPTZ,
  reference_count INT DEFAULT 0,
  
  -- Drift detection
  drift_score FLOAT DEFAULT 0,
  -- 0.0 = perfectly on-theme, 1.0 = completely off-theme
  
  -- System
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_memory_session ON story_memories(session_id);
CREATE INDEX idx_memory_type ON story_memories(memory_type);
CREATE INDEX idx_memory_importance ON story_memories(importance DESC);
CREATE INDEX idx_memory_sequence ON story_memories(session_id, sequence);
```

#### 6.1.2 Canonical Lore Table
```sql
CREATE TABLE lore_baselines (
  lore_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category TEXT NOT NULL, -- 'dark_world', 'light_world', 'experience', 'archetype'
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  importance FLOAT NOT NULL DEFAULT 0.8,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_lore_category ON lore_baselines(category);
```

#### 6.1.3 Drift Alerts Table
```sql
CREATE TABLE drift_alerts (
  alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  
  -- What drifted
  drift_type TEXT NOT NULL, -- 'quest_allocation', 'time_allocation', 'theme_consistency'
  severity TEXT NOT NULL CHECK (severity IN ('minor', 'moderate', 'major')),
  
  -- Details
  description TEXT NOT NULL,
  metrics JSONB, -- Specific metrics that triggered alert
  
  -- Recommended action
  recommended_correction TEXT,
  
  -- Status
  acknowledged BOOLEAN DEFAULT false,
  corrective_action_taken TEXT,
  
  -- System
  detected_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_drift_session ON drift_alerts(session_id);
CREATE INDEX idx_drift_severity ON drift_alerts(severity);
```

### 6.2 Vector Store: pgvector Extension

#### 6.2.1 Why pgvector?
- **Simplicity**: PostgreSQL extension, no separate service
- **Performance**: Efficient for <10M vectors
- **Integration**: Same database as structured data

#### 6.2.2 Semantic Search Queries
```sql
-- Find top-8 most relevant memories for context
SELECT memory_id, content, importance
FROM story_memories
WHERE session_id = $1
ORDER BY embedding <=> $2  -- Cosine distance to query embedding
LIMIT 8;
```

### 6.3 Cold Archive: S3 (JSONL Snapshots)

#### 6.3.1 Daily Snapshots
**Schedule**: Every 24 hours  
**Format**: JSONL (one JSON object per line)  
**Retention**: 90 days (Glacier after)

**Filename**: `story-memories/{session_id}/snapshot-{date}.jsonl`

---

## 7. API CONTRACTS

### 7.1 Add Memory

```
POST /memory/sessions/{session_id}
Authorization: Bearer <service_token>

Request:
{
  "memory_type": "fact",
  "content": "Player killed Vampire Lord Valdris in single combat",
  "importance": 0.9,
  "drift_score": 0.1  // Low drift (combat is on-theme)
}

Response:
{
  "memory_id": "uuid",
  "sequence": 1523,
  "created_at": "2025-11-14T12:00:00Z"
}
```

### 7.2 Retrieve Memories (Hybrid Query)

```
GET /memory/sessions/{session_id}?topK=8&context=vampire+negotiation
Authorization: Bearer <service_token>

Response:
{
  "memories": [
    {
      "memory_id": "uuid",
      "content": "Player killed Vampire Lord Valdris in single combat",
      "importance": 0.9,
      "last_referenced": "2025-11-14T11:55:00Z",
      "relevance_score": 0.95  // Semantic similarity to query
    },
    // ... 7 more
  ],
  "drift_warning": null  // or drift alert if detected
}
```

### 7.3 Drift Check

```
POST /memory/sessions/{session_id}/drift-check
Authorization: Bearer <service_token>

Request:
{
  "recent_window_hours": 3,  // Check last 3 hours
  "check_types": ["quest_allocation", "time_allocation", "theme_consistency"]
}

Response:
{
  "drift_detected": true,
  "drift_score": 0.35,  // 0.0 = on-theme, 1.0 = off-theme
  "severity": "moderate",
  "details": {
    "quest_allocation": {
      "main_story": 0.2,    // 20% of quests were main story
      "experience": 0.1,    // 10% were Experiences
      "side_quest": 0.3,    // 30% were side quests
      "tangential": 0.4     // 40% were off-theme! ⚠️
    },
    "time_allocation": {
      "body_harvesting": 0.15,
      "negotiation": 0.10,
      "racing": 0.45,  // ⚠️ Too much racing!
      "combat": 0.20,
      "exploration": 0.10
    }
  },
  "recommended_remediation": "Increase main quest opportunities. Reduce racing content generation.",
  "canonical_theme_reminder": "Core loop: Kill → Harvest → Negotiate → Get Drugs → Build Empire"
}
```

### 7.4 Consolidate Memories (Background Job)

```
POST /memory/sessions/{session_id}/consolidate
Authorization: Bearer <service_token>

Request:
{
  "consolidation_type": "importance_reweighting"  // or "summarization", "pruning"
}

Response:
{
  "job_id": "uuid",
  "status": "queued"
}

GET /memory/jobs/{job_id}
Response:
{
  "status": "completed",
  "memories_consolidated": 142,
  "memories_pruned": 23,
  "completed_at": "2025-11-14T12:05:00Z"
}
```

---

## 8. QUERY PATTERNS

### 8.1 Real-Time Retrieval (Story Teller Turn)

**Frequency**: Every Story Teller turn (~100 concurrent sessions)  
**Query**: Top-8 memories relevant to current context  
**Latency SLA**: <50ms P99

**Example Flow**:
1. Story Teller about to generate vampire negotiation dialogue
2. Sends query: "vampire negotiation + Valdris + blood pact"
3. Story Memory returns top-8 relevant memories (hybrid: semantic + recency)
4. Story Teller includes memories in prompt context
5. Generates contextually aware dialogue

**Optimization**:
- Cache hot memories in Redis (5-minute TTL)
- Pre-fetch common queries
- Index on session_id + embedding

### 8.2 Batch Consolidation (After Each Chapter)

**Frequency**: Asynchronous, after major story beats  
**Purpose**: Importance reweighting, memory pruning, summarization

**Process**:
1. Identify chapter completion (quest flag, time threshold, or explicit)
2. Trigger consolidation job
3. Reweight memories based on reference count and importance
4. Prune low-importance, unreferenced memories (<0.2 importance, 0 references, >7 days old)
5. Summarize clusters of related memories
6. Update drift scores based on recent patterns

### 8.3 Drift Detection (Periodic)

**Frequency**: Every 30 minutes OR after every 10 quests  
**Purpose**: Detect theme drift before it becomes severe

**Process**:
1. Analyze last N hours of memories
2. Calculate quest allocation distribution
3. Calculate time allocation distribution
4. Compare against canonical theme (lore baselines)
5. If drift score >0.3 → emit NATS event `story.drift.alert`
6. Guardrails Monitor and Story Teller subscribe to this event

---

## 9. DRIFT DETECTION ALGORITHMS

### 9.1 Quest Allocation Analysis

```python
def analyze_quest_allocation(session_id: str, window_hours: int) -> dict:
    """
    Analyze distribution of quest types in recent gameplay.
    
    Returns:
        {
            'main_story': 0.25,      # 25% of quests were main story
            'experience': 0.15,      # 15% were Experiences
            'side_quest': 0.40,      # 40% were side quests
            'tangential': 0.20,      # 20% were off-theme
            'drift_score': 0.20      # Overall drift (0-1)
        }
    """
    memories = get_memories_by_type(session_id, 'quest', window_hours)
    
    categories = {
        'main_story': 0,
        'experience': 0,
        'side_quest': 0,
        'tangential': 0
    }
    
    for memory in memories:
        category = classify_quest(memory.content)
        categories[category] += 1
    
    total = sum(categories.values())
    distribution = {k: v/total for k, v in categories.items()}
    
    # Drift score: Tangential content is drift
    distribution['drift_score'] = distribution['tangential']
    
    return distribution
```

### 9.2 Theme Consistency Check

```python
def check_theme_consistency(session_id: str, window_hours: int) -> dict:
    """
    Compare recent memories against canonical lore using semantic similarity.
    
    Returns:
        {
            'consistency_score': 0.75,  # 0-1, higher = more consistent
            'drift_score': 0.25,        # 1 - consistency_score
            'outlier_memories': [...]    # Memories far from canonical lore
        }
    """
    recent_memories = get_memories(session_id, window_hours)
    canonical_lore = get_lore_baselines(category='dark_world')
    
    similarities = []
    outliers = []
    
    for memory in recent_memories:
        # Find most similar canonical lore
        max_similarity = max(
            cosine_similarity(memory.embedding, lore.embedding)
            for lore in canonical_lore
        )
        similarities.append(max_similarity)
        
        if max_similarity < 0.5:  # Low similarity = outlier
            outliers.append(memory)
    
    consistency_score = np.mean(similarities)
    
    return {
        'consistency_score': consistency_score,
        'drift_score': 1 - consistency_score,
        'outlier_memories': outliers
    }
```

### 9.3 Time Allocation Analysis

```python
def analyze_time_allocation(session_id: str, window_hours: int) -> dict:
    """
    Track time spent in different activity types.
    
    Returns:
        {
            'body_harvesting': 0.20,  # 20% of time
            'negotiation': 0.15,
            'empire_management': 0.10,
            'combat': 0.25,
            'exploration': 0.15,
            'racing': 0.10,  # Off-theme
            'other': 0.05,
            'drift_score': 0.15  # Sum of off-theme activities
        }
    """
    memories = get_memories_by_type(session_id, 'theme_marker', window_hours)
    
    activities = defaultdict(float)
    
    for memory in memories:
        # Memory content: "activity=racing duration=600"
        activity, duration = parse_theme_marker(memory.content)
        activities[activity] += duration
    
    total_time = sum(activities.values())
    distribution = {k: v/total_time for k, v in activities.items()}
    
    # Define off-theme activities
    OFF_THEME = ['racing', 'fishing', 'gambling', 'sports']
    drift_score = sum(distribution.get(act, 0) for act in OFF_THEME)
    
    distribution['drift_score'] = drift_score
    
    return distribution
```

---

## 10. PERFORMANCE REQUIREMENTS

### 10.1 Latency

- **Real-Time Retrieval**: <50ms P99 (top-8 memories)
- **Drift Check**: <500ms (background, not blocking)
- **Consolidation**: Async, complete within 5 minutes

### 10.2 Throughput

- **100 Concurrent Sessions**: Each requests memories 2x per minute
- **Total**: ~200 queries/second
- **Scaling**: 3 ECS tasks (r6g.large)

### 10.3 Storage

- **Per Memory**: ~7 KB (1 KB text + 6 KB embedding)
- **Per Session**: ~10,000 memories over 100 hours of gameplay
- **Total**: 70 MB per session
- **For 1M Players**: 70 TB (PostgreSQL + backups + S3 archive)

### 10.4 Cache Strategy

#### 10.4.1 Redis Hot Cache
- **TTL**: 5 minutes
- **Contents**: Most recently accessed memories
- **Hit Rate Target**: >80%

#### 10.4.2 PostgreSQL Read Replica
- **Purpose**: Separate read traffic from writes
- **Replication Lag**: <1 second acceptable

---

## 11. INTEGRATION POINTS

### 11.1 Story Teller Service

**Use Case**: Retrieve relevant memories before generating content

```python
# In Story Teller Service
async def generate_vampire_dialogue(session_id: str, context: str):
    # Fetch relevant memories
    memories = await story_memory_client.get_memories(
        session_id=session_id,
        context=f"vampire negotiation {context}",
        top_k=8
    )
    
    # Include in prompt
    prompt = f"""
    RELEVANT MEMORIES:
    {format_memories(memories)}
    
    Generate vampire dialogue for: {context}
    """
    
    response = await llm.generate(prompt)
    
    # Store new memory
    await story_memory_client.add_memory(
        session_id=session_id,
        memory_type='character',
        content=f"Vampire dialogue: {response[:200]}",
        importance=0.6
    )
```

### 11.2 Quest System Service

**Use Case**: Check quest allocation before generating new quest

```python
# In Quest System Service
async def generate_quest(session_id: str):
    # Check for drift
    drift_check = await story_memory_client.drift_check(
        session_id=session_id,
        recent_window_hours=3
    )
    
    if drift_check['drift_detected'] and drift_check['severity'] == 'major':
        # Force main quest
        quest_type = 'main_story'
    else:
        # Normal probability distribution
        quest_type = weighted_random(['main_story', 'side_quest', 'tangential'])
    
    quest = generate_quest_by_type(quest_type)
    
    # Log quest
    await story_memory_client.add_memory(
        session_id=session_id,
        memory_type='quest',
        content=f"Generated {quest_type} quest: {quest.title}",
        drift_score=calculate_drift_score(quest_type)
    )
```

### 11.3 Guardrails Monitor

**Subscribe to Drift Alerts**:

```python
# In Guardrails Monitor
async def handle_drift_alert(message: dict):
    session_id = message['session_id']
    severity = message['severity']
    
    if severity == 'major':
        # Hard intervention: block off-theme content generation
        await set_content_restriction(session_id, 'tangential_quests', blocked=True)
        
        # Notify Story Teller
        await nats_publish('story.correction.required', {
            'session_id': session_id,
            'message': message['recommended_correction']
        })
```

---

## 12. MONITORING & ALERTS

### 12.1 Metrics to Track

- **Query Latency**: P50, P95, P99 for memory retrieval
- **Drift Alert Rate**: Alerts per session per hour
- **Memory Growth**: Memories created per session per hour
- **Cache Hit Rate**: Redis cache effectiveness
- **Drift Severity Distribution**: Minor vs Moderate vs Major

### 12.2 Alerts

- **High Latency**: P99 >50ms for >5 minutes
- **Severe Drift**: 3+ Major drift alerts in 10 minutes for same session
- **Storage Growth**: Memory table growing >10% per day
- **Cache Miss Rate**: <70% hit rate

---

## 13. SUCCESS CRITERIA

### 13.1 Functionality
- ✅ Story Memory Service operational
- ✅ Story Teller retrieves memories successfully
- ✅ Drift detection alerts fire appropriately
- ✅ Corrections (soft steering, memory reminders) applied

### 13.2 Performance
- ✅ <50ms P99 memory retrieval latency
- ✅ >80% Redis cache hit rate
- ✅ <500ms drift check latency

### 13.3 Quality
- ✅ <5% false positive drift alerts
- ✅ Drift corrected within 2 hours of detection
- ✅ Story coherence maintained across 100+ hour gameplay
- ✅ NO "race car simulator" drift in playtesting

---

**Next Phase**: Solutions (Design memory architecture & drift algorithms)  
**Document Status**: Complete for peer review

