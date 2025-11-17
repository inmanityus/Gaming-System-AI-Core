"""
Ethelred integration for localized content quality assurance.
Implements TML-11 (R-ML-ETHELRED-001, R-ML-ETHELRED-002).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from collections import defaultdict
import asyncio
import json

# Import Ethelred components
from services.ethelred_audio_metrics.intelligibility_analyzer import IntelligibilityAnalyzer
from services.ethelred_audio_metrics.archetype_analyzer import ArchetypeConformityAnalyzer
from services.ethelred_engagement.addiction_indicators import AddictionIndicatorCalculator
from services.ethelred_engagement.safety_constraints import EngagementSafetyConstraints

logger = logging.getLogger(__name__)


class LocalizedContentType(str, Enum):
    """Types of localized content to validate."""
    UI_TEXT = "ui_text"
    NARRATIVE_DIALOGUE = "narrative_dialogue"  
    TUTORIAL_INSTRUCTIONS = "tutorial_instructions"
    SYSTEM_MESSAGES = "system_messages"
    AUDIO_DIALOGUE = "audio_dialogue"
    SUBTITLES = "subtitles"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Must fix before release
    HIGH = "high"         # Should fix before release
    MEDIUM = "medium"     # Consider fixing
    LOW = "low"          # Nice to fix
    INFO = "info"        # Informational only


@dataclass
class LocalizedContentValidation:
    """Validation result for localized content."""
    content_id: str
    content_type: LocalizedContentType
    language_code: str
    
    # Validation results
    passed: bool = True
    issues: List[Dict[str, Any]] = None
    
    # Ethelred scores
    intelligibility_score: Optional[float] = None
    intelligibility_band: Optional[str] = None
    
    archetype_conformity_score: Optional[float] = None
    archetype_conformity_band: Optional[str] = None
    
    cultural_appropriateness: Optional[float] = None
    engagement_safety: Optional[bool] = None
    
    # Metadata
    validated_at: datetime = None
    validation_time_ms: float = 0
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.validated_at is None:
            self.validated_at = datetime.utcnow()


class LocalizedQAOrchestrator:
    """
    Orchestrates Ethelred quality checks for localized content.
    Ensures consistent quality across all languages.
    """
    
    def __init__(
        self,
        localization_service,
        language_system,
        ethelred_config: Dict[str, Any],
        postgres_pool=None
    ):
        self.localization = localization_service
        self.language_system = language_system
        self.config = ethelred_config
        self.postgres_pool = postgres_pool
        
        # Initialize Ethelred components
        self.intelligibility_analyzer = IntelligibilityAnalyzer(
            sample_rate=self.config.get('sample_rate', 48000)
        )
        self.archetype_analyzer = ArchetypeConformityAnalyzer(
            sample_rate=self.config.get('sample_rate', 48000)
        )
        
        if postgres_pool:
            self.addiction_calculator = AddictionIndicatorCalculator(postgres_pool)
        
        self.safety_constraints = EngagementSafetyConstraints()
        
        # Language-specific validators
        self.language_validators = self._initialize_language_validators()
    
    def _initialize_language_validators(self) -> Dict[str, Any]:
        """Initialize language-specific validation rules."""
        return {
            'ja-JP': {
                'politeness_levels': ['casual', 'polite', 'formal', 'honorific'],
                'character_limits': {
                    'ui_button': 8,
                    'ui_label': 20,
                    'subtitle_line': 30
                },
                'cultural_checks': ['honorific_usage', 'age_appropriateness']
            },
            'ar-SA': {
                'text_direction': 'rtl',
                'cultural_checks': ['religious_sensitivity', 'gender_appropriateness'],
                'numeral_system': 'eastern_arabic'
            },
            'zh-CN': {
                'character_limits': {
                    'ui_button': 6,
                    'ui_label': 15,
                    'subtitle_line': 25
                },
                'cultural_checks': ['political_sensitivity', 'simplified_traditional']
            },
            'ko-KR': {
                'politeness_levels': ['informal', 'formal'],
                'age_hierarchy': True,
                'cultural_checks': ['honorific_usage', 'age_appropriateness']
            }
        }
    
    async def validate_localized_content(
        self,
        content_id: str,
        content_type: LocalizedContentType,
        language_code: str,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        audio_data: Optional[bytes] = None,
        speaker_id: Optional[str] = None
    ) -> LocalizedContentValidation:
        """
        Validate a piece of localized content.
        
        Args:
            content_id: Unique identifier for content
            content_type: Type of content
            language_code: Target language
            text: Localized text
            context: Additional context (speaker, scene, etc.)
            audio_data: Optional audio for speech content
            speaker_id: Optional speaker/character ID
            
        Returns:
            Validation result with issues and scores
        """
        start_time = asyncio.get_event_loop().time()
        
        validation = LocalizedContentValidation(
            content_id=content_id,
            content_type=content_type,
            language_code=language_code
        )
        
        try:
            # Text validation
            await self._validate_text(
                text, content_type, language_code, context, validation
            )
            
            # Audio validation (if applicable)
            if audio_data and content_type == LocalizedContentType.AUDIO_DIALOGUE:
                await self._validate_audio(
                    audio_data, text, language_code, speaker_id, validation
                )
            
            # Cultural validation
            await self._validate_cultural_appropriateness(
                text, content_type, language_code, context, validation
            )
            
            # Engagement safety validation
            if content_type == LocalizedContentType.NARRATIVE_DIALOGUE:
                await self._validate_engagement_safety(
                    text, context, validation
                )
            
            # Determine if passed
            validation.passed = not any(
                issue.get('severity') in [ValidationSeverity.CRITICAL.value, 
                                         ValidationSeverity.HIGH.value]
                for issue in validation.issues
            )
            
        except Exception as e:
            logger.error(f"Validation error for {content_id}: {e}")
            validation.passed = False
            validation.issues.append({
                'type': 'validation_error',
                'severity': ValidationSeverity.CRITICAL.value,
                'message': str(e)
            })
        
        validation.validation_time_ms = (
            asyncio.get_event_loop().time() - start_time
        ) * 1000
        
        return validation
    
    async def _validate_text(
        self,
        text: str,
        content_type: LocalizedContentType,
        language_code: str,
        context: Optional[Dict[str, Any]],
        validation: LocalizedContentValidation
    ):
        """Validate text content."""
        # Length validation
        if content_type == LocalizedContentType.UI_TEXT:
            max_length = self._get_ui_length_limit(language_code, context)
            if len(text) > max_length:
                validation.issues.append({
                    'type': 'text_overflow',
                    'severity': ValidationSeverity.HIGH.value,
                    'message': f'Text exceeds limit: {len(text)} > {max_length}',
                    'text': text
                })
        
        # Character encoding validation
        if not self._validate_encoding(text, language_code):
            validation.issues.append({
                'type': 'encoding_error',
                'severity': ValidationSeverity.CRITICAL.value,
                'message': 'Text contains invalid characters for language',
                'language': language_code
            })
        
        # Placeholder validation
        placeholders = self._extract_placeholders(text)
        if context and 'expected_placeholders' in context:
            expected = set(context['expected_placeholders'])
            actual = set(placeholders)
            
            if expected != actual:
                validation.issues.append({
                    'type': 'placeholder_mismatch',
                    'severity': ValidationSeverity.CRITICAL.value,
                    'message': 'Placeholder mismatch',
                    'expected': list(expected),
                    'actual': list(actual)
                })
        
        # Language-specific validation
        if language_code in self.language_validators:
            await self._validate_language_specific(
                text, content_type, language_code, context, validation
            )
    
    async def _validate_audio(
        self,
        audio_data: bytes,
        text: str,
        language_code: str,
        speaker_id: Optional[str],
        validation: LocalizedContentValidation
    ):
        """Validate audio content using Ethelred."""
        # Convert audio data to numpy array
        import numpy as np
        import soundfile as sf
        import io
        
        try:
            # Read audio data
            audio_array, sample_rate = sf.read(io.BytesIO(audio_data))
            
            # Intelligibility analysis
            score, band = self.intelligibility_analyzer.analyze(audio_array)
            validation.intelligibility_score = score
            validation.intelligibility_band = band
            
            if band == 'unacceptable':
                validation.issues.append({
                    'type': 'poor_intelligibility',
                    'severity': ValidationSeverity.HIGH.value,
                    'message': f'Audio intelligibility is poor: {score:.2f}',
                    'band': band
                })
            elif band == 'degraded':
                validation.issues.append({
                    'type': 'degraded_intelligibility',
                    'severity': ValidationSeverity.MEDIUM.value,
                    'message': f'Audio intelligibility is degraded: {score:.2f}',
                    'band': band
                })
            
            # Archetype conformity (if speaker provided)
            if speaker_id:
                # Map speaker to archetype
                archetype_id = self._get_archetype_for_speaker(speaker_id)
                if archetype_id:
                    conf_score, conf_band = self.archetype_analyzer.analyze(
                        audio_array, archetype_id
                    )
                    validation.archetype_conformity_score = conf_score
                    validation.archetype_conformity_band = conf_band
                    
                    if conf_band == 'misaligned':
                        validation.issues.append({
                            'type': 'voice_misalignment',
                            'severity': ValidationSeverity.HIGH.value,
                            'message': f'Voice does not match character: {conf_score:.2f}',
                            'archetype': archetype_id,
                            'speaker': speaker_id
                        })
            
        except Exception as e:
            logger.error(f"Audio validation error: {e}")
            validation.issues.append({
                'type': 'audio_processing_error',
                'severity': ValidationSeverity.HIGH.value,
                'message': str(e)
            })
    
    async def _validate_cultural_appropriateness(
        self,
        text: str,
        content_type: LocalizedContentType,
        language_code: str,
        context: Optional[Dict[str, Any]],
        validation: LocalizedContentValidation
    ):
        """Validate cultural appropriateness."""
        if language_code not in self.language_validators:
            return
        
        validator = self.language_validators[language_code]
        cultural_checks = validator.get('cultural_checks', [])
        
        # Run cultural checks
        issues = []
        
        if 'religious_sensitivity' in cultural_checks:
            issues.extend(self._check_religious_sensitivity(text, language_code))
        
        if 'gender_appropriateness' in cultural_checks:
            issues.extend(self._check_gender_appropriateness(
                text, language_code, context
            ))
        
        if 'political_sensitivity' in cultural_checks:
            issues.extend(self._check_political_sensitivity(text, language_code))
        
        if 'honorific_usage' in cultural_checks:
            issues.extend(self._check_honorific_usage(
                text, language_code, context
            ))
        
        # Score cultural appropriateness
        if issues:
            validation.cultural_appropriateness = max(0, 1 - len(issues) * 0.2)
            
            for issue in issues:
                validation.issues.append({
                    'type': 'cultural_issue',
                    'severity': ValidationSeverity.HIGH.value,
                    'message': issue,
                    'language': language_code
                })
        else:
            validation.cultural_appropriateness = 1.0
    
    async def _validate_engagement_safety(
        self,
        text: str,
        context: Optional[Dict[str, Any]],
        validation: LocalizedContentValidation
    ):
        """Validate engagement safety constraints."""
        # Check if content could be used for manipulation
        manipulation_keywords = [
            'keep playing', 'don\'t stop', 'one more', 'almost there',
            'so close', 'nearly done', 'just a bit more'
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in manipulation_keywords if kw in text_lower]
        
        if found_keywords and context.get('is_repeated', False):
            validation.engagement_safety = False
            validation.issues.append({
                'type': 'engagement_manipulation',
                'severity': ValidationSeverity.HIGH.value,
                'message': 'Content may encourage unhealthy play patterns',
                'keywords': found_keywords
            })
        else:
            validation.engagement_safety = True
    
    async def _validate_language_specific(
        self,
        text: str,
        content_type: LocalizedContentType,
        language_code: str,
        context: Optional[Dict[str, Any]],
        validation: LocalizedContentValidation
    ):
        """Run language-specific validation rules."""
        validator = self.language_validators[language_code]
        
        # Japanese validation
        if language_code == 'ja-JP':
            # Check politeness level
            if context and 'required_politeness' in context:
                actual_politeness = self._detect_japanese_politeness(text)
                required = context['required_politeness']
                
                if actual_politeness != required:
                    validation.issues.append({
                        'type': 'politeness_mismatch',
                        'severity': ValidationSeverity.MEDIUM.value,
                        'message': f'Politeness level mismatch: {actual_politeness} != {required}',
                        'actual': actual_politeness,
                        'required': required
                    })
        
        # Arabic validation
        elif language_code == 'ar-SA':
            # Check text direction markers
            if content_type == LocalizedContentType.UI_TEXT:
                if not self._has_rtl_markers(text):
                    validation.issues.append({
                        'type': 'rtl_missing',
                        'severity': ValidationSeverity.MEDIUM.value,
                        'message': 'Text may need RTL direction markers'
                    })
        
        # Chinese validation
        elif language_code == 'zh-CN':
            # Check for traditional characters
            if self._contains_traditional_chinese(text):
                validation.issues.append({
                    'type': 'traditional_characters',
                    'severity': ValidationSeverity.HIGH.value,
                    'message': 'Text contains traditional Chinese characters'
                })
    
    async def validate_batch(
        self,
        content_items: List[Dict[str, Any]],
        parallel: bool = True
    ) -> List[LocalizedContentValidation]:
        """Validate multiple content items."""
        if parallel:
            tasks = []
            for item in content_items:
                task = self.validate_localized_content(
                    content_id=item['content_id'],
                    content_type=LocalizedContentType(item['content_type']),
                    language_code=item['language_code'],
                    text=item['text'],
                    context=item.get('context'),
                    audio_data=item.get('audio_data'),
                    speaker_id=item.get('speaker_id')
                )
                tasks.append(task)
            
            return await asyncio.gather(*tasks)
        else:
            results = []
            for item in content_items:
                result = await self.validate_localized_content(
                    content_id=item['content_id'],
                    content_type=LocalizedContentType(item['content_type']),
                    language_code=item['language_code'],
                    text=item['text'],
                    context=item.get('context'),
                    audio_data=item.get('audio_data'),
                    speaker_id=item.get('speaker_id')
                )
                results.append(result)
            return results
    
    async def generate_qa_report(
        self,
        validations: List[LocalizedContentValidation],
        language_code: str
    ) -> Dict[str, Any]:
        """Generate QA report for a language."""
        total = len(validations)
        passed = sum(1 for v in validations if v.passed)
        
        # Group issues by type
        issues_by_type = defaultdict(list)
        for validation in validations:
            for issue in validation.issues:
                issues_by_type[issue['type']].append({
                    'content_id': validation.content_id,
                    'severity': issue['severity'],
                    'message': issue['message']
                })
        
        # Calculate average scores
        intelligibility_scores = [
            v.intelligibility_score for v in validations
            if v.intelligibility_score is not None
        ]
        
        archetype_scores = [
            v.archetype_conformity_score for v in validations
            if v.archetype_conformity_score is not None
        ]
        
        cultural_scores = [
            v.cultural_appropriateness for v in validations
            if v.cultural_appropriateness is not None
        ]
        
        report = {
            'language_code': language_code,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_content': total,
                'passed': passed,
                'failed': total - passed,
                'pass_rate': passed / total if total > 0 else 0
            },
            'scores': {
                'avg_intelligibility': (
                    sum(intelligibility_scores) / len(intelligibility_scores)
                    if intelligibility_scores else None
                ),
                'avg_archetype_conformity': (
                    sum(archetype_scores) / len(archetype_scores)
                    if archetype_scores else None
                ),
                'avg_cultural_appropriateness': (
                    sum(cultural_scores) / len(cultural_scores)
                    if cultural_scores else None
                )
            },
            'issues': {
                issue_type: {
                    'count': len(issues),
                    'severity_breakdown': self._count_by_severity(issues)
                }
                for issue_type, issues in issues_by_type.items()
            },
            'critical_issues': [
                issue for issue_list in issues_by_type.values()
                for issue in issue_list
                if issue['severity'] == ValidationSeverity.CRITICAL.value
            ]
        }
        
        return report
    
    # Helper methods
    
    def _get_ui_length_limit(
        self,
        language_code: str,
        context: Optional[Dict[str, Any]]
    ) -> int:
        """Get UI text length limit for language."""
        element_type = context.get('ui_element_type', 'label') if context else 'label'
        
        if language_code in self.language_validators:
            limits = self.language_validators[language_code].get(
                'character_limits', {}
            )
            return limits.get(f'ui_{element_type}', 50)
        
        # Default limits
        return {
            'button': 20,
            'label': 50,
            'tooltip': 100,
            'dialog': 200
        }.get(element_type, 50)
    
    def _validate_encoding(self, text: str, language_code: str) -> bool:
        """Validate text encoding for language."""
        try:
            # Ensure text can be encoded in expected encoding
            if language_code.startswith('zh'):
                text.encode('gb18030')
            elif language_code.startswith('ja'):
                text.encode('shift_jis')
            elif language_code.startswith('ar'):
                text.encode('windows-1256')
            else:
                text.encode('utf-8')
            return True
        except UnicodeEncodeError:
            return False
    
    def _extract_placeholders(self, text: str) -> List[str]:
        """Extract placeholder variables from text."""
        import re
        placeholders = []
        
        # Common placeholder patterns
        patterns = [
            r'\{(\w+)\}',        # {variable}
            r'%\((\w+)\)s',      # %(variable)s
            r'\$\{(\w+)\}',      # ${variable}
            r'{{(\w+)}}'         # {{variable}}
        ]
        
        for pattern in patterns:
            placeholders.extend(re.findall(pattern, text))
        
        return placeholders
    
    def _get_archetype_for_speaker(self, speaker_id: str) -> Optional[str]:
        """Map speaker ID to archetype."""
        # This would be configured based on game data
        speaker_archetypes = {
            'vampire_lord': 'vampire_alpha',
            'player_character': 'human_agent',
            'ghoul_servant': 'corpse_tender'
        }
        
        return speaker_archetypes.get(speaker_id)
    
    def _check_religious_sensitivity(
        self,
        text: str,
        language_code: str
    ) -> List[str]:
        """Check for religious sensitivity issues."""
        issues = []
        
        if language_code == 'ar-SA':
            # Simplified checks - production would be more comprehensive
            sensitive_terms = ['alcohol', 'pork', 'gambling']
            text_lower = text.lower()
            
            for term in sensitive_terms:
                if term in text_lower:
                    issues.append(
                        f"Text contains potentially sensitive term: {term}"
                    )
        
        return issues
    
    def _check_gender_appropriateness(
        self,
        text: str,
        language_code: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Check gender appropriateness."""
        issues = []
        
        # This would be more sophisticated in production
        if context and 'speaker_gender' in context:
            # Check for gender-specific language
            pass
        
        return issues
    
    def _check_political_sensitivity(
        self,
        text: str,
        language_code: str
    ) -> List[str]:
        """Check for political sensitivity."""
        issues = []
        
        # Simplified - production would use more comprehensive checks
        if language_code == 'zh-CN':
            sensitive_terms = ['taiwan', 'tibet', 'democracy']
            text_lower = text.lower()
            
            for term in sensitive_terms:
                if term in text_lower:
                    issues.append(
                        f"Text may contain politically sensitive content: {term}"
                    )
        
        return issues
    
    def _check_honorific_usage(
        self,
        text: str,
        language_code: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Check proper honorific usage."""
        issues = []
        
        if language_code == 'ja-JP' and context:
            # Check for appropriate honorifics based on relationship
            relationship = context.get('speaker_relationship', 'neutral')
            
            # Simplified checks
            if relationship == 'superior_to_inferior':
                if 'さん' in text or 'sama' in text:
                    issues.append(
                        "Inappropriate honorific for superior speaking to inferior"
                    )
            elif relationship == 'inferior_to_superior':
                if not any(hon in text for hon in ['さん', 'sama', '様']):
                    issues.append(
                        "Missing honorific for inferior speaking to superior"
                    )
        
        return issues
    
    def _detect_japanese_politeness(self, text: str) -> str:
        """Detect Japanese politeness level."""
        # Simplified detection
        if any(marker in text for marker in ['です', 'ます', 'ございます']):
            return 'polite'
        elif any(marker in text for marker in ['だよ', 'だね', 'じゃん']):
            return 'casual'
        elif any(marker in text for marker in ['でございます', 'いたします']):
            return 'formal'
        
        return 'neutral'
    
    def _has_rtl_markers(self, text: str) -> bool:
        """Check if text has RTL direction markers."""
        rtl_markers = ['\u200F', '\u202B', '\u202E']
        return any(marker in text for marker in rtl_markers)
    
    def _contains_traditional_chinese(self, text: str) -> bool:
        """Check if text contains traditional Chinese characters."""
        # Simplified check - would use proper character database
        traditional_chars = ['國', '學', '愛', '體', '會', '經']
        return any(char in text for char in traditional_chars)
    
    def _count_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity."""
        severity_count = defaultdict(int)
        for issue in issues:
            severity_count[issue['severity']] += 1
        return dict(severity_count)
