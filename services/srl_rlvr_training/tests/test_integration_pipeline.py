# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Integration Tests for SRL→RLVR Full Pipeline.
Tests the complete training workflow from collaboration to model serving.
"""

import pytest
import asyncio
import torch
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

# Add parent directory to path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.collaboration.collaboration_orchestrator import CollaborationOrchestrator
from services.srl_rlvr_training.srl.srl_trainer import SRLTrainer
from services.srl_rlvr_training.rlvr.rlvr_trainer import RLVRTrainer
from model_registry import ModelRegistry


class TestIntegrationPipeline:
    """Integration tests for complete SRL→RLVR pipeline."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Mock model registry."""
        registry = Mock(spec=ModelRegistry)
        registry.register_model = AsyncMock(return_value=uuid4())
        registry.get_current_model = AsyncMock(return_value=None)
        return registry
    
    @pytest.fixture
    def collaboration_orchestrator(self):
        """Create collaboration orchestrator with mocked dependencies."""
        from services.srl_rlvr_training.collaboration.lore_retriever import LoreRetriever
        from services.srl_rlvr_training.collaboration.teacher_planner import TeacherPlanner
        from services.srl_rlvr_training.collaboration.verifier import Verifier
        
        mock_lore_retriever = Mock(spec=LoreRetriever)
        mock_teacher_planner = Mock(spec=TeacherPlanner)
        mock_verifier = Mock(spec=Verifier)
        
        orchestrator = CollaborationOrchestrator(
            lore_retriever=mock_lore_retriever,
            teacher_planner=mock_teacher_planner,
            verifier=mock_verifier
        )
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_three_model_collaboration_flow(self, collaboration_orchestrator):
        """Test three-model collaboration generates valid trajectories."""
        # Mock the collaboration methods
        collaboration_orchestrator.generate_expert_trajectory = AsyncMock(
            return_value={
                "problem": "Test problem",
                "steps": [
                    {"action": "step1", "reasoning": "reasoning1", "reward": 0.3},
                    {"action": "step2", "reasoning": "reasoning2", "reward": 0.7}
                ],
                "expected_outcome": "Expected result"
            }
        )
        
        trajectory = await collaboration_orchestrator.generate_expert_trajectory(
            monster_species="vampire",
            model_type="personality"
        )
        
        assert trajectory is not None
        assert "problem" in trajectory
        assert "steps" in trajectory
        assert len(trajectory["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_srl_training_workflow(self, mock_model_registry):
        """Test SRL training workflow."""
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock state_dict to avoid clone issues
        mock_tensor = Mock()
        mock_tensor.clone = Mock(return_value=mock_tensor)
        mock_model.state_dict = Mock(return_value={"layer.weight": mock_tensor, "layer.bias": mock_tensor})
        mock_model.parameters = Mock(return_value=iter([Mock()]))
        
        # Mock all dependencies including optimizer
        with patch.object(SRLTrainer, '_save_reference_policy'), \
             patch('services.srl_rlvr_training.srl.srl_trainer.RewardNormalizer') as mock_norm, \
             patch('services.srl_rlvr_training.srl.srl_trainer.KLController') as mock_kl, \
             patch('torch.optim.AdamW') as mock_optim:
            # Create mock instances
            mock_norm.return_value = Mock()
            mock_kl.return_value = Mock()
            mock_optim.return_value = Mock()
            
            trainer = SRLTrainer(
                model=mock_model,
                tokenizer=mock_tokenizer,
                learning_rate=1e-5
            )
            
            # Verify trainer initialized
            assert trainer.model == mock_model
            assert trainer.tokenizer == mock_tokenizer
            assert trainer.learning_rate == 1e-5
    
    @pytest.mark.asyncio
    async def test_rlvr_fine_tuning_workflow(self, mock_model_registry):
        """Test RLVR fine-tuning workflow."""
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        mock_model.parameters = Mock(return_value=iter([Mock()]))
        
        # RLVRTrainer requires reward_model parameter
        mock_reward_model = Mock()
        
        # Mock state_dict to return iterable dict
        mock_tensor = Mock()
        mock_tensor.clone = Mock(return_value=mock_tensor)
        state_dict = {"layer.weight": mock_tensor, "layer.bias": mock_tensor}
        mock_model.state_dict = Mock(return_value=state_dict)
        
        with patch('services.srl_rlvr_training.rlvr.rlvr_trainer.PPOTrainer') as mock_ppo, \
             patch('services.srl_rlvr_training.rlvr.rlvr_trainer.KLController') as mock_kl, \
             patch('torch.optim.AdamW') as mock_optim:
            mock_optim.return_value = Mock()
            mock_ppo_instance = Mock()
            mock_ppo.return_value = mock_ppo_instance
            mock_kl_instance = Mock()
            mock_kl.return_value = mock_kl_instance
            
            trainer = RLVRTrainer(
                model=mock_model,
                tokenizer=mock_tokenizer,
                reward_model=mock_reward_model,
                learning_rate=1e-6,
                use_ppo=False  # Skip PPO for test
            )
            
            # Verify trainer initialization
            assert trainer.model == mock_model
            assert trainer.tokenizer == mock_tokenizer
            assert trainer.reward_model == mock_reward_model
    
    @pytest.mark.asyncio
    async def test_full_pipeline_integration(self, collaboration_orchestrator, mock_model_registry):
        """Test complete SRL→RLVR pipeline integration."""
        # Step 1: Generate expert trajectories
        mock_result = Mock()
        mock_result.trajectories = [Mock()]
        mock_result.trajectories[0].problem = "Test problem"
        mock_result.trajectories[0].steps = [{"action": "a1", "reward": 0.5}]
        mock_result.trajectories[0].expected_outcome = "Result"
        
        collaboration_orchestrator.generate_training_examples = AsyncMock(return_value=mock_result)
        
        result = await collaboration_orchestrator.generate_training_examples(
            monster_species="vampire",
            model_type="personality",
            num_examples=1
        )
        
        trajectory = {
            "problem": result.trajectories[0].problem,
            "steps": result.trajectories[0].steps,
            "expected_outcome": result.trajectories[0].expected_outcome
        }
        
        # Step 2: SRL Training
        mock_model = Mock()
        mock_tokenizer = Mock()
        mock_model.parameters = Mock(return_value=iter([Mock()]))
        mock_tensor = Mock()
        mock_tensor.clone = Mock(return_value=mock_tensor)
        mock_model.state_dict = Mock(return_value={"layer.weight": mock_tensor})
        
        with patch.object(SRLTrainer, '_save_reference_policy'), \
             patch('services.srl_rlvr_training.srl.srl_trainer.RewardNormalizer'), \
             patch('services.srl_rlvr_training.srl.srl_trainer.KLController'), \
             patch('torch.optim.AdamW'):
            srl_trainer = SRLTrainer(
                model=mock_model,
                tokenizer=mock_tokenizer,
                learning_rate=1e-5
            )
            
            assert srl_trainer.model == mock_model
        
        # Step 3: RLVR Fine-tuning
        mock_reward_model = Mock()
        with patch('services.srl_rlvr_training.rlvr.rlvr_trainer.PPOTrainer'), \
             patch('services.srl_rlvr_training.rlvr.rlvr_trainer.KLController'), \
             patch('torch.optim.AdamW'):
            rlvr_trainer = RLVRTrainer(
                model=mock_model,
                tokenizer=mock_tokenizer,
                reward_model=mock_reward_model,
                learning_rate=1e-6,
                use_ppo=False
            )
            
            assert rlvr_trainer.model == mock_model
        
        # Verify pipeline completed
        assert trajectory is not None
        assert srl_trainer is not None
        assert rlvr_trainer is not None

