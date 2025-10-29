# Learning/Feedback Service Solution
**Service**: Continuous Model Improvement via ML Pipeline  
**Date**: January 29, 2025

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

**Next**: See `MODERATION-SERVICE.md` for content safety.

