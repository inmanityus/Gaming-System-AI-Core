"""
Addiction risk detector for identifying cohort-level addiction patterns.
Implements TEMO-07, TEMO-08.
"""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple

import asyncpg
import numpy as np

from .engagement_schemas import (
    AddictionRiskIndicators,
    AddictionRiskReport,
    RiskLevel,
    CohortDefinition
)

logger = logging.getLogger(__name__)


class AddictionDetector:
    """
    Detects addiction risk patterns at cohort level.
    R-EMO-ADD-002: No individual player tracking.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres = postgres_pool
        
        # Risk thresholds (configurable)
        self.THRESHOLDS = {
            'avg_daily_hours': {
                'low': 2.0,
                'medium': 4.0,
                'high': 6.0,
                'critical': 8.0
            },
            'night_play_fraction': {
                'low': 0.1,
                'medium': 0.25,
                'high': 0.4,
                'critical': 0.6
            },
            'rapid_return_rate': {
                'low': 0.1,
                'medium': 0.3,
                'high': 0.5,
                'critical': 0.7
            },
            'weekend_spike': {
                'low': 1.5,
                'medium': 2.0,
                'high': 3.0,
                'critical': 4.0
            }
        }
        
        # High-risk behavior patterns
        self.RISK_PATTERNS = {
            '3am_regular': 'Regular play during 3-5 AM',
            '12hr_binge': 'Single sessions exceeding 12 hours',
            'sleep_deprivation': 'Sessions starting within 4 hours of previous end',
            'work_hours_play': 'Consistent play during typical work hours (9-5 weekdays)',
            'escalating_duration': 'Session duration increasing week-over-week',
            'social_isolation': 'Declining variety in NPC interactions',
            'compulsive_restart': 'High frequency of save reloads for optimal outcomes'
        }
    
    async def assess_cohort_risk(
        self,
        cohort_def: CohortDefinition,
        build_id: str,
        period_days: int = 7
    ) -> AddictionRiskReport:
        """
        Assess addiction risk for a cohort over specified period.
        Returns aggregated risk report with no individual data.
        """
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=period_days)
        
        async with self.postgres.acquire() as conn:
            # Get cohort size (minimum 100 for privacy)
            cohort_size = await self._get_cohort_size(conn, cohort_def.cohort_id, period_start, period_end)
            
            if cohort_size < 100:
                logger.warning(f"Cohort {cohort_def.cohort_id} too small ({cohort_size}), skipping assessment")
                return self._create_insufficient_data_report(cohort_def, build_id, period_days, cohort_size)
            
            # Calculate risk indicators
            indicators = await self._calculate_risk_indicators(
                conn, cohort_def.cohort_id, build_id, period_start, period_end
            )
            
            # Detect high-risk patterns
            risk_patterns = await self._detect_risk_patterns(
                conn, cohort_def.cohort_id, build_id, period_start, period_end
            )
            
            # Identify correlated game systems
            associated_systems = await self._identify_associated_systems(
                conn, cohort_def.cohort_id, build_id, period_start, period_end
            )
            
            # Determine overall risk level
            risk_level = self._calculate_overall_risk(indicators, risk_patterns)
            
            # Generate summary and recommendations
            risk_summary = self._generate_risk_summary(indicators, risk_patterns, risk_level)
            recommendations = self._generate_recommendations(risk_level, risk_patterns, associated_systems)
            
            # Calculate confidence (based on data completeness)
            confidence = self._calculate_confidence(cohort_size, period_days)
            
            return AddictionRiskReport(
                cohort_id=cohort_def.cohort_id,
                region=cohort_def.region,
                age_band=cohort_def.age_band,
                platform=cohort_def.platform,
                cohort_size=cohort_size,
                report_period=f"{period_start.date()}/P{period_days}D",
                risk_indicators=indicators,
                overall_risk_level=risk_level,
                risk_summary=risk_summary,
                recommendations=recommendations,
                build_id=build_id,
                confidence_percentage=confidence
            )
    
    async def _get_cohort_size(
        self,
        conn: asyncpg.Connection,
        cohort_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> int:
        """Get unique session count for cohort."""
        result = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT e.session_id)
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.timestamp BETWEEN $2 AND $3
            """,
            cohort_id, period_start, period_end
        )
        return result or 0
    
    async def _calculate_risk_indicators(
        self,
        conn: asyncpg.Connection,
        cohort_id: str,
        build_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> AddictionRiskIndicators:
        """Calculate addiction risk indicators for cohort."""
        
        # Get session metrics
        session_data = await conn.fetch(
            """
            SELECT 
                total_duration_minutes,
                time_of_day_bucket,
                day_of_week,
                session_start,
                session_end,
                is_return_session,
                time_since_last_session_seconds
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'session_metrics'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if not session_data:
            return AddictionRiskIndicators(
                avg_daily_session_hours=0.0,
                night_time_play_fraction=0.0,
                rapid_session_return_rate=0.0,
                weekend_spike_ratio=1.0,
                high_risk_patterns=[],
                associated_systems=[]
            )
        
        # Calculate average daily hours
        total_minutes = sum(row['total_duration_minutes'] for row in session_data)
        total_days = (period_end - period_start).days
        avg_daily_hours = (total_minutes / 60.0) / max(total_days, 1)
        
        # Calculate night time play fraction (10 PM - 6 AM)
        night_sessions = sum(
            1 for row in session_data 
            if row['time_of_day_bucket'] in ['late_night', 'early_morning']
        )
        night_play_fraction = night_sessions / len(session_data)
        
        # Calculate rapid return rate (< 30 minutes between sessions)
        rapid_returns = sum(
            1 for row in session_data
            if row['is_return_session'] and 
            row['time_since_last_session_seconds'] and 
            row['time_since_last_session_seconds'] < 1800  # 30 minutes
        )
        rapid_return_rate = rapid_returns / len(session_data)
        
        # Calculate weekend spike
        weekday_minutes = []
        weekend_minutes = []
        for row in session_data:
            if row['day_of_week'] in [0, 6]:  # Sunday, Saturday
                weekend_minutes.append(row['total_duration_minutes'])
            else:
                weekday_minutes.append(row['total_duration_minutes'])
        
        if weekday_minutes and weekend_minutes:
            avg_weekday = np.mean(weekday_minutes)
            avg_weekend = np.mean(weekend_minutes)
            weekend_spike_ratio = avg_weekend / max(avg_weekday, 1)
        else:
            weekend_spike_ratio = 1.0
        
        return AddictionRiskIndicators(
            avg_daily_session_hours=avg_daily_hours,
            night_time_play_fraction=night_play_fraction,
            rapid_session_return_rate=rapid_return_rate,
            weekend_spike_ratio=weekend_spike_ratio,
            high_risk_patterns=[],  # Will be filled by pattern detection
            associated_systems=[]    # Will be filled by system correlation
        )
    
    async def _detect_risk_patterns(
        self,
        conn: asyncpg.Connection,
        cohort_id: str,
        build_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> List[str]:
        """Detect specific high-risk behavior patterns."""
        detected_patterns = []
        
        # Check for 3 AM regular play
        night_sessions = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'session_metrics'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
                AND EXTRACT(HOUR FROM e.session_start) BETWEEN 3 AND 5
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        total_sessions = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'session_metrics'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if total_sessions > 0 and night_sessions / total_sessions > 0.2:
            detected_patterns.append('3am_regular')
        
        # Check for 12+ hour binges
        long_sessions = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'session_metrics'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
                AND e.total_duration_minutes >= 720  -- 12 hours
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if long_sessions > 0:
            detected_patterns.append('12hr_binge')
        
        # Check for compulsive restart pattern
        high_reload_scenes = await conn.fetch(
            """
            SELECT scene_id, AVG(reload_count) as avg_reloads
            FROM engagement_aggregates
            WHERE aggregate_type = 'moral_tension'
                AND cohort_id = $1
                AND build_id = $2
                AND period_start >= $3
                AND period_end <= $4
                AND total_choices > 0
            GROUP BY scene_id
            HAVING AVG(reload_count) > 2.0
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if len(high_reload_scenes) >= 3:
            detected_patterns.append('compulsive_restart')
        
        return detected_patterns
    
    async def _identify_associated_systems(
        self,
        conn: asyncpg.Connection,
        cohort_id: str,
        build_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> List[str]:
        """Identify game systems associated with extended play."""
        associated_systems = []
        
        # Check which NPCs have highest interaction rates
        top_npcs = await conn.fetch(
            """
            SELECT npc_id, COUNT(*) as interaction_count
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.event_type = 'npc_interaction'
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            GROUP BY npc_id
            ORDER BY interaction_count DESC
            LIMIT 5
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if top_npcs:
            # Check if romance NPCs dominate interactions
            romance_npcs = ['npc_romance_1', 'npc_romance_2']  # Placeholder IDs
            romance_interactions = sum(
                row['interaction_count'] for row in top_npcs 
                if row['npc_id'] in romance_npcs
            )
            total_top_interactions = sum(row['interaction_count'] for row in top_npcs)
            
            if total_top_interactions > 0 and romance_interactions / total_top_interactions > 0.5:
                associated_systems.append('romance_system')
        
        # Check for specific arc engagement
        arc_engagement = await conn.fetch(
            """
            SELECT arc_id, COUNT(*) as event_count
            FROM engagement_events e
            JOIN session_cohorts sc ON e.session_id = sc.session_id
            WHERE sc.cohort_id = $1
                AND e.arc_id IS NOT NULL
                AND e.build_id = $2
                AND e.timestamp BETWEEN $3 AND $4
            GROUP BY arc_id
            ORDER BY event_count DESC
            LIMIT 3
            """,
            cohort_id, build_id, period_start, period_end
        )
        
        if arc_engagement:
            # Map arc IDs to systems (placeholder mapping)
            arc_system_map = {
                'arc_vampire': 'vampire_politics',
                'arc_flesh_debt': 'debt_collection',
                'arc_surgeon': 'body_modification'
            }
            
            for row in arc_engagement:
                system = arc_system_map.get(row['arc_id'])
                if system:
                    associated_systems.append(system)
        
        return list(set(associated_systems))  # Remove duplicates
    
    def _calculate_overall_risk(
        self,
        indicators: AddictionRiskIndicators,
        risk_patterns: List[str]
    ) -> RiskLevel:
        """Calculate overall risk level based on indicators and patterns."""
        risk_scores = []
        
        # Score based on average daily hours
        for level in ['critical', 'high', 'medium', 'low']:
            if indicators.avg_daily_session_hours >= self.THRESHOLDS['avg_daily_hours'][level]:
                risk_scores.append(RiskLevel[level.upper()])
                break
        
        # Score based on night play
        for level in ['critical', 'high', 'medium', 'low']:
            if indicators.night_time_play_fraction >= self.THRESHOLDS['night_play_fraction'][level]:
                risk_scores.append(RiskLevel[level.upper()])
                break
        
        # Score based on rapid returns
        for level in ['critical', 'high', 'medium', 'low']:
            if indicators.rapid_session_return_rate >= self.THRESHOLDS['rapid_return_rate'][level]:
                risk_scores.append(RiskLevel[level.upper()])
                break
        
        # High-risk patterns automatically elevate risk
        if len(risk_patterns) >= 3:
            risk_scores.append(RiskLevel.CRITICAL)
        elif len(risk_patterns) >= 2:
            risk_scores.append(RiskLevel.HIGH)
        elif len(risk_patterns) >= 1:
            risk_scores.append(RiskLevel.MEDIUM)
        
        # Return highest risk level
        if not risk_scores:
            return RiskLevel.LOW
        
        risk_values = [level.value for level in RiskLevel]
        highest_score = max(score.value for score in risk_scores)
        return RiskLevel(risk_values[risk_values.index(highest_score)])
    
    def _generate_risk_summary(
        self,
        indicators: AddictionRiskIndicators,
        risk_patterns: List[str],
        risk_level: RiskLevel
    ) -> str:
        """Generate human-readable risk summary."""
        summary_parts = []
        
        summary_parts.append(f"Overall addiction risk level: {risk_level.value.upper()}")
        
        if indicators.avg_daily_session_hours > 4:
            summary_parts.append(
                f"Cohort averages {indicators.avg_daily_session_hours:.1f} hours daily, "
                f"exceeding healthy gaming guidelines."
            )
        
        if indicators.night_time_play_fraction > 0.3:
            summary_parts.append(
                f"{indicators.night_time_play_fraction*100:.0f}% of sessions occur during "
                f"late night/early morning hours, suggesting sleep disruption."
            )
        
        if risk_patterns:
            pattern_descriptions = [self.RISK_PATTERNS.get(p, p) for p in risk_patterns]
            summary_parts.append(
                f"Detected high-risk patterns: {', '.join(pattern_descriptions)}"
            )
        
        return " ".join(summary_parts)
    
    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        risk_patterns: List[str],
        associated_systems: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on risk assessment."""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append(
                "Consider implementing session duration warnings after 2 hours of continuous play"
            )
            recommendations.append(
                "Add reminders to take breaks during extended gaming sessions"
            )
        
        if '3am_regular' in risk_patterns or '12hr_binge' in risk_patterns:
            recommendations.append(
                "Implement gentle 'fatigue' mechanics that encourage natural break points"
            )
            recommendations.append(
                "Add time-of-day awareness with subtle UI hints about real-world time"
            )
        
        if 'compulsive_restart' in risk_patterns:
            recommendations.append(
                "Review save/reload mechanics to reduce perfectionism pressure"
            )
            recommendations.append(
                "Consider adding 'ironman' mode options for players seeking challenge"
            )
        
        if 'romance_system' in associated_systems:
            recommendations.append(
                "Monitor romance content pacing to prevent unhealthy attachment patterns"
            )
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append(
                "URGENT: Consider voluntary play time limits and wellness resources in game menu"
            )
        
        return recommendations
    
    def _calculate_confidence(self, cohort_size: int, period_days: int) -> int:
        """Calculate confidence percentage based on data quality."""
        # Base confidence on cohort size
        size_confidence = min(cohort_size / 1000, 1.0) * 50  # Max 50% from size
        
        # Base confidence on observation period
        period_confidence = min(period_days / 30, 1.0) * 50  # Max 50% from period
        
        total_confidence = int(size_confidence + period_confidence)
        return min(total_confidence, 95)  # Cap at 95%
    
    def _create_insufficient_data_report(
        self,
        cohort_def: CohortDefinition,
        build_id: str,
        period_days: int,
        cohort_size: int
    ) -> AddictionRiskReport:
        """Create report when insufficient data available."""
        return AddictionRiskReport(
            cohort_id=cohort_def.cohort_id,
            region=cohort_def.region,
            age_band=cohort_def.age_band,
            platform=cohort_def.platform,
            cohort_size=cohort_size,
            report_period=f"{datetime.now(timezone.utc).date()}/P{period_days}D",
            risk_indicators=AddictionRiskIndicators(
                avg_daily_session_hours=0.0,
                night_time_play_fraction=0.0,
                rapid_session_return_rate=0.0,
                weekend_spike_ratio=1.0,
                high_risk_patterns=[],
                associated_systems=[]
            ),
            overall_risk_level=RiskLevel.LOW,
            risk_summary="Insufficient data for risk assessment",
            recommendations=["Increase cohort size to minimum 100 for privacy-preserving analytics"],
            build_id=build_id,
            confidence_percentage=0,
            notes="Cohort size below privacy threshold"
        )

