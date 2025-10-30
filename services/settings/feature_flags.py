"""

Feature Flags - Feature toggle system with rollout percentages and tier gating.

"""



import json

from typing import Dict, Optional

from uuid import UUID



from services.state_manager.connection_pool import get_postgres_pool, PostgreSQLPool





class FeatureFlag:

    """Represents a feature flag configuration."""

    

    def __init__(

        self,

        name: str,

        enabled: bool = False,

        rollout_percentage: int = 0,

        tier_gating: Optional[Dict[str, bool]] = None,

        ab_test_variant: Optional[str] = None,

    ):

        self.name = name

        self.enabled = enabled

        self.rollout_percentage = max(0, min(100, rollout_percentage))

        self.tier_gating = tier_gating or {}

        self.ab_test_variant = ab_test_variant

    

    def to_dict(self) -> dict:

        """Convert to dictionary."""

        return {

            "name": self.name,

            "enabled": self.enabled,

            "rollout_percentage": self.rollout_percentage,

            "tier_gating": self.tier_gating,

            "ab_test_variant": self.ab_test_variant,

        }

    

    @classmethod

    def from_dict(cls, data: dict) -> "FeatureFlag":

        """Create from dictionary."""

        return cls(

            name=data["name"],

            enabled=data.get("enabled", False),

            rollout_percentage=data.get("rollout_percentage", 0),

            tier_gating=data.get("tier_gating"),

            ab_test_variant=data.get("ab_test_variant"),

        )





class FeatureFlagManager:

    """

    Manages feature flags with rollout percentages and tier-based gating.

    """

    

    def __init__(self):

        self.postgres: Optional[PostgreSQLPool] = None

    

    async def _get_postgres(self) -> PostgreSQLPool:

        """Get PostgreSQL pool instance."""

        if self.postgres is None:

            self.postgres = await get_postgres_pool()

        return self.postgres

    

    async def create_flag(

        self,

        name: str,

        enabled: bool = False,

        rollout_percentage: int = 0,

        tier_gating: Optional[Dict[str, bool]] = None,

    ) -> FeatureFlag:

        """

        Create a new feature flag.

        

        Args:

            name: Feature flag name

            enabled: Whether feature is enabled globally

            rollout_percentage: Percentage rollout (0-100)

            tier_gating: Tier-based gating {"free": False, "premium": True, "whale": True}

        

        Returns:

            Created feature flag

        """

        postgres = await self._get_postgres()

        

        flag = FeatureFlag(

            name=name,

            enabled=enabled,

            rollout_percentage=rollout_percentage,

            tier_gating=tier_gating or {},

        )

        

        query = """

            INSERT INTO feature_flags (name, enabled, rollout_percentage, tier_gating, config)

            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb)

            ON CONFLICT (name)

            DO UPDATE SET enabled = $2, rollout_percentage = $3, tier_gating = $4::jsonb, updated_at = CURRENT_TIMESTAMP

            RETURNING name, enabled, rollout_percentage, tier_gating, config

        """

        

        result = await postgres.fetch(

            query,

            name,

            enabled,

            rollout_percentage,

            json.dumps(tier_gating or {}),

            json.dumps(flag.to_dict()),

        )

        

        return FeatureFlag.from_dict(json.loads(result["config"]))

    

    async def get_flag(self, name: str) -> Optional[FeatureFlag]:

        """

        Get a feature flag by name.

        

        Args:

            name: Feature flag name

        

        Returns:

            FeatureFlag or None if not found

        """

        postgres = await self._get_postgres()

        

        query = """

            SELECT name, enabled, rollout_percentage, tier_gating, config

            FROM feature_flags

            WHERE name = $1

        """

        

        result = await postgres.fetch(query, name)

        if not result:

            return None

        

        return FeatureFlag.from_dict(json.loads(result["config"]))

    

    async def is_enabled(self, name: str, user_tier: str = "free", user_id: Optional[UUID] = None) -> bool:

        """

        Check if a feature is enabled for a specific user.

        

        Args:

            name: Feature flag name

            user_tier: User tier (free/premium/whale)

            user_id: Optional user ID for rollout percentage calculation

        

        Returns:

            True if feature is enabled for this user

        """

        flag = await self.get_flag(name)

        if not flag:

            return False

        

        if not flag.enabled:

            return False

        

        # Check tier gating

        if flag.tier_gating and user_tier in flag.tier_gating:

            if not flag.tier_gating[user_tier]:

                return False

        

        # Check rollout percentage

        if flag.rollout_percentage < 100 and user_id:

            # Use UUID hash for consistent rollout

            user_hash = hash(str(user_id)) % 100

            if user_hash >= flag.rollout_percentage:

                return False

        

        return True

    

    async def update_flag(

        self,

        name: str,

        enabled: Optional[bool] = None,

        rollout_percentage: Optional[int] = None,

        tier_gating: Optional[Dict[str, bool]] = None,

    ) -> FeatureFlag:

        """

        Update a feature flag.

        

        Args:

            name: Feature flag name

            enabled: New enabled state

            rollout_percentage: New rollout percentage

            tier_gating: New tier gating 

        

        Returns:

            Updated feature flag

        """

        flag = await self.get_flag(name)

        if not flag:

            raise ValueError(f"Feature flag '{name}' not found")

        

        if enabled is not None:

            flag.enabled = enabled

        if rollout_percentage is not None:

            flag.rollout_percentage = max(0, min(100, rollout_percentage))

        if tier_gating is not None:

            flag.tier_gating = tier_gating

        

        postgres = await self._get_postgres()

        

        query = """

            UPDATE feature_flags

            SET enabled = $1, rollout_percentage = $2, tier_gating = $3::jsonb,

                config = $4::jsonb, updated_at = CURRENT_TIMESTAMP

            WHERE name = $5

            RETURNING name, enabled, rollout_percentage, tier_gating, config

        """

        

        result = await postgres.fetch(

            query,

            flag.enabled,

            flag.rollout_percentage,

            json.dumps(flag.tier_gating),

            json.dumps(flag.to_dict()),

            name,

        )

        

        # Invalidate cache

        from services.state_manager.connection_pool import get_redis_pool

        redis = await get_redis_pool()

        await redis.delete(f"feature_flag:{name}")

        

        return FeatureFlag.from_dict(json.loads(result["config"]))



