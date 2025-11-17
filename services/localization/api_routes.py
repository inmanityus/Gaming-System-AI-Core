"""
API routes for localization service.
Implements REST and NATS endpoints for localization operations.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from pydantic import BaseModel, Field
import asyncpg

from .service import LocalizationService
from .repository import LocalizationRepository

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1/localization", tags=["localization"])


# Request/Response models
class LocalizedString(BaseModel):
    """Response model for localized string."""
    key: str
    text: str
    language_code: str
    is_fallback: bool = False
    version: int = 1


class StringLookupRequest(BaseModel):
    """Request for single string lookup."""
    key: str
    language_code: str
    context: Optional[Dict[str, Any]] = None


class BulkStringLookupRequest(BaseModel):
    """Request for bulk string lookup."""
    keys: List[str]
    language_code: str
    context: Optional[Dict[str, Any]] = None


class LocalizationEntry(BaseModel):
    """Model for creating/updating localization entries."""
    key: str
    text: str
    category: str = "system"
    context: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    plural_forms: Dict[str, str] = Field(default_factory=dict)
    gender_forms: Dict[str, str] = Field(default_factory=dict)


class TranslationValidationResult(BaseModel):
    """Result of translation validation."""
    valid: bool
    placeholder_valid: bool
    length_ratio: float
    detected_language: str
    warnings: List[str]


class LanguagePreferences(BaseModel):
    """Player language preferences."""
    ui_language: str = "en-US"
    subtitle_language: Optional[str] = None
    voice_language: Optional[str] = None
    fallback_to_english: bool = True
    show_original_on_missing: bool = False
    use_dyslexia_font: bool = False
    subtitle_size: str = "medium"


class ImportResult(BaseModel):
    """Result of import operation."""
    created: int
    updated: int
    skipped: int
    errors: List[Dict[str, Any]]
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)


# Service instance (will be injected)
localization_service: Optional[LocalizationService] = None


def initialize_routes(postgres_pool: asyncpg.Pool):
    """Initialize routes with database connection."""
    global localization_service
    repository = LocalizationRepository(postgres_pool)
    localization_service = LocalizationService(repository)


# String lookup endpoints

@router.post("/lookup", response_model=LocalizedString)
async def lookup_string(request: StringLookupRequest):
    """
    Look up a single localized string.
    
    Returns the localized text with optional context interpolation.
    Falls back to configured fallback language if not found.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    text = await localization_service.get_string(
        request.key, request.language_code, request.context
    )
    
    # Check if it's a fallback (returned in brackets)
    is_fallback = text.startswith('[') and text.endswith(']')
    
    return LocalizedString(
        key=request.key,
        text=text,
        language_code=request.language_code,
        is_fallback=is_fallback
    )


@router.post("/lookup/bulk", response_model=Dict[str, str])
async def lookup_strings_bulk(request: BulkStringLookupRequest):
    """
    Look up multiple localized strings in a single request.
    
    More efficient than multiple individual lookups.
    Returns a dictionary mapping keys to localized texts.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    return await localization_service.get_strings_bulk(
        request.keys, request.language_code, request.context
    )


@router.get("/strings/{category}/{language_code}")
async def get_strings_by_category(
    category: str,
    language_code: str,
    include_unapproved: bool = Query(False, description="Include draft/review strings")
):
    """
    Get all strings in a category for a specific language.
    
    Useful for loading all UI strings at once.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    strings = await localization_service.repository.get_strings_by_category(
        category, language_code, include_unapproved
    )
    
    return {
        "category": category,
        "language_code": language_code,
        "count": len(strings),
        "strings": strings
    }


# Content management endpoints

@router.post("/entries/{language_code}")
async def create_or_update_entry(
    language_code: str,
    entry: LocalizationEntry
):
    """
    Create or update a localization entry.
    
    If the key already exists, it will be updated and version incremented.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    entry_id = await localization_service.repository.create_or_update_entry(
        entry.key, language_code, entry.text, entry.category,
        {
            'context': entry.context,
            'description': entry.description,
            'tags': entry.tags,
            'plural_forms': entry.plural_forms,
            'gender_forms': entry.gender_forms,
            'updated_by': 'api'  # In production, use actual user
        }
    )
    
    return {
        "entry_id": entry_id,
        "key": entry.key,
        "language_code": language_code,
        "status": "created" if entry_id else "updated"
    }


@router.post("/import/{language_code}")
async def import_translations(
    language_code: str,
    file: UploadFile = File(...),
    format: str = Query("json", description="Import format: json, csv, xliff"),
    validate: bool = Query(True, description="Validate translations before import")
) -> ImportResult:
    """
    Import translations from a file.
    
    Supports JSON, CSV, and XLIFF formats.
    Optionally validates translations before importing.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    # Read file content
    content = await file.read()
    
    try:
        if format == "json":
            data = json.loads(content)
        elif format in ["csv", "xliff"]:
            data = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        result = await localization_service.import_translations(
            data, language_code, format, validate
        )
        
        return ImportResult(**result)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{source_language}/{target_language}")
async def export_for_translation(
    source_language: str,
    target_language: str,
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    format: str = Query("json", description="Export format: json, csv, xliff"),
    only_missing: bool = Query(True, description="Export only missing translations")
):
    """
    Export strings for translation.
    
    Returns strings in the requested format with source text
    and any existing translations.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    category_list = categories.split(',') if categories else None
    
    try:
        export_data = await localization_service.export_for_translation(
            source_language, target_language, category_list, format
        )
        
        if format == "json":
            return export_data
        else:
            # Return as file download for CSV/XLIFF
            from fastapi.responses import Response
            
            if format == "csv":
                return Response(
                    content=export_data,
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=translations_{target_language}.csv"
                    }
                )
            elif format == "xliff":
                return Response(
                    content=export_data,
                    media_type="application/xliff+xml",
                    headers={
                        "Content-Disposition": f"attachment; filename=translations_{target_language}.xliff"
                    }
                )
                
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Validation endpoints

@router.post("/validate/{language_code}")
async def validate_translation(
    language_code: str,
    key: str = Body(...),
    text: str = Body(...),
    source_language: str = Body("en-US")
) -> TranslationValidationResult:
    """
    Validate a translation against the source text.
    
    Checks for placeholder mismatches, length issues, and other problems.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    result = await localization_service.validate_translation(
        key, text, source_language, language_code
    )
    
    return TranslationValidationResult(**result)


@router.get("/validate/all/{language_code}")
async def validate_all_translations(language_code: str):
    """
    Validate all translations for a language.
    
    Returns a report of all validation issues found.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    issues = await localization_service.repository.validate_translations(language_code)
    
    return {
        "language_code": language_code,
        "validation_date": datetime.utcnow().isoformat(),
        "total_issues": sum(len(v) for v in issues.values()),
        "issues_by_type": issues
    }


# Coverage and metrics endpoints

@router.get("/coverage/{build_id}")
async def get_coverage_report(
    build_id: str,
    languages: Optional[str] = Query(None, description="Comma-separated language codes")
):
    """
    Get localization coverage report for a build.
    
    Shows translation and approval percentages per language and category.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    language_list = languages.split(',') if languages else None
    
    report = await localization_service.get_coverage_report(build_id, language_list)
    
    return report


@router.post("/coverage/calculate/{build_id}/{language_code}")
async def calculate_coverage(build_id: str, language_code: str):
    """
    Calculate and store coverage metrics for a specific language.
    
    Updates the coverage tracking tables.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    coverage = await localization_service.repository.calculate_coverage(
        build_id, language_code
    )
    
    return coverage


# Language preference endpoints

@router.get("/preferences/{player_id}", response_model=Optional[LanguagePreferences])
async def get_language_preferences(player_id: str):
    """Get language preferences for a player."""
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    prefs = await localization_service.repository.get_language_preferences(player_id)
    
    if not prefs:
        return None
    
    return LanguagePreferences(**prefs)


@router.put("/preferences/{player_id}")
async def update_language_preferences(
    player_id: str,
    preferences: LanguagePreferences
):
    """Update language preferences for a player."""
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    await localization_service.repository.update_language_preferences(
        player_id, preferences.dict()
    )
    
    return {"status": "updated", "player_id": player_id}


# Language metadata endpoints

@router.get("/languages")
async def get_supported_languages(tier: Optional[int] = Query(None, ge=1, le=3)):
    """
    Get list of supported languages.
    
    Optionally filter by tier (1=full support, 2=subtitles only, 3=UI only).
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    languages = await localization_service.repository.get_supported_languages(tier)
    
    return {
        "count": len(languages),
        "languages": languages
    }


# Cache management

@router.post("/cache/clear")
async def clear_cache(
    language_code: Optional[str] = Query(None, description="Clear only specific language")
):
    """
    Clear the localization cache.
    
    Useful after bulk updates or imports.
    """
    if not localization_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    await localization_service.clear_cache(language_code)
    
    return {
        "status": "cleared",
        "language_code": language_code or "all"
    }


# Health check

@router.get("/health")
async def health_check():
    """Service health check."""
    return {
        "service": "localization",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
