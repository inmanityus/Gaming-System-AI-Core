"""
Localization service implementation.
Provides APIs for string lookup, bulk operations, and validation.
"""
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import json
import re
from collections import defaultdict
import asyncpg
from babel import Locale
from langdetect import detect_langs
import chardet

from .repository import LocalizationRepository

logger = logging.getLogger(__name__)


class LocalizationService:
    """
    Core localization service providing string lookup, validation,
    and management functionality.
    """
    
    def __init__(self, repository: LocalizationRepository):
        self.repository = repository
        self._cache = {}  # Simple in-memory cache
        self._supported_languages_cache = None
    
    async def get_string(self, key: str, language_code: str, 
                        context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a localized string with optional context for interpolation.
        
        Args:
            key: Localization key
            language_code: Target language code
            context: Optional context dict for placeholder replacement
            
        Returns:
            Localized string with placeholders replaced
        """
        # Check cache first
        cache_key = f"{language_code}:{key}"
        if cache_key in self._cache:
            entry = self._cache[cache_key]
        else:
            # Get from database
            entry = await self.repository.get_string(key, language_code)
            if entry:
                self._cache[cache_key] = entry
        
        if not entry:
            # Log missing translation
            logger.warning(f"Missing translation: key={key}, language={language_code}")
            return f"[{key}]"  # Return key as placeholder
        
        text = entry['text']
        
        # Handle pluralization if context includes count
        if context and 'count' in context and entry.get('plural_forms'):
            text = self._apply_plural_form(text, entry['plural_forms'], 
                                          context['count'], language_code)
        
        # Handle gendering if context includes gender
        if context and 'gender' in context and entry.get('gender_forms'):
            text = self._apply_gender_form(text, entry['gender_forms'], 
                                          context['gender'])
        
        # Replace placeholders
        if context:
            text = self._interpolate_text(text, context)
        
        return text
    
    async def get_strings_bulk(self, keys: List[str], language_code: str,
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Get multiple localized strings in one call.
        More efficient than multiple individual calls.
        
        Returns dict mapping keys to localized strings.
        """
        # Separate cached and uncached keys
        result = {}
        uncached_keys = []
        
        for key in keys:
            cache_key = f"{language_code}:{key}"
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                result[key] = entry['text']
            else:
                uncached_keys.append(key)
        
        # Fetch uncached keys
        if uncached_keys:
            entries = await self.repository.get_strings_bulk(uncached_keys, language_code)
            
            for key, entry in entries.items():
                cache_key = f"{language_code}:{key}"
                self._cache[cache_key] = entry
                result[key] = entry['text']
            
            # Add placeholders for missing keys
            for key in uncached_keys:
                if key not in result:
                    result[key] = f"[{key}]"
        
        # Apply context to all strings
        if context:
            for key in result:
                cache_key = f"{language_code}:{key}"
                if cache_key in self._cache:
                    entry = self._cache[cache_key]
                    text = result[key]
                    
                    # Apply plural/gender forms if available
                    if 'count' in context and entry.get('plural_forms'):
                        text = self._apply_plural_form(text, entry['plural_forms'],
                                                      context['count'], language_code)
                    
                    if 'gender' in context and entry.get('gender_forms'):
                        text = self._apply_gender_form(text, entry['gender_forms'],
                                                      context['gender'])
                    
                    result[key] = self._interpolate_text(text, context)
        
        return result
    
    async def validate_translation(self, key: str, text: str, 
                                 source_language: str, target_language: str) -> Dict[str, Any]:
        """
        Validate a translation against the source text.
        
        Returns validation results including:
        - placeholder_valid: bool
        - length_ratio: float (target/source length)
        - detected_language: str
        - warnings: List[str]
        """
        # Get source text
        source_entry = await self.repository.get_string(key, source_language)
        if not source_entry:
            return {
                'valid': False,
                'error': 'Source text not found'
            }
        
        source_text = source_entry['text']
        warnings = []
        
        # Validate placeholders
        placeholder_valid = self._validate_placeholders(text, source_text)
        if not placeholder_valid:
            warnings.append('Placeholder mismatch detected')
        
        # Check length ratio
        length_ratio = len(text) / len(source_text) if source_text else 0
        if length_ratio > 2.0:
            warnings.append(f'Translation is {length_ratio:.1f}x longer than source')
        elif length_ratio < 0.5:
            warnings.append(f'Translation is {length_ratio:.1f}x shorter than source')
        
        # Detect language
        try:
            detected_langs = detect_langs(text)
            detected_language = detected_langs[0].lang if detected_langs else 'unknown'
            
            # Check if detected language matches target
            if detected_language != target_language[:2]:  # Compare just language part
                warnings.append(f'Detected language {detected_language} does not match target')
        except:
            detected_language = 'unknown'
        
        # Check for common issues
        if self._contains_untranslated_placeholders(text):
            warnings.append('Contains untranslated placeholder text')
        
        if self._contains_mixed_scripts(text, target_language):
            warnings.append('Contains mixed writing scripts')
        
        return {
            'valid': len(warnings) == 0,
            'placeholder_valid': placeholder_valid,
            'length_ratio': length_ratio,
            'detected_language': detected_language,
            'warnings': warnings
        }
    
    async def export_for_translation(self, source_language: str, target_language: str,
                                    categories: Optional[List[str]] = None,
                                    format: str = 'json') -> Any:
        """
        Export strings for translation in various formats.
        
        Supported formats: json, csv, xliff
        """
        entries = await self.repository.export_for_translation(
            source_language, target_language, categories
        )
        
        if format == 'json':
            return self._export_as_json(entries, source_language, target_language)
        elif format == 'csv':
            return self._export_as_csv(entries)
        elif format == 'xliff':
            return self._export_as_xliff(entries, source_language, target_language)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def import_translations(self, data: Any, language_code: str, 
                                format: str = 'json',
                                validate: bool = True) -> Dict[str, Any]:
        """
        Import translations from various formats.
        
        Returns import statistics and any validation errors.
        """
        # Parse data based on format
        if format == 'json':
            entries = self._parse_json_import(data)
        elif format == 'csv':
            entries = self._parse_csv_import(data)
        elif format == 'xliff':
            entries = self._parse_xliff_import(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        # Validate entries if requested
        validation_errors = []
        if validate:
            for entry in entries:
                if 'source_text' in entry:
                    validation = await self.validate_translation(
                        entry['key'], entry['text'],
                        'en-US', language_code
                    )
                    if not validation['valid']:
                        validation_errors.append({
                            'key': entry['key'],
                            'warnings': validation['warnings']
                        })
        
        # Import entries
        import_result = await self.repository.bulk_import(
            entries, language_code, replace_existing=True
        )
        
        import_result['validation_errors'] = validation_errors
        
        return import_result
    
    async def get_coverage_report(self, build_id: str, 
                                language_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive coverage report for specified languages.
        """
        if not language_codes:
            # Get all enabled languages
            languages = await self.repository.get_supported_languages()
            language_codes = [lang['language_code'] for lang in languages]
        
        coverage_data = {}
        for language_code in language_codes:
            coverage_data[language_code] = await self.repository.calculate_coverage(
                build_id, language_code
            )
        
        # Calculate overall metrics
        total_strings = max(
            data['total_strings'] for data in coverage_data.values()
        ) if coverage_data else 0
        
        overall_coverage = {
            'build_id': build_id,
            'total_strings': total_strings,
            'languages': {}
        }
        
        for language_code, data in coverage_data.items():
            overall_coverage['languages'][language_code] = {
                'coverage_percentage': data['coverage_percentage'],
                'approval_percentage': data['approval_percentage'],
                'translated_strings': data['translated_strings'],
                'approved_strings': data['approved_strings']
            }
        
        return overall_coverage
    
    async def clear_cache(self, language_code: Optional[str] = None):
        """Clear the in-memory cache."""
        if language_code:
            # Clear only entries for specific language
            keys_to_remove = [k for k in self._cache.keys() 
                            if k.startswith(f"{language_code}:")]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear entire cache
            self._cache.clear()
        
        # Also clear supported languages cache
        self._supported_languages_cache = None
    
    # Private helper methods
    
    def _apply_plural_form(self, text: str, plural_forms: Dict[str, str], 
                          count: int, language_code: str) -> str:
        """Apply appropriate plural form based on count and language rules."""
        # Get plural rule for language
        try:
            locale = Locale.parse(language_code.replace('-', '_'))
            plural_form = locale.plural_form(count)
        except:
            # Default to simple one/other rule
            plural_form = 'one' if count == 1 else 'other'
        
        # Use the appropriate form or fall back to base text
        if str(plural_form) in plural_forms:
            return plural_forms[str(plural_form)]
        elif 'other' in plural_forms:
            return plural_forms['other']
        else:
            return text
    
    def _apply_gender_form(self, text: str, gender_forms: Dict[str, str], 
                          gender: str) -> str:
        """Apply appropriate gender form."""
        if gender in gender_forms:
            return gender_forms[gender]
        elif 'neutral' in gender_forms:
            return gender_forms['neutral']
        else:
            return text
    
    def _interpolate_text(self, text: str, context: Dict[str, Any]) -> str:
        """Replace placeholders in text with context values."""
        # Handle different placeholder formats
        # Python format: {name}
        for key, value in context.items():
            text = text.replace(f"{{{key}}}", str(value))
        
        # Printf format: %s, %d, %1$s
        # Simple implementation - production would need more robust handling
        if '%' in text:
            # Convert context values to list for positional replacement
            values = list(context.values())
            try:
                text = text % tuple(values)
            except:
                pass  # Ignore formatting errors
        
        return text
    
    def _validate_placeholders(self, text: str, reference_text: str) -> bool:
        """Check if placeholders match between texts."""
        # Extract placeholders from both texts
        text_placeholders = self._extract_placeholders(text)
        ref_placeholders = self._extract_placeholders(reference_text)
        
        # Compare sets
        return text_placeholders == ref_placeholders
    
    def _extract_placeholders(self, text: str) -> Set[str]:
        """Extract all placeholders from text."""
        placeholders = set()
        
        # Python format: {name}
        placeholders.update(re.findall(r'\{([^}]+)\}', text))
        
        # Printf format: %s, %d, %1$s
        placeholders.update(re.findall(r'%\d*\$?[sdif]', text))
        
        # Custom format: {{name}}
        placeholders.update(re.findall(r'\{\{([^}]+)\}\}', text))
        
        return placeholders
    
    def _contains_untranslated_placeholders(self, text: str) -> bool:
        """Check for common untranslated placeholder patterns."""
        patterns = [
            r'\[[\w.]+\]',  # [key.name]
            r'TODO:',
            r'FIXME:',
            r'XXX:',
            r'<untranslated>',
            r'{untranslated}'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_mixed_scripts(self, text: str, language_code: str) -> bool:
        """Check if text contains mixed writing scripts."""
        # This is a simplified check - production would need more sophisticated analysis
        if language_code.startswith('ja'):
            # Japanese can legitimately mix scripts
            return False
        elif language_code.startswith('zh'):
            # Check for mixed simplified/traditional or Latin
            has_latin = bool(re.search(r'[a-zA-Z]', text))
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
            return has_latin and has_chinese and len(text) > 10
        elif language_code.startswith('ar'):
            # Check for mixed Arabic and Latin
            has_latin = bool(re.search(r'[a-zA-Z]', text))
            has_arabic = bool(re.search(r'[\u0600-\u06ff]', text))
            return has_latin and has_arabic
        
        return False
    
    def _export_as_json(self, entries: List[Dict[str, Any]], 
                       source_language: str, target_language: str) -> Dict[str, Any]:
        """Export entries as JSON format."""
        export_data = {
            'source_language': source_language,
            'target_language': target_language,
            'export_date': datetime.utcnow().isoformat(),
            'entries': []
        }
        
        for entry in entries:
            export_entry = {
                'key': entry['key'],
                'source_text': entry['source_text'],
                'category': entry['category']
            }
            
            if entry.get('context'):
                export_entry['context'] = entry['context']
            
            if entry.get('existing_translation'):
                export_entry['existing_translation'] = entry['existing_translation']
            
            if entry.get('source_plural_forms'):
                export_entry['plural_forms'] = entry['source_plural_forms']
            
            if entry.get('source_gender_forms'):
                export_entry['gender_forms'] = entry['source_gender_forms']
            
            export_data['entries'].append(export_entry)
        
        return export_data
    
    def _export_as_csv(self, entries: List[Dict[str, Any]]) -> str:
        """Export entries as CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['key', 'category', 'source_text', 'existing_translation', 
                        'context', 'tags'])
        
        # Data rows
        for entry in entries:
            writer.writerow([
                entry['key'],
                entry['category'],
                entry['source_text'],
                entry.get('existing_translation', ''),
                entry.get('context', ''),
                ','.join(entry.get('tags', []))
            ])
        
        return output.getvalue()
    
    def _export_as_xliff(self, entries: List[Dict[str, Any]],
                        source_language: str, target_language: str) -> str:
        """Export entries as XLIFF 2.1 format."""
        # Simplified XLIFF export - production would use proper XML library
        xliff = f'''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="2.1" xmlns="urn:oasis:names:tc:xliff:document:2.1" 
       srcLang="{source_language}" trgLang="{target_language}">
  <file id="1">'''
        
        for i, entry in enumerate(entries):
            unit_id = f"unit_{i+1}"
            xliff += f'''
    <unit id="{unit_id}" name="{entry['key']}">
      <segment>
        <source>{self._escape_xml(entry['source_text'])}</source>'''
            
            if entry.get('existing_translation'):
                xliff += f'''
        <target>{self._escape_xml(entry['existing_translation'])}</target>'''
            else:
                xliff += '''
        <target></target>'''
            
            xliff += '''
      </segment>'''
            
            if entry.get('context'):
                xliff += f'''
      <notes>
        <note category="context">{self._escape_xml(entry['context'])}</note>
      </notes>'''
            
            xliff += '''
    </unit>'''
        
        xliff += '''
  </file>
</xliff>'''
        
        return xliff
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))
    
    def _parse_json_import(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse JSON import data."""
        entries = []
        
        for item in data.get('entries', []):
            entry = {
                'key': item['key'],
                'text': item.get('translation', item.get('text', '')),
                'category': item.get('category', 'system')
            }
            
            if 'context' in item:
                entry['context'] = item['context']
            
            if 'tags' in item:
                entry['tags'] = item['tags']
            
            if 'plural_forms' in item:
                entry['plural_forms'] = item['plural_forms']
            
            if 'gender_forms' in item:
                entry['gender_forms'] = item['gender_forms']
            
            if 'source_text' in item:
                entry['source_text'] = item['source_text']
            
            entries.append(entry)
        
        return entries
    
    def _parse_csv_import(self, data: str) -> List[Dict[str, Any]]:
        """Parse CSV import data."""
        import csv
        import io
        
        entries = []
        reader = csv.DictReader(io.StringIO(data))
        
        for row in reader:
            entry = {
                'key': row['key'],
                'text': row.get('translation', row.get('text', '')),
                'category': row.get('category', 'system')
            }
            
            if row.get('context'):
                entry['context'] = row['context']
            
            if row.get('tags'):
                entry['tags'] = row['tags'].split(',')
            
            entries.append(entry)
        
        return entries
    
    def _parse_xliff_import(self, data: str) -> List[Dict[str, Any]]:
        """Parse XLIFF import data."""
        # Simplified XLIFF parsing - production would use proper XML parser
        import xml.etree.ElementTree as ET
        
        entries = []
        root = ET.fromstring(data)
        
        # Handle XLIFF namespace
        ns = {'xliff': 'urn:oasis:names:tc:xliff:document:2.1'}
        
        for unit in root.findall('.//xliff:unit', ns):
            key = unit.get('name')
            segment = unit.find('xliff:segment', ns)
            
            if segment is not None:
                source = segment.find('xliff:source', ns)
                target = segment.find('xliff:target', ns)
                
                entry = {
                    'key': key,
                    'text': target.text if target is not None and target.text else '',
                    'category': 'system'
                }
                
                if source is not None and source.text:
                    entry['source_text'] = source.text
                
                # Look for notes
                notes = unit.find('xliff:notes', ns)
                if notes is not None:
                    context_note = notes.find('xliff:note[@category="context"]', ns)
                    if context_note is not None and context_note.text:
                        entry['context'] = context_note.text
                
                entries.append(entry)
        
        return entries
