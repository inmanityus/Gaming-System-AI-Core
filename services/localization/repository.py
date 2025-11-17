"""
Repository layer for localization data access.
Implements database operations for localization entries, preferences, and metadata.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import asyncpg
import json
from babel import Locale
from collections import defaultdict

logger = logging.getLogger(__name__)


class LocalizationRepository:
    """
    Repository for localization data access.
    All operations are async and use connection pooling.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.pool = postgres_pool
    
    async def get_string(self, key: str, language_code: str, 
                        fallback_language: str = 'en-US') -> Optional[Dict[str, Any]]:
        """
        Get a localized string by key and language.
        Falls back to specified language if not found.
        
        Returns dict with text and metadata, or None if not found.
        """
        async with self.pool.acquire() as conn:
            # Try requested language first
            row = await conn.fetchrow(
                """
                SELECT entry_id, key, language_code, text, category, 
                       plural_forms, gender_forms, tags, status, version
                FROM localization_entries
                WHERE key = $1 AND language_code = $2 AND status = 'approved'
                """,
                key, language_code
            )
            
            if row:
                return dict(row)
            
            # Try fallback language if different
            if language_code != fallback_language:
                row = await conn.fetchrow(
                    """
                    SELECT entry_id, key, language_code, text, category,
                           plural_forms, gender_forms, tags, status, version
                    FROM localization_entries
                    WHERE key = $1 AND language_code = $2 AND status = 'approved'
                    """,
                    key, fallback_language
                )
                
                if row:
                    result = dict(row)
                    result['is_fallback'] = True
                    return result
            
            return None
    
    async def get_strings_bulk(self, keys: List[str], language_code: str,
                              fallback_language: str = 'en-US') -> Dict[str, Dict[str, Any]]:
        """
        Get multiple localized strings in a single query.
        Returns dict mapping keys to localization data.
        """
        async with self.pool.acquire() as conn:
            # Get all requested strings
            rows = await conn.fetch(
                """
                SELECT entry_id, key, language_code, text, category,
                       plural_forms, gender_forms, tags, status, version
                FROM localization_entries
                WHERE key = ANY($1::text[]) 
                  AND language_code = $2 
                  AND status = 'approved'
                """,
                keys, language_code
            )
            
            results = {row['key']: dict(row) for row in rows}
            
            # Find missing keys
            missing_keys = [k for k in keys if k not in results]
            
            # Get fallbacks for missing keys
            if missing_keys and language_code != fallback_language:
                fallback_rows = await conn.fetch(
                    """
                    SELECT entry_id, key, language_code, text, category,
                           plural_forms, gender_forms, tags, status, version
                    FROM localization_entries
                    WHERE key = ANY($1::text[])
                      AND language_code = $2
                      AND status = 'approved'
                    """,
                    missing_keys, fallback_language
                )
                
                for row in fallback_rows:
                    result = dict(row)
                    result['is_fallback'] = True
                    results[row['key']] = result
            
            return results
    
    async def get_strings_by_category(self, category: str, language_code: str,
                                     include_unapproved: bool = False) -> List[Dict[str, Any]]:
        """Get all strings in a category for a language."""
        async with self.pool.acquire() as conn:
            status_clause = "" if include_unapproved else "AND status = 'approved'"
            
            rows = await conn.fetch(
                f"""
                SELECT entry_id, key, language_code, text, category,
                       plural_forms, gender_forms, tags, status, version,
                       context, description
                FROM localization_entries
                WHERE category = $1 AND language_code = $2 {status_clause}
                ORDER BY key
                """,
                category, language_code
            )
            
            return [dict(row) for row in rows]
    
    async def create_or_update_entry(self, key: str, language_code: str,
                                    text: str, category: str, 
                                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create or update a localization entry.
        Returns the entry_id.
        """
        metadata = metadata or {}
        
        async with self.pool.acquire() as conn:
            # Check if entry exists
            existing = await conn.fetchrow(
                "SELECT entry_id, version FROM localization_entries WHERE key = $1 AND language_code = $2",
                key, language_code
            )
            
            if existing:
                # Update existing entry
                entry_id = await conn.fetchval(
                    """
                    UPDATE localization_entries
                    SET text = $3,
                        category = $4,
                        context = $5,
                        description = $6,
                        tags = $7,
                        plural_forms = $8,
                        gender_forms = $9,
                        version = version + 1,
                        status = 'draft',
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = $10
                    WHERE key = $1 AND language_code = $2
                    RETURNING entry_id
                    """,
                    key, language_code, text, category,
                    metadata.get('context'),
                    metadata.get('description'),
                    metadata.get('tags', []),
                    json.dumps(metadata.get('plural_forms', {})),
                    json.dumps(metadata.get('gender_forms', {})),
                    metadata.get('updated_by')
                )
            else:
                # Create new entry
                entry_id = await conn.fetchval(
                    """
                    INSERT INTO localization_entries
                    (key, language_code, text, category, context, description,
                     tags, plural_forms, gender_forms, status, updated_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'draft', $10)
                    RETURNING entry_id
                    """,
                    key, language_code, text, category,
                    metadata.get('context'),
                    metadata.get('description'),
                    metadata.get('tags', []),
                    json.dumps(metadata.get('plural_forms', {})),
                    json.dumps(metadata.get('gender_forms', {})),
                    metadata.get('updated_by')
                )
            
            return str(entry_id)
    
    async def bulk_import(self, entries: List[Dict[str, Any]], 
                         language_code: str,
                         replace_existing: bool = False) -> Dict[str, int]:
        """
        Bulk import localization entries.
        Returns counts of created/updated/skipped entries.
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for entry in entries:
                    try:
                        key = entry.get('key')
                        if not key:
                            errors.append({'error': 'Missing key', 'entry': entry})
                            continue
                        
                        # Check if exists
                        existing = await conn.fetchval(
                            "SELECT entry_id FROM localization_entries WHERE key = $1 AND language_code = $2",
                            key, language_code
                        )
                        
                        if existing and not replace_existing:
                            skipped += 1
                            continue
                        
                        # Validate placeholders against source
                        if 'source_text' in entry and not await self._validate_placeholders(
                            entry.get('text', ''), 
                            entry.get('source_text', ''),
                            conn
                        ):
                            errors.append({
                                'error': 'Placeholder mismatch',
                                'key': key,
                                'text': entry.get('text'),
                                'source': entry.get('source_text')
                            })
                            continue
                        
                        if existing:
                            # Update
                            await conn.execute(
                                """
                                UPDATE localization_entries
                                SET text = $3,
                                    category = $4,
                                    context = $5,
                                    description = $6,
                                    tags = $7,
                                    plural_forms = $8,
                                    gender_forms = $9,
                                    version = version + 1,
                                    status = $10,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE key = $1 AND language_code = $2
                                """,
                                key, language_code,
                                entry.get('text', ''),
                                entry.get('category', 'system'),
                                entry.get('context'),
                                entry.get('description'),
                                entry.get('tags', []),
                                json.dumps(entry.get('plural_forms', {})),
                                json.dumps(entry.get('gender_forms', {})),
                                entry.get('status', 'draft')
                            )
                            updated += 1
                        else:
                            # Create
                            await conn.execute(
                                """
                                INSERT INTO localization_entries
                                (key, language_code, text, category, context, description,
                                 tags, plural_forms, gender_forms, status)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                                """,
                                key, language_code,
                                entry.get('text', ''),
                                entry.get('category', 'system'),
                                entry.get('context'),
                                entry.get('description'),
                                entry.get('tags', []),
                                json.dumps(entry.get('plural_forms', {})),
                                json.dumps(entry.get('gender_forms', {})),
                                entry.get('status', 'draft')
                            )
                            created += 1
                            
                    except Exception as e:
                        logger.error(f"Error importing entry {entry}: {e}")
                        errors.append({'error': str(e), 'entry': entry})
        
        return {
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'errors': errors
        }
    
    async def export_for_translation(self, source_language: str, target_language: str,
                                    categories: Optional[List[str]] = None,
                                    only_missing: bool = True) -> List[Dict[str, Any]]:
        """
        Export entries for translation.
        Returns list of entries with source text and any existing translations.
        """
        async with self.pool.acquire() as conn:
            category_clause = ""
            params = [source_language]
            
            if categories:
                category_clause = "AND s.category = ANY($2::text[])"
                params.append(categories)
            
            if only_missing:
                # Get source entries without translations
                query = f"""
                    SELECT s.key, s.text as source_text, s.category,
                           s.context, s.description, s.tags,
                           s.plural_forms as source_plural_forms,
                           s.gender_forms as source_gender_forms,
                           t.text as existing_translation,
                           t.status as translation_status
                    FROM localization_entries s
                    LEFT JOIN localization_entries t
                        ON s.key = t.key AND t.language_code = ${len(params) + 1}
                    WHERE s.language_code = $1
                      AND s.status = 'approved'
                      AND (t.entry_id IS NULL OR t.status != 'approved')
                      {category_clause}
                    ORDER BY s.category, s.key
                """
                params.append(target_language)
            else:
                # Get all source entries with their translations
                query = f"""
                    SELECT s.key, s.text as source_text, s.category,
                           s.context, s.description, s.tags,
                           s.plural_forms as source_plural_forms,
                           s.gender_forms as source_gender_forms,
                           t.text as existing_translation,
                           t.status as translation_status
                    FROM localization_entries s
                    LEFT JOIN localization_entries t
                        ON s.key = t.key AND t.language_code = ${len(params) + 1}
                    WHERE s.language_code = $1
                      AND s.status = 'approved'
                      {category_clause}
                    ORDER BY s.category, s.key
                """
                params.append(target_language)
            
            rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows]
    
    async def validate_translations(self, language_code: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate translations for completeness and correctness.
        Returns dict of issues by type.
        """
        issues = defaultdict(list)
        
        async with self.pool.acquire() as conn:
            # Check for missing translations
            missing = await conn.fetch(
                """
                SELECT s.key, s.category, s.text as source_text
                FROM localization_entries s
                LEFT JOIN localization_entries t
                    ON s.key = t.key AND t.language_code = $2
                WHERE s.language_code = 'en-US'
                  AND s.status = 'approved'
                  AND t.entry_id IS NULL
                ORDER BY s.category, s.key
                """,
                language_code
            )
            
            for row in missing:
                issues['missing_translation'].append(dict(row))
            
            # Check for placeholder mismatches
            mismatches = await conn.fetch(
                """
                SELECT t.key, t.text as translation, s.text as source_text
                FROM localization_entries t
                JOIN localization_entries s
                    ON t.key = s.key AND s.language_code = 'en-US'
                WHERE t.language_code = $1
                  AND NOT validate_localization_placeholders(t.text, s.text)
                """,
                language_code
            )
            
            for row in mismatches:
                issues['placeholder_mismatch'].append(dict(row))
            
            # Check for outdated translations
            outdated = await conn.fetch(
                """
                SELECT t.key, t.text as translation, t.version,
                       s.text as source_text, s.version as source_version
                FROM localization_entries t
                JOIN localization_entries s
                    ON t.key = s.key AND s.language_code = 'en-US'
                WHERE t.language_code = $1
                  AND t.version < s.version
                  AND t.status = 'approved'
                """,
                language_code
            )
            
            for row in outdated:
                issues['outdated_translation'].append(dict(row))
            
            return dict(issues)
    
    async def get_language_preferences(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get language preferences for a player."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT ui_language, subtitle_language, voice_language,
                       fallback_to_english, show_original_on_missing,
                       use_dyslexia_font, subtitle_size
                FROM language_preferences
                WHERE player_id = $1
                """,
                player_id
            )
            
            return dict(row) if row else None
    
    async def update_language_preferences(self, player_id: str, 
                                        preferences: Dict[str, Any]) -> None:
        """Update language preferences for a player."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO language_preferences
                (player_id, ui_language, subtitle_language, voice_language,
                 fallback_to_english, show_original_on_missing,
                 use_dyslexia_font, subtitle_size)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (player_id) DO UPDATE SET
                    ui_language = EXCLUDED.ui_language,
                    subtitle_language = EXCLUDED.subtitle_language,
                    voice_language = EXCLUDED.voice_language,
                    fallback_to_english = EXCLUDED.fallback_to_english,
                    show_original_on_missing = EXCLUDED.show_original_on_missing,
                    use_dyslexia_font = EXCLUDED.use_dyslexia_font,
                    subtitle_size = EXCLUDED.subtitle_size,
                    updated_at = CURRENT_TIMESTAMP
                """,
                player_id,
                preferences.get('ui_language', 'en-US'),
                preferences.get('subtitle_language'),
                preferences.get('voice_language'),
                preferences.get('fallback_to_english', True),
                preferences.get('show_original_on_missing', False),
                preferences.get('use_dyslexia_font', False),
                preferences.get('subtitle_size', 'medium')
            )
    
    async def calculate_coverage(self, build_id: str, language_code: str) -> Dict[str, Any]:
        """Calculate localization coverage metrics for a build."""
        async with self.pool.acquire() as conn:
            # Get counts by category
            coverage_data = await conn.fetch(
                """
                SELECT 
                    s.category,
                    COUNT(DISTINCT s.key) as total_keys,
                    COUNT(DISTINCT t.key) FILTER (WHERE t.text IS NOT NULL) as translated_keys,
                    COUNT(DISTINCT t.key) FILTER (WHERE t.status = 'review') as reviewed_keys,
                    COUNT(DISTINCT t.key) FILTER (WHERE t.status = 'approved') as approved_keys
                FROM localization_entries s
                LEFT JOIN localization_entries t
                    ON s.key = t.key AND t.language_code = $1
                WHERE s.language_code = 'en-US'
                  AND s.status = 'approved'
                GROUP BY s.category
                """,
                language_code
            )
            
            # Store coverage data
            async with conn.transaction():
                for row in coverage_data:
                    await conn.execute(
                        """
                        INSERT INTO localization_coverage
                        (build_id, language_code, category, total_keys,
                         translated_keys, reviewed_keys, approved_keys)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (build_id, language_code, category) DO UPDATE SET
                            total_keys = EXCLUDED.total_keys,
                            translated_keys = EXCLUDED.translated_keys,
                            reviewed_keys = EXCLUDED.reviewed_keys,
                            approved_keys = EXCLUDED.approved_keys,
                            calculated_at = CURRENT_TIMESTAMP
                        """,
                        build_id, language_code, row['category'],
                        row['total_keys'], row['translated_keys'],
                        row['reviewed_keys'], row['approved_keys']
                    )
            
            # Return summary
            total = sum(row['total_keys'] for row in coverage_data)
            translated = sum(row['translated_keys'] for row in coverage_data)
            approved = sum(row['approved_keys'] for row in coverage_data)
            
            return {
                'build_id': build_id,
                'language_code': language_code,
                'total_strings': total,
                'translated_strings': translated,
                'approved_strings': approved,
                'coverage_percentage': (translated / total * 100) if total > 0 else 0,
                'approval_percentage': (approved / total * 100) if total > 0 else 0,
                'by_category': [dict(row) for row in coverage_data]
            }
    
    async def get_supported_languages(self, tier: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of supported languages, optionally filtered by tier."""
        async with self.pool.acquire() as conn:
            if tier:
                rows = await conn.fetch(
                    """
                    SELECT language_code, language_name, native_name, tier,
                           ui_support, subtitle_support, voice_support,
                           text_direction, requires_special_font, font_family
                    FROM supported_languages
                    WHERE enabled = TRUE AND tier = $1
                    ORDER BY tier, language_code
                    """,
                    tier
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT language_code, language_name, native_name, tier,
                           ui_support, subtitle_support, voice_support,
                           text_direction, requires_special_font, font_family
                    FROM supported_languages
                    WHERE enabled = TRUE
                    ORDER BY tier, language_code
                    """
                )
            
            return [dict(row) for row in rows]
    
    async def _validate_placeholders(self, text: str, reference_text: str, 
                                    conn: asyncpg.Connection) -> bool:
        """Validate that placeholders match between translated and reference text."""
        result = await conn.fetchval(
            "SELECT validate_localization_placeholders($1, $2)",
            text, reference_text
        )
        return result
