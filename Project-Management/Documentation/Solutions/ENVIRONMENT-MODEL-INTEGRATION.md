# Environment Model Integration Solution
**Date**: January 29, 2025  
**Status**: Implemented

---

## OVERVIEW

Comprehensive solution for managing environment, landscape, and building AI models with:
- Light-Dark-Texture requirement validation
- AI Management System integration
- Story teller feature awareness
- Cross-world consistency enforcement

---

## ARCHITECTURE

### Components

1. **EnvironmentModelRegistry** - Specialized model registry for environment models
2. **FeatureAwareness** - Makes story teller aware of all available features
3. **CrossWorldConsistency** - Ensures consistent asset generation across worlds
4. **Integration with NarrativeGenerator** - Automatic feature context injection

---

## LIGHT-DARK-TEXTURE REQUIREMENTS

### Lighting Requirements

**Day World**:
- Bright sunshine
- Deep shadows
- Dark tunnels and underpasses
- Bright sparkling snow
- Vibrant meadows
- Sparkling creeks
- Deep blue waters
- Rainbows and lightning

**Dark World**:
- Deep darkness
- Pools of light
- Bright bars
- Dimly lit back alleys
- Bright moonlight (goes black when cloud passes)
- Shockingly bright spears of lightning
- Flashlight beams
- Dimly lit lamps
- Candlelight showing small regions

### Texture Requirements

Examples:
- Metal gleam
- Ancient stone/castle walls
- Polished new car
- Weathered old wagon
- Wooden floors
- Shiny mosaic tiles
- Blood glistening on wicked blades

### Destruction Requirements

Examples:
- Half destroyed buildings
- Demolished structures
- Broken chairs and doors
- Old and moldy interiors
- Holes smashed through windows and walls

### Creation Requirements

Examples:
- Young flowers growing
- Death vines expanding
- Spring blossoms
- Sparkling fresh water
- Beauty explosions

---

## MODEL REGISTRATION

### Register Environment Model

```python
from services.model_management.environment_model_registry import EnvironmentModelRegistry

registry = EnvironmentModelRegistry()

# Register a landscape model
model_id = await registry.register_environment_model(
    model_name="terrain-generator-v1",
    model_type="self_hosted",
    provider="huggingface",
    environment_category="environment_landscape",
    version="1.0.0",
    model_path="/models/terrain-generator",
    lighting_specs={
        "brightness_range": [0.1, 1.0],
        "shadow_casting": True,
        "atmosphere_type": "natural",
        "world_types": ["day", "dark"],
        "day_brightness": "high",
        "day_atmosphere": "bright_sunshine",
        "dark_brightness": "low",
        "dark_atmosphere": "moonlight",
    },
    texture_specs={
        "material_type": "natural",
        "texture_maps": ["diffuse", "normal", "roughness"],
        "surface_properties": ["snow", "meadow", "water", "stone"],
    },
    creation_specs={
        "growth_states": ["seedling", "growing", "mature"],
        "construction_phases": ["initial", "developing", "complete"],
        "creation_effects": ["bloom", "sparkle", "growth"],
    },
    resource_requirements={
        "vram_gb": 4,
        "compute_units": 2,
    },
)
```

### Environment Categories

- `environment_landscape` - Terrain, vegetation, water, natural features
- `environment_building_exterior` - Building exteriors, facades, structural elements
- `environment_building_interior` - Interior spaces, rooms, furniture, decorations
- `environment_lighting` - Lighting systems, shadows, atmosphere
- `environment_texture` - Material textures, surface properties, weathering
- `environment_destruction` - Damage states, destruction effects, decay
- `environment_creation` - Growth, construction, restoration effects

---

## FEATURE AWARENESS

### Story Teller Integration

The `FeatureAwareness` system automatically injects feature context into narrative generation prompts:

```python
from services.story_teller.feature_awareness import FeatureAwareness

awareness = FeatureAwareness()

# Get all available features
all_features = await awareness.get_all_features()

# Get feature-specific instructions
instructions = await awareness.get_feature_instructions(
    feature_type="environment_landscape",
    context={"world_type": "day"},
)

# Build context for story teller
context = await awareness.build_story_teller_prompt_context(
    world_type="day",
    location_type="landscape",
)
```

### Available Features

The system automatically discovers:
- Environment models (landscape, buildings, lighting, textures)
- Narrative models
- NPC models
- World generation capabilities
- Light-Dark-Texture system specifications

---

## CROSS-WORLD CONSISTENCY

### Create Canonical Template

```python
from services.story_teller.cross_world_consistency import CrossWorldConsistency

consistency = CrossWorldConsistency()

# Create canonical building template
template = await consistency.create_canonical_template(
    asset_type="building",
    asset_name="old_warehouse",
    canonical_description="A three-story warehouse with brick exterior and large windows",
    ldt_specs={
        "lighting": {
            "brightness_range": [0.3, 0.8],
            "shadow_casting": True,
            "world_types": ["day", "dark"],
        },
        "textures": {
            "material_type": "brick",
            "texture_maps": ["diffuse", "normal", "roughness"],
            "surface_properties": ["weathered", "aged"],
        },
        "destruction": {
            "damage_states": ["intact", "damaged", "half_destroyed", "demolished"],
            "physics_properties": {"structural": True},
        },
    },
    generation_parameters={
        "seed": 12345,
        "style": "industrial",
        "era": "modern",
    },
)
```

### Generate Asset from Template

```python
# Generate asset for a specific world
asset_spec = await consistency.generate_asset_from_template(
    template=template,
    world_id=world_id,
    world_type="day",
    modifications={
        "destruction": {
            "damage_states": "half_destroyed",
            "destruction_effects": ["broken_windows", "collapsed_roof"],
        },
    },
)

# Same building in different world with modifications
asset_spec_dark = await consistency.generate_asset_from_template(
    template=template,
    world_id=another_world_id,
    world_type="dark",
    modifications={
        "destruction": {
            "damage_states": "intact",  # Different state
        },
    },
)
```

### Verify Consistency

```python
# Verify asset is consistent across worlds
verification = await consistency.verify_consistency(
    asset_name="old_warehouse",
    world_ids=[world_id_1, world_id_2, world_id_3],
)

print(f"Consistent: {verification['consistent']}")
print(f"Template Hash: {verification['template_hash']}")
```

---

## INTEGRATION WITH NARRATIVE GENERATOR

The `NarrativeGenerator` automatically includes feature awareness context:

```python
from services.story_teller.narrative_generator import NarrativeGenerator

generator = NarrativeGenerator()

# Generate narrative - automatically includes feature context
narrative = await generator.generate_narrative(
    player_id=player_id,
    node_type="exploration",
    title="Exploring the Warehouse District",
    description="Player discovers an old warehouse",
    context_hints={
        "location_type": "building_exterior",
        "world_type": "day",
    },
)
```

The prompt automatically includes:
- All available environment models
- Light-Dark-Texture specifications
- World generation capabilities
- Feature-specific instructions

---

## DATABASE SCHEMA

### Asset Templates Table

```sql
CREATE TABLE asset_templates (
    template_id UUID PRIMARY KEY,
    asset_type VARCHAR(100) NOT NULL,
    asset_name VARCHAR(255) NOT NULL,
    canonical_description TEXT NOT NULL,
    ldt_specs JSONB DEFAULT '{}',
    generation_parameters JSONB DEFAULT '{}',
    template_hash VARCHAR(64) NOT NULL UNIQUE,
    model_id UUID REFERENCES models(model_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Asset Generations Table

```sql
CREATE TABLE asset_generations (
    generation_id UUID PRIMARY KEY,
    template_id UUID REFERENCES asset_templates(template_id),
    world_id UUID NOT NULL,
    world_type VARCHAR(20) NOT NULL,
    generation_prompt TEXT NOT NULL,
    ldt_specs JSONB DEFAULT '{}',
    modifications JSONB DEFAULT '{}',
    template_hash VARCHAR(64) NOT NULL,
    generated_asset_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## USAGE EXAMPLES

### Example 1: Register Landscape Model

```python
registry = EnvironmentModelRegistry()

model_id = await registry.register_environment_model(
    model_name="landscape-generator-v2",
    model_type="self_hosted",
    provider="ollama",
    environment_category="environment_landscape",
    version="2.0.0",
    lighting_specs={
        "brightness_range": [0.2, 1.0],
        "shadow_casting": True,
        "world_types": ["day", "dark"],
    },
    texture_specs={
        "material_type": "natural",
        "texture_maps": ["diffuse", "normal"],
    },
    creation_specs={
        "growth_states": ["seedling", "mature"],
    },
)
```

### Example 2: Story Teller Directs Building Creation

```python
# Story teller wants to create a building
template = await consistency.create_canonical_template(
    asset_type="building",
    asset_name="police_station",
    canonical_description="A two-story police station with stone facade and large front entrance",
    ldt_specs={
        "lighting": {"world_types": ["day", "dark"]},
        "textures": {"material_type": "stone"},
    },
    generation_parameters={"style": "municipal"},
)

# Generate in player's world
asset = await consistency.generate_asset_from_template(
    template=template,
    world_id=player_world_id,
    world_type="day",
)
```

### Example 3: Story Teller Destroys Building

```python
# Get existing template
template = await consistency.get_canonical_template("police_station")

# Generate destroyed version
destroyed_asset = await consistency.generate_asset_from_template(
    template=template,
    world_id=player_world_id,
    world_type="dark",
    modifications={
        "destruction": {
            "damage_states": "half_destroyed",
            "destruction_effects": ["collapsed_wall", "broken_windows"],
        },
    },
)
```

---

## BENEFITS

1. **Consistency**: Same building looks identical across all worlds initially
2. **Flexibility**: Story teller can modify assets while maintaining version control
3. **Feature Awareness**: Story teller knows all available features automatically
4. **Resource Management**: Light-Dark-Texture requirements properly validated
5. **Integration**: Seamlessly integrated with AI Management System
6. **Minimal Instructions**: Expert models build based on minimal canonical descriptions

---

## MIGRATION

Run the database migration:

```bash
psql -h localhost -U postgres -d <database_name> -f database/migrations/009_asset_templates.sql
```

---

## TESTING

```python
# Test environment model registration
pytest tests/test_environment_model_registry.py

# Test feature awareness
pytest tests/test_feature_awareness.py

# Test cross-world consistency
pytest tests/test_cross_world_consistency.py
```

---

## FUTURE ENHANCEMENTS

1. Asset versioning system
2. Automatic asset regeneration on template updates
3. Asset preview generation
4. Batch asset generation
5. Asset template marketplace

