"""
Comprehensive tests for Orchestration Service.
Created via pairwise testing with peer review.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from services.orchestration.orchestration_service import OrchestrationService
from services.orchestration.models import ContentRequest, ContentResponse
from services.orchestration.layers import (
    FoundationLayer,
    CustomizationLayer,
    InteractionLayer,
    CoordinationLayer
)


@pytest_asyncio.fixture
async def orchestration_service():
    """Create orchestration service instance for testing."""
    service = OrchestrationService()
    yield service
    await service.close()


@pytest_asyncio.fixture
def mock_inference_service():
    """Mock inference service."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={"personality": "fierce", "type": "vampire"})
    return mock


@pytest_asyncio.fixture
def mock_cloud_llm():
    """Mock cloud LLM client."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={"plan": "coordination plan", "tactics": "pack_coordination"})
    return mock


class TestFoundationLayer:
    """Tests for FoundationLayer (Layer 1)."""
    
    @pytest_asyncio.fixture
    def foundation_layer(self, mock_inference_service):
        """Create FoundationLayer instance."""
        return FoundationLayer(inference_service=mock_inference_service)
    
    @pytest.mark.asyncio
    async def test_generate_base_with_seed(self, foundation_layer):
        """Test foundation generation with seed."""
        request = ContentRequest(
            seed=12345,
            monster_type="vampire",
            biome="forest",
            size=100
        )
        
        result = await foundation_layer.generate_base(request)
        
        assert result is not None
        assert "monster" in result
        assert "terrain" in result
        assert "room" in result
        assert result["monster"]["type"] == "vampire"
        assert result["terrain"]["biome"] == "forest"
    
    @pytest.mark.asyncio
    async def test_generate_base_without_seed(self, foundation_layer):
        """Test foundation generation without seed."""
        request = ContentRequest()
        
        result = await foundation_layer.generate_base(request)
        
        assert result is not None
        assert "monster" in result
        assert "terrain" in result
        assert "room" in result
    
    @pytest.mark.asyncio
    async def test_generate_monster_base(self, foundation_layer):
        """Test monster base generation."""
        monster = await foundation_layer._generate_monster_base(seed=42, monster_type="zombie")
        
        assert monster["type"] == "zombie"
        assert "health" in monster
        assert "attack" in monster
        assert "defense" in monster
        assert "speed" in monster
    
    @pytest.mark.asyncio
    async def test_generate_terrain(self, foundation_layer):
        """Test terrain generation."""
        terrain = await foundation_layer._generate_terrain(biome="desert", size=200)
        
        assert terrain["biome"] == "desert"
        assert terrain["size"] == 200
        assert "features" in terrain
    
    @pytest.mark.asyncio
    async def test_generate_room(self, foundation_layer):
        """Test room generation."""
        room = await foundation_layer._generate_room(
            dimensions={"width": 20, "height": 30},
            seed=99
        )
        
        assert room["dimensions"]["width"] == 20
        assert room["dimensions"]["height"] == 30
        assert "exits" in room
        assert "lighting" in room


class TestCustomizationLayer:
    """Tests for CustomizationLayer (Layer 2)."""
    
    @pytest_asyncio.fixture
    def customization_layer(self, mock_inference_service):
        """Create CustomizationLayer instance."""
        return CustomizationLayer(inference_service=mock_inference_service)
    
    @pytest.mark.asyncio
    async def test_customize_monster_with_service(self, customization_layer, mock_inference_service):
        """Test monster customization with inference service."""
        base_monster = {"type": "vampire", "health": 100, "attack": 25}
        
        result = await customization_layer.customize_monster(base_monster)
        
        assert result is not None
        assert result["type"] == "vampire"  # Type preserved
        assert "personality" in result
        mock_inference_service.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customize_monster_without_service(self):
        """Test monster customization without inference service."""
        layer = CustomizationLayer(inference_service=None)
        base_monster = {"type": "zombie", "health": 80}
        
        result = await layer.customize_monster(base_monster)
        
        assert result is not None
        assert result["type"] == "zombie"
        assert "personality" in result
    
    @pytest.mark.asyncio
    async def test_enhance_terrain(self, customization_layer):
        """Test terrain enhancement."""
        terrain = {"biome": "forest", "size": 100}
        
        result = await customization_layer.enhance_terrain(terrain)
        
        assert result["biome"] == "forest"
        assert "details" in result
    
    @pytest.mark.asyncio
    async def test_detail_room(self, customization_layer):
        """Test room detailing."""
        room = {"dimensions": {"width": 10, "height": 10}, "lighting": "bright", "exits": 2}
        
        result = await customization_layer.detail_room(room)
        
        assert result["dimensions"]["width"] == 10
        assert "atmosphere" in result


class TestInteractionLayer:
    """Tests for InteractionLayer (Layer 3)."""
    
    @pytest_asyncio.fixture
    def interaction_layer(self, mock_inference_service):
        """Create InteractionLayer instance."""
        return InteractionLayer(inference_service=mock_inference_service)
    
    @pytest.mark.asyncio
    async def test_generate_dialogue_with_active_npcs(self, interaction_layer, mock_inference_service):
        """Test dialogue generation for active NPCs."""
        npcs = [
            {"id": "npc1", "type": "vampire", "is_active": True},
            {"id": "npc2", "type": "zombie", "is_active": True}
        ]
        player_context = {"player_id": "player1", "location": "forest"}
        
        result = await interaction_layer.generate_dialogue(npcs, player_context)
        
        assert len(result) == 2
        assert all("npc_id" in dialogue for dialogue in result)
        assert all("dialogue" in dialogue for dialogue in result)
    
    @pytest.mark.asyncio
    async def test_generate_dialogue_with_inactive_npcs(self, interaction_layer):
        """Test dialogue generation skips inactive NPCs."""
        npcs = [
            {"id": "npc1", "type": "vampire", "is_active": False},
            {"id": "npc2", "type": "zombie", "is_active": False}
        ]
        
        result = await interaction_layer.generate_dialogue(npcs)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_generate_npc_dialogue(self, interaction_layer, mock_inference_service):
        """Test single NPC dialogue generation."""
        npc = {"id": "npc1", "type": "vampire"}
        player_context = {"player_id": "player1"}
        
        result = await interaction_layer.generate_npc_dialogue(npc, player_context)
        
        assert result["npc_id"] == "npc1"
        assert result["npc_type"] == "vampire"
        assert "dialogue" in result
        assert "tone" in result


class TestCoordinationLayer:
    """Tests for CoordinationLayer (Layer 4)."""
    
    @pytest_asyncio.fixture
    def coordination_layer(self, mock_cloud_llm):
        """Create CoordinationLayer instance."""
        return CoordinationLayer(cloud_llm_client=mock_cloud_llm)
    
    @pytest.mark.asyncio
    async def test_coordinate_with_cloud_llm(self, coordination_layer, mock_cloud_llm):
        """Test coordination with cloud LLM."""
        content = {"monsters": [{"type": "vampire"}], "terrain": {"biome": "forest"}}
        interactions = [{"npc_id": "npc1", "dialogue": "Hello"}]
        
        result = await coordination_layer.coordinate(content, interactions)
        
        assert result is not None
        assert "scenario_type" in result or "plan" in result
        mock_cloud_llm.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_coordinate_without_cloud_llm(self):
        """Test coordination without cloud LLM (fallback)."""
        layer = CoordinationLayer(cloud_llm_client=None)
        content = {"monsters": []}
        
        result = await layer.coordinate(content)
        
        assert result is not None
        assert "scenario_type" in result
    
    @pytest.mark.asyncio
    async def test_coordinate_battle(self, coordination_layer, mock_cloud_llm):
        """Test battle coordination."""
        monsters = [
            {"id": "monster1", "type": "vampire", "attack": 25},
            {"id": "monster2", "type": "zombie", "attack": 20}
        ]
        player = {"id": "player1", "health": 100}
        
        result = await coordination_layer.coordinate_battle(monsters, player)
        
        assert result is not None
        assert "monster_actions" in result
        assert "coordinator_plan" in result
        assert len(result["monster_actions"]) == 2


class TestOrchestrationService:
    """Tests for main OrchestrationService."""
    
    @pytest.mark.asyncio
    async def test_generate_content_full_pipeline(self, orchestration_service, mock_inference_service, mock_cloud_llm):
        """Test full 4-layer pipeline."""
        with patch.object(orchestration_service, 'layer1', FoundationLayer(inference_service=mock_inference_service)):
            with patch.object(orchestration_service, 'layer2', CustomizationLayer(inference_service=mock_inference_service)):
                with patch.object(orchestration_service, 'layer3', InteractionLayer(inference_service=mock_inference_service)):
                    with patch.object(orchestration_service, 'layer4', CoordinationLayer(cloud_llm_client=mock_cloud_llm)):
                        request = ContentRequest(
                            seed=42,
                            monster_type="vampire",
                            biome="forest",
                            activate_npcs=True,
                            requires_coordination=True
                        )
                        
                        response = await orchestration_service.generate_content(request)
                        
                        assert isinstance(response, ContentResponse)
                        assert response.foundation is not None
                        assert response.customized is not None
                        assert response.interactions is not None
                        assert response.orchestration is not None
    
    @pytest.mark.asyncio
    async def test_generate_content_minimal(self, orchestration_service):
        """Test content generation with minimal request."""
        request = ContentRequest()
        
        response = await orchestration_service.generate_content(request)
        
        assert isinstance(response, ContentResponse)
        assert response.foundation is not None
    
    @pytest.mark.asyncio
    async def test_resolve_conflicts(self, orchestration_service):
        """Test conflict resolution."""
        layer_outputs = {
            "foundation": {"monster": {"type": "vampire"}},
            "customized": {"monster": {"type": "zombie"}}  # Conflict
        }
        
        result = await orchestration_service.resolve_conflicts(layer_outputs)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_coordinate_battle(self, orchestration_service):
        """Test battle coordination."""
        monsters = [{"id": "m1", "type": "vampire"}, {"id": "m2", "type": "zombie"}]
        player = {"id": "p1", "health": 100}
        
        result = await orchestration_service.coordinate_battle(monsters, player)
        
        assert result is not None
        assert "monster_actions" in result
        assert "coordinator_plan" in result

