# "The Body Broker" - AI-Driven Gaming Core

**Project**: AI-powered horror game with dynamic NPCs and procedural content generation  
**Engine**: Unreal Engine 5.6+  
**Platform**: Steam + PC (Windows 10/11)  
**Status**: Architecture Complete - Ready for Implementation

---

## 🎮 PROJECT OVERVIEW

"The Body Broker" is a horror game where players operate as a body broker between two worlds:
- **Day World**: Rob morgues, build labs, grow body parts, acquire supernatural powers
- **Night World**: Sell parts to monsters, navigate house politics, survive being hunted

### Key Innovation
**Hierarchical 4-layer LLM architecture** that enables:
- Dynamic NPC dialogue (not pre-written scripts)
- Procedural content generation with AI assistance
- Emergent narrative experiences unique to each player
- Real-time adaptation to player choices

---

## 🏗️ ARCHITECTURE

### Service Modules (8 Integrated Services)
1. **Game Engine Service** - Unreal Engine 5 integration, gameplay mechanics
2. **AI Inference Service** - LLM model serving (Ollama/vLLM)
3. **Orchestration Service** - 4-layer hierarchical pipeline coordination
4. **Payment Service** - Stripe integration, subscriptions
5. **State Management Service** - Redis/PostgreSQL/Vector DB
6. **Learning Service** - AWS SageMaker continuous improvement pipeline
7. **Moderation Service** - Content safety, guardrails
8. **Settings Service** - Configuration management

### AI Infrastructure
- **Local Models**: Ollama (Tier 1/2/3 NPCs)
- **Cloud Models**: 9 API providers (Claude 4.5, GPT-5, DeepSeek V3.1, GLM, Kimi, etc.)
- **Hybrid Approach**: 80% local (cost-effective), 20% cloud (orchestration)

---

## 📁 PROJECT STRUCTURE

```
Gaming-System-AI-Core/
├── docs/
│   ├── Requirements.md              # Complete requirements
│   ├── RECOMMENDATIONS.md            # Technical recommendations
│   ├── solutions/                   # Service solution documents
│   ├── tasks/                       # Task breakdown
│   ├── OLLAMA-MODELS-AVAILABLE.md   # Local model inventory
│   ├── API-KEYS-CONFIGURATION.md    # API provider setup
│   └── ACTUAL-DEPLOYMENT-CONFIGURATION.md
├── scripts/
│   ├── test-azure-ai.ps1            # Test Azure deployments
│   ├── test-all-providers.ps1      # Test all API providers
│   ├── test-ollama-models.ps1      # Test local models
│   └── test-aws-sagemaker.ps1      # Test AWS access
├── .env.example                    # Environment template
└── README.md                       # This file
```

---

## 🚀 QUICK START

### Prerequisites
- Unreal Engine 5.6+
- Ollama (local LLM serving)
- AWS CLI (SageMaker access)
- 2x RTX 5090 (32GB each) or equivalent

### API Providers Configured (9 Total)
1. Azure AI (MAI-DS-R1, DeepSeek-V3.1, Sora)
2. OpenAI Direct
3. DeepSee Direct
4. Anthropic (Claude)
5. Google Gemini
6. OpenRouter AI
7. Hugging Face
8. Moonshot (Kimi)
9. GLM (Zhipu AI)

### Setup
1. Copy `.env.example` to `.env` and fill in API keys
2. Pull Ollama models: `ollama pull llama3.1:8b mistral:7b phi3:mini`
3. Verify AWS access: `aws sts get-caller-identity`
4. Review `docs/tasks/GLOBAL-MANAGER.md` for build order

---

## 📚 DOCUMENTATION

### Core Documents
- **[Requirements.md](docs/Requirements.md)** - Complete game requirements
- **[RECOMMENDATIONS.md](docs/RECOMMENDATIONS.md)** - Technical recommendations
- **[SOLUTION-ANALYSIS.md](docs/SOLUTION-ANALYSIS.md)** - Service decomposition

### Solution Documents
- `docs/solutions/` - Detailed technical solutions for each service

### Task Management
- `docs/tasks/GLOBAL-MANAGER.md` - Master coordination file
- `docs/tasks/*-TASKS.md` - Service-specific task breakdowns

### Configuration
- `docs/API-KEYS-CONFIGURATION.md` - API provider setup
- `docs/OLLAMA-MODELS-AVAILABLE.md` - Local model inventory
- `docs/AWS-SAGEMAKER-SETUP.md` - AWS configuration

---

## 🔧 DEVELOPMENT

### Testing
```powershell
# Test all API providers
.\scripts\test-all-providers.ps1

# Test Ollama models
.\scripts\test-ollama-models.ps1

# Test AWS SageMaker
.\scripts\test-aws-sagemaker.ps1

# Test Azure AI
.\scripts\test-azure-ai.ps1
```

### Implementation Phases
See `docs/tasks/GLOBAL-MANAGER.md` for complete build order and dependencies.

---

## 🔒 SECURITY

- ⚠️ **Never commit `.env` file** - Contains API keys
- ✅ `.env` is in `.gitignore`
- ✅ Use `.env.example` as template
- ✅ Rotate keys if exposed

---

## 📊 CURRENT STATUS

✅ **Architecture**: Complete (8 services designed)  
✅ **Requirements**: Fully documented  
✅ **API Providers**: 9 providers configured  
✅ **Local Models**: Ollama models verified  
✅ **AWS Services**: SageMaker access confirmed  
✅ **Tasks**: Broken down and ready  
⏭️ **Implementation**: Ready to begin Phase 1

---

## 🤝 CONTRIBUTING

This is a private project. For access, contact the project owner.

---

## 📝 LICENSE

Private project - All rights reserved

---

**Last Updated**: January 29, 2025  
**Version**: Architecture Complete - Pre-Implementation

