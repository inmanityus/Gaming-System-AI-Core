# Model Training Requirements - SRL→RLVR System
**Project**: "The Body Broker" - AI-Driven Horror Game  
**Last Updated**: 2025-01-29  
**Status**: NEW REQUIREMENTS - Must Replace All Existing Training Approaches
**Location**: docs/requirements/ subfolder

---

## 🚨 CRITICAL REQUIREMENTS - ALL MANDATORY

### Core Principle
**ALL model training MUST use the SRL→RLVR training solution. NO exceptions. NO alternative training methods.**

### Immediate Actions Required
1. **Audit**: Find and identify ALL existing training/fine-tuning tasks
2. **Scrap**: Any models that have been "fine-tuned" using incorrect methods must be scrapped and re-trained
3. **Switch**: ALL untrained models must use the SRL→RLVR solution
4. **Replace**: Any training tasks using old methods must be replaced with new SRL→RLVR tasks

---

## 1. COMPREHENSIVE MODEL TYPE REQUIREMENTS

The SRL→RLVR solution MUST properly train models for EVERY specific role in the game:

### 1.1 Personality Models
**Training Requirements:**
- **Emotions**: Understand and generate appropriate emotional responses
- **Expressions**: Facial expression mapping based on emotions
- **Actions**: Personality-driven action selection
- **Inherent Traits**: Core personality characteristics (aggression, intelligence, charisma, survival instincts, faction loyalty, personal goals)
- **Dynamic Adaptation**: Adjust behavior based on player interactions

**Training Data Sources:**
- Monster species lore
- Character stat definitions
- Behavioral pattern examples
- Historical interaction logs

### 1.2 Facial Expression Models
**Training Requirements:**
- **Emotion Mapping**: Map emotions to facial expressions
- **Body Language Integration**: Coordinate with body language systems
- **Context Awareness**: Expressions must match dialogue and actions
- **Personality Variation**: Different personalities show emotions differently

**Training Data Sources:**
- Facial expression libraries
- Emotion-action correlation data
- Personality-expression mapping
- Game-specific expression requirements

### 1.3 Building Generation Models
**Training Requirements:**
- **Exterior Generation**: Buildings, streets, city layouts
- **Interior Generation**: Apartments, morgues, labs
- **Architectural Styles**: Consistent with game world aesthetic
- **Day/Night Variations**: Different interiors for day vs. night worlds
- **Environmental Storytelling**: Buildings tell stories through design

**Training Data Sources:**
- Architectural style guides
- Building type specifications
- City layout patterns
- Environmental storytelling requirements

### 1.4 Animal Models
**Training Requirements:**
- **Behavior Patterns**: Natural animal behaviors (bears, mountain lions, sharks, etc.)
- **Day vs. Night**: Different animals in different worlds
- **Terrain-Specific**: Animals appropriate to geography (mountains, ocean, plains)
- **Interaction Logic**: How animals interact with player and monsters

**Training Data Sources:**
- Animal behavior databases
- Terrain-specific animal lists
- Game world context
- Interaction scenario examples

### 1.5 Plant Models
**Training Requirements:**
- **Flora Generation**: Plants appropriate to terrain and season
- **Ecosystem Integration**: Plants work within biome systems
- **Seasonal Variations**: Plants change with seasons (Fall colors, Winter bare, Spring growth, Summer full)
- **Environmental Impact**: Plants affect gameplay (cover, resources, atmosphere)

**Training Data Sources:**
- Flora databases by biome
- Seasonal variation data
- Ecosystem interaction patterns
- Game-specific plant requirements

### 1.6 Tree Models
**Training Requirements:**
- **Tree Generation**: Appropriate to terrain and season
- **Environmental Sounds**: Trees make sounds (groan in wind, etc.)
- **Visual Impact**: Trees contribute to atmosphere
- **Gameplay Elements**: Trees as cover, landmarks, resources

**Training Data Sources:**
- Tree species databases
- Seasonal variation data
- Sound effect requirements
- Gameplay integration needs

### 1.7 Sound Models
**Training Requirements:**
- **Building Sounds**: Creaks, rumbles, mechanical sounds
- **Animal Sounds**: All animal vocalizations (cats meow, etc.)
- **Environmental Sounds**: Trees groaning, wind, water
- **Vehicle Sounds**: Cars rumbling, sirens
- **Background Ambience**: Insects, distant conversations, plates clinking
- **Music Generation**: Eerie tracks, high energy, jump scare emphasis, contextual music

**Training Data Sources:**
- Sound effect libraries
- Music style guides
- Environmental sound requirements
- Game-specific audio needs

---

## 2. DYNAMIC TRAINING REQUIREMENTS

### 2.1 Never Static Examples
**CRITICAL**: Training examples must NEVER be static.

**Requirements:**
- **Continuous Improvement**: Each training run must look for new and better ways to create examples
- **Technology Advancement**: As technology grows, training capabilities must grow
- **Problem Evolution**: Training must adapt to new problem types and scenarios
- **Innovation**: Always seek novel approaches to example generation

**Implementation:**
- Three-model collaboration continuously improves example generation methods
- Research new training techniques as they emerge
- Experiment with different example formats and structures
- Analyze training effectiveness and iterate

### 2.2 Dynamic Rules Integration
**Requirements:**
- **Versioned Rules**: Training must use current dynamic rules version
- **Rule Updates**: When rules update, models must be re-trained with new rules
- **Rule Compliance**: All training examples must comply with current rules
- **Rule Evolution**: Training system must handle rule changes gracefully

---

## 3. MODEL SELECTION SYSTEM REQUIREMENTS

### 3.1 Dynamic Model Selection
**CRITICAL**: Model selection must be based on responsibilities and best viable self-hosted model for that job.

**Requirements:**
- **Responsibility-Based**: Model selection determined by task requirements (personality, facial, building, etc.)
- **Best Fit**: Always select the best available model for specific tasks
- **Not Arbitrary**: Selection must be data-driven, not arbitrary or static
- **Performance-Based**: Selection based on benchmarks and testing, not assumptions

### 3.2 Cost-Benefit Analysis
**Requirements:**
- **New Model Evaluation**: When new models are released, perform cost-benefit analysis
- **Replacement Criteria**: Determine if new model warrants replacement of existing
- **Training Cost**: Account for training costs in replacement decision
- **Performance Gain**: Measure actual performance improvements, not just claims
- **Swap Process**: Trained new models must be swapped in when warranted

**Analysis Criteria:**
- Performance benchmarks (relevant to task)
- Resource requirements (VRAM, compute)
- Training time and cost
- Inference latency
- Quality metrics
- Cost per inference

### 3.3 Continuous Model Evaluation
**Requirements:**
- **Regular Reviews**: Periodically evaluate all models for improvements
- **Benchmark Updates**: Update benchmarks as game evolves
- **Task-Specific Metrics**: Different metrics for different model types
- **Automated Evaluation**: System must automatically evaluate models

---

## 4. PAID MODEL FINE-TUNING REQUIREMENTS

### 4.1 Supported Providers
**Requirements:**
- **Gemini**: Fine-tuning support through Google Cloud
- **ChatGPT**: Fine-tuning through OpenAI API
- **Anthropic Claude**: Fine-tuning through Anthropic API (when available)
- **Other Providers**: Monitor and support new fine-tuning offerings

### 4.2 Fine-Tuning Strategy
**Requirements:**
- **Always Evaluate**: Always look for fine-tuning opportunities
- **Cost-Benefit**: Evaluate fine-tuning cost vs. prompt engineering effectiveness
- **Task-Specific**: Fine-tune for specific high-value tasks
- **Quality Improvement**: Fine-tuning must provide measurable quality improvement

### 4.3 Integration with Training System
**Requirements:**
- **SRL→RLVR**: Use SRL→RLVR approach for paid model fine-tuning where applicable
- **Data Consistency**: Use same training data quality standards
- **Validation**: Validate fine-tuned models with same rigor as self-hosted models
- **Rollback**: Support rollback of fine-tuned models if issues detected

### 4.4 Prompt Engineering Fallback
**Requirements:**
- **When Fine-Tuning Unavailable**: Use prompt engineering when fine-tuning not available
- **Optimization**: Continuously optimize prompts for best results
- **Template Management**: Maintain prompt templates for different tasks
- **A/B Testing**: Test different prompt strategies

---

## 5. MODEL PERFORMANCE TRACKING REQUIREMENTS

### 5.1 Performance Metrics
**Requirements:**
- **Latency Tracking**: Track inference latency (p50, p95, p99)
- **Quality Metrics**: Track output quality (task-specific metrics)
- **Error Rates**: Track error and failure rates
- **Resource Usage**: Track VRAM, compute, memory usage
- **Cost Tracking**: Track cost per inference for paid models

### 5.2 Weakness Detection
**Requirements:**
- **Continuous Monitoring**: Monitor all models continuously
- **Anomaly Detection**: Detect performance degradation or quality issues
- **Trend Analysis**: Identify trends indicating weakness
- **Alert System**: Alert when weakness detected
- **Prevention**: Replace models BEFORE weaknesses become game issues

### 5.3 Multi-Model Evaluation System
**Requirements:**
- **Three-Model Collaboration**: Use three models to determine evaluation criteria
- **Benchmark Selection**: Models determine which benchmarks are relevant
- **Research Integration**: Research model strengths and weaknesses
- **Testing**: Test models to verify performance claims
- **Decision Making**: Models help make replacement decisions

### 5.4 Performance History
**Requirements:**
- **Historical Tracking**: Track performance over time
- **Comparison**: Compare current vs. historical performance
- **Regression Detection**: Detect performance regressions
- **Improvement Tracking**: Track improvements from training

---

## 6. INTEGRATION REQUIREMENTS

### 6.1 AWS Deployment
**Requirements:**
- **All Training in AWS**: All model training must run in AWS (local dev computer cannot handle model inference)
- **SageMaker Integration**: Use AWS SageMaker for training
- **Step Functions**: Use AWS Step Functions for workflow orchestration
- **ECR**: Use AWS ECR for container registry
- **S3**: Use AWS S3 for data storage
- **DynamoDB**: Use AWS DynamoDB for metadata
- **CloudWatch**: Use AWS CloudWatch for monitoring

### 6.2 Existing System Integration
**Requirements:**
- **Model Management System**: Integrate with existing model management
- **AI Inference Service**: Models must work with inference service
- **Orchestration Service**: Models must integrate with orchestration
- **State Management**: Models must integrate with game state

### 6.3 Testing Integration
**Requirements:**
- **Comprehensive Testing**: Rigorous testing throughout (cutting edge, no safety net)
- **Integration Testing**: Test integration with all systems
- **Performance Testing**: Test performance under load
- **Quality Testing**: Test output quality

---

## 7. SUCCESS CRITERIA

### 7.1 Training Success
- ✅ All model types successfully trained using SRL→RLVR
- ✅ Training examples continuously improve
- ✅ Models meet performance requirements
- ✅ Models meet quality requirements

### 7.2 Model Selection Success
- ✅ Dynamic selection based on responsibilities
- ✅ Cost-benefit analysis performed for new models
- ✅ Models replaced when warranted
- ✅ Selection not arbitrary or static

### 7.3 Paid Model Success
- ✅ Fine-tuning opportunities identified and evaluated
- ✅ Fine-tuned models provide quality improvements
- ✅ Prompt engineering optimized when fine-tuning unavailable

### 7.4 Performance Tracking Success
- ✅ All models continuously monitored
- ✅ Weaknesses detected before becoming issues
- ✅ Models replaced proactively
- ✅ Performance history maintained

---

## 8. MANDATORY ENFORCEMENT

### 8.1 No Exceptions
**CRITICAL**: There are NO exceptions to these requirements.

- ❌ NO training using old methods
- ❌ NO static examples
- ❌ NO arbitrary model selection
- ❌ NO ignoring paid model fine-tuning opportunities
- ❌ NO skipping performance tracking

### 8.2 All Rules Apply
**CRITICAL**: All rules in `/all-rules` must be followed, including:
- Peer-based coding for all implementation
- Pairwise testing for all tests
- Three-AI review for all solutions
- Comprehensive testing after every task
- Memory consolidation after every task
- 45-minute milestones
- Timer service running
- Work visibility in real-time
- Automatic continuation

---

**END OF MODEL TRAINING REQUIREMENTS**

