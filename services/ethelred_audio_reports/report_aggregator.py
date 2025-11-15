"""
Audio report aggregator that creates per-archetype and per-language reports.
Implements TAUD-09 (R-AUD-OUT-002).
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
from collections import defaultdict

import asyncpg
import numpy as np

logger = logging.getLogger(__name__)


class AudioReportAggregator:
    """
    Aggregates audio quality scores into build/archetype/language reports.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres = postgres_pool
    
    async def generate_archetype_report(
        self,
        build_id: str,
        archetype_id: str,
        language_code: str,
        period_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate aggregated report for a specific archetype and language.
        """
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(hours=period_hours)
        
        # Fetch all scores for this archetype/language/build
        async with self.postgres.acquire() as conn:
            scores_data = await conn.fetch(
                """
                SELECT 
                    s.segment_id,
                    s.intelligibility_score, s.intelligibility_band,
                    s.naturalness_score, s.naturalness_band,
                    s.archetype_conformity_score, s.archetype_conformity_band,
                    s.simulator_stability_score, s.simulator_stability_band,
                    s.mix_quality_score, s.mix_quality_band,
                    seg.scene_id, seg.emotional_tag
                FROM audio_scores s
                JOIN audio_segments seg ON s.segment_id = seg.segment_id
                WHERE seg.build_id = $1
                    AND seg.archetype_id = $2
                    AND seg.language_code = $3
                    AND seg.created_at BETWEEN $4 AND $5
                ORDER BY seg.created_at
                """,
                build_id, archetype_id, language_code, period_start, period_end
            )
        
        if not scores_data:
            return self._empty_report(build_id, archetype_id, language_code)
        
        # Calculate distributions and statistics
        report = {
            'build_id': build_id,
            'archetype_id': archetype_id,
            'language_code': language_code,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'num_segments': len(scores_data),
            'summary': {}
        }
        
        # Calculate per-metric statistics
        for metric_name in ['intelligibility', 'naturalness', 'archetype_conformity', 
                          'simulator_stability', 'mix_quality']:
            scores = [row[f'{metric_name}_score'] for row in scores_data 
                     if row[f'{metric_name}_score'] is not None]
            bands = [row[f'{metric_name}_band'] for row in scores_data 
                    if row[f'{metric_name}_band'] is not None]
            
            if scores:
                # Calculate distribution
                band_distribution = {}
                for band in set(bands):
                    band_distribution[band] = bands.count(band) / len(bands)
                
                # Calculate statistics
                metric_summary = {
                    'mean': float(np.mean(scores)),
                    'std': float(np.std(scores)),
                    'min': float(np.min(scores)),
                    'max': float(np.max(scores)),
                    'median': float(np.median(scores)),
                    'p25': float(np.percentile(scores, 25)),
                    'p75': float(np.percentile(scores, 75)),
                    'band_distribution': band_distribution
                }
                
                report['summary'][metric_name] = metric_summary
        
        # Identify common deviations
        report['common_deviations'] = await self._identify_common_deviations(scores_data)
        
        # Get previous build comparison if available
        report['comparison_prev_build'] = await self._compare_with_previous_build(
            conn, build_id, archetype_id, language_code
        )
        
        # Scene-specific analysis
        report['scene_analysis'] = self._analyze_by_scene(scores_data)
        
        # Emotional tag analysis
        report['emotion_analysis'] = self._analyze_by_emotion(scores_data)
        
        return report
    
    async def _identify_common_deviations(self, scores_data: List[asyncpg.Record]) -> List[str]:
        """Identify common quality issues across segments."""
        deviations = []
        
        # Check for systematic low scores
        metrics_with_issues = defaultdict(list)
        
        for row in scores_data:
            # Intelligibility issues
            if row['intelligibility_band'] in ['degraded', 'unacceptable']:
                metrics_with_issues['intelligibility'].append({
                    'scene': row['scene_id'],
                    'score': row['intelligibility_score']
                })
            
            # Naturalness issues
            if row['naturalness_band'] in ['robotic', 'monotone']:
                metrics_with_issues['naturalness'].append({
                    'scene': row['scene_id'],
                    'score': row['naturalness_score']
                })
            
            # Archetype conformity issues
            if row['archetype_conformity_band'] in ['too_flat', 'misaligned']:
                metrics_with_issues['archetype'].append({
                    'scene': row['scene_id'],
                    'score': row['archetype_conformity_score']
                })
            
            # Simulator stability issues
            if row['simulator_stability_band'] == 'unstable':
                metrics_with_issues['simulator'].append({
                    'scene': row['scene_id'],
                    'score': row['simulator_stability_score']
                })
        
        # Generate deviation descriptions
        for metric, issues in metrics_with_issues.items():
            if len(issues) >= 5:  # Systematic if 5+ segments affected
                affected_scenes = set(issue['scene'] for issue in issues if issue['scene'])
                avg_score = np.mean([issue['score'] for issue in issues])
                
                if metric == 'intelligibility':
                    deviations.append(
                        f"Systematic intelligibility issues (avg: {avg_score:.2f}) "
                        f"in {len(issues)} segments"
                    )
                elif metric == 'naturalness':
                    deviations.append(
                        f"Robotic/monotone speech detected (avg: {avg_score:.2f}) "
                        f"across {len(affected_scenes)} scenes"
                    )
                elif metric == 'archetype':
                    deviations.append(
                        f"Voice not matching archetype profile (avg: {avg_score:.2f}) "
                        f"in {len(issues)} segments"
                    )
                elif metric == 'simulator':
                    deviations.append(
                        f"Simulator instability detected in {len(issues)} segments"
                    )
        
        return deviations
    
    async def _compare_with_previous_build(
        self,
        conn: asyncpg.Connection,
        current_build_id: str,
        archetype_id: str,
        language_code: str
    ) -> Optional[Dict[str, Any]]:
        """Compare metrics with previous build."""
        # Get the most recent previous report
        prev_report = await conn.fetchrow(
            """
            SELECT 
                build_id,
                report_summary
            FROM audio_archetype_reports
            WHERE archetype_id = $1
                AND language_code = $2
                AND build_id != $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            archetype_id, language_code, current_build_id
        )
        
        if not prev_report or not prev_report['report_summary']:
            return None
        
        try:
            prev_summary = json.loads(prev_report['report_summary'])
            comparison = {
                'build_id': prev_report['build_id'],
                'deltas': {}
            }
            
            # Calculate deltas for each metric
            for metric in ['archetype_conformity', 'simulator_stability']:
                if metric in prev_summary.get('summary', {}):
                    prev_mean = prev_summary['summary'][metric].get('mean', 0)
                    # Current mean will be calculated by caller
                    comparison['deltas'][f'{metric}_delta'] = None  # Placeholder
            
            return comparison
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse previous report JSON for {archetype_id}")
            return None
    
    def _analyze_by_scene(self, scores_data: List[asyncpg.Record]) -> Dict[str, Dict[str, float]]:
        """Analyze metrics by scene."""
        scene_metrics = defaultdict(lambda: defaultdict(list))
        
        for row in scores_data:
            if row['scene_id']:
                scene = row['scene_id']
                for metric in ['intelligibility', 'naturalness', 'archetype_conformity']:
                    score = row[f'{metric}_score']
                    if score is not None:
                        scene_metrics[scene][metric].append(score)
        
        # Calculate averages
        scene_analysis = {}
        for scene, metrics in scene_metrics.items():
            scene_analysis[scene] = {}
            for metric, scores in metrics.items():
                if scores:
                    scene_analysis[scene][f'{metric}_avg'] = float(np.mean(scores))
        
        return scene_analysis
    
    def _analyze_by_emotion(self, scores_data: List[asyncpg.Record]) -> Dict[str, Dict[str, float]]:
        """Analyze metrics by emotional tag."""
        emotion_metrics = defaultdict(lambda: defaultdict(list))
        
        for row in scores_data:
            if row['emotional_tag']:
                emotion = row['emotional_tag']
                for metric in ['naturalness', 'archetype_conformity']:
                    score = row[f'{metric}_score']
                    if score is not None:
                        emotion_metrics[emotion][metric].append(score)
        
        # Calculate statistics
        emotion_analysis = {}
        for emotion, metrics in emotion_metrics.items():
            emotion_analysis[emotion] = {
                'count': len(metrics.get('naturalness', [])),
                'metrics': {}
            }
            for metric, scores in metrics.items():
                if scores:
                    emotion_analysis[emotion]['metrics'][metric] = {
                        'mean': float(np.mean(scores)),
                        'std': float(np.std(scores))
                    }
        
        return emotion_analysis
    
    def _empty_report(self, build_id: str, archetype_id: str, language_code: str) -> Dict[str, Any]:
        """Create empty report when no data available."""
        return {
            'build_id': build_id,
            'archetype_id': archetype_id,
            'language_code': language_code,
            'num_segments': 0,
            'summary': {},
            'common_deviations': [],
            'comparison_prev_build': None,
            'scene_analysis': {},
            'emotion_analysis': {}
        }
    
    async def store_report(self, report: Dict[str, Any]) -> str:
        """Store report in database and return report ID."""
        report_id = str(uuid4())
        
        async with self.postgres.acquire() as conn:
            # Extract comparison data if present
            comparison = report.get('comparison_prev_build')
            
            await conn.execute(
                """
                INSERT INTO audio_archetype_reports (
                    report_id, build_id, archetype_id, language_code,
                    report_summary, common_deviations, comparison_prev_build,
                    created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (build_id, archetype_id, language_code) 
                DO UPDATE SET
                    report_summary = EXCLUDED.report_summary,
                    common_deviations = EXCLUDED.common_deviations,
                    comparison_prev_build = EXCLUDED.comparison_prev_build,
                    created_at = EXCLUDED.created_at
                """,
                report_id,
                report['build_id'],
                report['archetype_id'],
                report['language_code'],
                json.dumps(report),
                report.get('common_deviations', []),
                json.dumps(comparison) if comparison else None,
                datetime.now(timezone.utc)
            )
        
        logger.info(f"Stored audio report {report_id} for {report['archetype_id']}/{report['language_code']}")
        
        return report_id
    
    async def get_build_summary(self, build_id: str) -> Dict[str, Any]:
        """Get summary across all archetypes/languages for a build."""
        async with self.postgres.acquire() as conn:
            reports = await conn.fetch(
                """
                SELECT 
                    archetype_id,
                    language_code,
                    report_summary,
                    common_deviations
                FROM audio_archetype_reports
                WHERE build_id = $1
                """,
                build_id
            )
        
        if not reports:
            return {
                'build_id': build_id,
                'total_archetypes': 0,
                'total_languages': 0,
                'archetype_summaries': {}
            }
        
        # Aggregate across archetypes
        archetype_summaries = {}
        languages = set()
        
        for row in reports:
            archetype = row['archetype_id']
            language = row['language_code']
            languages.add(language)
            
            if archetype not in archetype_summaries:
                archetype_summaries[archetype] = {
                    'languages': [],
                    'overall_health': 'unknown',
                    'key_issues': []
                }
            
            archetype_summaries[archetype]['languages'].append(language)
            
            # Extract key metrics from report
            try:
                summary = json.loads(row['report_summary'])
                
                # Determine health based on mean scores
                health_score = 0
                metric_count = 0
                
                for metric in ['intelligibility', 'naturalness', 'archetype_conformity']:
                    if metric in summary.get('summary', {}):
                        mean_score = summary['summary'][metric].get('mean', 0)
                        health_score += mean_score
                        metric_count += 1
                
                if metric_count > 0:
                    avg_health = health_score / metric_count
                    if avg_health >= 0.8:
                        health = 'good'
                    elif avg_health >= 0.6:
                        health = 'fair'
                    else:
                        health = 'poor'
                    
                    # Update overall health (worst case)
                    current_health = archetype_summaries[archetype]['overall_health']
                    if current_health == 'unknown' or health == 'poor':
                        archetype_summaries[archetype]['overall_health'] = health
                    elif current_health == 'good' and health == 'fair':
                        archetype_summaries[archetype]['overall_health'] = 'fair'
                
                # Add deviations
                if row['common_deviations']:
                    archetype_summaries[archetype]['key_issues'].extend(row['common_deviations'])
                    
            except json.JSONDecodeError:
                logger.error(f"Failed to parse report summary for {archetype}/{language}")
        
        # Remove duplicate issues
        for archetype in archetype_summaries:
            archetype_summaries[archetype]['key_issues'] = list(
                set(archetype_summaries[archetype]['key_issues'])
            )
        
        return {
            'build_id': build_id,
            'total_archetypes': len(archetype_summaries),
            'total_languages': len(languages),
            'languages': sorted(list(languages)),
            'archetype_summaries': archetype_summaries
        }
