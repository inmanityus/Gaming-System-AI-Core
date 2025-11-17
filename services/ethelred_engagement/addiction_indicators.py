"""
Cohort-level addiction risk indicator computation
"""
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import asyncpg
import numpy as np
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AddictionIndicatorConfig:
    """Configuration for addiction risk indicators."""
    # Time windows for "unhealthy" play patterns (can be overridden via environment)
    night_time_start: time = time(
        int(os.getenv('ADDICTION_NIGHT_TIME_START_HOUR', '23')),
        int(os.getenv('ADDICTION_NIGHT_TIME_START_MINUTE', '0'))
    )
    night_time_end: time = time(
        int(os.getenv('ADDICTION_NIGHT_TIME_END_HOUR', '5')),
        int(os.getenv('ADDICTION_NIGHT_TIME_END_MINUTE', '0'))
    )
    early_morning_start: time = time(
        int(os.getenv('ADDICTION_EARLY_MORNING_START_HOUR', '2')),
        int(os.getenv('ADDICTION_EARLY_MORNING_START_MINUTE', '0'))
    )
    early_morning_end: time = time(
        int(os.getenv('ADDICTION_EARLY_MORNING_END_HOUR', '6')),
        int(os.getenv('ADDICTION_EARLY_MORNING_END_MINUTE', '0'))
    )
    
    # Session thresholds
    excessive_session_hours: float = float(os.getenv('ADDICTION_EXCESSIVE_SESSION_HOURS', '4.0'))
    one_more_run_window_minutes: int = int(os.getenv('ADDICTION_ONE_MORE_RUN_WINDOW_MINUTES', '10'))
    
    # Risk factor thresholds
    night_time_fraction_threshold: float = float(os.getenv('ADDICTION_NIGHT_TIME_FRACTION_THRESHOLD', '0.3'))
    one_more_run_loops_threshold: float = float(os.getenv('ADDICTION_ONE_MORE_RUN_LOOPS_THRESHOLD', '4'))
    excessive_session_fraction_threshold: float = float(os.getenv('ADDICTION_EXCESSIVE_SESSION_FRACTION_THRESHOLD', '0.25'))
    consecutive_days_threshold: int = int(os.getenv('ADDICTION_CONSECUTIVE_DAYS_THRESHOLD', '21'))
    time_between_sessions_threshold: float = float(os.getenv('ADDICTION_TIME_BETWEEN_SESSIONS_THRESHOLD', '8'))
    weekend_ratio_threshold: float = float(os.getenv('ADDICTION_WEEKEND_RATIO_THRESHOLD', '0.5'))


class AddictionIndicatorCalculator:
    """
    Computes cohort-level addiction risk indicators.
    
    CRITICAL: All computations are at cohort level only.
    No individual player metrics are computed or stored.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool, config: Optional[AddictionIndicatorConfig] = None):
        self.postgres = postgres_pool
        self.config = config or AddictionIndicatorConfig()
    
    async def compute_indicators(
        self,
        cohort: Dict[str, str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Compute all addiction risk indicators for a cohort.
        
        Returns dict with:
        - All indicator values
        - Sample size
        - Confidence level
        - Risk factors identified
        """
        # Get session data for cohort
        sessions = await self._get_cohort_sessions(cohort, start_date, end_date)
        
        if not sessions:
            logger.warning(f"No sessions found for cohort {cohort}")
            return self._empty_indicators()
        
        # Compute each indicator
        indicators = {}
        
        # R-EMO-ADD-001: Night-time play fraction
        indicators['night_time_fraction'] = self._compute_night_time_fraction(sessions)
        
        # R-EMO-ADD-002: "One more run" loops
        indicators['one_more_run_loops'] = await self._compute_one_more_run_loops(
            cohort, sessions
        )
        
        # R-EMO-ADD-003: Excessive session distribution
        session_metrics = self._compute_session_metrics(sessions)
        indicators.update(session_metrics)
        
        # Additional risk metrics
        indicators['consecutive_days_played_p90'] = self._compute_consecutive_days(sessions)
        indicators['avg_time_between_sessions_hours'] = self._compute_time_between_sessions(sessions)
        indicators['early_morning_sessions_fraction'] = self._compute_early_morning_fraction(sessions)
        indicators['weekend_vs_weekday_ratio'] = self._compute_weekend_ratio(sessions)
        
        # Get engagement context for correlation
        engagement_metrics = await self._get_engagement_metrics(cohort, start_date, end_date)
        indicators.update(engagement_metrics)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(indicators)
        
        # Compute confidence based on sample size
        sample_size = len(sessions)
        confidence_level = self._compute_confidence(sample_size)
        
        return {
            **indicators,
            'sample_size': sample_size,
            'confidence_level': confidence_level,
            'risk_factors': risk_factors
        }
    
    async def _get_cohort_sessions(
        self,
        cohort: Dict[str, str],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get session data for a cohort."""
        async with self.postgres.acquire() as conn:
            # Build cohort filter
            cohort_conditions = []
            params = [start_date, end_date]
            param_count = 2
            
            for key, value in cohort.items():
                if value:
                    param_count += 1
                    cohort_conditions.append(
                        f"cohort_metadata->>${param_count-1} = ${param_count}"
                    )
                    params.append(value)
            
            cohort_where = " AND ".join(cohort_conditions) if cohort_conditions else "TRUE"
            
            # Get aggregated session metrics
            rows = await conn.fetch(
                f"""
                SELECT 
                    session_id,
                    MIN(created_at) as session_start,
                    MAX(created_at) as session_end,
                    COUNT(*) as event_count,
                    MAX(event_data->>'total_playtime_minutes') as total_playtime_minutes
                FROM engagement_events
                WHERE event_type = 'session_metrics'
                    AND created_at BETWEEN $1 AND $2
                    AND {cohort_where}
                GROUP BY session_id
                ORDER BY session_start
                """,
                *params
            )
            
        return [dict(row) for row in rows]
    
    def _compute_night_time_fraction(self, sessions: List[Dict[str, Any]]) -> float:
        """Compute fraction of play during night-time hours."""
        if not sessions:
            return 0.0
            
        total_minutes = 0
        night_minutes = 0
        
        for session in sessions:
            start = session['session_start']
            end = session['session_end']
            duration_minutes = (end - start).total_seconds() / 60
            total_minutes += duration_minutes
            
            # Calculate overlap with night time window
            night_overlap = self._calculate_time_window_overlap(
                start, end, self.config.night_time_start, self.config.night_time_end
            )
            night_minutes += night_overlap
        
        return night_minutes / total_minutes if total_minutes > 0 else 0.0
    
    async def _compute_one_more_run_loops(
        self,
        cohort: Dict[str, str],
        sessions: List[Dict[str, Any]]
    ) -> float:
        """
        Compute average "one more run" loops per session.
        Detects when players start new sessions shortly after ending previous ones.
        """
        if len(sessions) < 2:
            return 0.0
            
        one_more_runs = 0
        analyzed_sessions = 0
        
        for i in range(1, len(sessions)):
            prev_end = sessions[i-1]['session_end']
            curr_start = sessions[i]['session_start']
            
            # Time between sessions
            gap_minutes = (curr_start - prev_end).total_seconds() / 60
            
            # Count as "one more run" if gap is small
            if 0 < gap_minutes <= self.config.one_more_run_window_minutes:
                one_more_runs += 1
            
            analyzed_sessions += 1
        
        return one_more_runs / analyzed_sessions if analyzed_sessions > 0 else 0.0
    
    def _compute_session_metrics(self, sessions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute session duration metrics."""
        if not sessions:
            return {
                'excessive_session_fraction': 0.0,
                'avg_session_duration_hours': 0.0,
                'max_session_duration_hours': 0.0
            }
        
        durations_hours = []
        excessive_count = 0
        
        for session in sessions:
            # Try to get duration from event data first
            if session.get('total_playtime_minutes'):
                duration_hours = float(session['total_playtime_minutes']) / 60
            else:
                # Fall back to timestamp difference
                duration = session['session_end'] - session['session_start']
                duration_hours = duration.total_seconds() / 3600
            
            durations_hours.append(duration_hours)
            
            if duration_hours > self.config.excessive_session_hours:
                excessive_count += 1
        
        return {
            'excessive_session_fraction': excessive_count / len(sessions),
            'avg_session_duration_hours': np.mean(durations_hours),
            'max_session_duration_hours': np.max(durations_hours)
        }
    
    def _compute_consecutive_days(self, sessions: List[Dict[str, Any]]) -> int:
        """Compute 90th percentile of consecutive days played."""
        if not sessions:
            return 0
            
        # Group sessions by date
        sessions_by_date = defaultdict(list)
        for session in sessions:
            date = session['session_start'].date()
            sessions_by_date[date].append(session)
        
        # Find consecutive day streaks
        sorted_dates = sorted(sessions_by_date.keys())
        streaks = []
        current_streak = 1
        
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_streak += 1
            else:
                streaks.append(current_streak)
                current_streak = 1
        streaks.append(current_streak)
        
        # Return 90th percentile
        return int(np.percentile(streaks, 90)) if streaks else 0
    
    def _compute_time_between_sessions(self, sessions: List[Dict[str, Any]]) -> float:
        """Compute average time between sessions in hours."""
        if len(sessions) < 2:
            return 0.0
            
        gaps = []
        for i in range(1, len(sessions)):
            gap = sessions[i]['session_start'] - sessions[i-1]['session_end']
            gaps.append(gap.total_seconds() / 3600)
        
        return np.mean(gaps) if gaps else 0.0
    
    def _compute_early_morning_fraction(self, sessions: List[Dict[str, Any]]) -> float:
        """Compute fraction of sessions starting in early morning hours."""
        if not sessions:
            return 0.0
            
        early_morning_count = 0
        
        for session in sessions:
            start_time = session['session_start'].time()
            if self.config.early_morning_start <= start_time <= self.config.early_morning_end:
                early_morning_count += 1
        
        return early_morning_count / len(sessions)
    
    def _compute_weekend_ratio(self, sessions: List[Dict[str, Any]]) -> float:
        """Compute ratio of weekend to weekday play time."""
        weekend_minutes = 0
        weekday_minutes = 0
        
        for session in sessions:
            start = session['session_start']
            end = session['session_end']
            duration_minutes = (end - start).total_seconds() / 60
            
            # 5 = Saturday, 6 = Sunday
            if start.weekday() in [5, 6]:
                weekend_minutes += duration_minutes
            else:
                weekday_minutes += duration_minutes
        
        if weekday_minutes == 0:
            return float('inf') if weekend_minutes > 0 else 1.0
        
        return weekend_minutes / weekday_minutes
    
    def _calculate_time_window_overlap(
        self,
        session_start: datetime,
        session_end: datetime,
        window_start: time,
        window_end: time
    ) -> float:
        """Calculate minutes of overlap with a daily time window."""
        overlap_minutes = 0
        current = session_start
        
        while current < session_end:
            # Check each day the session spans
            day_end = datetime.combine(current.date(), time(23, 59, 59))
            segment_end = min(session_end, day_end)
            
            # Convert window times to datetimes for this day
            if window_start > window_end:  # Window crosses midnight
                # Handle before midnight
                window_dt_start = datetime.combine(current.date(), window_start)
                window_dt_end = datetime.combine(current.date(), time(23, 59, 59))
                overlap_minutes += self._compute_overlap(current, segment_end, window_dt_start, window_dt_end)
                
                # Handle after midnight
                if current.date() < session_end.date():
                    next_day = current.date() + timedelta(days=1)
                    window_dt_start = datetime.combine(next_day, time(0, 0))
                    window_dt_end = datetime.combine(next_day, window_end)
                    overlap_minutes += self._compute_overlap(current, segment_end, window_dt_start, window_dt_end)
            else:  # Normal window within same day
                window_dt_start = datetime.combine(current.date(), window_start)
                window_dt_end = datetime.combine(current.date(), window_end)
                overlap_minutes += self._compute_overlap(current, segment_end, window_dt_start, window_dt_end)
            
            # Move to next day
            current = datetime.combine(current.date() + timedelta(days=1), time(0, 0))
        
        return overlap_minutes
    
    def _compute_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> float:
        """Compute overlap between two time ranges in minutes."""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start < overlap_end:
            return (overlap_end - overlap_start).total_seconds() / 60
        return 0.0
    
    async def _get_engagement_metrics(
        self,
        cohort: Dict[str, str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get engagement metrics for context."""
        # This would query the engagement_aggregates table
        # For now, return placeholder values
        return {
            'avg_npc_attachment_index': 0.5,
            'avg_moral_tension_index': 0.5,
            'dominant_engagement_profile': 'balanced'
        }
    
    def _identify_risk_factors(self, indicators: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors based on indicators."""
        risk_factors = []
        
        # Check each indicator against concerning thresholds
        if indicators.get('night_time_fraction', 0) > self.config.night_time_fraction_threshold:
            risk_factors.append('excessive_night_play')
        
        if indicators.get('one_more_run_loops', 0) > self.config.one_more_run_loops_threshold:
            risk_factors.append('compulsive_restart_pattern')
        
        if indicators.get('excessive_session_fraction', 0) > self.config.excessive_session_fraction_threshold:
            risk_factors.append('marathon_sessions')
        
        if indicators.get('consecutive_days_played_p90', 0) > self.config.consecutive_days_threshold:
            risk_factors.append('no_break_pattern')
        
        if indicators.get('avg_time_between_sessions_hours', 0) < self.config.time_between_sessions_threshold:
            risk_factors.append('insufficient_cooldown')
        
        if indicators.get('weekend_vs_weekday_ratio', 0) < self.config.weekend_ratio_threshold:
            risk_factors.append('weekday_dominance')
        
        return risk_factors
    
    def _compute_confidence(self, sample_size: int) -> float:
        """Compute confidence level based on sample size."""
        # Simple confidence calculation
        # In practice, would use statistical methods
        if sample_size >= 1000:
            return 0.99
        elif sample_size >= 500:
            return 0.95
        elif sample_size >= 100:
            return 0.90
        elif sample_size >= 50:
            return 0.80
        elif sample_size >= 20:
            return 0.70
        else:
            return 0.50
    
    def _empty_indicators(self) -> Dict[str, Any]:
        """Return empty indicator set for cohorts with no data."""
        return {
            'night_time_fraction': None,
            'one_more_run_loops': None,
            'excessive_session_fraction': None,
            'avg_session_duration_hours': None,
            'max_session_duration_hours': None,
            'consecutive_days_played_p90': None,
            'avg_time_between_sessions_hours': None,
            'early_morning_sessions_fraction': None,
            'weekend_vs_weekday_ratio': None,
            'avg_npc_attachment_index': None,
            'avg_moral_tension_index': None,
            'dominant_engagement_profile': None,
            'sample_size': 0,
            'confidence_level': 0.0,
            'risk_factors': []
        }

