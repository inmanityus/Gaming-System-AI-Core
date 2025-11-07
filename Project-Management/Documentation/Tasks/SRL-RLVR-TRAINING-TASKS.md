# SRL→RLVR Training System - Comprehensive Task Breakdown
**Date**: 2025-01-29  
**Status**: Phase 3 Complete - Detailed Task Breakdown  
**Based On**: Consolidated Architecture (Phase 2)  
**Enforcement**: ALL rules in `/all-rules` are MANDATORY

---

## 📋 TASK ORGANIZATION

Tasks are organized by component/service. Each task includes:
- **Task ID**: Unique identifier
- **Title**: Clear task name  
- **Component**: Service/component name
- **Description**: Detailed requirements
- **Acceptance Criteria**: How to verify completion
- **Dependencies**: Prerequisites
- **Estimated Time**: Duration estimate
- **Watchdog Protocols**: Command protection protocol
- **Testing Requirements**: Test requirements (mandatory)

**Note**: This task breakdown is based on the comprehensive architecture. Detailed tasks follow the format from existing task files with gaming-specific model types.

---

## FOUNDATION: OBSERVABILITY, LOGGING, WATCHDOGS

### Task OBS-001: Structured Logging Library
**Component**: Observability  
**Description**: Implement Python logging library emitting structured JSON logs with context, tracing, PII redaction per /all-rules requirements.

**Deliverables**:
- `libs/logging/structured_logger.py`
- `libs/logging/context.py`
- `libs/logging/redaction.py`
- Config: `configs/logging.yaml`

**Acceptance Criteria**:
- All services emit structured JSON logs
- Logs include trace_id, request_id, session_id
- PII automatically redacted
- Dynamic log level control

**Dependencies**: None  
**Estimated Time**: 1.5 days  
**Watchdog Protocols**: Non-blocking queue handler, 2ms formatting budget  
**Testing Requirements**: Unit tests, integration tests, load tests (2k logs/sec)

---

### Task OBS-002: Watchdog Decorator and Circuit Breaker
**Component**: Observability  
**Description**: Implement watchdog decorator for time budgets, heartbeats, retries, circuit breakers per /all-rules.

**Deliverables**:
- `libs/watchdog/decorators.py`
- `libs/watchdog/circuit_breaker.py`
- `libs/watchdog/heartbeat.py`

**Acceptance Criteria**:
- @watchdog decorator works for sync/async functions
- Circuit breaker with Redis backend
- Heartbeats and retries functional

**Dependencies**: OBS-001  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Environment variable configuration, non-blocking events  
**Testing Requirements**: Unit tests, integration tests, fault injection tests

---

## DATA LAYER

### Task DATA-001: Game-Specific Data Schemas
**Component**: Data  
**Description**: Define Pydantic models and JSON Schemas for gaming models:
- PersonalityModelData (emotions, expressions, actions, traits)
- FacialExpressionData (emotions, blendshapes, AUs)
- BuildingData (exterior, interior, style, constraints)
- AnimalData (species, behavior, terrain, day/night)
- PlantData (species, biome, season, ecosystem)
- TreeData (species, season, environmental)
- SoundData (effects, music, context, mood)

**Deliverables**:
- `libs/schemas/personality.py`
- `libs/schemas/facial.py`
- `libs/schemas/buildings.py`
- `libs/schemas/animals.py`
- `libs/schemas/plants.py`
- `libs/schemas/trees.py`
- `libs/schemas/sounds.py`

**Acceptance Criteria**:
- JSON schemas versioned and validated
- All model types covered
- Schema validation <200ms per record

**Dependencies**: None  
**Estimated Time**: 1 day  
**Watchdog Protocols**: Schema validation time budget  
**Testing Requirements**: Unit tests, fuzz tests with hypothesis

---

### Task DATA-002: S3 Data Lake Setup (Terraform)
**Component**: Data Infrastructure  
**Description**: Create versioned, encrypted S3 buckets with lifecycle policies for gaming data:
- `raw/personality/`, `raw/facial/`, `raw/buildings/`, etc.
- `curated/`, `model-ready/`, `evaluations/`, `logs/`

**Deliverables**:
- `infra/terraform/s3/main.tf`
- `infra/terraform/kms/s3_kms.tf`

**Acceptance Criteria**:
- All buckets created with KMS encryption
- Lifecycle policies configured
- Object versioning enabled

**Dependencies**: None  
**Estimated Time**: 1 day  
**Watchdog Protocols**: CloudWatch alarms for S3 errors  
**Testing Requirements**: Terratest for bucket creation

---

## THREE-MODEL COLLABORATION SYSTEM

### Task COLLAB-001: Model A - Lore Retriever/Synthesizer
**Component**: Three-Model Collaboration  
**Description**: Implement Model A that aggregates game lore for monster species, building types, etc. Retrieves from knowledge base, synthesizes with dynamic rules.

**Deliverables**:
- `services/collaboration/lore_retriever.py`
- `services/collaboration/knowledge_base_client.py`
- `services/collaboration/lore_synthesizer.py`

**Acceptance Criteria**:
- Retrieves relevant lore for any entity type
- Synthesizes canonical LoreBundle
- Integrates with dynamic rules engine
- Validates output structure

**Dependencies**: DATA-001, DATA-002  
**Estimated Time**: 2 days  
**Watchdog Protocols**: 5s timeout per retrieval, circuit breaker for KB  
**Testing Requirements**: Unit tests, integration tests with KB

---

### Task COLLAB-002: Model B - Teacher Planner
**Component**: Three-Model Collaboration  
**Description**: Implement Model B that generates expert step-by-step strategies with reasoning. Creates expert trajectories for training.

**Deliverables**:
- `services/collaboration/teacher_planner.py`
- `services/collaboration/trajectory_generator.py`
- `services/collaboration/scenario_builder.py`

**Acceptance Criteria**:
- Generates expert trajectories with step-wise reasoning
- Creates multiple variants per scenario
- Validates with Model C before acceptance
- Produces structured output

**Dependencies**: COLLAB-001  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: 10s timeout per trajectory, heartbeat every 2s  
**Testing Requirements**: Unit tests, trajectory quality tests

---

### Task COLLAB-003: Model C - Structurer/Verifier
**Component**: Three-Model Collaboration  
**Description**: Implement Model C that validates structure, enforces rules, produces reward signals. Verifies entire episodes.

**Deliverables**:
- `services/collaboration/structurer_verifier.py`
- `services/collaboration/rule_engine.py`
- `services/collaboration/reward_calculator.py`

**Acceptance Criteria**:
- Validates actions against rules and state
- Generates reward components
- Verifies episode outcomes
- Produces RLVR rewards

**Dependencies**: COLLAB-001  
**Estimated Time**: 2 days  
**Watchdog Protocols**: 3s timeout per validation, circuit breaker  
**Testing Requirements**: Unit tests, validation accuracy tests

---

## SRL TRAINING PIPELINE

### Task SRL-001: SRL Trainer Implementation
**Component**: SRL Training  
**Description**: Implement SRL training pipeline with step-wise rewards, KL divergence penalty, reward normalization per Google SRL paper.

**Deliverables**:
- `services/training/srl_trainer.py`
- `services/training/reward_normalizer.py`
- `services/training/kl_controller.py`
- Config: `configs/srl_training.yaml`

**Acceptance Criteria**:
- Step-wise dense rewards calculated
- KL divergence penalty enforced
- Reward normalization functional
- Training stability (KL < 0.1)

**Dependencies**: COLLAB-001..003, DATA-001  
**Estimated Time**: 3 days  
**Watchdog Protocols**: Per-step heartbeat, timeout enforcement  
**Testing Requirements**: Unit tests, training stability tests

---

## RLVR FINE-TUNING PIPELINE

### Task RLVR-001: RLVR Trainer Implementation
**Component**: RLVR Training  
**Description**: Implement RLVR fine-tuning with PPO, outcome rewards, optional DPO alternative.

**Deliverables**:
- `services/training/rlvr_trainer.py`
- `services/training/ppo_trainer.py`
- `services/training/dpo_trainer.py` (optional)

**Acceptance Criteria**:
- PPO improves over SFT baseline
- Outcome rewards functional
- KL penalty prevents divergence
- Checkpoints and metrics logged

**Dependencies**: SRL-001  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: Step-level watchdog, reward model latency monitoring  
**Testing Requirements**: Unit tests, reward monotonicity tests

---

## MODEL TYPE TRAINING TASKS (7 TYPES)

### Task MODEL-PERS-001: Personality Model Training
**Component**: Model Training - Personality  
**Description**: Train personality models for emotions, expressions, actions, inherent traits using SRL→RLVR pipeline.

**Deliverables**:
- `models/personality/train_srl.py`
- `models/personality/train_rlvr.py`
- `models/personality/infer.py`
- Training configs per personality type

**Acceptance Criteria**:
- Model understands emotions, expressions, actions
- Traits (aggression, intelligence, charisma) properly modeled
- Dynamic adaptation to player interactions
- Meets performance requirements

**Dependencies**: SRL-001, RLVR-001, DATA-001  
**Estimated Time**: 3 days  
**Watchdog Protocols**: Training step timeouts, GPU heartbeat  
**Testing Requirements**: Unit tests, inference latency tests, quality evaluation

---

### Task MODEL-FACIAL-001: Facial Expression Model Training
**Component**: Model Training - Facial Expressions  
**Description**: Train facial expression models mapping emotions to FACS AUs and blendshapes.

**Deliverables**:
- `models/facial/train_srl.py`
- `models/facial/train_rlvr.py`
- `models/facial/au_regressor.py`
- `models/facial/blendshape_mapper.py`

**Acceptance Criteria**:
- Emotion to AU mapping accurate
- AU to blendshape mapping rig-specific
- Body language integration functional
- Temporal stability maintained

**Dependencies**: MODEL-PERS-001, SRL-001, RLVR-001  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: Inference latency <50ms  
**Testing Requirements**: Unit tests, AU accuracy tests, identity preservation tests

---

### Task MODEL-BUILD-001: Building Generation Model Training
**Component**: Model Training - Buildings  
**Description**: Train models for exterior and interior building generation with architectural styles.

**Deliverables**:
- `models/buildings/exterior/train_srl.py`
- `models/buildings/interior/train_srl.py`
- `models/buildings/grammar_generator.py`
- `models/buildings/style_controller.py`

**Acceptance Criteria**:
- Exterior generation meets style requirements
- Interior generation with floor plans
- Day/night variations supported
- Environmental storytelling functional

**Dependencies**: SRL-001, RLVR-001, DATA-001  
**Estimated Time**: 3.5 days  
**Watchdog Protocols**: Generation timeout, constraint validation  
**Testing Requirements**: Unit tests, constraint satisfaction tests, style evaluation

---

### Task MODEL-ANIMAL-001: Animal Model Training
**Component**: Model Training - Animals  
**Description**: Train animal models for behavior, morphology, terrain-specific characteristics.

**Deliverables**:
- `models/animals/train_srl.py`
- `models/animals/morphology_generator.py`
- `models/animals/behavior_model.py`
- `models/animals/terrain_adapter.py`

**Acceptance Criteria**:
- Natural animal behaviors modeled
- Day vs. night behavior differences
- Terrain-specific adaptations
- Interaction logic functional

**Dependencies**: SRL-001, RLVR-001, DATA-001  
**Estimated Time**: 3 days  
**Watchdog Protocols**: Generation budgets, behavior validation  
**Testing Requirements**: Unit tests, morphology accuracy, behavior naturalness

---

### Task MODEL-PLANT-001: Plant Model Training
**Component**: Model Training - Plants  
**Description**: Train plant models for flora generation, ecosystem integration, seasonal variations.

**Deliverables**:
- `models/plants/train_srl.py`
- `models/plants/lsystem_generator.py`
- `models/plants/seasonal_variator.py`
- `models/plants/ecosystem_integrator.py`

**Acceptance Criteria**:
- Plants appropriate to terrain and season
- Ecosystem integration functional
- Seasonal variations accurate
- Environmental impact modeled

**Dependencies**: SRL-001, RLVR-001, DATA-001  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: Generation timeouts, diversity validation  
**Testing Requirements**: Unit tests, seasonal consistency, ecosystem tests

---

### Task MODEL-TREE-001: Tree Model Training
**Component**: Model Training - Trees  
**Description**: Train tree models for generation, seasonal variations, environmental sounds.

**Deliverables**:
- `models/trees/train_srl.py`
- `models/trees/topology_generator.py`
- `models/trees/seasonal_handler.py`
- `models/trees/sound_integrator.py`

**Acceptance Criteria**:
- Realistic tree generation
- Seasonal foliage variations
- Environmental sounds integrated
- Gameplay elements functional

**Dependencies**: MODEL-PLANT-001, SRL-001, RLVR-001  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: Generation budgets, wind animation validation  
**Testing Requirements**: Unit tests, branching statistics, seasonal tests

---

### Task MODEL-SOUND-001: Sound Model Training
**Component**: Model Training - Sounds  
**Description**: Train sound models for effects, music, environmental audio generation.

**Deliverables**:
- `models/sounds/effects/train_srl.py`
- `models/sounds/music/train_srl.py`
- `models/sounds/environmental/train_srl.py`
- `models/sounds/synthesizer.py`

**Acceptance Criteria**:
- Building sounds, animal sounds, environmental sounds
- Music generation (eerie, high energy, jump scare)
- Background ambience functional
- Quality meets requirements

**Dependencies**: SRL-001, RLVR-001, DATA-001  
**Estimated Time**: 3 days  
**Watchdog Protocols**: Generation timeouts, quality validation  
**Testing Requirements**: Unit tests, audio quality tests, MOS evaluation

---

## DYNAMIC SYSTEMS

### Task DYN-001: Dynamic Example Generation System
**Component**: Dynamic Systems  
**Description**: Implement system that NEVER generates static examples. Continuously improves generation methods, seeks new approaches.

**Deliverables**:
- `services/dynamic/example_generator.py`
- `services/dynamic/novelty_scorer.py`
- `services/dynamic/coverage_tracker.py`
- `services/dynamic/improvement_analyzer.py`

**Acceptance Criteria**:
- Examples never repeated (provenance tracking)
- Generation methods continuously improved
- Coverage gaps identified and filled
- Novelty and difficulty properly managed

**Dependencies**: COLLAB-001..003, DATA-002  
**Estimated Time**: 3 days  
**Watchdog Protocols**: Generation timeouts, cache management  
**Testing Requirements**: Unit tests, coverage tests, novelty tests

---

### Task DYN-002: Dynamic Rules Integration
**Component**: Dynamic Systems  
**Description**: Integrate versioned dynamic rules engine. Models re-train when rules update.

**Deliverables**:
- `services/rules/rules_engine.py`
- `services/rules/version_manager.py`
- `services/rules/change_detector.py`
- `services/rules/retrain_trigger.py`

**Acceptance Criteria**:
- Rules versioned and tracked
- Rule changes trigger re-training
- Models comply with current rules
- Rule evolution handled gracefully

**Dependencies**: DATA-002  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Rule validation timeouts  
**Testing Requirements**: Unit tests, version transition tests

---

### Task DYN-003: Dynamic Model Selection System
**Component**: Dynamic Systems  
**Description**: Implement responsibility-based model selection with cost-benefit analysis. Not arbitrary or static.

**Deliverables**:
- `services/selection/model_selector.py`
- `services/selection/cost_benefit_analyzer.py`
- `services/selection/responsibility_mapper.py`
- `services/selection/replacement_manager.py`

**Acceptance Criteria**:
- Selection based on task responsibilities
- Cost-benefit analysis functional
- New models evaluated automatically
- Replacement when warranted

**Dependencies**: PERF-001 (Model Registry)  
**Estimated Time**: 3 days  
**Watchdog Protocols**: Selection timeout, fallback logic  
**Testing Requirements**: Unit tests, cost-benefit accuracy tests

---

## PAID MODEL FINE-TUNING

### Task FINETUNE-001: Gemini Fine-Tuning Integration
**Component**: Paid Fine-Tuning  
**Description**: Implement Gemini fine-tuning via Google Vertex AI. Dataset preparation, job launch, monitoring, artifact retrieval.

**Deliverables**:
- `services/finetune/providers/gemini_adapter.py`
- `services/finetune/dataset_preparer.py`
- `services/finetune/job_monitor.py`

**Acceptance Criteria**:
- Fine-tuning jobs launch successfully
- Status monitoring functional
- Artifacts retrieved and registered
- Cost tracking accurate

**Dependencies**: SEC-003 (Secrets), DATA-002  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: API timeouts, retries, cost estimation  
**Testing Requirements**: Integration tests with sandbox, cost validation

---

### Task FINETUNE-002: ChatGPT Fine-Tuning Integration
**Component**: Paid Fine-Tuning  
**Description**: Implement OpenAI fine-tuning for GPT models. Dataset formatting, job management, evaluation.

**Deliverables**:
- `services/finetune/providers/openai_adapter.py`
- `services/finetune/formatters/openai_format.py`

**Acceptance Criteria**:
- Fine-tuning jobs functional
- Model registration after completion
- Evaluation integrated
- Cost controls enforced

**Dependencies**: SEC-003, DATA-002  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: API timeouts, rate limiting, budget checks  
**Testing Requirements**: Integration tests, cost validation

---

### Task FINETUNE-003: Anthropic Fine-Tuning Integration
**Component**: Paid Fine-Tuning  
**Description**: Implement Anthropic fine-tuning when available. Prompt engineering fallback when not available.

**Deliverables**:
- `services/finetune/providers/anthropic_adapter.py`
- `services/finetune/prompt_optimizer.py` (fallback)

**Acceptance Criteria**:
- Fine-tuning supported when available
- Prompt engineering optimized fallback
- Quality improvements measurable
- Cost-benefit analysis functional

**Dependencies**: SEC-003, DATA-002  
**Estimated Time**: 2 days  
**Estimated Time** (fallback only): 1.5 days  
**Watchdog Protocols**: API timeouts, prompt optimization budgets  
**Testing Requirements**: Integration tests, prompt quality tests

---

### Task FINETUNE-004: Fine-Tuning Cost-Benefit Evaluator
**Component**: Paid Fine-Tuning  
**Description**: Implement system to evaluate fine-tuning opportunities vs prompt engineering. Three-model collaboration for criteria.

**Deliverables**:
- `services/finetune/cost_benefit_evaluator.py`
- `services/finetune/three_model_collaborator.py`

**Acceptance Criteria**:
- Fine-tuning vs prompt engineering evaluation
- Three models determine criteria
- Quality improvements measured
- Cost tracking accurate

**Dependencies**: FINETUNE-001..003  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Evaluation timeouts, fallback logic  
**Testing Requirements**: Unit tests, evaluation accuracy tests

---

## PERFORMANCE TRACKING

### Task PERF-001: Model Registry (SageMaker Model Registry)
**Component**: Performance Tracking  
**Description**: Deploy SageMaker Model Registry for model tracking, versioning, promotion workflows.

**Deliverables**:
- `infra/terraform/sagemaker/registry.tf`
- `services/registry/model_registry.py`
- `services/registry/promotion_workflow.py`

**Acceptance Criteria**:
- Models registered with metadata
- Versioning functional
- Promotion workflows implemented
- Integration with deployment

**Dependencies**: DEP-AWS-006  
**Estimated Time**: 1.5 days  
**Watchdog Protocols**: Registry API timeouts  
**Testing Requirements**: Integration tests, promotion workflow tests

---

### Task PERF-002: Performance Monitoring System
**Component**: Performance Tracking  
**Description**: Implement continuous monitoring for all models: latency, quality, errors, costs.

**Deliverables**:
- `services/monitoring/metrics_collector.py`
- `services/monitoring/anomaly_detector.py`
- `services/monitoring/weakness_analyzer.py`

**Acceptance Criteria**:
- All metrics collected (latency, quality, errors, costs)
- Anomalies detected automatically
- Weaknesses identified before issues
- Dashboards functional

**Dependencies**: MON-003 (Prometheus), PERF-001  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Metric collection timeouts  
**Testing Requirements**: Unit tests, anomaly detection tests

---

### Task PERF-003: Weakness Detection and Alerting
**Component**: Performance Tracking  
**Description**: Implement system to detect model weaknesses proactively. Replace models before issues occur.

**Deliverables**:
- `services/monitoring/weakness_detector.py`
- `services/monitoring/trend_analyzer.py`
- `services/monitoring/alert_manager.py`

**Acceptance Criteria**:
- Weaknesses detected early
- Trends analyzed over time
- Alerts fire on degradation
- Replacement triggered automatically

**Dependencies**: PERF-002  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Detection timeouts, alert rate limiting  
**Testing Requirements**: Unit tests, trend analysis tests

---

### Task PERF-004: Three-Model Evaluation System
**Component**: Performance Tracking  
**Description**: Implement three-model collaboration for evaluation criteria, benchmark selection, research integration.

**Deliverables**:
- `services/evaluation/three_model_evaluator.py`
- `services/evaluation/benchmark_selector.py`
- `services/evaluation/research_integrator.py`

**Acceptance Criteria**:
- Three models collaborate on evaluation
- Relevant benchmarks selected
- Research integrated
- Testing validates claims

**Dependencies**: PERF-002  
**Estimated Time**: 2.5 days  
**Watchdog Protocols**: Evaluation timeouts, model selection  
**Testing Requirements**: Unit tests, evaluation consistency tests

---

## AWS DEPLOYMENT

### Task DEP-AWS-001: VPC and Networking (Terraform)
**Component**: AWS Infrastructure  
**Description**: Create production VPC with private subnets, NAT, VPC endpoints, security groups.

**Deliverables**:
- `infra/terraform/network/main.tf`
- `infra/terraform/network/vpc_endpoints.tf`

**Acceptance Criteria**:
- VPC created across 3 AZs
- VPC endpoints for AWS services
- Private subnets for compute
- Flow logs enabled

**Dependencies**: None  
**Estimated Time**: 1 day  
**Watchdog Protocols**: CloudWatch alarms on NAT errors  
**Testing Requirements**: Terratest for topology

---

### Task DEP-AWS-002: EKS Cluster Setup
**Component**: AWS Infrastructure  
**Description**: Deploy EKS cluster with managed nodegroups, GPU node pools, autoscaling.

**Deliverables**:
- `infra/terraform/eks/main.tf`
- `infra/k8s/cluster-autoscaler/values.yaml`

**Acceptance Criteria**:
- EKS cluster functional
- GPU nodes available
- Autoscaling configured
- Node pools tagged correctly

**Dependencies**: DEP-AWS-001  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Cluster health monitoring  
**Testing Requirements**: kubectl tests, autoscaling tests

---

### Task DEP-AWS-003: SageMaker Setup
**Component**: AWS Infrastructure  
**Description**: Configure SageMaker for training jobs, model endpoints, execution roles.

**Deliverables**:
- `infra/terraform/sagemaker/main.tf`
- `infra/terraform/iam/sagemaker_roles.tf`

**Acceptance Criteria**:
- Training jobs can run
- Endpoints deployable
- Roles properly scoped
- KMS encryption enabled

**Dependencies**: DEP-AWS-001  
**Estimated Time**: 1.5 days  
**Watchdog Protocols**: Job timeout alarms  
**Testing Requirements**: Training job test, endpoint test

---

### Task DEP-AWS-004: Step Functions Workflows
**Component**: AWS Infrastructure  
**Description**: Create Step Functions state machines for training pipelines, evaluation, deployment.

**Deliverables**:
- `infra/terraform/stepfunctions/main.tf`
- `services/orchestrator/step_functions/training_flow.asl.json`
- `services/orchestrator/step_functions/evaluation_flow.asl.json`

**Acceptance Criteria**:
- Workflows defined and functional
- Error handling implemented
- Human-in-the-loop supported
- Monitoring integrated

**Dependencies**: DEP-AWS-002, DEP-AWS-003  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Workflow timeouts, DLQ configuration  
**Testing Requirements**: Workflow execution tests

---

## SECURITY

### Task SEC-001: Secrets Management (AWS Secrets Manager)
**Component**: Security  
**Description**: Store all API keys, provider credentials in Secrets Manager with rotation.

**Deliverables**:
- `infra/terraform/secrets/main.tf`
- `libs/secrets/client.py`
- `lambda/rotate_secrets/index.py`

**Acceptance Criteria**:
- All secrets in Secrets Manager
- Rotation functional
- No secrets in code/logs
- Access via IAM roles

**Dependencies**: DEP-AWS-001  
**Estimated Time**: 1 day  
**Watchdog Protocols**: Secret fetch timeout (200ms), cache fallback  
**Testing Requirements**: Integration tests, rotation tests

---

### Task SEC-002: IAM Least Privilege
**Component**: Security  
**Description**: Create fine-grained IAM roles for all services with least privilege.

**Deliverables**:
- `infra/terraform/iam/roles.tf`
- `infra/terraform/iam/policies/`

**Acceptance Criteria**:
- All services have dedicated roles
- Minimal permissions granted
- Resource-level restrictions
- Access Analyzer validation

**Dependencies**: DEP-AWS-001  
**Estimated Time**: 1.5 days  
**Watchdog Protocols**: Policy change monitoring  
**Testing Requirements**: IAM Access Analyzer tests

---

### Task SEC-003: KMS Encryption
**Component**: Security  
**Description**: Encrypt all storage (S3, RDS, EBS) with KMS CMKs, enable rotation.

**Deliverables**:
- `infra/terraform/kms/main.tf`
- `infra/terraform/kms/keys.tf`

**Acceptance Criteria**:
- All storage encrypted
- Key rotation enabled
- Key policies restrictive
- Audit logging enabled

**Dependencies**: DEP-AWS-001  
**Estimated Time**: 1 day  
**Watchdog Protocols**: KMS error alarms  
**Testing Requirements**: Encryption verification tests

---

## TESTING

### Task TEST-001: Comprehensive Testing Framework
**Component**: Testing  
**Description**: Implement testing framework covering unit, integration, e2e, load, chaos, security per /all-rules.

**Deliverables**:
- `tests/unit/`, `tests/integration/`, `tests/e2e/`
- `tests/load/`, `tests/chaos/`, `tests/security/`
- `pytest.ini`, test configs

**Acceptance Criteria**:
- 100% test coverage required
- All test types implemented
- CI integration functional
- Performance benchmarks defined

**Dependencies**: All core components  
**Estimated Time**: 3 days (ongoing)  
**Watchdog Protocols**: Test timeouts, resource cleanup  
**Testing Requirements**: Self-testing (tests for tests)

---

## INTEGRATION

### Task INT-001: Integration with Existing Systems
**Component**: Integration  
**Description**: Integrate SRL→RLVR training system with existing model management, AI inference, orchestration services.

**Deliverables**:
- `services/integration/model_management_adapter.py`
- `services/integration/inference_adapter.py`
- `services/integration/orchestration_adapter.py`

**Acceptance Criteria**:
- All integrations functional
- API contracts validated
- Error handling robust
- Performance acceptable

**Dependencies**: All MODEL-* tasks, PERF-001  
**Estimated Time**: 2 days  
**Watchdog Protocols**: Integration timeouts, circuit breakers  
**Testing Requirements**: Integration tests, contract tests

---

## TASK DEPENDENCIES SUMMARY

```
FOUNDATION:
  OBS-001 → OBS-002
  DATA-002 → DATA-001

THREE-MODEL COLLABORATION:
  DATA-001, DATA-002 → COLLAB-001
  COLLAB-001 → COLLAB-002
  COLLAB-001 → COLLAB-003

TRAINING PIPELINE:
  COLLAB-* → SRL-001
  SRL-001 → RLVR-001

MODEL TRAINING:
  SRL-001, RLVR-001 → MODEL-PERS-001
  MODEL-PERS-001 → MODEL-FACIAL-001
  SRL-001, RLVR-001 → MODEL-BUILD-001
  SRL-001, RLVR-001 → MODEL-ANIMAL-001
  SRL-001, RLVR-001 → MODEL-PLANT-001
  MODEL-PLANT-001 → MODEL-TREE-001
  SRL-001, RLVR-001 → MODEL-SOUND-001

DYNAMIC SYSTEMS:
  COLLAB-*, DATA-002 → DYN-001
  DATA-002 → DYN-002
  PERF-001 → DYN-003

PAID FINE-TUNING:
  SEC-003, DATA-002 → FINETUNE-001..003
  FINETUNE-* → FINETUNE-004

PERFORMANCE:
  DEP-AWS-006 → PERF-001
  MON-003 → PERF-002
  PERF-002 → PERF-003
  PERF-002 → PERF-004

AWS DEPLOYMENT:
  DEP-AWS-001 → DEP-AWS-002, DEP-AWS-003
  DEP-AWS-002, DEP-AWS-003 → DEP-AWS-004

SECURITY:
  DEP-AWS-001 → SEC-001..003

TESTING:
  All components → TEST-001

INTEGRATION:
  All MODEL-*, PERF-001 → INT-001
```

---

## TIME ESTIMATION (SERIAL)

- Foundation (OBS, DATA): ~5 days
- Three-Model Collaboration: ~6.5 days
- Training Pipeline (SRL, RLVR): ~5.5 days
- Model Training (7 types): ~20 days
- Dynamic Systems: ~8 days
- Paid Fine-Tuning: ~9 days
- Performance Tracking: ~8 days
- AWS Deployment: ~6.5 days
- Security: ~3.5 days
- Testing: ~3 days
- Integration: ~2 days

**Total (serial)**: ~77 days  
**With parallel teams**: Plan resourcing accordingly

---

**STATUS**: Phase 3 Complete - Ready for Phase 4 (Global Coordination)

**Next Steps**:
1. Review task breakdown for completeness
2. Create management files
3. Integrate with Global Manager
4. Begin Phase 4

