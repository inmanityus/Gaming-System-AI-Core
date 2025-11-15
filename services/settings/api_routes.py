"""

API Routes - RESTful endpoints for Settings Service.

"""

import os

from typing import Any, Dict, Optional

from uuid import UUID



from fastapi import APIRouter, HTTPException, status, Header, Depends

from pydantic import BaseModel, Field, ValidationError

from .config_manager import ConfigManager, ConfigValidationError
from .content_level_manager import (
    ContentLevelManager,
    ContentPolicyError,
    PlayerContentPolicyNotFound,
    ContentProfileNotFound,
)
from .content_schemas import (
    CategoryLevels,
    ContentProfile as ContentProfileModel,
)
from .feature_flags import FeatureFlagManager
from .preference_handler import PreferenceHandler
from .tier_manager import TierManager




router = APIRouter(prefix="/api/v1/settings", tags=["settings"])



# SECURITY: Admin API Keys for protected admin operations
ADMIN_API_KEYS = set(os.getenv('SETTINGS_ADMIN_KEYS', '').split(',')) if os.getenv('SETTINGS_ADMIN_KEYS') else set()

async def verify_admin_access(x_api_key: str = Header(None)):
    """
    SECURITY: Verify admin API key for sensitive operations.
    
    Required for: tier changes, config changes, feature flag updates.
    These operations can cause revenue theft or system compromise.
    """
    if not ADMIN_API_KEYS:
        raise HTTPException(
            status_code=503,
            detail="Admin operations disabled: SETTINGS_ADMIN_KEYS not configured"
        )
    
    if not x_api_key or x_api_key not in ADMIN_API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized: Admin access required")
    return True

config_manager = ConfigManager()
content_level_manager = ContentLevelManager()
feature_flags = FeatureFlagManager()
preferences = PreferenceHandler()
tier_manager = TierManager()





class SettingRequest(BaseModel):

    """Request schema for setting a configuration value."""

    category: str = Field(..., min_length=1, max_length=50)

    key: str = Field(..., min_length=1, max_length=100)

    value: Any = Field(..., description="Setting value (must be JSON-serializable)")





class PreferenceRequest(BaseModel):

    """Request schema for setting a player preference."""

    category: str = Field(..., min_length=1, max_length=50)

    key: str = Field(..., min_length=1, max_length=100)

    value: Any = Field(..., description="Preference value (must be JSON-serializable)")





class FeatureFlagRequest(BaseModel):

    """Request schema for updating a feature flag."""

    enabled: Optional[bool] = None

    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)

    tier_gating: Optional[Dict[str, bool]] = None





# Configuration endpoints

@router.get("/config/{category}/{key}")

async def get_config(category: str, key: str):

    """Get a configuration setting."""

    try:

        value = await config_manager.get_setting(category, key)

        if value is None:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")

        return {"category": category, "key": key, "value": value}

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.put("/config/{category}/{key}", status_code=status.HTTP_204_NO_CONTENT)

async def set_config(
    category: str, 
    key: str, 
    request: SettingRequest,
    _admin: bool = Depends(verify_admin_access)  # SECURITY: Admin only
):

    """Set a configuration setting (triggers hot-reload). REQUIRES ADMIN API KEY."""

    try:

        await config_manager.set_setting(category, key, request.value)

        return None

    except ConfigValidationError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.get("/config")

async def get_all_config(category: Optional[str] = None):

    """Get all configuration settings."""

    try:

        settings = await config_manager.get_all_settings(category)

        return settings

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





# Preference endpoints

@router.get("/preferences/{player_id}/{category}/{key}")

async def get_preference(player_id: UUID, category: str, key: str):

    """Get a player preference."""

    try:

        value = await preferences.get_preference(player_id, category, key)

        if value is None:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")

        return {"player_id": str(player_id), "category": category, "key": key, "value": value}

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.put("/preferences/{player_id}/{category}/{key}", status_code=status.HTTP_204_NO_CONTENT)

async def set_preference(player_id: UUID, category: str, key: str, request: PreferenceRequest):

    """Set a player preference."""

    try:

        await preferences.set_preference(player_id, category, key, request.value)

        return None

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.get("/preferences/{player_id}")

async def get_all_preferences(player_id: UUID, category: Optional[str] = None):

    """Get all preferences for a player."""

    try:

        prefs = await preferences.get_all_preferences(player_id, category)

        return prefs

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





# Feature flag endpoints

@router.get("/feature-flags/{name}")

async def get_feature_flag(name: str):

    """Get a feature flag."""

    try:

        flag = await feature_flags.get_flag(name)

        if not flag:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

        return flag.to_dict()

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.get("/feature-flags/{name}/enabled")

async def check_feature_enabled(name: str, user_tier: str = "free", user_id: Optional[UUID] = None):

    """Check if a feature is enabled for a user."""

    try:

        enabled = await feature_flags.is_enabled(name, user_tier, user_id)

        return {"name": name, "enabled": enabled, "user_tier": user_tier}

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.put("/feature-flags/{name}", status_code=status.HTTP_204_NO_CONTENT)

async def update_feature_flag(
    name: str, 
    request: FeatureFlagRequest,
    _admin: bool = Depends(verify_admin_access)  # SECURITY: Admin only
):

    """Update a feature flag (triggers hot-reload). REQUIRES ADMIN API KEY."""

    try:

        await feature_flags.update_flag(

            name,

            enabled=request.enabled,

            rollout_percentage=request.rollout_percentage,

            tier_gating=request.tier_gating,

        )

        return None

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





# Tier endpoints

@router.get("/tiers/{player_id}")

async def get_player_tier(player_id: UUID):

    """Get a player's tier."""

    try:

        tier = await tier_manager.get_player_tier(player_id)

        limits = await tier_manager.get_tier_limits(player_id)

        return {"player_id": str(player_id), "tier": tier, "limits": limits}

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.put("/tiers/{player_id}/{tier}", status_code=status.HTTP_204_NO_CONTENT)

async def set_player_tier(
    player_id: UUID, 
    tier: str,
    _admin: bool = Depends(verify_admin_access)  # SECURITY: Admin only - REVENUE PROTECTION
):

    """Set a player's tier. REQUIRES ADMIN API KEY (prevents revenue theft)."""

    try:

        await tier_manager.set_player_tier(player_id, tier)

        return None

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ---------------------------------------------------------------------------
# Content Governance – Content Levels & Policies
# ---------------------------------------------------------------------------


class ContentLevelRequest(BaseModel):

    """Request payload for creating/updating a content level profile."""

    name: str = Field(..., min_length=1, max_length=100)

    description: Optional[str] = None

    levels: CategoryLevels

    is_system_default: bool = False

    target_age_rating: Optional[str] = None

    sensitive_themes_flags: Dict[str, bool] = Field(default_factory=dict)


class PlayerContentPolicyRequest(BaseModel):

    """Request payload for setting a player's content policy."""

    base_profile_id: UUID

    overrides: Optional[Dict[str, int]] = None

    custom_rules: Optional[Dict[str, Any]] = None


class SessionSnapshotRequest(BaseModel):

    """Request payload for creating a session content policy snapshot."""

    player_id: UUID


@router.get("/content-levels")
async def list_content_levels():

    """
    List all content level profiles.
    """

    try:

        profiles_by_name = await content_level_manager.list_profiles()

        return [p.model_dump() for p in profiles_by_name.values()]

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/content-levels", status_code=status.HTTP_201_CREATED)
async def create_content_level(
    request: ContentLevelRequest,
    _admin: bool = Depends(verify_admin_access),  # Admin-only – policy changes
):

    """
    Create or update a content level profile.
    """

    try:

        profile = ContentProfileModel(
            name=request.name,
            description=request.description,
            levels=request.levels,
            sensitive_themes_flags=request.sensitive_themes_flags,
            is_system_default=request.is_system_default,
            target_age_rating=request.target_age_rating,
        )

    except ValidationError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    try:

        created = await content_level_manager.create_profile(profile)

        return created.model_dump()

    except ContentPolicyError as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/content-levels/{level_id}")
async def get_content_level(level_id: UUID):

    """
    Get a specific content level profile by ID.
    """

    try:

        profile = await content_level_manager.get_profile_by_id(level_id)

        return profile.model_dump()

    except ContentProfileNotFound as e:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/players/{player_id}/content-policy")
async def get_player_content_policy(player_id: UUID):

    """
    Get the effective content policy configuration for a player.
    """

    try:

        policy = await content_level_manager.get_player_policy(player_id)

        return policy.model_dump()

    except PlayerContentPolicyNotFound as e:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put(
    "/players/{player_id}/content-policy",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def set_player_content_policy(player_id: UUID, request: PlayerContentPolicyRequest):

    """
    Set or update the per-player content policy.
    """

    try:

        await content_level_manager.upsert_player_policy(
            player_id=player_id,
            base_profile_id=request.base_profile_id,
            overrides=request.overrides,
            custom_rules=request.custom_rules,
        )

        return None

    except ContentPolicyError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/content-policy/snapshot",
    status_code=status.HTTP_201_CREATED,
)
async def create_session_content_policy_snapshot(
    session_id: UUID,
    request: SessionSnapshotRequest,
):

    """
    Compute and persist a per-session content policy snapshot.
    """

    try:

        snapshot = await content_level_manager.snapshot_session_policy(
            session_id=session_id,
            player_id=request.player_id,
        )

        return snapshot.model_dump()

    except PlayerContentPolicyNotFound as e:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except ContentPolicyError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

