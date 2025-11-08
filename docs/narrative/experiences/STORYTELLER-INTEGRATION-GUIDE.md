# Storyteller Integration Guide - Experiences System

**Version:** 1.0.0  
**Last Updated:** 2025-11-08  
**Target Audience:** Storyteller AI, System Architects  
**Status:** Implementation Guide  

---

## Purpose of This Guide

This document provides the Storyteller AI with comprehensive instructions on:
1. **Understanding** the Experiences System conceptually
2. **Selecting** appropriate experiences for player context
3. **Integrating** experiences into narrative flow
4. **Balancing** experience frequency and variety
5. **Utilizing** automation APIs effectively

---

## Core Concept for Storyteller

### What Are Experiences?

Think of experiences as **temporary side quests with unique gameplay**. They are NOT:
- Permanent world changes
- Required story progression
- Generic encounters

They ARE:
- Self-contained adventures
- Optional (mostly) content
- Reward-driven mini-games
- Variety generators

### Why Use Experiences?

**Player Engagement:**
- Combat monotony and repetition
- Provide unexpected surprises
- Offer skill-based challenges
- Reward exploration and curiosity

**Narrative Tools:**
- Deliver backstory through historical battles
- Explore character psychology via dream realms
- Test player morality through choices
- Provide world-building through alternate realities

**Progression Systems:**
- Gate powerful rewards behind challenges
- Offer optional difficulty for advanced players
- Create memorable "hero moments"
- Build player reputation and achievements

---

## Decision Framework: When to Use Experiences

### Player State Analysis

Before spawning an experience, evaluate:

#### **1. Player Level & Power**
```yaml
if player.level < 5:
  # Too early for most experiences
  available_experiences = []
  
elif player.level 5-15:
  # Early game experiences
  available_experiences = [
    "DungeonDiving-Simple",
    "ArenaCombat-Basic",
    "PuzzleLabyrinths-Easy"
  ]
  
elif player.level 15-30:
  # Mid-game experiences
  available_experiences = [
    "AlternateRealityPortals",
    "HistoricalBattles-Ancient",
    "SurvivalChallenges-Standard"
  ]
  
elif player.level 30+:
  # End-game experiences
  available_experiences = [
    "BossGauntlets-Legendary",
    "TowerAscension-Hard",
    "HistoricalBattles-Modern"
  ]
```

#### **2. Recent Activity**
```python
def check_experience_cooldown(player_id):
    last_experience_time = get_last_experience_timestamp(player_id)
    time_since = current_time() - last_experience_time
    
    if time_since < 30_minutes:
        # Too soon, player needs main world time
        return False, "Cooldown active"
    elif time_since < 2_hours:
        # Okay for optional discovery
        return True, "Optional spawn"
    else:
        # Prime time for experience
        return True, "Recommended spawn"
```

#### **3. Narrative Context**
```python
def select_narrative_appropriate_experience(story_arc, location, player_state):
    """
    Match experience to current story context.
    """
    
    # Example: Player investigating ancient ruins
    if story_arc == "AncientMystery" and location.type == "Ruins":
        return [
            "AlternateRealityPortals-AncientCivilization",
            "HistoricalBattles-AncientEra",
            "PuzzleLabyrinths-TempleRiddles"
        ]
    
    # Example: Player in modern city
    elif location.type == "ModernCity":
        return [
            "UrbanWarfare-GangTerritory",
            "StealthInfiltration-CorporateHeist",
            "RacingVehicular-StreetRacing"
        ]
    
    # Example: Player near water
    elif location.has_feature("Water") or location.type == "Coast":
        return [
            "UnderwaterExpeditions-SunkenRuins",
            "AlternateRealityPortals-OceanicRealm"
        ]
```

#### **4. Player Preferences (Learned)**
```python
def get_player_preference_weights(player_id):
    """
    Track player behavior to learn preferences.
    """
    stats = get_player_experience_stats(player_id)
    
    preferences = {
        "combat_heavy": stats["combat_completion_rate"],
        "puzzle_focus": stats["puzzle_completion_rate"],
        "exploration": stats["exploration_time_ratio"],
        "solo_play": stats["solo_vs_group_ratio"],
        "difficulty_preference": stats["average_difficulty_selected"]
    }
    
    return preferences
```

---

## Experience Selection Algorithm

### Step-by-Step Process

```python
def select_experience_for_player(player):
    """
    Storyteller's main experience selection function.
    """
    
    # Step 1: Get available experience types
    available = filter_by_player_level(ALL_EXPERIENCE_TYPES, player.level)
    
    # Step 2: Filter by narrative appropriateness
    narratively_appropriate = filter_by_narrative_context(
        available, 
        player.current_story_arc,
        player.location
    )
    
    # Step 3: Check cooldowns and frequency
    not_oversaturated = filter_by_frequency(
        narratively_appropriate,
        player.experience_history
    )
    
    # Step 4: Apply player preference weights
    weighted = apply_preference_weights(
        not_oversaturated,
        player.learned_preferences
    )
    
    # Step 5: Select final experience
    selected = weighted_random_choice(weighted)
    
    # Step 6: Determine variant and difficulty
    variant = select_variant(selected, player)
    difficulty = recommend_difficulty(player)
    
    return {
        "experience_type": selected,
        "variant": variant,
        "difficulty": difficulty,
        "entry_mechanism": determine_entry_type(player, selected)
    }
```

---

## Entry Mechanism Selection

### When to Use Each Type

#### **Forced (5% of experiences)**
**Use When:**
- Critical story moment demands it
- Player has repeatedly ignored optional portals
- Dramatic narrative beat requires shock
- Tutorial/introduction to new experience type

**Example:**
```python
if player.ignored_portal_count > 5:
    # Player not engaging with optional content
    # Force them into an easy experience to show value
    return {
        "entry": "forced",
        "experience": "ArenaCombat-Tutorial",
        "narrative": "A magical vortex suddenly appears and pulls you in!"
    }
```

#### **Optional (70% of experiences)**
**Use When:**
- Normal gameplay flow
- Player is exploring naturally
- No immediate narrative pressure
- Rewarding curious players

**Discovery Methods:**
- Glowing portals in wilderness
- Mysterious doors in dungeons
- NPC rumors about locations
- Map markers (optional content)

#### **Quest-Based (25% of experiences)**
**Use When:**
- Integrating into storyline
- NPC requests assistance
- Faction missions
- Tutorial/guided introduction

**Quest Integration:**
```yaml
Quest: "Clear the Goblin Warren"
  - NPC: Village Elder
  - Location: Forest cave entrance
  - Experience: DungeonDiving-GoblinWarren
  - Difficulty: Scaled to player level
  - Rewards: Quest rewards + dungeon loot
  - Narrative: Village plagued by goblin raids
```

---

## Frequency Balancing

### Recommended Frequency by Type

| Experience Type | Frequency | Reason |
|-----------------|-----------|--------|
| Dungeon Diving | High | Core gameplay loop |
| Arena Combat | High | Quick, repeatable |
| Alternate Reality Portals | Medium | Special, not overused |
| Historical Battles | Low | Epic, memorable events |
| Stealth Infiltration | Medium | Varies gameplay |
| Survival Challenges | Low | Intense, draining |
| Puzzle Labyrinths | Medium | Mental break from combat |
| Boss Gauntlets | Low | High difficulty, special |
| Racing & Vehicular | Medium | Fun diversion |
| Urban Warfare | Medium | Specific context needed |
| Underwater Expeditions | Low | Unique environments |
| Desert Wasteland | Medium | Thematic |
| Ethereal Realms | Low | Surreal, special moments |
| Tower Ascension | Very Low | Extended challenge |

### Daily Experience Budget

```python
def calculate_daily_experience_allowance(player_session_length):
    """
    Determine how many experiences per play session.
    """
    if player_session_length < 1_hour:
        return 0-1  # Short session, maybe one quick experience
    
    elif player_session_length 1-3_hours:
        return 1-3  # Normal session, a few experiences
    
    elif player_session_length > 3_hours:
        return 3-6  # Long session, multiple experiences
    
    # Never exceed: 1 experience per 30-45 minutes of gameplay
```

---

## Narrative Integration Patterns

### Pattern 1: Lore Delivery
**Use Case:** Teach players about world history

```yaml
Scenario: Player discovers ancient obelisk
  - Trigger: Touch obelisk
  - Experience: AlternateRealityPortals-AncientCivilization
  - Purpose: Show civilization at its peak
  - Reward: Knowledge codex, artifacts
  - Narrative Outcome: Player understands why civilization fell
```

### Pattern 2: Character Development
**Use Case:** Explore character's past or psyche

```yaml
Scenario: Player sleeps at inn
  - Trigger: Sleep action
  - Experience: EtherealRealms-DreamWorld
  - Purpose: Character confronts trauma/memory
  - Reward: Psychological growth, ability unlock
  - Narrative Outcome: Character arc progression
```

### Pattern 3: Moral Choice
**Use Case:** Test player ethics

```yaml
Scenario: Player encounters time portal
  - Trigger: Portal discovery
  - Experience: HistoricalBattles-MoralDilemma
  - Purpose: Player chooses side in conflict
  - Reward: Faction alignment, reputation
  - Narrative Outcome: World state changes based on choice
```

### Pattern 4: Power Gating
**Use Case:** Lock progression behind skill check

```yaml
Scenario: Player needs legendary weapon
  - Trigger: Quest requirement
  - Experience: BossGauntlets-WeaponTrials
  - Purpose: Prove worthiness
  - Reward: Legendary weapon
  - Narrative Outcome: Player recognized as hero
```

### Pattern 5: World-Building
**Use Case:** Show diversity of game world

```yaml
Scenario: Player explores new region
  - Trigger: Regional discovery
  - Experience: DesertWasteland-NomadTrials
  - Purpose: Introduce regional culture/threats
  - Reward: Regional gear, faction introduction
  - Narrative Outcome: World feels larger, more varied
```

---

## API Usage Examples

### Example 1: Spawn Optional Portal

```python
# Storyteller decides to spawn a portal
request = {
    "action": "spawn_experience_portal",
    "location": {"x": 1234.5, "y": 5678.9, "z": 100.0},
    "experience_type": "AlternateRealityPortals",
    "variant": "FairyRealm",
    "entry_type": "optional",
    "visual_cue": "SwirlingVortex",
    "audio_cue": "MysticalHum",
    "duration": "persistent",  # Or "30_minutes" for timed appearance
    "player_level_requirement": 10
}

# Send to UE5 Control Model
response = ue5_api.post("/api/ue5/spawn-portal", request)

# Response
{
    "status": "success",
    "portal_id": "uuid-portal-12345",
    "location": {"x": 1234.5, "y": 5678.9, "z": 100.0},
    "active": True,
    "description": "A shimmering portal to a fairy realm..."
}
```

### Example 2: Load Experience When Player Enters

```python
# Player activates portal
event = {
    "event_type": "player_entered_portal",
    "portal_id": "uuid-portal-12345",
    "player_id": "player-67890",
    "player_state": {
        "level": 15,
        "health": 100,
        "inventory": [/* items */]
    }
}

# Storyteller prepares experience
experience_config = {
    "experience_type": "AlternateRealityPortals",
    "variant": "FairyRealm",
    "difficulty": "Normal",
    "player_state": event["player_state"]
}

# Request UE5 Control Model to load
response = ue5_api.post("/api/ue5/load-experience", experience_config)

# Monitor experience
while not experience_complete:
    status = ue5_api.get(f"/api/ue5/experience-status/{response['experience_id']}")
    # Update player state, provide hints if struggling, etc.
```

### Example 3: Process Completion

```python
# Experience completes
completion_data = {
    "experience_id": "uuid-exp-12345",
    "player_id": "player-67890",
    "completion_status": "success",  # Or "failed", "abandoned"
    "duration": 2700,  # seconds
    "deaths": 2,
    "objectives_completed": 8,
    "performance_score": 0.85,
    "difficulty": "Normal"
}

# Calculate rewards
rewards = reward_api.post("/api/rewards/calculate", completion_data)

# {
#     "gold": 1500,
#     "experience": 5000,
#     "items": ["FairyWings-Cosmetic", "MagicWand-Rare"],
#     "achievements": ["FirstPortal", "FairyRealmExplorer"]
# }

# Grant rewards to player
player_api.post("/api/player/grant-rewards", {
    "player_id": "player-67890",
    "rewards": rewards
})

# Update narrative state
storyteller.process_experience_outcome(completion_data, rewards)
# - Player has visited fairy realm
# - Unlocked fairy-related quests
# - Reputation with fey increased
```

---

## Best Practices for Storyteller

### DO:
✅ **Vary experience types** - Don't repeat the same type too often  
✅ **Match difficulty to player skill** - Use performance metrics  
✅ **Integrate narratively** - Experiences should feel purposeful  
✅ **Respect player time** - Don't force long experiences on casual players  
✅ **Reward exploration** - Place best experiences off the beaten path  
✅ **Learn from player behavior** - Adapt to preferences  
✅ **Balance challenge and accessibility** - Offer multiple difficulty tiers  

### DON'T:
❌ **Force too often** - Forced experiences should be rare  
❌ **Ignore player state** - Don't spawn experiences during critical story moments  
❌ **Oversaturate** - Too many experiences feel grindy  
❌ **Break immersion** - Experiences should fit world logic  
❌ **Punish failure harshly** - Experiences should feel rewarding even on failure  
❌ **Neglect solo players** - Ensure single-player viability  

---

## Monitoring & Adaptation

### Key Metrics to Track

```python
player_metrics = {
    "experience_completion_rate": 0.75,  # 75% of started experiences finished
    "average_duration": 35,  # minutes
    "difficulty_distribution": {
        "Easy": 0.10,
        "Normal": 0.50,
        "Hard": 0.30,
        "Expert": 0.08,
        "Legendary": 0.02
    },
    "type_preferences": {
        "DungeonDiving": 0.30,
        "ArenaCombat": 0.20,
        "HistoricalBattles": 0.15,
        # ... others
    },
    "repeat_rate": 0.40,  # 40% of experiences are repeated runs
    "social_play_ratio": 0.25  # 25% done in groups
}
```

### Adaptation Strategies

**If completion rate < 50%:**
```python
# Players abandoning experiences
actions = [
    "reduce_difficulty_slightly",
    "shorten_experience_duration",
    "increase_mid-experience_rewards",
    "add_checkpoints",
    "provide_more_hints"
]
```

**If repeat rate > 70%:**
```python
# Players grinding same experience
actions = [
    "introduce_new_variant",
    "diminishing_returns_on_rewards",
    "unlock_harder_difficulty_tier",
    "rotate_experience_availability"
]
```

**If engagement decreasing:**
```python
# Players ignoring experiences
actions = [
    "introduce_new_experience_type",
    "increase_reward_quality",
    "create_limited-time_special_event",
    "improve_visual_presentation_of_portals"
]
```

---

## Example Storyteller Decision Tree

```python
def storyteller_experience_decision(player, world_state):
    """
    Complete decision-making process.
    """
    
    # Context gathering
    player_level = player.level
    location = player.current_location
    story_arc = player.story_progress
    last_experience_time = player.last_experience_timestamp
    player_preferences = player.learned_preferences
    
    # Decision point 1: Should we offer an experience?
    if last_experience_time < 30_minutes_ago:
        return None  # Too soon
    
    if world_state.in_critical_story_moment:
        return None  # Don't interrupt important moments
    
    if player.is_in_combat or player.is_in_dialogue:
        return None  # Bad timing
    
    # Decision point 2: What type of experience?
    available_types = get_available_experiences(player_level)
    narrative_appropriate = filter_by_narrative(available_types, story_arc, location)
    weighted_by_preference = apply_preference_weights(narrative_appropriate, player_preferences)
    
    if not weighted_by_preference:
        return None  # No appropriate experiences
    
    selected_type = weighted_random(weighted_by_preference)
    
    # Decision point 3: What variant and difficulty?
    variant = select_variant(selected_type, player, world_state)
    difficulty = calculate_recommended_difficulty(player)
    
    # Decision point 4: How should it appear?
    entry_mechanism = decide_entry_mechanism(player, selected_type, story_arc)
    
    # Decision point 5: Where should it spawn?
    spawn_location = determine_spawn_location(player, selected_type, entry_mechanism)
    
    # Final decision package
    return {
        "type": selected_type,
        "variant": variant,
        "difficulty": difficulty,
        "entry": entry_mechanism,
        "location": spawn_location,
        "narrative_context": generate_narrative_hook(selected_type, story_arc),
        "estimated_duration": get_duration_estimate(selected_type, variant, difficulty)
    }
```

---

## Conclusion

The Storyteller AI has complete control over when, where, and how experiences appear in the game world. By following this integration guide, the Storyteller can:

- **Enhance Player Engagement** through varied, timely content
- **Advance Narrative** by using experiences as storytelling tools
- **Balance Challenge** with appropriate difficulty selection
- **Respect Player Autonomy** through optional content and choice
- **Create Memorable Moments** through epic, unique experiences

The Experiences System is a powerful tool in the Storyteller's arsenal for creating a dynamic, engaging, and endlessly replayable game world.

---

**Key Takeaway:**  
Experiences are **temporary adventures** that provide **variety, challenge, and rewards** while serving the **overarching narrative**. Use them wisely to create a game world that feels alive, surprising, and endlessly entertaining.

---

**Related Documents:**
- `00-EXPERIENCES-OVERVIEW.md` - System overview
- `AUTOMATION-ARCHITECTURE.md` - Technical implementation
- All experience type documents (01-15) - Detailed specifications

