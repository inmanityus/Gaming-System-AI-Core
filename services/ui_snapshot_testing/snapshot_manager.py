"""
UI Snapshot testing for localized UI elements.
Implements TML-07 (R-ML-QA-001, R-ML-QA-002).
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64

logger = logging.getLogger(__name__)


class UIElementType(str, Enum):
    """Types of UI elements to test."""
    BUTTON = "button"
    LABEL = "label"
    DIALOG = "dialog"
    MENU = "menu"
    HUD = "hud"
    SUBTITLE = "subtitle"
    TOOLTIP = "tooltip"
    NOTIFICATION = "notification"


class IssueType(str, Enum):
    """Types of localization issues."""
    TEXT_OVERFLOW = "text_overflow"
    TRUNCATION = "truncation"
    FONT_MISSING = "font_missing"
    LAYOUT_BROKEN = "layout_broken"
    CONTRAST_POOR = "contrast_poor"
    OVERLAP = "overlap"
    ALIGNMENT = "alignment"
    WRAPPING = "wrapping"
    CHARACTER_CORRUPTION = "character_corruption"


@dataclass
class UIElement:
    """Definition of a UI element to test."""
    element_id: str
    type: UIElementType
    localization_key: str
    
    # Layout constraints
    x: int
    y: int
    width: int
    height: int
    
    # Style properties
    font_size: int = 16
    font_family: str = "default"
    text_color: str = "#FFFFFF"
    background_color: Optional[str] = None
    padding: int = 10
    alignment: str = "left"  # left, center, right
    
    # Additional properties
    max_lines: Optional[int] = None
    allow_wrap: bool = True
    scale_to_fit: bool = False


@dataclass
class SnapshotResult:
    """Result of a UI snapshot test."""
    element_id: str
    language_code: str
    text: str
    
    # Visual results
    screenshot: Optional[bytes] = None
    screenshot_width: Optional[int] = None
    screenshot_height: Optional[int] = None
    
    # Issues found
    issues: List[Dict[str, Any]] = None
    
    # Metrics
    text_width: float = 0
    text_height: float = 0
    overflow_pixels: int = 0
    utilization_percentage: float = 0  # How much of available space is used
    
    # Status
    passed: bool = True
    tested_at: datetime = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.tested_at is None:
            self.tested_at = datetime.utcnow()


@dataclass
class FontConfig:
    """Font configuration for different languages."""
    language_code: str
    font_path: str
    fallback_fonts: List[str] = None
    requires_special_rendering: bool = False
    line_height_multiplier: float = 1.0
    
    def __post_init__(self):
        if self.fallback_fonts is None:
            self.fallback_fonts = []


class UISnapshotManager:
    """
    Manages UI snapshot testing for localized text.
    Generates screenshots and detects visual issues.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.font_configs = self._load_font_configs()
        self.font_cache = {}
        self.issue_detectors = self._initialize_detectors()
    
    def _load_font_configs(self) -> Dict[str, FontConfig]:
        """Load font configurations for different languages."""
        configs = {
            'en-US': FontConfig(
                language_code='en-US',
                font_path='assets/fonts/Roboto-Regular.ttf',
                fallback_fonts=['Arial', 'sans-serif']
            ),
            'ja-JP': FontConfig(
                language_code='ja-JP',
                font_path='assets/fonts/NotoSansCJK-Regular.ttc',
                fallback_fonts=['MS Gothic', 'Hiragino Sans'],
                requires_special_rendering=True,
                line_height_multiplier=1.2
            ),
            'zh-CN': FontConfig(
                language_code='zh-CN',
                font_path='assets/fonts/NotoSansSC-Regular.otf',
                fallback_fonts=['SimHei', 'Microsoft YaHei'],
                requires_special_rendering=True,
                line_height_multiplier=1.15
            ),
            'ko-KR': FontConfig(
                language_code='ko-KR',
                font_path='assets/fonts/NotoSansKR-Regular.otf',
                fallback_fonts=['Malgun Gothic', 'Gulim'],
                requires_special_rendering=True,
                line_height_multiplier=1.1
            ),
            'ar-SA': FontConfig(
                language_code='ar-SA',
                font_path='assets/fonts/NotoSansArabic-Regular.ttf',
                fallback_fonts=['Arial', 'Tahoma'],
                requires_special_rendering=True,
                line_height_multiplier=1.3
            ),
            'th-TH': FontConfig(
                language_code='th-TH',
                font_path='assets/fonts/NotoSansThai-Regular.ttf',
                fallback_fonts=['Tahoma', 'sans-serif'],
                requires_special_rendering=True,
                line_height_multiplier=1.4
            )
        }
        
        # Default fallback
        for lang_code in ['fr-FR', 'de-DE', 'es-ES', 'pt-BR', 'ru-RU', 'it-IT']:
            configs[lang_code] = FontConfig(
                language_code=lang_code,
                font_path='assets/fonts/Roboto-Regular.ttf',
                fallback_fonts=['Arial', 'sans-serif'],
                line_height_multiplier=1.1
            )
        
        return configs
    
    def _initialize_detectors(self) -> Dict[IssueType, callable]:
        """Initialize issue detection functions."""
        return {
            IssueType.TEXT_OVERFLOW: self._detect_text_overflow,
            IssueType.TRUNCATION: self._detect_truncation,
            IssueType.FONT_MISSING: self._detect_font_missing,
            IssueType.CONTRAST_POOR: self._detect_poor_contrast,
            IssueType.CHARACTER_CORRUPTION: self._detect_character_corruption
        }
    
    async def test_element(
        self,
        element: UIElement,
        text: str,
        language_code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> SnapshotResult:
        """
        Test a single UI element with localized text.
        
        Args:
            element: UI element definition
            text: Localized text to test
            language_code: Language of the text
            context: Additional context (e.g., game state)
            
        Returns:
            Snapshot test result with issues and screenshot
        """
        result = SnapshotResult(
            element_id=element.element_id,
            language_code=language_code,
            text=text
        )
        
        try:
            # Get appropriate font
            font = self._get_font(language_code, element.font_family, element.font_size)
            
            # Create canvas
            img = Image.new('RGBA', (element.width, element.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw background if specified
            if element.background_color:
                draw.rectangle(
                    [(0, 0), (element.width, element.height)],
                    fill=element.background_color
                )
            
            # Calculate text metrics
            text_bbox = self._get_text_bbox(draw, text, font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            result.text_width = text_width
            result.text_height = text_height
            
            # Calculate available space
            available_width = element.width - (2 * element.padding)
            available_height = element.height - (2 * element.padding)
            
            # Check for overflow
            if text_width > available_width:
                result.overflow_pixels = int(text_width - available_width)
                result.issues.append({
                    'type': IssueType.TEXT_OVERFLOW.value,
                    'severity': 'high',
                    'details': {
                        'text_width': text_width,
                        'available_width': available_width,
                        'overflow': result.overflow_pixels
                    }
                })
                result.passed = False
            
            if text_height > available_height:
                result.issues.append({
                    'type': IssueType.TEXT_OVERFLOW.value,
                    'severity': 'high',
                    'details': {
                        'text_height': text_height,
                        'available_height': available_height,
                        'overflow': int(text_height - available_height)
                    }
                })
                result.passed = False
            
            # Draw text with proper handling
            if element.allow_wrap:
                self._draw_wrapped_text(
                    draw, text, font, element, language_code, result
                )
            else:
                self._draw_single_line_text(
                    draw, text, font, element, language_code, result
                )
            
            # Check for additional issues
            for issue_type, detector in self.issue_detectors.items():
                issue = detector(img, element, text, language_code, font)
                if issue:
                    result.issues.append(issue)
                    result.passed = False
            
            # Calculate space utilization
            result.utilization_percentage = (
                (text_width * text_height) / 
                (available_width * available_height) * 100
            )
            
            # Convert image to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            result.screenshot = img_buffer.getvalue()
            result.screenshot_width = img.width
            result.screenshot_height = img.height
            
        except Exception as e:
            logger.error(f"Error testing UI element {element.element_id}: {e}")
            result.passed = False
            result.issues.append({
                'type': 'error',
                'severity': 'critical',
                'message': str(e)
            })
        
        return result
    
    async def test_batch(
        self,
        elements: List[UIElement],
        texts: Dict[str, str],
        language_code: str,
        parallel: bool = True
    ) -> List[SnapshotResult]:
        """Test multiple UI elements."""
        if parallel:
            tasks = []
            for element in elements:
                text = texts.get(element.localization_key, f"[{element.localization_key}]")
                task = self.test_element(element, text, language_code)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
        else:
            results = []
            for element in elements:
                text = texts.get(element.localization_key, f"[{element.localization_key}]")
                result = await self.test_element(element, text, language_code)
                results.append(result)
            return results
    
    def _get_font(self, language_code: str, font_family: str, size: int):
        """Get appropriate font for language."""
        # Cache key
        cache_key = f"{language_code}:{font_family}:{size}"
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # Get font config
        font_config = self.font_configs.get(
            language_code, 
            self.font_configs['en-US']
        )
        
        # Try to load font
        try:
            if font_family == "default":
                font_path = font_config.font_path
            else:
                # Custom font
                font_path = f"assets/fonts/{font_family}"
            
            # For this example, use default PIL font
            # In production, would load actual TTF/OTF files
            font = ImageFont.load_default()
            
        except Exception as e:
            logger.warning(f"Failed to load font {font_path}: {e}")
            font = ImageFont.load_default()
        
        self.font_cache[cache_key] = font
        return font
    
    def _get_text_bbox(self, draw: ImageDraw.Draw, text: str, font) -> Tuple[int, int, int, int]:
        """Get bounding box for text."""
        # PIL's textbbox method
        try:
            return draw.textbbox((0, 0), text, font=font)
        except AttributeError:
            # Fallback for older PIL versions
            width, height = draw.textsize(text, font=font)
            return (0, 0, width, height)
    
    def _draw_wrapped_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font,
        element: UIElement,
        language_code: str,
        result: SnapshotResult
    ):
        """Draw text with word wrapping."""
        font_config = self.font_configs.get(language_code, self.font_configs['en-US'])
        
        # Simple word wrapping
        words = text.split()
        lines = []
        current_line = []
        
        available_width = element.width - (2 * element.padding)
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = self._get_text_bbox(draw, test_line, font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= available_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word too long, truncate
                    lines.append(word)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Check max lines
        if element.max_lines and len(lines) > element.max_lines:
            lines = lines[:element.max_lines]
            lines[-1] = lines[-1][:-3] + '...'  # Add ellipsis
            result.issues.append({
                'type': IssueType.TRUNCATION.value,
                'severity': 'medium',
                'details': {
                    'total_lines': len(lines),
                    'max_lines': element.max_lines
                }
            })
        
        # Draw lines
        y_offset = element.padding
        line_height = element.font_size * font_config.line_height_multiplier
        
        for line in lines:
            x_offset = self._calculate_x_offset(
                draw, line, font, element, available_width
            )
            
            draw.text(
                (x_offset, y_offset),
                line,
                font=font,
                fill=element.text_color
            )
            
            y_offset += line_height
    
    def _draw_single_line_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font,
        element: UIElement,
        language_code: str,
        result: SnapshotResult
    ):
        """Draw single line text with optional truncation."""
        available_width = element.width - (2 * element.padding)
        
        # Check if text fits
        bbox = self._get_text_bbox(draw, text, font)
        text_width = bbox[2] - bbox[0]
        
        display_text = text
        if text_width > available_width:
            # Truncate with ellipsis
            display_text = self._truncate_text(
                draw, text, font, available_width
            )
            result.issues.append({
                'type': IssueType.TRUNCATION.value,
                'severity': 'medium',
                'details': {
                    'original_length': len(text),
                    'truncated_length': len(display_text)
                }
            })
        
        # Calculate position
        x_offset = self._calculate_x_offset(
            draw, display_text, font, element, available_width
        )
        y_offset = element.padding
        
        # Draw text
        draw.text(
            (x_offset, y_offset),
            display_text,
            font=font,
            fill=element.text_color
        )
    
    def _calculate_x_offset(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font,
        element: UIElement,
        available_width: int
    ) -> int:
        """Calculate X offset based on alignment."""
        if element.alignment == 'left':
            return element.padding
        
        bbox = self._get_text_bbox(draw, text, font)
        text_width = bbox[2] - bbox[0]
        
        if element.alignment == 'center':
            return element.padding + (available_width - text_width) // 2
        elif element.alignment == 'right':
            return element.padding + available_width - text_width
        
        return element.padding
    
    def _truncate_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font,
        max_width: int
    ) -> str:
        """Truncate text to fit within max width."""
        ellipsis = '...'
        ellipsis_bbox = self._get_text_bbox(draw, ellipsis, font)
        ellipsis_width = ellipsis_bbox[2] - ellipsis_bbox[0]
        
        available_width = max_width - ellipsis_width
        
        # Binary search for the right length
        left, right = 0, len(text)
        result = ""
        
        while left <= right:
            mid = (left + right) // 2
            test_text = text[:mid]
            bbox = self._get_text_bbox(draw, test_text, font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= available_width:
                result = test_text
                left = mid + 1
            else:
                right = mid - 1
        
        return result + ellipsis if result != text else text
    
    def _detect_text_overflow(
        self,
        img: Image.Image,
        element: UIElement,
        text: str,
        language_code: str,
        font
    ) -> Optional[Dict[str, Any]]:
        """Detect text overflow issues."""
        # Already handled in main flow
        return None
    
    def _detect_truncation(
        self,
        img: Image.Image,
        element: UIElement,
        text: str,
        language_code: str,
        font
    ) -> Optional[Dict[str, Any]]:
        """Detect text truncation issues."""
        # Already handled in main flow
        return None
    
    def _detect_font_missing(
        self,
        img: Image.Image,
        element: UIElement,
        text: str,
        language_code: str,
        font
    ) -> Optional[Dict[str, Any]]:
        """Detect missing font characters."""
        # Check for replacement characters (�)
        if '�' in text or '\ufffd' in text:
            return {
                'type': IssueType.FONT_MISSING.value,
                'severity': 'critical',
                'details': {
                    'message': 'Replacement characters found in rendered text'
                }
            }
        
        # Check for boxes or missing glyphs
        # This would require more sophisticated image analysis
        # For now, return None
        return None
    
    def _detect_poor_contrast(
        self,
        img: Image.Image,
        element: UIElement,
        text: str,
        language_code: str,
        font
    ) -> Optional[Dict[str, Any]]:
        """Detect poor text contrast."""
        if not element.background_color:
            return None
        
        # Simple contrast calculation
        text_color = self._parse_color(element.text_color)
        bg_color = self._parse_color(element.background_color)
        
        contrast_ratio = self._calculate_contrast_ratio(text_color, bg_color)
        
        # WCAG AA standard: 4.5:1 for normal text
        if contrast_ratio < 4.5:
            return {
                'type': IssueType.CONTRAST_POOR.value,
                'severity': 'high',
                'details': {
                    'contrast_ratio': contrast_ratio,
                    'required_ratio': 4.5,
                    'text_color': element.text_color,
                    'background_color': element.background_color
                }
            }
        
        return None
    
    def _detect_character_corruption(
        self,
        img: Image.Image,
        element: UIElement,
        text: str,
        language_code: str,
        font
    ) -> Optional[Dict[str, Any]]:
        """Detect corrupted characters."""
        # Check for common corruption patterns
        corruption_patterns = [
            '???',  # Multiple question marks
            '□□□',  # Boxes
            '...',  # Unintended ellipsis
        ]
        
        for pattern in corruption_patterns:
            if pattern in text and pattern not in element.localization_key:
                return {
                    'type': IssueType.CHARACTER_CORRUPTION.value,
                    'severity': 'high',
                    'details': {
                        'pattern_found': pattern,
                        'message': 'Potential character encoding issue'
                    }
                }
        
        return None
    
    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """Parse color string to RGB tuple."""
        if color_str.startswith('#'):
            # Hex color
            color_str = color_str[1:]
            if len(color_str) == 3:
                # Short form
                color_str = ''.join([c*2 for c in color_str])
            
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return (r, g, b)
        
        # Default to black
        return (0, 0, 0)
    
    def _calculate_contrast_ratio(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int]
    ) -> float:
        """Calculate WCAG contrast ratio between two colors."""
        def relative_luminance(color):
            r, g, b = [c/255.0 for c in color]
            
            # Apply gamma correction
            r = r/12.92 if r <= 0.03928 else ((r + 0.055)/1.055) ** 2.4
            g = g/12.92 if g <= 0.03928 else ((g + 0.055)/1.055) ** 2.4
            b = b/12.92 if b <= 0.03928 else ((b + 0.055)/1.055) ** 2.4
            
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = relative_luminance(color1)
        l2 = relative_luminance(color2)
        
        # Ensure l1 is the lighter color
        if l1 < l2:
            l1, l2 = l2, l1
        
        return (l1 + 0.05) / (l2 + 0.05)
    
    async def generate_report(
        self,
        results: List[SnapshotResult],
        output_format: str = 'html'
    ) -> str:
        """Generate a report from snapshot results."""
        if output_format == 'html':
            return self._generate_html_report(results)
        elif output_format == 'json':
            return self._generate_json_report(results)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_html_report(self, results: List[SnapshotResult]) -> str:
        """Generate HTML report with screenshots."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>UI Snapshot Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .element { margin: 20px 0; border: 1px solid #ddd; padding: 15px; }
        .passed { border-left: 5px solid #4CAF50; }
        .failed { border-left: 5px solid #f44336; }
        .screenshot { max-width: 100%; border: 1px solid #ddd; }
        .issue { background: #ffebee; padding: 10px; margin: 10px 0; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .metric { background: #e3f2fd; padding: 10px; }
    </style>
</head>
<body>
    <h1>UI Snapshot Test Report</h1>
"""
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        
        html += f"""
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Elements Tested: {total}</p>
        <p>Passed: {passed}</p>
        <p>Failed: {failed}</p>
        <p>Success Rate: {passed/total*100:.1f}%</p>
    </div>
"""
        
        # Individual results
        for result in results:
            status_class = 'passed' if result.passed else 'failed'
            html += f"""
    <div class="element {status_class}">
        <h3>{result.element_id} ({result.language_code})</h3>
        <p><strong>Text:</strong> {result.text}</p>
"""
            
            # Metrics
            html += """
        <div class="metrics">
"""
            html += f"""
            <div class="metric">Text Width: {result.text_width:.0f}px</div>
            <div class="metric">Text Height: {result.text_height:.0f}px</div>
            <div class="metric">Overflow: {result.overflow_pixels}px</div>
            <div class="metric">Utilization: {result.utilization_percentage:.1f}%</div>
"""
            html += """
        </div>
"""
            
            # Issues
            if result.issues:
                html += """
        <h4>Issues Found:</h4>
"""
                for issue in result.issues:
                    html += f"""
        <div class="issue">
            <strong>{issue.get('type', 'Unknown')}:</strong> 
            {issue.get('severity', 'Unknown')} severity<br>
            {json.dumps(issue.get('details', {}), indent=2)}
        </div>
"""
            
            # Screenshot
            if result.screenshot:
                screenshot_b64 = base64.b64encode(result.screenshot).decode()
                html += f"""
        <h4>Screenshot:</h4>
        <img class="screenshot" src="data:image/png;base64,{screenshot_b64}" 
             alt="Screenshot of {result.element_id}">
"""
            
            html += """
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _generate_json_report(self, results: List[SnapshotResult]) -> str:
        """Generate JSON report."""
        report_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_elements': len(results),
                'passed': sum(1 for r in results if r.passed),
                'failed': sum(1 for r in results if not r.passed)
            },
            'results': []
        }
        
        for result in results:
            result_data = {
                'element_id': result.element_id,
                'language_code': result.language_code,
                'text': result.text,
                'passed': result.passed,
                'metrics': {
                    'text_width': result.text_width,
                    'text_height': result.text_height,
                    'overflow_pixels': result.overflow_pixels,
                    'utilization_percentage': result.utilization_percentage
                },
                'issues': result.issues,
                'tested_at': result.tested_at.isoformat()
            }
            
            # Include screenshot as base64 if requested
            if result.screenshot:
                result_data['screenshot'] = base64.b64encode(result.screenshot).decode()
            
            report_data['results'].append(result_data)
        
        return json.dumps(report_data, indent=2)
