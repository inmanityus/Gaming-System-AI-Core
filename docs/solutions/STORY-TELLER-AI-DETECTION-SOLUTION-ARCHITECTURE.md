# Story Teller AI Detection System - Solution Architecture
**Date**: 2025-11-20  
**Status**: DRAFT - Multi-Model Solution Design  
**Contributors**: Claude Sonnet 4.5, GPT 5.1, Gemini 2.5 Pro, Grok 4

---

## 1. SOLUTION OVERVIEW

This document presents the technical solution for implementing the Story Teller AI Detection & Review System, designed to generate narratives that are completely undetectable as AI-generated.

### Solution Principles
1. **Adversarial Architecture**: Generation and detection in continuous competition
2. **Microservices Design**: Independent, scalable components
3. **Event-Driven Flow**: Asynchronous processing for performance
4. **Continuous Learning**: Models evolve based on detection feedback
5. **Multi-Layer Validation**: Quality gates at each stage

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Components

```yaml
story-teller-system:
  orchestration:
    - workflow-engine        # Apache Airflow or Temporal
    - state-manager         # Redis + PostgreSQL
    - event-bus            # Kafka/RabbitMQ
    
  generation-layer:
    - model-ensemble:
        - gpt-5.1          # via OpenAI API
        - claude-4.1       # via Anthropic API
        - gemini-2.5      # via Google API
        - grok-4          # via X.AI API
    - dynamic-router       # Custom Python service
    - context-manager      # Manages state between models
    
  review-layer:
    - creativity-reviewer   # Fine-tuned Llama-3-70B
    - originality-checker  # Fine-tuned Mistral-8x7B
    - lore-validator      # RAG-enhanced BERT
    - continuity-guard    # Custom transformer model
    
  detection-layer:
    - statistical-detector  # Perplexity/burstiness analyzer
    - neural-detector      # Custom discriminator network
    - commercial-apis      # GPTZero, Originality.ai
    - ensemble-aggregator  # Weighted voting system
    
  support-services:
    - lore-rag-service     # pgvector + embedding API
    - continuity-db        # Neo4j graph database
    - metrics-collector    # Prometheus + Grafana
    - admin-portal        # React + FastAPI
```

### 2.2 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Load Balancer (ALB)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  API Gateway (Kong)                      │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│               Kubernetes Cluster (EKS)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Orchestration Namespace               │   │
│  │  - Workflow Engine Pods (3 replicas)            │   │
│  │  - State Manager Pods (2 replicas)              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Generation Namespace                   │   │
│  │  - Model Router Pods (5 replicas)               │   │
│  │  - Context Manager Pods (3 replicas)            │   │
│  │  - Model Adapters (1 per model)                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │             Review Namespace                     │   │
│  │  - Reviewer Pods (GPU, 2-4 per type)            │   │
│  │  - Score Aggregator Pods (3 replicas)           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Detection Namespace                    │   │
│  │  - Detector Pods (GPU, 2-3 per type)            │   │
│  │  - Feedback Generator Pods (2 replicas)         │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Data Layer                              │
│  - PostgreSQL (RDS Aurora)                              │
│  - Redis Cluster (ElastiCache)                          │
│  - Neo4j (EC2 or Aura)                                  │
│  - S3 (Document storage)                                │
└─────────────────────────────────────────────────────────┘
```

---

## 3. IMPLEMENTATION COMPONENTS

### 3.1 Workflow Engine

**Technology**: Apache Airflow or Temporal
**Purpose**: Orchestrate the multi-stage generation process

```python
# Example DAG for story generation
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'story-teller',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'story_generation_pipeline',
    default_args=default_args,
    description='Multi-stage story generation with review and detection',
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:
    
    initialize = PythonOperator(
        task_id='initialize_context',
        python_callable=initialize_generation_context,
    )
    
    generate = PythonOperator(
        task_id='ensemble_generation',
        python_callable=run_model_ensemble,
    )
    
    review = PythonOperator(
        task_id='creative_review',
        python_callable=run_reviewers,
    )
    
    detect = PythonOperator(
        task_id='ai_detection',
        python_callable=run_detectors,
    )
    
    refine = PythonOperator(
        task_id='iterative_refinement',
        python_callable=refine_content,
    )
    
    finalize = PythonOperator(
        task_id='finalize_output',
        python_callable=prepare_final_narrative,
    )
    
    initialize >> generate >> [review, detect] >> refine >> finalize
```

### 3.2 Model Ensemble Service

**Technology**: Python FastAPI + Celery
**Purpose**: Manage multiple AI models for generation

```python
# services/generation/model_ensemble.py
from fastapi import FastAPI, BackgroundTasks
from celery import Celery
from typing import Dict, List, Optional
import asyncio

app = FastAPI()
celery = Celery('tasks', broker='redis://redis:6379')

class ModelEnsemble:
    def __init__(self):
        self.models = {
            'gpt-5.1': GPT51Adapter(),
            'claude-4.1': Claude41Adapter(),
            'gemini-2.5': Gemini25Adapter(),
            'grok-4': Grok4Adapter(),
        }
        self.router = DynamicModelRouter()
        
    async def generate(self, 
                      prompt: str, 
                      context: Dict,
                      world_config: Dict) -> Dict:
        """
        Orchestrate multi-model generation
        """
        # Select models based on content type
        selected_models = self.router.select_models(
            content_type=context.get('type', 'narrative'),
            performance_requirement=context.get('latency', 'normal')
        )
        
        # Parallel generation
        tasks = []
        for model_name in selected_models:
            model = self.models[model_name]
            task = asyncio.create_task(
                model.generate(prompt, context, world_config)
            )
            tasks.append((model_name, task))
        
        # Collect results
        results = {}
        for model_name, task in tasks:
            try:
                results[model_name] = await task
            except Exception as e:
                logger.error(f"Model {model_name} failed: {e}")
                
        # Synthesize outputs
        final_output = self.synthesize_outputs(results, context)
        return final_output
    
    def synthesize_outputs(self, results: Dict, context: Dict) -> Dict:
        """
        Combine multiple model outputs intelligently
        """
        # Weight models based on their specialization
        weights = self.router.get_weights(context)
        
        # Voting mechanism for conflicts
        synthesized = {
            'text': self.weighted_text_merge(results, weights),
            'metadata': self.merge_metadata(results),
            'confidence': self.calculate_confidence(results),
        }
        
        return synthesized

@app.post("/generate")
async def generate_narrative(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    API endpoint for narrative generation
    """
    # Queue the generation task
    task = celery.send_task(
        'generate_with_ensemble',
        args=[request.dict()]
    )
    
    return {
        'task_id': task.id,
        'status': 'queued',
        'estimated_time': estimate_generation_time(request)
    }
```

### 3.3 Review Service Architecture

**Technology**: Transformers + Custom Models
**Purpose**: Evaluate narratives for quality and compliance

```python
# services/review/reviewer_ensemble.py
import torch
from transformers import AutoModelForSequenceClassification
from typing import List, Dict, Tuple

class ReviewerEnsemble:
    def __init__(self):
        self.reviewers = {
            'creativity': CreativityReviewer(
                model_path='models/llama3-70b-creativity'
            ),
            'originality': OriginalityReviewer(
                model_path='models/mistral-8x7b-originality'
            ),
            'lore': LoreReviewer(
                model_path='models/bert-lore-validator',
                knowledge_base='postgresql://lore_db'
            ),
            'continuity': ContinuityReviewer(
                model_path='models/custom-continuity',
                graph_db='neo4j://continuity_graph'
            ),
        }
        
    async def review(self, 
                    narrative: str, 
                    context: Dict,
                    world_id: str) -> ReviewResult:
        """
        Comprehensive narrative review
        """
        scores = {}
        feedback = []
        
        # Parallel review execution
        review_tasks = []
        for name, reviewer in self.reviewers.items():
            task = asyncio.create_task(
                reviewer.evaluate(narrative, context, world_id)
            )
            review_tasks.append((name, task))
        
        # Collect results
        for name, task in review_tasks:
            result = await task
            scores[name] = result.score
            feedback.extend(result.feedback)
        
        # Aggregate scores
        overall_score = self.calculate_overall_score(scores)
        
        # Generate structured feedback
        structured_feedback = self.structure_feedback(
            feedback, 
            scores, 
            narrative
        )
        
        return ReviewResult(
            scores=scores,
            overall_score=overall_score,
            feedback=structured_feedback,
            pass_threshold=self.get_threshold(world_id)
        )

class CreativityReviewer:
    def __init__(self, model_path: str):
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_path
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
    async def evaluate(self, 
                      text: str, 
                      context: Dict, 
                      world_id: str) -> ReviewScore:
        """
        Evaluate narrative creativity
        """
        # Tokenize input
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True,
            max_length=2048
        )
        
        # Generate creativity score
        with torch.no_grad():
            outputs = self.model(**inputs)
            creativity_score = torch.sigmoid(outputs.logits).item()
        
        # Analyze specific creative elements
        creative_elements = self.analyze_creative_elements(text)
        
        # Generate feedback
        feedback = self.generate_feedback(
            creativity_score, 
            creative_elements
        )
        
        return ReviewScore(
            score=creativity_score * 100,
            feedback=feedback,
            details=creative_elements
        )
```

### 3.4 AI Detection Service

**Technology**: Custom PyTorch Models + External APIs
**Purpose**: Ensure output is undetectable as AI-generated

```python
# services/detection/detection_ensemble.py
import numpy as np
from typing import Dict, List, Tuple
import torch
import torch.nn as nn

class DetectionEnsemble:
    def __init__(self):
        self.detectors = {
            'statistical': StatisticalDetector(),
            'neural': NeuralDetector(
                model_path='models/custom_discriminator.pt'
            ),
            'perplexity': PerplexityAnalyzer(),
            'external': ExternalAPIDetector([
                'gptzero',
                'originality_ai',
                'writer_com'
            ])
        }
        self.adversarial_trainer = AdversarialTrainer()
        
    async def detect(self, 
                    text: str, 
                    metadata: Dict) -> DetectionResult:
        """
        Multi-method AI detection
        """
        detection_scores = {}
        detailed_feedback = []
        
        # Run all detectors
        for name, detector in self.detectors.items():
            score, feedback = await detector.analyze(text, metadata)
            detection_scores[name] = score
            detailed_feedback.append({
                'detector': name,
                'score': score,
                'feedback': feedback
            })
        
        # Calculate aggregate score
        aggregate_score = self.calculate_aggregate_score(
            detection_scores
        )
        
        # Generate improvement suggestions
        suggestions = self.generate_improvement_suggestions(
            text,
            detailed_feedback,
            aggregate_score
        )
        
        # Update adversarial training data
        if self.should_update_training(aggregate_score):
            self.adversarial_trainer.add_sample(
                text, 
                detection_scores, 
                metadata
            )
        
        return DetectionResult(
            aggregate_score=aggregate_score,
            individual_scores=detection_scores,
            feedback=detailed_feedback,
            suggestions=suggestions,
            passes_threshold=(aggregate_score < 5.0)
        )

class AdversarialTrainer:
    """
    Continuously improve generation based on detection feedback
    """
    def __init__(self):
        self.training_buffer = []
        self.discriminator = self.load_discriminator()
        self.update_frequency = 1000  # samples
        
    def add_sample(self, 
                   text: str, 
                   detection_scores: Dict, 
                   metadata: Dict):
        """
        Add detected sample to training buffer
        """
        self.training_buffer.append({
            'text': text,
            'scores': detection_scores,
            'metadata': metadata,
            'timestamp': datetime.utcnow()
        })
        
        if len(self.training_buffer) >= self.update_frequency:
            self.trigger_retraining()
    
    async def trigger_retraining(self):
        """
        Retrain discriminator and update generator guidance
        """
        # Prepare training data
        X = [sample['text'] for sample in self.training_buffer]
        y = [sample['scores']['aggregate'] for sample in self.training_buffer]
        
        # Fine-tune discriminator
        self.discriminator.fine_tune(X, y)
        
        # Extract patterns for generator improvement
        patterns = self.analyze_detection_patterns()
        
        # Update generator prompts/parameters
        await self.update_generator_guidance(patterns)
        
        # Clear buffer
        self.training_buffer = []
```

### 3.5 RAG Service for Lore

**Technology**: PostgreSQL + pgvector + LangChain
**Purpose**: Efficient retrieval of narrative documents

```python
# services/lore/rag_service.py
from langchain.vectorstores import PGVector
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
import asyncpg
from typing import List, Dict

class LoreRAGService:
    def __init__(self, connection_string: str):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large"
        )
        self.vector_store = PGVector(
            connection_string=connection_string,
            embedding_function=self.embeddings,
            collection_name="narrative_lore"
        )
        self.compressor = self.setup_compressor()
        
    def setup_compressor(self):
        """
        Setup contextual compression for relevant extraction
        """
        compressor_llm = ChatOpenAI(
            temperature=0, 
            model_name="gpt-5.1"
        )
        return LLMChainExtractor.from_llm(compressor_llm)
    
    async def retrieve_lore(self, 
                           query: str, 
                           world_id: str,
                           context_type: str = 'general',
                           top_k: int = 10) -> List[Dict]:
        """
        Retrieve relevant lore with contextual compression
        """
        # Build metadata filter
        metadata_filter = {
            'world_id': world_id,
            'document_type': self.map_context_type(context_type)
        }
        
        # Retrieve raw documents
        raw_docs = await self.vector_store.asimilarity_search(
            query,
            k=top_k * 2,  # Over-retrieve for compression
            filter=metadata_filter
        )
        
        # Apply contextual compression
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=self.vector_store.as_retriever(
                search_kwargs={
                    "k": top_k * 2,
                    "filter": metadata_filter
                }
            )
        )
        
        compressed_docs = await compression_retriever.aget_relevant_documents(
            query
        )
        
        # Format for consumption
        formatted_lore = []
        for doc in compressed_docs[:top_k]:
            formatted_lore.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'relevance_score': doc.metadata.get('score', 0.0),
                'source': doc.metadata.get('source', 'unknown'),
                'chunk_id': doc.metadata.get('chunk_id', '')
            })
        
        return formatted_lore
    
    async def validate_lore_consistency(self,
                                       narrative: str,
                                       world_id: str) -> Dict:
        """
        Check narrative against established lore
        """
        # Extract key entities and facts
        entities = await self.extract_entities(narrative)
        
        # Verify each against lore
        inconsistencies = []
        for entity in entities:
            lore_facts = await self.retrieve_lore(
                query=f"{entity['type']}: {entity['name']}",
                world_id=world_id,
                context_type='entity'
            )
            
            conflicts = self.check_conflicts(
                entity, 
                lore_facts
            )
            
            if conflicts:
                inconsistencies.extend(conflicts)
        
        return {
            'is_consistent': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies,
            'confidence': self.calculate_confidence(inconsistencies)
        }
```

### 3.6 Admin Portal

**Technology**: React + FastAPI + PostgreSQL
**Purpose**: Secure interface for rule management

```python
# services/admin/portal_api.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Dict
import json

app = FastAPI(title="Story Teller Admin Portal")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class RuleEngine:
    def __init__(self, db: Session):
        self.db = db
        
    async def get_reviewer_rules(self, 
                                reviewer_type: str,
                                world_id: Optional[str] = None) -> Dict:
        """
        Retrieve current reviewer rules
        """
        query = self.db.query(ReviewerRule).filter(
            ReviewerRule.reviewer_type == reviewer_type
        )
        
        if world_id:
            query = query.filter(ReviewerRule.world_id == world_id)
            
        rules = query.all()
        return [rule.to_dict() for rule in rules]
    
    async def update_reviewer_rule(self,
                                  rule_id: int,
                                  rule_data: Dict,
                                  user_id: str) -> Dict:
        """
        Update reviewer rule with audit trail
        """
        rule = self.db.query(ReviewerRule).get(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Store previous version
        rule_history = ReviewerRuleHistory(
            rule_id=rule_id,
            previous_data=rule.rule_data,
            updated_by=user_id,
            updated_at=datetime.utcnow()
        )
        self.db.add(rule_history)
        
        # Update rule
        rule.rule_data = json.dumps(rule_data)
        rule.version += 1
        rule.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Trigger rule reload in services
        await self.notify_services_rule_update(rule_id)
        
        return rule.to_dict()

@app.get("/api/rules/{reviewer_type}")
async def get_rules(
    reviewer_type: str,
    world_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reviewer rules
    """
    engine = RuleEngine(db)
    return await engine.get_reviewer_rules(reviewer_type, world_id)

@app.put("/api/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update reviewer rule
    """
    if not current_user.has_permission('rule.update'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
        
    engine = RuleEngine(db)
    return await engine.update_reviewer_rule(
        rule_id, 
        rule_data.dict(), 
        current_user.id
    )
```

---

## 4. DEPLOYMENT STRATEGY

### 4.1 Infrastructure as Code

```yaml
# terraform/story-teller/main.tf
module "story_teller_cluster" {
  source = "./modules/eks"
  
  cluster_name = "story-teller-eks"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
  
  node_groups = {
    orchestration = {
      instance_types = ["m5.xlarge"]
      min_size      = 2
      max_size      = 10
      desired_size  = 3
    }
    
    generation = {
      instance_types = ["g5.2xlarge"]  # GPU for models
      min_size      = 2
      max_size      = 20
      desired_size  = 5
      
      taints = [{
        key    = "gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
    
    review_detection = {
      instance_types = ["g5.xlarge"]
      min_size      = 4
      max_size      = 40
      desired_size  = 10
      
      taints = [{
        key    = "ml-workload"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }
}

module "databases" {
  source = "./modules/data-layer"
  
  # PostgreSQL for lore and state
  postgres_config = {
    engine         = "aurora-postgresql"
    engine_version = "15.4"
    instance_class = "db.r6g.2xlarge"
    storage_size   = 1000
    
    extensions = ["pgvector", "pg_trgm", "uuid-ossp"]
  }
  
  # Redis for caching and queues
  redis_config = {
    node_type      = "cache.m6g.xlarge"
    num_nodes      = 3
    engine_version = "7.0"
  }
  
  # Neo4j for continuity graph
  neo4j_config = {
    instance_type = "m5.2xlarge"
    volume_size   = 500
    version       = "5.15"
  }
}
```

### 4.2 Kubernetes Manifests

```yaml
# k8s/story-teller/generation-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-ensemble
  namespace: story-generation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: model-ensemble
  template:
    metadata:
      labels:
        app: model-ensemble
    spec:
      nodeSelector:
        node.kubernetes.io/instance-type: g5.2xlarge
      tolerations:
      - key: "gpu"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      containers:
      - name: ensemble-service
        image: story-teller/model-ensemble:v1.0.0
        resources:
          requests:
            memory: "32Gi"
            cpu: "8"
            nvidia.com/gpu: "1"
          limits:
            memory: "64Gi"
            cpu: "16"
            nvidia.com/gpu: "1"
        env:
        - name: MODELS_CONFIG
          valueFrom:
            configMapKeyRef:
              name: model-config
              key: ensemble.json
        - name: KAFKA_BROKERS
          value: "kafka-0.kafka:9092,kafka-1.kafka:9092,kafka-2.kafka:9092"
        volumeMounts:
        - name: model-cache
          mountPath: /models
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: model-ensemble
  namespace: story-generation
spec:
  selector:
    app: model-ensemble
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  - port: 9090
    targetPort: 9090
    name: metrics
```

### 4.3 Auto-Scaling Configuration

```yaml
# k8s/story-teller/autoscaling.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: model-ensemble-hpa
  namespace: story-generation
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: model-ensemble
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: generation_queue_depth
      target:
        type: AverageValue
        averageValue: "30"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 4
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
```

---

## 5. MONITORING & OBSERVABILITY

### 5.1 Metrics Architecture

```yaml
# prometheus/story-teller-metrics.yaml
groups:
  - name: story_teller_generation
    interval: 30s
    rules:
      - record: generation:success_rate
        expr: |
          sum(rate(story_generation_complete_total[5m])) /
          sum(rate(story_generation_attempts_total[5m]))
          
      - record: generation:ai_detection_score
        expr: |
          histogram_quantile(0.95,
            sum(rate(ai_detection_score_bucket[5m])) by (le)
          )
          
      - record: generation:creativity_score
        expr: |
          avg(story_creativity_score)
          
      - alert: HighAIDetectionRate
        expr: generation:ai_detection_score > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High AI detection rate"
          description: "AI detection score is {{ $value }}% (threshold: 10%)"
          
      - alert: LowCreativityScore
        expr: generation:creativity_score < 70
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low creativity scores"
          description: "Average creativity score is {{ $value }}% (threshold: 70%)"
```

### 5.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Story Teller AI System",
    "panels": [
      {
        "title": "Generation Pipeline Status",
        "targets": [
          {
            "expr": "sum(rate(story_generation_complete_total[5m])) by (status)"
          }
        ]
      },
      {
        "title": "AI Detection Scores",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(ai_detection_score_bucket[5m])) by (le, detector))"
          }
        ]
      },
      {
        "title": "Model Performance",
        "targets": [
          {
            "expr": "avg(model_inference_duration_seconds) by (model)"
          }
        ]
      },
      {
        "title": "Review Scores Distribution",
        "targets": [
          {
            "expr": "avg(review_score) by (reviewer_type)"
          }
        ]
      }
    ]
  }
}
```

---

## 6. COST OPTIMIZATION

### 6.1 Resource Allocation Strategy

```yaml
cost_optimization:
  model_tiering:
    tier_1:  # Fast, small models for drafts
      models: ["llama-3-8b", "mistral-7b"]
      use_cases: ["initial_draft", "simple_edits"]
      cost_per_1k_tokens: 0.0001
      
    tier_2:  # Medium models for refinement
      models: ["llama-3-70b", "mixtral-8x7b"]
      use_cases: ["creative_review", "style_improvement"]
      cost_per_1k_tokens: 0.001
      
    tier_3:  # Large models for final polish
      models: ["gpt-5.1", "claude-4.1", "gemini-2.5"]
      use_cases: ["final_generation", "complex_narratives"]
      cost_per_1k_tokens: 0.01
      
  caching_strategy:
    lore_cache:
      ttl: 3600  # 1 hour
      size: 10GB
      
    generation_cache:
      ttl: 300   # 5 minutes
      size: 50GB
      
    embedding_cache:
      ttl: 86400 # 24 hours
      size: 100GB
      
  spot_instances:
    enabled: true
    percentage: 70  # 70% spot, 30% on-demand
    fallback: true
```

### 6.2 Cost Monitoring

```python
# services/cost/monitor.py
class CostMonitor:
    def __init__(self):
        self.thresholds = {
            'hourly': 100,    # $100/hour
            'daily': 2000,    # $2000/day
            'monthly': 50000  # $50k/month
        }
        
    async def track_generation_cost(self, 
                                   generation_id: str,
                                   model_usage: Dict[str, int]) -> float:
        """
        Track cost per generation
        """
        total_cost = 0
        
        for model, tokens in model_usage.items():
            rate = self.get_model_rate(model)
            cost = (tokens / 1000) * rate
            total_cost += cost
            
            # Record in metrics
            await self.metrics.record(
                'generation_cost',
                cost,
                tags={
                    'model': model,
                    'generation_id': generation_id
                }
            )
        
        # Check thresholds
        await self.check_cost_thresholds()
        
        return total_cost
```

---

## 7. IMPLEMENTATION TIMELINE

### Phase 1: Foundation (Weeks 1-4)
- Set up infrastructure (EKS, databases)
- Deploy orchestration layer
- Implement basic generation ensemble
- Create simple review service

### Phase 2: Core Features (Weeks 5-8)
- Implement full reviewer ensemble
- Deploy detection layer
- Create adversarial training pipeline
- Build RAG service

### Phase 3: Refinement (Weeks 9-12)
- Optimize performance
- Implement caching layers
- Build admin portal
- Create monitoring dashboards

### Phase 4: Production (Weeks 13-16)
- Load testing at scale
- Security hardening
- Documentation completion
- Production deployment

---

## APPENDIX: KEY DECISIONS

### Technology Choices
1. **Kubernetes**: For orchestration and scaling
2. **Kafka**: For high-throughput event streaming
3. **PostgreSQL + pgvector**: For vector similarity search
4. **Neo4j**: For relationship tracking
5. **FastAPI**: For high-performance APIs
6. **React**: For admin portal UI

### Model Selection Rationale
1. **GPT-5.1**: Best overall quality
2. **Claude 4.1**: Superior character consistency
3. **Gemini 2.5**: Excellent world-building
4. **Grok 4**: Creative edge cases
5. **Open-source**: Cost efficiency and customization

### Architecture Patterns
1. **Microservices**: Independent scaling and development
2. **Event-driven**: Asynchronous processing
3. **Circuit breakers**: Fault tolerance
4. **Caching layers**: Performance optimization
5. **Observability-first**: Comprehensive monitoring
