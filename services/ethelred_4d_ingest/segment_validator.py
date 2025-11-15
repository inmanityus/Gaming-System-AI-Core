"""
Segment validation and normalization for 4D Vision capture data.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import re
from loguru import logger


class SegmentValidator:
    """Validates and normalizes 4D segment descriptors."""
    
    # Valid camera types per R-4D-IN-001
    VALID_CAMERA_TYPES = {
        "player_pov", "debug", "test", "cinematic", 
        "fixed", "follow", "overhead"
    }
    
    # Valid sampling modes per R-4D-IN-003
    VALID_SAMPLING_MODES = {
        "frame_level",    # Every frame captured
        "window_based",   # Time windows (e.g., 5-10s)
        "event_based"     # Triggered by gameplay events
    }
    
    # Valid gameplay event types
    VALID_EVENT_TYPES = {
        "damage_taken", "death", "scare_moment", "boss_encounter",
        "puzzle_start", "puzzle_complete", "cutscene_start", "cutscene_end",
        "checkpoint", "level_transition", "combat_start", "combat_end"
    }
    
    # Required fields for segment
    REQUIRED_FIELDS = {
        "build_id", "scene_id", "level_name", 
        "start_timestamp", "end_timestamp", "sampling_mode"
    }
    
    # Scene ID pattern
    SCENE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")
    
    def validate_segment(self, segment_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate a segment descriptor.
        
        Returns:
            (is_valid, errors, normalized_data)
        """
        errors = []
        normalized = segment_data.copy()
        
        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(segment_data.keys())
        if missing_fields:
            errors.extend(f"Missing required field: {field}" for field in missing_fields)
            return False, errors, normalized
        
        # Validate build_id
        if not self._validate_build_id(segment_data.get("build_id")):
            errors.append("Invalid build_id format")
        
        # Validate scene_id
        scene_id = segment_data.get("scene_id")
        if not scene_id or not self.SCENE_ID_PATTERN.match(scene_id):
            errors.append(f"Invalid scene_id format: {scene_id}")
        
        # Validate timestamps
        try:
            start_ts = self._parse_timestamp(segment_data["start_timestamp"])
            end_ts = self._parse_timestamp(segment_data["end_timestamp"])
            
            if start_ts >= end_ts:
                errors.append("start_timestamp must be before end_timestamp")
            else:
                duration = (end_ts - start_ts).total_seconds()
                if duration < 0.1:
                    errors.append(f"Segment too short: {duration}s")
                elif duration > 300:  # 5 minutes max
                    errors.append(f"Segment too long: {duration}s")
                
                normalized["duration_seconds"] = duration
                normalized["start_timestamp"] = start_ts
                normalized["end_timestamp"] = end_ts
                
        except Exception as e:
            errors.append(f"Invalid timestamp: {e}")
        
        # Validate sampling mode
        sampling_mode = segment_data.get("sampling_mode")
        if sampling_mode not in self.VALID_SAMPLING_MODES:
            errors.append(f"Invalid sampling_mode: {sampling_mode}")
        
        # Validate cameras
        cameras = segment_data.get("camera_configs", [])
        if not cameras:
            errors.append("At least one camera configuration required")
        else:
            camera_errors, normalized["camera_configs"] = self._validate_cameras(cameras)
            errors.extend(camera_errors)
        
        # Validate media URIs
        media_uris = segment_data.get("media_uris", {})
        if not media_uris:
            errors.append("No media URIs provided")
        else:
            uri_errors = self._validate_media_uris(media_uris, cameras)
            errors.extend(uri_errors)
        
        # Validate gameplay events
        events = segment_data.get("gameplay_events", [])
        event_errors, normalized["gameplay_events"] = self._validate_events(events)
        errors.extend(event_errors)
        
        # Validate performance metrics
        if "performance_metrics" in segment_data:
            perf_errors, normalized["performance_metrics"] = self._validate_performance(
                segment_data["performance_metrics"]
            )
            errors.extend(perf_errors)
        
        # Frame count validation
        frame_count = segment_data.get("frame_count", 0)
        if frame_count < 1:
            errors.append(f"Invalid frame_count: {frame_count}")
        
        return len(errors) == 0, errors, normalized
    
    def _validate_build_id(self, build_id: str) -> bool:
        """Validate build ID format."""
        if not build_id:
            return False
        # Expected format: v1.2.3-dev-abcd123
        return bool(re.match(r"^v\d+\.\d+\.\d+(-\w+)?(-[a-f0-9]+)?$", build_id))
    
    def _parse_timestamp(self, ts: Any) -> datetime:
        """Parse timestamp from various formats."""
        if isinstance(ts, datetime):
            return ts
        elif isinstance(ts, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except:
                # Try other common formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        return datetime.strptime(ts, fmt)
                    except:
                        continue
        elif isinstance(ts, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(ts)
        
        raise ValueError(f"Cannot parse timestamp: {ts}")
    
    def _validate_cameras(self, cameras: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """Validate camera configurations."""
        errors = []
        normalized = []
        camera_ids = set()
        
        for i, cam in enumerate(cameras):
            if not isinstance(cam, dict):
                errors.append(f"Camera {i}: Invalid format")
                continue
            
            # Check required fields
            cam_id = cam.get("camera_id")
            if not cam_id:
                errors.append(f"Camera {i}: Missing camera_id")
                continue
            
            if cam_id in camera_ids:
                errors.append(f"Duplicate camera_id: {cam_id}")
            camera_ids.add(cam_id)
            
            # Validate camera type
            cam_type = cam.get("camera_type")
            if cam_type not in self.VALID_CAMERA_TYPES:
                errors.append(f"Camera {cam_id}: Invalid type '{cam_type}'")
            
            # Validate FOV
            fov = cam.get("fov", 90.0)
            if not (30 <= fov <= 170):
                errors.append(f"Camera {cam_id}: Invalid FOV {fov}")
            
            # Validate position/rotation
            norm_cam = cam.copy()
            
            position = cam.get("position", [0, 0, 0])
            if len(position) != 3:
                errors.append(f"Camera {cam_id}: Invalid position")
            norm_cam["position"] = list(position)
            
            rotation = cam.get("rotation", [0, 0, 0])
            if len(rotation) != 3:
                errors.append(f"Camera {cam_id}: Invalid rotation")
            norm_cam["rotation"] = list(rotation)
            
            normalized.append(norm_cam)
        
        return errors, normalized
    
    def _validate_media_uris(self, media_uris: Dict[str, str], cameras: List[Dict]) -> List[str]:
        """Validate media URI mappings."""
        errors = []
        camera_ids = {cam.get("camera_id") for cam in cameras if cam.get("camera_id")}
        
        # Check each camera has a media URI
        for cam_id in camera_ids:
            if cam_id not in media_uris:
                errors.append(f"No media URI for camera {cam_id}")
        
        # Validate URI format
        for cam_id, uri in media_uris.items():
            if cam_id not in camera_ids:
                errors.append(f"Media URI for unknown camera: {cam_id}")
            
            if not self._validate_storage_uri(uri):
                errors.append(f"Invalid media URI for {cam_id}: {uri}")
        
        return errors
    
    def _validate_storage_uri(self, uri: str) -> bool:
        """Validate storage URI format."""
        if not uri:
            return False
        
        # Support S3, local paths, and HTTP(S) URLs
        valid_prefixes = ("s3://", "file://", "http://", "https://", "/")
        return any(uri.startswith(prefix) for prefix in valid_prefixes)
    
    def _validate_events(self, events: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """Validate gameplay events."""
        errors = []
        normalized = []
        
        for i, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append(f"Event {i}: Invalid format")
                continue
            
            event_id = event.get("event_id")
            if not event_id:
                errors.append(f"Event {i}: Missing event_id")
                continue
            
            event_type = event.get("event_type")
            if event_type not in self.VALID_EVENT_TYPES:
                logger.warning(f"Unknown event type: {event_type}")
                # Don't error on unknown types - allow extensibility
            
            # Validate timestamp
            try:
                norm_event = event.copy()
                norm_event["timestamp"] = self._parse_timestamp(event.get("timestamp"))
                normalized.append(norm_event)
            except Exception as e:
                errors.append(f"Event {event_id}: Invalid timestamp - {e}")
        
        return errors, normalized
    
    def _validate_performance(self, perf: Dict) -> Tuple[List[str], Dict]:
        """Validate performance metrics."""
        errors = []
        normalized = perf.copy()
        
        # Validate FPS metrics
        for metric in ["avg_fps", "min_fps", "max_fps"]:
            value = perf.get(metric)
            if value is not None:
                if not isinstance(value, (int, float)) or value < 0:
                    errors.append(f"Invalid {metric}: {value}")
                elif value > 1000:  # Sanity check
                    errors.append(f"Unrealistic {metric}: {value}")
        
        # Validate utilization percentages
        for metric in ["gpu_utilization", "cpu_utilization"]:
            value = perf.get(metric)
            if value is not None:
                if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                    errors.append(f"Invalid {metric}: {value}")
        
        # Validate counts
        for metric in ["draw_calls", "triangles_rendered"]:
            value = perf.get(metric)
            if value is not None:
                if not isinstance(value, int) or value < 0:
                    errors.append(f"Invalid {metric}: {value}")
        
        return errors, normalized
