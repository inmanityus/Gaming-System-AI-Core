"""
Engagement metric calculator for computing NPC attachment, moral tension, and engagement profiles.
Implements TEMO-04, TEMO-05, TEMO-06.
"""
import asyncio
import json
import logging
import math
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID

import asyncpg
import numpy as np
from pydantic import BaseModel

from .engagement_schemas import (
    NPCAttachmentMetrics,
    MoralTensionMetrics,
    EngagementProfile,
    EngagementAggregate,
    AggregateType,
    InteractionType,
    HelpHarmFlag
)

logger = logging.getLogger(__name__)


class MetricCalculator:
    """Calculates various engagement metrics from raw events."""
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres = postgres_pool
        
        # Thresholds for profile detection
        self.PROFILE_THRESHOLDS = {
            'lore-driven explorer': {
                'min_dialogue_completion': 0.8,
                'exploration_coverage': 0.7
            },
            'combat-focused': {
                'combat_participation': 0.9,
                'dialogue_skip_rate': 0.6
            },
            'completionist': {
                'quest_completion': 0.95,
                'collectible_rate': 0.9
            },
            'moral extremist': {
                'extreme_choice_rate': 0.8,
                'moral_consistency': 0.9
            },
            'social butterfly': {
                'npc_interaction_rate': 0.9,
                'gift_giving_rate': 0.7
            }
        }
    
    async def calculate_npc_attachment(
        self,
        cohort_id: str,
        npc_id: str,
        build_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> NPCAttachmentMetrics:
        """
        Calculate NPC attachment metrics for a cohort.
        Implements R-EMO-MET-001.
        """
        async with self.postgres.acquire() as conn:
            # Get all interactions for this NPC within the cohort and time period
            interactions = await conn.fetch(
                """
                SELECT 
                    e.interaction_type,
                    e.help_harm_flag,
                    COUNT(*) as count
                FROM engagement_events e
                JOIN session_cohorts sc ON e.session_id = sc.session_id
                WHERE sc.cohort_id = $1
                    AND e.event_type = 'npc_interaction'
                    AND e.npc_id = $2
                    AND e.build_id = $3
                    AND e.timestamp BETWEEN $4 AND $5
                GROUP BY e.interaction_type, e.help_harm_flag
                """,
                cohort_id, npc_id, build_id, period_start, period_end
            )
            
            # Count actions by type
            helpful_actions = 0
            harmful_actions = 0
            neutral_actions = 0
            total_interactions = 0
            
            interaction_counts = defaultdict(int)
            
            for row in interactions:
                count = row['count']
                total_interactions += count
                interaction_counts[row['interaction_type']] += count
                
                if row['help_harm_flag'] == HelpHarmFlag.HELPFUL.value:
                    helpful_actions += count
                elif row['help_harm_flag'] == HelpHarmFlag.HARMFUL.value:
                    harmful_actions += count
                else:
                    neutral_actions += count
            
            # Calculate protection/harm ratio
            if harmful_actions > 0:
                protection_harm_ratio = helpful_actions / harmful_actions
            else:
                protection_harm_ratio = float(helpful_actions)  # All helpful if no harm
            
            # Calculate attention score (based on interaction diversity and frequency)
            interaction_diversity = len(interaction_counts) / 5.0  # 5 interaction types max
            interaction_frequency = min(total_interactions / 100.0, 1.0)  # Normalize to 100 interactions
            attention_score = (interaction_diversity + interaction_frequency) / 2.0
            
            # Calculate abandonment frequency (based on "ignore" interactions)
            ignore_count = interaction_counts.get(InteractionType.IGNORE.value, 0)
            abandonment_frequency = ignore_count / max(total_interactions, 1)
            
            # Get proximity time (simplified - in real system would track actual proximity)
            proximity_result = await conn.fetchrow(
                """
                SELECT SUM(
                    CASE 
                        WHEN interaction_type = 'dialogue' THEN 120  -- 2 min avg dialogue
                        WHEN interaction_type = 'gift' THEN 30      -- 30 sec gift
                        WHEN interaction_type = 'assist' THEN 60    -- 1 min assist
                        WHEN interaction_type = 'harm' THEN 45      -- 45 sec harm
                        ELSE 5                                       -- 5 sec ignore
                    END
                ) as total_proximity_seconds
                FROM engagement_events e
                JOIN session_cohorts sc ON e.session_id = sc.session_id
                WHERE sc.cohort_id = $1
                    AND e.event_type = 'npc_interaction'
                    AND e.npc_id = $2
                    AND e.build_id = $3
                    AND e.timestamp BETWEEN $4 AND $5
                """,
                cohort_id, npc_id, build_id, period_start, period_end
            )
            
            total_proximity_seconds = proximity_result['total_proximity_seconds'] or 0
            
            return NPCAttachmentMetrics(
                npc_id=npc_id,
                protection_harm_ratio=protection_harm_ratio,
                attention_score=attention_score,
                abandonment_frequency=abandonment_frequency,
                total_interactions=total_interactions,
                helpful_actions=helpful_actions,
                harmful_actions=harmful_actions,
                neutral_actions=neutral_actions,
                total_proximity_time_seconds=total_proximity_seconds
            )
    
    async def calculate_moral_tension(
        self,
        cohort_id: str,
        scene_id: str,
        build_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> MoralTensionMetrics:
        """
        Calculate moral decision tension metrics.
        Implements R-EMO-MET-002.
        """
        async with self.postgres.acquire() as conn:
            # Get all moral choices for this scene
            choices = await conn.fetch(
                """
                SELECT 
                    e.selected_option_id,
                    e.decision_latency_ms,
                    e.num_retries,
                    e.reloaded_save,
                    e.options
                FROM engagement_events e
                JOIN session_cohorts sc ON e.session_id = sc.session_id
                WHERE sc.cohort_id = $1
                    AND e.event_type = 'moral_choice'
                    AND e.scene_id = $2
                    AND e.build_id = $3
                    AND e.timestamp BETWEEN $4 AND $5
                """,
                cohort_id, scene_id, build_id, period_start, period_end
            )
            
            if not choices:
                return MoralTensionMetrics(
                    scene_id=scene_id,
                    tension_index=0.0,
                    choice_distribution_entropy=0.0,
                    avg_decision_latency_seconds=0.0,
                    total_choices=0,
                    reload_count=0,
                    option_counts={}
                )
            
            # Count options and calculate metrics
            option_counts = Counter()
            total_latency_ms = 0
            reload_count = 0
            retry_count = 0
            
            for row in choices:
                option_counts[row['selected_option_id']] += 1
                total_latency_ms += row['decision_latency_ms']
                if row['reloaded_save']:
                    reload_count += 1
                retry_count += row['num_retries']
            
            total_choices = len(choices)
            avg_latency_seconds = (total_latency_ms / 1000) / total_choices
            
            # Calculate choice distribution entropy (Shannon entropy)
            entropy = 0.0
            for count in option_counts.values():
                if count > 0:
                    p = count / total_choices
                    entropy -= p * math.log2(p)
            
            # Normalize entropy by max possible (log2 of number of options)
            num_options = len(option_counts)
            if num_options > 1:
                max_entropy = math.log2(num_options)
                normalized_entropy = entropy / max_entropy
            else:
                normalized_entropy = 0.0
            
            # Calculate tension index based on:
            # - High entropy (split decisions)
            # - Long decision times
            # - Reloads and retries
            latency_factor = min(avg_latency_seconds / 30.0, 1.0)  # Normalize to 30 seconds
            reload_factor = reload_count / total_choices
            retry_factor = retry_count / total_choices
            
            tension_index = (
                normalized_entropy * 0.4 +
                latency_factor * 0.3 +
                reload_factor * 0.2 +
                retry_factor * 0.1
            )
            
            return MoralTensionMetrics(
                scene_id=scene_id,
                tension_index=min(tension_index, 1.0),
                choice_distribution_entropy=entropy,
                avg_decision_latency_seconds=avg_latency_seconds,
                total_choices=total_choices,
                reload_count=reload_count,
                option_counts=dict(option_counts)
            )
    
    async def detect_engagement_profile(
        self,
        cohort_id: str,
        build_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Optional[EngagementProfile]:
        """
        Detect primary engagement profile for a cohort.
        Implements R-EMO-MET-003.
        """
        async with self.postgres.acquire() as conn:
            # Get behavioral metrics for the cohort
            metrics = await self._calculate_behavioral_metrics(
                conn, cohort_id, build_id, period_start, period_end
            )
            
            if not metrics:
                return None
            
            # Score each profile based on metrics
            profile_scores = {}
            
            # Lore-driven explorer
            if metrics.get('dialogue_completion', 0) >= self.PROFILE_THRESHOLDS['lore-driven explorer']['min_dialogue_completion']:
                profile_scores['lore-driven explorer'] = (
                    metrics['dialogue_completion'] * 0.6 +
                    metrics.get('exploration_coverage', 0) * 0.4
                )
            
            # Combat-focused
            if metrics.get('dialogue_skip_rate', 0) >= self.PROFILE_THRESHOLDS['combat-focused']['dialogue_skip_rate']:
                profile_scores['combat-focused'] = (
                    metrics.get('combat_participation', 0) * 0.7 +
                    metrics['dialogue_skip_rate'] * 0.3
                )
            
            # Completionist
            if metrics.get('quest_completion', 0) >= self.PROFILE_THRESHOLDS['completionist']['quest_completion']:
                profile_scores['completionist'] = (
                    metrics['quest_completion'] * 0.5 +
                    metrics.get('collectible_rate', 0) * 0.5
                )
            
            # Moral extremist
            if metrics.get('extreme_choice_rate', 0) >= self.PROFILE_THRESHOLDS['moral extremist']['extreme_choice_rate']:
                profile_scores['moral extremist'] = (
                    metrics['extreme_choice_rate'] * 0.6 +
                    metrics.get('moral_consistency', 0) * 0.4
                )
            
            # Social butterfly
            if metrics.get('npc_interaction_rate', 0) >= self.PROFILE_THRESHOLDS['social butterfly']['npc_interaction_rate']:
                profile_scores['social butterfly'] = (
                    metrics['npc_interaction_rate'] * 0.5 +
                    metrics.get('gift_giving_rate', 0) * 0.5
                )
            
            if not profile_scores:
                return None
            
            # Select highest scoring profile
            best_profile = max(profile_scores.items(), key=lambda x: x[1])
            profile_name = best_profile[0]
            confidence = best_profile[1]
            
            # Get profile definition
            profile_def = await conn.fetchrow(
                "SELECT * FROM engagement_profile_definitions WHERE profile_name = $1",
                profile_name
            )
            
            if not profile_def:
                return None
            
            return EngagementProfile(
                profile_id=profile_def['profile_id'],
                profile_name=profile_name,
                profile_confidence=confidence,
                characteristic_behaviors=profile_def['example_behaviors'] or []
            )
    
    async def _calculate_behavioral_metrics(
        self,
        conn: asyncpg.Connection,
        cohort_id: str,
        build_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, float]:
        """Calculate various behavioral metrics for profile detection."""
        metrics = {}
        
        # Dialogue completion rate
        dialogue_stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(DISTINCT npc_id) as npcs_talked_to,
                COUNT(CASE WHEN interaction_type = 'dialogue' THEN 1 END) as dialogue_count,
                COUNT(CASE WHEN interaction_type = 'ignore' THEN 1 END) as ignore_count
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'npc_interaction'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if dialogue_stats['dialogue_count'] + dialogue_stats['ignore_count'] > 0:
            metrics['dialogue_completion'] = dialogue_stats['dialogue_count'] / (
                dialogue_stats['dialogue_count'] + dialogue_stats['ignore_count']
            )
            metrics['dialogue_skip_rate'] = 1 - metrics['dialogue_completion']
        else:
            metrics['dialogue_completion'] = 0
            metrics['dialogue_skip_rate'] = 0
        
        # NPC interaction rate
        session_count = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT e.session_id)
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if session_count > 0:
            metrics['npc_interaction_rate'] = dialogue_stats['npcs_talked_to'] / session_count
        else:
            metrics['npc_interaction_rate'] = 0
        
        # Gift giving rate
        gift_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'npc_interaction'
                AND e.interaction_type = 'gift'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if dialogue_stats['npcs_talked_to'] > 0:
            metrics['gift_giving_rate'] = gift_count / dialogue_stats['npcs_talked_to']
        else:
            metrics['gift_giving_rate'] = 0
        
        # Moral choice extremism
        moral_choices = await conn.fetch(
            """
            SELECT 
                e.selected_option_id,
                e.options
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'moral_choice'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if moral_choices:
            extreme_count = 0
            consistency_scores = []
            
            for row in moral_choices:
                options = json.loads(row['options']) if isinstance(row['options'], str) else row['options']
                selected = row['selected_option_id']
                
                # Check if selected option has extreme tags
                for opt in options:
                    if opt['option_id'] == selected:
                        tags = opt.get('tags', [])
                        if any(tag in ['evil', 'pure_good', 'cruel', 'selfless'] for tag in tags):
                            extreme_count += 1
                        break
            
            metrics['extreme_choice_rate'] = extreme_count / len(moral_choices)
            
            # TODO: Calculate moral consistency (would need to track choice patterns over time)
            metrics['moral_consistency'] = 0.8  # Placeholder
        else:
            metrics['extreme_choice_rate'] = 0
            metrics['moral_consistency'] = 0
        
        # Placeholder metrics (would be calculated from other systems)
        metrics['exploration_coverage'] = 0.75  # Would come from world traversal data
        metrics['combat_participation'] = 0.5   # Would come from combat telemetry
        metrics['quest_completion'] = 0.85      # Would come from quest system
        metrics['collectible_rate'] = 0.7       # Would come from inventory system
        
        return metrics
    
    async def store_aggregate(self, aggregate: EngagementAggregate) -> None:
        """Store computed aggregate metrics."""
        async with self.postgres.acquire() as conn:
            # Extract type-specific fields
            npc_metrics = aggregate.npc_attachment
            moral_metrics = aggregate.moral_tension
            profile = aggregate.engagement_profile
            
            await conn.execute(
                """
                INSERT INTO engagement_aggregates (
                    aggregate_type, cohort_id, npc_id, arc_id, scene_id, build_id,
                    period_start, period_end,
                    protection_harm_ratio, attention_score, abandonment_frequency,
                    total_interactions, helpful_actions, harmful_actions, neutral_actions,
                    total_proximity_time_seconds,
                    tension_index, choice_distribution_entropy, avg_decision_latency_seconds,
                    total_choices, reload_count, option_counts,
                    profile_id, profile_name, profile_confidence, characteristic_behaviors,
                    metrics, computed_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, $10, $11, $12, $13, $14, $15, $16,
                    $17, $18, $19, $20, $21, $22,
                    $23, $24, $25, $26, $27, $28
                )
                ON CONFLICT (aggregate_type, cohort_id, npc_id, arc_id, scene_id, build_id, period_start)
                DO UPDATE SET
                    period_end = EXCLUDED.period_end,
                    protection_harm_ratio = EXCLUDED.protection_harm_ratio,
                    attention_score = EXCLUDED.attention_score,
                    abandonment_frequency = EXCLUDED.abandonment_frequency,
                    total_interactions = EXCLUDED.total_interactions,
                    helpful_actions = EXCLUDED.helpful_actions,
                    harmful_actions = EXCLUDED.harmful_actions,
                    neutral_actions = EXCLUDED.neutral_actions,
                    total_proximity_time_seconds = EXCLUDED.total_proximity_time_seconds,
                    tension_index = EXCLUDED.tension_index,
                    choice_distribution_entropy = EXCLUDED.choice_distribution_entropy,
                    avg_decision_latency_seconds = EXCLUDED.avg_decision_latency_seconds,
                    total_choices = EXCLUDED.total_choices,
                    reload_count = EXCLUDED.reload_count,
                    option_counts = EXCLUDED.option_counts,
                    profile_id = EXCLUDED.profile_id,
                    profile_name = EXCLUDED.profile_name,
                    profile_confidence = EXCLUDED.profile_confidence,
                    characteristic_behaviors = EXCLUDED.characteristic_behaviors,
                    metrics = EXCLUDED.metrics,
                    computed_at = EXCLUDED.computed_at
                """,
                aggregate.aggregate_type.value,
                aggregate.cohort_id,
                npc_metrics.npc_id if npc_metrics else None,
                None,  # arc_id - not used yet
                moral_metrics.scene_id if moral_metrics else None,
                aggregate.build_id,
                aggregate.period_start,
                aggregate.period_end,
                npc_metrics.protection_harm_ratio if npc_metrics else None,
                npc_metrics.attention_score if npc_metrics else None,
                npc_metrics.abandonment_frequency if npc_metrics else None,
                npc_metrics.total_interactions if npc_metrics else None,
                npc_metrics.helpful_actions if npc_metrics else None,
                npc_metrics.harmful_actions if npc_metrics else None,
                npc_metrics.neutral_actions if npc_metrics else None,
                npc_metrics.total_proximity_time_seconds if npc_metrics else None,
                moral_metrics.tension_index if moral_metrics else None,
                moral_metrics.choice_distribution_entropy if moral_metrics else None,
                moral_metrics.avg_decision_latency_seconds if moral_metrics else None,
                moral_metrics.total_choices if moral_metrics else None,
                moral_metrics.reload_count if moral_metrics else None,
                json.dumps(moral_metrics.option_counts) if moral_metrics else None,
                profile.profile_id if profile else None,
                profile.profile_name if profile else None,
                profile.profile_confidence if profile else None,
                profile.characteristic_behaviors if profile else None,
                json.dumps(aggregate.metrics),
                aggregate.computed_at
            )
