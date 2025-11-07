# Quantization Quality Benchmarks & A/B Testing
**Date**: January 29, 2025  
**Critical**: Medium Priority - Quality Assurance

---

## OVERVIEW

Complete quality assurance framework for model quantization to ensure acceptable quality degradation while achieving performance gains.

---

## QUALITY BENCHMARKS

### Acceptable Quality Loss Thresholds

| Metric | Threshold | Measurement Method |
|--------|-----------|-------------------|
| **Perplexity Increase** | < 8% | Language modeling evaluation |
| **BLEU Score Drop** | < 5% | Translation quality (if applicable) |
| **Toxicity Score** | No increase | Safety evaluation |
| **Coherence Score** | > 0.85 | Human evaluation |
| **Player Satisfaction** | No drop | User feedback (1-5 scale) |
| **Skip Rate** | < 2% | Players skipping NPC responses |

### Quality Testing Framework

```python
from dataclasses import dataclass
from typing import Dict, List
import numpy as np

@dataclass
class QualityMetrics:
    perplexity_fp32: float
    perplexity_int8: float
    bleu_fp32: float
    bleu_int8: float
    toxicity_fp32: float
    toxicity_int8: float
    coherence_fp32: float
    coherence_int8: float

class QuantizationQualityTester:
    def __init__(self):
        self.fp32_model = load_model("llama3.1-8b-fp32")
        self.int8_model = load_quantized_model("llama3.1-8b-int8")
        self.test_dataset = load_quality_test_dataset()
    
    async def evaluate_quantization_quality(self) -> QualityMetrics:
        """Run comprehensive quality evaluation"""
        results_fp32 = []
        results_int8 = []
        
        for test_case in self.test_dataset:
            # FP32 baseline
            response_fp32 = await self.fp32_model.generate(test_case.prompt)
            metrics_fp32 = self.compute_metrics(test_case, response_fp32)
            results_fp32.append(metrics_fp32)
            
            # INT8 quantized
            response_int8 = await self.int8_model.generate(test_case.prompt)
            metrics_int8 = self.compute_metrics(test_case, response_int8)
            results_int8.append(metrics_int8)
        
        # Aggregate metrics
        return QualityMetrics(
            perplexity_fp32=np.mean([r.perplexity for r in results_fp32]),
            perplexity_int8=np.mean([r.perplexity for r in results_int8]),
            bleu_fp32=np.mean([r.bleu for r in results_fp32]),
            bleu_int8=np.mean([r.bleu for r in results_int8]),
            toxicity_fp32=np.mean([r.toxicity for r in results_fp32]),
            toxicity_int8=np.mean([r.toxicity for r in results_int8]),
            coherence_fp32=np.mean([r.coherence for r in results_fp32]),
            coherence_int8=np.mean([r.coherence for r in results_int8])
        )
    
    def compute_metrics(self, test_case, response) -> Dict:
        """Compute quality metrics for a response"""
        return {
            "perplexity": self.compute_perplexity(response, test_case.reference),
            "bleu": self.compute_bleu(response, test_case.reference),
            "toxicity": self.compute_toxicity(response),
            "coherence": self.compute_coherence(response, test_case.context)
        }
    
    def validate_quality(self, metrics: QualityMetrics) -> tuple[bool, List[str]]:
        """Validate metrics meet thresholds"""
        issues = []
        
        # Check perplexity increase
        perplexity_increase = (
            (metrics.perplexity_int8 - metrics.perplexity_fp32) / 
            metrics.perplexity_fp32
        ) * 100
        if perplexity_increase > 8:
            issues.append(f"Perplexity increase {perplexity_increase:.2f}% exceeds 8% threshold")
        
        # Check BLEU drop
        bleu_drop = metrics.bleu_fp32 - metrics.bleu_int8
        if bleu_drop > 0.05:
            issues.append(f"BLEU drop {bleu_drop:.4f} exceeds 0.05 threshold")
        
        # Check toxicity
        if metrics.toxicity_int8 > metrics.toxicity_fp32:
            issues.append("Toxicity increased with quantization")
        
        # Check coherence
        if metrics.coherence_int8 < 0.85:
            issues.append(f"Coherence {metrics.coherence_int8:.2f} below 0.85 threshold")
        
        return len(issues) == 0, issues
```

---

## A/B TESTING STRATEGY

### Gradual Rollout Plan

```python
class QuantizationABTest:
    def __init__(self):
        self.ab_test_config = {
            "phase_1": {
                "fp32_percent": 90,  # 90% stay on FP32
                "int8_percent": 10,  # 10% test INT8
                "duration_days": 7,
                "success_criteria": {
                    "quality_complaints": "< 2%",
                    "skip_rate_increase": "< 1%",
                    "player_satisfaction_drop": "< 0.1 points"
                }
            },
            "phase_2": {
                "fp32_percent": 50,
                "int8_percent": 50,
                "duration_days": 14,
                "success_criteria": {
                    "quality_complaints": "< 1.5%",
                    "skip_rate_increase": "< 0.5%",
                    "player_satisfaction_drop": "< 0.05 points"
                }
            },
            "phase_3": {
                "fp32_percent": 10,
                "int8_percent": 90,
                "duration_days": 7,
                "success_criteria": {
                    "quality_complaints": "< 1%",
                    "skip_rate_increase": "< 0.2%",
                    "player_satisfaction_drop": "< 0.02 points"
                }
            }
        }
    
    async def assign_model_version(self, user_id: str) -> str:
        """Assign FP32 or INT8 based on A/B test"""
        user_hash = hash(user_id) % 100
        
        current_phase = self.get_current_phase()
        config = self.ab_test_config[current_phase]
        
        if user_hash < config["int8_percent"]:
            return "int8"
        else:
            return "fp32"
    
    async def monitor_ab_test(self):
        """Monitor A/B test metrics"""
        while True:
            await asyncio.sleep(3600)  # Every hour
            
            metrics = await self.compute_ab_test_metrics()
            
            # Check success criteria
            current_phase = self.get_current_phase()
            criteria = self.ab_test_config[current_phase]["success_criteria"]
            
            if not self.meet_criteria(metrics, criteria):
                # Rollback to FP32 for all users
                await self.rollback_quantization()
                send_alert("Quantization A/B test failed, rolled back", severity="critical")
                break
            
            # Progress to next phase if criteria met
            if self.should_progress_phase(metrics, current_phase):
                await self.progress_to_next_phase()
```

### Rollback Criteria

```python
ROLLBACK_TRIGGERS = {
    "quality_complaints": 0.02,  # 2% of users complain
    "skip_rate_increase": 0.01,  # 1% increase in skip rate
    "player_satisfaction_drop": 0.1,  # 0.1 point drop (on 1-5 scale)
    "toxicity_increase": 0.05,  # 5% increase in toxicity
}

async def should_rollback(self, metrics: Dict) -> bool:
    """Check if quantization should be rolled back"""
    for metric, threshold in ROLLBACK_TRIGGERS.items():
        if metrics[metric] > threshold:
            return True
    return False

async def rollback_quantization(self):
    """Rollback all users to FP32"""
    await self.redis.set("quantization_enabled", "false")
    await self.redis.delete("ab_test_config")
    
    # Notify all services
    await self.publish_event({
        "type": "quantization_rollback",
        "reason": "quality_threshold_exceeded"
    })
```

---

## MODEL-SPECIFIC QUANTIZATION COMPATIBILITY

### Tested Models

| Model | FP32 → INT8 | FP32 → BF16 | Notes |
|-------|-------------|-------------|-------|
| **Llama-3.1-8B** | ✅ Compatible | ✅ Compatible | Excellent quantization support |
| **Mistral-7B** | ✅ Compatible | ✅ Compatible | Good quantization support |
| **Phi-3-mini** | ✅ Compatible | ⚠️ Not needed | Already optimized |
| **DeepSeek-R1** | ✅ Compatible | ✅ Compatible | Tested via Azure deployment |

### Quantization Framework

```python
# Use vLLM quantization
from vllm import LLM

# INT8 quantization
llm_int8 = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    quantization="awq",  # 8-bit quantization
    max_model_len=4096
)

# BF16 quantization (alternative)
llm_bf16 = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    dtype="bfloat16",  # Half precision
    max_model_len=4096
)

# Compare performance
async def benchmark_models(test_prompts: List[str]):
    results = []
    for prompt in test_prompts:
        # FP32 baseline
        start = time.time()
        response_fp32 = await llm_fp32.generate(prompt)
        latency_fp32 = time.time() - start
        
        # INT8
        start = time.time()
        response_int8 = await llm_int8.generate(prompt)
        latency_int8 = time.time() - start
        
        speedup = latency_fp32 / latency_int8
        
        results.append({
            "speedup": speedup,
            "quality_drop": self.compare_quality(response_fp32, response_int8)
        })
    
    avg_speedup = np.mean([r["speedup"] for r in results])
    avg_quality_drop = np.mean([r["quality_drop"] for r in results])
    
    return avg_speedup, avg_quality_drop
```

---

## CONTINUOUS MONITORING

### Quality Metrics Dashboard

```python
# Prometheus metrics
quality_drop = Gauge('quantization_quality_drop', 'Quality degradation', ['metric'])
player_satisfaction = Gauge('player_satisfaction_score', 'Satisfaction score', ['model_version'])
skip_rate = Gauge('dialogue_skip_rate', 'Skip rate', ['model_version'])

async def monitor_quality_continuously(self):
    """Continuous quality monitoring"""
    while True:
        await asyncio.sleep(3600)  # Every hour
        
        # Compare FP32 vs INT8 metrics
        fp32_metrics = await self.get_model_metrics("fp32")
        int8_metrics = await self.get_model_metrics("int8")
        
        # Track quality drop
        quality_drop.labels(metric="perplexity").set(
            int8_metrics.perplexity - fp32_metrics.perplexity
        )
        
        # Track player satisfaction
        player_satisfaction.labels(model_version="int8").set(
            int8_metrics.satisfaction_score
        )
        
        # Alert if thresholds exceeded
        if int8_metrics.satisfaction_score < 4.0:  # Below 4/5
            send_alert("Player satisfaction below threshold for INT8 model")
```

---

**Status**: Complete quality assurance framework for quantization

