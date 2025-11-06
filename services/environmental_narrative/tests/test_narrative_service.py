"""
Tests for EnvironmentalNarrativeService.
"""

import pytest
from uuid import uuid4
from services.environmental_narrative.narrative_service import (
    EnvironmentalNarrativeService,
    SceneType,
    NarrativeWeight,
)


class TestEnvironmentalNarrativeService:
    """Tests for EnvironmentalNarrativeService."""
    
    def test_generate_story_scene(self):
        """Test story scene generation."""
        service = EnvironmentalNarrativeService()
        location = (100.0, 200.0, 50.0)
        
        scene = service.generate_story_scene(SceneType.ABANDONED_CAMP, location)
        
        assert scene.scene_type == SceneType.ABANDONED_CAMP
        assert scene.location == location
        assert scene.clutter_density >= 8  # min from template
        assert len(scene.objects) == scene.clutter_density
        assert len(scene.discovery_markers) > 0
    
    def test_generate_battle_aftermath(self):
        """Test battle aftermath scene generation."""
        service = EnvironmentalNarrativeService()
        location = (0.0, 0.0, 0.0)
        
        scene = service.generate_story_scene(SceneType.BATTLE_AFTERMATH, location)
        
        assert scene.scene_type == SceneType.BATTLE_AFTERMATH
        assert "damage_pattern" in scene.discovery_markers or "blood_stain" in scene.discovery_markers
    
    def test_record_discovery(self):
        """Test discovery recording."""
        service = EnvironmentalNarrativeService()
        player_id = uuid4()
        
        # Generate a scene first
        scene = service.generate_story_scene(SceneType.ABANDONED_CAMP, (0.0, 0.0, 0.0))
        object_id = scene.objects[0].object_id
        
        reward = service.record_discovery(player_id, object_id=object_id, noticed=True)
        
        assert reward.player_id == player_id
        assert reward.object_id == object_id
        assert reward.noticed is True
        assert reward.reward_value > 0
    
    def test_discovery_metrics(self):
        """Test discovery metrics tracking."""
        service = EnvironmentalNarrativeService()
        player_id = uuid4()
        
        scene = service.generate_story_scene(SceneType.ABANDONED_CAMP, (0.0, 0.0, 0.0))
        
        # Record some discoveries
        service.record_discovery(player_id, scene_id=scene.scene_id, noticed=True)
        service.record_discovery(player_id, scene_id=scene.scene_id, noticed=False)
        
        metrics = service.get_discovery_metrics()
        
        assert metrics["total_details"] == 2
        assert metrics["noticed_details"] == 1
        assert metrics["unnoticed_details"] == 1
        assert metrics["discovery_rate"] == 0.5
    
    def test_record_environmental_change(self):
        """Test environmental change recording."""
        service = EnvironmentalNarrativeService()
        player_id = uuid4()
        location = (10.0, 20.0, 30.0)
        
        service.record_environmental_change(
            "player_action",
            location,
            "Player destroyed wall",
            player_id
        )
        
        history = service.get_environmental_history(location, radius=5.0)
        assert len(history) == 1
        assert history[0]["change_type"] == "player_action"
        assert history[0]["description"] == "Player destroyed wall"
    
    def test_get_scene(self):
        """Test scene retrieval."""
        service = EnvironmentalNarrativeService()
        location = (0.0, 0.0, 0.0)
        
        scene = service.generate_story_scene(SceneType.LONG_TERM_SETTLEMENT, location)
        retrieved = service.get_scene(scene.scene_id)
        
        assert retrieved is not None
        assert retrieved.scene_id == scene.scene_id
        assert retrieved.scene_type == scene.scene_type
    
    def test_get_object_metadata(self):
        """Test object metadata retrieval."""
        service = EnvironmentalNarrativeService()
        scene = service.generate_story_scene(SceneType.ABANDONED_CAMP, (0.0, 0.0, 0.0))
        
        obj_id = scene.objects[0].object_id
        metadata = service.get_object_metadata(obj_id)
        
        assert metadata is not None
        assert metadata.object_id == obj_id
        assert len(metadata.story_tags) > 0
