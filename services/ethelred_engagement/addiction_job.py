"""
Addiction Risk Analytics Job
Runs on schedule to compute cohort-level addiction risk indicators
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
import json
import asyncpg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from services.ethelred_engagement.addiction_indicators import AddictionIndicatorCalculator
from services.ethelred_engagement.report_generator import AddictionReportGenerator

logger = logging.getLogger(__name__)


class AddictionRiskJob:
    """
    Scheduled job that computes cohort-level addiction risk indicators
    from engagement telemetry data.
    
    CRITICAL: Only computes cohort-level metrics, never individual player metrics.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool, nats_client: Any):
        self.postgres = postgres_pool
        self.nats = nats_client
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # Initialize indicator calculator and report generator
        self.indicator_calculator = AddictionIndicatorCalculator(postgres_pool)
        self.report_generator = AddictionReportGenerator(postgres_pool)
        
        # Cohort dimensions for grouping
        self.COHORT_DIMENSIONS = ['region', 'age_band', 'platform']
        
        # Thresholds cache
        self._thresholds_cache = {}
        self._thresholds_last_loaded = None
    
    async def start(self):
        """Start the scheduled job."""
        if self.is_running:
            logger.warning("AddictionRiskJob is already running")
            return
            
        self.is_running = True
        
        # Schedule daily runs at 3 AM UTC
        self.scheduler.add_job(
            self._run_risk_analysis,
            CronTrigger(hour=3, minute=0),
            id='addiction_risk_daily',
            name='Daily Addiction Risk Analysis',
            replace_existing=True
        )
        
        # Schedule weekly comprehensive reports on Sundays
        self.scheduler.add_job(
            self._run_comprehensive_report,
            CronTrigger(day_of_week='sun', hour=4, minute=0),
            id='addiction_risk_weekly',
            name='Weekly Comprehensive Risk Report',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("AddictionRiskJob started with daily and weekly schedules")
    
    async def stop(self):
        """Stop the scheduled job."""
        if not self.is_running:
            return
            
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("AddictionRiskJob stopped")
    
    async def _load_risk_thresholds(self):
        """Load risk thresholds from database."""
        # Cache thresholds for 1 hour
        if (self._thresholds_last_loaded and 
            datetime.utcnow() - self._thresholds_last_loaded < timedelta(hours=1)):
            return self._thresholds_cache
            
        async with self.postgres.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT metric_name, healthy_max, moderate_max, concerning_max
                FROM addiction_risk_thresholds
                WHERE enabled = TRUE
                """
            )
            
        self._thresholds_cache = {
            row['metric_name']: {
                'healthy_max': row['healthy_max'],
                'moderate_max': row['moderate_max'],
                'concerning_max': row['concerning_max']
            }
            for row in rows
        }
        self._thresholds_last_loaded = datetime.utcnow()
        
        return self._thresholds_cache
    
    def _determine_risk_level(self, metrics: Dict[str, float], thresholds: Dict) -> str:
        """
        Determine overall risk level based on metrics and thresholds.
        Uses a weighted approach where severe indicators dominate.
        """
        risk_scores = []
        
        for metric_name, value in metrics.items():
            if metric_name not in thresholds or value is None:
                continue
                
            thresh = thresholds[metric_name]
            if value <= thresh['healthy_max']:
                risk_scores.append(0)
            elif value <= thresh['moderate_max']:
                risk_scores.append(1)
            elif value <= thresh['concerning_max']:
                risk_scores.append(2)
            else:
                risk_scores.append(3)
        
        if not risk_scores:
            return 'healthy'
            
        # If any metric is severe, overall is at least concerning
        max_risk = max(risk_scores)
        avg_risk = sum(risk_scores) / len(risk_scores)
        
        if max_risk >= 3:
            return 'severe'
        elif max_risk >= 2 or avg_risk >= 1.5:
            return 'concerning'
        elif avg_risk >= 0.5:
            return 'moderate'
        else:
            return 'healthy'
    
    async def _run_risk_analysis(self):
        """Run daily addiction risk analysis."""
        logger.info("Starting daily addiction risk analysis")
        try:
            # Get distinct cohorts from recent data
            cohorts = await self._get_active_cohorts()
            logger.info(f"Found {len(cohorts)} active cohorts to analyze")
            
            # Load risk thresholds
            thresholds = await self._load_risk_thresholds()
            
            # Process each cohort
            for cohort in cohorts:
                try:
                    await self._analyze_cohort(cohort, thresholds)
                except Exception as e:
                    logger.error(f"Error analyzing cohort {cohort}: {e}", exc_info=True)
                    # Continue with other cohorts
            
            logger.info("Daily addiction risk analysis completed")
            
        except Exception as e:
            logger.error(f"Error in addiction risk analysis: {e}", exc_info=True)
    
    async def _run_comprehensive_report(self):
        """Run weekly comprehensive report generation."""
        logger.info("Starting weekly comprehensive addiction risk report")
        try:
            # Generate comprehensive report
            build_id = 'current-build'  # TODO: Get from config/context
            report_date = datetime.utcnow()
            
            report_result = await self.report_generator.generate_weekly_report(
                build_id, report_date
            )
            
            logger.info(f"Generated comprehensive report: {report_result['report_id']}")
            
            # Emit event about report availability
            await self._emit_report_event(report_result)
            
            # If any cohorts show severe risk, emit alert
            risk_summary = report_result['risk_summary']
            if risk_summary.get('severe', 0) > 0:
                await self._emit_severe_risk_alert(build_id, risk_summary)
            
        except Exception as e:
            logger.error(f"Error in comprehensive report: {e}", exc_info=True)
    
    async def _get_active_cohorts(self, days_back: int = 7) -> List[Dict[str, str]]:
        """Get list of cohorts with recent activity."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        async with self.postgres.acquire() as conn:
            # Get distinct cohort combinations from recent engagement events
            # This is a placeholder query - actual implementation depends on telemetry schema
            rows = await conn.fetch(
                """
                SELECT DISTINCT 
                    cohort_metadata->>'region' as region,
                    cohort_metadata->>'age_band' as age_band,
                    cohort_metadata->>'platform' as platform
                FROM engagement_events
                WHERE created_at > $1
                    AND cohort_metadata IS NOT NULL
                    AND cohort_metadata->>'region' IS NOT NULL
                """,
                cutoff
            )
            
        return [dict(row) for row in rows]
    
    async def _analyze_cohort(self, cohort: Dict[str, str], thresholds: Dict):
        """Analyze addiction risk for a specific cohort."""
        logger.info(f"Analyzing cohort: {cohort}")
        
        # Define analysis window (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Compute addiction indicators
        indicators = await self.indicator_calculator.compute_indicators(
            cohort, start_date, end_date
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(indicators, thresholds)
        
        # Identify high-risk features (placeholder - would analyze feature usage)
        high_risk_features = await self._identify_high_risk_features(
            cohort, indicators, start_date, end_date
        )
        
        # Generate recommendations based on risk factors
        recommendations = self._generate_recommendations(
            indicators.get('risk_factors', []),
            high_risk_features
        )
        
        # Build report
        report_data = {
            'build_id': 'current-build',  # TODO: Get from config/context
            'report_date': datetime.utcnow().date(),
            'cohort_identifier': cohort,
            'night_time_fraction': indicators.get('night_time_fraction'),
            'one_more_run_loops': indicators.get('one_more_run_loops'),
            'excessive_session_fraction': indicators.get('excessive_session_fraction'),
            'avg_session_duration_hours': indicators.get('avg_session_duration_hours'),
            'max_session_duration_hours': indicators.get('max_session_duration_hours'),
            'consecutive_days_played_p90': indicators.get('consecutive_days_played_p90'),
            'avg_time_between_sessions_hours': indicators.get('avg_time_between_sessions_hours'),
            'early_morning_sessions_fraction': indicators.get('early_morning_sessions_fraction'),
            'weekend_vs_weekday_ratio': indicators.get('weekend_vs_weekday_ratio'),
            'avg_npc_attachment_index': indicators.get('avg_npc_attachment_index'),
            'avg_moral_tension_index': indicators.get('avg_moral_tension_index'),
            'dominant_engagement_profile': indicators.get('dominant_engagement_profile'),
            'sample_size': indicators.get('sample_size', 0),
            'confidence_level': indicators.get('confidence_level', 0.0),
            'risk_level': risk_level,
            'risk_factors': indicators.get('risk_factors', []),
            'recommendations': recommendations,
            'high_risk_features': high_risk_features
        }
        
        # Store the report
        await self._store_report(report_data)
        
        # Emit event
        await self._emit_risk_event(report_data)
    
    async def _store_report(self, report_data: Dict[str, Any]):
        """Store addiction risk report in database."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO addiction_risk_reports (
                    build_id, report_date, cohort_identifier,
                    night_time_fraction, one_more_run_loops, excessive_session_fraction,
                    avg_session_duration_hours, max_session_duration_hours,
                    consecutive_days_played_p90, avg_time_between_sessions_hours,
                    early_morning_sessions_fraction, weekend_vs_weekday_ratio,
                    avg_npc_attachment_index, avg_moral_tension_index, dominant_engagement_profile,
                    sample_size, confidence_level, risk_level,
                    risk_factors, recommendations, high_risk_features
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                """,
                report_data['build_id'],
                report_data['report_date'],
                json.dumps(report_data['cohort_identifier']),
                report_data['night_time_fraction'],
                report_data['one_more_run_loops'],
                report_data['excessive_session_fraction'],
                report_data['avg_session_duration_hours'],
                report_data['max_session_duration_hours'],
                report_data['consecutive_days_played_p90'],
                report_data['avg_time_between_sessions_hours'],
                report_data['early_morning_sessions_fraction'],
                report_data['weekend_vs_weekday_ratio'],
                report_data['avg_npc_attachment_index'],
                report_data['avg_moral_tension_index'],
                report_data['dominant_engagement_profile'],
                report_data['sample_size'],
                report_data['confidence_level'],
                report_data['risk_level'],
                report_data['risk_factors'],
                report_data['recommendations'],
                json.dumps(report_data['high_risk_features'])
            )
    
    async def _emit_risk_event(self, report_data: Dict[str, Any]):
        """Emit addiction risk event to NATS."""
        # Event structure following canonical pattern
        event = {
            'trace_id': str(uuid4().hex),
            'timestamp': datetime.utcnow(timezone.utc).isoformat(),
            'build_id': report_data['build_id'],
            'domain': 'Engagement',
            'issue_type': 'ADDICTION_RISK_REPORT',
            'severity': self._risk_to_severity(report_data['risk_level']),
            'confidence': report_data['confidence_level'],
            'payload': report_data
        }
        
        await self.nats.publish(
            'events.ethelred.emo.v1.addiction_risk',
            json.dumps(event).encode()
        )
    
    def _risk_to_severity(self, risk_level: str) -> str:
        """Map risk level to event severity."""
        mapping = {
            'healthy': 'INFO',
            'moderate': 'WARNING',
            'concerning': 'ERROR',
            'severe': 'CRITICAL'
        }
        return mapping.get(risk_level, 'INFO')
    
    async def _identify_high_risk_features(
        self,
        cohort: Dict[str, str],
        indicators: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Identify game features correlated with addiction indicators.
        This is a placeholder - would analyze feature usage data.
        """
        high_risk_features = []
        
        # In a real implementation, would correlate feature usage with risk indicators
        # For now, return example features based on risk factors
        risk_factors = indicators.get('risk_factors', [])
        
        if 'marathon_sessions' in risk_factors:
            high_risk_features.append({
                'feature': 'endless_mode',
                'correlation': 0.73,
                'description': 'Endless game mode associated with long sessions'
            })
        
        if 'compulsive_restart_pattern' in risk_factors:
            high_risk_features.append({
                'feature': 'quick_restart_button',
                'correlation': 0.65,
                'description': 'Quick restart feature enabling rapid re-engagement'
            })
        
        if 'excessive_night_play' in risk_factors:
            high_risk_features.append({
                'feature': 'night_events',
                'correlation': 0.58,
                'description': 'Time-limited events occurring at night'
            })
        
        return high_risk_features
    
    def _generate_recommendations(
        self,
        risk_factors: List[str],
        high_risk_features: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate design recommendations based on risk analysis."""
        recommendations = []
        
        # Map risk factors to recommendations
        factor_recommendations = {
            'excessive_night_play': 'Consider adding gentle reminders about healthy play times after 11 PM',
            'compulsive_restart_pattern': 'Add cooldown periods or reflection moments between rapid restarts',
            'marathon_sessions': 'Implement session break suggestions after 2-3 hours of continuous play',
            'no_break_pattern': 'Design daily/weekly content that encourages natural break points',
            'insufficient_cooldown': 'Increase time-gated content to discourage immediate re-engagement',
            'weekday_dominance': 'Review if game systems inadvertently punish weekend-only players'
        }
        
        for factor in risk_factors:
            if factor in factor_recommendations:
                recommendations.append(factor_recommendations[factor])
        
        # Add feature-specific recommendations
        for feature in high_risk_features:
            if feature['correlation'] > 0.6:
                recommendations.append(
                    f"Review {feature['feature']}: {feature['description']}"
                )
        
        # Always include safety reminder
        recommendations.append(
            'All changes should prioritize player wellbeing over engagement metrics'
        )
        
        return recommendations
    
    async def _emit_report_event(self, report_result: Dict[str, Any]):
        """Emit event about comprehensive report availability."""
        event = {
            'trace_id': str(uuid4().hex),
            'timestamp': datetime.utcnow(timezone.utc).isoformat(),
            'build_id': report_result.get('build_id', 'current-build'),
            'domain': 'Engagement',
            'issue_type': 'ADDICTION_REPORT_GENERATED',
            'severity': 'INFO',
            'confidence': 1.0,
            'payload': {
                'report_id': report_result['report_id'],
                'report_date': report_result['report_date'].isoformat(),
                'cohorts_analyzed': report_result['cohorts_analyzed'],
                'risk_summary': report_result['risk_summary']
            }
        }
        
        await self.nats.publish(
            'events.ethelred.emo.v1.report_generated',
            json.dumps(event).encode()
        )
    
    async def _emit_severe_risk_alert(self, build_id: str, risk_summary: Dict[str, int]):
        """Emit alert when severe addiction risk is detected."""
        event = {
            'trace_id': str(uuid4().hex),
            'timestamp': datetime.utcnow(timezone.utc).isoformat(),
            'build_id': build_id,
            'domain': 'Engagement',
            'issue_type': 'SEVERE_ADDICTION_RISK_DETECTED',
            'severity': 'CRITICAL',
            'confidence': 0.95,
            'payload': {
                'severe_cohorts': risk_summary['severe'],
                'concerning_cohorts': risk_summary.get('concerning', 0),
                'message': f"{risk_summary['severe']} cohorts show severe addiction risk indicators"
            }
        }
        
        await self.nats.publish(
            'events.ethelred.emo.v1.severe_risk_alert',
            json.dumps(event).encode()
        )


# Service entry point
async def main():
    """Main entry point for the addiction risk job."""
    logging.basicConfig(level=logging.INFO)
    
    # In production, these would come from config
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ethelred',
        'user': 'postgres',
        'password': 'password'
    }
    
    # Create connection pool
    postgres_pool = await asyncpg.create_pool(**db_config, min_size=1, max_size=5)
    
    # Create NATS client (placeholder)
    class MockNats:
        async def publish(self, subject, data):
            logger.info(f"Would publish to {subject}: {len(data)} bytes")
    
    nats_client = MockNats()
    
    # Create and start job
    job = AddictionRiskJob(postgres_pool, nats_client)
    await job.start()
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down addiction risk job")
        await job.stop()
        await postgres_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
