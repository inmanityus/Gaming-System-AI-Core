"""
Design-facing report generator for addiction risk analytics.
Generates human-readable reports for designers and ethics reviewers.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import asyncpg
from jinja2 import Template
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import base64

logger = logging.getLogger(__name__)


class AddictionReportGenerator:
    """
    Generates human-readable reports from addiction risk data.
    
    CRITICAL: Reports focus on cohort-level patterns only, never individual players.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres = postgres_pool
        
        # HTML template for reports
        self.report_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>Addiction Risk Report - {{ report_date }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #333; }
        .warning { background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .critical { background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .info { background-color: #d1ecf1; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .metric { margin: 15px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }
        .recommendation { margin: 10px 0; padding: 10px; background: #e7f3ff; border-left: 4px solid #0056b3; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .chart { margin: 20px 0; text-align: center; }
        .risk-healthy { color: #28a745; }
        .risk-moderate { color: #ffc107; }
        .risk-concerning { color: #fd7e14; }
        .risk-severe { color: #dc3545; }
    </style>
</head>
<body>
    <h1>Addiction Risk Analysis Report</h1>
    <div class="info">
        <strong>Report Date:</strong> {{ report_date }}<br>
        <strong>Analysis Period:</strong> {{ start_date }} to {{ end_date }}<br>
        <strong>Build:</strong> {{ build_id }}
    </div>
    
    <div class="warning">
        <strong>⚠️ Ethics Notice:</strong> This report analyzes cohort-level patterns only. 
        No individual player data is included. All recommendations should prioritize player 
        wellbeing over engagement metrics.
    </div>
    
    <h2>Executive Summary</h2>
    <p>{{ executive_summary }}</p>
    
    <h2>Risk Distribution by Cohort</h2>
    <table>
        <thead>
            <tr>
                <th>Cohort</th>
                <th>Risk Level</th>
                <th>Sample Size</th>
                <th>Key Indicators</th>
            </tr>
        </thead>
        <tbody>
            {% for cohort in cohort_summaries %}
            <tr>
                <td>{{ cohort.identifier }}</td>
                <td class="risk-{{ cohort.risk_level }}">{{ cohort.risk_level|upper }}</td>
                <td>{{ cohort.sample_size }}</td>
                <td>{{ cohort.key_indicators|join(', ') }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <h2>Key Metrics Overview</h2>
    {% for metric in key_metrics %}
    <div class="metric">
        <strong>{{ metric.name }}:</strong> {{ metric.description }}<br>
        <small>Healthy: ≤{{ metric.healthy_max }}, Moderate: ≤{{ metric.moderate_max }}, 
        Concerning: ≤{{ metric.concerning_max }}</small>
    </div>
    {% endfor %}
    
    <h2>Risk Indicator Trends</h2>
    <div class="chart">
        <img src="data:image/png;base64,{{ trend_chart }}" alt="Risk Indicator Trends">
    </div>
    
    <h2>High-Risk Features Analysis</h2>
    {% if high_risk_features %}
    <table>
        <thead>
            <tr>
                <th>Feature</th>
                <th>Correlation</th>
                <th>Description</th>
                <th>Affected Cohorts</th>
            </tr>
        </thead>
        <tbody>
            {% for feature in high_risk_features %}
            <tr>
                <td>{{ feature.name }}</td>
                <td>{{ "%.2f"|format(feature.correlation) }}</td>
                <td>{{ feature.description }}</td>
                <td>{{ feature.affected_cohorts|length }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>No specific features identified as high-risk in this analysis period.</p>
    {% endif %}
    
    <h2>Design Recommendations</h2>
    {% for rec in recommendations %}
    <div class="recommendation">
        <strong>{{ rec.category }}:</strong> {{ rec.text }}
        {% if rec.priority == 'high' %}
        <span style="color: red;">[HIGH PRIORITY]</span>
        {% endif %}
    </div>
    {% endfor %}
    
    <h2>Comparison with Previous Period</h2>
    {% if comparison %}
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Current Period</th>
                <th>Previous Period</th>
                <th>Change</th>
            </tr>
        </thead>
        <tbody>
            {% for comp in comparison %}
            <tr>
                <td>{{ comp.metric }}</td>
                <td>{{ "%.2f"|format(comp.current) }}</td>
                <td>{{ "%.2f"|format(comp.previous) }}</td>
                <td class="{% if comp.change > 0.1 %}risk-concerning{% elif comp.change < -0.1 %}risk-healthy{% endif %}">
                    {{ "%+.2f"|format(comp.change) }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>No previous period data available for comparison.</p>
    {% endif %}
    
    <h2>Appendix: Methodology</h2>
    <div class="info">
        <p>This report analyzes the following addiction risk indicators:</p>
        <ul>
            <li><strong>Night-time Play Fraction:</strong> Percentage of gameplay occurring between 11 PM and 5 AM</li>
            <li><strong>One More Run Loops:</strong> Frequency of immediate session restarts</li>
            <li><strong>Excessive Sessions:</strong> Proportion of sessions exceeding 4 hours</li>
            <li><strong>Consecutive Days:</strong> 90th percentile of continuous play streaks</li>
            <li><strong>Early Morning Sessions:</strong> Sessions starting between 2 AM and 6 AM</li>
        </ul>
        <p>All metrics are computed at cohort level with minimum sample sizes to ensure statistical validity 
        and player privacy.</p>
    </div>
    
    <div class="warning">
        <strong>Confidentiality:</strong> This report contains sensitive game health metrics. 
        Please handle according to company data classification policies.
    </div>
</body>
</html>
        """)
    
    async def generate_weekly_report(self, build_id: str, report_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive weekly addiction risk report."""
        logger.info(f"Generating weekly report for {report_date}")
        
        # Define report period
        end_date = report_date
        start_date = end_date - timedelta(days=7)
        
        # Fetch report data
        cohort_data = await self._fetch_cohort_reports(build_id, start_date, end_date)
        metric_definitions = await self._fetch_metric_definitions()
        previous_data = await self._fetch_previous_period_data(build_id, start_date)
        
        # Analyze and aggregate
        executive_summary = self._generate_executive_summary(cohort_data)
        cohort_summaries = self._summarize_cohorts(cohort_data)
        high_risk_features = self._aggregate_high_risk_features(cohort_data)
        recommendations = self._consolidate_recommendations(cohort_data, high_risk_features)
        comparison = self._compare_periods(cohort_data, previous_data)
        
        # Generate visualizations
        trend_chart = await self._generate_trend_chart(cohort_data)
        
        # Render HTML report
        html_content = self.report_template.render(
            report_date=report_date.strftime("%Y-%m-%d"),
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            build_id=build_id,
            executive_summary=executive_summary,
            cohort_summaries=cohort_summaries,
            key_metrics=metric_definitions,
            trend_chart=trend_chart,
            high_risk_features=high_risk_features,
            recommendations=recommendations,
            comparison=comparison
        )
        
        # Store report
        report_id = await self._store_report(build_id, report_date, html_content)
        
        return {
            'report_id': report_id,
            'report_date': report_date,
            'cohorts_analyzed': len(cohort_data),
            'risk_summary': self._get_risk_summary(cohort_data),
            'html_content': html_content
        }
    
    async def _fetch_cohort_reports(
        self, 
        build_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch cohort reports for the period."""
        async with self.postgres.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM addiction_risk_reports
                WHERE build_id = $1 
                    AND report_date BETWEEN $2 AND $3
                ORDER BY report_date, cohort_identifier
                """,
                build_id, start_date.date(), end_date.date()
            )
        
        return [dict(row) for row in rows]
    
    async def _fetch_metric_definitions(self) -> List[Dict[str, Any]]:
        """Fetch metric threshold definitions."""
        async with self.postgres.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT metric_name, description, unit, 
                       healthy_max, moderate_max, concerning_max
                FROM addiction_risk_thresholds
                WHERE enabled = TRUE
                ORDER BY metric_name
                """
            )
        
        return [{
            'name': row['metric_name'].replace('_', ' ').title(),
            'description': row['description'],
            'unit': row['unit'],
            'healthy_max': row['healthy_max'],
            'moderate_max': row['moderate_max'],
            'concerning_max': row['concerning_max']
        } for row in rows]
    
    async def _fetch_previous_period_data(
        self, 
        build_id: str, 
        current_start: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch data from previous period for comparison."""
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=7)
        
        return await self._fetch_cohort_reports(build_id, previous_start, previous_end)
    
    def _generate_executive_summary(self, cohort_data: List[Dict[str, Any]]) -> str:
        """Generate executive summary of findings."""
        if not cohort_data:
            return "No cohort data available for this period."
        
        total_cohorts = len(cohort_data)
        risk_counts = {'healthy': 0, 'moderate': 0, 'concerning': 0, 'severe': 0}
        
        for cohort in cohort_data:
            risk_counts[cohort['risk_level']] += 1
        
        severe_pct = (risk_counts['severe'] / total_cohorts) * 100
        concerning_pct = (risk_counts['concerning'] / total_cohorts) * 100
        
        summary = f"Analyzed {total_cohorts} player cohorts during this period. "
        
        if risk_counts['severe'] > 0:
            summary += f"⚠️ {risk_counts['severe']} cohorts ({severe_pct:.1f}%) show severe addiction risk indicators. "
        
        if risk_counts['concerning'] > 0:
            summary += f"{risk_counts['concerning']} cohorts ({concerning_pct:.1f}%) show concerning patterns. "
        
        if risk_counts['severe'] == 0 and risk_counts['concerning'] == 0:
            summary += "No cohorts show severe or concerning addiction risk indicators. "
        
        summary += "See detailed analysis below for specific risk factors and recommendations."
        
        return summary
    
    def _summarize_cohorts(self, cohort_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create summary for each cohort."""
        summaries = []
        
        for cohort in cohort_data:
            # Format cohort identifier
            cohort_id = json.loads(cohort['cohort_identifier'])
            identifier_str = ", ".join([f"{k}={v}" for k, v in cohort_id.items()])
            
            # Identify key indicators
            key_indicators = []
            if cohort['night_time_fraction'] and cohort['night_time_fraction'] > 0.3:
                key_indicators.append(f"Night play: {cohort['night_time_fraction']:.1%}")
            if cohort['excessive_session_fraction'] and cohort['excessive_session_fraction'] > 0.25:
                key_indicators.append(f"Long sessions: {cohort['excessive_session_fraction']:.1%}")
            if cohort['one_more_run_loops'] and cohort['one_more_run_loops'] > 4:
                key_indicators.append(f"Restart loops: {cohort['one_more_run_loops']:.1f}")
            
            summaries.append({
                'identifier': identifier_str,
                'risk_level': cohort['risk_level'],
                'sample_size': cohort['sample_size'],
                'key_indicators': key_indicators[:3]  # Top 3 indicators
            })
        
        # Sort by risk level (severe first)
        risk_order = {'severe': 0, 'concerning': 1, 'moderate': 2, 'healthy': 3}
        summaries.sort(key=lambda x: risk_order[x['risk_level']])
        
        return summaries[:20]  # Top 20 cohorts
    
    def _aggregate_high_risk_features(self, cohort_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate high-risk features across cohorts."""
        feature_map = {}
        
        for cohort in cohort_data:
            if not cohort['high_risk_features']:
                continue
                
            features = json.loads(cohort['high_risk_features'])
            cohort_id = json.loads(cohort['cohort_identifier'])
            
            for feature in features:
                feature_name = feature['feature']
                if feature_name not in feature_map:
                    feature_map[feature_name] = {
                        'name': feature_name,
                        'description': feature.get('description', ''),
                        'correlations': [],
                        'affected_cohorts': []
                    }
                
                feature_map[feature_name]['correlations'].append(feature['correlation'])
                feature_map[feature_name]['affected_cohorts'].append(cohort_id)
        
        # Calculate average correlations and format
        aggregated = []
        for feature_data in feature_map.values():
            avg_correlation = sum(feature_data['correlations']) / len(feature_data['correlations'])
            aggregated.append({
                'name': feature_data['name'],
                'description': feature_data['description'],
                'correlation': avg_correlation,
                'affected_cohorts': feature_data['affected_cohorts']
            })
        
        # Sort by correlation strength
        aggregated.sort(key=lambda x: x['correlation'], reverse=True)
        
        return aggregated[:10]  # Top 10 features
    
    def _consolidate_recommendations(
        self, 
        cohort_data: List[Dict[str, Any]], 
        high_risk_features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Consolidate and prioritize recommendations."""
        recommendation_counts = {}
        
        # Count recommendation occurrences
        for cohort in cohort_data:
            for rec in cohort['recommendations']:
                if rec not in recommendation_counts:
                    recommendation_counts[rec] = 0
                recommendation_counts[rec] += 1
        
        # Categorize and prioritize
        categorized = []
        
        for rec, count in recommendation_counts.items():
            category = self._categorize_recommendation(rec)
            priority = 'high' if count > len(cohort_data) * 0.3 else 'normal'
            
            categorized.append({
                'category': category,
                'text': rec,
                'priority': priority,
                'affected_cohorts': count
            })
        
        # Add feature-specific recommendations
        for feature in high_risk_features[:5]:
            if feature['correlation'] > 0.6:
                categorized.append({
                    'category': 'Feature Review',
                    'text': f"Review {feature['name']}: {feature['description']}",
                    'priority': 'high' if feature['correlation'] > 0.7 else 'normal',
                    'affected_cohorts': len(feature['affected_cohorts'])
                })
        
        # Sort by priority and affected cohorts
        categorized.sort(key=lambda x: (x['priority'] != 'high', -x['affected_cohorts']))
        
        return categorized[:15]  # Top 15 recommendations
    
    def _categorize_recommendation(self, recommendation: str) -> str:
        """Categorize recommendation by type."""
        if 'reminder' in recommendation.lower() or 'notification' in recommendation.lower():
            return 'Player Communication'
        elif 'cooldown' in recommendation.lower() or 'break' in recommendation.lower():
            return 'Session Management'
        elif 'content' in recommendation.lower() or 'event' in recommendation.lower():
            return 'Content Design'
        elif 'feature' in recommendation.lower() or 'system' in recommendation.lower():
            return 'Feature Review'
        else:
            return 'General'
    
    def _compare_periods(
        self, 
        current_data: List[Dict[str, Any]], 
        previous_data: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Compare metrics between periods."""
        if not previous_data:
            return None
        
        # Aggregate metrics by period
        current_metrics = self._aggregate_period_metrics(current_data)
        previous_metrics = self._aggregate_period_metrics(previous_data)
        
        comparison = []
        for metric in ['night_time_fraction', 'excessive_session_fraction', 
                      'avg_session_duration_hours', 'one_more_run_loops']:
            if metric in current_metrics and metric in previous_metrics:
                comparison.append({
                    'metric': metric.replace('_', ' ').title(),
                    'current': current_metrics[metric],
                    'previous': previous_metrics[metric],
                    'change': current_metrics[metric] - previous_metrics[metric]
                })
        
        return comparison
    
    def _aggregate_period_metrics(self, cohort_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate metrics across all cohorts for a period."""
        metrics = {}
        counts = {}
        
        for cohort in cohort_data:
            weight = cohort['sample_size']
            
            for metric in ['night_time_fraction', 'excessive_session_fraction', 
                          'avg_session_duration_hours', 'one_more_run_loops']:
                if cohort[metric] is not None:
                    if metric not in metrics:
                        metrics[metric] = 0
                        counts[metric] = 0
                    
                    metrics[metric] += cohort[metric] * weight
                    counts[metric] += weight
        
        # Calculate weighted averages
        for metric in metrics:
            if counts[metric] > 0:
                metrics[metric] /= counts[metric]
        
        return metrics
    
    async def _generate_trend_chart(self, cohort_data: List[Dict[str, Any]]) -> str:
        """Generate trend visualization chart."""
        if not cohort_data:
            return ""
        
        # Group by date
        dates = sorted(set(c['report_date'] for c in cohort_data))
        
        # Calculate daily risk distribution
        daily_risks = []
        for date in dates:
            day_data = [c for c in cohort_data if c['report_date'] == date]
            risk_counts = {'healthy': 0, 'moderate': 0, 'concerning': 0, 'severe': 0}
            
            for cohort in day_data:
                risk_counts[cohort['risk_level']] += 1
            
            total = sum(risk_counts.values())
            if total > 0:
                daily_risks.append({
                    'date': date,
                    'healthy': risk_counts['healthy'] / total,
                    'moderate': risk_counts['moderate'] / total,
                    'concerning': risk_counts['concerning'] / total,
                    'severe': risk_counts['severe'] / total
                })
        
        # Create stacked area chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        dates_plot = [d['date'] for d in daily_risks]
        healthy = [d['healthy'] for d in daily_risks]
        moderate = [d['moderate'] for d in daily_risks]
        concerning = [d['concerning'] for d in daily_risks]
        severe = [d['severe'] for d in daily_risks]
        
        # Stack the data
        ax.fill_between(dates_plot, 0, healthy, color='#28a745', alpha=0.8, label='Healthy')
        ax.fill_between(dates_plot, healthy, 
                       [h+m for h,m in zip(healthy, moderate)], 
                       color='#ffc107', alpha=0.8, label='Moderate')
        ax.fill_between(dates_plot, 
                       [h+m for h,m in zip(healthy, moderate)], 
                       [h+m+c for h,m,c in zip(healthy, moderate, concerning)], 
                       color='#fd7e14', alpha=0.8, label='Concerning')
        ax.fill_between(dates_plot, 
                       [h+m+c for h,m,c in zip(healthy, moderate, concerning)], 
                       [h+m+c+s for h,m,c,s in zip(healthy, moderate, concerning, severe)], 
                       color='#dc3545', alpha=0.8, label='Severe')
        
        ax.set_ylim(0, 1)
        ax.set_ylabel('Proportion of Cohorts')
        ax.set_xlabel('Date')
        ax.set_title('Addiction Risk Level Distribution Over Time')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return chart_base64
    
    def _get_risk_summary(self, cohort_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get risk level counts."""
        summary = {'healthy': 0, 'moderate': 0, 'concerning': 0, 'severe': 0}
        
        for cohort in cohort_data:
            summary[cohort['risk_level']] += 1
        
        return summary
    
    async def _store_report(
        self, 
        build_id: str, 
        report_date: datetime, 
        html_content: str
    ) -> str:
        """Store generated report in database/storage."""
        # In a real implementation, would store in S3 or similar
        # For now, just log that we would store it
        report_id = f"{build_id}_{report_date.strftime('%Y%m%d')}"
        logger.info(f"Would store report {report_id} ({len(html_content)} bytes)")
        
        # Could also store metadata in a reports table
        # async with self.postgres.acquire() as conn:
        #     await conn.execute(...)
        
        return report_id
