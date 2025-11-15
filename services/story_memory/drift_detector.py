"""
Drift & Conflict Detector - Analyzes story state for narrative drift and conflicts.
"""
import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

import asyncpg
from loguru import logger
from nats.aio.client import Client as NATS

from .story_schemas import (
    DriftType, DriftSeverity, DriftMetrics, StoryConflict,
    ConflictSeverity, ArcRole
)
from .story_state_manager import StoryStateManager


class DriftDetector:
    """Detects narrative drift and conflicts in player stories."""
    
    # Drift thresholds
    THRESHOLDS = {
        'time_without_main_arc': timedelta(hours=2),  # No main arc progress
        'tangential_quest_ratio': 0.3,  # 30% tangential quests
        'off_theme_time_ratio': 0.25,   # 25% time in off-theme activities
        'theme_consistency_min': 0.7,    # 70% theme consistency required
    }
    
    # Off-theme activities for The Body Broker
    OFF_THEME_ACTIVITIES = {
        'racing', 'fishing', 'gambling', 'sports', 'farming',
        'cooking', 'dating_sim', 'puzzle_solving'
    }
    
    def __init__(
        self,
        nats_client: NATS,
        story_state_manager: StoryStateManager,
        postgres_pool: asyncpg.Pool
    ):
        self.nc = nats_client
        self.story_manager = story_state_manager
        self.postgres = postgres_pool
        self._analysis_cache: Dict[str, datetime] = {}
        self._analysis_interval = timedelta(minutes=30)
    
    async def start(self):
        """Start the drift detection background task."""
        asyncio.create_task(self._periodic_drift_check())
        logger.info("Drift detector started")
    
    async def check_drift(
        self, 
        player_id: UUID,
        window_hours: int = 3,
        force: bool = False
    ) -> Optional[DriftMetrics]:
        """
        Check for narrative drift in recent gameplay.
        
        Args:
            player_id: Player to check
            window_hours: Hours of recent gameplay to analyze
            force: Skip cache and force fresh analysis
            
        Returns:
            DriftMetrics if drift detected, None otherwise
        """
        # Check cache unless forced
        cache_key = str(player_id)
        if not force and cache_key in self._analysis_cache:
            last_check = self._analysis_cache[cache_key]
            if datetime.utcnow() - last_check < self._analysis_interval:
                return None
        
        logger.info(f"Analyzing drift for player {player_id} (last {window_hours} hours)")
        
        # Run all drift checks
        time_drift = await self._check_time_allocation_drift(player_id, window_hours)
        quest_drift = await self._check_quest_allocation_drift(player_id, window_hours)
        theme_drift = await self._check_theme_consistency(player_id, window_hours)
        
        # Determine overall drift
        drift_scores = []
        severities = []
        
        if time_drift:
            drift_scores.append(time_drift[1])
            severities.append(time_drift[2])
        
        if quest_drift:
            drift_scores.append(quest_drift[1])
            severities.append(quest_drift[2])
        
        if theme_drift:
            drift_scores.append(theme_drift[1])
            severities.append(theme_drift[2])
        
        if not drift_scores:
            self._analysis_cache[cache_key] = datetime.utcnow()
            return None
        
        # Calculate overall metrics
        overall_score = max(drift_scores)
        overall_severity = max(severities, key=lambda s: ['minor', 'moderate', 'major'].index(s))
        
        # Build drift metrics
        metrics = DriftMetrics(
            drift_type=DriftType.TIME_ALLOCATION if time_drift else DriftType.QUEST_ALLOCATION,
            severity=overall_severity,
            drift_score=overall_score
        )
        
        # Add detailed breakdowns
        if time_drift:
            metrics.time_allocation = time_drift[0]
        if quest_drift:
            metrics.quest_allocation = quest_drift[0]
        if theme_drift:
            metrics.theme_consistency = theme_drift[0]
        
        # Generate remediation
        metrics.recommended_correction = self._generate_correction(
            metrics, player_id
        )
        metrics.canonical_reminder = (
            "Core game loop: Kill → Harvest → Negotiate → Get Drugs → Build Empire. "
            "Dark fantasy body brokering, not side activities."
        )
        
        # Store drift alert
        await self._store_drift_alert(player_id, metrics)
        
        # Emit drift event
        await self._emit_drift_event(player_id, metrics)
        
        self._analysis_cache[cache_key] = datetime.utcnow()
        return metrics
    
    async def check_conflicts(
        self,
        player_id: UUID
    ) -> List[StoryConflict]:
        """Check for narrative conflicts and inconsistencies."""
        conflicts = []
        
        # Check NPC state conflicts
        npc_conflicts = await self._check_npc_state_conflicts(player_id)
        conflicts.extend(npc_conflicts)
        
        # Check quest availability conflicts
        quest_conflicts = await self._check_quest_logic_conflicts(player_id)
        conflicts.extend(quest_conflicts)
        
        # Check world state conflicts
        world_conflicts = await self._check_world_state_conflicts(player_id)
        conflicts.extend(world_conflicts)
        
        # Store and emit conflicts
        for conflict in conflicts:
            await self._store_conflict(player_id, conflict)
            await self._emit_conflict_event(player_id, conflict)
        
        return conflicts
    
    async def _periodic_drift_check(self):
        """Periodically check all active players for drift."""
        while True:
            try:
                # Get active players (those with recent events)
                async with self.postgres.acquire() as conn:
                    active_players = await conn.fetch(
                        """
                        SELECT DISTINCT player_id
                        FROM story_events
                        WHERE created_at > $1
                        """,
                        datetime.utcnow() - timedelta(hours=24)
                    )
                
                for row in active_players:
                    player_id = row['player_id']
                    try:
                        await self.check_drift(player_id)
                        await self.check_conflicts(player_id)
                    except Exception as e:
                        logger.error(f"Error checking drift for player {player_id}: {e}")
                
            except Exception as e:
                logger.error(f"Error in periodic drift check: {e}")
            
            # Wait before next check
            await asyncio.sleep(1800)  # 30 minutes
    
    async def _check_time_allocation_drift(
        self,
        player_id: UUID,
        window_hours: int
    ) -> Optional[Tuple[Dict[str, float], float, DriftSeverity]]:
        """Check time allocation across activity types."""
        window_start = datetime.utcnow() - timedelta(hours=window_hours)
        
        async with self.postgres.acquire() as conn:
            # Get time allocation from events
            # This is simplified - real implementation would track actual time
            activities = await conn.fetch(
                """
                SELECT 
                    event_data->>'activity_type' as activity,
                    COUNT(*) as count
                FROM story_events
                WHERE player_id = $1 
                    AND created_at > $2
                    AND event_type = 'activity_logged'
                GROUP BY event_data->>'activity_type'
                """,
                player_id, window_start
            )
            
            if not activities:
                return None
            
            # Calculate distribution
            total = sum(row['count'] for row in activities)
            distribution = {
                row['activity']: row['count'] / total
                for row in activities
            }
            
            # Check for off-theme dominance
            off_theme_ratio = sum(
                ratio for activity, ratio in distribution.items()
                if activity in self.OFF_THEME_ACTIVITIES
            )
            
            if off_theme_ratio > self.THRESHOLDS['off_theme_time_ratio']:
                severity = self._calculate_severity(
                    off_theme_ratio, 
                    self.THRESHOLDS['off_theme_time_ratio']
                )
                return distribution, off_theme_ratio, severity
        
        return None
    
    async def _check_quest_allocation_drift(
        self,
        player_id: UUID,
        window_hours: int
    ) -> Optional[Tuple[Dict[str, float], float, DriftSeverity]]:
        """Check quest type distribution."""
        window_start = datetime.utcnow() - timedelta(hours=window_hours)
        
        async with self.postgres.acquire() as conn:
            # Get quest completions by type
            quests = await conn.fetch(
                """
                SELECT 
                    event_data->>'quest_type' as quest_type,
                    COUNT(*) as count
                FROM story_events
                WHERE player_id = $1 
                    AND created_at > $2
                    AND event_type = 'quest_completed'
                GROUP BY event_data->>'quest_type'
                """,
                player_id, window_start
            )
            
            if not quests:
                return None
            
            # Calculate distribution
            total = sum(row['count'] for row in quests)
            distribution = defaultdict(float)
            
            for row in quests:
                quest_type = row['quest_type'] or 'unknown'
                distribution[quest_type] = row['count'] / total
            
            # Check tangential quest ratio
            tangential_ratio = distribution.get('tangential', 0.0)
            
            if tangential_ratio > self.THRESHOLDS['tangential_quest_ratio']:
                severity = self._calculate_severity(
                    tangential_ratio,
                    self.THRESHOLDS['tangential_quest_ratio']
                )
                return dict(distribution), tangential_ratio, severity
        
        return None
    
    async def _check_theme_consistency(
        self,
        player_id: UUID,
        window_hours: int
    ) -> Optional[Tuple[float, float, DriftSeverity]]:
        """Check thematic consistency of recent content."""
        # Simplified version - real implementation would use embeddings
        # and semantic similarity against canonical lore
        
        # For now, return None (no drift detected)
        return None
    
    async def _check_npc_state_conflicts(
        self,
        player_id: UUID
    ) -> List[StoryConflict]:
        """Check for NPC state inconsistencies."""
        conflicts = []
        
        # This would check:
        # - NPCs marked dead but appearing in quests
        # - NPCs with conflicting relationship states
        # - NPCs in impossible locations
        
        return conflicts
    
    async def _check_quest_logic_conflicts(
        self,
        player_id: UUID
    ) -> List[StoryConflict]:
        """Check for quest logic issues."""
        conflicts = []
        
        # This would check:
        # - Prerequisites not met for completed quests
        # - Repeated introductory quests
        # - Mutually exclusive quests both completed
        
        return conflicts
    
    async def _check_world_state_conflicts(
        self,
        player_id: UUID
    ) -> List[StoryConflict]:
        """Check story memory vs world state."""
        conflicts = []
        
        # This would check:
        # - Destroyed locations appearing in story
        # - Territory control mismatches
        # - Resource availability conflicts
        
        return conflicts
    
    def _calculate_severity(
        self, 
        actual_value: float, 
        threshold: float
    ) -> DriftSeverity:
        """Calculate drift severity based on how far over threshold."""
        ratio = actual_value / threshold
        
        if ratio < 1.5:
            return DriftSeverity.MINOR
        elif ratio < 2.0:
            return DriftSeverity.MODERATE
        else:
            return DriftSeverity.MAJOR
    
    def _generate_correction(
        self, 
        metrics: DriftMetrics,
        player_id: UUID
    ) -> str:
        """Generate correction recommendation."""
        corrections = []
        
        if metrics.quest_allocation and metrics.quest_allocation.get('tangential', 0) > 0.3:
            corrections.append(
                "Increase main story quest opportunities. "
                "Reduce tangential quest generation."
            )
        
        if metrics.time_allocation:
            off_theme = [
                activity for activity in self.OFF_THEME_ACTIVITIES
                if metrics.time_allocation.get(activity, 0) > 0.1
            ]
            if off_theme:
                corrections.append(
                    f"Reduce {', '.join(off_theme)} content. "
                    "Steer back to body brokering core loop."
                )
        
        if metrics.severity == DriftSeverity.MAJOR:
            corrections.append(
                "Consider hard constraints on off-theme content generation."
            )
        
        return ' '.join(corrections) if corrections else "Soft steering recommended."
    
    async def _store_drift_alert(
        self,
        player_id: UUID,
        metrics: DriftMetrics
    ) -> None:
        """Store drift alert in database."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO story_drift_alerts
                    (player_id, drift_type, severity, drift_score,
                     metrics, recommended_correction)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                player_id, metrics.drift_type.value, metrics.severity.value,
                metrics.drift_score, json.dumps(metrics.dict(exclude_none=True)),
                metrics.recommended_correction
            )
    
    async def _store_conflict(
        self,
        player_id: UUID,
        conflict: StoryConflict
    ) -> None:
        """Store conflict in database."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO story_conflicts
                    (player_id, conflict_type, involved_entities,
                     conflicting_facts, severity)
                VALUES ($1, $2, $3, $4, $5)
                """,
                player_id, conflict.conflict_type,
                json.dumps(conflict.involved_entities),
                json.dumps(conflict.conflicting_facts),
                conflict.severity.value
            )
    
    async def _emit_drift_event(
        self,
        player_id: UUID,
        metrics: DriftMetrics
    ) -> None:
        """Emit drift event on NATS."""
        await self.nc.publish(
            "events.story.v1.drift",
            json.dumps({
                'player_id': str(player_id),
                'drift_type': metrics.drift_type.value,
                'severity': metrics.severity.value,
                'drift_score': metrics.drift_score,
                'metrics': metrics.dict(exclude_none=True),
                'timestamp': datetime.utcnow().isoformat()
            }).encode()
        )
    
    async def _emit_conflict_event(
        self,
        player_id: UUID,
        conflict: StoryConflict
    ) -> None:
        """Emit conflict alert event on NATS."""
        await self.nc.publish(
            "events.story.v1.conflict_alert",
            json.dumps({
                'player_id': str(player_id),
                'conflict': conflict.dict(),
                'timestamp': datetime.utcnow().isoformat()
            }).encode()
        )
