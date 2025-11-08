"""

API Routes - RESTful endpoints for Settings Service.

"""



from typing import Any, Dict, Optional

from uuid import UUID



from fastapi import APIRouter, HTTPException, status

from pydantic import BaseModel, Field



from config_manager import ConfigManager, ConfigValidationError

from feature_flags import FeatureFlagManager

from preference_handler import PreferenceHandler

from tier_manager import TierManager



router = APIRouter(prefix="/api/v1/settings", tags=["settings"])



config_manager = ConfigManager()

feature_flags = FeatureFlagManager()

preferences = PreferenceHandler()

tier_manager = TierManager()





class SettingRequest(BaseModel):

    """Request schema for setting a configuration value."""

    category: str = Field(..., min_length=1, max_length=50)

    key: str = Field(..., min_length=1, max_length=100)

    value: Any(..., description="Setting value (must be JSON-serializable)")





class PreferenceRequest(BaseModel):

    """Request schema for setting a player preference."""

    category: str = Field(..., min_length=1, max_length=50)

    key: str = Field(..., min_length=1, max_length=100)

    value: Any(..., description="Preference value (must be JSON-serializable)")





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

async def set_config(category: str, key: str, request: SettingRequest):

    """Set a configuration setting (triggers hot-reload)."""

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

async def update_feature_flag(name: str, request: FeatureFlagRequest):

    """Update a feature flag (triggers hot-reload)."""

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

async def set_player_tier(player_id: UUID, tier: str):

    """Set a player's tier."""

    try:

        await tier_manager.set_player_tier(player_id, tier)

        return None

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



