# Learning/Feedback Service Solution
**Service**: Continuous Model Improvement via ML Pipeline  
**Date**: January 29, 2025  
**Status**: ⭐ **UPDATED** - CI/CD Deployment Pipeline added

---

## SERVICE OVERVIEW

Collects feedback from game instances, processes it via AWS ML services, and continuously improves models through retraining and A/B testing.

---

## ARCHITECTURE

### Technology Stack
- **Data Collection**: Kinesis Streams
- **Storage**: S3
- **Training**: AWS SageMaker
- **Deployment**: SageMaker Endpoints
- **Monitoring**: CloudWatch

### Feedback Collection Pipeline

```python
import boto3
import json

kinesis = boto3.client('kinesis')
s3 = boto3.client('s3')

def collect_feedback(game_event):
    """
    Collect feedback from game events
    - Player interactions
    - NPC dialogue quality
    - Model performance metrics
    """
    payload = {
        'event_type': game_event.type,
        'timestamp': game_event.timestamp,
        'data': game_event.data,
        'model_version': game_event.model_version
    }
    
    # Stream to Kinesis
    kinesis.put_record(
        StreamName='game-feedback-stream',
        Data=json.dumps(payload),
        PartitionKey=game_event.user_id
    )
```

### SageMaker Pipeline

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep

def create_training_pipeline():
    # Step 1: Process feedback data
    process_step = ProcessingStep(
        name="ProcessFeedbackData",
        processor=processing_processor,
        inputs=[
            ProcessingInput(
                source=s3_input_path,
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="train",
                source="/opt/ml/processing/train",
                destination=s3_train_path
            )
        ]
    )
    
    # Step 2: Train LoRA adapter
    train_step = TrainingStep(
        name="TrainLoRAAdapter",
        estimator=estimator,
        inputs={
            "training": TrainingInput(
                s3_data=process_step.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri
            )
        }
    )
    
    # Step 3: Evaluate model
    eval_step = ProcessingStep(
        name="EvaluateModel",
        processor=eval_processor,
        inputs=[
            ProcessingInput(
                source=train_step.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model"
            )
        ]
    )
    
    # Create pipeline
    pipeline = Pipeline(
        name="ModelTrainingPipeline",
        steps=[process_step, train_step, eval_step]
    )
    
    return pipeline
```

### Model Versioning & A/B Testing

```python
def deploy_model_variant(model_name, model_artifact_path):
    # Create model
    model = sagemaker.Model(
        model_data=model_artifact_path,
        role=sagemaker_role,
        image_uri=training_image
    )
    
    # Deploy endpoint with A/B testing
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type='ml.m5.xlarge',
        variant_name=model_name,
        variant_weight=10  # 10% traffic
    )
    
    return predictor
```

### Trigger Retraining

```python
def check_model_drift():
    """
    Monitor model performance and trigger retraining if drift detected
    """
    metrics = get_model_metrics()
    
    if metrics.quality_score < 0.85:  # Below threshold
        # Trigger pipeline
        pipeline = get_pipeline('ModelTrainingPipeline')
        execution = pipeline.start()
        
        # Wait for completion
        execution.wait()
        
        # Deploy new model
        deploy_model_variant('v2', execution.steps[-1].outputs[0])
```

---

## MODEL DEPLOYMENT PIPELINE ⭐ **NEW**

**Critical Integration Path**: Learning Service → Model Registry → CI/CD → AI Inference

### Automated Deployment Flow

```python
from sagemaker.model import Model
from sagemaker.pipeline import Pipeline
import mlflow

class ModelDeploymentPipeline:
    def __init__(self):
        self.model_registry = mlflow.tracking.MlflowClient()
        self.sagemaker_role = "arn:aws:iam::ACCOUNT:role/SageMakerRole"
    
    def deploy_to_production(self, model_artifact_path: str, model_version: str):
        """
        Complete deployment pipeline:
        1. Register model in MLflow
        2. Run automated tests
        3. Canary deployment (5% traffic)
        4. Full rollout
        5. Monitor and rollback if needed
        """
        
        # Step 1: Register in Model Registry
        model_uri = f"runs:/{run_id}/model"
        mv = mlflow.register_model(
            model_uri,
            "body-broker-models"
        )
        
        # Step 2: Automated Testing
        test_results = self.run_automated_tests(mv.version)
        if not test_results.passed:
            raise Exception(f"Model tests failed: {test_results.errors}")
        
        # Step 3: Safety Checks
        safety_score = self.check_safety_filters(mv.version)
        if safety_score.toxicity > TOXICITY_THRESHOLD:
            raise Exception(f"Model rejected: toxicity score too high")
        
        # Step 4: Deploy to Canary (5% traffic)
        canary_endpoint = self.deploy_canary(mv, traffic_weight=5)
        
        # Step 5: Monitor canary performance
        canary_metrics = self.monitor_canary(canary_endpoint, duration_hours=24)
        if canary_metrics.error_rate > 0.01:  # 1% error threshold
            self.rollback_canary(canary_endpoint)
            raise Exception("Canary deployment failed, rolled back")
        
        # Step 6: Full Rollout
        production_endpoint = self.deploy_full(canary_endpoint, traffic_weight=100)
        
        return production_endpoint
    
    def run_automated_tests(self, model_version: str) -> TestResults:
        """Run safety, performance, and quality tests"""
        tests = [
            self.test_toxicity_score(model_version),
            self.test_perplexity_score(model_version),
            self.test_latency(model_version),
            self.test_output_quality(model_version)
        ]
        
        return TestResults(
            passed=all(t.passed for t in tests),
            errors=[t.error for t in tests if not t.passed]
        )
    
    def deploy_canary(self, model_version, traffic_weight: int = 5):
        """Deploy to 5% of traffic for testing"""
        model = Model(
            model_data=f"s3://models/body-broker/{model_version}/model.tar.gz",
            role=self.sagemaker_role,
            framework_version="2.0"
        )
        
        predictor = model.deploy(
            initial_instance_count=1,
            instance_type="ml.g4dn.xlarge",
            variant_name=f"canary-{model_version}",
            variant_weight=traffic_weight
        )
        
        return predictor
    
    def deploy_full(self, canary_endpoint, traffic_weight: int = 100):
        """Move from canary to full production"""
        # Update traffic weight to 100%
        canary_endpoint.update_endpoint_weights({
            f"canary-{model_version}": traffic_weight
        })
        
        return canary_endpoint
```

### CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/model-deployment.yml
name: Model Deployment Pipeline

on:
  workflow_dispatch:
    inputs:
      model_version:
        description: 'Model version to deploy'
        required: true

jobs:
  test-model:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Model Tests
        run: |
          python tests/test_model_safety.py --version ${{ github.event.inputs.model_version }}
          python tests/test_model_performance.py --version ${{ github.event.inputs.model_version }}
  
  deploy-canary:
    needs: test-model
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Canary
        run: |
          aws sagemaker create-endpoint-config \
            --endpoint-config-name canary-${{ github.event.inputs.model_version }} \
            --production-variants VariantName=canary,ModelName=model-${{ version }},InitialVariantWeight=5
  
  monitor-canary:
    needs: deploy-canary
    runs-on: ubuntu-latest
    steps:
      - name: Monitor Canary Performance
        run: |
          python scripts/monitor_canary.py --duration 24h
  
  deploy-production:
    needs: monitor-canary
    if: success()
    runs-on: ubuntu-latest
    steps:
      - name: Full Production Rollout
        run: |
          aws sagemaker update-endpoint-weights \
            --endpoint-name production-endpoint \
            --production-variants VariantName=canary,Weight=100
```

### Model Versioning & Rollback

```python
class ModelVersion:
    model_id: str
    version: str
    training_date: datetime
    player_cohort: List[str]
    performance_metrics: Dict[str, float]
    deployment_status: str  # "canary", "production", "rolled_back"

def rollback_model(version: str):
    """Rollback to previous version"""
    previous_version = get_previous_production_version()
    
    # Update traffic weights
    update_endpoint_weights({
        f"model-{previous_version}": 100,
        f"model-{version}": 0
    })
    
    # Log rollback
    log_model_event({
        "event": "rollback",
        "from_version": version,
        "to_version": previous_version,
        "reason": "performance degradation"
    })
```

### Integration with AI Inference Service

```python
# AI Inference Service receives new models
@app.post("/api/v1/models/deploy")
async def deploy_model(model_deployment: ModelDeployment):
    """
    Receives deployment notification from CI/CD pipeline
    """
    # Load new model
    await load_model(
        model_id=model_deployment.model_id,
        model_path=model_deployment.model_path,
        version=model_deployment.version
    )
    
    # Update routing to use new model
    update_model_routing(model_deployment.model_id, model_deployment.traffic_weight)
    
    return {"status": "deployed", "version": model_deployment.version}
```

---

**Next**: See `MODERATION-SERVICE.md` for content safety.

