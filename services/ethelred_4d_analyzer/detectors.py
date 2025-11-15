"""
Detector implementations for 4D Vision analysis.

These are skeleton implementations that demonstrate the interface
and basic detection logic. In production, these would use ML models
and sophisticated computer vision algorithms.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import random
import math
import numpy as np
from loguru import logger

from .detector_base import (
    VisionDetector, BatchDetector, StreamingDetector,
    DetectorFinding, SegmentContext
)


class AnimationDetector(StreamingDetector):
    """
    Detects animation and rigging issues (R-4D-DET-001).
    
    Issues detected:
    - T-pose/A-pose glitches
    - Bone deformation errors
    - IK constraint violations
    - Animation blending artifacts
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Configurable thresholds
        self.t_pose_threshold = self.config.get("t_pose_threshold", 0.85)
        self.bone_stretch_threshold = self.config.get("bone_stretch_threshold", 1.5)
        self.ik_error_threshold = self.config.get("ik_error_threshold", 0.1)
        self.blend_artifact_threshold = self.config.get("blend_artifact_threshold", 0.7)
        self.sensitivity_mode = self.config.get("sensitivity_mode", "medium")
        
        # Tracking state across frames
        self._pose_history = []
        self._max_history = 30  # 1 second at 30fps
        
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_issue_types": [
                "t_pose", "a_pose", "bone_stretching", "ik_violation",
                "blend_artifact", "missing_animation", "frozen_animation"
            ],
            "requires_depth": False,
            "performance_impact": "medium",
            "configuration": {
                **self.config,
                "active_thresholds": {
                    "t_pose": self.t_pose_threshold,
                    "bone_stretch": self.bone_stretch_threshold,
                    "ik_error": self.ik_error_threshold,
                    "blend_artifact": self.blend_artifact_threshold
                }
            }
        }
    
    def _analyze_pose_features(self, frame: Dict[str, Any]) -> Dict[str, float]:
        """Extract pose features from frame (stub for ML model)."""
        # In production, this would use actual pose estimation
        return {
            "arm_angle": random.uniform(0, 180),  # Degrees from body
            "leg_spread": random.uniform(0, 90),   # Degrees
            "spine_curvature": random.uniform(0, 45),
            "hand_elevation": random.uniform(0, 2),  # Relative to shoulder height
            "pose_confidence": random.uniform(0.5, 1.0)
        }
    
    def _detect_t_pose(self, pose_features: Dict[str, float]) -> Tuple[bool, float]:
        """Detect T-pose based on pose features."""
        arm_angle = pose_features.get("arm_angle", 0)
        hand_elevation = pose_features.get("hand_elevation", 0)
        
        # T-pose characterized by arms at ~90 degrees, hands at shoulder level
        t_pose_score = 0.0
        if 80 <= arm_angle <= 100:
            t_pose_score += 0.5
        if 0.9 <= hand_elevation <= 1.1:
            t_pose_score += 0.5
            
        # Adjust for sensitivity mode
        if self.sensitivity_mode == "high":
            t_pose_score *= 1.2
        elif self.sensitivity_mode == "low":
            t_pose_score *= 0.8
            
        is_t_pose = t_pose_score >= self.t_pose_threshold
        return is_t_pose, min(t_pose_score, 1.0)
    
    def _detect_frozen_animation(self) -> Tuple[bool, float]:
        """Detect if animation is frozen by checking pose history."""
        if len(self._pose_history) < 10:
            return False, 0.0
            
        # Calculate variance in recent poses
        recent_poses = self._pose_history[-10:]
        arm_angles = [p.get("arm_angle", 0) for p in recent_poses]
        variance = np.var(arm_angles) if arm_angles else 0
        
        # Low variance indicates frozen animation
        is_frozen = variance < 0.01
        confidence = 1.0 - min(variance * 100, 1.0)
        
        return is_frozen, confidence
    
    def _check_animation_context(self, frame_time: float, segment: SegmentContext) -> List[str]:
        """Check gameplay context that might affect animation expectations."""
        contexts = []
        
        for event in segment.gameplay_events:
            event_time = event.get("timestamp", segment.start_timestamp).timestamp()
            if abs(event_time - frame_time) < 1.0:  # Within 1 second
                event_type = event.get("event_type", "")
                if event_type == "death":
                    contexts.append("death_sequence")
                elif event_type == "combat_start":
                    contexts.append("combat")
                elif event_type == "puzzle_start":
                    contexts.append("puzzle_interaction")
                    
        return contexts
    
    async def analyze_frame(
        self,
        frame: Dict[str, Any],
        frame_index: int,
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze a single frame for animation issues."""
        findings = []
        
        # Extract pose features
        pose_features = self._analyze_pose_features(frame)
        self._pose_history.append(pose_features)
        if len(self._pose_history) > self._max_history:
            self._pose_history.pop(0)
        
        # Calculate frame time
        fps = segment.performance_metrics.get("avg_fps", 30)
        frame_time = segment.start_timestamp.timestamp() + (frame_index / fps)
        
        # Get animation context
        contexts = self._check_animation_context(frame_time, segment)
        
        # T-pose detection
        is_t_pose, t_pose_confidence = self._detect_t_pose(pose_features)
        if is_t_pose and "death_sequence" not in contexts:  # T-pose might be valid in death
            findings.append(DetectorFinding(
                detector_type="animation",
                issue_id=f"anim_{segment.segment_id}_{frame_index}_tpose",
                issue_type="t_pose",
                severity=0.8,
                confidence=t_pose_confidence,
                timestamp=datetime.fromtimestamp(frame_time),
                camera_id=list(segment.media_uris.keys())[0] if segment.media_uris else None,
                screen_coords=(0.5, 0.5),
                description="Character detected in T-pose, likely animation system failure",
                explainability={
                    "signals": {
                        "arm_angle": pose_features.get("arm_angle"),
                        "hand_elevation": pose_features.get("hand_elevation"),
                        "pose_confidence": pose_features.get("pose_confidence")
                    },
                    "thresholds": {
                        "t_pose_threshold": self.t_pose_threshold,
                        "sensitivity_mode": self.sensitivity_mode
                    },
                    "notes": f"T-pose detected with confidence {t_pose_confidence:.2f}"
                },
                metrics={
                    "pose_confidence": t_pose_confidence,
                    "duration_frames": len([p for p in self._pose_history[-5:] 
                                           if self._detect_t_pose(p)[0]])
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.9
            ))
        
        # Frozen animation detection
        is_frozen, frozen_confidence = self._detect_frozen_animation()
        if is_frozen and "puzzle_interaction" not in contexts:  # Might be still during puzzles
            findings.append(DetectorFinding(
                detector_type="animation",
                issue_id=f"anim_{segment.segment_id}_{frame_index}_frozen",
                issue_type="frozen_animation",
                severity=0.7,
                confidence=frozen_confidence,
                timestamp=datetime.fromtimestamp(frame_time),
                description="Animation appears frozen, no movement detected",
                explainability={
                    "signals": {
                        "pose_variance": 0.0,
                        "frames_analyzed": len(self._pose_history)
                    },
                    "thresholds": {
                        "variance_threshold": 0.01
                    },
                    "notes": "Low variance in pose data indicates frozen animation"
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.8
            ))
        
        # Context-specific checks
        if "death_sequence" in contexts:
            # Special checks for death animations
            if random.random() < 0.1:  # Simulate detection
                findings.append(DetectorFinding(
                    detector_type="animation", 
                    issue_id=f"anim_{segment.segment_id}_{frame_index}_death",
                    issue_type="missing_animation",
                    severity=0.6,
                    confidence=0.75,
                    timestamp=datetime.fromtimestamp(frame_time),
                    description="Death animation may be missing or interrupted",
                    explainability={
                        "signals": {
                            "death_event_detected": True,
                            "animation_state": "unknown"
                        },
                        "notes": "Death event triggered but no corresponding animation detected"
                    },
                    affected_goals=["G-IMMERSION", "G-HORROR"],
                    player_impact=0.7
                ))
        
        return findings


class PhysicsDetector(BatchDetector):
    """
    Detects physics and collision issues (R-4D-DET-002).
    
    Issues detected:
    - Object interpenetration/clipping
    - Ragdoll explosions
    - Floating objects
    - Collision detection failures
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Configurable thresholds
        self.clipping_threshold = self.config.get("clipping_threshold", 0.05)  # meters
        self.ragdoll_velocity_threshold = self.config.get("ragdoll_velocity_threshold", 50.0)  # m/s
        self.float_distance_threshold = self.config.get("float_distance_threshold", 0.1)  # meters
        self.jitter_threshold = self.config.get("jitter_threshold", 5.0)  # ms variance
        self.sensitivity_mode = self.config.get("sensitivity_mode", "medium")
        
        # Tracking state
        self._object_positions = {}  # Track positions for velocity calculations
        self._collision_history = []
        
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_issue_types": [
                "clipping", "interpenetration", "ragdoll_explosion",
                "floating_object", "collision_failure", "physics_jitter"
            ],
            "requires_depth": True,
            "performance_impact": "high",
            "configuration": {
                **self.config,
                "active_thresholds": {
                    "clipping": self.clipping_threshold,
                    "ragdoll_velocity": self.ragdoll_velocity_threshold,
                    "float_distance": self.float_distance_threshold,
                    "jitter": self.jitter_threshold
                }
            }
        }
    
    def _extract_depth_features(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract depth-based features for physics analysis."""
        # In production, would process actual depth maps
        return {
            "object_distances": {
                "character_to_wall": random.uniform(-0.2, 0.5),  # Negative means clipping
                "character_to_ground": random.uniform(0, 0.3),
                "objects_to_ground": [random.uniform(-0.1, 0.5) for _ in range(3)]
            },
            "velocity_estimates": {
                "ragdoll_parts": [random.uniform(0, 60) for _ in range(5)],  # m/s
                "debris": [random.uniform(0, 20) for _ in range(10)]
            },
            "collision_points": [
                {"pos": (x, y, z), "normal": (nx, ny, nz), "depth": d}
                for x, y, z, nx, ny, nz, d in [
                    (100, 200, 50, 0, 0, 1, random.uniform(0, 0.3))
                    for _ in range(random.randint(0, 5))
                ]
            ]
        }
    
    def _detect_clipping(self, depth_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect object interpenetration/clipping issues."""
        findings = []
        
        # Check character-to-wall distance
        char_wall_dist = depth_features["object_distances"]["character_to_wall"]
        if char_wall_dist < -self.clipping_threshold:
            penetration = abs(char_wall_dist)
            severity = min(penetration / 0.5, 1.0)  # Max severity at 0.5m penetration
            
            findings.append(DetectorFinding(
                detector_type="physics",
                issue_id=f"phys_{self.segment_id}_clip_wall",
                issue_type="clipping",
                severity=severity,
                confidence=0.85,
                timestamp=self.current_timestamp,
                world_coords=(100.0, 200.0, 50.0),
                description=f"Character clipping through wall by {penetration:.2f}m",
                explainability={
                    "signals": {
                        "penetration_depth": penetration,
                        "clipping_threshold": self.clipping_threshold
                    },
                    "thresholds": {
                        "clipping_threshold": self.clipping_threshold,
                        "sensitivity_mode": self.sensitivity_mode
                    },
                    "notes": f"Object penetration exceeds threshold by {penetration - self.clipping_threshold:.2f}m"
                },
                metrics={
                    "penetration_depth": penetration,
                    "object_pairs": ["character", "wall_geometry"]
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.7 if severity > 0.5 else 0.5
            ))
        
        # Check for multiple collision points indicating complex clipping
        collision_points = depth_features["collision_points"]
        if len(collision_points) > 3:
            avg_depth = sum(cp["depth"] for cp in collision_points) / len(collision_points)
            if avg_depth > self.clipping_threshold:
                findings.append(DetectorFinding(
                    detector_type="physics",
                    issue_id=f"phys_{self.segment_id}_multi_clip",
                    issue_type="interpenetration",
                    severity=0.6,
                    confidence=0.8,
                    timestamp=self.current_timestamp,
                    description=f"Multiple collision points detected ({len(collision_points)} contacts)",
                    explainability={
                        "signals": {
                            "collision_count": len(collision_points),
                            "avg_penetration": avg_depth
                        },
                        "notes": "Complex geometry interpenetration detected"
                    },
                    affected_goals=["G-IMMERSION"],
                    player_impact=0.6
                ))
        
        return findings
    
    def _detect_ragdoll_explosion(self, depth_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect ragdoll physics explosions."""
        findings = []
        
        velocities = depth_features["velocity_estimates"]["ragdoll_parts"]
        max_velocity = max(velocities) if velocities else 0
        
        if max_velocity > self.ragdoll_velocity_threshold:
            severity = min(max_velocity / 100.0, 1.0)  # Max severity at 100 m/s
            
            findings.append(DetectorFinding(
                detector_type="physics",
                issue_id=f"phys_{self.segment_id}_ragdoll_explosion",
                issue_type="ragdoll_explosion",
                severity=severity,
                confidence=0.9,
                timestamp=self.current_timestamp,
                description=f"Ragdoll explosion detected, max velocity {max_velocity:.1f} m/s",
                explainability={
                    "signals": {
                        "max_velocity": max_velocity,
                        "all_velocities": velocities
                    },
                    "thresholds": {
                        "velocity_threshold": self.ragdoll_velocity_threshold
                    },
                    "notes": "Unrealistic ragdoll velocities indicate physics system failure"
                },
                metrics={
                    "max_ragdoll_velocity": max_velocity,
                    "avg_ragdoll_velocity": sum(velocities) / len(velocities) if velocities else 0
                },
                affected_goals=["G-IMMERSION", "G-HORROR"],
                player_impact=0.9
            ))
        
        return findings
    
    def _detect_floating_objects(self, depth_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect objects floating above ground."""
        findings = []
        
        ground_distances = depth_features["object_distances"]["objects_to_ground"]
        
        for i, distance in enumerate(ground_distances):
            if distance > self.float_distance_threshold:
                findings.append(DetectorFinding(
                    detector_type="physics",
                    issue_id=f"phys_{self.segment_id}_float_{i}",
                    issue_type="floating_object",
                    severity=0.4,
                    confidence=0.85,
                    timestamp=self.current_timestamp,
                    description=f"Object floating {distance:.2f}m above ground",
                    explainability={
                        "signals": {
                            "ground_distance": distance,
                            "object_index": i
                        },
                        "thresholds": {
                            "float_threshold": self.float_distance_threshold
                        },
                        "notes": "Object not properly grounded, likely physics constraint failure"
                    },
                    metrics={
                        "float_height": distance
                    },
                    affected_goals=["G-IMMERSION"],
                    player_impact=0.5
                ))
        
        return findings
    
    def _detect_physics_jitter(self, segment: SegmentContext) -> List[DetectorFinding]:
        """Detect physics jitter from performance metrics."""
        findings = []
        
        perf = segment.performance_metrics
        frame_variance = perf.get("frame_time_variance", 0)
        
        if frame_variance > self.jitter_threshold:
            severity = min(frame_variance / 20.0, 1.0)  # Max severity at 20ms variance
            
            # Adjust for sensitivity
            if self.sensitivity_mode == "low":
                severity *= 0.8
            elif self.sensitivity_mode == "high":
                severity *= 1.2
            
            findings.append(DetectorFinding(
                detector_type="physics",
                issue_id=f"phys_{segment.segment_id}_jitter",
                issue_type="physics_jitter",
                severity=severity,
                confidence=0.9,
                timestamp=segment.start_timestamp,
                description=f"Physics instability detected, frame variance {frame_variance:.1f}ms",
                explainability={
                    "signals": {
                        "frame_time_variance": frame_variance,
                        "avg_fps": perf.get("avg_fps", 30),
                        "min_fps": perf.get("min_fps", 30)
                    },
                    "thresholds": {
                        "jitter_threshold": self.jitter_threshold,
                        "sensitivity_mode": self.sensitivity_mode
                    },
                    "notes": "High frame time variance often correlates with physics instability"
                },
                metrics={
                    "frame_time_variance": frame_variance,
                    "avg_fps": perf.get("avg_fps", 30)
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.6 if severity > 0.7 else 0.5
            ))
        
        return findings
    
    async def analyze_batch(
        self,
        frames: List[Dict[str, Any]],
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze frames for physics issues."""
        findings = []
        
        # Store context for helper methods
        self.segment_id = segment.segment_id
        self.current_timestamp = segment.start_timestamp
        
        # Extract depth features from batch
        depth_features = self._extract_depth_features(frames)
        
        # Run different physics detectors
        findings.extend(self._detect_clipping(depth_features))
        findings.extend(self._detect_ragdoll_explosion(depth_features))
        findings.extend(self._detect_floating_objects(depth_features))
        findings.extend(self._detect_physics_jitter(segment))
        
        # Check for physics-related gameplay events
        for event in segment.gameplay_events:
            if event.get("event_type") == "physics_explosion":
                # Validate if explosion was intentional
                findings.append(DetectorFinding(
                    detector_type="physics",
                    issue_id=f"phys_{segment.segment_id}_unintended_explosion",
                    issue_type="collision_failure",
                    severity=0.7,
                    confidence=0.75,
                    timestamp=event.get("timestamp", segment.start_timestamp),
                    description="Unintended physics explosion detected",
                    explainability={
                        "signals": {
                            "event_type": "physics_explosion",
                            "gameplay_context": event.get("context", "unknown")
                        },
                        "notes": "Physics explosion without appropriate gameplay trigger"
                    },
                    affected_goals=["G-IMMERSION"],
                    player_impact=0.8
                ))
        
        return findings


class RenderingDetector(StreamingDetector):
    """
    Detects rendering artifacts (R-4D-DET-003).
    
    Issues detected:
    - Z-fighting
    - Texture streaming failures
    - LOD popping
    - Shadow acne
    - Shader compilation hitches
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Configurable thresholds
        self.z_fight_threshold = self.config.get("z_fight_threshold", 0.02)  # Screen area
        self.texture_delay_threshold = self.config.get("texture_delay_threshold", 2.0)  # seconds
        self.lod_pop_threshold = self.config.get("lod_pop_threshold", 0.1)  # Distance ratio
        self.shadow_quality_threshold = self.config.get("shadow_quality_threshold", 0.3)
        self.shader_hitch_threshold = self.config.get("shader_hitch_threshold", 100)  # ms
        self.sensitivity_mode = self.config.get("sensitivity_mode", "medium")
        
        # Tracking state
        self._texture_load_times = {}
        self._lod_transitions = []
        self._frame_times = []
        
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_issue_types": [
                "z_fighting", "texture_missing", "lod_pop",
                "shadow_acne", "shader_hitch", "culling_error"
            ],
            "requires_depth": True,
            "performance_impact": "medium",
            "configuration": {
                **self.config,
                "active_thresholds": {
                    "z_fight": self.z_fight_threshold,
                    "texture_delay": self.texture_delay_threshold,
                    "lod_pop": self.lod_pop_threshold,
                    "shadow_quality": self.shadow_quality_threshold,
                    "shader_hitch": self.shader_hitch_threshold
                }
            }
        }
    
    def _analyze_render_features(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        """Extract rendering features from frame."""
        # In production, would analyze actual frame buffer
        return {
            "z_buffer_conflicts": [
                {"area": random.uniform(0, 0.1), "location": (random.random(), random.random())}
                for _ in range(random.randint(0, 3))
            ],
            "texture_states": {
                f"texture_{i}": random.choice(["loaded", "loading", "missing"])
                for i in range(10)
            },
            "lod_levels": {
                f"object_{i}": random.randint(0, 4)
                for i in range(5)
            },
            "shadow_map_quality": random.uniform(0, 1),
            "frame_time": random.uniform(10, 50)  # ms
        }
    
    def _detect_z_fighting(self, render_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect Z-fighting artifacts."""
        findings = []
        
        z_conflicts = render_features["z_buffer_conflicts"]
        total_area = sum(c["area"] for c in z_conflicts)
        
        if total_area > self.z_fight_threshold:
            # Adjust severity based on area and sensitivity
            severity = min(total_area / 0.1, 1.0)
            if self.sensitivity_mode == "high":
                severity = min(severity * 1.2, 1.0)
            elif self.sensitivity_mode == "low":
                severity *= 0.8
            
            # Find the most prominent conflict
            largest_conflict = max(z_conflicts, key=lambda c: c["area"]) if z_conflicts else None
            
            findings.append(DetectorFinding(
                detector_type="rendering",
                issue_id=f"rend_{self.segment_id}_{self.frame_index}_zfight",
                issue_type="z_fighting",
                severity=severity,
                confidence=0.85,
                timestamp=self.current_timestamp,
                screen_coords=largest_conflict["location"] if largest_conflict else (0.5, 0.5),
                description=f"Z-fighting detected affecting {total_area*100:.1f}% of screen",
                explainability={
                    "signals": {
                        "total_conflict_area": total_area,
                        "conflict_count": len(z_conflicts),
                        "largest_area": largest_conflict["area"] if largest_conflict else 0
                    },
                    "thresholds": {
                        "z_fight_threshold": self.z_fight_threshold,
                        "sensitivity_mode": self.sensitivity_mode
                    },
                    "notes": "Z-buffer precision issues causing surface flickering"
                },
                metrics={
                    "affected_area": total_area,
                    "flicker_rate": 30.0 * len(z_conflicts)  # Estimate based on conflicts
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.6 if severity > 0.5 else 0.4
            ))
        
        return findings
    
    def _detect_texture_issues(self, render_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect texture streaming and loading issues."""
        findings = []
        
        texture_states = render_features["texture_states"]
        missing_textures = [t for t, state in texture_states.items() if state == "missing"]
        loading_textures = [t for t, state in texture_states.items() if state == "loading"]
        
        # Check for missing textures
        if missing_textures:
            findings.append(DetectorFinding(
                detector_type="rendering",
                issue_id=f"rend_{self.segment_id}_{self.frame_index}_texture_miss",
                issue_type="texture_missing",
                severity=0.7,
                confidence=0.9,
                timestamp=self.current_timestamp,
                description=f"{len(missing_textures)} textures failed to load",
                explainability={
                    "signals": {
                        "missing_count": len(missing_textures),
                        "missing_textures": missing_textures[:5]  # First 5
                    },
                    "notes": "Texture streaming system failure or memory pressure"
                },
                metrics={
                    "missing_texture_count": len(missing_textures),
                    "texture_memory_mb": 2048  # Simulated
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.8
            ))
        
        # Track loading delays
        current_time = self.current_timestamp.timestamp()
        for tex in loading_textures:
            if tex not in self._texture_load_times:
                self._texture_load_times[tex] = current_time
            elif current_time - self._texture_load_times[tex] > self.texture_delay_threshold:
                findings.append(DetectorFinding(
                    detector_type="rendering",
                    issue_id=f"rend_{self.segment_id}_{self.frame_index}_texture_delay_{tex}",
                    issue_type="texture_missing",
                    severity=0.5,
                    confidence=0.85,
                    timestamp=self.current_timestamp,
                    description=f"Texture {tex} taking too long to load",
                    explainability={
                        "signals": {
                            "load_duration": current_time - self._texture_load_times[tex],
                            "texture_id": tex
                        },
                        "thresholds": {
                            "delay_threshold": self.texture_delay_threshold
                        },
                        "notes": "Slow texture streaming impacting visual quality"
                    },
                    affected_goals=["G-IMMERSION"],
                    player_impact=0.6
                ))
        
        return findings
    
    def _detect_shader_hitches(self, render_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect shader compilation hitches."""
        findings = []
        
        frame_time = render_features["frame_time"]
        self._frame_times.append(frame_time)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)
        
        # Check for sudden frame time spikes (shader compilation)
        if len(self._frame_times) >= 5:
            avg_frame_time = sum(self._frame_times[:-1]) / (len(self._frame_times) - 1)
            if frame_time > avg_frame_time + self.shader_hitch_threshold:
                findings.append(DetectorFinding(
                    detector_type="rendering",
                    issue_id=f"rend_{self.segment_id}_{self.frame_index}_shader_hitch",
                    issue_type="shader_hitch",
                    severity=0.8,
                    confidence=0.9,
                    timestamp=self.current_timestamp,
                    description=f"Shader compilation hitch, frame time spike to {frame_time:.1f}ms",
                    explainability={
                        "signals": {
                            "frame_time": frame_time,
                            "avg_frame_time": avg_frame_time,
                            "spike_delta": frame_time - avg_frame_time
                        },
                        "thresholds": {
                            "hitch_threshold": self.shader_hitch_threshold
                        },
                        "notes": "First-time shader compilation causing frame drops"
                    },
                    metrics={
                        "hitch_duration": frame_time,
                        "baseline_frame_time": avg_frame_time
                    },
                    affected_goals=["G-IMMERSION"],
                    player_impact=0.9
                ))
        
        return findings
    
    async def analyze_frame(
        self,
        frame: Dict[str, Any],
        frame_index: int,
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze frame for rendering issues."""
        findings = []
        
        # Store context
        self.segment_id = segment.segment_id
        self.frame_index = frame_index
        self.current_timestamp = datetime.fromtimestamp(
            segment.start_timestamp.timestamp() + frame_index / 30.0
        )
        
        # Extract render features
        render_features = self._analyze_render_features(frame)
        
        # Run detectors
        findings.extend(self._detect_z_fighting(render_features))
        findings.extend(self._detect_texture_issues(render_features))
        findings.extend(self._detect_shader_hitches(render_features))
        
        # LOD popping detection (simplified)
        if random.random() < 0.05:  # 5% chance
            findings.append(DetectorFinding(
                detector_type="rendering",
                issue_id=f"rend_{segment.segment_id}_{frame_index}_lod_pop",
                issue_type="lod_pop",
                severity=0.4,
                confidence=0.8,
                timestamp=self.current_timestamp,
                description="LOD transition too abrupt, causing visual pop",
                explainability={
                    "signals": {
                        "lod_transition_distance": 50.0,  # meters
                        "lod_levels": render_features["lod_levels"]
                    },
                    "thresholds": {
                        "lod_pop_threshold": self.lod_pop_threshold
                    },
                    "notes": "LOD bias needs adjustment for smoother transitions"
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.5
            ))
        
        # Shadow quality issues
        shadow_quality = render_features["shadow_map_quality"]
        if shadow_quality < self.shadow_quality_threshold:
            findings.append(DetectorFinding(
                detector_type="rendering",
                issue_id=f"rend_{segment.segment_id}_{frame_index}_shadow",
                issue_type="shadow_acne",
                severity=0.5,
                confidence=0.75,
                timestamp=self.current_timestamp,
                description="Shadow quality below acceptable threshold",
                explainability={
                    "signals": {
                        "shadow_quality": shadow_quality,
                        "shadow_resolution": 1024  # Simulated
                    },
                    "thresholds": {
                        "quality_threshold": self.shadow_quality_threshold
                    },
                    "notes": "Shadow bias or resolution issues causing artifacts"
                },
                affected_goals=["G-IMMERSION", "G-HORROR"],
                player_impact=0.6
            ))
        
        return findings


class LightingDetector(BatchDetector):
    """
    Detects lighting and atmosphere issues (R-4D-DET-004).
    
    Issues detected:
    - Scenes too dark/bright
    - Missing horror atmosphere
    - Light leaking
    - Shadow quality issues
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Configurable thresholds
        self.dark_threshold = self.config.get("dark_threshold", 0.05)  # Avg luminance
        self.bright_threshold = self.config.get("bright_threshold", 0.85)
        self.horror_luminance_max = self.config.get("horror_luminance_max", 0.3)
        self.contrast_min = self.config.get("contrast_min", 3.0)
        self.light_leak_threshold = self.config.get("light_leak_threshold", 0.1)
        self.flicker_frequency_threshold = self.config.get("flicker_frequency_threshold", 10)  # Hz
        self.sensitivity_mode = self.config.get("sensitivity_mode", "medium")
        
        # Tracking state
        self._luminance_history = []
        self._scene_metadata = {}
        
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_issue_types": [
                "too_dark", "too_bright", "no_atmosphere",
                "light_leak", "shadow_missing", "flickering_light"
            ],
            "requires_depth": False,
            "performance_impact": "low",
            "configuration": {
                **self.config,
                "active_thresholds": {
                    "dark": self.dark_threshold,
                    "bright": self.bright_threshold,
                    "horror_max": self.horror_luminance_max,
                    "contrast_min": self.contrast_min,
                    "light_leak": self.light_leak_threshold
                }
            }
        }
    
    def _analyze_lighting_features(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract lighting features from frame batch."""
        # In production, would compute actual histograms and lighting metrics
        luminance_values = [random.uniform(0, 1) for _ in frames]
        return {
            "avg_luminance": sum(luminance_values) / len(luminance_values),
            "min_luminance": min(luminance_values),
            "max_luminance": max(luminance_values),
            "contrast_ratio": max(luminance_values) / (min(luminance_values) + 0.01),
            "dark_pixel_ratio": sum(1 for l in luminance_values if l < 0.1) / len(luminance_values),
            "bright_pixel_ratio": sum(1 for l in luminance_values if l > 0.9) / len(luminance_values),
            "luminance_variance": np.var(luminance_values),
            "histogram": {
                "low": sum(1 for l in luminance_values if l < 0.3),
                "mid": sum(1 for l in luminance_values if 0.3 <= l < 0.7),
                "high": sum(1 for l in luminance_values if l >= 0.7)
            },
            "light_sources": [
                {"position": (random.uniform(-10, 10), random.uniform(0, 5), random.uniform(-10, 10)),
                 "intensity": random.uniform(0, 1000),
                 "color_temp": random.uniform(2000, 6500)}
                for _ in range(random.randint(1, 5))
            ],
            "shadow_coverage": random.uniform(0.3, 0.8),
            "ambient_level": random.uniform(0, 0.3)
        }
    
    def _detect_visibility_issues(self, lighting_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect scenes that are too dark or too bright."""
        findings = []
        
        avg_lum = lighting_features["avg_luminance"]
        min_lum = lighting_features["min_luminance"]
        dark_ratio = lighting_features["dark_pixel_ratio"]
        
        # Too dark detection
        if avg_lum < self.dark_threshold or dark_ratio > 0.8:
            severity = 1.0 - (avg_lum / self.dark_threshold) if avg_lum < self.dark_threshold else dark_ratio
            
            findings.append(DetectorFinding(
                detector_type="lighting",
                issue_id=f"light_{self.segment_id}_dark",
                issue_type="too_dark",
                severity=severity,
                confidence=0.9,
                timestamp=self.current_timestamp,
                description="Scene visibility below acceptable threshold",
                explainability={
                    "signals": {
                        "avg_luminance": avg_lum,
                        "min_luminance": min_lum,
                        "dark_pixel_ratio": dark_ratio
                    },
                    "thresholds": {
                        "dark_threshold": self.dark_threshold,
                        "sensitivity_mode": self.sensitivity_mode
                    },
                    "notes": f"{dark_ratio*100:.1f}% of pixels below visibility threshold"
                },
                metrics={
                    "avg_luminance": avg_lum,
                    "dark_pixel_percentage": dark_ratio * 100
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.8 if severity > 0.7 else 0.6
            ))
        
        # Too bright detection
        bright_ratio = lighting_features["bright_pixel_ratio"]
        if avg_lum > self.bright_threshold or bright_ratio > 0.5:
            severity = (avg_lum - self.bright_threshold) / (1.0 - self.bright_threshold) if avg_lum > self.bright_threshold else bright_ratio
            
            findings.append(DetectorFinding(
                detector_type="lighting",
                issue_id=f"light_{self.segment_id}_bright",
                issue_type="too_bright",
                severity=severity,
                confidence=0.85,
                timestamp=self.current_timestamp,
                description="Scene overexposed, causing visibility issues",
                explainability={
                    "signals": {
                        "avg_luminance": avg_lum,
                        "max_luminance": lighting_features["max_luminance"],
                        "bright_pixel_ratio": bright_ratio
                    },
                    "thresholds": {
                        "bright_threshold": self.bright_threshold
                    },
                    "notes": "Excessive brightness reducing visual comfort"
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.6
            ))
        
        return findings
    
    def _detect_horror_atmosphere(self, lighting_features: Dict[str, Any], segment: SegmentContext) -> List[DetectorFinding]:
        """Check if horror scenes have appropriate atmosphere."""
        findings = []
        
        # Determine if this should be a horror scene
        is_horror_scene = (
            "horror" in segment.level_name.lower() or
            "dark" in segment.level_name.lower() or
            "scary" in segment.level_name.lower() or
            any(e.get("event_type") == "horror_sequence" for e in segment.gameplay_events)
        )
        
        if not is_horror_scene:
            return findings
        
        avg_lum = lighting_features["avg_luminance"]
        contrast = lighting_features["contrast_ratio"]
        shadow_coverage = lighting_features["shadow_coverage"]
        
        # Horror scenes should be dark with high contrast
        if avg_lum > self.horror_luminance_max:
            findings.append(DetectorFinding(
                detector_type="lighting",
                issue_id=f"light_{segment.segment_id}_no_atmosphere",
                issue_type="no_atmosphere",
                severity=0.7,
                confidence=0.8,
                timestamp=self.current_timestamp,
                description="Horror scene too bright, lacking appropriate atmosphere",
                explainability={
                    "signals": {
                        "avg_luminance": avg_lum,
                        "expected_max": self.horror_luminance_max,
                        "shadow_coverage": shadow_coverage
                    },
                    "thresholds": {
                        "horror_luminance_max": self.horror_luminance_max
                    },
                    "notes": "Horror scenes require darker, more atmospheric lighting"
                },
                metrics={
                    "avg_luminance": avg_lum,
                    "contrast_ratio": contrast
                },
                affected_goals=["G-HORROR"],
                player_impact=0.8
            ))
        
        # Check contrast for dramatic lighting
        if contrast < self.contrast_min:
            findings.append(DetectorFinding(
                detector_type="lighting",
                issue_id=f"light_{segment.segment_id}_low_contrast",
                issue_type="no_atmosphere",
                severity=0.5,
                confidence=0.75,
                timestamp=self.current_timestamp,
                description="Insufficient lighting contrast for horror atmosphere",
                explainability={
                    "signals": {
                        "contrast_ratio": contrast,
                        "expected_min": self.contrast_min
                    },
                    "notes": "Horror scenes benefit from dramatic lighting contrasts"
                },
                affected_goals=["G-HORROR"],
                player_impact=0.6
            ))
        
        return findings
    
    def _detect_lighting_artifacts(self, lighting_features: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect light leaking and other artifacts."""
        findings = []
        
        # Light leak detection (simplified)
        # In production, would check for light bleeding through geometry
        variance = lighting_features["luminance_variance"]
        if variance > 0.5 and random.random() < 0.1:  # High variance might indicate leaks
            findings.append(DetectorFinding(
                detector_type="lighting",
                issue_id=f"light_{self.segment_id}_leak",
                issue_type="light_leak",
                severity=0.6,
                confidence=0.7,
                timestamp=self.current_timestamp,
                description="Light bleeding through geometry detected",
                explainability={
                    "signals": {
                        "luminance_variance": variance,
                        "suspicious_bright_spots": 3  # Simulated
                    },
                    "notes": "Light passing through solid objects, breaking immersion"
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.6
            ))
        
        # Flickering light detection
        if len(self._luminance_history) >= 10:
            # Check for rapid changes
            recent_changes = [
                abs(self._luminance_history[i] - self._luminance_history[i-1])
                for i in range(1, len(self._luminance_history))
            ]
            flicker_score = sum(1 for c in recent_changes if c > 0.2) / len(recent_changes)
            
            if flicker_score > 0.3:  # 30% of frames have significant changes
                findings.append(DetectorFinding(
                    detector_type="lighting",
                    issue_id=f"light_{self.segment_id}_flicker",
                    issue_type="flickering_light",
                    severity=0.5,
                    confidence=0.85,
                    timestamp=self.current_timestamp,
                    description="Unintended light flickering detected",
                    explainability={
                        "signals": {
                            "flicker_score": flicker_score,
                            "change_magnitude": max(recent_changes)
                        },
                        "notes": "Rapid lighting changes without gameplay justification"
                    },
                    affected_goals=["G-IMMERSION"],
                    player_impact=0.5
                ))
        
        # Missing shadows
        shadow_coverage = lighting_features["shadow_coverage"]
        if shadow_coverage < 0.2 and len(lighting_features["light_sources"]) > 0:
            findings.append(DetectorFinding(
                detector_type="lighting",
                issue_id=f"light_{self.segment_id}_no_shadows",
                issue_type="shadow_missing",
                severity=0.4,
                confidence=0.8,
                timestamp=self.current_timestamp,
                description="Scene lacks proper shadow coverage",
                explainability={
                    "signals": {
                        "shadow_coverage": shadow_coverage,
                        "light_source_count": len(lighting_features["light_sources"])
                    },
                    "notes": "Insufficient shadows for number of light sources"
                },
                affected_goals=["G-IMMERSION", "G-HORROR"],
                player_impact=0.5
            ))
        
        return findings
    
    async def analyze_batch(
        self,
        frames: List[Dict[str, Any]],
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze frames for lighting issues."""
        findings = []
        
        # Store context
        self.segment_id = segment.segment_id
        self.current_timestamp = segment.start_timestamp
        
        # Extract lighting features
        lighting_features = self._analyze_lighting_features(frames)
        
        # Update history
        self._luminance_history.append(lighting_features["avg_luminance"])
        if len(self._luminance_history) > 30:
            self._luminance_history.pop(0)
        
        # Run detectors
        findings.extend(self._detect_visibility_issues(lighting_features))
        findings.extend(self._detect_horror_atmosphere(lighting_features, segment))
        findings.extend(self._detect_lighting_artifacts(lighting_features))
        
        return findings


class PerformanceDetector(BatchDetector):
    """
    Detects performance issues (R-4D-DET-005).
    
    Issues detected:
    - Frame rate drops
    - Frame pacing issues
    - Input lag spikes
    - Memory pressure indicators
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Platform-specific thresholds
        platform = self.config.get("platform", "pc")
        self.target_fps = {
            "pc": 60,
            "console": 30,
            "mobile": 30
        }.get(platform, 60)
        
        self.fps_drop_threshold = self.config.get("fps_drop_threshold", self.target_fps * 0.5)
        self.frame_variance_threshold = self.config.get("frame_variance_threshold", 5.0)  # ms
        self.input_lag_threshold = self.config.get("input_lag_threshold", 100)  # ms
        self.memory_pressure_threshold = self.config.get("memory_pressure_threshold", 0.9)  # 90%
        self.build_type = self.config.get("build_type", "release")  # dev/qa/staging/release
        self.sensitivity_mode = self.config.get("sensitivity_mode", "medium")
        
        # Tracking state
        self._fps_history = []
        self._frame_time_history = []
        self._memory_history = []
        
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_issue_types": [
                "fps_drop", "frame_pacing", "input_lag",
                "memory_pressure", "thermal_throttling"
            ],
            "requires_depth": False,
            "performance_impact": "low",
            "configuration": {
                **self.config,
                "platform": self.config.get("platform", "pc"),
                "target_fps": self.target_fps,
                "active_thresholds": {
                    "fps_drop": self.fps_drop_threshold,
                    "frame_variance": self.frame_variance_threshold,
                    "input_lag": self.input_lag_threshold,
                    "memory_pressure": self.memory_pressure_threshold
                }
            }
        }
    
    def _analyze_performance_metrics(self, segment: SegmentContext) -> Dict[str, Any]:
        """Extract and enhance performance metrics."""
        perf = segment.performance_metrics
        
        # Simulate additional performance data
        frame_times = [random.uniform(10, 50) for _ in range(30)]
        
        return {
            "avg_fps": perf.get("avg_fps", self.target_fps),
            "min_fps": perf.get("min_fps", self.target_fps),
            "max_fps": perf.get("max_fps", self.target_fps),
            "frame_time_variance": np.var(frame_times),
            "frame_times": frame_times,
            "percentile_95": np.percentile(frame_times, 95),
            "percentile_99": np.percentile(frame_times, 99),
            "input_lag": random.uniform(50, 150),  # ms
            "memory_used": perf.get("memory_used_mb", random.uniform(1000, 4000)),
            "memory_total": perf.get("memory_total_mb", 4096),
            "gpu_temp": random.uniform(60, 85),  # Celsius
            "cpu_usage": random.uniform(0.3, 0.9),
            "draw_calls": perf.get("draw_calls", random.randint(1000, 8000)),
            "triangles": perf.get("triangles", random.randint(100000, 2000000))
        }
    
    def _detect_fps_drops(self, perf_metrics: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect frame rate issues."""
        findings = []
        
        min_fps = perf_metrics["min_fps"]
        avg_fps = perf_metrics["avg_fps"]
        
        # Update history
        self._fps_history.append(min_fps)
        if len(self._fps_history) > 60:  # Keep 2 seconds worth
            self._fps_history.pop(0)
        
        # Check for sustained drops
        if min_fps < self.fps_drop_threshold:
            drop_ratio = min_fps / self.target_fps
            severity = 1.0 - drop_ratio
            
            # Adjust severity for build type
            if self.build_type == "dev":
                severity *= 0.7  # Less critical in dev builds
            elif self.build_type == "release":
                severity *= 1.2  # More critical in release
            
            severity = min(severity, 1.0)
            
            # Check if drop is sustained
            recent_low_count = sum(1 for fps in self._fps_history[-10:] if fps < self.fps_drop_threshold)
            is_sustained = recent_low_count > 5
            
            findings.append(DetectorFinding(
                detector_type="performance",
                issue_id=f"perf_{self.segment_id}_fps_drop",
                issue_type="fps_drop",
                severity=severity,
                confidence=0.95,
                timestamp=self.current_timestamp,
                description=f"Frame rate dropped to {min_fps} FPS ({drop_ratio*100:.1f}% of target)",
                explainability={
                    "signals": {
                        "min_fps": min_fps,
                        "avg_fps": avg_fps,
                        "target_fps": self.target_fps,
                        "is_sustained": is_sustained
                    },
                    "thresholds": {
                        "fps_drop_threshold": self.fps_drop_threshold,
                        "platform": self.config.get("platform", "pc"),
                        "build_type": self.build_type
                    },
                    "notes": f"{'Sustained' if is_sustained else 'Transient'} FPS drop detected"
                },
                metrics={
                    "min_fps": min_fps,
                    "avg_fps": avg_fps,
                    "drop_duration": recent_low_count / 30.0  # seconds
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.9 if severity > 0.7 else 0.7
            ))
        
        return findings
    
    def _detect_frame_pacing(self, perf_metrics: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect frame timing issues."""
        findings = []
        
        variance = perf_metrics["frame_time_variance"]
        p95 = perf_metrics["percentile_95"]
        p99 = perf_metrics["percentile_99"]
        
        if variance > self.frame_variance_threshold:
            severity = min(variance / 20.0, 1.0)  # Max severity at 20ms variance
            
            # Adjust for sensitivity
            if self.sensitivity_mode == "high":
                severity = min(severity * 1.2, 1.0)
            elif self.sensitivity_mode == "low":
                severity *= 0.8
            
            findings.append(DetectorFinding(
                detector_type="performance",
                issue_id=f"perf_{self.segment_id}_pacing",
                issue_type="frame_pacing",
                severity=severity,
                confidence=0.9,
                timestamp=self.current_timestamp,
                description=f"Irregular frame pacing, variance {variance:.1f}ms",
                explainability={
                    "signals": {
                        "frame_time_variance": variance,
                        "percentile_95": p95,
                        "percentile_99": p99,
                        "target_frame_time": 1000.0 / self.target_fps
                    },
                    "thresholds": {
                        "variance_threshold": self.frame_variance_threshold,
                        "sensitivity_mode": self.sensitivity_mode
                    },
                    "notes": "High frame time variance causes perceptible stuttering"
                },
                metrics={
                    "frame_time_variance": variance,
                    "percentile_95": p95,
                    "percentile_99": p99
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.7 if severity > 0.6 else 0.5
            ))
        
        return findings
    
    def _detect_input_lag(self, perf_metrics: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect input responsiveness issues."""
        findings = []
        
        input_lag = perf_metrics["input_lag"]
        
        if input_lag > self.input_lag_threshold:
            severity = min((input_lag - self.input_lag_threshold) / 100.0, 1.0)
            
            findings.append(DetectorFinding(
                detector_type="performance",
                issue_id=f"perf_{self.segment_id}_input_lag",
                issue_type="input_lag",
                severity=severity,
                confidence=0.85,
                timestamp=self.current_timestamp,
                description=f"High input latency detected: {input_lag:.0f}ms",
                explainability={
                    "signals": {
                        "input_lag": input_lag,
                        "frame_times": perf_metrics["percentile_95"],
                        "cpu_usage": perf_metrics["cpu_usage"]
                    },
                    "thresholds": {
                        "input_lag_threshold": self.input_lag_threshold
                    },
                    "notes": "Input lag above 100ms significantly impacts gameplay feel"
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.8
            ))
        
        return findings
    
    def _detect_resource_pressure(self, perf_metrics: Dict[str, Any]) -> List[DetectorFinding]:
        """Detect memory and thermal issues."""
        findings = []
        
        # Memory pressure
        memory_ratio = perf_metrics["memory_used"] / perf_metrics["memory_total"]
        if memory_ratio > self.memory_pressure_threshold:
            findings.append(DetectorFinding(
                detector_type="performance",
                issue_id=f"perf_{self.segment_id}_memory",
                issue_type="memory_pressure",
                severity=0.7,
                confidence=0.9,
                timestamp=self.current_timestamp,
                description=f"High memory usage: {memory_ratio*100:.1f}% of available",
                explainability={
                    "signals": {
                        "memory_used_mb": perf_metrics["memory_used"],
                        "memory_total_mb": perf_metrics["memory_total"],
                        "usage_ratio": memory_ratio
                    },
                    "thresholds": {
                        "memory_pressure_threshold": self.memory_pressure_threshold
                    },
                    "notes": "High memory usage can lead to stuttering and crashes"
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.7
            ))
        
        # Thermal throttling
        gpu_temp = perf_metrics["gpu_temp"]
        if gpu_temp > 80:  # Celsius
            min_fps = perf_metrics["min_fps"]
            avg_fps = perf_metrics["avg_fps"]
            findings.append(DetectorFinding(
                detector_type="performance",
                issue_id=f"perf_{self.segment_id}_thermal",
                issue_type="thermal_throttling",
                severity=0.6,
                confidence=0.8,
                timestamp=self.current_timestamp,
                description=f"GPU temperature elevated: {gpu_temp}°C",
                explainability={
                    "signals": {
                        "gpu_temp": gpu_temp,
                        "fps_correlation": min_fps < avg_fps * 0.7
                    },
                    "notes": "High temperatures may cause thermal throttling"
                },
                affected_goals=["G-IMMERSION"],
                player_impact=0.6
            ))
        
        return findings
    
    async def analyze_batch(
        self,
        frames: List[Dict[str, Any]],
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze performance metrics."""
        findings = []
        
        # Store context
        self.segment_id = segment.segment_id
        self.current_timestamp = segment.start_timestamp
        
        # Analyze performance
        perf_metrics = self._analyze_performance_metrics(segment)
        
        # Run detectors
        findings.extend(self._detect_fps_drops(perf_metrics))
        findings.extend(self._detect_frame_pacing(perf_metrics))
        findings.extend(self._detect_input_lag(perf_metrics))
        findings.extend(self._detect_resource_pressure(perf_metrics))
        
        return findings


class FlowDetector(BatchDetector):
    """
    Detects gameplay flow issues (R-4D-DET-006).
    
    Issues detected:
    - Soft locks
    - Stuck states
    - Progress blockers
    - Interaction failures
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Configurable thresholds
        self.death_rate_threshold = self.config.get("death_rate_threshold", 1.0)  # deaths per minute
        self.stuck_duration_threshold = self.config.get("stuck_duration_threshold", 30)  # seconds
        self.interaction_retry_threshold = self.config.get("interaction_retry_threshold", 5)
        self.puzzle_time_threshold = self.config.get("puzzle_time_threshold", 300)  # 5 minutes
        self.movement_threshold = self.config.get("movement_threshold", 5.0)  # meters
        self.sensitivity_mode = self.config.get("sensitivity_mode", "medium")
        
        # Tracking state
        self._position_history = []
        self._interaction_history = {}
        self._death_locations = []
        
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_issue_types": [
                "soft_lock", "stuck_player", "progress_blocked",
                "interaction_failed", "objective_unclear"
            ],
            "requires_depth": False,
            "performance_impact": "low",
            "configuration": {
                **self.config,
                "active_thresholds": {
                    "death_rate": self.death_rate_threshold,
                    "stuck_duration": self.stuck_duration_threshold,
                    "interaction_retry": self.interaction_retry_threshold,
                    "puzzle_time": self.puzzle_time_threshold,
                    "movement": self.movement_threshold
                }
            }
        }
    
    def _analyze_movement_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract movement patterns from gameplay events."""
        positions = []
        for event in events:
            if "position" in event:
                positions.append(event["position"])
        
        # Simulate position data if none provided
        if not positions:
            positions = [
                (random.uniform(-10, 10), random.uniform(-10, 10), 0)
                for _ in range(10)
            ]
        
        # Calculate movement statistics
        total_distance = 0
        if len(positions) > 1:
            for i in range(1, len(positions)):
                dist = math.sqrt(
                    sum((a - b) ** 2 for a, b in zip(positions[i], positions[i-1]))
                )
                total_distance += dist
        
        # Detect if player is stuck in small area
        if positions:
            x_coords = [p[0] for p in positions]
            y_coords = [p[1] for p in positions]
            movement_radius = max(
                max(x_coords) - min(x_coords),
                max(y_coords) - min(y_coords)
            ) / 2
        else:
            movement_radius = 0
        
        return {
            "positions": positions,
            "total_distance": total_distance,
            "movement_radius": movement_radius,
            "avg_speed": total_distance / len(positions) if positions else 0
        }
    
    def _detect_soft_locks(self, events: List[Dict[str, Any]], segment: SegmentContext) -> List[DetectorFinding]:
        """Detect soft lock situations."""
        findings = []
        
        # Analyze deaths
        death_events = [e for e in events if e.get("event_type") == "death"]
        if death_events:
            deaths_per_minute = len(death_events) / (segment.duration_seconds / 60)
            
            if deaths_per_minute > self.death_rate_threshold:
                # Check if deaths are in same location (definite soft lock indicator)
                death_positions = [e.get("position", (0, 0, 0)) for e in death_events]
                unique_positions = len(set(death_positions))
                
                severity = min(deaths_per_minute / 3.0, 1.0)  # Max severity at 3 deaths/min
                if unique_positions == 1:  # All deaths in same spot
                    severity = min(severity * 1.5, 1.0)
                
                findings.append(DetectorFinding(
                    detector_type="flow",
                    issue_id=f"flow_{segment.segment_id}_softlock_deaths",
                    issue_type="soft_lock",
                    severity=severity,
                    confidence=0.9 if unique_positions == 1 else 0.8,
                    timestamp=segment.start_timestamp,
                    description=f"High death rate ({deaths_per_minute:.1f}/min) indicates soft lock",
                    explainability={
                        "signals": {
                            "death_count": len(death_events),
                            "deaths_per_minute": deaths_per_minute,
                            "unique_death_locations": unique_positions,
                            "segment_duration": segment.duration_seconds
                        },
                        "thresholds": {
                            "death_rate_threshold": self.death_rate_threshold
                        },
                        "notes": "Repeated deaths in same location strongly indicate soft lock"
                    },
                    metrics={
                        "death_count": len(death_events),
                        "deaths_per_minute": deaths_per_minute
                    },
                    affected_goals=["G-IMMERSION", "G-LONGTERM"],
                    player_impact=0.9
                ))
        
        # Check for stuck player (no movement)
        movement = self._analyze_movement_patterns(events)
        if movement["movement_radius"] < self.movement_threshold and segment.duration_seconds > self.stuck_duration_threshold:
            findings.append(DetectorFinding(
                detector_type="flow",
                issue_id=f"flow_{segment.segment_id}_stuck",
                issue_type="stuck_player",
                severity=0.7,
                confidence=0.85,
                timestamp=segment.start_timestamp,
                description=f"Player stuck in {movement['movement_radius']:.1f}m radius for {segment.duration_seconds}s",
                explainability={
                    "signals": {
                        "movement_radius": movement["movement_radius"],
                        "duration": segment.duration_seconds,
                        "total_distance": movement["total_distance"]
                    },
                    "thresholds": {
                        "movement_threshold": self.movement_threshold,
                        "stuck_duration_threshold": self.stuck_duration_threshold
                    },
                    "notes": "Minimal movement over extended period indicates stuck state"
                },
                affected_goals=["G-IMMERSION", "G-LONGTERM"],
                player_impact=0.8
            ))
        
        return findings
    
    def _detect_progress_blockers(self, events: List[Dict[str, Any]], segment: SegmentContext) -> List[DetectorFinding]:
        """Detect progress blocking issues."""
        findings = []
        
        # Analyze puzzle attempts
        puzzle_starts = [e for e in events if e.get("event_type") == "puzzle_start"]
        puzzle_completes = [e for e in events if e.get("event_type") == "puzzle_complete"]
        puzzle_resets = [e for e in events if e.get("event_type") == "puzzle_reset"]
        
        if puzzle_starts and not puzzle_completes:
            puzzle_duration = segment.duration_seconds
            reset_count = len(puzzle_resets)
            
            if puzzle_duration > self.puzzle_time_threshold:
                severity = min(puzzle_duration / 600.0, 1.0)  # Max severity at 10 minutes
                
                findings.append(DetectorFinding(
                    detector_type="flow",
                    issue_id=f"flow_{segment.segment_id}_puzzle_blocked",
                    issue_type="progress_blocked",
                    severity=severity,
                    confidence=0.8,
                    timestamp=segment.start_timestamp,
                    description=f"Puzzle unsolved after {puzzle_duration:.0f}s with {reset_count} resets",
                    explainability={
                        "signals": {
                            "puzzle_duration": puzzle_duration,
                            "reset_count": reset_count,
                            "attempt_count": len(puzzle_starts)
                        },
                        "thresholds": {
                            "puzzle_time_threshold": self.puzzle_time_threshold
                        },
                        "notes": "Extended puzzle time suggests difficulty spike or unclear mechanics"
                    },
                    metrics={
                        "puzzle_attempts": len(puzzle_starts),
                        "time_in_puzzle": puzzle_duration
                    },
                    affected_goals=["G-LONGTERM"],
                    player_impact=0.7
                ))
        
        # Check for quest/objective issues
        quest_starts = [e for e in events if e.get("event_type") == "quest_start"]
        quest_abandons = [e for e in events if e.get("event_type") == "quest_abandon"]
        
        if quest_abandons and quest_starts:
            abandon_rate = len(quest_abandons) / len(quest_starts)
            if abandon_rate > 0.5:
                findings.append(DetectorFinding(
                    detector_type="flow",
                    issue_id=f"flow_{segment.segment_id}_quest_unclear",
                    issue_type="objective_unclear",
                    severity=0.6,
                    confidence=0.75,
                    timestamp=segment.start_timestamp,
                    description=f"High quest abandon rate ({abandon_rate*100:.0f}%)",
                    explainability={
                        "signals": {
                            "quest_starts": len(quest_starts),
                            "quest_abandons": len(quest_abandons),
                            "abandon_rate": abandon_rate
                        },
                        "notes": "Players abandoning quests suggests unclear objectives"
                    },
                    affected_goals=["G-LONGTERM"],
                    player_impact=0.6
                ))
        
        return findings
    
    def _detect_interaction_failures(self, events: List[Dict[str, Any]], segment: SegmentContext) -> List[DetectorFinding]:
        """Detect interaction system failures."""
        findings = []
        
        # Track interaction attempts
        interaction_events = [e for e in events if "interaction" in e.get("event_type", "")]
        
        # Group by interaction target
        interaction_targets = {}
        for event in interaction_events:
            target = event.get("target", "unknown")
            if target not in interaction_targets:
                interaction_targets[target] = {"attempts": 0, "successes": 0}
            
            interaction_targets[target]["attempts"] += 1
            if event.get("success", False):
                interaction_targets[target]["successes"] += 1
        
        # Check for repeated failed interactions
        for target, stats in interaction_targets.items():
            if stats["attempts"] > self.interaction_retry_threshold and stats["successes"] == 0:
                findings.append(DetectorFinding(
                    detector_type="flow",
                    issue_id=f"flow_{segment.segment_id}_interact_fail_{target}",
                    issue_type="interaction_failed",
                    severity=0.7,
                    confidence=0.85,
                    timestamp=segment.start_timestamp,
                    description=f"Repeated interaction failures with {target}",
                    explainability={
                        "signals": {
                            "target": target,
                            "attempts": stats["attempts"],
                            "successes": stats["successes"]
                        },
                        "thresholds": {
                            "retry_threshold": self.interaction_retry_threshold
                        },
                        "notes": "Multiple failed attempts suggest broken interaction"
                    },
                    metrics={
                        "interaction_attempts": stats["attempts"],
                        "success_rate": 0
                    },
                    affected_goals=["G-IMMERSION"],
                    player_impact=0.7
                ))
        
        return findings
    
    async def analyze_batch(
        self,
        frames: List[Dict[str, Any]],
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze gameplay flow."""
        findings = []
        
        # Store context
        self.segment_id = segment.segment_id
        self.current_timestamp = segment.start_timestamp
        
        events = segment.gameplay_events
        
        # Run flow detectors
        findings.extend(self._detect_soft_locks(events, segment))
        findings.extend(self._detect_progress_blockers(events, segment))
        findings.extend(self._detect_interaction_failures(events, segment))
        
        return findings


# Registry of all detectors
DETECTOR_CLASSES = {
    "animation": AnimationDetector,
    "physics": PhysicsDetector,
    "rendering": RenderingDetector,
    "lighting": LightingDetector,
    "performance": PerformanceDetector,
    "flow": FlowDetector
}


def create_detector(detector_type: str, config: Optional[Dict[str, Any]] = None) -> VisionDetector:
    """Create a detector instance by type."""
    detector_class = DETECTOR_CLASSES.get(detector_type)
    if not detector_class:
        raise ValueError(f"Unknown detector type: {detector_type}")
    
    return detector_class(config=config)
