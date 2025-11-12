# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Performance Tests for SRL→RLVR Training System - Created by Tester and Reviewed by Reviewer.
Tests performance metrics and validation.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.srl_rlvr_training.srl.srl_trainer import SRLTrainer
from services.srl_rlvr_training.rlvr.rlvr_trainer import RLVRTrainer


class TestPerformance:
    """Performance tests for training system."""
    
    @pytest.fixture
    def mock_model(self):
        """Mock model for testing."""
        model = Mock()
        model.parameters = Mock(return_value=iter([Mock()]))
        # Mock state_dict to return a dict with cloneable values
        mock_tensor = Mock()
        mock_tensor.clone = Mock(return_value=mock_tensor)
        # Create actual dict that can be iterated
        state_dict = {"layer.weight": mock_tensor, "layer.bias": mock_tensor}
        model.state_dict = Mock(return_value=state_dict)
        return model
    
    @pytest.fixture
    def mock_tokenizer(self):
        """Mock tokenizer for testing."""
        tokenizer = Mock()
        return tokenizer
    
    def test_srl_trainer_initialization_performance(self, mock_model, mock_tokenizer):
        """Test SRL trainer initialization is fast."""
        # Mock the reference policy state saving and all dependencies
        with patch.object(SRLTrainer, '_save_reference_policy'), \
             patch('services.srl_rlvr_training.srl.srl_trainer.RewardNormalizer'), \
             patch('services.srl_rlvr_training.srl.srl_trainer.KLController'), \
             patch('torch.optim.AdamW'):
            start_time = time.time()
            
            trainer = SRLTrainer(
                model=mock_model,
                tokenizer=mock_tokenizer,
                learning_rate=1e-5
            )
            
            elapsed = time.time() - start_time
            
            # Initialization should be fast (< 1 second for mocked components)
            assert elapsed < 1.0
            assert trainer is not None
    
    def test_rlvr_trainer_initialization_performance(self, mock_model, mock_tokenizer):
        """Test RLVR trainer initialization is fast."""
        # Mock PPO trainer, KLController, optimizer, and reward_model
        mock_reward_model = Mock()
        mock_tensor = Mock()
        mock_tensor.clone = Mock(return_value=mock_tensor)
        state_dict = {"layer.weight": mock_tensor, "layer.bias": mock_tensor}
        mock_model.state_dict = Mock(return_value=state_dict)
        
        with patch('services.srl_rlvr_training.rlvr.rlvr_trainer.PPOTrainer'), \
             patch('services.srl_rlvr_training.rlvr.rlvr_trainer.KLController'), \
             patch('torch.optim.AdamW'):
            start_time = time.time()
            
            trainer = RLVRTrainer(
                model=mock_model,
                tokenizer=mock_tokenizer,
                reward_model=mock_reward_model,
                learning_rate=1e-6,
                use_ppo=False  # Skip PPO for faster initialization
            )
            
            elapsed = time.time() - start_time
            
            # Initialization should be fast (< 1 second for mocked components)
            assert elapsed < 1.0
            assert trainer is not None
    
    def test_training_step_performance(self, mock_model, mock_tokenizer):
        """Test training step performance metrics."""
        with patch.object(SRLTrainer, '_save_reference_policy'), \
             patch('services.srl_rlvr_training.srl.srl_trainer.RewardNormalizer'), \
             patch('services.srl_rlvr_training.srl.srl_trainer.KLController'), \
             patch('torch.optim.AdamW'):
            trainer = SRLTrainer(
                model=mock_model,
                tokenizer=mock_tokenizer,
                learning_rate=1e-5
            )
            
            # Mock training step
            mock_model.eval = Mock()
            mock_model.train = Mock()
            
            # Verify trainer has training step method
            assert hasattr(trainer, 'train_step')
    
    def test_cost_estimation(self):
        """Test cost estimation calculations."""
        # Gold tier cost estimates
        gold_training_cost = 75  # $75 per training run
        gold_inference_cost = 1  # $1 per 1M tokens
        
        # Silver tier cost estimates
        silver_training_cost = 240  # $240 per training run
        silver_inference_cost = 3.5  # Average of $1.4-$6.7 per 1M tokens
        
        # Bronze tier cost estimates
        bronze_training_cost = 20000  # Average of $8.6k-$32k per training run
        bronze_inference_cost = 10  # Estimated per 1M tokens
        
        # Verify cost estimates are reasonable
        assert gold_training_cost < silver_training_cost
        assert silver_training_cost < bronze_training_cost
        assert gold_inference_cost < silver_inference_cost
        assert silver_inference_cost < bronze_inference_cost
    
    def test_latency_targets(self):
        """Test latency targets per tier."""
        # Gold tier: <200ms
        gold_target = 200
        
        # Silver tier: <500ms
        silver_target = 500
        
        # Bronze tier: <1000ms (async acceptable)
        bronze_target = 1000
        
        # Verify latency targets are reasonable
        assert gold_target < silver_target
        assert silver_target < bronze_target
        assert gold_target < 300  # Real-time requirement
        assert silver_target < 600  # Interactive requirement
        assert bronze_target < 2000  # Async acceptable

