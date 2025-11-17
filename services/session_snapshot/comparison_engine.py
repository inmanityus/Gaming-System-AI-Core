"""
Session snapshot comparison for detecting localization drift.
Implements TML-06 (R-ML-STATE-001, R-ML-STATE-002) and TML-09 (R-ML-SNAP-001).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib
import json
import difflib
from collections import defaultdict

logger = logging.getLogger(__name__)


class SnapshotDifferenceType(str, Enum):
    """Types of differences between snapshots."""
    TEXT_CHANGED = "text_changed"
    TEXT_ADDED = "text_added"
    TEXT_REMOVED = "text_removed"
    AUDIO_CHANGED = "audio_changed"
    TIMING_CHANGED = "timing_changed"
    CONTEXT_CHANGED = "context_changed"
    TRANSLATION_QUALITY = "translation_quality"
    LENGTH_VARIANCE = "length_variance"
    PLACEHOLDER_MISMATCH = "placeholder_mismatch"
    TONE_SHIFT = "tone_shift"


class DriftSeverity(str, Enum):
    """Severity levels for localization drift."""
    CRITICAL = "critical"  # Breaking changes
    HIGH = "high"         # Significant changes needing review
    MEDIUM = "medium"     # Notable changes
    LOW = "low"          # Minor changes
    INFO = "info"        # Informational only


@dataclass
class LocalizationSnapshot:
    """A snapshot of localization state at a point in time."""
    snapshot_id: str
    build_id: str
    language_code: str
    timestamp: datetime
    
    # Text content
    strings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # key -> {text, category, version, hash, metadata}
    
    # Audio metadata
    audio_assets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # key -> {duration, size, hash, sample_rate}
    
    # Timing data
    timing_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # key -> {subtitle_count, word_count, sync_quality}
    
    # Coverage metrics
    coverage: Dict[str, float] = field(default_factory=dict)
    
    # Quality metrics
    quality_scores: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    total_strings: int = 0
    total_audio_files: int = 0
    total_size_mb: float = 0.0
    
    def calculate_hash(self) -> str:
        """Calculate hash of snapshot content."""
        content = {
            'strings': sorted(
                [(k, v['text'], v['version']) for k, v in self.strings.items()]
            ),
            'audio': sorted(
                [(k, v['hash']) for k, v in self.audio_assets.items()]
            )
        }
        
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()


@dataclass
class DriftAnalysis:
    """Analysis of drift between two snapshots."""
    from_snapshot_id: str
    to_snapshot_id: str
    language_code: str
    
    # Time span
    time_delta_hours: float
    
    # Differences found
    differences: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary metrics
    total_changes: int = 0
    strings_added: int = 0
    strings_removed: int = 0
    strings_modified: int = 0
    
    # Quality impact
    quality_impact: float = 0.0  # -1 to 1, negative is worse
    coverage_impact: float = 0.0
    
    # Risk assessment
    risk_level: DriftSeverity = DriftSeverity.LOW
    requires_review: bool = False
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)


class SessionSnapshotComparison:
    """
    Compares localization snapshots to detect drift and quality changes.
    Tracks changes over time and identifies potential issues.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.severity_thresholds = self._load_severity_thresholds()
        self.quality_weights = self._load_quality_weights()
    
    def _load_severity_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load thresholds for determining severity."""
        return {
            'text_length_change': {
                'critical': 2.0,   # 200% change
                'high': 1.5,      # 150% change
                'medium': 1.3,    # 130% change
                'low': 1.1       # 110% change
            },
            'quality_drop': {
                'critical': 0.3,  # 30% drop
                'high': 0.2,     # 20% drop
                'medium': 0.1,   # 10% drop
                'low': 0.05     # 5% drop
            },
            'coverage_drop': {
                'critical': 0.2,  # 20% drop
                'high': 0.1,     # 10% drop
                'medium': 0.05,  # 5% drop
                'low': 0.02     # 2% drop
            }
        }
    
    def _load_quality_weights(self) -> Dict[str, float]:
        """Load weights for quality calculations."""
        return {
            'text_quality': 0.4,
            'audio_quality': 0.3,
            'timing_quality': 0.2,
            'consistency': 0.1
        }
    
    async def capture_snapshot(
        self,
        build_id: str,
        language_code: str,
        localization_service,
        audio_service=None,
        timing_service=None
    ) -> LocalizationSnapshot:
        """
        Capture a complete snapshot of localization state.
        
        Args:
            build_id: Build identifier
            language_code: Language to snapshot
            localization_service: Service for text data
            audio_service: Optional service for audio data
            timing_service: Optional service for timing data
            
        Returns:
            Complete localization snapshot
        """
        snapshot = LocalizationSnapshot(
            snapshot_id=self._generate_snapshot_id(),
            build_id=build_id,
            language_code=language_code,
            timestamp=datetime.utcnow()
        )
        
        # Capture text strings
        categories = ['ui', 'narrative', 'system', 'tutorial']
        for category in categories:
            strings = await localization_service.repository.get_strings_by_category(
                category, language_code, include_unapproved=False
            )
            
            for string_data in strings:
                key = string_data['key']
                snapshot.strings[key] = {
                    'text': string_data['text'],
                    'category': string_data['category'],
                    'version': string_data['version'],
                    'hash': self._hash_text(string_data['text']),
                    'metadata': {
                        'plural_forms': string_data.get('plural_forms', {}),
                        'gender_forms': string_data.get('gender_forms', {}),
                        'tags': string_data.get('tags', [])
                    }
                }
        
        snapshot.total_strings = len(snapshot.strings)
        
        # Capture audio metadata if available
        if audio_service:
            audio_metadata = await audio_service.get_audio_metadata(
                language_code, list(snapshot.strings.keys())
            )
            
            for key, metadata in audio_metadata.items():
                snapshot.audio_assets[key] = {
                    'duration': metadata.get('duration', 0),
                    'size': metadata.get('size', 0),
                    'hash': metadata.get('hash', ''),
                    'sample_rate': metadata.get('sample_rate', 48000)
                }
                snapshot.total_size_mb += metadata.get('size', 0) / (1024 * 1024)
            
            snapshot.total_audio_files = len(snapshot.audio_assets)
        
        # Capture timing data if available
        if timing_service:
            timing_metadata = await timing_service.get_timing_metadata(
                language_code, list(snapshot.audio_assets.keys())
            )
            
            for key, metadata in timing_metadata.items():
                snapshot.timing_data[key] = {
                    'subtitle_count': metadata.get('subtitle_count', 0),
                    'word_count': metadata.get('word_count', 0),
                    'sync_quality': metadata.get('sync_quality', 0.0)
                }
        
        # Calculate coverage
        snapshot.coverage = await self._calculate_coverage(snapshot)
        
        # Calculate quality scores
        snapshot.quality_scores = await self._calculate_quality_scores(snapshot)
        
        return snapshot
    
    def compare_snapshots(
        self,
        snapshot1: LocalizationSnapshot,
        snapshot2: LocalizationSnapshot
    ) -> DriftAnalysis:
        """
        Compare two snapshots and analyze drift.
        
        Args:
            snapshot1: Earlier snapshot
            snapshot2: Later snapshot
            
        Returns:
            Drift analysis with differences and recommendations
        """
        analysis = DriftAnalysis(
            from_snapshot_id=snapshot1.snapshot_id,
            to_snapshot_id=snapshot2.snapshot_id,
            language_code=snapshot1.language_code,
            time_delta_hours=(
                (snapshot2.timestamp - snapshot1.timestamp).total_seconds() / 3600
            )
        )
        
        # Compare text strings
        self._compare_strings(snapshot1, snapshot2, analysis)
        
        # Compare audio assets
        self._compare_audio(snapshot1, snapshot2, analysis)
        
        # Compare timing data
        self._compare_timing(snapshot1, snapshot2, analysis)
        
        # Compare quality and coverage
        self._compare_quality_metrics(snapshot1, snapshot2, analysis)
        
        # Assess overall risk
        self._assess_risk(analysis)
        
        # Generate recommendations
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _compare_strings(
        self,
        snapshot1: LocalizationSnapshot,
        snapshot2: LocalizationSnapshot,
        analysis: DriftAnalysis
    ):
        """Compare text strings between snapshots."""
        keys1 = set(snapshot1.strings.keys())
        keys2 = set(snapshot2.strings.keys())
        
        # Added strings
        added_keys = keys2 - keys1
        analysis.strings_added = len(added_keys)
        
        for key in added_keys:
            analysis.differences.append({
                'type': SnapshotDifferenceType.TEXT_ADDED.value,
                'key': key,
                'text': snapshot2.strings[key]['text'],
                'category': snapshot2.strings[key]['category'],
                'severity': DriftSeverity.INFO.value
            })
        
        # Removed strings
        removed_keys = keys1 - keys2
        analysis.strings_removed = len(removed_keys)
        
        for key in removed_keys:
            analysis.differences.append({
                'type': SnapshotDifferenceType.TEXT_REMOVED.value,
                'key': key,
                'text': snapshot1.strings[key]['text'],
                'category': snapshot1.strings[key]['category'],
                'severity': DriftSeverity.HIGH.value  # Removal is more serious
            })
        
        # Modified strings
        common_keys = keys1 & keys2
        
        for key in common_keys:
            data1 = snapshot1.strings[key]
            data2 = snapshot2.strings[key]
            
            if data1['hash'] != data2['hash']:
                analysis.strings_modified += 1
                
                # Analyze the change
                change_analysis = self._analyze_text_change(
                    data1['text'], data2['text'], key
                )
                
                analysis.differences.append({
                    'type': SnapshotDifferenceType.TEXT_CHANGED.value,
                    'key': key,
                    'old_text': data1['text'],
                    'new_text': data2['text'],
                    'category': data1['category'],
                    'severity': change_analysis['severity'],
                    'details': change_analysis
                })
                
                # Check for specific issues
                if change_analysis.get('placeholder_mismatch'):
                    analysis.differences.append({
                        'type': SnapshotDifferenceType.PLACEHOLDER_MISMATCH.value,
                        'key': key,
                        'severity': DriftSeverity.CRITICAL.value,
                        'details': change_analysis['placeholder_details']
                    })
        
        analysis.total_changes = (
            analysis.strings_added + 
            analysis.strings_removed + 
            analysis.strings_modified
        )
    
    def _analyze_text_change(
        self,
        old_text: str,
        new_text: str,
        key: str
    ) -> Dict[str, Any]:
        """Analyze a text change in detail."""
        result = {
            'severity': DriftSeverity.LOW.value,
            'length_ratio': len(new_text) / len(old_text) if old_text else float('inf'),
            'similarity': self._calculate_similarity(old_text, new_text),
            'placeholder_mismatch': False
        }
        
        # Check length change
        thresholds = self.severity_thresholds['text_length_change']
        if result['length_ratio'] >= thresholds['critical'] or \
           result['length_ratio'] <= 1/thresholds['critical']:
            result['severity'] = DriftSeverity.CRITICAL.value
        elif result['length_ratio'] >= thresholds['high'] or \
             result['length_ratio'] <= 1/thresholds['high']:
            result['severity'] = DriftSeverity.HIGH.value
        elif result['length_ratio'] >= thresholds['medium'] or \
             result['length_ratio'] <= 1/thresholds['medium']:
            result['severity'] = DriftSeverity.MEDIUM.value
        
        # Check placeholders
        old_placeholders = self._extract_placeholders(old_text)
        new_placeholders = self._extract_placeholders(new_text)
        
        if old_placeholders != new_placeholders:
            result['placeholder_mismatch'] = True
            result['placeholder_details'] = {
                'old': list(old_placeholders),
                'new': list(new_placeholders),
                'added': list(new_placeholders - old_placeholders),
                'removed': list(old_placeholders - new_placeholders)
            }
            result['severity'] = DriftSeverity.CRITICAL.value
        
        # Check for tone shift (simplified)
        if self._detect_tone_shift(old_text, new_text):
            result['tone_shift'] = True
            if result['severity'] == DriftSeverity.LOW.value:
                result['severity'] = DriftSeverity.MEDIUM.value
        
        return result
    
    def _compare_audio(
        self,
        snapshot1: LocalizationSnapshot,
        snapshot2: LocalizationSnapshot,
        analysis: DriftAnalysis
    ):
        """Compare audio assets between snapshots."""
        keys1 = set(snapshot1.audio_assets.keys())
        keys2 = set(snapshot2.audio_assets.keys())
        
        # Check for audio changes
        common_keys = keys1 & keys2
        
        for key in common_keys:
            audio1 = snapshot1.audio_assets[key]
            audio2 = snapshot2.audio_assets[key]
            
            if audio1['hash'] != audio2['hash']:
                # Audio file changed
                duration_change = abs(audio2['duration'] - audio1['duration'])
                
                severity = DriftSeverity.LOW.value
                if duration_change > 2.0:  # More than 2 seconds difference
                    severity = DriftSeverity.HIGH.value
                elif duration_change > 0.5:  # More than 0.5 seconds
                    severity = DriftSeverity.MEDIUM.value
                
                analysis.differences.append({
                    'type': SnapshotDifferenceType.AUDIO_CHANGED.value,
                    'key': key,
                    'old_duration': audio1['duration'],
                    'new_duration': audio2['duration'],
                    'duration_change': duration_change,
                    'size_change_mb': (audio2['size'] - audio1['size']) / (1024 * 1024),
                    'severity': severity
                })
    
    def _compare_timing(
        self,
        snapshot1: LocalizationSnapshot,
        snapshot2: LocalizationSnapshot,
        analysis: DriftAnalysis
    ):
        """Compare timing data between snapshots."""
        keys1 = set(snapshot1.timing_data.keys())
        keys2 = set(snapshot2.timing_data.keys())
        
        common_keys = keys1 & keys2
        
        for key in common_keys:
            timing1 = snapshot1.timing_data[key]
            timing2 = snapshot2.timing_data[key]
            
            sync_quality_drop = timing1['sync_quality'] - timing2['sync_quality']
            
            if sync_quality_drop > 0.1:  # 10% drop in sync quality
                analysis.differences.append({
                    'type': SnapshotDifferenceType.TIMING_CHANGED.value,
                    'key': key,
                    'old_sync_quality': timing1['sync_quality'],
                    'new_sync_quality': timing2['sync_quality'],
                    'quality_drop': sync_quality_drop,
                    'severity': DriftSeverity.MEDIUM.value if sync_quality_drop < 0.2 
                              else DriftSeverity.HIGH.value
                })
    
    def _compare_quality_metrics(
        self,
        snapshot1: LocalizationSnapshot,
        snapshot2: LocalizationSnapshot,
        analysis: DriftAnalysis
    ):
        """Compare overall quality metrics."""
        # Coverage comparison
        for metric, value1 in snapshot1.coverage.items():
            value2 = snapshot2.coverage.get(metric, 0)
            drop = value1 - value2
            
            if drop > 0:
                analysis.coverage_impact -= drop
                
                thresholds = self.severity_thresholds['coverage_drop']
                if drop >= thresholds['critical']:
                    severity = DriftSeverity.CRITICAL.value
                elif drop >= thresholds['high']:
                    severity = DriftSeverity.HIGH.value
                elif drop >= thresholds['medium']:
                    severity = DriftSeverity.MEDIUM.value
                else:
                    severity = DriftSeverity.LOW.value
                
                if severity != DriftSeverity.LOW.value:
                    analysis.differences.append({
                        'type': SnapshotDifferenceType.CONTEXT_CHANGED.value,
                        'metric': f'coverage_{metric}',
                        'old_value': value1,
                        'new_value': value2,
                        'drop': drop,
                        'severity': severity
                    })
        
        # Quality score comparison
        for metric, value1 in snapshot1.quality_scores.items():
            value2 = snapshot2.quality_scores.get(metric, 0)
            drop = value1 - value2
            
            if drop > 0:
                analysis.quality_impact -= drop * self.quality_weights.get(metric, 0.1)
                
                if drop >= 0.1:  # 10% quality drop
                    analysis.differences.append({
                        'type': SnapshotDifferenceType.TRANSLATION_QUALITY.value,
                        'metric': f'quality_{metric}',
                        'old_value': value1,
                        'new_value': value2,
                        'drop': drop,
                        'severity': DriftSeverity.HIGH.value if drop >= 0.2
                                   else DriftSeverity.MEDIUM.value
                    })
    
    def _assess_risk(self, analysis: DriftAnalysis):
        """Assess overall risk level of the drift."""
        # Count severities
        severity_counts = defaultdict(int)
        for diff in analysis.differences:
            severity_counts[diff.get('severity', DriftSeverity.LOW.value)] += 1
        
        # Determine overall risk
        if severity_counts[DriftSeverity.CRITICAL.value] > 0:
            analysis.risk_level = DriftSeverity.CRITICAL
            analysis.requires_review = True
        elif severity_counts[DriftSeverity.HIGH.value] >= 5:
            analysis.risk_level = DriftSeverity.HIGH
            analysis.requires_review = True
        elif severity_counts[DriftSeverity.MEDIUM.value] >= 10:
            analysis.risk_level = DriftSeverity.MEDIUM
            analysis.requires_review = True
        elif analysis.quality_impact < -0.1 or analysis.coverage_impact < -0.05:
            analysis.risk_level = DriftSeverity.HIGH
            analysis.requires_review = True
        else:
            analysis.risk_level = DriftSeverity.LOW
    
    def _generate_recommendations(self, analysis: DriftAnalysis):
        """Generate actionable recommendations based on analysis."""
        if analysis.risk_level == DriftSeverity.CRITICAL:
            analysis.recommendations.append(
                "URGENT: Critical changes detected. Immediate review required."
            )
        
        # String recommendations
        if analysis.strings_removed > 10:
            analysis.recommendations.append(
                f"Review {analysis.strings_removed} removed strings to ensure "
                "no critical content was accidentally deleted."
            )
        
        if analysis.strings_modified > 50:
            analysis.recommendations.append(
                f"Large number of string modifications ({analysis.strings_modified}). "
                "Consider incremental rollout or additional QA testing."
            )
        
        # Placeholder issues
        placeholder_issues = [
            d for d in analysis.differences
            if d['type'] == SnapshotDifferenceType.PLACEHOLDER_MISMATCH.value
        ]
        if placeholder_issues:
            analysis.recommendations.append(
                f"Fix {len(placeholder_issues)} placeholder mismatches before release. "
                "These will cause runtime errors."
            )
        
        # Quality recommendations
        if analysis.quality_impact < -0.1:
            analysis.recommendations.append(
                "Significant quality degradation detected. Review recent changes "
                "and consider reverting problematic modifications."
            )
        
        if analysis.coverage_impact < -0.05:
            analysis.recommendations.append(
                "Localization coverage has decreased. Ensure all new content "
                "is properly translated before release."
            )
        
        # Time-based recommendations
        if analysis.time_delta_hours < 24 and analysis.total_changes > 100:
            analysis.recommendations.append(
                "High change velocity detected. Consider slowing down and "
                "reviewing changes more thoroughly."
            )
    
    def _hash_text(self, text: str) -> str:
        """Generate hash of text content."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def _extract_placeholders(self, text: str) -> Set[str]:
        """Extract placeholder patterns from text."""
        import re
        patterns = [
            r'\{(\w+)\}',        # {variable}
            r'%(\w+)%',          # %variable%
            r'\$\{(\w+)\}',      # ${variable}
            r'{{(\w+)}}',        # {{variable}}
            r'%[sdif]',          # Printf style
            r'%\d+\$[sdif]'      # Positional printf
        ]
        
        placeholders = set()
        for pattern in patterns:
            placeholders.update(re.findall(pattern, text))
        
        return placeholders
    
    def _detect_tone_shift(self, old_text: str, new_text: str) -> bool:
        """Simple tone shift detection."""
        # This would be more sophisticated in production
        formal_markers = ['please', 'kindly', 'would you', 'could you']
        casual_markers = ['hey', 'yeah', 'gonna', 'wanna', 'ok', 'okay']
        
        old_formal = sum(1 for marker in formal_markers if marker in old_text.lower())
        new_formal = sum(1 for marker in formal_markers if marker in new_text.lower())
        old_casual = sum(1 for marker in casual_markers if marker in old_text.lower())
        new_casual = sum(1 for marker in casual_markers if marker in new_text.lower())
        
        # Detect shift from formal to casual or vice versa
        if old_formal > old_casual and new_casual > new_formal:
            return True
        if old_casual > old_formal and new_formal > new_casual:
            return True
        
        return False
    
    async def _calculate_coverage(
        self,
        snapshot: LocalizationSnapshot
    ) -> Dict[str, float]:
        """Calculate coverage metrics for snapshot."""
        coverage = {}
        
        # Text coverage by category
        categories = defaultdict(int)
        for string_data in snapshot.strings.values():
            categories[string_data['category']] += 1
        
        total = len(snapshot.strings)
        for category, count in categories.items():
            coverage[f'text_{category}'] = count / total if total > 0 else 0
        
        # Audio coverage
        if snapshot.total_strings > 0:
            coverage['audio'] = len(snapshot.audio_assets) / snapshot.total_strings
        
        # Timing coverage
        if len(snapshot.audio_assets) > 0:
            coverage['timing'] = len(snapshot.timing_data) / len(snapshot.audio_assets)
        
        return coverage
    
    async def _calculate_quality_scores(
        self,
        snapshot: LocalizationSnapshot
    ) -> Dict[str, float]:
        """Calculate quality scores for snapshot."""
        scores = {}
        
        # Text quality (simplified - would be more sophisticated)
        text_lengths = [len(s['text']) for s in snapshot.strings.values()]
        if text_lengths:
            avg_length = sum(text_lengths) / len(text_lengths)
            # Penalize very short or very long strings
            if 10 <= avg_length <= 100:
                scores['text_quality'] = 0.9
            elif 5 <= avg_length <= 200:
                scores['text_quality'] = 0.7
            else:
                scores['text_quality'] = 0.5
        
        # Audio quality (based on coverage and consistency)
        if snapshot.total_strings > 0:
            audio_coverage = len(snapshot.audio_assets) / snapshot.total_strings
            scores['audio_quality'] = audio_coverage
        
        # Timing quality (based on sync scores)
        if snapshot.timing_data:
            sync_scores = [t['sync_quality'] for t in snapshot.timing_data.values()]
            scores['timing_quality'] = sum(sync_scores) / len(sync_scores)
        
        return scores
    
    def _generate_snapshot_id(self) -> str:
        """Generate unique snapshot ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def generate_drift_report(
        self,
        analyses: List[DriftAnalysis],
        output_format: str = 'json'
    ) -> str:
        """Generate drift report from multiple analyses."""
        if output_format == 'json':
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'analyses_count': len(analyses),
                'languages': list(set(a.language_code for a in analyses)),
                'total_differences': sum(a.total_changes for a in analyses),
                'critical_issues': sum(
                    1 for a in analyses
                    if a.risk_level == DriftSeverity.CRITICAL.value
                ),
                'requires_review': any(a.requires_review for a in analyses),
                'analyses': [
                    {
                        'from_snapshot': a.from_snapshot_id,
                        'to_snapshot': a.to_snapshot_id,
                        'language': a.language_code,
                        'risk_level': a.risk_level.value,
                        'total_changes': a.total_changes,
                        'requires_review': a.requires_review,
                        'recommendations': a.recommendations,
                        'critical_differences': [
                            d for d in a.differences
                            if d.get('severity') == DriftSeverity.CRITICAL.value
                        ]
                    }
                    for a in analyses
                ]
            }
            
            return json.dumps(report, indent=2)
        
        else:
            raise ValueError(f"Unsupported format: {output_format}")
