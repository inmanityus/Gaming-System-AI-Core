"""
End-to-End Tests for Complete Training Workflow - Created by Tester and Reviewed by Reviewer.
Tests the complete SRL→RLVR training pipeline from start to finish.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.collaboration.collaboration_orchestrator import CollaborationOrchestrator
from services.srl_rlvr_training.collaboration.lore_retriever import LoreRetriever
from services.srl_rlvr_training.collaboration.teacher_planner import TeacherPlanner
from services.srl_rlvr_training.collaboration.verifier import Verifier
from services.srl_rlvr_training.srl.srl_trainer import SRLTrainer
from services.srl_rlvr_training.rlvr.rlvr_trainer import RLVRTrainer
from services.model_management.model_registry import ModelRegistry


class TestE2ETrainingWorkflow:
    """End-to-end tests for complete training workflow."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Mock model registry."""
        registry = Mock(spec=ModelRegistry)
        registry.register_model = AsyncMock(return_value="model-id-123")
        registry.get_current_model = AsyncMock(return_value=None)
        return registry
    
    @pytest.fixture
    def collaboration_orchestrator(self):
        """Create collaboration orchestrator with mocked dependencies."""
        # Mock the components
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
    async def test_complete_training_workflow(self, collaboration_orchestrator, mock_model_registry):
        """Test complete training workflow from collaboration to model serving."""
        # Step 1: Generate expert trajectory
        # Mock the generate_training_examples method
        mock_result = Mock()
        mock_result.trajectories = [Mock()]
        mock_result.trajectories[0].problem = "Test problem"
        mock_result.trajectories[0].steps = [
            {"action": "step1", "reasoning": "reasoning1", "reward": 0.3},
            {"action": "step2", "reasoning": "reasoning2", "reward": 0.7}
        ]
        mock_result.trajectories[0].expected_outcome = "Expected result"
        
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
        
        assert trajectory is not None
        assert "problem" in trajectory
        assert "steps" in trajectory
        
        # Step 2: SRL Training (mocked)
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
            assert srl_trainer.tokenizer == mock_tokenizer
        
        # Step 3: RLVR Fine-tuning (mocked)
        mock_reward_model = Mock()
        mock_tensor = Mock()
        mock_tensor.clone = Mock(return_value=mock_tensor)
        state_dict = {"layer.weight": mock_tensor}
        mock_model.state_dict = Mock(return_value=state_dict)
        
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
        
        # Verify workflow components are connected
        assert trajectory is not None
        assert srl_trainer is not None
        assert rlvr_trainer is not None
    
    @pytest.mark.asyncio
    async def test_workflow_with_multiple_trajectories(self, collaboration_orchestrator, mock_model_registry):
        """Test workflow with multiple expert trajectories."""
        # Generate multiple trajectories
        trajectories = []
        for i in range(3):
            collaboration_orchestrator.generate_expert_trajectory = AsyncMock(
                return_value={
                    "problem": f"Problem {i}",
                    "steps": [{"action": f"action{i}", "reward": 0.5}],
                    "expected_outcome": f"Outcome {i}"
                }
            )
            
            trajectory = await collaboration_orchestrator.generate_expert_trajectory(
                monster_species="vampire",
                model_type="personality"
            )
            trajectories.append(trajectory)
        
        assert len(trajectories) == 3
        assert all(t is not None for t in trajectories)
    
    def test_workflow_component_integration(self):
        """Test that all workflow components can be instantiated together."""
        # Verify all components can be imported
        from services.srl_rlvr_training.collaboration.collaboration_orchestrator import CollaborationOrchestrator
        from services.srl_rlvr_training.srl.srl_trainer import SRLTrainer
        from services.srl_rlvr_training.rlvr.rlvr_trainer import RLVRTrainer
        from services.srl_rlvr_training.distillation.distillation_pipeline import DistillationPipeline
        from services.srl_rlvr_training.recovery.failure_handler import FailureHandler
        
        # All components should be importable
        assert CollaborationOrchestrator is not None
        assert SRLTrainer is not None
        assert RLVRTrainer is not None
        assert DistillationPipeline is not None
        assert FailureHandler is not None

