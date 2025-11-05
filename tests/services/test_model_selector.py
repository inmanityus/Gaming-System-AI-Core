"""
Real tests for Dynamic Model Selector.
Created via pairwise testing protocol.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.srl_rlvr_training.dynamic.model_selector import (
    DynamicModelSelector,
    ModelCandidate
)


class TestDynamicModelSelector:
    """Real tests for model selector."""
    
    def test_initialization(self):
        """Test selector initialization."""
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        assert selector.benchmark_db_url == "http://test:8080"
        assert selector.model_registry == {}
        assert selector.selection_history == []
    
    def test_initialization_with_registry_url(self):
        """Test initialization with separate registry URL."""
        selector = DynamicModelSelector(
            benchmark_db_url="http://benchmark:8080",
            model_registry_url="http://registry:8080"
        )
        assert selector.benchmark_db_url == "http://benchmark:8080"
        assert selector.model_registry_url == "http://registry:8080"
    
    @patch('services.srl_rlvr_training.dynamic.model_selector.HTTPX_AVAILABLE', True)
    @patch('services.srl_rlvr_training.dynamic.model_selector.httpx')
    def test_get_candidates_with_api(self, mock_httpx):
        """Test getting candidates via API."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {
                    "model_id": "model1",
                    "model_type": "personality",
                    "capability_score": 0.8,
                    "cost_per_token": 0.001,
                    "latency_ms": 50.0
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client
        
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        selector.http_client = mock_client
        
        # Mock benchmark scores
        selector._get_benchmark_scores = Mock(return_value={"accuracy": 0.9})
        
        candidates = selector._get_candidates(
            model_type="personality",
            task_responsibilities={"required_capabilities": {"speed": 0.7}}
        )
        
        assert len(candidates) > 0
        assert isinstance(candidates[0], ModelCandidate)
        assert candidates[0].model_id == "model1"
    
    def test_get_candidates_with_cached_registry(self):
        """Test getting candidates from cached registry."""
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        selector.http_client = None
        
        # Add candidate to registry
        candidate = ModelCandidate(
            model_id="cached_model",
            model_type="personality",
            capability_score=0.7,
            cost_per_token=0.001,
            latency_ms=100.0,
            responsibility_match=0.8,
            benchmark_scores={"accuracy": 0.85}
        )
        selector.model_registry["cached_model"] = candidate
        
        candidates = selector._get_candidates(
            model_type="personality",
            task_responsibilities={"required_capabilities": {}}
        )
        
        assert len(candidates) > 0
        assert candidates[0].model_id == "cached_model"
    
    def test_get_candidates_with_default_models(self):
        """Test getting candidates with default models fallback."""
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        selector.http_client = None
        
        candidates = selector._get_candidates(
            model_type="personality",
            task_responsibilities={}
        )
        
        # Should have at least one default candidate
        assert len(candidates) > 0
        assert candidates[0].model_type == "personality"
    
    def test_calculate_responsibility_match(self):
        """Test responsibility match calculation."""
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        
        model_data = {
            "model_type": "personality",
            "capabilities": {
                "speed": 0.8,
                "accuracy": 0.9
            }
        }
        
        task_responsibilities = {
            "required_capabilities": {
                "speed": 0.7,
                "accuracy": 0.8
            },
            "model_type": "personality"
        }
        
        match_score = selector._calculate_responsibility_match(model_data, task_responsibilities)
        
        assert 0.0 <= match_score <= 1.0
        assert match_score > 0.5  # Should match well
    
    def test_calculate_responsibility_match_no_requirements(self):
        """Test responsibility match with no requirements."""
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        
        model_data = {"model_type": "personality"}
        task_responsibilities = {}
        
        match_score = selector._calculate_responsibility_match(model_data, task_responsibilities)
        
        assert match_score == 0.7  # Default match
    
    def test_filter_by_budget(self):
        """Test filtering candidates by budget."""
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        
        candidates = [
            ModelCandidate(
                model_id="cheap",
                model_type="test",
                capability_score=0.7,
                cost_per_token=0.0005,
                latency_ms=50.0,
                responsibility_match=0.8,
                benchmark_scores={}
            ),
            ModelCandidate(
                model_id="expensive",
                model_type="test",
                capability_score=0.9,
                cost_per_token=0.01,
                latency_ms=200.0,
                responsibility_match=0.9,
                benchmark_scores={}
            )
        ]
        
        budget_constraints = {
            "max_cost_per_token": 0.001,
            "max_latency_ms": 100.0
        }
        
        filtered = selector._filter_by_budget(candidates, budget_constraints)
        
        assert len(filtered) == 1
        assert filtered[0].model_id == "cheap"
    
    def test_select_model(self):
        """Test model selection."""
        selector = DynamicModelSelector(benchmark_db_url="http://test:8080")
        
        # Mock _get_candidates to return test candidates
        test_candidates = [
            ModelCandidate(
                model_id="model1",
                model_type="personality",
                capability_score=0.8,
                cost_per_token=0.001,
                latency_ms=50.0,
                responsibility_match=0.9,
                benchmark_scores={}
            ),
            ModelCandidate(
                model_id="model2",
                model_type="personality",
                capability_score=0.7,
                cost_per_token=0.0005,
                latency_ms=40.0,
                responsibility_match=0.8,
                benchmark_scores={}
            )
        ]
        
        selector._get_candidates = Mock(return_value=test_candidates)
        
        selected = selector.select_model(
            task_responsibilities={"required_capabilities": {}},
            model_type="personality"
        )
        
        assert selected is not None
        assert selected in ["model1", "model2"]
        assert len(selector.selection_history) > 0

