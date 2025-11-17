"""
Multi-language launch readiness certification system.
Implements TML-12 (R-ML-LAUNCH-001, R-ML-LAUNCH-002).
"""
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import asyncio
import json

# Import required components
from services.localization.repository import LocalizationRepository
from services.language_system.language_gateway import LanguageGateway
from services.ethelred_integration.localized_qa import LocalizedQAOrchestrator
from services.localization_metrics.metrics_tracker import LocalizationMetricsTracker

logger = logging.getLogger(__name__)


class ReadinessCheckType(str, Enum):
    """Types of readiness checks."""
    CONTENT_COMPLETENESS = "content_completeness"
    TRANSLATION_QUALITY = "translation_quality"
    AUDIO_COVERAGE = "audio_coverage"
    TECHNICAL_VALIDATION = "technical_validation"
    PERFORMANCE_METRICS = "performance_metrics"
    USER_ACCEPTANCE = "user_acceptance"
    LEGAL_COMPLIANCE = "legal_compliance"
    CULTURAL_REVIEW = "cultural_review"


class ReadinessStatus(str, Enum):
    """Readiness status levels."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    CERTIFIED = "certified"


class LaunchIssue(str, Enum):
    """Types of launch-blocking issues."""
    MISSING_CONTENT = "missing_content"
    POOR_QUALITY = "poor_quality"
    TECHNICAL_ERROR = "technical_error"
    PERFORMANCE_ISSUE = "performance_issue"
    COMPLIANCE_ISSUE = "compliance_issue"
    CULTURAL_CONCERN = "cultural_concern"


@dataclass
class ReadinessCheck:
    """Individual readiness check result."""
    check_type: ReadinessCheckType
    status: ReadinessStatus
    score: float = 0.0  # 0-100
    passed: bool = False
    
    # Details
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    checked_at: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    checked_by: str = "system"


@dataclass
class LanguageReadinessReport:
    """Complete readiness report for a language."""
    language_code: str
    overall_status: ReadinessStatus
    overall_score: float  # 0-100
    is_certified: bool = False
    
    # Individual checks
    checks: Dict[ReadinessCheckType, ReadinessCheck] = field(default_factory=dict)
    
    # Summary
    launch_blocking_issues: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Certification
    certified_at: Optional[datetime] = None
    certified_by: Optional[str] = None
    certification_expires: Optional[datetime] = None
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    report_version: str = "1.0"


class MultiLanguageLaunchCertifier:
    """
    Certifies languages as ready for launch.
    Comprehensive validation across all aspects.
    """
    
    def __init__(
        self,
        localization_repo: LocalizationRepository,
        language_gateway: LanguageGateway,
        qa_orchestrator: LocalizedQAOrchestrator,
        metrics_tracker: LocalizationMetricsTracker,
        config: Dict[str, Any]
    ):
        self.localization = localization_repo
        self.language_gateway = language_gateway
        self.qa_orchestrator = qa_orchestrator
        self.metrics = metrics_tracker
        self.config = config
        
        # Readiness thresholds
        self.thresholds = {
            'content_completeness': config.get('completeness_threshold', 0.98),
            'translation_quality': config.get('quality_threshold', 0.90),
            'audio_coverage': config.get('audio_threshold', 0.95),
            'technical_validation': config.get('technical_threshold', 0.99),
            'performance_metrics': config.get('performance_threshold', 0.95),
            'user_acceptance': config.get('acceptance_threshold', 0.80),
            'legal_compliance': config.get('compliance_threshold', 1.0),
            'cultural_review': config.get('cultural_threshold', 0.95)
        }
        
        # Required content categories
        self.required_categories = [
            'ui_core',
            'tutorial',
            'narrative_main',
            'system_messages',
            'error_messages',
            'achievements',
            'settings',
            'legal_notices'
        ]
    
    async def certify_language(
        self,
        language_code: str,
        force_refresh: bool = False
    ) -> LanguageReadinessReport:
        """
        Perform full certification check for a language.
        
        Args:
            language_code: Language to certify
            force_refresh: Force fresh checks even if recent exists
            
        Returns:
            Complete readiness report
        """
        start_time = asyncio.get_event_loop().time()
        
        # Check if recent certification exists
        if not force_refresh:
            recent = await self._get_recent_certification(language_code)
            if recent:
                return recent
        
        report = LanguageReadinessReport(
            language_code=language_code,
            overall_status=ReadinessStatus.IN_PROGRESS,
            overall_score=0.0
        )
        
        try:
            # Run all checks in parallel where possible
            check_tasks = {
                ReadinessCheckType.CONTENT_COMPLETENESS: self._check_content_completeness(
                    language_code
                ),
                ReadinessCheckType.TRANSLATION_QUALITY: self._check_translation_quality(
                    language_code
                ),
                ReadinessCheckType.AUDIO_COVERAGE: self._check_audio_coverage(
                    language_code
                ),
                ReadinessCheckType.TECHNICAL_VALIDATION: self._check_technical_validation(
                    language_code
                ),
                ReadinessCheckType.PERFORMANCE_METRICS: self._check_performance_metrics(
                    language_code
                )
            }
            
            # Run parallel checks
            check_results = await asyncio.gather(
                *check_tasks.values(),
                return_exceptions=True
            )
            
            # Process results
            for check_type, result in zip(check_tasks.keys(), check_results):
                if isinstance(result, Exception):
                    logger.error(f"Check {check_type} failed: {result}")
                    report.checks[check_type] = ReadinessCheck(
                        check_type=check_type,
                        status=ReadinessStatus.FAILED,
                        score=0.0,
                        passed=False,
                        issues=[{
                            'type': 'check_error',
                            'message': str(result)
                        }]
                    )
                else:
                    report.checks[check_type] = result
            
            # Run sequential checks that depend on previous results
            report.checks[ReadinessCheckType.USER_ACCEPTANCE] = await self._check_user_acceptance(
                language_code, report.checks
            )
            
            report.checks[ReadinessCheckType.LEGAL_COMPLIANCE] = await self._check_legal_compliance(
                language_code
            )
            
            report.checks[ReadinessCheckType.CULTURAL_REVIEW] = await self._check_cultural_review(
                language_code, report.checks
            )
            
            # Calculate overall results
            self._calculate_overall_status(report)
            
            # Check for launch blocking issues
            self._identify_launch_blockers(report)
            
            # Determine certification
            if self._can_certify(report):
                report.is_certified = True
                report.certified_at = datetime.utcnow()
                report.certified_by = "automated_system"
                report.certification_expires = datetime.utcnow() + timedelta(days=30)
                report.overall_status = ReadinessStatus.CERTIFIED
            
            # Save report
            await self._save_certification_report(report)
            
        except Exception as e:
            logger.error(f"Certification error for {language_code}: {e}")
            report.overall_status = ReadinessStatus.FAILED
            report.launch_blocking_issues.append({
                'issue': LaunchIssue.TECHNICAL_ERROR.value,
                'message': f'Certification process failed: {str(e)}'
            })
        
        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        logger.info(
            f"Language certification for {language_code} completed in {duration_ms:.1f}ms. "
            f"Status: {report.overall_status}"
        )
        
        return report
    
    async def _check_content_completeness(
        self,
        language_code: str
    ) -> ReadinessCheck:
        """Check if all required content is translated."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.CONTENT_COMPLETENESS,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            # Get content statistics
            stats = await self.localization.get_language_statistics(language_code)
            
            total_keys = stats['total_keys']
            translated_keys = stats['translated_keys']
            missing_keys = stats['missing_keys']
            
            # Check each required category
            category_coverage = {}
            for category in self.required_categories:
                cat_stats = await self.localization.get_category_statistics(
                    language_code, category
                )
                
                coverage = (
                    cat_stats['translated'] / cat_stats['total']
                    if cat_stats['total'] > 0 else 0
                )
                category_coverage[category] = coverage
                
                if coverage < 1.0:
                    check.issues.append({
                        'category': category,
                        'coverage': coverage,
                        'missing': cat_stats['total'] - cat_stats['translated']
                    })
            
            # Calculate overall score
            overall_coverage = translated_keys / total_keys if total_keys > 0 else 0
            check.score = overall_coverage * 100
            
            # Check against threshold
            check.passed = overall_coverage >= self.thresholds['content_completeness']
            check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
            
            check.details = {
                'total_keys': total_keys,
                'translated_keys': translated_keys,
                'missing_keys': missing_keys,
                'coverage': overall_coverage,
                'category_coverage': category_coverage
            }
            
            if not check.passed:
                check.recommendations.append(
                    f"Complete translation of {len(missing_keys)} missing keys"
                )
                
                # Prioritize missing categories
                critical_missing = [
                    cat for cat, cov in category_coverage.items()
                    if cov < 0.9 and cat in ['ui_core', 'tutorial', 'system_messages']
                ]
                
                if critical_missing:
                    check.recommendations.append(
                        f"Priority: Complete critical categories: {', '.join(critical_missing)}"
                    )
            
        except Exception as e:
            logger.error(f"Content completeness check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    async def _check_translation_quality(
        self,
        language_code: str
    ) -> ReadinessCheck:
        """Check translation quality across all content."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.TRANSLATION_QUALITY,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            # Sample content for quality check
            sample_size = self.config.get('quality_sample_size', 100)
            sample_content = await self.localization.get_content_sample(
                language_code, sample_size
            )
            
            # Run QA validation on sample
            validations = await self.qa_orchestrator.validate_batch(
                sample_content, parallel=True
            )
            
            # Analyze results
            total_validated = len(validations)
            passed_validation = sum(1 for v in validations if v.passed)
            
            critical_issues = []
            high_issues = []
            
            for validation in validations:
                for issue in validation.issues:
                    if issue['severity'] == 'critical':
                        critical_issues.append({
                            'content_id': validation.content_id,
                            'issue': issue
                        })
                    elif issue['severity'] == 'high':
                        high_issues.append({
                            'content_id': validation.content_id,
                            'issue': issue
                        })
            
            # Calculate quality score
            quality_score = passed_validation / total_validated if total_validated > 0 else 0
            
            # Apply penalties for critical issues
            critical_penalty = len(critical_issues) * 0.05
            quality_score = max(0, quality_score - critical_penalty)
            
            check.score = quality_score * 100
            check.passed = quality_score >= self.thresholds['translation_quality']
            check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
            
            check.details = {
                'sample_size': total_validated,
                'passed_validation': passed_validation,
                'critical_issues': len(critical_issues),
                'high_issues': len(high_issues),
                'quality_score': quality_score
            }
            
            if critical_issues:
                check.issues.extend(critical_issues[:5])  # Top 5 critical
                check.recommendations.append(
                    f"Fix {len(critical_issues)} critical quality issues"
                )
            
            if not check.passed:
                check.recommendations.append(
                    "Review and improve translations with low quality scores"
                )
            
        except Exception as e:
            logger.error(f"Translation quality check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    async def _check_audio_coverage(
        self,
        language_code: str
    ) -> ReadinessCheck:
        """Check audio/TTS coverage for dialogues."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.AUDIO_COVERAGE,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            # Get dialogue content
            dialogue_keys = await self.localization.get_keys_by_category(
                language_code, 'narrative_dialogue'
            )
            
            total_dialogues = len(dialogue_keys)
            audio_available = 0
            tts_available = 0
            missing_audio = []
            
            # Check each dialogue
            for key in dialogue_keys:
                content = await self.localization.get_content(
                    key, language_code
                )
                
                if content.get('audio_file'):
                    audio_available += 1
                elif content.get('tts_enabled', False):
                    tts_available += 1
                else:
                    missing_audio.append({
                        'key': key,
                        'text': content.get('text', '')[:100]
                    })
            
            # Calculate coverage
            coverage = (
                (audio_available + tts_available) / total_dialogues
                if total_dialogues > 0 else 0
            )
            
            check.score = coverage * 100
            check.passed = coverage >= self.thresholds['audio_coverage']
            check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
            
            check.details = {
                'total_dialogues': total_dialogues,
                'recorded_audio': audio_available,
                'tts_enabled': tts_available,
                'missing': len(missing_audio),
                'coverage': coverage
            }
            
            if missing_audio:
                check.issues.append({
                    'type': 'missing_audio',
                    'count': len(missing_audio),
                    'samples': missing_audio[:5]
                })
                
                check.recommendations.append(
                    f"Add audio or enable TTS for {len(missing_audio)} dialogues"
                )
            
            # Check TTS quality if significant portion uses TTS
            if tts_available > total_dialogues * 0.2:
                tts_quality = await self._check_tts_quality(language_code)
                check.details['tts_quality'] = tts_quality
                
                if tts_quality < 0.8:
                    check.recommendations.append(
                        "Consider recording more human voice to improve quality"
                    )
            
        except Exception as e:
            logger.error(f"Audio coverage check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    async def _check_technical_validation(
        self,
        language_code: str
    ) -> ReadinessCheck:
        """Check technical aspects like encoding, formats, etc."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.TECHNICAL_VALIDATION,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            issues = []
            
            # Check encoding consistency
            encoding_issues = await self._validate_encoding(language_code)
            if encoding_issues:
                issues.extend(encoding_issues)
            
            # Check placeholder consistency
            placeholder_issues = await self._validate_placeholders(language_code)
            if placeholder_issues:
                issues.extend(placeholder_issues)
            
            # Check format strings
            format_issues = await self._validate_format_strings(language_code)
            if format_issues:
                issues.extend(format_issues)
            
            # Check UI layout compatibility
            layout_issues = await self._validate_ui_layout(language_code)
            if layout_issues:
                issues.extend(layout_issues)
            
            # Check file formats
            file_issues = await self._validate_file_formats(language_code)
            if file_issues:
                issues.extend(file_issues)
            
            # Calculate score
            total_checks = 5
            failed_checks = len([i for i in issues if i.get('severity') == 'critical'])
            
            check.score = ((total_checks - failed_checks) / total_checks) * 100
            check.passed = check.score >= self.thresholds['technical_validation'] * 100
            check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
            
            check.details = {
                'total_checks': total_checks,
                'issues_found': len(issues),
                'critical_issues': failed_checks
            }
            
            if issues:
                check.issues = issues[:10]  # Top 10 issues
                
                if failed_checks > 0:
                    check.recommendations.append(
                        f"Fix {failed_checks} critical technical issues"
                    )
            
        except Exception as e:
            logger.error(f"Technical validation check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    async def _check_performance_metrics(
        self,
        language_code: str
    ) -> ReadinessCheck:
        """Check performance metrics for language."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.PERFORMANCE_METRICS,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            # Get performance metrics
            metrics = await self.metrics.get_performance_metrics(language_code)
            
            # Check load times
            avg_load_time = metrics.get('avg_load_time_ms', 0)
            p95_load_time = metrics.get('p95_load_time_ms', 0)
            
            load_time_ok = (
                avg_load_time < self.config.get('max_avg_load_time', 100) and
                p95_load_time < self.config.get('max_p95_load_time', 200)
            )
            
            # Check TTS performance
            tts_metrics = await self.language_gateway.get_tts_metrics(language_code)
            avg_tts_time = tts_metrics.get('avg_generation_time_ms', 0)
            tts_cache_hit = tts_metrics.get('cache_hit_rate', 0)
            
            tts_ok = (
                avg_tts_time < self.config.get('max_tts_time', 500) and
                tts_cache_hit > self.config.get('min_cache_hit_rate', 0.8)
            )
            
            # Check memory usage
            memory_usage = metrics.get('memory_usage_mb', 0)
            memory_ok = memory_usage < self.config.get('max_memory_mb', 100)
            
            # Calculate overall performance score
            performance_score = 0
            if load_time_ok:
                performance_score += 40
            if tts_ok:
                performance_score += 40
            if memory_ok:
                performance_score += 20
            
            check.score = performance_score
            check.passed = performance_score >= self.thresholds['performance_metrics'] * 100
            check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
            
            check.details = {
                'load_times': {
                    'avg_ms': avg_load_time,
                    'p95_ms': p95_load_time,
                    'threshold_ok': load_time_ok
                },
                'tts_performance': {
                    'avg_generation_ms': avg_tts_time,
                    'cache_hit_rate': tts_cache_hit,
                    'threshold_ok': tts_ok
                },
                'memory': {
                    'usage_mb': memory_usage,
                    'threshold_ok': memory_ok
                }
            }
            
            if not load_time_ok:
                check.issues.append({
                    'type': 'slow_load_time',
                    'avg_ms': avg_load_time,
                    'p95_ms': p95_load_time
                })
                check.recommendations.append(
                    "Optimize content loading - consider chunking or lazy loading"
                )
            
            if not tts_ok:
                check.issues.append({
                    'type': 'slow_tts',
                    'avg_ms': avg_tts_time,
                    'cache_hit': tts_cache_hit
                })
                check.recommendations.append(
                    "Pre-generate common TTS audio or improve caching"
                )
            
        except Exception as e:
            logger.error(f"Performance metrics check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    async def _check_user_acceptance(
        self,
        language_code: str,
        previous_checks: Dict[ReadinessCheckType, ReadinessCheck]
    ) -> ReadinessCheck:
        """Check user acceptance test results."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.USER_ACCEPTANCE,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            # Get UAT results if available
            uat_results = await self._get_uat_results(language_code)
            
            if not uat_results:
                # No UAT data - check if we can estimate
                if self._can_estimate_acceptance(previous_checks):
                    check.score = self._estimate_acceptance_score(previous_checks)
                    check.status = ReadinessStatus.NEEDS_REVIEW
                    check.passed = check.score >= self.thresholds['user_acceptance'] * 100
                    
                    check.details = {
                        'method': 'estimated',
                        'based_on': 'automated_checks'
                    }
                    
                    check.recommendations.append(
                        "Conduct user acceptance testing with native speakers"
                    )
                else:
                    check.status = ReadinessStatus.NOT_STARTED
                    check.score = 0
                    check.passed = False
                    check.issues.append({
                        'type': 'no_uat_data',
                        'message': 'User acceptance testing not performed'
                    })
            else:
                # Analyze UAT results
                total_testers = uat_results['total_testers']
                satisfaction_score = uat_results['avg_satisfaction']
                comprehension_score = uat_results['avg_comprehension']
                usability_score = uat_results['avg_usability']
                
                # Calculate weighted score
                check.score = (
                    satisfaction_score * 0.4 +
                    comprehension_score * 0.4 +
                    usability_score * 0.2
                ) * 100
                
                check.passed = check.score >= self.thresholds['user_acceptance'] * 100
                check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
                
                check.details = {
                    'method': 'user_testing',
                    'total_testers': total_testers,
                    'satisfaction': satisfaction_score,
                    'comprehension': comprehension_score,
                    'usability': usability_score,
                    'feedback_items': uat_results.get('feedback_summary', [])
                }
                
                # Add issues from feedback
                critical_feedback = [
                    fb for fb in uat_results.get('feedback', [])
                    if fb.get('severity') == 'critical'
                ]
                
                if critical_feedback:
                    check.issues.extend(critical_feedback[:5])
                    check.recommendations.append(
                        f"Address {len(critical_feedback)} critical user feedback items"
                    )
            
        except Exception as e:
            logger.error(f"User acceptance check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    async def _check_legal_compliance(
        self,
        language_code: str
    ) -> ReadinessCheck:
        """Check legal and compliance requirements."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.LEGAL_COMPLIANCE,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            compliance_issues = []
            
            # Check required legal notices
            legal_categories = ['terms_of_service', 'privacy_policy', 'eula']
            
            for category in legal_categories:
                content = await self.localization.get_content_by_category(
                    language_code, category
                )
                
                if not content:
                    compliance_issues.append({
                        'type': 'missing_legal_content',
                        'category': category,
                        'severity': 'critical'
                    })
                else:
                    # Verify completeness
                    for key, value in content.items():
                        if not value.get('text') or len(value['text']) < 100:
                            compliance_issues.append({
                                'type': 'incomplete_legal_content',
                                'category': category,
                                'key': key,
                                'severity': 'critical'
                            })
            
            # Check age rating compliance
            age_rating_ok = await self._check_age_rating_compliance(language_code)
            if not age_rating_ok:
                compliance_issues.append({
                    'type': 'age_rating_violation',
                    'severity': 'critical'
                })
            
            # Check region-specific requirements
            region_issues = await self._check_regional_compliance(language_code)
            compliance_issues.extend(region_issues)
            
            # Calculate score
            critical_issues = len([
                i for i in compliance_issues
                if i.get('severity') == 'critical'
            ])
            
            if critical_issues > 0:
                check.score = 0  # Any critical compliance issue = 0
            else:
                check.score = 100 - (len(compliance_issues) * 10)
            
            check.passed = check.score >= self.thresholds['legal_compliance'] * 100
            check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
            
            check.details = {
                'total_issues': len(compliance_issues),
                'critical_issues': critical_issues,
                'categories_checked': legal_categories
            }
            
            if compliance_issues:
                check.issues = compliance_issues
                check.recommendations.append(
                    "Resolve all legal compliance issues before launch"
                )
            
        except Exception as e:
            logger.error(f"Legal compliance check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    async def _check_cultural_review(
        self,
        language_code: str,
        previous_checks: Dict[ReadinessCheckType, ReadinessCheck]
    ) -> ReadinessCheck:
        """Check cultural appropriateness review."""
        check = ReadinessCheck(
            check_type=ReadinessCheckType.CULTURAL_REVIEW,
            status=ReadinessStatus.IN_PROGRESS
        )
        
        start = asyncio.get_event_loop().time()
        
        try:
            # Get cultural review data
            cultural_review = await self._get_cultural_review(language_code)
            
            if not cultural_review:
                # Use automated checks if manual review not available
                quality_check = previous_checks.get(ReadinessCheckType.TRANSLATION_QUALITY)
                
                if quality_check:
                    # Extract cultural scores from quality check
                    validations = quality_check.details.get('validations', [])
                    cultural_scores = [
                        v.get('cultural_appropriateness', 0)
                        for v in validations
                        if v.get('cultural_appropriateness') is not None
                    ]
                    
                    if cultural_scores:
                        avg_cultural = sum(cultural_scores) / len(cultural_scores)
                        check.score = avg_cultural * 100
                        check.status = ReadinessStatus.NEEDS_REVIEW
                        
                        check.details = {
                            'method': 'automated',
                            'samples_checked': len(cultural_scores)
                        }
                    else:
                        check.status = ReadinessStatus.NOT_STARTED
                        check.score = 0
                        
                        check.issues.append({
                            'type': 'no_cultural_data',
                            'message': 'Cultural review not performed'
                        })
                
                check.recommendations.append(
                    "Conduct manual cultural review with native speakers"
                )
            else:
                # Use manual review results
                check.score = cultural_review['overall_score'] * 100
                check.passed = check.score >= self.thresholds['cultural_review'] * 100
                check.status = ReadinessStatus.PASSED if check.passed else ReadinessStatus.FAILED
                
                check.details = {
                    'method': 'manual_review',
                    'reviewer': cultural_review.get('reviewer'),
                    'review_date': cultural_review.get('date'),
                    'categories_reviewed': cultural_review.get('categories', [])
                }
                
                # Add issues from review
                if cultural_review.get('issues'):
                    check.issues.extend(cultural_review['issues'])
                    
                    critical_cultural = [
                        i for i in cultural_review['issues']
                        if i.get('severity') == 'critical'
                    ]
                    
                    if critical_cultural:
                        check.recommendations.append(
                            f"Address {len(critical_cultural)} critical cultural issues"
                        )
            
            check.passed = check.score >= self.thresholds['cultural_review'] * 100
            
        except Exception as e:
            logger.error(f"Cultural review check failed: {e}")
            check.status = ReadinessStatus.FAILED
            check.passed = False
            check.score = 0
            check.issues.append({
                'error': str(e)
            })
        
        check.duration_ms = (asyncio.get_event_loop().time() - start) * 1000
        return check
    
    def _calculate_overall_status(self, report: LanguageReadinessReport):
        """Calculate overall readiness status and score."""
        if not report.checks:
            report.overall_status = ReadinessStatus.NOT_STARTED
            report.overall_score = 0
            return
        
        # Weight each check type
        weights = {
            ReadinessCheckType.CONTENT_COMPLETENESS: 0.20,
            ReadinessCheckType.TRANSLATION_QUALITY: 0.20,
            ReadinessCheckType.AUDIO_COVERAGE: 0.15,
            ReadinessCheckType.TECHNICAL_VALIDATION: 0.15,
            ReadinessCheckType.PERFORMANCE_METRICS: 0.10,
            ReadinessCheckType.USER_ACCEPTANCE: 0.10,
            ReadinessCheckType.LEGAL_COMPLIANCE: 0.05,
            ReadinessCheckType.CULTURAL_REVIEW: 0.05
        }
        
        total_weight = 0
        weighted_score = 0
        
        failed_critical = False
        needs_review = False
        
        for check_type, check in report.checks.items():
            weight = weights.get(check_type, 0.1)
            total_weight += weight
            weighted_score += check.score * weight
            
            if check.status == ReadinessStatus.FAILED:
                if check_type in [
                    ReadinessCheckType.LEGAL_COMPLIANCE,
                    ReadinessCheckType.CONTENT_COMPLETENESS
                ]:
                    failed_critical = True
                    
            elif check.status == ReadinessStatus.NEEDS_REVIEW:
                needs_review = True
        
        # Normalize score
        report.overall_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Determine status
        if failed_critical:
            report.overall_status = ReadinessStatus.FAILED
        elif needs_review:
            report.overall_status = ReadinessStatus.NEEDS_REVIEW
        elif all(check.passed for check in report.checks.values()):
            report.overall_status = ReadinessStatus.PASSED
        else:
            report.overall_status = ReadinessStatus.IN_PROGRESS
    
    def _identify_launch_blockers(self, report: LanguageReadinessReport):
        """Identify launch blocking issues."""
        # Content completeness blockers
        content_check = report.checks.get(ReadinessCheckType.CONTENT_COMPLETENESS)
        if content_check and not content_check.passed:
            coverage = content_check.details.get('coverage', 0)
            if coverage < 0.95:
                report.launch_blocking_issues.append({
                    'issue': LaunchIssue.MISSING_CONTENT.value,
                    'severity': 'critical',
                    'description': f'Content coverage too low: {coverage:.1%}',
                    'required_action': 'Complete missing translations'
                })
        
        # Quality blockers
        quality_check = report.checks.get(ReadinessCheckType.TRANSLATION_QUALITY)
        if quality_check:
            critical_issues = quality_check.details.get('critical_issues', 0)
            if critical_issues > 0:
                report.launch_blocking_issues.append({
                    'issue': LaunchIssue.POOR_QUALITY.value,
                    'severity': 'critical',
                    'description': f'{critical_issues} critical quality issues found',
                    'required_action': 'Fix critical translation issues'
                })
        
        # Technical blockers
        tech_check = report.checks.get(ReadinessCheckType.TECHNICAL_VALIDATION)
        if tech_check and not tech_check.passed:
            report.launch_blocking_issues.append({
                'issue': LaunchIssue.TECHNICAL_ERROR.value,
                'severity': 'critical',
                'description': 'Technical validation failed',
                'required_action': 'Resolve technical issues'
            })
        
        # Performance blockers
        perf_check = report.checks.get(ReadinessCheckType.PERFORMANCE_METRICS)
        if perf_check and perf_check.score < 80:
            report.launch_blocking_issues.append({
                'issue': LaunchIssue.PERFORMANCE_ISSUE.value,
                'severity': 'high',
                'description': 'Performance below acceptable levels',
                'required_action': 'Optimize loading and TTS performance'
            })
        
        # Compliance blockers
        compliance_check = report.checks.get(ReadinessCheckType.LEGAL_COMPLIANCE)
        if compliance_check and not compliance_check.passed:
            report.launch_blocking_issues.append({
                'issue': LaunchIssue.COMPLIANCE_ISSUE.value,
                'severity': 'critical',
                'description': 'Legal compliance requirements not met',
                'required_action': 'Complete all legal requirements'
            })
        
        # Cultural blockers
        cultural_check = report.checks.get(ReadinessCheckType.CULTURAL_REVIEW)
        if cultural_check:
            critical_cultural = [
                i for i in cultural_check.issues
                if i.get('severity') == 'critical'
            ]
            if critical_cultural:
                report.launch_blocking_issues.append({
                    'issue': LaunchIssue.CULTURAL_CONCERN.value,
                    'severity': 'critical',
                    'description': f'{len(critical_cultural)} critical cultural issues',
                    'required_action': 'Address cultural sensitivity issues'
                })
    
    def _can_certify(self, report: LanguageReadinessReport) -> bool:
        """Determine if language can be certified."""
        # No critical launch blockers
        if any(
            blocker['severity'] == 'critical'
            for blocker in report.launch_blocking_issues
        ):
            return False
        
        # All required checks passed
        required_checks = [
            ReadinessCheckType.CONTENT_COMPLETENESS,
            ReadinessCheckType.TRANSLATION_QUALITY,
            ReadinessCheckType.TECHNICAL_VALIDATION,
            ReadinessCheckType.LEGAL_COMPLIANCE
        ]
        
        for check_type in required_checks:
            check = report.checks.get(check_type)
            if not check or not check.passed:
                return False
        
        # Overall score meets threshold
        min_certification_score = self.config.get('min_certification_score', 90)
        if report.overall_score < min_certification_score:
            return False
        
        return True
    
    # Helper methods
    
    async def _get_recent_certification(
        self,
        language_code: str
    ) -> Optional[LanguageReadinessReport]:
        """Get recent certification if exists and valid."""
        # Would check database/cache for recent report
        # For now, return None to always run fresh
        return None
    
    async def _save_certification_report(
        self,
        report: LanguageReadinessReport
    ):
        """Save certification report to database."""
        # Would save to database
        pass
    
    async def _check_tts_quality(self, language_code: str) -> float:
        """Check TTS quality score."""
        # Would analyze TTS quality metrics
        return 0.85  # Placeholder
    
    async def _validate_encoding(
        self,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Validate text encoding."""
        # Would check encoding issues
        return []
    
    async def _validate_placeholders(
        self,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Validate placeholder consistency."""
        # Would check placeholder mismatches
        return []
    
    async def _validate_format_strings(
        self,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Validate format string consistency."""
        # Would check format string issues
        return []
    
    async def _validate_ui_layout(
        self,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Validate UI layout compatibility."""
        # Would check UI overflow issues
        return []
    
    async def _validate_file_formats(
        self,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Validate file format compliance."""
        # Would check file format issues
        return []
    
    async def _get_uat_results(
        self,
        language_code: str
    ) -> Optional[Dict[str, Any]]:
        """Get user acceptance test results."""
        # Would fetch from database
        return None
    
    def _can_estimate_acceptance(
        self,
        previous_checks: Dict[ReadinessCheckType, ReadinessCheck]
    ) -> bool:
        """Check if we can estimate acceptance score."""
        required = [
            ReadinessCheckType.TRANSLATION_QUALITY,
            ReadinessCheckType.TECHNICAL_VALIDATION
        ]
        
        for check_type in required:
            if check_type not in previous_checks:
                return False
                
        return True
    
    def _estimate_acceptance_score(
        self,
        previous_checks: Dict[ReadinessCheckType, ReadinessCheck]
    ) -> float:
        """Estimate acceptance score from other checks."""
        quality_score = previous_checks[ReadinessCheckType.TRANSLATION_QUALITY].score
        tech_score = previous_checks[ReadinessCheckType.TECHNICAL_VALIDATION].score
        
        # Conservative estimate
        return min(quality_score, tech_score) * 0.9
    
    async def _check_age_rating_compliance(
        self,
        language_code: str
    ) -> bool:
        """Check age rating compliance."""
        # Would check content against age ratings
        return True
    
    async def _check_regional_compliance(
        self,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Check region-specific compliance."""
        # Would check regional requirements
        return []
    
    async def _get_cultural_review(
        self,
        language_code: str
    ) -> Optional[Dict[str, Any]]:
        """Get manual cultural review results."""
        # Would fetch from database
        return None
    
    def _count_by_severity(
        self,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count issues by severity."""
        from collections import defaultdict
        severity_count = defaultdict(int)
        
        for issue in issues:
            severity = issue.get('severity', 'medium')
            severity_count[severity] += 1
            
        return dict(severity_count)
