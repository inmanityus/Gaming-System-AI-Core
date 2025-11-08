# Experiences System - Automation Architecture

**Version:** 1.0.0  
**Last Updated:** 2025-11-08  
**Status:** Implementation Design  
**Engine:** Unreal Engine 5.6.1  

---

## Executive Summary

The Experiences System requires comprehensive automation through a hierarchical AI model architecture. Each component must operate autonomously while coordinating with the Storyteller and other system services. This document defines the complete automation architecture, AI model specifications, and integration patterns.

---

## Hierarchical Model Architecture

### Level 1: Storyteller (Master Controller)
**Model:** GPT-5 Pro or Claude Sonnet 4.5  
**Role:** High-level narrative and experience orchestration

**Responsibilities:**
- Determine when/where experiences appear in main world
- Select appropriate experience types for player state
- Weave experiences into overarching narrative
- Balance experience frequency and variety
- Monitor player engagement metrics

**Interfaces:**
- Experience Selector Service
- Player State Manager
- World State Manager
- Narrative Database

---

### Level 2: Experience Control Models

#### 2A. UE5 Control Model
**Model:** GPT-Codex-2 (OpenAI API Direct) or Claude Sonnet 4.5  
**Role:** Unreal Engine-specific implementation

**Responsibilities:**
- Translate high-level experience specifications into UE5 commands
- Manage World Partition streaming
- Control material system and post-processing
- Handle lighting scenario transitions
- Coordinate asset loading/unloading
- Execute blueprint logic
- Manage Niagara VFX systems

**UE5 Interface Specification:**
```python
class UE5ControlModel:
    """
    Dedicated model for UE5 engine control.
    Provides natural language interface to engine features.
    """
    
    def load_experience_world(self, experience_type: str, 
                              variant: str,
                              player_state: dict) -> dict:
        """
        Load experience world partition and configure environment.
        
        Args:
            experience_type: e.g., "DungeonDiving", "HistoricalBattle"
            variant: Specific subtype (e.g., "GoblinWarren", "Thermopylae")
            player_state: Current player data for scaling
        
        Returns:
            World load status and configuration details
        """
        # Translate to UE5 console commands
        commands = [
            f"World.LoadPartition {experience_type}_{variant}",
            f"World.StreamingPriority High",
            f"Material.ApplyProfile {variant}_MaterialProfile",
            f"PostProcess.ApplyVolume {variant}_PP_Volume",
            f"Lighting.LoadScenario {variant}_LightingSetup"
        ]
        
        # Execute commands and return status
        return self.execute_ue5_commands(commands)
    
    def configure_visual_style(self, style: str) -> dict:
        """
        Apply visual style configuration.
        
        Args:
            style: Visual aesthetic (e.g., "Anime", "Photorealistic", 
                   "DarkFantasy", "SciFi")
        
        Returns:
            Applied settings confirmation
        """
        style_profiles = {
            "Anime": {
                "material_shader": "ToonShader",
                "post_process": "CelShading",
                "outline_thickness": 2.0,
                "bloom_intensity": 3.5,
                "color_grading_lut": "Anime_Vibrant"
            },
            "Photorealistic": {
                "material_shader": "PBR",
                "lumen_enabled": True,
                "ray_tracing": True,
                "bloom_intensity": 1.0,
                "color_grading_lut": "Realistic_Neutral"
            },
            # ... other profiles
        }
        
        profile = style_profiles.get(style)
        return self.apply_material_profile(profile)
    
    def spawn_procedural_content(self, generation_params: dict) -> list:
        """
        Coordinate procedural content generation.
        """
        # Interface with Procedural Generation Service
        pass
    
    def get_engine_capabilities(self) -> dict:
        """
        Query current engine features and limitations.
        Used by Storyteller to understand what's possible.
        """
        return {
            "max_world_size": (20000, 20000, 10000),  # meters
            "max_ai_units": 1000,
            "nanite_supported": True,
            "lumen_supported": True,
            "visual_styles": ["Anime", "Photorealistic", "DarkFantasy", 
                            "SciFi", "Stylized"],
            "supported_experience_types": [/* all 15 types */]
        }
```

**Communication Protocol:**
```
Storyteller → UE5 Control Model
Request: {
    "action": "spawn_experience",
    "experience_type": "HistoricalBattle",
    "variant": "Thermopylae",
    "player_level": 25,
    "difficulty": "Expert"
}

UE5 Control Model → Storyteller
Response: {
    "status": "success",
    "world_loaded": True,
    "spawn_location": [1234.5, 6789.0, 100.0],
    "estimated_duration": "60-90 minutes",
    "visual_profile": "Ancient_Greece",
    "enemy_count": 150
}
```

---

#### 2B. Experience Generator Service
**Model:** GPT-5 Pro for creative generation  
**Role:** Procedural content creation within experience types

**Responsibilities:**
- Generate procedural dungeon layouts
- Create enemy spawn patterns
- Design puzzle configurations
- Generate loot tables
- Create narrative flavor text
- Adapt content to player preferences

**Generation API:**
```python
class ExperienceGenerator:
    """
    Generates specific experience instances with variation.
    """
    
    def generate_dungeon_layout(self, params: dict) -> dict:
        """
        Create procedural dungeon layout.
        
        Args:
            params: {
                "algorithm": "BSP" | "CellularAutomata" | "DrunkardsWalk",
                "room_count": int,
                "complexity": float (0-1),
                "theme": str
            }
        
        Returns:
            Dungeon data structure with rooms, corridors, spawns
        """
        # Use procedural algorithms from research
        layout = self.apply_algorithm(params["algorithm"], params)
        
        # Add gameplay elements
        layout = self.place_enemies(layout, params)
        layout = self.place_traps(layout, params)
        layout = self.place_treasures(layout, params)
        layout = self.place_boss_room(layout)
        
        return layout
    
    def generate_battle_scenario(self, params: dict) -> dict:
        """
        Create historical battle scenario.
        """
        pass
    
    def generate_rewards(self, params: dict) -> list:
        """
        Create balanced reward loot tables.
        """
        pass
```

---

#### 2C. Difficulty Scaler Service
**Model:** DeepSeek V3 for numerical optimization  
**Role:** Dynamic difficulty adjustment

**Responsibilities:**
- Scale enemy stats to player level
- Adjust loot quality
- Modify spawn rates
- Tune resource availability
- Balance challenge vs frustration

**Scaling Algorithm:**
```python
class DifficultyScaler:
    """
    Dynamically scales experience difficulty.
    """
    
    def scale_experience(self, base_difficulty: str,
                         player_stats: dict,
                         party_size: int) -> dict:
        """
        Calculate scaled difficulty parameters.
        
        Args:
            base_difficulty: "Easy" | "Normal" | "Hard" | "Expert" | "Legendary"
            player_stats: Current player statistics
            party_size: Number of players (1-20)
        
        Returns:
            Scaled parameters for experience
        """
        difficulty_multipliers = {
            "Easy": {"hp": 0.5, "damage": 0.5, "xp": 0.7},
            "Normal": {"hp": 1.0, "damage": 1.0, "xp": 1.0},
            "Hard": {"hp": 1.5, "damage": 1.5, "xp": 1.5},
            "Expert": {"hp": 2.5, "damage": 2.0, "xp": 2.5},
            "Legendary": {"hp": 4.0, "damage": 3.0, "xp": 5.0}
        }
        
        base_mult = difficulty_multipliers[base_difficulty]
        
        # Adjust for player level
        level_factor = player_stats["level"] / 50  # Normalize to 0-1
        
        # Adjust for party size
        party_factor = 1.0 + (party_size - 1) * 0.3  # 30% per additional player
        
        # Calculate final scaling
        scaled = {
            "enemy_hp_multiplier": base_mult["hp"] * (1 + level_factor) * party_factor,
            "enemy_damage_multiplier": base_mult["damage"] * (1 + level_factor * 0.5),
            "enemy_count_multiplier": party_factor,
            "loot_quality_multiplier": base_mult["xp"],
            "xp_multiplier": base_mult["xp"] * (1 + level_factor * 0.2)
        }
        
        return scaled
```

---

#### 2D. Reward Calculator Service
**Model:** GPT-5 or Gemini 2.5 Pro  
**Role:** Economy balancing and reward generation

**Responsibilities:**
- Generate appropriate loot for difficulty/time
- Balance in-game economy
- Prevent power creep
- Create meaningful progression
- Ensure reward variety

**Reward System:**
```python
class RewardCalculator:
    """
    Calculates balanced rewards for experiences.
    """
    
    def calculate_rewards(self, experience_data: dict) -> dict:
        """
        Determine rewards based on experience completion.
        
        Args:
            experience_data: {
                "type": str,
                "difficulty": str,
                "duration": int (minutes),
                "performance_score": float (0-1),
                "death_count": int,
                "completion_time": int (seconds),
                "objectives_completed": int
            }
        
        Returns:
            Reward package
        """
        base_rewards = self.get_base_rewards(experience_data["type"],
                                              experience_data["difficulty"])
        
        # Apply performance modifiers
        performance_mult = 1.0 + experience_data["performance_score"]
        
        # Penalize deaths
        death_penalty = 0.9 ** experience_data["death_count"]
        
        # Bonus for speed
        speed_bonus = self.calculate_speed_bonus(experience_data)
        
        final_rewards = {
            "gold": int(base_rewards["gold"] * performance_mult * death_penalty * speed_bonus),
            "experience": int(base_rewards["xp"] * performance_mult),
            "items": self.select_items(base_rewards["item_pool"], 
                                       performance_mult),
            "reputation": base_rewards["reputation"],
            "achievements": self.check_achievements(experience_data)
        }
        
        return final_rewards
    
    def validate_economy_impact(self, rewards: dict) -> bool:
        """
        Ensure rewards don't break in-game economy.
        """
        # Check against economy thresholds
        pass
```

---

### Level 3: Specialized Service Models

#### 3A. Procedural Generation Service
**Model:** Specialized generation model  
**Role:** Execute procedural algorithms

**Algorithms Implemented:**
- BSP (Binary Space Partitioning)
- Cellular Automata
- Drunkard's Walk
- Wave Function Collapse
- Voronoi Diagrams
- Perlin Noise for terrain

---

#### 3B. AI Navigation Service
**Model:** Pathfinding and navigation AI  
**Role:** Runtime navigation mesh generation

**Capabilities:**
- Generate nav meshes for procedural layouts
- Calculate optimal paths for AI
- Handle dynamic obstacles
- Support flying/swimming AI

---

#### 3C. Visual Profile Manager
**Model:** Style transfer and material management  
**Role:** Switch visual aesthetics seamlessly

**Profiles:**
- Anime/Stylized
- Photorealistic
- Dark Fantasy
- Sci-Fi
- Desert/Arid
- Underwater
- Historical

---

#### 3D. Audio Manager Service
**Model:** Audio mixing and adaptive music  
**Role:** Manage soundscapes

**Features:**
- Adaptive music systems
- 3D positional audio
- Ambient soundscapes per experience
- Combat music intensity scaling

---

## Integration Patterns

### Pattern 1: Experience Spawning Flow
```
1. Player discovers portal/trigger
2. Storyteller queries player state
3. Storyteller selects appropriate experience type
4. Storyteller requests UE5 Control Model to load experience
5. UE5 Control Model:
   a. Requests Experience Generator to create instance
   b. Requests Difficulty Scaler to calculate parameters
   c. Loads world partition
   d. Applies visual profile
   e. Spawns procedural content
6. Player enters experience
7. Experience runs autonomously
8. On completion:
   a. Reward Calculator determines loot
   b. Storyteller receives completion data
   c. UE5 Control Model unloads experience
   d. Player returns to main world with rewards
```

### Pattern 2: Real-Time Difficulty Adjustment
```
During Experience:
1. Monitor player performance metrics
   - Death count
   - Health percentage
   - Completion rate
2. If player struggling → Difficulty Scaler reduces challenge
3. If player breezing → Difficulty Scaler increases challenge
4. Adjustments are subtle and gradual
5. Final rewards reflect actual difficulty faced
```

### Pattern 3: Narrative Integration
```
1. Storyteller identifies story beat requiring experience
2. Selects experience type that fits narrative
3. Generates narrative context (why portal appears)
4. Player completes experience
5. Storyteller interprets results into story consequences
6. World state updates based on outcome
```

---

## Communication Protocol

### Message Format (JSON)
```json
{
  "sender": "Storyteller",
  "recipient": "UE5ControlModel",
  "timestamp": "2025-11-08T12:34:56Z",
  "action": "spawn_experience",
  "payload": {
    "experience_type": "DungeonDiving",
    "variant": "GoblinWarren",
    "difficulty": "Normal",
    "player_level": 15,
    "party_size": 3
  },
  "correlation_id": "uuid-12345-67890"
}
```

### Response Format
```json
{
  "sender": "UE5ControlModel",
  "recipient": "Storyteller",
  "timestamp": "2025-11-08T12:35:12Z",
  "status": "success" | "error",
  "correlation_id": "uuid-12345-67890",
  "result": {
    "world_loaded": true,
    "spawn_location": [x, y, z],
    "estimated_duration": "30-60 minutes",
    "configuration": { /* details */ }
  }
}
```

---

## API Endpoints

### Storyteller APIs (HTTP REST)

**POST `/api/storyteller/request-experience`**
```
Request experience spawn from Storyteller.
Body: {experience_request}
Response: {experience_details}
```

**GET `/api/storyteller/available-experiences`**
```
Query available experience types.
Params: player_id, location, context
Response: [list of suitable experiences]
```

**POST `/api/storyteller/complete-experience`**
```
Report experience completion.
Body: {completion_data}
Response: {rewards, narrative_consequences}
```

---

### UE5 Control Model APIs

**POST `/api/ue5/load-world`**
```
Load experience world partition.
Body: {experience_config}
Response: {load_status}
```

**POST `/api/ue5/apply-visual-profile`**
```
Switch visual aesthetic.
Body: {profile_name}
Response: {applied_settings}
```

**GET `/api/ue5/engine-capabilities`**
```
Query UE5 features available.
Response: {capabilities}
```

---

### Experience Generator APIs

**POST `/api/generator/create-dungeon`**
```
Generate dungeon layout.
Body: {generation_params}
Response: {dungeon_data}
```

**POST `/api/generator/create-battle`**
```
Generate battle scenario.
Body: {battle_params}
Response: {battle_data}
```

---

### Difficulty Scaler APIs

**POST `/api/scaler/calculate-difficulty`**
```
Calculate scaled parameters.
Body: {base_difficulty, player_stats, party_size}
Response: {scaled_parameters}
```

**POST `/api/scaler/adjust-real-time`**
```
Real-time difficulty adjustment.
Body: {current_metrics}
Response: {adjustment_instructions}
```

---

### Reward Calculator APIs

**POST `/api/rewards/calculate`**
```
Calculate experience rewards.
Body: {experience_data, performance_metrics}
Response: {reward_package}
```

**POST `/api/rewards/validate-economy`**
```
Validate economy impact.
Body: {rewards}
Response: {validated_rewards, warnings}
```

---

## Error Handling

### Fault Tolerance
- All services implement retry logic (exponential backoff)
- Fallback to default configurations if service unavailable
- Graceful degradation (reduce features rather than fail completely)

### Logging & Monitoring
- All API calls logged with correlation IDs
- Performance metrics tracked
- Error rates monitored
- Alerts for anomalies

---

## Deployment Architecture

### Service Deployment (AWS)

**Storyteller Service:**
- ECS/Fargate container
- Auto-scaling based on player count
- Redis cache for session state

**UE5 Control Model:**
- Dedicated EC2 instances (GPU if needed)
- Communicates directly with UE5 server instances
- Model cached in memory for low latency

**Support Services:**
- Lambda functions for lightweight tasks
- RDS PostgreSQL for persistent data
- S3 for asset storage
- CloudFront CDN for asset delivery

---

## Performance Requirements

### Latency Targets
- Experience spawn request → 3 seconds max
- Visual profile switch → < 1 second
- Difficulty adjustment → real-time (< 100ms)
- Reward calculation → < 500ms

### Throughput
- Support 10,000 concurrent experiences
- 1,000 experience spawns per minute
- 10,000 reward calculations per minute

---

## Security & Safety

### AI Model Safety
- Output validation (ensure commands are safe)
- Rate limiting (prevent abuse)
- Audit logging (track all actions)
- Rollback mechanisms (undo problematic changes)

### Data Privacy
- Player data anonymized for AI training
- Sensitive information encrypted
- GDPR/CCPA compliant

---

## Testing & Validation

### Model Testing
- Unit tests for each AI model endpoint
- Integration tests for multi-model workflows
- Load testing for performance validation
- A/B testing for reward balance

### Experience Quality Assurance
- Automated play-testing bots
- Metrics: completion rate, player deaths, time taken
- Player feedback collection
- Continuous improvement loop

---

## Maintenance & Updates

### Model Updates
- Models versioned (e.g., v1.2.3)
- Blue-green deployment for zero downtime
- Gradual rollout with canary testing
- Rollback plans for failed updates

### Engine Updates
- UE5 Control Model updated with each engine version
- Capability discovery system keeps documentation current
- Backward compatibility maintained for 2 versions

---

## Conclusion

This automation architecture enables the Storyteller to autonomously create, manage, and balance diverse experiences using a hierarchical AI model system. Each component has clear responsibilities, well-defined interfaces, and robust error handling. The system is designed for scalability, maintainability, and continuous improvement.

**Key Strengths:**
- Full automation via AI models
- Hierarchical structure for complexity management
- UE5-specific control model for engine mastery
- Dynamic difficulty and reward balancing
- Comprehensive error handling and monitoring

**Automation Requirements Met:**
✅ Everything automated via AI models  
✅ Complete UE5 control through dedicated model  
✅ Procedural generation for infinite variety  
✅ Real-time adaptation to player behavior  
✅ Economy balancing and reward calculation  
✅ Narrative integration with Storyteller  

---

**Related Documents:**
- `00-EXPERIENCES-OVERVIEW.md` - System overview
- `STORYTELLER-INTEGRATION-GUIDE.md` - Storyteller implementation
- `IMPLEMENTATION-TASKS.md` - Development task breakdown

