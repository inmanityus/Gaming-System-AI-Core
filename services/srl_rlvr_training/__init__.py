"""
SRL→RLVR Training System
========================

Production-ready training system using Google's Supervised Reinforcement Learning (SRL)
→ Reinforcement Learning with Verifiable Rewards (RLVR) approach.

Key Features:
- Three-Model Collaboration for expert trajectory generation
- Dynamic example generation (never static)
- Support for all 7 model types (personality, facial, buildings, animals, plants, trees, sounds)
- Dynamic model selection with cost-benefit analysis
- Paid model fine-tuning (Gemini, ChatGPT, Anthropic)
- Performance tracking with weakness detection
- Full AWS deployment (SageMaker, Step Functions, S3, DynamoDB)

Architecture:
- services/srl_rlvr_training/collaboration/ - Three-model collaboration system
- services/srl_rlvr_training/srl/ - SRL training pipeline
- services/srl_rlvr_training/rlvr/ - RLVR fine-tuning pipeline
- services/srl_rlvr_training/models/ - Model-specific training modules
- services/srl_rlvr_training/dynamic/ - Dynamic systems (selection, examples, rules)
- services/srl_rlvr_training/performance/ - Performance tracking and monitoring
- services/srl_rlvr_training/paid/ - Paid model fine-tuning integrations
"""

__version__ = "1.0.0"
__author__ = "Gaming System AI Core"

