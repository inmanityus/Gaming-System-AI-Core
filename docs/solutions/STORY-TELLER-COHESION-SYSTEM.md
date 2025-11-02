# Story Teller Cohesion System Solution
**Date**: 2025-01-29  
**Status**: Solution Architecture - Phase 2  
**Enforcement**: ALL rules in `/all-rules` are MANDATORY

---

## 🚨 EXECUTIVE SUMMARY

The Story Teller Cohesion System is a MAJOR responsibility that ensures the world remains cohesive, prevents chaos, maintains storylines, and enforces guardrails. This system uses deep learning to learn optimal storyline limits and anticipate player interactions.

### **Key Responsibilities:**
- **World Cohesion**: Prevent world from going off-rails into chaos
- **Storyline Preservation**: Maintain major/minor storylines (unless disrupted)
- **End Goal Management**: Preserve important end goals (or morph into better ones)
- **Storyline Limiting**: Prevent player overwhelm through dynamic limits
- **Guard Rails Enforcement**: Ensure world never breaks game guardrails
- **Deep Learning Integration**: Learn optimal limits and predict player interactions

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 System Components

```python
CohesionSystem {
  StorylineTracker {
    activeStorylines: Map<StorylineID, StorylineState>
    majorStorylines: Set<StorylineID>
    minorStorylines: Set<StorylineID>
    endGoals: Map<StorylineID, EndGoal>
    storylineGraph: Graph<Storyline, Dependencies>
  }
  
  GuardRails {
    worldStateValidator: Function<WorldState -> ValidationResult>
    storylineConsistencyChecker: Function<Storyline -> ConsistencyCheck>
    endGoalPreserver: Function<EndGoal -> PreservationResult>
    disruptionHandler: Function<Event -> DisruptionResponse>
  }
  
  StorylineLimiter {
    playerCapacityModel: DeepLearningModel
    activeLimit: Integer
    pathComplexityManager: Function<Paths -> ComplexityScore>
    overwhelmPreventer: Function<PlayerState -> Action>
  }
  
  DeepLearningComponents {
    playerCapacityLearner: LSTM
    interactionPredictor: Transformer
    pathOptimizer: ReinforcementLearning
    coherenceScorer: NeuralNetwork
  }
}
```

### 1.2 Integration Points

**With World Simulation Engine:**
- Validate world state changes before applying
- Check storyline consistency during simulation
- Preserve end goals during world evolution

**With Story Teller Service:**
- Limit active storylines
- Ensure new storylines don't conflict
- Track storyline progression

**With Player Interactions:**
- Predict player choices
- Anticipate player path selection
- Prevent overwhelm

---

## 2. STORYLINE TRACKING SYSTEM

### 2.1 Storyline Registry

```python
class StorylineTracker:
    def __init__(self):
        self.active_storylines: Dict[str, StorylineState] = {}
        self.major_storylines: Set[str] = set()
        self.minor_storylines: Set[str] = set()
        self.end_goals: Dict[str, EndGoal] = {}
        self.storyline_graph = StorylineGraph()
    
    async def register_storyline(
        self,
        storyline_id: str,
        storyline_type: str,  # "major" or "minor"
        end_goal: EndGoal,
        dependencies: List[str] = None
    ):
        """
        Register a new storyline with tracking.
        
        Storylines are tracked with:
        - State (active, paused, disrupted, completed)
        - End goal
        - Dependencies on other storylines
        - Player participation
        """
        storyline_state = StorylineState(
            id=storyline_id,
            type=storyline_type,
            state="active",
            end_goal=end_goal,
            dependencies=dependencies or [],
            created_at=time.time()
        )
        
        self.active_storylines[storyline_id] = storyline_state
        
        if storyline_type == "major":
            self.major_storylines.add(storyline_id)
        else:
            self.minor_storylines.add(storyline_id)
        
        self.end_goals[storyline_id] = end_goal
        
        # Add to dependency graph
        self.storyline_graph.add_node(storyline_id, storyline_state)
        for dep_id in dependencies or []:
            self.storyline_graph.add_edge(dep_id, storyline_id)
    
    async def update_storyline_state(
        self,
        storyline_id: str,
        new_state: str,
        reason: str = None
    ):
        """
        Update storyline state (active, paused, disrupted, completed).
        
        State transitions:
        - active → paused: Player temporarily away
        - active → disrupted: Outside event disrupted
        - active → completed: End goal reached
        - paused → active: Player returns
        - disrupted → active: Disruption resolved
        """
        if storyline_id not in self.active_storylines:
            raise ValueError(f"Storyline {storyline_id} not found")
        
        old_state = self.active_storylines[storyline_id].state
        
        # Validate state transition
        valid_transitions = {
            "active": ["paused", "disrupted", "completed"],
            "paused": ["active"],
            "disrupted": ["active", "completed"],
            "completed": []  # Terminal state
        }
        
        if new_state not in valid_transitions.get(old_state, []):
            raise ValueError(
                f"Invalid transition: {old_state} → {new_state}"
            )
        
        self.active_storylines[storyline_id].state = new_state
        self.active_storylines[storyline_id].last_update = time.time()
        
        if reason:
            self.active_storylines[storyline_id].state_history.append({
                "timestamp": time.time(),
                "from_state": old_state,
                "to_state": new_state,
                "reason": reason
            })
```

### 2.2 End Goal Management

```python
class EndGoalManager:
    async def preserve_end_goal(
        self,
        storyline_id: str,
        end_goal: EndGoal,
        allow_morphing: bool = True
    ):
        """
        Preserve end goal, or morph into better goal if warranted.
        
        End goals should:
        - Remain important end goals
        - Not be dropped unless disrupted
        - Morph into better goals if context changes
        - Be preserved across world state changes
        """
        current_goal = self.end_goals.get(storyline_id)
        
        if not current_goal:
            # New end goal
            self.end_goals[storyline_id] = end_goal
            return
        
        # Check if morphing is warranted
        if allow_morphing:
            better_goal = await self._evaluate_goal_improvement(
                current_goal,
                end_goal,
                storyline_id
            )
            
            if better_goal and better_goal != current_goal:
                # Morph to better goal
                await self._morph_goal(storyline_id, current_goal, better_goal)
                return
        
        # Preserve existing goal
        await self._reinforce_goal(storyline_id, current_goal)
    
    async def _morph_goal(
        self,
        storyline_id: str,
        old_goal: EndGoal,
        new_goal: EndGoal
    ):
        """
        Morph end goal into better version.
        
        Example:
        - Old: "Defeat the vampire lord"
        - New: "Become the vampire lord's ally" (better, more interesting)
        """
        self.end_goals[storyline_id] = new_goal
        
        # Record morphing event
        await self._record_goal_morph(
            storyline_id,
            old_goal,
            new_goal,
            reason="Context change made new goal better"
        )
```

---

## 3. GUARD RAILS SYSTEM

### 3.1 World State Validation

```python
class GuardRails:
    def __init__(self):
        self.world_state_validator = WorldStateValidator()
        self.consistency_checker = ConsistencyChecker()
        self.end_goal_preserver = EndGoalPreserver()
    
    async def validate_world_state(
        self,
        world_state: Dict,
        proposed_changes: Dict
    ) -> ValidationResult:
        """
        Validate proposed world state changes before applying.
        
        Checks:
        1. World doesn't go off-rails into chaos
        2. Storylines remain consistent
        3. End goals preserved
        4. Guard rails not broken
        """
        # Check 1: World coherence
        coherence_check = await self._check_world_coherence(
            world_state,
            proposed_changes
        )
        
        if not coherence_check.passed:
            return ValidationResult(
                passed=False,
                reason="World coherence violated",
                details=coherence_check.violations
            )
        
        # Check 2: Storyline consistency
        consistency_check = await self._check_storyline_consistency(
            world_state,
            proposed_changes
        )
        
        if not consistency_check.passed:
            return ValidationResult(
                passed=False,
                reason="Storyline consistency violated",
                details=consistency_check.violations
            )
        
        # Check 3: End goal preservation
        goal_check = await self._check_end_goal_preservation(
            world_state,
            proposed_changes
        )
        
        if not goal_check.passed:
            return ValidationResult(
                passed=False,
                reason="End goal preservation violated",
                details=goal_check.violations
            )
        
        # Check 4: Guard rails
        guardrail_check = await self._check_guardrails(
            world_state,
            proposed_changes
        )
        
        if not guardrail_check.passed:
            return ValidationResult(
                passed=False,
                reason="Guard rails violated",
                details=guardrail_check.violations
            )
        
        return ValidationResult(passed=True)
    
    async def _check_world_coherence(
        self,
        world_state: Dict,
        proposed_changes: Dict
    ) -> CoherenceCheck:
        """
        Check if world remains coherent (doesn't go into chaos).
        
        Coherence rules:
        - Factions can't suddenly switch allegiances without reason
        - NPCs can't teleport without explanation
        - Locations can't disappear
        - Laws of world can't be broken
        """
        violations = []
        
        # Check faction coherence
        faction_check = await self._check_faction_coherence(
            world_state,
            proposed_changes
        )
        violations.extend(faction_check.violations)
        
        # Check location coherence
        location_check = await self._check_location_coherence(
            world_state,
            proposed_changes
        )
        violations.extend(location_check.violations)
        
        # Check causality coherence
        causality_check = await self._check_causality_coherence(
            world_state,
            proposed_changes
        )
        violations.extend(causality_check.violations)
        
        return CoherenceCheck(
            passed=len(violations) == 0,
            violations=violations
        )
```

### 3.2 Consistency Checking

```python
class ConsistencyChecker:
    async def check_storyline_consistency(
        self,
        storyline_id: str,
        new_event: Event
    ) -> ConsistencyCheck:
        """
        Check if new event maintains storyline consistency.
        
        Consistency rules:
        - Events align with storyline progression
        - Character motivations remain consistent
        - Plot threads don't contradict
        - Timeline remains logical
        """
        storyline = await self._get_storyline(storyline_id)
        
        violations = []
        
        # Check event alignment
        if not self._event_aligns_with_storyline(new_event, storyline):
            violations.append("Event does not align with storyline")
        
        # Check character consistency
        character_check = await self._check_character_consistency(
            new_event,
            storyline
        )
        violations.extend(character_check.violations)
        
        # Check plot consistency
        plot_check = await self._check_plot_consistency(
            new_event,
            storyline
        )
        violations.extend(plot_check.violations)
        
        return ConsistencyCheck(
            passed=len(violations) == 0,
            violations=violations
        )
```

### 3.3 Disruption Handling

```python
class DisruptionHandler:
    async def handle_disruption(
        self,
        storyline_id: str,
        disruption_event: Event
    ) -> DisruptionResponse:
        """
        Handle storyline disruption by outside events.
        
        Disruptions can:
        - Pause storyline temporarily
        - Redirect storyline path
        - Merge with other storylines
        - Complete storyline early (if disruption resolves goal)
        
        Example:
        - Storyline: "Investigate corruption"
        - Disruption: "City destroyed by dragon"
        - Response: Pause investigation, redirect to survival storyline
        """
        storyline = await self._get_storyline(storyline_id)
        
        # Assess disruption impact
        impact = await self._assess_disruption_impact(
            storyline,
            disruption_event
        )
        
        if impact.severity == "critical":
            # Critical disruption: Redirect or complete
            if impact.resolves_end_goal:
                # Disruption resolves end goal → complete storyline
                await self._complete_storyline(storyline_id, "disruption_resolved")
            else:
                # Disruption redirects storyline
                await self._redirect_storyline(storyline_id, impact.new_path)
        
        elif impact.severity == "moderate":
            # Moderate disruption: Pause or adapt
            await self._adapt_storyline(storyline_id, impact.adaptations)
        
        else:
            # Minor disruption: Continue with adjustments
            await self._adjust_storyline(storyline_id, impact.adjustments)
        
        return DisruptionResponse(
            storyline_id=storyline_id,
            action_taken=impact.response_action,
            new_state=await self._get_storyline_state(storyline_id)
        )
```

---

## 4. STORYLINE LIMITING SYSTEM

### 4.1 Dynamic Limit Management

```python
class StorylineLimiter:
    def __init__(self):
        self.player_capacity_model = PlayerCapacityModel()
        self.active_limit = 5  # Default limit
        self.path_complexity_manager = PathComplexityManager()
    
    async def check_storyline_limit(
        self,
        player_id: str,
        requested_storylines: List[str]
    ) -> LimitCheckResult:
        """
        Check if player can handle additional storylines.
        
        Uses deep learning to determine optimal limit per player.
        Considers:
        - Player's historical capacity
        - Current active storylines
        - Path complexity
        - Player engagement level
        """
        # Get player capacity from deep learning model
        player_capacity = await self.player_capacity_model.predict(
            player_id=player_id,
            current_storylines=await self._get_active_storylines(player_id),
            engagement_level=await self._get_engagement_level(player_id)
        )
        
        # Get path complexity
        path_complexity = await self.path_complexity_manager.assess_complexity(
            requested_storylines
        )
        
        # Calculate if player can handle
        current_count = len(await self._get_active_storylines(player_id))
        requested_count = len(requested_storylines)
        
        if current_count + requested_count > player_capacity.max_storylines:
            return LimitCheckResult(
                allowed=False,
                reason="Would exceed player capacity",
                current_count=current_count,
                capacity=player_capacity.max_storylines
            )
        
        if path_complexity.score > player_capacity.max_complexity:
            return LimitCheckResult(
                allowed=False,
                reason="Path complexity too high",
                complexity_score=path_complexity.score,
                max_complexity=player_capacity.max_complexity
            )
        
        return LimitCheckResult(
            allowed=True,
            current_count=current_count,
            capacity=player_capacity.max_storylines
        )
    
    async def prevent_overwhelm(
        self,
        player_id: str
    ) -> PreventOverwhelmAction:
        """
        Prevent player overwhelm by managing active storylines.
        
        Actions:
        - Pause low-priority storylines
        - Suggest completing active storylines
        - Reduce path complexity
        - Offer storyline prioritization
        """
        active_storylines = await self._get_active_storylines(player_id)
        
        if len(active_storylines) > self.active_limit:
            # Over limit: Suggest actions
            low_priority = await self._identify_low_priority_storylines(
                active_storylines
            )
            
            return PreventOverwhelmAction(
                action="suggest_pause",
                storylines_to_pause=low_priority,
                reason="Prevent overwhelm",
                suggestion_message=(
                    f"You have {len(active_storylines)} active storylines. "
                    f"Consider pausing {len(low_priority)} lower-priority ones."
                )
            )
        
        return PreventOverwhelmAction(action="no_action_needed")
```

### 4.2 Path Complexity Management

```python
class PathComplexityManager:
    async def assess_complexity(
        self,
        storylines: List[str]
    ) -> ComplexityScore:
        """
        Assess complexity of storyline paths.
        
        Complexity factors:
        - Number of storylines
        - Inter-dependencies
        - Choice points
        - Required player attention
        """
        complexity_score = 0
        
        # Base complexity: number of storylines
        complexity_score += len(storylines) * 10
        
        # Dependency complexity
        dependency_count = await self._count_dependencies(storylines)
        complexity_score += dependency_count * 5
        
        # Choice complexity
        choice_points = await self._count_choice_points(storylines)
        complexity_score += choice_points * 3
        
        # Attention complexity
        attention_required = await self._assess_attention_required(storylines)
        complexity_score += attention_required * 2
        
        return ComplexityScore(
            score=complexity_score,
            factors={
                "storyline_count": len(storylines),
                "dependencies": dependency_count,
                "choice_points": choice_points,
                "attention_required": attention_required
            }
        )
```

---

## 5. DEEP LEARNING COMPONENTS

### 5.1 Player Capacity Model

```python
class PlayerCapacityModel:
    """
    Deep learning model that learns optimal storyline limits per player.
    
    Architecture: LSTM (Long Short-Term Memory)
    Inputs:
    - Player's historical storyline completion rates
    - Player's engagement patterns
    - Player's choice complexity preferences
    - Player's time investment
    
    Output:
    - Maximum storylines player can handle
    - Maximum path complexity
    - Optimal storyline mix (major vs minor)
    """
    
    def __init__(self):
        self.model = self._build_lstm_model()
        self.training_data_collector = TrainingDataCollector()
    
    async def predict(
        self,
        player_id: str,
        current_storylines: List[str],
        engagement_level: float
    ) -> PlayerCapacity:
        """
        Predict player's capacity for storylines.
        """
        # Get player history
        history = await self._get_player_history(player_id)
        
        # Prepare features
        features = self._prepare_features(
            history=history,
            current_storylines=current_storylines,
            engagement_level=engagement_level
        )
        
        # Predict
        prediction = self.model.predict(features)
        
        return PlayerCapacity(
            max_storylines=int(prediction["max_storylines"]),
            max_complexity=float(prediction["max_complexity"]),
            optimal_major_count=int(prediction["optimal_major"]),
            optimal_minor_count=int(prediction["optimal_minor"])
        )
    
    async def train(self, training_data: List[PlayerTrainingExample]):
        """
        Train model on player behavior data.
        
        Training examples include:
        - Player's storyline completion rates
        - Player's overwhelm indicators
        - Player's engagement metrics
        """
        # Prepare training data
        X, y = self._prepare_training_data(training_data)
        
        # Train model
        self.model.fit(X, y, epochs=10, batch_size=32)
        
        # Validate
        validation_score = self.model.evaluate(X, y)
        
        return TrainingResult(
            model_version=self.model.version,
            validation_score=validation_score
        )
```

### 5.2 Interaction Predictor

```python
class InteractionPredictor:
    """
    Transformer model that predicts player interactions with archetypes.
    
    Architecture: Transformer
    Inputs:
    - Player's historical choices
    - Current world state
    - Available NPCs and their archetypes
    - Active storylines
    
    Output:
    - Predicted player interactions
    - Predicted path selections
    - Predicted engagement levels
    """
    
    async def predict_interactions(
        self,
        player_id: str,
        available_npcs: List[NPC],
        active_storylines: List[str]
    ) -> InteractionPrediction:
        """
        Predict how player will interact with different archetypes.
        """
        # Get player history
        history = await self._get_player_history(player_id)
        
        # Prepare context
        context = self._prepare_context(
            history=history,
            available_npcs=available_npcs,
            active_storylines=active_storylines
        )
        
        # Predict
        prediction = self.model.predict(context)
        
        return InteractionPrediction(
            predicted_interactions=prediction["interactions"],
            predicted_paths=prediction["paths"],
            confidence_scores=prediction["confidence"]
        )
```

### 5.3 Path Optimizer

```python
class PathOptimizer:
    """
    Reinforcement learning model that optimizes storyline paths.
    
    Architecture: Deep Q-Network (DQN)
    Objective: Maximize player engagement while maintaining coherence
    """
    
    async def optimize_paths(
        self,
        player_id: str,
        available_paths: List[Path]
    ) -> OptimizedPaths:
        """
        Optimize storyline paths for player engagement.
        """
        # Get player state
        player_state = await self._get_player_state(player_id)
        
        # Evaluate paths
        path_scores = []
        for path in available_paths:
            score = await self._evaluate_path(path, player_state)
            path_scores.append((path, score))
        
        # Select optimal paths
        optimal_paths = sorted(
            path_scores,
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5 paths
        
        return OptimizedPaths(
            recommended_paths=[p[0] for p in optimal_paths],
            scores=[p[1] for p in optimal_paths]
        )
```

---

## 6. DATABASE SCHEMA

```sql
-- Storyline tracking
CREATE TABLE storylines (
    storyline_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    storyline_name VARCHAR(255) NOT NULL,
    storyline_type VARCHAR(20) NOT NULL,  -- "major" or "minor"
    state VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, paused, disrupted, completed
    end_goal JSONB NOT NULL,
    player_id UUID REFERENCES players(id),
    world_state_id UUID REFERENCES world_states(id),
    dependencies JSONB DEFAULT '[]',  -- Array of storyline_ids
    state_history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- End goals
CREATE TABLE end_goals (
    goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    storyline_id UUID NOT NULL REFERENCES storylines(storyline_id),
    goal_description TEXT NOT NULL,
    goal_type VARCHAR(50),  -- defeat, acquire, discover, etc.
    importance_score INTEGER DEFAULT 5,  -- 1-10
    morphable BOOLEAN DEFAULT TRUE,
    morph_history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Disruptions
CREATE TABLE disruptions (
    disruption_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    storyline_id UUID NOT NULL REFERENCES storylines(storyline_id),
    disruption_type VARCHAR(50),  -- outside_event, player_action, etc.
    disruption_description TEXT,
    severity VARCHAR(20),  -- minor, moderate, critical
    response_action VARCHAR(50),  -- pause, redirect, complete, adapt
    created_at TIMESTAMP DEFAULT NOW()
);

-- Player capacity tracking
CREATE TABLE player_capacity (
    player_id UUID PRIMARY KEY REFERENCES players(id),
    max_storylines INTEGER DEFAULT 5,
    max_complexity FLOAT DEFAULT 50.0,
    optimal_major_count INTEGER DEFAULT 2,
    optimal_minor_count INTEGER DEFAULT 3,
    last_prediction TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(50)
);

-- Path complexity tracking
CREATE TABLE path_complexity (
    path_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    storyline_ids JSONB NOT NULL,  -- Array of storyline IDs
    complexity_score FLOAT NOT NULL,
    factors JSONB,  -- {storyline_count, dependencies, choice_points, ...}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_storylines_player_state ON storylines(player_id, state);
CREATE INDEX idx_storylines_world_state ON storylines(world_state_id);
CREATE INDEX idx_end_goals_storyline ON end_goals(storyline_id);
CREATE INDEX idx_disruptions_storyline ON disruptions(storyline_id);
```

---

## 7. INTEGRATION WITH WORLD SIMULATION

### 7.1 World State Validation Integration

```python
# In world_simulation_engine.py
class WorldSimulationEngine:
    def __init__(self):
        # ... existing code ...
        self.cohesion_system = CohesionSystem()
    
    async def _process_simulation_cycle(self):
        # ... existing simulation logic ...
        
        # Before applying state changes, validate
        validation_result = await self.cohesion_system.guard_rails.validate_world_state(
            world_state=self._simulation_state,
            proposed_changes=proposed_state_changes
        )
        
        if not validation_result.passed:
            # Reject changes that violate cohesion
            await self._handle_validation_failure(validation_result)
            return
        
        # Apply validated changes
        self._simulation_state.update(proposed_state_changes)
```

### 7.2 Storyline Tracking Integration

```python
# In story_teller service
class StoryTellerService:
    def __init__(self):
        # ... existing code ...
        self.cohesion_system = CohesionSystem()
    
    async def generate_storyline(
        self,
        player_id: str,
        world_state_id: str
    ):
        # Check storyline limit
        limit_check = await self.cohesion_system.storyline_limiter.check_storyline_limit(
            player_id=player_id,
            requested_storylines=[new_storyline_id]
        )
        
        if not limit_check.allowed:
            # Prevent overwhelm
            await self.cohesion_system.storyline_limiter.prevent_overwhelm(player_id)
            return None
        
        # Generate storyline
        storyline = await self._generate_storyline(...)
        
        # Register with tracker
        await self.cohesion_system.storyline_tracker.register_storyline(
            storyline_id=storyline.id,
            storyline_type=storyline.type,
            end_goal=storyline.end_goal,
            dependencies=storyline.dependencies
        )
        
        return storyline
```

---

## 8. API DESIGN

```python
# Validate world state changes
POST /api/v1/cohesion/validate-world-state
Request: {
    "world_state": {...},
    "proposed_changes": {...}
}
Response: {
    "passed": true/false,
    "reason": "...",
    "violations": [...]
}

# Register storyline
POST /api/v1/cohesion/storyline/register
Request: {
    "storyline_id": "uuid",
    "storyline_type": "major",
    "end_goal": {...},
    "dependencies": [...]
}

# Check storyline limit
POST /api/v1/cohesion/storyline/check-limit
Request: {
    "player_id": "uuid",
    "requested_storylines": [...]
}
Response: {
    "allowed": true/false,
    "current_count": 3,
    "capacity": 5
}

# Handle disruption
POST /api/v1/cohesion/disruption/handle
Request: {
    "storyline_id": "uuid",
    "disruption_event": {...}
}
Response: {
    "action_taken": "pause",
    "new_state": "paused"
}
```

---

**END OF SOLUTION DOCUMENT**




