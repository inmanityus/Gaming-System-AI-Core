# 🎬 Scene Controllers & Story Constraints - Implementation Plan

**Date**: 2025-11-09  
**Priority**: HIGH  
**Effort**: 2-3 weeks  
**Dependencies**: After Archetype Chains (uses same NPC models)  
**Status**: Ready to implement after Archetype Chains complete

---

## 🎯 OBJECTIVE

Build production system for high-level NPC direction within story constraints.

**User Requirement**:
> "If storyteller wants player to lose battle, enemies DON'T run away"

**Core Principle**: NPCs act autonomously within narrative bounds. Story constraints override personality when needed.

---

## 📋 REQUIREMENTS (From User)

### Must-Have Features:
1. High-level NPC direction in battles/scenes
2. Story-constrained autonomous behavior
3. Personality influences actions BUT story constraints override
4. Example scenarios:
   - Player must lose → enemies stay and fight
   - Player must win → enemies flee at appropriate time
   - NPC must survive → self-preservation overrides aggression
   - NPC must die → removes self-preservation behaviors

---

## 🏗️ ARCHITECTURE DESIGN

### Component 1: Scene Controller Service

**File**: `services/scene_controller/controller.py`

**Responsibilities**:
- Manage active scenes (battles, conversations, quests)
- Apply narrative constraints to NPCs in scene
- Coordinate NPC behavior within scene
- Report scene status to storyteller

**API Endpoints**:
- `POST /api/scene/create` - Create new scene
- `POST /api/scene/{scene_id}/add_npc` - Add NPC to scene
- `POST /api/scene/{scene_id}/set_constraint` - Apply story constraint
- `GET /api/scene/{scene_id}/status` - Get scene status
- `POST /api/scene/{scene_id}/complete` - End scene

**Data Model**:
```python
class Scene:
    scene_id: str
    scene_type: str  # battle, conversation, quest_encounter
    npcs: List[str]  # NPC IDs in scene
    constraints: List[Constraint]
    start_time: datetime
    status: str  # active, paused, complete
    metadata: Dict
```

---

### Component 2: Story Constraint System

**File**: `services/scene_controller/constraints.py`

**Constraint Types**:

#### 1. Outcome Constraints:
```python
class OutcomeConstraint:
    type: str  # "player_must_win", "player_must_lose", "draw"
    strength: float  # 0.0-1.0 (how hard to enforce)
    methods: List[str]  # ["limit_damage", "flee_at_low_health", "call_reinforcements"]
```

#### 2. Behavior Constraints:
```python
class BehaviorConstraint:
    prohibited_actions: List[str]  # ["flee", "surrender", "call_for_help"]
    required_actions: List[str]  # ["attack_player", "defend_position"]
    action_priorities: Dict[str, float]  # Adjust action weights
```

#### 3. Survival Constraints:
```python
class SurvivalConstraint:
    npc_must_survive: bool
    npc_must_die: bool
    death_timing: str  # "early", "mid", "late", "specific_trigger"
    death_method: str  # "combat", "sacrifice", "environmental"
```

#### 4. Participation Constraints:
```python
class ParticipationConstraint:
    must_engage: bool  # NPC must participate in scene
    engagement_level: str  # "aggressive", "defensive", "passive"
    dialogue_required: bool
    min_interactions: int
```

---

### Component 3: Battle Director

**File**: `services/scene_controller/battle_director.py`

**Responsibilities**:
- Orchestrate combat encounters
- Apply win/loss constraints dynamically
- Balance challenge vs. narrative
- Adjust enemy difficulty in real-time

**Key Algorithms**:

#### Dynamic Difficulty Adjustment:
```python
def adjust_enemy_behavior(
    current_player_health: float,
    desired_outcome: str,  # "win", "lose", "close_fight"
    time_remaining: float
) -> BehaviorAdjustment:
    """
    Adjust enemy aggression/accuracy/damage to achieve desired outcome.
    
    Example:
    - Player must lose: Increase enemy accuracy 20-30%
    - Player must win: Decrease enemy damage 15-25%
    - Close fight: Dynamic balance based on health ratio
    """
```

#### Retreat Logic Override:
```python
def should_enemy_retreat(
    npc_id: str,
    npc_health: float,
    personality_suggests_retreat: bool,
    story_constraint: Constraint
) -> bool:
    """
    Determine if enemy should retreat considering story constraints.
    
    Priority:
    1. Story constraint (highest)
    2. Personality trait
    3. Tactical situation
    """
    if story_constraint.prohibits_retreat:
        return False  # Story overrides personality
    
    return personality_suggests_retreat
```

---

### Component 4: NPC Instruction System

**File**: `services/scene_controller/npc_instructions.py`

**High-Level Instructions**:

```python
class NPCInstruction:
    instruction_type: str
    target_npc: str
    priority: int  # 1-10, higher = more important
    overrides_personality: bool
    expires_at: Optional[datetime]
    
# Examples:
INSTRUCTIONS = {
    "be_aggressive_but_dont_kill": {
        "actions": {
            "attack": 0.8,  # High attack rate
            "killing_blow": 0.0  # Never use killing moves
        },
        "overrides": ["mercy", "restraint"]
    },
    "retreat_when_low_health": {
        "triggers": {"health_below": 0.3},
        "actions": {"flee": 1.0},
        "unless": ["story_prohibits_retreat"]
    },
    "defend_location": {
        "actions": {
            "hold_position": 1.0,
            "flee": 0.0
        },
        "overrides": ["self_preservation"]
    }
}
```

---

## 🔗 INTEGRATION WITH EXISTING SYSTEMS

### Integration Point 1: Orchestration Service
**Location**: `services/orchestration/`  
**Current**: 4-layer pipeline (perception → planning → execution → feedback)

**Integration**:
- Add scene context to perception layer
- Check story constraints in planning layer
- Override action selection if constraint violated
- Report constraint adherence to storyteller

**Changes Required**:
```python
# In orchestration pipeline:
def plan_action(npc_id: str, context: Dict) -> Action:
    # Get scene context
    scene = scene_controller.get_active_scene(npc_id)
    
    # Plan action based on personality
    planned_action = personality_model.select_action(npc_id, context)
    
    # Check story constraints
    if scene and scene.has_constraints():
        validated_action = scene.validate_action(planned_action, npc_id)
        if validated_action != planned_action:
            logger.info(f"Story constraint overrode action: {planned_action} → {validated_action}")
            return validated_action
    
    return planned_action
```

---

### Integration Point 2: NPC Behavior System
**Location**: `services/npc_behavior/`

**Integration**:
- Query scene controller before major decisions
- Apply instruction modifiers to action probabilities
- Log constraint violations (for debugging)

---

### Integration Point 3: Storyteller Service
**Location**: `services/storyteller/`, `services/story-teller/`

**Integration**:
- Storyteller creates scenes with constraints
- Monitors scene progress
- Adjusts constraints dynamically based on narrative flow

**New API**:
```python
# Storyteller can modify scene constraints mid-scene
storyteller.update_scene_constraint(
    scene_id="battle_tavern_001",
    new_constraint=OutcomeConstraint(
        type="player_must_escape",  # Changed from "player_must_win"
        strength=0.9,
        methods=["enemies_block_exits"]
    )
)
```

---

## 📊 IMPLEMENTATION PHASES

### Week 1: Foundation & Design
**Days 1-2**: Detailed Design
- [ ] Finalize constraint schema (YAML/JSON)
- [ ] Design scene state machine
- [ ] Define integration points with orchestration
- [ ] Create database schema for scenes

**Days 3-4**: Core Infrastructure
- [ ] Implement Scene class and SceneController
- [ ] Implement Constraint base classes
- [ ] Create scene storage (PostgreSQL + Redis)
- [ ] Basic API endpoints

**Day 5**: Testing
- [ ] Unit tests for constraints
- [ ] Integration tests with mock NPCs
- [ ] Peer review with GPT-5 Pro

---

### Week 2: Battle Director & Instructions
**Days 1-3**: Battle Director
- [ ] Implement dynamic difficulty adjustment
- [ ] Implement retreat logic override
- [ ] Implement reinforcement logic
- [ ] Test with multiple battle scenarios

**Days 4-5**: NPC Instructions
- [ ] Implement instruction parser
- [ ] Create instruction library (common patterns)
- [ ] Test instruction priority system
- [ ] Peer review

---

### Week 3: Integration & Polish
**Days 1-2**: Orchestration Integration
- [ ] Modify orchestration pipeline
- [ ] Add scene context checking
- [ ] Test constraint enforcement

**Days 3-4**: Storyteller Integration
- [ ] Add scene creation API
- [ ] Test dynamic constraint modification
- [ ] End-to-end scenario testing

**Day 5**: Polish & Documentation
- [ ] Performance optimization
- [ ] Complete documentation
- [ ] Demo scenarios
- [ ] Final peer review

---

## 🧪 TESTING STRATEGY (Pairwise Testing Required)

### Test Scenario 1: Player Must Lose Battle
**Setup**:
- 3 vampire NPCs vs player
- Constraint: player_must_lose
- Vampire personality: Strategic, will retreat if losing

**Expected**:
- Vampires fight aggressively
- Vampires DO NOT retreat even at low health
- Player is defeated
- Story constraint logged as enforced

**Success**: Player loses, vampires override retreat personality

---

### Test Scenario 2: NPC Must Survive
**Setup**:
- 1 quest-critical NPC in dangerous battle
- Constraint: npc_must_survive
- NPC personality: Brave (low self-preservation)

**Expected**:
- NPC fights but preserves health
- NPC retreats at 40% health (override brave personality)
- NPC avoids obviously fatal actions
- NPC survives to end of scene

**Success**: NPC survives despite brave personality

---

### Test Scenario 3: Balanced Fight
**Setup**:
- 5 werewolves vs player
- Constraint: close_fight (no outcome preference)
- Werewolves: Pack tactics, aggressive

**Expected**:
- Natural werewolf behavior (pack tactics)
- NO artificial constraint influence
- Outcome determined by actual combat
- Personality drives all decisions

**Success**: Fight feels natural, no visible AI manipulation

---

## 💰 COST & RESOURCES

### Development:
- **Engineers**: 2 engineers × 3 weeks = $30K-50K
- **Testing**: $5K
- **Total**: $35K-55K

### Operational:
- **Scene Controller Service**: +$5/mo (Fargate)
- **Database Storage**: Minimal (scenes are ephemeral)
- **Total**: +$5-10/mo

---

## ✅ SUCCESS CRITERIA

### Functional:
- ✅ Scenes created and managed correctly
- ✅ Constraints applied to all NPCs in scene
- ✅ Story constraints override personality 100% of time
- ✅ Natural behavior when no constraints

### Performance:
- ✅ Constraint checking: <5ms overhead per NPC action
- ✅ Scene coordination: <10ms per NPC
- ✅ Scales to 100 NPCs per scene

### Quality:
- ✅ Player cannot detect AI manipulation
- ✅ Behavior feels natural within constraints
- ✅ No immersion-breaking moments

---

## 📚 RELATED SYSTEMS

### Depends On:
- Archetype Chains (provides NPC personality models)
- Orchestration Service (execution pipeline)
- Storyteller Service (creates scenes/constraints)

### Blocks:
- Nothing (can be added incrementally)

### Enables:
- Narrative-driven combat
- Complex quest scenarios
- Cinematic battle sequences
- Story-critical encounters

---

**Status**: ✅ Plan Complete  
**Ready**: After Archetype Chains (3-4 weeks from now)  
**Priority**: HIGH (essential for Gold-tier narrative)

---

**Created**: 2025-11-09  
**Timeline**: Implement after Archetype Chains MVP  
**Estimated Start**: ~January 2026

