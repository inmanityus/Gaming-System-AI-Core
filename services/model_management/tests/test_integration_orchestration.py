"""
Integration tests for Orchestration Service ↔ Deployment Manager integration.
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from services.ai_integration.service_coordinator import ServiceCoordinator
from services.model_management.deployment_manager import DeploymentManager


@pytest.fixture
def deployment_manager():
    """Create DeploymentManager instance with mocked database."""
    manager = DeploymentManager()
    # Mock the database pool
    with patch.object(manager, 'db_pool'):
        manager.db_pool = None
        yield manager


@pytest.fixture
def service_coordinator(deployment_manager):
    """Create ServiceCoordinator with DeploymentManager integration."""
    return ServiceCoordinator(deployment_manager=deployment_manager)


@pytest.mark.asyncio
async def test_deployment_coordination_integration(service_coordinator):
    """Test that ServiceCoordinator can coordinate model deployments."""
    new_model_id = str(uuid4())
    current_model_id = str(uuid4())
    
    # Mock deployment manager
    with patch.object(service_coordinator.deployment_manager, 'deploy_model') as mock_deploy:
        mock_deploy.return_value = True
        
        # Mock broadcast update
        with patch.object(service_coordinator, 'broadcast_update') as mock_broadcast:
            mock_broadcast.return_value = {"success": True}
            
            # Coordinate deployment
            result = await service_coordinator.coordinate_model_deployment(
                new_model_id=new_model_id,
                current_model_id=current_model_id,
                use_case="interaction_layer",
                strategy="blue_green"
            )
            
            # Verify deployment was called
            assert mock_deploy.called
            call_args = mock_deploy.call_args
            assert call_args[1]["new_model_id"] == new_model_id
            assert call_args[1]["current_model_id"] == current_model_id
            assert call_args[1]["strategy"] == "blue_green"
            
            # Verify broadcast was called on success
            assert mock_broadcast.called
            assert result["success"] is True


@pytest.mark.asyncio
async def test_deployment_coordination_with_broadcast(service_coordinator):
    """Test that successful deployments trigger service broadcasts."""
    new_model_id = str(uuid4())
    current_model_id = str(uuid4())
    
    # Mock successful deployment
    with patch.object(service_coordinator.deployment_manager, 'deploy_model', return_value=True):
        with patch.object(service_coordinator, 'broadcast_update') as mock_broadcast:
            mock_broadcast.return_value = {"success": True}
            
            result = await service_coordinator.coordinate_model_deployment(
                new_model_id=new_model_id,
                current_model_id=current_model_id,
                use_case="foundation_layer",
                strategy="canary"
            )
            
            # Verify broadcast was called with correct data
            assert mock_broadcast.called
            broadcast_data = mock_broadcast.call_args[1]["data"]
            assert broadcast_data["use_case"] == "foundation_layer"
            assert broadcast_data["new_model_id"] == new_model_id
            assert broadcast_data["status"] == "completed"


@pytest.mark.asyncio
async def test_deployment_coordination_failure_handling(service_coordinator):
    """Test that deployment failures are handled gracefully."""
    new_model_id = str(uuid4())
    current_model_id = str(uuid4())
    
    # Mock deployment failure
    with patch.object(service_coordinator.deployment_manager, 'deploy_model', return_value=False):
        with patch.object(service_coordinator, 'broadcast_update') as mock_broadcast:
            result = await service_coordinator.coordinate_model_deployment(
                new_model_id=new_model_id,
                current_model_id=current_model_id,
                use_case="customization_layer",
                strategy="blue_green"
            )
            
            # Verify broadcast was NOT called on failure
            assert not mock_broadcast.called
            assert result["success"] is False


@pytest.mark.asyncio
async def test_deployment_coordination_exception_handling(service_coordinator):
    """Test that deployment exceptions are caught and handled."""
    new_model_id = str(uuid4())
    current_model_id = str(uuid4())
    
    # Mock deployment to raise exception
    with patch.object(service_coordinator.deployment_manager, 'deploy_model', side_effect=Exception("Deployment error")):
        result = await service_coordinator.coordinate_model_deployment(
            new_model_id=new_model_id,
            current_model_id=current_model_id,
            use_case="coordination_layer",
            strategy="all_at_once"
        )
        
        # Verify error is returned gracefully
        assert result["success"] is False
        assert "error" in result
        assert result["new_model_id"] == new_model_id
        assert result["current_model_id"] == current_model_id


@pytest.mark.asyncio
async def test_deployment_strategy_support(service_coordinator):
    """Test that all deployment strategies are supported."""
    new_model_id = str(uuid4())
    current_model_id = str(uuid4())
    
    strategies = ["blue_green", "canary", "all_at_once"]
    
    for strategy in strategies:
        with patch.object(service_coordinator.deployment_manager, 'deploy_model', return_value=True):
            with patch.object(service_coordinator, 'broadcast_update'):
                result = await service_coordinator.coordinate_model_deployment(
                    new_model_id=new_model_id,
                    current_model_id=current_model_id,
                    use_case="interaction_layer",
                    strategy=strategy
                )
                
                assert result["strategy"] == strategy
                assert result["success"] is True

