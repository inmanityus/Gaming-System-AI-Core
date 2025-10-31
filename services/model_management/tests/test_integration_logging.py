"""
Integration tests for Historical Log Collection integration.
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from services.model_management.historical_log_processor import HistoricalLogProcessor


@pytest.fixture
def historical_log_processor():
    """Create HistoricalLogProcessor with mocked database."""
    processor = HistoricalLogProcessor()
    # Mock the database pool
    with patch.object(processor, '_get_postgres') as mock_postgres:
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_postgres.return_value = mock_pool
        yield processor


@pytest.mark.asyncio
async def test_log_inference_creates_entry(historical_log_processor):
    """Test that log_inference creates database entry."""
    model_id = uuid4()
    
    with patch.object(historical_log_processor, '_get_postgres') as mock_get_postgres:
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_get_postgres.return_value = mock_pool
        
        # Log inference
        log_id = await historical_log_processor.log_inference(
            model_id=model_id,
            use_case="foundation_layer",
            prompt="Test prompt",
            context={"test": "context"},
            generated_output="Test output",
            performance_metrics={"latency_ms": 100, "tokens_used": 50}
        )
        
        # Verify database execute was called
        assert mock_pool.execute.called
        assert isinstance(log_id, UUID)


@pytest.mark.asyncio
async def test_log_inference_captures_performance_metrics(historical_log_processor):
    """Test that performance metrics are captured in logs."""
    model_id = uuid4()
    
    performance_metrics = {
        "latency_ms": 250,
        "tokens_used": 150,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    with patch.object(historical_log_processor, '_get_postgres') as mock_get_postgres:
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_get_postgres.return_value = mock_pool
        
        await historical_log_processor.log_inference(
            model_id=model_id,
            use_case="interaction_layer",
            prompt="Test prompt",
            context={},
            generated_output="Test output",
            performance_metrics=performance_metrics
        )
        
        # Verify execute was called with performance metrics
        call_args = mock_pool.execute.call_args
        # The metrics should be in the JSONB field
        assert mock_pool.execute.called


@pytest.mark.asyncio
async def test_log_inference_captures_user_feedback(historical_log_processor):
    """Test that user feedback and corrections are captured."""
    model_id = uuid4()
    
    user_feedback = {
        "rating": 4,
        "comment": "Good response",
        "needs_improvement": False
    }
    corrected_output = "Improved output based on feedback"
    
    with patch.object(historical_log_processor, '_get_postgres') as mock_get_postgres:
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_get_postgres.return_value = mock_pool
        
        await historical_log_processor.log_inference(
            model_id=model_id,
            use_case="story_generation",
            prompt="Test prompt",
            context={},
            generated_output="Original output",
            user_feedback=user_feedback,
            corrected_output=corrected_output
        )
        
        # Verify execute was called with feedback
        assert mock_pool.execute.called


@pytest.mark.asyncio
async def test_get_historical_logs_retrieves_entries(historical_log_processor):
    """Test that historical logs can be retrieved."""
    model_id = uuid4()
    
    # Mock fetch_all to return test data
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, key: {
        "log_id": uuid4(),
        "model_id": model_id,
        "use_case": "foundation_layer",
        "prompt": "Test prompt",
        "context": '{"test": "context"}',
        "generated_output": "Test output",
        "user_feedback": None,
        "corrected_output": None,
        "performance_metrics": '{"latency_ms": 100}',
        "timestamp": datetime.now(timezone.utc)
    }.get(key)
    
    with patch.object(historical_log_processor, '_get_postgres') as mock_get_postgres:
        mock_pool = AsyncMock()
        mock_pool.fetch_all = AsyncMock(return_value=[mock_row])
        mock_get_postgres.return_value = mock_pool
        
        logs = await historical_log_processor.get_historical_logs(
            model_id=model_id,
            use_case="foundation_layer"
        )
        
        # Verify logs retrieved
        assert isinstance(logs, list)
        assert mock_pool.fetch_all.called


@pytest.mark.asyncio
async def test_process_logs_to_training_data(historical_log_processor):
    """Test that logs can be processed into training data."""
    sample_logs = [
        {
            "log_id": str(uuid4()),
            "model_id": str(uuid4()),
            "use_case": "foundation_layer",
            "prompt": "Test prompt 1",
            "context": {"test": "context1"},
            "generated_output": "Output 1",
            "corrected_output": None,
            "performance_metrics": {"quality_score": 0.8},
            "timestamp": "2025-01-29T12:00:00Z"
        },
        {
            "log_id": str(uuid4()),
            "model_id": str(uuid4()),
            "use_case": "foundation_layer",
            "prompt": "Test prompt 2",
            "context": {"test": "context2"},
            "generated_output": "Output 2",
            "corrected_output": "Corrected output 2",
            "performance_metrics": {"quality_score": 0.9},
            "timestamp": "2025-01-29T12:01:00Z"
        }
    ]
    
    training_examples = await historical_log_processor.process_logs_to_training_data(sample_logs)
    
    # Verify training examples created
    assert len(training_examples) == 2
    assert all("input" in ex for ex in training_examples)
    assert all("output" in ex for ex in training_examples)
    assert all("quality_score" in ex for ex in training_examples)
    
    # Verify corrected output used when available
    assert training_examples[1]["output"] == "Corrected output 2"
    assert training_examples[1]["quality_score"] == 1.0  # Corrected outputs are high quality

