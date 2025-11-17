"""
Tests for 4D Vision segment validation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from ..segment_validator import SegmentValidator


class TestSegmentValidator:
    """Test suite for segment validator."""
    
    @pytest.fixture
    def validator(self):
        return SegmentValidator()
    
    @pytest.fixture
    def valid_segment(self):
        """Create a valid segment for testing."""
        now = datetime.utcnow()
        return {
            "segment_id": str(uuid4()),
            "build_id": "v1.2.3-dev-abc123",
            "scene_id": "horror_basement_01",
            "level_name": "Chapter1_Basement",
            "start_timestamp": now.isoformat(),
            "end_timestamp": (now + timedelta(seconds=10)).isoformat(),
            "sampling_mode": "window_based",
            "frame_count": 300,
            "camera_configs": [
                {
                    "camera_id": "player_pov",
                    "camera_type": "player_pov",
                    "fov": 90.0,
                    "position": [0, 0, 1.8],
                    "rotation": [0, 0, 0]
                }
            ],
            "media_uris": {
                "player_pov": "s3://bucket/segments/123/player_pov.mp4"
            },
            "performance_metrics": {
                "avg_fps": 60.0,
                "min_fps": 55.0,
                "max_fps": 62.0,
                "frame_time_variance": 2.0
            }
        }
    
    def test_validate_valid_segment(self, validator, valid_segment):
        """Test validation of a valid segment."""
        is_valid, errors, normalized = validator.validate_segment(valid_segment)
        
        assert is_valid is True
        assert len(errors) == 0
        assert "duration_seconds" in normalized
        assert normalized["duration_seconds"] == 10.0
    
    def test_missing_required_fields(self, validator):
        """Test validation with missing required fields."""
        segment = {
            "build_id": "v1.0.0",
            # Missing other required fields
        }
        
        is_valid, errors, normalized = validator.validate_segment(segment)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required field" in e for e in errors)
    
    def test_invalid_build_id(self, validator, valid_segment):
        """Test validation with invalid build ID."""
        valid_segment["build_id"] = "invalid-build"
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid build_id" in e for e in errors)
    
    def test_invalid_scene_id(self, validator, valid_segment):
        """Test validation with invalid scene ID."""
        valid_segment["scene_id"] = "scene with spaces!"
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid scene_id" in e for e in errors)
    
    def test_invalid_timestamp_order(self, validator, valid_segment):
        """Test validation with start > end timestamp."""
        valid_segment["start_timestamp"] = valid_segment["end_timestamp"]
        valid_segment["end_timestamp"] = datetime.utcnow().isoformat()
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("start_timestamp must be before end_timestamp" in e for e in errors)
    
    def test_segment_too_short(self, validator, valid_segment):
        """Test validation with segment too short."""
        start = datetime.utcnow()
        valid_segment["start_timestamp"] = start.isoformat()
        valid_segment["end_timestamp"] = (start + timedelta(seconds=0.05)).isoformat()
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Segment too short" in e for e in errors)
    
    def test_segment_too_long(self, validator, valid_segment):
        """Test validation with segment too long."""
        start = datetime.utcnow()
        valid_segment["start_timestamp"] = start.isoformat()
        valid_segment["end_timestamp"] = (start + timedelta(seconds=400)).isoformat()
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Segment too long" in e for e in errors)
    
    def test_invalid_sampling_mode(self, validator, valid_segment):
        """Test validation with invalid sampling mode."""
        valid_segment["sampling_mode"] = "invalid_mode"
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid sampling_mode" in e for e in errors)
    
    def test_no_cameras(self, validator, valid_segment):
        """Test validation with no camera configurations."""
        valid_segment["camera_configs"] = []
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("At least one camera configuration required" in e for e in errors)
    
    def test_duplicate_camera_ids(self, validator, valid_segment):
        """Test validation with duplicate camera IDs."""
        valid_segment["camera_configs"].append({
            "camera_id": "player_pov",  # Duplicate
            "camera_type": "debug",
            "fov": 120.0,
            "position": [0, 5, 0],
            "rotation": [90, 0, 0]
        })
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Duplicate camera_id" in e for e in errors)
    
    def test_invalid_camera_type(self, validator, valid_segment):
        """Test validation with invalid camera type."""
        valid_segment["camera_configs"][0]["camera_type"] = "invalid_type"
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid type" in e for e in errors)
    
    def test_invalid_fov(self, validator, valid_segment):
        """Test validation with invalid FOV."""
        valid_segment["camera_configs"][0]["fov"] = 180.0  # Too wide
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid FOV" in e for e in errors)
    
    def test_missing_media_uri(self, validator, valid_segment):
        """Test validation with missing media URI for camera."""
        valid_segment["media_uris"] = {}  # No URIs
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("No media URI for camera" in e for e in errors)
    
    def test_invalid_media_uri(self, validator, valid_segment):
        """Test validation with invalid media URI."""
        valid_segment["media_uris"]["player_pov"] = "not-a-valid-uri"
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid media URI" in e for e in errors)
    
    def test_valid_gameplay_events(self, validator, valid_segment):
        """Test validation with gameplay events."""
        now = datetime.utcnow()
        valid_segment["gameplay_events"] = [
            {
                "event_id": "evt_001",
                "event_type": "damage_taken",
                "timestamp": (now + timedelta(seconds=5)).isoformat(),
                "metadata": {"damage": 25, "source": "zombie_01"}
            }
        ]
        
        is_valid, errors, normalized = validator.validate_segment(valid_segment)
        
        assert is_valid is True
        assert len(normalized["gameplay_events"]) == 1
    
    def test_invalid_event_timestamp(self, validator, valid_segment):
        """Test validation with invalid event timestamp."""
        valid_segment["gameplay_events"] = [
            {
                "event_id": "evt_001",
                "event_type": "death",
                "timestamp": "invalid-timestamp"
            }
        ]
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid timestamp" in e for e in errors)
    
    def test_unknown_event_type(self, validator, valid_segment):
        """Test validation with unknown event type (should warn, not error)."""
        valid_segment["gameplay_events"] = [
            {
                "event_id": "evt_001",
                "event_type": "custom_event",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is True  # Unknown events allowed for extensibility
    
    def test_invalid_performance_metrics(self, validator, valid_segment):
        """Test validation with invalid performance metrics."""
        valid_segment["performance_metrics"] = {
            "avg_fps": -10,  # Negative FPS
            "gpu_utilization": 150,  # > 100%
            "draw_calls": "not-a-number"
        }
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Invalid avg_fps" in e for e in errors)
        assert any("Invalid gpu_utilization" in e for e in errors)
        assert any("Invalid draw_calls" in e for e in errors)
    
    def test_unrealistic_fps(self, validator, valid_segment):
        """Test validation with unrealistic FPS values."""
        valid_segment["performance_metrics"]["max_fps"] = 5000  # Unrealistic
        
        is_valid, errors, _ = validator.validate_segment(valid_segment)
        
        assert is_valid is False
        assert any("Unrealistic max_fps" in e for e in errors)
    
    def test_timestamp_parsing_formats(self, validator, valid_segment):
        """Test timestamp parsing with different formats."""
        # Test ISO format
        valid_segment["start_timestamp"] = "2024-01-01T12:00:00Z"
        valid_segment["end_timestamp"] = "2024-01-01T12:00:10Z"
        
        is_valid, errors, normalized = validator.validate_segment(valid_segment)
        assert is_valid is True
        
        # Test Unix timestamp
        start_unix = datetime.utcnow().timestamp()
        valid_segment["start_timestamp"] = start_unix
        valid_segment["end_timestamp"] = start_unix + 10
        
        is_valid, errors, normalized = validator.validate_segment(valid_segment)
        assert is_valid is True
    
    def test_normalization(self, validator, valid_segment):
        """Test that data is properly normalized."""
        # Add some data that needs normalization
        valid_segment["camera_configs"][0]["position"] = (1, 2, 3)  # Tuple
        valid_segment["camera_configs"][0]["rotation"] = [45]  # Wrong length
        
        is_valid, errors, normalized = validator.validate_segment(valid_segment)
        
        assert is_valid is False  # Rotation has wrong length
        
        # Fix rotation
        valid_segment["camera_configs"][0]["rotation"] = [45, 0, 0]
        is_valid, errors, normalized = validator.validate_segment(valid_segment)
        
        assert is_valid is True
        assert normalized["camera_configs"][0]["position"] == [1, 2, 3]  # Converted to list
        assert isinstance(normalized["start_timestamp"], datetime)
        assert isinstance(normalized["end_timestamp"], datetime)

