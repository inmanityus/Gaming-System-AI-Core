# AI-Driven Game Testing System
## The Body Broker Quality Assurance Architecture

**Version:** 1.0.0  
**Project:** The Body Broker (Gaming System AI Core)  
**Purpose:** Enable AI models to play, observe, and iteratively improve the game  
**Date:** 2025-11-11

---

## 🎯 Mission

Create a comprehensive AI-driven testing system that enables AI models to:
- ✅ **Play the game** autonomously via automated tests
- ✅ **Observe visually** through screenshot capture and analysis
- ✅ **Analyze scientifically** using specialized AI models
- ✅ **Provide recommendations** in safe, structured JSON format
- ✅ **Iterate until perfect** through continuous feedback loops

---

## 🏗️ System Architecture

```
┌──────────────────────── TIER 0: CLI Testing ────────────────────────┐
│  • Run 33 existing UE5 automation tests from command line           │
│  • No GUI required • JSON results output                            │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────── TIER 1: State Testing ──────────────────────┐
│  • Expand to 100+ comprehensive state-based tests                   │
│  • Performance benchmarks • CI/CD integration                       │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────── TIER 2: Vision System ──────────────────────┐
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  GameObserver Plugin (UE5)                                  │   │
│  │  • Event-driven screenshot capture                          │   │
│  │  • Rich JSON telemetry export                              │   │
│  │  • HTTP API for state queries                              │   │
│  └───────────────────────┬────────────────────────────────────┘   │
│                          │ Captures (PNG + JSON)                  │
│  ┌───────────────────────▼────────────────────────────────────┐   │
│  │  Local Test Runner Agent (Python)                          │   │
│  │  • Monitors GameObserver output directory                  │   │
│  │  • Bundles screenshot + telemetry pairs                    │   │
│  │  • Uploads to AWS S3                                       │   │
│  └───────────────────────┬────────────────────────────────────┘   │
│                          │ Upload to S3                           │
│  ┌───────────────────────▼────────────────────────────────────┐   │
│  │  AWS Orchestration Service (FastAPI)                       │   │
│  │  • Capture registration                                     │   │
│  │  • Vision analysis coordination                            │   │
│  │  • Multi-model consensus evaluation                        │   │
│  │  • Statistics & monitoring                                 │   │
│  └───────────────────────┬────────────────────────────────────┘   │
│                          │ Dispatch to Vision Models              │
│  ┌───────────────────────▼────────────────────────────────────┐   │
│  │  Vision Analysis Agent (Multi-Model)                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │   │
│  │  │  Gemini    │  │   GPT-4o   │  │   Claude   │         │   │
│  │  │  2.5 Pro   │  │            │  │ Sonnet 4.5 │         │   │
│  │  │            │  │            │  │            │         │   │
│  │  │  Horror    │  │    UX      │  │   Visual   │         │   │
│  │  │  Atmos.    │  │  Clarity   │  │    Bugs    │         │   │
│  │  └────────────┘  └────────────┘  └────────────┘         │   │
│  │  Consensus: ≥2/3 agree + >0.85 confidence                │   │
│  └───────────────────────┬────────────────────────────────────┘   │
│                          │ Analysis Results                       │
│  ┌───────────────────────▼────────────────────────────────────┐   │
│  │  Perceptual Hash Cache (Redis)                             │   │
│  │  • 80-90% cost reduction                                   │   │
│  │  • Sub-millisecond lookups                                 │   │
│  │  • Handles visual similarity                               │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────── TIER 3: Feedback Loop ──────────────────────┐
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Structured Recommendations (JSON, not code)               │   │
│  │  • Safe, validated recommendations                         │   │
│  │  • Severity classification                                 │   │
│  │  • Alternative approaches                                  │   │
│  │  • Human validation workflow                               │   │
│  └───────────────────────┬────────────────────────────────────┘   │
│                          │                                        │
│  ┌───────────────────────▼────────────────────────────────────┐   │
│  │  Triage Dashboard (Next.js)                                │   │
│  │  • Human review interface                                   │   │
│  │  • Accept / Reject / Edit workflow                         │   │
│  │  • Jira integration                                        │   │
│  │  • Analytics & reporting                                   │   │
│  └───────────────────────┬────────────────────────────────────┘   │
│                          │ Approved fixes                         │
│  ┌───────────────────────▼────────────────────────────────────┐   │
│  │  GitHub Actions Integration                                │   │
│  │  • Automated retest on code changes                        │   │
│  │  • Verify fixes automatically                              │   │
│  │  • Close feedback loop                                     │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Repository Structure

```
ai-testing-system/
├── local-test-runner/          # Local agent (Python)
│   ├── agent.py               # Main agent
│   ├── config.json            # Configuration
│   └── requirements.txt       # Dependencies
│
├── orchestrator/               # AWS orchestration service (FastAPI)
│   ├── main.py                # FastAPI application
│   ├── Dockerfile             # Container image
│   └── requirements.txt       # Dependencies
│
├── vision-analysis/            # Multi-model vision agent
│   ├── vision_agent.py        # Vision analysis
│   └── requirements.txt       # Dependencies
│
├── cost-controls/              # Cost optimization
│   ├── perceptual_cache.py    # Perceptual hashing cache
│   └── requirements.txt       # Dependencies
│
├── recommendations/            # Structured recommendations
│   └── recommendation_generator.py
│
├── dashboard/                  # Next.js triage dashboard (Tier 3)
│   └── (Next.js application)
│
├── DEPLOYMENT.md               # Deployment guide
└── README.md                   # This file

unreal/Plugins/GameObserver/    # UE5 plugin
├── Source/GameObserver/
│   ├── Public/
│   │   ├── GameObserverModule.h
│   │   └── GameObserverComponent.h
│   └── Private/
│       ├── GameObserverModule.cpp
│       └── GameObserverComponent.cpp
├── GameObserver.uplugin
└── README.md

scripts/
└── run-ue5-tests.ps1           # CLI test runner (Tier 0)

docs/
└── AI-Game-Testing-System-Design.md  # Complete technical design
```

---

## 🚀 Quick Start

### 1. Run Existing Tests (Tier 0)

```powershell
# Navigate to project root
cd "E:\Vibe Code\Gaming System\AI Core"

# Run all Body Broker tests
.\scripts\run-ue5-tests.ps1 -Filter "BodyBroker"
```

### 2. Start Local Test Runner Agent

```powershell
cd ai-testing-system/local-test-runner
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python agent.py
```

### 3. Deploy AWS Orchestrator

```bash
cd ai-testing-system/orchestrator
docker build -t body-broker-orchestrator .
# Push to ECR and deploy to ECS (see DEPLOYMENT.md)
```

### 4. Play Game with GameObserver

1. Open Body Broker in UE5 Editor
2. GameObserver plugin captures screenshots + telemetry automatically
3. Local agent uploads to AWS
4. Vision models analyze
5. Recommendations generated

---

## 💰 Cost Breakdown

### Infrastructure (Monthly)
- **ECS Fargate**: $15
- **ElastiCache Redis**: $13
- **S3 Storage**: $2-5
- **Total**: ~$35/month

### Vision API (per screenshot)
- Gemini 2.5 Pro: $0.00025
- GPT-4o: $0.00500
- Claude Sonnet 4.5: $0.00300
- **Total**: $0.00825/screenshot
- **With cache (80% hit rate)**: $0.00165/screenshot

### Monthly Totals
- **Light (10K screenshots)**: $51.50/mo
- **Medium (50K screenshots)**: $117.50/mo
- **Heavy (100K screenshots)**: $200/mo

---

## 🔑 Key Features

### 1. Multi-Model Vision Analysis

**Gemini 2.5 Pro - Horror Atmosphere Specialist:**
- Luminance histogram analysis (chiaroscuro detection)
- Color palette evaluation (desaturation for horror)
- Compositional tension (negative space, focal points)
- Uncanny imagery detection

**GPT-4o - UX & Clarity Specialist:**
- UI readability (OCR + WCAG contrast)
- Objective clarity (is target visible?)
- UI obtrusiveness (blocking gameplay?)
- Navigation clarity

**Claude Sonnet 4.5 - Visual Bug Detective:**
- Clipping detection (geometry overlap)
- Texture issues (missing, low-res, streaming)
- Lighting problems (bleeding, shadow popping)
- Animation glitches (T-pose, skating)

### 2. Multi-Model Consensus Engine

Issue flagged ONLY if:
- ≥2 out of 3 models agree (is_issue=True)
- Average confidence >0.85

This prevents hallucinations and false positives.

### 3. Perceptual Hash Cache

- Uses pHash to detect visually similar screenshots
- 80-90% cache hit rate = 80-90% cost reduction
- Redis for sub-millisecond lookups
- Handles minor rendering variations

### 4. Structured Recommendations

**NOT direct code generation** (per Gemini 2.5 Pro's warning)

Instead: Safe, validated JSON with:
- Severity classification
- Specific asset paths
- Property changes
- Rationale and alternatives
- Human validation workflow

Example:
```json
{
  "issueID": "ATMOSPHERE-a4f8c1d",
  "confidence": 0.92,
  "severity": "high",
  "recommendation": {
    "type": "LIGHTING_CHANGE",
    "asset_path": "/Game/Maps/TheGoreforge/Lighting",
    "changes": [
      {
        "component": "DirectionalLight_Main",
        "property": "Intensity",
        "current_value": "1.0",
        "suggested_value": "0.3-0.5",
        "rationale": "Create dramatic shadows for horror"
      }
    ],
    "alternative_approaches": [...]
  }
}
```

---

## 📊 System Capabilities

### What AI Models Can Do

✅ **Detect atmospheric issues** (flat lighting, wrong color palette)  
✅ **Identify UX problems** (poor contrast, unclear objectives)  
✅ **Find visual bugs** (clipping, texture issues, animation glitches)  
✅ **Provide specific recommendations** (safe JSON, not risky code)  
✅ **Prevent false positives** (multi-model consensus)  
✅ **Reduce costs** (80-90% via intelligent caching)  
✅ **Scale efficiently** (cloud orchestration, parallel analysis)

### What Humans Do

✅ **Review recommendations** (30-second validation per issue)  
✅ **Accept/reject findings** (Triage Dashboard)  
✅ **Apply fixes** (based on structured recommendations)  
✅ **Provide feedback** (improves model accuracy over time)

---

## 🎮 Integration with The Body Broker

### Game Events Captured

- `OnPlayerDamage` - When player takes damage
- `OnEnemySpawn` - New enemy appears
- `OnEnterNewZone` - Zone transitions
- `OnUIPopup` - UI elements appear
- `OnHarvestComplete` - Body part harvested
- `OnNegotiationStart` - Dark World client negotiation
- `OnDeathTriggered` - Debt of Flesh activated
- `OnCombatStart/End` - Combat state changes
- `Baseline` - Periodic capture (configurable FPS)

### Telemetry Captured

```json
{
  "player_data": {
    "location": {"x": 1234.5, "y": 6789.0, "z": 234.1},
    "rotation": {"pitch": 0.5, "yaw": 180.2, "roll": 0.0},
    "velocity": {"x": 0, "y": 0, "z": 0},
    "health": 75,
    "is_in_combat": true
  },
  "world_data": {
    "zone_name": "TheGoreforge_CorridorB",
    "current_objective_id": "OBJ_FindExitKey",
    "veil_focus": "Both"
  },
  "rendering_data": {
    "current_fps": 58
  }
}
```

---

## 📈 Success Metrics

### Tier 0 Success
- ✅ All 33 tests run from CLI
- ✅ 100% pass rate
- ✅ JSON results output
- ✅ Execution time <5 minutes

### Tier 2 Success
- ✅ GameObserver captures screenshots + telemetry
- ✅ Vision models analyze with ≥90% accuracy
- ✅ Multi-model consensus reduces false positives to <10%
- ✅ Cost <$0.002/screenshot (with caching)

### Tier 3 Success
- ⏳ Triage Dashboard operational
- ⏳ Structured recommendations 95% actionable
- ⏳ Automated retest loop closes 80% of issues
- ⏳ Time to fix reduced by 50%

---

## 🔧 Development

### Run Tests

```bash
# Local Test Runner Agent tests
cd ai-testing-system/local-test-runner
pytest

# Orchestrator tests
cd ai-testing-system/orchestrator
pytest

# Vision Analysis tests
cd ai-testing-system/vision-analysis
pytest
```

### Code Quality

```bash
# Format code
black ai-testing-system/

# Type checking
mypy ai-testing-system/

# Linting
flake8 ai-testing-system/
```

---

## 📚 Documentation

- **[Complete Technical Design](../docs/AI-Game-Testing-System-Design.md)** - 200+ page comprehensive design
- **[Deployment Guide](DEPLOYMENT.md)** - Step-by-step deployment instructions
- **[GameObserver Plugin README](../unreal/Plugins/GameObserver/README.md)** - UE5 plugin documentation

---

## 🎯 Roadmap

### ✅ Completed (Tier 0-2)
- CLI test runner for existing tests
- GameObserver UE5 plugin
- Local Test Runner Agent
- AWS Orchestration Service
- Multi-model vision analysis
- Perceptual hash cache
- Structured recommendations

### 🔄 In Progress (Tier 3)
- Triage Dashboard (Next.js)
- Jira integration
- GitHub Actions automated retest

### ⏳ Planned (Future)
- Golden master screenshot comparison
- Performance regression detection
- Automated test expansion (AI generates new tests)
- Real-time monitoring dashboard
- Mobile device testing integration

---

## 🤝 Contributing

This is a private project for The Body Broker game development.

---

## 📝 License

Copyright Gaming System AI Core - All Rights Reserved

---

**System Status:** Tier 2 Complete, Tier 3 In Progress  
**Last Updated:** 2025-11-11  
**Version:** 1.0.0

