# Model Management System Solution
**Date**: 2025-01-29  
**Status**: Solution Architecture - Phase 2  
**Enforcement**: ALL rules in `/all-rules` are MANDATORY

---

## 🚨 EXECUTIVE SUMMARY

The Model Management System is a comprehensive, automated system that ensures the best possible models are always in use. It manages both paid models (Story Teller) and self-hosted models, automatically discovering, fine-tuning, testing, and deploying new models while maintaining guardrails and rollback capability.

### **Key Features:**
- **Paid Model Management**: Auto-check and switch to best available models
- **Self-Hosted Model Management**: Auto-discover, download, fine-tune, test, deploy
- **Meta-Management Layer**: Another model manages all models
- **Guardrails Enforcement**: Ensures immersive/addictive but NOT harmful
- **Rollback Capability**: Automatic rollback if issues detected
- **Historical Log Integration**: Uses logs for fine-tuning and validation

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 System Components

```python
ModelManagementSystem {
  MetaManagementModel {
    orchestrator: ModelOrchestrator
    monitor: SystemMonitor
    decisionEngine: OptimizationDecisionEngine
    guardrailsEnforcer: GuardrailsEnforcer
  }
  
  ModelDiscovery {
    paidModelScanner: PaidModelScanner  # OpenRouter, Anthropic, OpenAI, etc.
    selfHostedScanner: SelfHostedScanner  # HuggingFace, Ollama, etc.
    modelRanker: ModelRanker
    modelRegistry: ModelRegistry
  }
  
  FineTuningPipeline {
    historicalLogProcessor: HistoricalLogProcessor
    trainingDataPreparer: TrainingDataPreparer
    fineTuner: FineTuner  # LoRA and full fine-tuning
    useCaseCopyManager: UseCaseCopyManager
  }
  
  TestingFramework {
    behaviorComparator: BehaviorComparator
    performanceBenchmark: PerformanceBenchmark
    safetyValidator: SafetyValidator
    similarityScorer: SimilarityScorer
  }
  
  DeploymentManager {
    blueGreenDeployer: BlueGreenDeployer
    canaryReleaser: CanaryReleaser
    trafficShifter: TrafficShifter
    rollbackManager: RollbackManager
  }
  
  GuardrailsMonitor {
    outputMonitor: RealTimeOutputMonitor
    safetyChecker: SafetyChecker
    addictionMetricTracker: AddictionMetricTracker
    harmfulContentDetector: HarmfulContentDetector
  }
}
```

---

## 2. PAID MODEL MANAGEMENT

### 2.1 Model Discovery & Selection

```python
class PaidModelManager:
    """
    Manages paid models (Story Teller uses these).
    Always checks for best possible models and auto-switches.
    """
    
    def __init__(self):
        self.model_scanner = PaidModelScanner()
        self.model_comparator = ModelComparator()
        self.model_switcher = ModelSwitcher()
        self.current_models = {}
    
    async def check_for_better_models(
        self,
        use_case: str,  # "story_generation", "narrative_coordination", etc.
        current_model: str
    ) -> Optional[str]:
        """
        Check for better models available for specific use case.
        
        Process:
        1. Scan available models from OpenRouter, Anthropic, OpenAI, etc.
        2. Rank by: performance, cost, latency, quality
        3. Compare with current model
        4. Return better model if found
        """
        # Scan available models
        available_models = await self.model_scanner.scan_available_models(
            use_case=use_case,
            providers=["openai", "anthropic", "google", "openrouter"]
        )
        
        # Rank models
        ranked_models = await self.model_comparator.rank_models(
            models=available_models,
            criteria={
                "performance_score": 0.3,
                "cost_efficiency": 0.2,
                "latency": 0.2,
                "quality_metrics": 0.3
            }
        )
        
        # Compare with current
        current_performance = await self._get_model_performance(current_model)
        
        for ranked_model in ranked_models:
            if ranked_model.score > current_performance.score:
                return ranked_model.model_id
        
        return None
    
    async def auto_switch_model(
        self,
        use_case: str,
        new_model: str,
        current_model: str
    ):
        """
        Automatically switch to better model.
        
        Process:
        1. Validate new model works
        2. Run shadow deployment (parallel testing)
        3. Gradually shift traffic
        4. Monitor for issues
        5. Complete switch or rollback
        """
        # Validate new model
        validation = await self._validate_model(new_model, use_case)
        if not validation.passed:
            return False
        
        # Shadow deployment (run both models in parallel)
        await self._start_shadow_deployment(new_model, current_model)
        
        # Monitor shadow results
        shadow_results = await self._monitor_shadow_deployment(
            duration_minutes=60
        )
        
        if shadow_results.success_rate >= 0.95:
            # Gradually shift traffic
            await self._shift_traffic_gradually(
                new_model,
                current_model,
                steps=[10, 25, 50, 75, 100]  # Percent traffic
            )
            
            # Monitor each step
            for step_percent in [10, 25, 50, 75, 100]:
                await self._monitor_traffic_shift(step_percent, duration_minutes=30)
                if await self._detect_issues():
                    # Rollback if issues detected
                    await self._rollback_traffic_shift()
                    return False
            
            # Complete switch
            await self._complete_switch(new_model, current_model)
            return True
        
        return False
```

### 2.2 Model Scanning

```python
class PaidModelScanner:
    """
    Scans available models from paid providers.
    """
    
    async def scan_available_models(
        self,
        use_case: str,
        providers: List[str]
    ) -> List[ModelInfo]:
        """
        Scan providers for available models.
        
        Sources:
        - OpenRouter: Latest models across providers
        - Provider APIs: Direct API access for latest models
        - Model registries: Centralized model information
        """
        all_models = []
        
        for provider in providers:
            if provider == "openrouter":
                models = await self._scan_openrouter()
            elif provider == "openai":
                models = await self._scan_openai_api()
            elif provider == "anthropic":
                models = await self._scan_anthropic_api()
            elif provider == "google":
                models = await self._scan_google_api()
            
            all_models.extend(models)
        
        # Filter by use case compatibility
        compatible_models = [
            m for m in all_models
            if self._is_compatible_for_use_case(m, use_case)
        ]
        
        return compatible_models
```

---

## 3. SELF-HOSTED MODEL MANAGEMENT

### 3.1 Model Discovery & Download

```python
class SelfHostedModelManager:
    """
    Manages self-hosted models.
    Auto-identifies, downloads, fine-tunes, tests, and deploys.
    """
    
    def __init__(self):
        self.model_scanner = SelfHostedScanner()
        self.download_manager = ModelDownloadManager()
        self.fine_tuning_pipeline = FineTuningPipeline()
        self.testing_framework = TestingFramework()
        self.deployment_manager = DeploymentManager()
    
    async def discover_and_deploy_new_model(
        self,
        use_case: str,  # "npc_dialogue", "faction_decision", etc.
        current_model_id: str
    ) -> bool:
        """
        Complete pipeline: discover → download → fine-tune → test → deploy.
        """
        # 1. Discover best models
        candidate_models = await self.model_scanner.scan_and_rank_models(
            use_case=use_case,
            sources=["huggingface", "ollama", "other_repos"]
        )
        
        if not candidate_models:
            return False
        
        best_candidate = candidate_models[0]
        
        # 2. Download model
        downloaded_model = await self.download_manager.download_model(
            model_id=best_candidate.id,
            source=best_candidate.source
        )
        
        # 3. Create use-case specific copies
        use_case_copies = await self._create_use_case_copies(
            base_model=downloaded_model,
            use_cases=self._get_all_use_cases_for_model_type(best_candidate.type)
        )
        
        # 4. Fine-tune each copy
        fine_tuned_models = []
        for use_case_copy in use_case_copies:
            fine_tuned = await self.fine_tuning_pipeline.fine_tune_model(
                model=use_case_copy,
                historical_logs=await self._get_historical_logs(use_case_copy.use_case),
                initial_training_data=await self._get_initial_training_data(use_case_copy.use_case)
            )
            fine_tuned_models.append(fine_tuned)
        
        # 5. Test until similar/better behavior
        for fine_tuned_model in fine_tuned_models:
            test_results = await self.testing_framework.test_model(
                candidate_model=fine_tuned_model,
                current_model=await self._get_current_model(fine_tuned_model.use_case)
            )
            
            if not test_results.meets_threshold:
                # Re-train with more data
                await self._retrain_with_feedback(fine_tuned_model, test_results)
                # Test again (repeat until threshold met)
                continue
            
            # 6. Deploy after validation
            deployment_success = await self.deployment_manager.deploy_model(
                new_model=fine_tuned_model,
                current_model=await self._get_current_model(fine_tuned_model.use_case),
                deployment_strategy="blue_green"
            )
            
            if deployment_success:
                await self._update_model_registry(fine_tuned_model)
        
        return True
```

### 3.2 Model Discovery & Ranking

```python
class SelfHostedScanner:
    """
    Scans and ranks downloadable models.
    """
    
    async def scan_and_rank_models(
        self,
        use_case: str,
        sources: List[str]
    ) -> List[RankedModel]:
        """
        Scan sources and rank models by suitability.
        
        Ranking Criteria:
        - Performance metrics (benchmarks)
        - Resource requirements (VRAM, compute)
        - Model size (affects download/load time)
        - Community adoption (downloads, stars)
        - Recent updates (active maintenance)
        - License compatibility
        """
        all_models = []
        
        for source in sources:
            if source == "huggingface":
                models = await self._scan_huggingface(use_case)
            elif source == "ollama":
                models = await self._scan_ollama(use_case)
            else:
                models = await self._scan_custom_repo(source, use_case)
            
            all_models.extend(models)
        
        # Rank models
        ranked = await self._rank_models(
            models=all_models,
            criteria={
                "benchmark_scores": 0.3,
                "resource_efficiency": 0.2,
                "model_size": 0.1,
                "community_health": 0.15,
                "recent_updates": 0.15,
                "license_compatibility": 0.1
            },
            use_case=use_case
        )
        
        return ranked
```

### 3.3 Use-Case Copy Management

```python
class UseCaseCopyManager:
    """
    Creates and manages differently named copies for different use cases.
    """
    
    async def create_use_case_copies(
        self,
        base_model: Model,
        use_cases: List[str]
    ) -> List[Model]:
        """
        Create differently named copies for each use case.
        
        Naming Convention:
        - Base: llama-3.1-8b-instruct
        - NPC Dialogue: llama-3.1-8b-instruct-npc-dialogue
        - Faction Decision: llama-3.1-8b-instruct-faction-decision
        - Personality Model: llama-3.1-8b-instruct-personality
        """
        copies = []
        
        for use_case in use_cases:
            copy = await self._clone_model(
                base_model=base_model,
                new_name=f"{base_model.name}-{use_case.replace('_', '-')}"
            )
            
            # Customize for use case
            await self._customize_for_use_case(copy, use_case)
            
            copies.append(copy)
        
        return copies
    
    async def _customize_for_use_case(
        self,
        model: Model,
        use_case: str
    ):
        """
        Customize model configuration for specific use case.
        
        Customizations:
        - Temperature settings
        - Max tokens
        - System prompts
        - Sampling parameters
        - Quantization level (if needed)
        """
        use_case_config = self._get_use_case_config(use_case)
        
        model.config.update({
            "temperature": use_case_config.temperature,
            "max_tokens": use_case_config.max_tokens,
            "system_prompt_template": use_case_config.system_prompt,
            "sampling_params": use_case_config.sampling_params
        })
```

### 3.4 Fine-Tuning Pipeline with Historical Logs

```python
class FineTuningPipeline:
    """
    Fine-tunes models using historical logs + initial training data.
    """
    
    async def fine_tune_model(
        self,
        model: Model,
        historical_logs: List[LogEntry],
        initial_training_data: List[TrainingExample]
    ) -> FineTunedModel:
        """
        Fine-tune model using historical logs and initial data.
        
        Process:
        1. Process historical logs into training format
        2. Combine with initial training data
        3. Prepare training dataset
        4. Fine-tune (LoRA or full)
        5. Validate fine-tuned model
        """
        # Process historical logs
        processed_logs = await self._process_historical_logs(historical_logs)
        
        # Combine datasets
        training_data = await self._combine_training_data(
            historical_data=processed_logs,
            initial_data=initial_training_data
        )
        
        # Prepare for training
        training_dataset = await self._prepare_training_dataset(training_data)
        validation_dataset = await self._prepare_validation_dataset(training_data)
        
        # Fine-tune (prefer LoRA for efficiency)
        if model.supports_lora:
            fine_tuned_model = await self._fine_tune_lora(
                base_model=model,
                training_dataset=training_dataset,
                validation_dataset=validation_dataset
            )
        else:
            fine_tuned_model = await self._fine_tune_full(
                base_model=model,
                training_dataset=training_dataset,
                validation_dataset=validation_dataset
            )
        
        # Validate
        validation_results = await self._validate_fine_tuned_model(
            fine_tuned_model,
            validation_dataset
        )
        
        if not validation_results.passed:
            # Re-train with adjustments
            return await self._retrain_with_adjustments(
                model,
                training_data,
                validation_results.feedback
            )
        
        return fine_tuned_model
    
    async def _process_historical_logs(
        self,
        logs: List[LogEntry]
    ) -> List[TrainingExample]:
        """
        Convert historical logs into training examples.
        
        Logs contain:
        - Input prompts
        - Generated outputs
        - User feedback (if available)
        - Performance metrics
        - Context information
        
        Training examples created:
        - Input: prompt + context
        - Output: generated text (or corrected if feedback available)
        """
        training_examples = []
        
        for log_entry in logs:
            # Extract training data from log
            example = TrainingExample(
                input=log_entry.prompt + "\n" + log_entry.context,
                output=log_entry.output if log_entry.user_feedback is None else log_entry.corrected_output,
                metadata={
                    "timestamp": log_entry.timestamp,
                    "use_case": log_entry.use_case,
                    "performance": log_entry.performance_metrics
                }
            )
            
            training_examples.append(example)
        
        # Filter high-quality examples
        quality_filtered = await self._filter_high_quality_examples(training_examples)
        
        return quality_filtered
```

### 3.5 Testing Framework

```python
class TestingFramework:
    """
    Tests models to ensure similar/better behavior than current.
    """
    
    async def test_model(
        self,
        candidate_model: Model,
        current_model: Model
    ) -> TestResults:
        """
        Comprehensive testing comparing candidate to current.
        
        Tests:
        1. Behavior similarity (responses should be similar in quality/tone)
        2. Performance benchmarks (should be similar or better)
        3. Safety validation (should pass all safety checks)
        4. Use-case specific tests
        """
        results = TestResults()
        
        # 1. Behavior similarity test
        similarity_results = await self._test_behavior_similarity(
            candidate=candidate_model,
            current=current_model
        )
        results.behavior_similarity = similarity_results
        
        # 2. Performance benchmarks
        performance_results = await self._run_performance_benchmarks(
            candidate=candidate_model,
            current=current_model
        )
        results.performance = performance_results
        
        # 3. Safety validation
        safety_results = await self._validate_safety(
            candidate=candidate_model
        )
        results.safety = safety_results
        
        # 4. Use-case specific tests
        use_case_results = await self._run_use_case_tests(
            candidate=candidate_model,
            current=current_model,
            use_case=candidate_model.use_case
        )
        results.use_case_performance = use_case_results
        
        # Overall assessment
        results.meets_threshold = (
            similarity_results.score >= 0.95 and  # 95% similarity required
            performance_results.overall_score >= current_model.performance_score and
            safety_results.passed and
            use_case_results.passed
        )
        
        return results
    
    async def _test_behavior_similarity(
        self,
        candidate: Model,
        current: Model
    ) -> SimilarityResults:
        """
        Test if candidate behaves similarly to current model.
        
        Uses:
        - Test prompts from historical logs
        - Semantic similarity scoring
        - Response quality comparison
        - Tone/style consistency
        """
        test_prompts = await self._get_test_prompts_from_logs(limit=100)
        
        candidate_responses = []
        current_responses = []
        
        for prompt in test_prompts:
            candidate_resp = await candidate.generate(prompt)
            current_resp = await current.generate(prompt)
            
            candidate_responses.append(candidate_resp)
            current_responses.append(current_resp)
        
        # Calculate similarity
        semantic_similarity = await self._calculate_semantic_similarity(
            candidate_responses,
            current_responses
        )
        
        quality_similarity = await self._compare_quality_scores(
            candidate_responses,
            current_responses
        )
        
        return SimilarityResults(
            score=(semantic_similarity + quality_similarity) / 2,
            semantic_similarity=semantic_similarity,
            quality_similarity=quality_similarity,
            details={
                "test_prompts": len(test_prompts),
                "average_similarity": (semantic_similarity + quality_similarity) / 2
            }
        )
```

---

## 4. DEPLOYMENT & ROLLBACK

### 4.1 Blue-Green Deployment

```python
class DeploymentManager:
    """
    Manages model deployment with rollback capability.
    """
    
    async def deploy_model(
        self,
        new_model: Model,
        current_model: Model,
        deployment_strategy: str = "blue_green"
    ) -> bool:
        """
        Deploy new model using specified strategy.
        
        Strategies:
        - blue_green: Run both models, shift traffic gradually
        - canary: Small percentage of traffic to new model
        - all_at_once: Immediate switch (risky, not recommended)
        """
        if deployment_strategy == "blue_green":
            return await self._blue_green_deploy(new_model, current_model)
        elif deployment_strategy == "canary":
            return await self._canary_deploy(new_model, current_model)
        else:
            raise ValueError(f"Unknown strategy: {deployment_strategy}")
    
    async def _blue_green_deploy(
        self,
        new_model: Model,
        current_model: Model
    ) -> bool:
        """
        Blue-green deployment: run both models in parallel.
        """
        # Create snapshot for rollback
        await self.rollback_manager.create_snapshot(current_model)
        
        # Deploy new model (green) alongside current (blue)
        await self._deploy_green_instance(new_model)
        
        # Gradually shift traffic
        traffic_shifts = [10, 25, 50, 75, 100]  # Percentages
        
        for shift_percent in traffic_shifts:
            await self._shift_traffic(new_model, shift_percent)
            
            # Monitor for issues
            await asyncio.sleep(300)  # 5 minutes monitoring
            
            issues = await self._detect_deployment_issues(new_model)
            
            if issues:
                # Rollback immediately
                await self.rollback_manager.rollback(current_model)
                return False
        
        # Complete deployment
        await self._decommission_blue_instance(current_model)
        return True
```

### 4.2 Rollback Manager

```python
class RollbackManager:
    """
    Manages model rollback when issues detected.
    """
    
    def __init__(self):
        self.snapshots: Dict[str, ModelSnapshot] = {}
    
    async def create_snapshot(
        self,
        model: Model
    ) -> str:
        """
        Create snapshot of model state for rollback.
        
        Snapshot includes:
        - Model weights/files
        - Configuration
        - Performance metrics
        - Current traffic allocation
        """
        snapshot_id = f"snapshot-{model.id}-{int(time.time())}"
        
        snapshot = ModelSnapshot(
            id=snapshot_id,
            model_id=model.id,
            model_state=await self._capture_model_state(model),
            configuration=model.config,
            performance_metrics=await self._get_current_metrics(model),
            traffic_allocation=await self._get_traffic_allocation(model),
            timestamp=time.time()
        )
        
        self.snapshots[snapshot_id] = snapshot
        await self._persist_snapshot(snapshot)
        
        return snapshot_id
    
    async def rollback(
        self,
        target_model_id: str = None,
        snapshot_id: str = None
    ) -> bool:
        """
        Rollback to previous model state.
        
        Can rollback to:
        - Specific snapshot (snapshot_id)
        - Previous model version (target_model_id)
        - Most recent stable snapshot
        """
        if snapshot_id:
            snapshot = self.snapshots[snapshot_id]
        elif target_model_id:
            snapshot = await self._find_snapshot_for_model(target_model_id)
        else:
            snapshot = await self._get_most_recent_stable_snapshot()
        
        # Restore model state
        await self._restore_model_state(snapshot)
        
        # Restore traffic allocation
        await self._restore_traffic_allocation(snapshot)
        
        # Verify rollback success
        verification = await self._verify_rollback(snapshot)
        
        return verification.success
```

---

## 5. GUARDRAILS ENFORCEMENT

### 5.1 Guardrails Monitor

```python
class GuardrailsMonitor:
    """
    Monitors all models to ensure guardrails compliance.
    
    Key Principle: Immersive/addictive but NOT harmful to humans in real life.
    """
    
    def __init__(self):
        self.output_monitor = RealTimeOutputMonitor()
        self.safety_checker = SafetyChecker()
        self.addiction_tracker = AddictionMetricTracker()
        self.harmful_detector = HarmfulContentDetector()
    
    async def monitor_model_outputs(
        self,
        model_id: str,
        outputs: List[ModelOutput]
    ) -> MonitoringResults:
        """
        Monitor model outputs for guardrails compliance.
        
        Checks:
        1. Safety: No harmful content
        2. Addiction metrics: Engagement vs harmful addiction
        3. Ethical compliance: Fair, non-discriminatory
        4. Content appropriateness: Age-appropriate, rating-compliant
        """
        results = MonitoringResults()
        
        # 1. Safety checks
        safety_results = await self.safety_checker.check_outputs(outputs)
        results.safety = safety_results
        
        # 2. Addiction metrics
        addiction_results = await self.addiction_tracker.analyze_engagement(outputs)
        results.addiction_metrics = addiction_results
        
        # 3. Harmful content detection
        harmful_results = await self.harmful_detector.detect(outputs)
        results.harmful_content = harmful_results
        
        # Overall compliance
        results.compliant = (
            safety_results.passed and
            addiction_results.healthy_engagement and
            not harmful_results.detected
        )
        
        # Auto-intervention if non-compliant
        if not results.compliant:
            await self._trigger_intervention(model_id, results)
        
        return results
    
    async def _trigger_intervention(
        self,
        model_id: str,
        results: MonitoringResults
    ):
        """
        Trigger intervention when guardrails violated.
        
        Interventions:
        - Block harmful outputs
        - Adjust model parameters
        - Retrain model if persistent issues
        - Rollback model if severe violations
        """
        if results.harmful_content.severity == "critical":
            # Immediate rollback
            await self.rollback_manager.rollback(model_id)
        elif results.harmful_content.severity == "high":
            # Adjust parameters or block outputs
            await self._adjust_model_parameters(model_id, results)
        elif results.safety.passed == False:
            # Retrain with safety data
            await self._trigger_safety_retraining(model_id)
```

### 5.2 Addiction Metrics

```python
class AddictionMetricTracker:
    """
    Tracks engagement vs harmful addiction.
    
    Healthy Engagement:
    - Players return regularly but not obsessively
    - Players take breaks
    - Players have healthy balance
    
    Harmful Addiction:
    - Players unable to stop
    - Players neglect real-life responsibilities
    - Players show signs of distress when unable to play
    """
    
    async def analyze_engagement(
        self,
        outputs: List[ModelOutput]
    ) -> AddictionAnalysis:
        """
        Analyze if outputs encourage healthy or harmful engagement.
        
        Metrics:
        - Engagement hooks (healthy: encouraging return, unhealthy: manipulative)
        - Break encouragement (healthy models encourage breaks)
        - Real-life balance (healthy models acknowledge real life)
        - Manipulation techniques (unhealthy: FOMO, endless loops)
        """
        healthy_indicators = 0
        unhealthy_indicators = 0
        
        for output in outputs:
            # Check for healthy engagement patterns
            if self._encourages_breaks(output):
                healthy_indicators += 1
            if self._acknowledges_real_life(output):
                healthy_indicators += 1
            if self._has_respectful_boundaries(output):
                healthy_indicators += 1
            
            # Check for unhealthy patterns
            if self._uses_manipulation(output):
                unhealthy_indicators += 1
            if self._creates_fomo(output):
                unhealthy_indicators += 1
            if self._encourages_obsession(output):
                unhealthy_indicators += 1
        
        # Calculate score
        total_checks = len(outputs) * 3  # 3 checks per output
        healthy_score = healthy_indicators / total_checks
        unhealthy_score = unhealthy_indicators / total_checks
        
        return AddictionAnalysis(
            healthy_engagement=healthy_score >= 0.7,
            unhealthy_patterns_detected=unhealthy_score > 0.3,
            healthy_score=healthy_score,
            unhealthy_score=unhealthy_score,
            recommendation="continue" if healthy_score >= 0.7 else "intervene"
        )
```

---

## 6. META-MANAGEMENT MODEL

### 6.1 Meta-Manager Architecture

```python
class MetaManagementModel:
    """
    Meta-management model that orchestrates all model management.
    
    This model:
    - Does NOT directly participate in player worlds
    - Ensures best models at all times
    - Monitors and optimizes system
    - Enforces guardrails
    - Makes optimization decisions
    """
    
    def __init__(self):
        self.model_manager = ModelManagementSystem()
        self.monitor = SystemMonitor()
        self.decision_engine = OptimizationDecisionEngine()
        self.guardrails_enforcer = GuardrailsEnforcer()
    
    async def run_optimization_loop(self):
        """
        Continuous optimization loop.
        
        Runs:
        - Model discovery checks
        - Performance monitoring
        - Guardrails enforcement
        - Optimization decisions
        - Automatic improvements
        """
        while True:
            # 1. Check for better models
            await self._check_for_better_models()
            
            # 2. Monitor current models
            monitoring_results = await self.monitor.monitor_all_models()
            
            # 3. Enforce guardrails
            guardrails_results = await self.guardrails_enforcer.check_all_models()
            
            # 4. Make optimization decisions
            decisions = await self.decision_engine.analyze_and_decide(
                monitoring_results,
                guardrails_results
            )
            
            # 5. Implement decisions
            await self._implement_decisions(decisions)
            
            # 6. Wait before next cycle
            await asyncio.sleep(3600)  # Check every hour
    
    async def _check_for_better_models(self):
        """
        Check all use cases for better models.
        """
        use_cases = await self._get_all_use_cases()
        
        for use_case in use_cases:
            current_model = await self._get_current_model(use_case)
            
            # Check paid models (if applicable)
            if use_case.uses_paid_models:
                better_paid = await self.model_manager.paid_model_manager.check_for_better_models(
                    use_case=use_case.id,
                    current_model=current_model.id
                )
                
                if better_paid:
                    await self.model_manager.paid_model_manager.auto_switch_model(
                        use_case=use_case.id,
                        new_model=better_paid,
                        current_model=current_model.id
                    )
            
            # Check self-hosted models
            better_self_hosted = await self.model_manager.self_hosted_manager.discover_and_deploy_new_model(
                use_case=use_case.id,
                current_model_id=current_model.id
            )
    
    async def _implement_decisions(
        self,
        decisions: List[OptimizationDecision]
    ):
        """
        Implement optimization decisions.
        
        Decision types:
        - Deploy new model
        - Rollback model
        - Adjust model parameters
        - Retrain model
        - Update guardrails
        """
        for decision in decisions:
            if decision.type == "deploy_model":
                await self.model_manager.deployment_manager.deploy_model(
                    new_model=decision.target_model,
                    current_model=decision.current_model
                )
            elif decision.type == "rollback":
                await self.model_manager.rollback_manager.rollback(
                    model_id=decision.target_model.id
                )
            elif decision.type == "adjust_parameters":
                await self.model_manager.adjust_model_parameters(
                    model_id=decision.target_model.id,
                    adjustments=decision.parameter_adjustments
                )
            elif decision.type == "retrain":
                await self.model_manager.fine_tuning_pipeline.retrain_model(
                    model_id=decision.target_model.id,
                    reason=decision.reason
                )
```

---

## 7. DATABASE SCHEMA

```sql
-- Model registry
CREATE TABLE models (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- "paid" or "self_hosted"
    provider VARCHAR(100),  -- "openai", "anthropic", "huggingface", etc.
    use_case VARCHAR(100) NOT NULL,  -- "story_generation", "npc_dialogue", etc.
    version VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- "current", "candidate", "deprecated", "testing"
    model_path TEXT,  -- Path to model files (self-hosted)
    configuration JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, version, use_case)
);

-- Historical logs (for fine-tuning)
CREATE TABLE model_historical_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id),
    use_case VARCHAR(100),
    prompt TEXT NOT NULL,
    context JSONB,
    generated_output TEXT NOT NULL,
    user_feedback JSONB,  -- If user provided feedback/corrections
    corrected_output TEXT,  -- Corrected output if feedback provided
    performance_metrics JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Model snapshots (for rollback)
CREATE TABLE model_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id),
    snapshot_name VARCHAR(255),
    model_state_path TEXT NOT NULL,  -- Path to saved model state
    configuration JSONB NOT NULL,
    performance_metrics JSONB,
    traffic_allocation JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Guardrails monitoring
CREATE TABLE guardrails_violations (
    violation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id),
    violation_type VARCHAR(50),  -- "safety", "addiction", "harmful_content", etc.
    severity VARCHAR(20),  -- "critical", "high", "medium", "low"
    violation_details JSONB,
    output_sample TEXT,
    intervention_taken VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Model deployment history
CREATE TABLE model_deployments (
    deployment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id),
    deployment_type VARCHAR(50),  -- "blue_green", "canary", "all_at_once"
    status VARCHAR(20),  -- "in_progress", "completed", "rolled_back", "failed"
    traffic_percentage INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT NOW(),
    completion_time TIMESTAMP,
    rollback_reason TEXT
);

-- Indexes
CREATE INDEX idx_models_use_case_status ON models(use_case, status);
CREATE INDEX idx_models_type_status ON models(model_type, status);
CREATE INDEX idx_historical_logs_model_time ON model_historical_logs(model_id, timestamp DESC);
CREATE INDEX idx_guardrails_violations_model_time ON guardrails_violations(model_id, timestamp DESC);
CREATE INDEX idx_model_snapshots_model_time ON model_snapshots(model_id, created_at DESC);
```

---

## 8. API DESIGN

```python
# Model discovery
GET /api/v1/model-management/discover?use_case={use_case}
Response: {
    "candidate_models": [...],
    "ranking": [...],
    "recommendations": [...]
}

# Fine-tune model
POST /api/v1/model-management/fine-tune
Request: {
    "base_model_id": "uuid",
    "use_cases": [...],
    "historical_logs_range": {"start": "...", "end": "..."}
}
Response: {
    "fine_tuned_models": [...],
    "training_status": "in_progress",
    "estimated_completion": "..."
}

# Test model
POST /api/v1/model-management/test
Request: {
    "candidate_model_id": "uuid",
    "current_model_id": "uuid"
}
Response: {
    "test_results": {...},
    "meets_threshold": true/false,
    "similarity_score": 0.95
}

# Deploy model
POST /api/v1/model-management/deploy
Request: {
    "new_model_id": "uuid",
    "current_model_id": "uuid",
    "strategy": "blue_green"
}
Response: {
    "deployment_id": "uuid",
    "status": "in_progress"
}

# Rollback
POST /api/v1/model-management/rollback
Request: {
    "model_id": "uuid",
    "snapshot_id": "uuid"  # Optional
}

# Guardrails check
GET /api/v1/model-management/guardrails/{model_id}
Response: {
    "compliance_status": "compliant",
    "violations": [...],
    "metrics": {...}
}
```

---

**END OF SOLUTION DOCUMENT**


