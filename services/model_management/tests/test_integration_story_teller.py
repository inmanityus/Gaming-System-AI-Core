"""
Integration tests for Story Teller Service ↔ Guardrails Monitor integration.
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from services.story_teller.narrative_generator import NarrativeGenerator
from services.model_management.guardrails_monitor import GuardrailsMonitor


@pytest.fixture
async def guardrails_monitor():
    """Create GuardrailsMonitor instance for testing."""
    return GuardrailsMonitor()


@pytest.fixture
async def narrative_generator(guardrails_monitor):
    """Create NarrativeGenerator with GuardrailsMonitor integration."""
    return NarrativeGenerator(guardrails_monitor=guardrails_monitor)


@pytest.mark.asyncio
async def test_guardrails_monitoring_integration(narrative_generator):
    """Test that guardrails monitoring happens during narrative generation."""
    # Mock guardrails monitor
    with patch.object(narrative_generator.guardrails_monitor, 'monitor_outputs') as mock_monitor:
        mock_monitor.return_value = {
            "compliant": True,
            "violations": [],
            "safety": {"passed": True},
            "addiction_metrics": {"healthy_engagement": True},
            "harmful_content": {"detected": False}
        }
        
        # Mock LLM call
        with patch.object(narrative_generator, '_call_llm_service') as mock_llm:
            mock_llm.return_value = '{"narrative_content": "Test narrative", "choices": [{"id": "choice1", "text": "Choice 1"}]}'
            
            # Mock player context
            with patch.object(narrative_generator, '_get_player_context') as mock_context:
                from services.story_teller.narrative_generator import NarrativeContext
                mock_context.return_value = NarrativeContext(
                    player_id=uuid4(),
                    current_world="day",
                    location="test_location",
                    player_stats={},
                    story_history=[],
                    world_state={},
                    npc_relationships={}
                )
                
                # Generate narrative (should trigger monitoring)
                result = await narrative_generator.generate_narrative(
                    player_id=uuid4(),
                    node_type="dialogue",
                    title="Test Node",
                    description="Test Description"
                )
                
                # Verify monitoring was called
                assert mock_monitor.called
                call_args = mock_monitor.call_args
                # Check if called with args or kwargs
                if call_args.args:
                    assert call_args.args[0] == "story_generation"  # model_id
                    outputs = call_args.args[1]
                else:
                    assert call_args.kwargs["model_id"] == "story_generation"
                    outputs = call_args.kwargs["outputs"]
                assert "Test narrative" in outputs
                assert "Choice 1" in outputs


@pytest.mark.asyncio
async def test_guardrails_violation_fallback(narrative_generator):
    """Test that critical violations trigger fallback content."""
    # Mock guardrails monitor to return critical violation
    with patch.object(narrative_generator.guardrails_monitor, 'monitor_outputs') as mock_monitor:
        mock_monitor.return_value = {
            "compliant": False,
            "violations": [{
                "type": "safety",
                "severity": "critical",
                "details": {"reason": "Harmful content detected"}
            }],
            "safety": {"passed": False, "severity": "critical"},
            "addiction_metrics": {"healthy_engagement": True},
            "harmful_content": {"detected": True}
        }
        
        # Mock LLM call
        with patch.object(narrative_generator, '_call_llm_service') as mock_llm:
            mock_llm.return_value = '{"narrative_content": "Harmful content", "choices": []}'
            
            # Mock player context
            with patch.object(narrative_generator, '_get_player_context') as mock_context:
                from services.story_teller.narrative_generator import NarrativeContext
                mock_context.return_value = NarrativeContext(
                    player_id=uuid4(),
                    current_world="day",
                    location="test_location",
                    player_stats={},
                    story_history=[],
                    world_state={},
                    npc_relationships={}
                )
                
                # Generate narrative (should return fallback)
                result = await narrative_generator.generate_narrative(
                    player_id=uuid4(),
                    node_type="dialogue",
                    title="Test Node",
                    description="Test Description"
                )
                
                # Verify fallback content returned
                assert "dialogue" in result["narrative_content"].lower() or "Test Description" in result["narrative_content"]
                assert len(result["choices"]) > 0


@pytest.mark.asyncio
async def test_historical_logging_story_generation(narrative_generator):
    """Test that story generation is logged to historical logs."""
    # Mock guardrails monitor
    with patch.object(narrative_generator.guardrails_monitor, 'monitor_outputs') as mock_monitor:
        mock_monitor.return_value = {
            "compliant": True,
            "violations": []
        }
        
        # Mock model ID retrieval
        with patch.object(narrative_generator, '_get_model_id_for_logging') as mock_get_id:
            mock_get_id.return_value = str(uuid4())
            
            # Mock historical log processor
            with patch.object(narrative_generator.historical_log_processor, 'log_inference') as mock_log:
                mock_log.return_value = uuid4()
                
                # Mock LLM call
                with patch.object(narrative_generator, '_call_llm_service') as mock_llm:
                    mock_llm.return_value = '{"narrative_content": "Test narrative", "choices": []}'
                    
                    # Mock player context
                    with patch.object(narrative_generator, '_get_player_context') as mock_context:
                        from services.story_teller.narrative_generator import NarrativeContext
                        mock_context.return_value = NarrativeContext(
                            player_id=uuid4(),
                            current_world="day",
                            location="test_location",
                            player_stats={},
                            story_history=[],
                            world_state={},
                            npc_relationships={}
                        )
                        
                        # Generate narrative
                        await narrative_generator.generate_narrative(
                            player_id=uuid4(),
                            node_type="dialogue",
                            title="Test Node",
                            description="Test Description"
                        )
                        
                        # Verify logging was called
                        assert mock_log.called
                        call_args = mock_log.call_args
                        assert call_args[1]["use_case"] == "story_generation"
                        assert "Test narrative" in call_args[1]["generated_output"]


@pytest.mark.asyncio
async def test_error_handling_guardrails_failure(narrative_generator):
    """Test that guardrails failures don't block narrative generation."""
    # Mock guardrails monitor to fail
    with patch.object(narrative_generator.guardrails_monitor, 'monitor_outputs', side_effect=Exception("Monitoring failed")):
        # Mock LLM call
        with patch.object(narrative_generator, '_call_llm_service') as mock_llm:
            mock_llm.return_value = '{"narrative_content": "Test narrative", "choices": []}'
            
            # Mock player context
            with patch.object(narrative_generator, '_get_player_context') as mock_context:
                from services.story_teller.narrative_generator import NarrativeContext
                mock_context.return_value = NarrativeContext(
                    player_id=uuid4(),
                    current_world="day",
                    location="test_location",
                    player_stats={},
                    story_history=[],
                    world_state={},
                    npc_relationships={}
                )
                
                # Should still generate narrative (fallback to default behavior)
                result = await narrative_generator.generate_narrative(
                    player_id=uuid4(),
                    node_type="dialogue",
                    title="Test Node",
                    description="Test Description"
                )
                
                # Verify narrative returned
                assert result is not None
                assert "narrative_content" in result

