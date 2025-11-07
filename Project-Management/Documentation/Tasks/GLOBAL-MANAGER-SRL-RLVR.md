# Global Manager - SRL→RLVR Training System Integration
**Date**: 2025-01-29  
**Phase**: 4 - Global Coordination  
**Status**: Complete Integration Plan

---

## PROJECT OVERVIEW

**Project**: "The Body Broker" - AI-Driven Gaming Core  
**New System**: SRL→RLVR Training System  
**Architecture**: Integration with existing 8 service modules + New Training System  
**Platform**: Steam + PC (Windows 10/11)  
**Engine**: Unreal Engine 5.6+  
**Deployment**: Full AWS (all training and inference)

---

## 🚨 CRITICAL REQUIREMENTS - ALL MANDATORY

### All Model Types Must Be Trained
1. ✅ **Personality Models**: Emotions, expressions, actions, traits
2. ✅ **Facial Expression Models**: Emotion mapping, blendshapes, AUs
3. ✅ **Building Models**: Exterior and interior generation
4. ✅ **Animal Models**: Behavior, morphology, terrain-specific
5. ✅ **Plant Models**: Flora generation, ecosystem integration, seasons
6. ✅ **Tree Models**: Generation, seasonal variations, sounds
7. ✅ **Sound Models**: Effects, music, environmental audio

### Dynamic Systems - Never Static
- ✅ **Dynamic Example Generation**: NEVER static examples, continuously improving
- ✅ **Dynamic Rules Integration**: Versioned rules, re-training on updates
- ✅ **Dynamic Model Selection**: Responsibility-based, cost-benefit analysis, not arbitrary

### Paid Model Fine-Tuning
- ✅ **Gemini**: Vertex AI fine-tuning integration
- ✅ **ChatGPT**: OpenAI fine-tuning integration
- ✅ **Anthropic**: Fine-tuning when available, prompt engineering fallback

### Performance Tracking
- ✅ **Continuous Monitoring**: All models, all metrics
- ✅ **Weakness Detection**: Before issues occur
- ✅ **Three-Model Evaluation**: For criteria and benchmarking

### AWS Deployment
- ✅ **All Training in AWS**: No local inference
- ✅ **SageMaker**: Training jobs and endpoints
- ✅ **Step Functions**: Orchestration workflows
- ✅ **S3**: Data lake and artifacts
- ✅ **DynamoDB**: Metadata and registries

---

## INTEGRATION POINTS VALIDATION

### ✅ SRL→RLVR Training System ↔ Existing Model Management System

**Integration Point**:
- **Protocol**: REST API + EventBridge events
- **Contract**: 
  - `POST /models/register {modelType, version, metrics, artifacts[], trainingMetadata}`
  - `POST /models/{id}/promote {stage, approvalMetadata}`
  - `EVENT ModelRegistered` → Model Management System
  - `EVENT ModelPromoted` → Model Management System
- **Authentication**: IAM role `srlTrainerRole` → `ModelMgmtWrite` permissions
- **Status**: ✅ Defined and validated

**Data Flow**:
1. SRL→RLVR training completes
2. Model registered via Model Management API
3. Model Management System stores metadata, versions, deployment configs
4. Event emitted for downstream consumers
5. Model available for selection by Dynamic Model Selector

---

### ✅ SRL→RLVR Training System ↔ AI Inference Service

**Integration Point**:
- **Protocol**: REST API + deployment events
- **Contract**:
  - `POST /deploy {modelId, stage, autoscalingPolicy, costTargets, modelType}`
  - `GET /models/available {modelType, constraints}` → Returns candidate models
  - `EVENT ModelDeploymentReady` → AI Inference Service
  - `EVENT InferenceCanaryMetrics` → SRL→RLVR for feedback
- **Authentication**: IAM role `srlTrainerRole` → `InferenceDeploy` permissions
- **Status**: ✅ Defined and validated

**Data Flow**:
1. SRL→RLVR registers trained model
2. Optional auto-deploy to Staging inference endpoint
3. AI Inference Service provisions SageMaker endpoint
4. Dynamic Model Selector queries available models
5. Inference metrics feed back to performance tracking

---

### ✅ SRL→RLVR Training System ↔ Orchestration Service

**Integration Point**:
- **Protocol**: Step Functions invoke + EventBridge triggers
- **Contract**:
  - `StartExecution(train_srl_to_rlvr, input=TrainingRequest)`
  - `EVENT TrainingJobStatus {requestId, status, metrics, artifacts}`
  - `EVENT TrainingComplete {modelId, version, metrics}`
- **Authentication**: IAM role `orchestratorRole` → Step Functions permissions
- **Status**: ✅ Defined and validated

**Data Flow**:
1. Orchestration Service triggers training via Step Functions
2. SRL→RLVR training pipeline executes
3. Status events emitted throughout training
4. Completion event triggers model registration
5. Orchestration coordinates with other services

---

### ✅ SRL→RLVR Training System ↔ State Management (Redis/PostgreSQL)

**Integration Point**:
- **Protocol**: Redis (hot) + PostgreSQL (persistent) + Vector DB
- **Contract**:
  - Training job state: `training:{jobId}` → Redis
  - Model metadata: PostgreSQL `models` table
  - Example embeddings: Vector DB for similarity search
  - Lore storage: PostgreSQL + Vector DB for retrieval
- **Status**: ✅ Defined and validated

**Data Flow**:
1. Training jobs store state in Redis
2. Model metadata persisted to PostgreSQL
3. Lore Retriever queries PostgreSQL + Vector DB
4. Example Generator uses vector similarity
5. Performance metrics stored in PostgreSQL

---

### ✅ Dynamic Model Selection ↔ All Services

**Integration Point**:
- **Protocol**: REST API calls from all consumers
- **Contract**:
  - `POST /select {modelType, constraints, preferences}`
  - Returns: `{chosenModelId, scoreBreakdown, rationale}`
- **Consumers**:
  - AI Inference Service (for routing)
  - Orchestration Service (for planning)
  - Game Engine (for model selection hints)
- **Status**: ✅ Defined and validated

---

### ✅ Paid Fine-Tuning ↔ Billing Service

**Integration Point**:
- **Protocol**: REST API + EventBridge
- **Contract**:
  - `POST /charges/hold {tenantId, estimateUSD, purpose}`
  - `POST /charges/commit {holdId, actualUSD}`
  - `POST /charges/release {holdId}`
  - `EVENT ChargeCommitted` / `ChargeExceeded`
- **Status**: ✅ Defined and validated

---

## BUILD ORDER & DEPENDENCIES

### Phase 0: Foundation & Infrastructure (Weeks 1-2)
**Priority**: CRITICAL - Must complete first

1. **AWS Infrastructure (Terraform)**:
   - VPC, subnets, NAT, VPC endpoints
   - S3 buckets (data lake, artifacts, logs)
   - DynamoDB tables (registries, metadata)
   - ECR repositories
   - Secrets Manager setup
   - EventBridge bus
   - SQS queues + DLQs
   - API Gateway

2. **Security Foundation**:
   - IAM roles and policies (least privilege)
   - KMS CMKs for encryption
   - Secrets Manager configuration
   - VPC security groups
   - WAF rules

3. **Observability Foundation**:
   - CloudWatch log groups
   - CloudWatch metrics and dashboards
   - X-Ray tracing setup
   - Prometheus/Grafana (optional)

4. **CI/CD Pipeline**:
   - GitHub Actions workflows
   - Terraform plan/apply
   - Docker build, scan, push
   - Security scanning (Secrets, SBOM, SLSA)

**Dependencies**: None  
**Deliverables**: All infrastructure ready, CI/CD functional

---

### Phase 1: Core Training Components (Weeks 3-5)
**Priority**: CRITICAL - Enables all training

1. **Three-Model Collaboration System**:
   - Model A: Lore Retriever/Synthesizer (COLLAB-001)
   - Model B: Teacher Planner (COLLAB-002)
   - Model C: Structurer/Verifier (COLLAB-003)

2. **SRL Training Pipeline**:
   - SRL Trainer (SRL-001)
   - Reward Normalizer
   - KL Divergence Controller

3. **Data Layer**:
   - Data schemas (DATA-001)
   - S3 data lake (DATA-002)
   - Dataset ingestion (DATA-004)

4. **Basic Observability**:
   - Structured logging (OBS-001)
   - Watchdog system (OBS-002)
   - Context propagation (OBS-003)

**Dependencies**: Phase 0 complete  
**Deliverables**: Three-model system functional, SRL training works

---

### Phase 2: RLVR & First Model Types (Weeks 6-8)
**Priority**: HIGH - Proves end-to-end pipeline

1. **RLVR Training Pipeline**:
   - RLVR Trainer (RLVR-001)
   - PPO implementation
   - Evaluation suite (RLVR-002)

2. **First Two Model Types** (Proof of Concept):
   - Personality Model Training (MODEL-PERS-001)
   - Animal Model Training (MODEL-ANIMAL-001)

3. **Model Registry Integration**:
   - SageMaker Model Registry (PERF-001)
   - Model registration workflows
   - Promotion gates

4. **Basic Dynamic Systems**:
   - Dynamic Example Generation (DYN-001)
   - Dynamic Rules Integration (DYN-002)

**Dependencies**: Phase 1 complete  
**Deliverables**: End-to-end training works for 2 model types

---

### Phase 3: Remaining Model Types (Weeks 9-11)
**Priority**: HIGH - Complete model coverage

1. **Remaining 5 Model Types**:
   - Facial Expression (MODEL-FACIAL-001)
   - Buildings - Exterior (MODEL-BUILD-001)
   - Buildings - Interior (MODEL-BUILD-001)
   - Plants (MODEL-PLANT-001)
   - Trees (MODEL-TREE-001)
   - Sounds (MODEL-SOUND-001)

2. **Model-Specific Optimizations**:
   - Per-type training strategies
   - Evaluation metrics per type
   - Quality gates per type

**Dependencies**: Phase 2 complete  
**Deliverables**: All 7 model types trainable

---

### Phase 4: Dynamic Selection & Paid Fine-Tuning (Weeks 12-14)
**Priority**: MEDIUM - Advanced features

1. **Dynamic Model Selection**:
   - Model Selector (DYN-003)
   - Cost-Benefit Analyzer
   - Responsibility Mapper
   - Replacement Manager

2. **Paid Model Fine-Tuning**:
   - Gemini integration (FINETUNE-001)
   - ChatGPT integration (FINETUNE-002)
   - Anthropic integration (FINETUNE-003)
   - Cost-Benefit Evaluator (FINETUNE-004)

3. **Integration with Existing Systems**:
   - Model Management System (INT-001)
   - AI Inference Service
   - Orchestration Service

**Dependencies**: Phase 3 complete  
**Deliverables**: Dynamic selection functional, paid fine-tuning available

---

### Phase 5: Performance Tracking & Weakness Detection (Weeks 15-16)
**Priority**: MEDIUM - Operations excellence

1. **Performance Tracking**:
   - Monitoring System (PERF-002)
   - Weakness Detection (PERF-003)
   - Three-Model Evaluation (PERF-004)

2. **Advanced Monitoring**:
   - Prometheus/Grafana dashboards
   - CloudWatch anomaly detection
   - Alerting and escalation

**Dependencies**: Phase 4 complete  
**Deliverables**: Full observability, proactive issue detection

---

### Phase 6: Testing & Security Hardening (Weeks 17-18)
**Priority**: HIGH - Production readiness

1. **Comprehensive Testing**:
   - Unit tests (TEST-001)
   - Integration tests
   - E2E tests
   - Load tests
   - Chaos tests
   - Security tests

2. **Security Hardening**:
   - IAM least privilege review
   - Secrets rotation
   - Encryption verification
   - Vulnerability scanning
   - Compliance checks

**Dependencies**: Phase 5 complete  
**Deliverables**: 100% test coverage, security hardened

---

### Phase 7: Production Deployment & Operations (Weeks 19-20)
**Priority**: CRITICAL - Go-live preparation

1. **Production Deployment**:
   - Terraform production environment
   - Blue-green deployment setup
   - Canary release configuration
   - Rollback procedures

2. **Operations Readiness**:
   - Runbooks documentation
   - Incident response procedures
   - Disaster recovery testing
   - Cost monitoring and alerts

**Dependencies**: Phase 6 complete  
**Deliverables**: Production-ready, fully operational

---

## COMMAND INTEGRATION

### Locked Commands (Active)

**MANDATORY**: These commands are locked and enforced via Step Functions:

1. **`/all-rules`**: 
   - **Purpose**: Verify and enforce all rules from `/all-rules`
   - **Implementation**: Step Functions state machine `all_rules_verify`
   - **Enforcement**: Fail-close on rule violations
   - **Gates**: All training, deployment, promotion operations

2. **`/autonomous`**:
   - **Purpose**: Autonomous training/evaluation cycles
   - **Implementation**: Step Functions state machine `autonomous_runner`
   - **Safety**: Budget guardrails + rule engine approval required
   - **Use**: Continuous improvement cycles

3. **`/complete-everything`**:
   - **Purpose**: Full build: generate→train→evaluate→back-test→register→deploy
   - **Implementation**: Step Functions state machine `complete_everything`
   - **Gates**: Milestone rule enforced (integrated testing, learning consolidation, back-tests)
   - **Use**: Complete training pipeline execution

4. **`/test-comprehensive`**:
   - **Purpose**: End-to-end integration tests across all services and model types
   - **Implementation**: Step Functions state machine `test_comprehensive`
   - **Outputs**: Test report artifact, metrics, pass/fail
   - **Use**: After every milestone, before deployments

5. **`/test-end-user`**:
   - **Purpose**: Black-box tests mimicking end-user flows via API Gateway
   - **Implementation**: Step Functions state machine `test_end_user`
   - **Outputs**: UX success metrics, latency, error rates
   - **Use**: Pre-production validation

6. **`/milestone`**:
   - **Purpose**: Testing integration per task, learning consolidation, back-tests
   - **Implementation**: Integrated into every task completion
   - **Requirements**:
     - ✅ Runs comprehensive tests
     - ✅ Consolidates learnings to memory
     - ✅ Back-tests everything built
     - ✅ Ensures nothing breaks
   - **Enforcement**: Mandatory after every task

---

## MILESTONE RULE ENFORCEMENT

### Mandatory Process

**Every task completion MUST**:

1. **Run Comprehensive Tests**:
   - Unit tests (if applicable)
   - Integration tests (if applicable)
   - Contract tests
   - All existing tests (regression)

2. **Consolidate Learning**:
   - Extract key learnings
   - Save to project memory (`.cursor/memory/project/`)
   - Update global memory (Global-History, Global-Reasoning)
   - Document decisions and patterns

3. **Back-Test Everything Built**:
   - Run full test suite
   - Verify no regressions
   - Check integration points
   - Validate performance metrics

4. **Ensure Nothing Breaks**:
   - All existing functionality works
   - No breaking changes
   - Backward compatibility maintained
   - Documentation updated

**Enforcement**: 
- Step Functions gates enforce milestone rule
- Block promotions/deployments if milestone rule fails
- Notify owners on violations

---

## CODE INTEGRITY & ANTI-FAKE CHECKS

### Mandatory CI Jobs

1. **Mock Code Detector**:
   - Block builds if `src/` imports `mock/fake/stub` libraries
   - Regex scan for `TODO MOCK`, `FAKE_`, `PLACEHOLDER`, `DUMMY` outside `tests/`
   - Block packaging of modules under `**/mocks/**` unless test-only

2. **Secret Scanner**:
   - GitLeaks / TruffleHog
   - Block on secrets in code

3. **SBOM Generation**:
   - Syft + Grype
   - Verify dependencies

4. **SLSA Provenance**:
   - Attestations in Rekor
   - Build provenance tracking

5. **Artifact Signing**:
   - Cosign verification
   - Signature validation

6. **Checksum Verification**:
   - Verify artifact checksums match registered values

7. **Reproducibility Check**:
   - Rerun minimal training deterministically
   - Compare metrics within tolerance

### Runtime Guards

- ❌ **Refuse to start** if `/all-rules` not mounted or version mismatch
- ❌ **Refuse to deploy** if artifact signature invalid
- ❌ **Block production** if mock-code-detector flagged artifact
- ❌ **Block promotion** if milestone rule not passed

---

## EXISTING TASK AUDIT & REPLACEMENT

### Tasks to Scrap/Replace

**ALL existing training/fine-tuning tasks must be REPLACED**:

1. **MODEL-MANAGEMENT-TASKS.md**:
   - Task 7.4: Historical Log Processing → **REPLACE** with SRL→RLVR approach
   - Task 7.5: Fine-Tuning Pipeline → **REPLACE** with SRL→RLVR approach
   - Task 7.6: Testing Framework → **ENHANCE** with SRL→RLVR requirements

2. **AI-INFERENCE-TASKS.md**:
   - Any tasks mentioning "fine-tune" → **REVIEW** and update to use SRL→RLVR
   - Model selection logic → **REPLACE** with dynamic model selection system

3. **Other Task Files**:
   - Review all files for "training" or "fine-tune" → **AUDIT** and replace

**Action Required**:
- Mark old tasks as **DEPRECATED - REPLACE WITH SRL→RLVR**
- Add note: "All training must use SRL→RLVR solution per Global Manager"
- Update task dependencies to point to new SRL→RLVR tasks

---

## TASK DEPENDENCIES SUMMARY

```
PHASE 0 (Foundation):
  None → DEP-AWS-001..008, SEC-001..003, OBS-001..004, CI-001..005

PHASE 1 (Core Training):
  PHASE 0 → DATA-001, DATA-002, DATA-004
  DATA-* → COLLAB-001
  COLLAB-001 → COLLAB-002, COLLAB-003
  COLLAB-* → SRL-001

PHASE 2 (RLVR & First Models):
  SRL-001 → RLVR-001
  RLVR-001 → MODEL-PERS-001, MODEL-ANIMAL-001
  SRL-001, RLVR-001 → DYN-001, DYN-002

PHASE 3 (Remaining Models):
  MODEL-PERS-001 → MODEL-FACIAL-001
  SRL-001, RLVR-001 → MODEL-BUILD-001
  SRL-001, RLVR-001 → MODEL-PLANT-001
  MODEL-PLANT-001 → MODEL-TREE-001
  SRL-001, RLVR-001 → MODEL-SOUND-001

PHASE 4 (Dynamic & Paid):
  PERF-001 → DYN-003
  SEC-003, DATA-002 → FINETUNE-001..003
  FINETUNE-* → FINETUNE-004

PHASE 5 (Performance):
  DEP-AWS-006 → PERF-001
  MON-003 → PERF-002
  PERF-002 → PERF-003, PERF-004

PHASE 6 (Testing):
  All components → TEST-001

PHASE 7 (Integration):
  All MODEL-*, PERF-001 → INT-001
```

---

## GLOBAL-DOCS SHARING

### Task: Add to Global-Docs

**After completion of SRL→RLVR Training System**, add solution document to `Global-Docs/` for other projects to use:

**Deliverable**:
- Copy `docs/solutions/SRL-RLVR-TRAINING-SYSTEM-ENHANCED.md` to `Global-Docs/SRL-RLVR-TRAINING-SYSTEM.md`
- Ensure all project-specific references removed
- Make it generic for any gaming/AI project
- Document reuse guidelines

**Dependencies**: Phase 2 Complete (Solution Architecture)  
**Status**: Pending until system proven

---

## QUALITY ENFORCEMENT

### Golden Rule
- ❌ **NO mock/fake data** - All implementations must be real
- ❌ **NO simulated solutions** - Real functionality only
- ❌ **NO placeholder code** - Production-ready from day one
- ✅ **REAL implementations only** - Everything works

### Validation System
- Multi-model peer review required (minimum 3 models, all meeting minimum levels)
- AWS optimization where applicable
- Security from the beginning
- Documentation maintained
- Testing mandatory (100% coverage target)

---

## SESSION HANDOFF

### For Next Session

**Current State**:
- ✅ Phase 1-4: Complete (Analysis, Solutions, Tasks, Global Coordination)
- ✅ Requirements: Consolidated to `docs/requirements/`
- ✅ Solution: Complete architecture in `docs/solutions/SRL-RLVR-TRAINING-SYSTEM-ENHANCED.md`
- ✅ Tasks: Complete breakdown in `docs/tasks/SRL-RLVR-TRAINING-TASKS.md`
- ✅ Global Manager: This file (`docs/tasks/GLOBAL-MANAGER-SRL-RLVR.md`)
- 🔄 Ready for implementation (Phase 0: Foundation)

**Next Steps**:
1. Begin Phase 0: Foundation & Infrastructure
2. Follow build order defined above
3. Use `/all-rules` for all work
4. Enforce milestone rule after every task
5. Test comprehensively after every milestone
6. Continue automatically - never stop, never wait

**Key Files**:
- Solutions: `docs/solutions/SRL-RLVR-TRAINING-SYSTEM-ENHANCED.md`
- Tasks: `docs/tasks/SRL-RLVR-TRAINING-TASKS.md`
- Requirements: `docs/requirements/MODEL-TRAINING-REQUIREMENTS.md`
- This File: `docs/tasks/GLOBAL-MANAGER-SRL-RLVR.md`

---

## RISK MITIGATION

### Technical Risks
- **Cost Overruns**: Budget guardrails, cost estimation, anomaly detection
- **Model Quality**: Continuous evaluation, weakness detection, A/B testing
- **Training Stability**: KL divergence monitoring, reward normalization, early stopping
- **Integration Issues**: Contract testing, versioning, backward compatibility

### Operational Risks
- **System Complexity**: Comprehensive monitoring, runbooks, incident playbooks
- **Data Quality**: Data validation, lineage tracking, provenance requirements
- **Security**: Secrets management, IAM least privilege, encryption everywhere
- **Compliance**: Rule enforcement, audit logging, data retention policies

---

## SUCCESS CRITERIA

### Technical Metrics
- ✅ All 7 model types successfully trained
- ✅ Training examples never static (dynamic generation functional)
- ✅ Model selection dynamic and cost-optimized
- ✅ Paid fine-tuning functional for all providers
- ✅ Performance tracking detects weaknesses proactively
- ✅ 100% AWS deployment (no local inference)
- ✅ All rules in `/all-rules` enforced

### Operational Metrics
- ✅ Training pipeline: End-to-end execution < 24 hours for any model type
- ✅ Model quality: Metrics meet or exceed targets
- ✅ Cost efficiency: Training costs within budget
- ✅ System reliability: 99.9% uptime for training infrastructure
- ✅ Security: Zero security incidents, all scans passing

### Process Metrics
- ✅ Milestone rule: Enforced after every task (100% compliance)
- ✅ Testing: 100% test coverage, all tests passing
- ✅ Documentation: All components documented
- ✅ Code quality: No fake/mock code, all real implementations

---

**STATUS**: ✅ **Phase 4 Complete - Global Coordination Ready**

**All integration points validated. All requirements supported. Build order determined. Commands locked. Ready for implementation.**

---

**Global Manager File Location**: `docs/tasks/GLOBAL-MANAGER-SRL-RLVR.md`

**This file serves as the authoritative coordination document for the SRL→RLVR Training System integration with the existing gaming platform.**

