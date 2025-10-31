"""
End-to-End workflow tests for Model Management System integrations.
Tests complete data flows from service to service.
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from services.ai_integration.llm_client import LLMClient
from services.ai_integration.service_coordinator import ServiceCoordinator
from services.story_teller.narrative_generator import NarrativeGenerator
from services.model_management.model_registry import ModelRegistry
from services.model_management.deployment_manager import DeploymentManager
from services.model_management.guardrails_monitor import GuardrailsMonitor


@pytest.fixture
def mock_model_registry():
    """Create mocked ModelRegistry."""
    registry = MagicMock()
    registry.get_current_model = AsyncMock(return_value={
        "model_id": str(uuid4()),
        "model_name": "test-model",
        "use_case": "foundation_layer",
        "configuration": {"endpoint": "http://localhost:8001/generate"}
    })
    return registry


@pytest.fixture
def mock_llm_client(mock_model_registry):
    """Create LLMClient with mocked registry."""
    client = LLMClient(model_registry=mock_model_registry)
    # Mock historical log processor
    with patch.object(client, 'historical_log_processor'):
        client.historical_log_processor.log_inference = AsyncMock(return_value=uuid4())
        yield client


@pytest.mark.asyncio
async def test_e2e_model_registry_to_inference_to_logs(mock_llm_client, mock_model_registry):
    """Test complete workflow: Model Registry → AI Inference → Historical Logs."""
    # Setup: Model in registry
    model_id = str(uuid4())
    mock_model_registry.get_current_model.return_value = {
        "model_id": model_id,
        "use_case": "foundation_layer",
        "configuration": {"endpoint": "http://localhost:8001/generate"}
    }
    
    # Mock LLM service response
    with patch.object(mock_llm_client, '_make_request') as mock_request:
        mock_request.return_value = {
            "text": "Generated response",
            "tokens_used": 150
        }
        
        # Execute: Generate text (should trigger registry lookup and logging)
        result = await mock_llm_client.generate_text(
            layer="foundation",
            prompt="Test prompt",
            context={"test": "context"},
            max_tokens=1000,
            temperature=0.7
        )
        
        # Verify: Model was retrieved from registry
        assert mock_model_registry.get_current_model.called
        
        # Verify: Historical log was created
        assert mock_llm_client.historical_log_processor.log_inference.called
        log_call = mock_llm_client.historical_log_processor.log_inference.call_args
        assert log_call[1]["use_case"] == "foundation_layer"
        assert log_call[1]["prompt"] == "Test prompt"
        assert log_call[1]["generated_output"] == "Generated response"
        
        # Verify: Response returned successfully
        assert result["success"] is True
        assert result["model_id"] == model_id


@pytest.mark.asyncio
async def test_e2e_deployment_to_orchestration_to_broadcast():
    """Test complete workflow: Deployment Manager → Orchestration → Service Broadcast."""
    # Setup: Deployment Manager and Service Coordinator
    deployment_manager = DeploymentManager()
    coordinator = ServiceCoordinator(deployment_manager=deployment_manager)
    
    new_model_id = str(uuid4())
    current_model_id = str(uuid4())
    
    # Mock deployment manager
    with patch.object(deployment_manager, 'deploy_model', return_value=True):
        # Mock broadcast update
        with patch.object(coordinator, 'broadcast_update') as mock_broadcast:
            mock_broadcast.return_value = {"success": True}
            
            # Execute: Coordinate deployment
            result = await coordinator.coordinate_model_deployment(
                new_model_id=new_model_id,
                current_model_id=current_model_id,
                use_case="interaction_layer",
                strategy="blue_green"
            )
            
            # Verify: Deployment was called
            assert deployment_manager.deploy_model.called
            
            # Verify: Broadcast was triggered
            assert mock_broadcast.called
            broadcast_data = mock_broadcast.call_args[1]["data"]
            assert broadcast_data["new_model_id"] == new_model_id
            assert broadcast_data["status"] == "completed"
            
            # Verify: Result indicates success
            assert result["success"] is True


@pytest.mark.asyncio
async def test_e2e_narrative_to_guardrails_to_logs():
    """Test complete workflow: Narrative Generation → Guardrails → Historical Logs."""
    # Setup: Narrative Generator with Guardrails Monitor
    guardrails_monitor = GuardrailsMonitor()
    generator = NarrativeGenerator(guardrails_monitor=guardrails_monitor)
    
    # Mock guardrails monitor
    with patch.object(generator.guardrails_monitor, 'monitor_outputs') as mock_monitor:
        mock_monitor.return_value = {
            "compliant": True,
            "violations": [],
            "safety": {"passed": True},
            "addiction_metrics": {"healthy_engagement": True},
            "harmful_content": {"detected": False}
        }
        
        # Mock model ID retrieval
        with patch.object(generator, '_get_model_id_for_logging', return_value=str(uuid4())):
            # Mock historical log processor
            with patch.object(generator.historical_log_processor, 'log_inference') as mock_log:
                mock_log.return_value = uuid4()
                
                # Mock LLM service
                with patch.object(generator, '_call_llm_service') as mock_llm:
                    mock_llm.return_value = '{"narrative_content": "Test narrative", "choices": [{"id": "c1", "text": "Choice 1"}]}'
                    
                    # Mock player context
                    with patch.object(generator, '_get_player_context') as mock_context:
                        from services.story_teller.narrative_generator import NarrativeContext
                        mock_context.return_value = NarrativeContext(
                            player_id=uuid4(),
                            current_world="day",
                            location="test",
                            player_stats={},
                            story_history=[],
                            world_state={},
                            npc_relationships={}
                        )
                        
                        # Execute: Generate narrative
                        result = await generator.generate_narrative(
                            player_id=uuid4(),
                            node_type="dialogue",
                            title="Test Node",
                            description="Test Description"
                        )
                        
                        # Verify: Guardrails monitoring was called
                        assert mock_monitor.called
                        call_args = mock_monitor.call_args
                        # Handle both args and kwargs
                        if call_args.args:
                            monitor_outputs = call_args.args[1]
                        else:
                            monitor_outputs = call_args.kwargs["outputs"]
                        assert "Test narrative" in monitor_outputs
                        assert "Choice 1" in monitor_outputs
                        
                        # Verify: Historical log was created
                        assert mock_log.called
                        log_call = mock_log.call_args
                        assert log_call[1]["use_case"] == "story_generation"
                        assert "Test narrative" in log_call[1]["generated_output"]
                        
                        # Verify: Narrative returned
                        assert "narrative_content" in result


@pytest.mark.asyncio
async def test_e2e_complete_model_lifecycle():
    """Test complete model lifecycle: Registration → Deployment → Usage → Logging."""
    # Setup: All components
    registry = ModelRegistry()
    deployment_manager = DeploymentManager()
    coordinator = ServiceCoordinator(deployment_manager=deployment_manager)
    
    # Step 1: Register model
    with patch.object(registry, '_get_postgres') as mock_postgres:
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_postgres.return_value = mock_pool
        
        model_id = await registry.register_model(
            model_name="test-model-v2",
            model_type="self_hosted",
            provider="ollama",
            use_case="interaction_layer",
            version="2.0"
        )
        await registry.update_model_status(model_id, "candidate")
        
        # Step 2: Get current model for comparison
        current_model_id = uuid4()
        with patch.object(registry, 'get_current_model', return_value={"model_id": str(current_model_id)}):
            # Step 3: Deploy new model
            with patch.object(deployment_manager, 'deploy_model', return_value=True):
                with patch.object(coordinator, 'broadcast_update') as mock_broadcast:
                    result = await coordinator.coordinate_model_deployment(
                        new_model_id=str(model_id),
                        current_model_id=str(current_model_id),
                        use_case="interaction_layer",
                        strategy="canary"
                    )
                    
                    # Verify: Deployment completed
                    assert result["success"] is True
                    assert mock_broadcast.called


@pytest.mark.asyncio
async def test_e2e_error_recovery_workflow():
    """Test error recovery in complete workflows."""
    # Test: Registry unavailable → Graceful fallback
    client = LLMClient()
    with patch.object(client.model_registry, 'get_current_model', side_effect=Exception("Registry down")):
        with patch.object(client, '_make_request', return_value={"text": "Fallback response", "tokens_used": 50}):
            result = await client.generate_text(
                layer="foundation",
                prompt="Test",
                context={}
            )
            # Should still work with fallback
            assert result["success"] is True or result.get("fallback") is True


@pytest.mark.asyncio
async def test_e2e_performance_tracking():
    """Test that performance metrics flow through complete workflows."""
    mock_registry = MagicMock()
    mock_registry.get_current_model = AsyncMock(return_value={
        "model_id": str(uuid4()),
        "use_case": "foundation_layer"
    })
    
    client = LLMClient(model_registry=mock_registry)
    
    with patch.object(client, '_make_request', return_value={"text": "Response", "tokens_used": 200}):
        with patch.object(client.historical_log_processor, 'log_inference') as mock_log:
            mock_log.return_value = uuid4()
            
            result = await client.generate_text(
                layer="foundation",
                prompt="Test",
                context={},
                max_tokens=1000,
                temperature=0.8
            )
            
            # Verify: Performance metrics captured
            assert mock_log.called
            metrics = mock_log.call_args[1]["performance_metrics"]
            assert "latency_ms" in metrics
            assert "tokens_used" in metrics
            assert metrics["tokens_used"] == 200
            assert "temperature" in metrics
            assert metrics["temperature"] == 0.8

