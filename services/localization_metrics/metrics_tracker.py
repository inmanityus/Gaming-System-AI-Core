"""
Localization metrics tracking for build-over-build analysis.
Implements TML-10 (R-ML-MET-001, R-ML-MET-002).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncpg
import json
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of localization metrics."""
    # Coverage metrics
    TEXT_COVERAGE = "text_coverage"
    AUDIO_COVERAGE = "audio_coverage"
    TIMING_COVERAGE = "timing_coverage"
    
    # Quality metrics
    TRANSLATION_QUALITY = "translation_quality"
    AUDIO_QUALITY = "audio_quality"
    SYNC_QUALITY = "sync_quality"
    
    # Efficiency metrics
    TRANSLATION_VELOCITY = "translation_velocity"
    AUDIO_GENERATION_TIME = "audio_generation_time"
    BUILD_READINESS = "build_readiness"
    
    # Issue metrics
    MISSING_TRANSLATIONS = "missing_translations"
    PLACEHOLDER_ERRORS = "placeholder_errors"
    UI_OVERFLOW_ISSUES = "ui_overflow_issues"
    
    # Performance metrics
    LOCALIZATION_LOAD_TIME = "localization_load_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    API_RESPONSE_TIME = "api_response_time"


class TrendDirection(str, Enum):
    """Direction of metric trends."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


@dataclass
class MetricSnapshot:
    """A single metric measurement at a point in time."""
    metric_type: MetricType
    value: float
    language_code: str
    build_id: str
    timestamp: datetime
    
    # Optional dimensions
    category: Optional[str] = None
    tier: Optional[int] = None
    
    # Metadata
    sample_size: Optional[int] = None
    confidence: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricTrend:
    """Trend analysis for a metric over time."""
    metric_type: MetricType
    language_code: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Data points
    snapshots: List[MetricSnapshot] = field(default_factory=list)
    
    # Trend analysis
    current_value: float = 0.0
    previous_value: float = 0.0
    change_percentage: float = 0.0
    direction: TrendDirection = TrendDirection.STABLE
    
    # Statistical analysis
    mean: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    
    # Projections
    projected_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    
    # Alerts
    alerts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LocalizationReadiness:
    """Overall localization readiness for a build/language."""
    build_id: str
    language_code: str
    timestamp: datetime
    
    # Readiness scores (0-100)
    overall_score: float = 0.0
    text_score: float = 0.0
    audio_score: float = 0.0
    quality_score: float = 0.0
    
    # Tier recommendation
    recommended_tier: int = 3  # 1=Full, 2=Subtitles, 3=UI only
    current_tier: int = 3
    
    # Blocking issues
    blocking_issues: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Detailed breakdown
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Sign-off status
    ready_for_release: bool = False
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


class LocalizationMetricsTracker:
    """
    Tracks and analyzes localization metrics across builds.
    Provides trend analysis, projections, and readiness assessments.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool, config: Dict[str, Any]):
        self.pool = postgres_pool
        self.config = config
        self.alert_thresholds = self._load_alert_thresholds()
        self.readiness_weights = self._load_readiness_weights()
    
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load thresholds for metric alerts."""
        return {
            MetricType.TEXT_COVERAGE: {
                'critical': 0.7,   # Below 70%
                'warning': 0.85    # Below 85%
            },
            MetricType.AUDIO_COVERAGE: {
                'critical': 0.5,   # Below 50%
                'warning': 0.7     # Below 70%
            },
            MetricType.TRANSLATION_QUALITY: {
                'critical': 0.6,   # Below 60%
                'warning': 0.75    # Below 75%
            },
            MetricType.UI_OVERFLOW_ISSUES: {
                'critical': 50,    # More than 50 issues
                'warning': 20      # More than 20 issues
            },
            MetricType.MISSING_TRANSLATIONS: {
                'critical': 100,   # More than 100 missing
                'warning': 50      # More than 50 missing
            }
        }
    
    def _load_readiness_weights(self) -> Dict[str, float]:
        """Load weights for readiness calculation."""
        return {
            'text_coverage': 0.3,
            'audio_coverage': 0.2,
            'translation_quality': 0.25,
            'ui_issues': 0.15,
            'sync_quality': 0.1
        }
    
    async def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        language_code: str,
        build_id: str,
        category: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Record a metric snapshot."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO localization_metrics
                (metric_type, value, language_code, build_id, category, 
                 timestamp, details)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                metric_type.value,
                value,
                language_code,
                build_id,
                category,
                datetime.utcnow(),
                json.dumps(details or {})
            )
    
    async def calculate_coverage_metrics(
        self,
        build_id: str,
        language_code: str,
        localization_service,
        audio_service=None
    ):
        """Calculate and record coverage metrics."""
        # Text coverage
        coverage_data = await localization_service.repository.calculate_coverage(
            build_id, language_code
        )
        
        text_coverage = coverage_data['coverage_percentage'] / 100
        await self.record_metric(
            MetricType.TEXT_COVERAGE,
            text_coverage,
            language_code,
            build_id,
            details=coverage_data['by_category']
        )
        
        # Record category-specific coverage
        for category_data in coverage_data['by_category']:
            await self.record_metric(
                MetricType.TEXT_COVERAGE,
                category_data['translation_coverage'] / 100,
                language_code,
                build_id,
                category=category_data['category']
            )
        
        # Audio coverage (if service available)
        if audio_service:
            audio_coverage = await audio_service.calculate_coverage(
                language_code,
                list(coverage_data['translated_strings'])
            )
            
            await self.record_metric(
                MetricType.AUDIO_COVERAGE,
                audio_coverage['percentage'] / 100,
                language_code,
                build_id,
                details={
                    'total_strings': audio_coverage['total'],
                    'with_audio': audio_coverage['covered']
                }
            )
    
    async def calculate_quality_metrics(
        self,
        build_id: str,
        language_code: str,
        validation_results: Dict[str, Any]
    ):
        """Calculate and record quality metrics."""
        # Translation quality (based on validation)
        total_strings = validation_results.get('total_strings', 0)
        valid_strings = validation_results.get('valid_strings', 0)
        
        if total_strings > 0:
            quality_score = valid_strings / total_strings
            await self.record_metric(
                MetricType.TRANSLATION_QUALITY,
                quality_score,
                language_code,
                build_id,
                details={
                    'placeholder_errors': validation_results.get('placeholder_errors', 0),
                    'length_issues': validation_results.get('length_issues', 0),
                    'encoding_issues': validation_results.get('encoding_issues', 0)
                }
            )
        
        # UI overflow issues
        ui_issues = validation_results.get('ui_overflow_issues', 0)
        await self.record_metric(
            MetricType.UI_OVERFLOW_ISSUES,
            float(ui_issues),
            language_code,
            build_id,
            details=validation_results.get('ui_issue_details', {})
        )
        
        # Missing translations
        missing = validation_results.get('missing_translations', 0)
        await self.record_metric(
            MetricType.MISSING_TRANSLATIONS,
            float(missing),
            language_code,
            build_id
        )
    
    async def get_trend(
        self,
        metric_type: MetricType,
        language_code: str,
        days: int = 30
    ) -> MetricTrend:
        """Get trend analysis for a metric."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trend = MetricTrend(
            metric_type=metric_type,
            language_code=language_code,
            start_date=start_date,
            end_date=end_date
        )
        
        # Fetch historical data
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT metric_type, value, language_code, build_id, 
                       timestamp, category, details
                FROM localization_metrics
                WHERE metric_type = $1
                  AND language_code = $2
                  AND timestamp >= $3
                  AND timestamp <= $4
                  AND category IS NULL
                ORDER BY timestamp
                """,
                metric_type.value,
                language_code,
                start_date,
                end_date
            )
            
            for row in rows:
                snapshot = MetricSnapshot(
                    metric_type=MetricType(row['metric_type']),
                    value=row['value'],
                    language_code=row['language_code'],
                    build_id=row['build_id'],
                    timestamp=row['timestamp'],
                    category=row['category'],
                    details=json.loads(row['details'] or '{}')
                )
                trend.snapshots.append(snapshot)
        
        # Analyze trend
        self._analyze_trend(trend)
        
        # Check for alerts
        self._check_alerts(trend)
        
        return trend
    
    def _analyze_trend(self, trend: MetricTrend):
        """Analyze trend patterns and statistics."""
        if not trend.snapshots:
            return
        
        values = [s.value for s in trend.snapshots]
        
        # Basic statistics
        trend.current_value = values[-1]
        trend.previous_value = values[-2] if len(values) > 1 else values[-1]
        trend.mean = statistics.mean(values)
        trend.std_dev = statistics.stdev(values) if len(values) > 1 else 0
        trend.min_value = min(values)
        trend.max_value = max(values)
        
        # Change percentage
        if trend.previous_value != 0:
            trend.change_percentage = (
                (trend.current_value - trend.previous_value) / 
                trend.previous_value * 100
            )
        
        # Determine direction
        if len(values) < 3:
            trend.direction = TrendDirection.STABLE
        else:
            # Simple trend detection using recent values
            recent_values = values[-5:]
            
            if self._is_improving(recent_values, trend.metric_type):
                trend.direction = TrendDirection.IMPROVING
            elif self._is_degrading(recent_values, trend.metric_type):
                trend.direction = TrendDirection.DEGRADING
            elif self._is_volatile(recent_values):
                trend.direction = TrendDirection.VOLATILE
            else:
                trend.direction = TrendDirection.STABLE
        
        # Simple linear projection
        if len(values) >= 5:
            trend.projected_value = self._project_value(values)
            
            # Confidence interval (simplified)
            margin = trend.std_dev * 1.96  # 95% confidence
            trend.confidence_interval = (
                max(0, trend.projected_value - margin),
                min(1, trend.projected_value + margin)
            )
    
    def _is_improving(self, values: List[float], metric_type: MetricType) -> bool:
        """Check if metric is improving."""
        if len(values) < 3:
            return False
        
        # For most metrics, higher is better
        positive_metrics = [
            MetricType.TEXT_COVERAGE,
            MetricType.AUDIO_COVERAGE,
            MetricType.TRANSLATION_QUALITY,
            MetricType.CACHE_HIT_RATE
        ]
        
        # For some metrics, lower is better
        negative_metrics = [
            MetricType.MISSING_TRANSLATIONS,
            MetricType.UI_OVERFLOW_ISSUES,
            MetricType.PLACEHOLDER_ERRORS,
            MetricType.API_RESPONSE_TIME
        ]
        
        # Calculate trend
        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])
        
        if metric_type in positive_metrics:
            return second_half > first_half * 1.05  # 5% improvement
        elif metric_type in negative_metrics:
            return second_half < first_half * 0.95  # 5% improvement
        
        return False
    
    def _is_degrading(self, values: List[float], metric_type: MetricType) -> bool:
        """Check if metric is degrading."""
        # Opposite of improving
        if len(values) < 3:
            return False
        
        positive_metrics = [
            MetricType.TEXT_COVERAGE,
            MetricType.AUDIO_COVERAGE,
            MetricType.TRANSLATION_QUALITY,
            MetricType.CACHE_HIT_RATE
        ]
        
        negative_metrics = [
            MetricType.MISSING_TRANSLATIONS,
            MetricType.UI_OVERFLOW_ISSUES,
            MetricType.PLACEHOLDER_ERRORS,
            MetricType.API_RESPONSE_TIME
        ]
        
        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])
        
        if metric_type in positive_metrics:
            return second_half < first_half * 0.95  # 5% degradation
        elif metric_type in negative_metrics:
            return second_half > first_half * 1.05  # 5% degradation
        
        return False
    
    def _is_volatile(self, values: List[float]) -> bool:
        """Check if metric is volatile."""
        if len(values) < 3:
            return False
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        # High coefficient of variation indicates volatility
        cv = std_dev / mean if mean != 0 else 0
        return cv > 0.3  # 30% coefficient of variation
    
    def _project_value(self, values: List[float]) -> float:
        """Simple linear projection."""
        # Use recent trend for projection
        recent_values = values[-5:]
        
        if len(recent_values) < 2:
            return values[-1]
        
        # Simple linear regression
        x = list(range(len(recent_values)))
        y = recent_values
        
        # Calculate slope
        n = len(x)
        xy_sum = sum(x[i] * y[i] for i in range(n))
        x_sum = sum(x)
        y_sum = sum(y)
        x_squared_sum = sum(x[i] ** 2 for i in range(n))
        
        if (n * x_squared_sum - x_sum ** 2) != 0:
            slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum ** 2)
            intercept = (y_sum - slope * x_sum) / n
            
            # Project next value
            next_x = n
            projected = slope * next_x + intercept
            
            # Bound to reasonable range
            return max(0, min(1, projected))
        
        return values[-1]
    
    def _check_alerts(self, trend: MetricTrend):
        """Check for alert conditions."""
        if trend.metric_type not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[trend.metric_type]
        current = trend.current_value
        
        # Critical alerts
        if 'critical' in thresholds:
            if (trend.metric_type in [MetricType.TEXT_COVERAGE, 
                                     MetricType.AUDIO_COVERAGE,
                                     MetricType.TRANSLATION_QUALITY]):
                # Lower is bad
                if current < thresholds['critical']:
                    trend.alerts.append({
                        'level': 'critical',
                        'message': f'{trend.metric_type.value} is critically low: {current:.2f}',
                        'threshold': thresholds['critical']
                    })
            else:
                # Higher is bad
                if current > thresholds['critical']:
                    trend.alerts.append({
                        'level': 'critical',
                        'message': f'{trend.metric_type.value} is critically high: {current:.2f}',
                        'threshold': thresholds['critical']
                    })
        
        # Warning alerts
        if 'warning' in thresholds and not trend.alerts:
            if (trend.metric_type in [MetricType.TEXT_COVERAGE,
                                     MetricType.AUDIO_COVERAGE,
                                     MetricType.TRANSLATION_QUALITY]):
                if current < thresholds['warning']:
                    trend.alerts.append({
                        'level': 'warning',
                        'message': f'{trend.metric_type.value} is below warning threshold: {current:.2f}',
                        'threshold': thresholds['warning']
                    })
            else:
                if current > thresholds['warning']:
                    trend.alerts.append({
                        'level': 'warning',
                        'message': f'{trend.metric_type.value} is above warning threshold: {current:.2f}',
                        'threshold': thresholds['warning']
                    })
        
        # Trend alerts
        if trend.direction == TrendDirection.DEGRADING:
            trend.alerts.append({
                'level': 'warning',
                'message': f'{trend.metric_type.value} is showing degrading trend',
                'change': trend.change_percentage
            })
    
    async def calculate_readiness(
        self,
        build_id: str,
        language_code: str
    ) -> LocalizationReadiness:
        """Calculate overall localization readiness."""
        readiness = LocalizationReadiness(
            build_id=build_id,
            language_code=language_code,
            timestamp=datetime.utcnow()
        )
        
        # Get latest metrics
        async with self.pool.acquire() as conn:
            metrics = {}
            
            # Get latest value for each metric type
            for metric_type in MetricType:
                row = await conn.fetchrow(
                    """
                    SELECT value, details
                    FROM localization_metrics
                    WHERE metric_type = $1
                      AND language_code = $2
                      AND build_id = $3
                      AND category IS NULL
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    metric_type.value,
                    language_code,
                    build_id
                )
                
                if row:
                    metrics[metric_type.value] = row['value']
        
        readiness.metrics = metrics
        
        # Calculate component scores
        readiness.text_score = self._calculate_text_score(metrics)
        readiness.audio_score = self._calculate_audio_score(metrics)
        readiness.quality_score = self._calculate_quality_score(metrics)
        
        # Calculate overall score
        readiness.overall_score = (
            readiness.text_score * self.readiness_weights['text_coverage'] +
            readiness.audio_score * self.readiness_weights['audio_coverage'] +
            readiness.quality_score * self.readiness_weights['translation_quality']
        ) * 100
        
        # Determine tier recommendation
        readiness.recommended_tier = self._recommend_tier(readiness)
        
        # Check for blocking issues
        self._check_blocking_issues(readiness, metrics)
        
        # Determine if ready for release
        readiness.ready_for_release = (
            readiness.overall_score >= 80 and
            len(readiness.blocking_issues) == 0
        )
        
        return readiness
    
    def _calculate_text_score(self, metrics: Dict[str, float]) -> float:
        """Calculate text readiness score."""
        text_coverage = metrics.get(MetricType.TEXT_COVERAGE.value, 0)
        missing = metrics.get(MetricType.MISSING_TRANSLATIONS.value, 0)
        
        # Penalize for missing translations
        missing_penalty = min(0.3, missing / 1000)  # Max 30% penalty
        
        return max(0, text_coverage - missing_penalty)
    
    def _calculate_audio_score(self, metrics: Dict[str, float]) -> float:
        """Calculate audio readiness score."""
        audio_coverage = metrics.get(MetricType.AUDIO_COVERAGE.value, 0)
        sync_quality = metrics.get(MetricType.SYNC_QUALITY.value, 1.0)
        
        # Weight coverage more than sync quality
        return audio_coverage * 0.8 + sync_quality * 0.2
    
    def _calculate_quality_score(self, metrics: Dict[str, float]) -> float:
        """Calculate quality readiness score."""
        translation_quality = metrics.get(MetricType.TRANSLATION_QUALITY.value, 0)
        ui_issues = metrics.get(MetricType.UI_OVERFLOW_ISSUES.value, 0)
        placeholder_errors = metrics.get(MetricType.PLACEHOLDER_ERRORS.value, 0)
        
        # Penalties for issues
        ui_penalty = min(0.3, ui_issues / 100)  # Max 30% penalty
        placeholder_penalty = min(0.2, placeholder_errors / 50)  # Max 20% penalty
        
        return max(0, translation_quality - ui_penalty - placeholder_penalty)
    
    def _recommend_tier(self, readiness: LocalizationReadiness) -> int:
        """Recommend localization tier based on scores."""
        # Tier 1: Full support (text, audio, voice)
        if (readiness.text_score >= 0.95 and
            readiness.audio_score >= 0.90 and
            readiness.quality_score >= 0.85 and
            readiness.overall_score >= 90):
            return 1
        
        # Tier 2: Subtitles only (text, no voice)
        elif (readiness.text_score >= 0.85 and
              readiness.quality_score >= 0.75 and
              readiness.overall_score >= 75):
            return 2
        
        # Tier 3: UI only (basic text)
        else:
            return 3
    
    def _check_blocking_issues(
        self,
        readiness: LocalizationReadiness,
        metrics: Dict[str, float]
    ):
        """Check for issues that block release."""
        # Critical text coverage
        text_coverage = metrics.get(MetricType.TEXT_COVERAGE.value, 0)
        if text_coverage < 0.7:
            readiness.blocking_issues.append({
                'type': 'low_text_coverage',
                'severity': 'critical',
                'message': f'Text coverage too low: {text_coverage:.1%}',
                'required': 0.7
            })
        
        # Placeholder errors
        placeholder_errors = metrics.get(MetricType.PLACEHOLDER_ERRORS.value, 0)
        if placeholder_errors > 0:
            readiness.blocking_issues.append({
                'type': 'placeholder_errors',
                'severity': 'critical',
                'message': f'Placeholder errors found: {int(placeholder_errors)}',
                'details': 'These will cause runtime errors'
            })
        
        # Excessive UI issues
        ui_issues = metrics.get(MetricType.UI_OVERFLOW_ISSUES.value, 0)
        if ui_issues > 50:
            readiness.blocking_issues.append({
                'type': 'ui_overflow',
                'severity': 'high',
                'message': f'Too many UI overflow issues: {int(ui_issues)}',
                'threshold': 50
            })
        
        # Add warnings for non-blocking issues
        if text_coverage < 0.85:
            readiness.warnings.append(
                f'Text coverage below target: {text_coverage:.1%} < 85%'
            )
        
        audio_coverage = metrics.get(MetricType.AUDIO_COVERAGE.value, 0)
        if readiness.recommended_tier == 1 and audio_coverage < 0.8:
            readiness.warnings.append(
                f'Audio coverage low for Tier 1: {audio_coverage:.1%} < 80%'
            )
    
    async def get_dashboard_data(
        self,
        build_id: str,
        languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        if not languages:
            # Get all active languages
            languages = await self._get_active_languages()
        
        dashboard = {
            'build_id': build_id,
            'generated_at': datetime.utcnow().isoformat(),
            'languages': {},
            'summary': {
                'ready_count': 0,
                'blocked_count': 0,
                'warning_count': 0
            }
        }
        
        for language in languages:
            # Get readiness
            readiness = await self.calculate_readiness(build_id, language)
            
            # Get key trends
            text_trend = await self.get_trend(
                MetricType.TEXT_COVERAGE, language, days=7
            )
            quality_trend = await self.get_trend(
                MetricType.TRANSLATION_QUALITY, language, days=7
            )
            
            dashboard['languages'][language] = {
                'readiness': {
                    'overall_score': readiness.overall_score,
                    'tier': readiness.recommended_tier,
                    'ready': readiness.ready_for_release,
                    'blocking_issues': len(readiness.blocking_issues),
                    'warnings': len(readiness.warnings)
                },
                'trends': {
                    'text_coverage': {
                        'current': text_trend.current_value,
                        'change': text_trend.change_percentage,
                        'direction': text_trend.direction.value
                    },
                    'quality': {
                        'current': quality_trend.current_value,
                        'change': quality_trend.change_percentage,
                        'direction': quality_trend.direction.value
                    }
                },
                'alerts': text_trend.alerts + quality_trend.alerts
            }
            
            # Update summary
            if readiness.ready_for_release:
                dashboard['summary']['ready_count'] += 1
            if readiness.blocking_issues:
                dashboard['summary']['blocked_count'] += 1
            if readiness.warnings:
                dashboard['summary']['warning_count'] += 1
        
        return dashboard
    
    async def _get_active_languages(self) -> List[str]:
        """Get list of languages with recent activity."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT language_code
                FROM localization_metrics
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
                ORDER BY language_code
                """
            )
            
            return [row['language_code'] for row in rows]
    
    async def export_metrics_report(
        self,
        build_id: str,
        start_date: datetime,
        end_date: datetime,
        format: str = 'json'
    ) -> str:
        """Export detailed metrics report."""
        # Gather all data
        report_data = {
            'build_id': build_id,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'languages': {}
        }
        
        languages = await self._get_active_languages()
        
        for language in languages:
            language_data = {
                'metrics': {},
                'readiness': None,
                'trends': {}
            }
            
            # Get all metric trends
            for metric_type in MetricType:
                trend = await self.get_trend(
                    metric_type,
                    language,
                    days=(end_date - start_date).days
                )
                
                language_data['trends'][metric_type.value] = {
                    'current': trend.current_value,
                    'mean': trend.mean,
                    'std_dev': trend.std_dev,
                    'min': trend.min_value,
                    'max': trend.max_value,
                    'direction': trend.direction.value,
                    'change_percentage': trend.change_percentage,
                    'data_points': len(trend.snapshots)
                }
            
            # Get readiness
            readiness = await self.calculate_readiness(build_id, language)
            language_data['readiness'] = {
                'overall_score': readiness.overall_score,
                'tier': readiness.recommended_tier,
                'ready': readiness.ready_for_release,
                'issues': readiness.blocking_issues,
                'warnings': readiness.warnings
            }
            
            report_data['languages'][language] = language_data
        
        if format == 'json':
            return json.dumps(report_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
