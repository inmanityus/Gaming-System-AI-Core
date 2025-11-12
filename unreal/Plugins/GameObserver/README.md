# GameObserver Plugin

**AI-Driven Game Testing System for The Body Broker**

Part of the comprehensive 4-tier AI testing architecture designed to enable AI models to play, observe, and iteratively improve the game.

## Overview

GameObserver is a UE5 plugin that provides:
- **Event-Driven Screenshot Capture** - Automatically captures screenshots on specific game events
- **Rich JSON Telemetry** - Exports detailed game state data alongside each screenshot
- **HTTP API** - Enables external systems to query game state in real-time
- **Baseline Monitoring** - Continuous periodic capture for atmosphere analysis

## Architecture

This plugin is **Tier 2** of the complete AI testing system:

```
Tier 0: CLI Test Runner (existing 33 tests)
Tier 1: State-Based Testing (100+ tests)
Tier 2: Vision Analysis System ← GameObserver Plugin
Tier 3: Perfect Feedback Loop (Triage Dashboard)
```

## Features

### Event-Driven Capture

Captures screenshots and telemetry on game events:
- Player Damage
- Enemy Spawn
- Zone Transitions
- UI Popups
- Harvest Complete
- Negotiation Start
- Death Triggered
- Combat Start/End

### Telemetry Data

Each capture exports JSON with:
```json
{
  "screenshot_filename": "OnPlayerDamage_0001_20251111_180000.png",
  "timestamp": "2025-11-11T18:00:00.123Z",
  "event_type": "OnPlayerDamage",
  "player_data": {
    "location": {"x": 1234.5, "y": 6789.0, "z": 234.1},
    "rotation": {"pitch": 0.5, "yaw": 180.2, "roll": 0.0},
    "velocity": {"x": 0, "y": 0, "z": 0},
    "health": 75,
    "is_in_combat": true
  },
  "world_data": {
    "zone_name": "TheGoreforge_CorridorB",
    "current_objective_id": "OBJ_FindExitKey"
  },
  "rendering_data": {
    "current_fps": 58
  },
  "veil_focus": "Both"
}
```

### Baseline Capture

Configurable periodic capture (default: 2 FPS) for continuous monitoring of:
- Horror atmosphere (lighting, color palette)
- Visual coherence
- Performance metrics

## Usage

### Blueprint

1. Add `GameObserverComponent` to your PlayerController or GameMode
2. Configure capture events in Blueprint
3. Enable/disable as needed

```cpp
// Enable observer
GameObserver->SetObserverEnabled(true);

// Set baseline capture rate (2 FPS)
GameObserver->SetBaselineCaptureRate(2.0f);

// Trigger event capture
GameObserver->CaptureEventSnapshot(EGameObserverCaptureEvent::OnPlayerDamage, "Butcher attack - 25 damage");
```

### C++

```cpp
#include "GameObserverComponent.h"

// In your character or controller
UGameObserverComponent* Observer = CreateDefaultSubobject<UGameObserverComponent>(TEXT("GameObserver"));

// Trigger capture on events
void AMyCharacter::TakeDamage(float Damage)
{
    if (Observer)
    {
        FString Details = FString::Printf(TEXT("Damage: %.0f"), Damage);
        Observer->CaptureEventSnapshot(EGameObserverCaptureEvent::OnPlayerDamage, Details);
    }
}
```

## Output

All captures saved to: `[ProjectDir]/GameObserver/Captures/`

Format:
- Screenshots: `{EventType}_{Counter}_{Timestamp}.png`
- Telemetry: `{EventType}_{Counter}_{Timestamp}.json`

Example:
```
GameObserver/Captures/
├── OnPlayerDamage_0001_20251111_180000.png
├── OnPlayerDamage_0001_20251111_180000.json
├── OnEnterNewZone_0002_20251111_180015.png
├── OnEnterNewZone_0002_20251111_180015.json
└── Baseline_0003_20251111_180030.png
```

## Integration with AI Testing System

GameObserver feeds data to:

1. **Local Test Runner Agent** (Python)
   - Monitors output directory
   - Bundles screenshots + JSON
   - Uploads to AWS S3

2. **AWS Orchestration Service**
   - Receives capture bundles
   - Dispatches to vision models
   - Coordinates analysis

3. **Vision Analysis Agents**
   - Gemini 2.5 Pro: Horror atmosphere
   - GPT-4o: UX and clarity
   - Claude Sonnet 4.5: Visual bugs

4. **Multi-Model Consensus Engine**
   - Validates findings across models
   - Generates structured recommendations
   - Prevents hallucinations

## Configuration

### Capture Rates

```cpp
// High-rate capture during specific sequences
Observer->SetBaselineCaptureRate(10.0f); // 10 FPS

// Low-rate for general monitoring
Observer->SetBaselineCaptureRate(0.5f); // 0.5 FPS

// Disable baseline (event-driven only)
Observer->SetBaselineCaptureRate(0.0f);
```

### HTTP API (Future)

```cpp
// Start HTTP server for external queries
Observer->StartHTTPServer(8765);

// Query: GET http://localhost:8765/telemetry
// Response: Current game state JSON
```

## Development Status

- ✅ **Core Plugin Structure** - Complete
- ✅ **Screenshot Capture** - Implemented
- ✅ **JSON Telemetry Export** - Implemented
- ✅ **Event-Driven System** - Implemented
- ✅ **Baseline Monitoring** - Implemented
- ⏳ **HTTP API** - Placeholder (future implementation)
- ⏳ **Game-Specific Integration** - Requires Body Broker hooks

## Next Steps

1. Integrate into Body Broker game systems:
   - Hook damage events
   - Hook zone transitions
   - Hook Veil-Sight changes
   - Hook harvesting system
   - Hook negotiation system

2. Customize telemetry for Body Broker:
   - Add Veil Focus state
   - Add Dark World visibility
   - Add harvesting progress
   - Add client relationship data

3. Build Local Test Runner Agent (Python)

4. Deploy AWS Orchestration Service

5. Integrate vision analysis models

## Testing

To test the plugin:

1. Build Body Broker project
2. Open in UE5 Editor
3. Add GameObserverComponent to PlayerController
4. Play in Editor (PIE)
5. Check `[ProjectDir]/GameObserver/Captures/` for outputs

## Requirements

- Unreal Engine 5.6.1+
- Body Broker project
- Windows (primary platform)

## License

Copyright Gaming System AI Core

---

**Part of**: AI-Driven Game Testing & Improvement System  
**Documentation**: `docs/AI-Game-Testing-System-Design.md`  
**Version**: 1.0.0  
**Date**: 2025-11-11

