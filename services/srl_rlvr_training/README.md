# SRL→RLVR Training System Service

Production-ready training system for small AI models using Google's SRL→RLVR approach.

## Service Structure

```
srl_rlvr_training/
├── collaboration/      # Three-model collaboration (Lore Retriever, Teacher Planner, Verifier)
├── srl/                # SRL training pipeline (step-wise supervised rewards)
├── rlvr/               # RLVR fine-tuning pipeline (outcome-based rewards)
├── models/             # Model-specific training modules (7 model types)
├── dynamic/            # Dynamic systems (model selection, example generation, rules)
├── performance/        # Performance tracking and weakness detection
├── paid/               # Paid model fine-tuning (Gemini, ChatGPT, Anthropic)
├── api/                # FastAPI REST API endpoints
├── orchestration/      # AWS Step Functions integration
├── data/               # Data management and curation
└── tests/              # Comprehensive test suite
```

## Quick Start

See `docs/solutions/SRL-RLVR-TRAINING-SYSTEM-ENHANCED.md` for complete architecture.

See `docs/tasks/SRL-RLVR-TRAINING-TASKS.md` for implementation tasks.

## Key Principles

1. **Never Static Examples**: All training examples generated dynamically
2. **Three-Model Collaboration**: Expert trajectories via collaboration
3. **SRL → RLVR**: Step-wise then outcome-based rewards
4. **All Model Types**: Personality, facial, buildings, animals, plants, trees, sounds
5. **Dynamic Selection**: Responsibility-based model selection with cost-benefit
6. **Performance Tracking**: Continuous monitoring and weakness detection

## AWS Deployment

All training runs in AWS:
- **SageMaker**: Training jobs and endpoints
- **Step Functions**: Orchestration
- **S3**: Data storage
- **DynamoDB**: Metadata and tracking
- **CloudWatch**: Monitoring and logging

See `docs/solutions/SRL-RLVR-TRAINING-SYSTEM-ENHANCED.md` for deployment details.

