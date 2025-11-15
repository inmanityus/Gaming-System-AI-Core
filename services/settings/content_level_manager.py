"""
Content Level Manager
=====================

Implements the core Content Governance primitives on the Settings service side:
- System + custom content profiles (`content_levels` table)
- Per-player content policy (`player_content_profiles` table)
- Per-session content policy snapshots (`session_content_policy` table)

This module focuses on **data correctness and policy computation**. It does not
own HTTP or NATS wiring; API routes and event publishers call into this layer.
"""

from __future__ import annotations

import json
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import ValidationError

from services.state_manager.connection_pool import PostgreSQLPool, get_postgres_pool

from .content_schemas import (
    CategoryLevels,
    ContentProfile,
    PlayerContentPolicy,
    SessionContentPolicySnapshot,
    compute_effective_levels,
)


class ContentPolicyError(Exception):
    """Base class for content policy errors."""


class ContentProfileNotFound(ContentPolicyError):
    """Raised when a referenced content profile does not exist."""


class PlayerContentPolicyNotFound(ContentPolicyError):
    """Raised when a player has no content policy configured."""


class ContentLevelManager:
    """
    Core business logic for content profiles and content policies.

    All DB access goes through PostgreSQLPool so this can be reused from
    FastAPI routes, NATS workers, or background tasks.
    """

    def __init__(self, postgres: Optional[PostgreSQLPool] = None) -> None:
        self._postgres: Optional[PostgreSQLPool] = postgres

    async def _get_postgres(self) -> PostgreSQLPool:
        """Lazily obtain a PostgreSQLPool instance."""
        if self._postgres is None:
            self._postgres = await get_postgres_pool()
        return self._postgres

    # -------------------------------------------------------------------------
    # Profile registry
    # -------------------------------------------------------------------------

    async def create_profile(self, profile: ContentProfile) -> ContentProfile:
        """
        Create a new content profile in the `content_levels` table.

        If profile.id is None a UUID will be generated server-side.
        """
        postgres = await self._get_postgres()

        profile_id = profile.id or uuid4()
        levels: CategoryLevels = profile.levels

        query = """
            INSERT INTO content_levels (
                id,
                name,
                description,
                violence_gore_level,
                sexual_content_nudity_level,
                language_profanity_level,
                horror_intensity_level,
                drugs_substances_level,
                sensitive_themes_level,
                moral_complexity_level,
                sensitive_themes_flags,
                is_system_default,
                target_age_rating
            )
            VALUES (
                $1, $2, $3,
                $4, $5, $6, $7, $8, $9, $10,
                $11::jsonb,
                $12,
                $13
            )
            ON CONFLICT (name)
            DO UPDATE SET
                description = EXCLUDED.description,
                violence_gore_level = EXCLUDED.violence_gore_level,
                sexual_content_nudity_level = EXCLUDED.sexual_content_nudity_level,
                language_profanity_level = EXCLUDED.language_profanity_level,
                horror_intensity_level = EXCLUDED.horror_intensity_level,
                drugs_substances_level = EXCLUDED.drugs_substances_level,
                sensitive_themes_level = EXCLUDED.sensitive_themes_level,
                moral_complexity_level = EXCLUDED.moral_complexity_level,
                sensitive_themes_flags = EXCLUDED.sensitive_themes_flags,
                is_system_default = EXCLUDED.is_system_default,
                target_age_rating = EXCLUDED.target_age_rating,
                updated_at = CURRENT_TIMESTAMP
            RETURNING
                id,
                name,
                description,
                violence_gore_level,
                sexual_content_nudity_level,
                language_profanity_level,
                horror_intensity_level,
                drugs_substances_level,
                sensitive_themes_level,
                moral_complexity_level,
                sensitive_themes_flags,
                is_system_default,
                target_age_rating
        """

        result = await postgres.fetch(
            query,
            profile_id,
            profile.name,
            profile.description or "",
            levels.violence_gore,
            levels.sexual_content_nudity,
            levels.language_profanity,
            levels.horror_intensity,
            levels.drugs_substances,
            levels.sensitive_themes,
            levels.moral_complexity,
            json.dumps(profile.sensitive_themes_flags or {}),
            profile.is_system_default,
            profile.target_age_rating,
        )

        if result is None:
            raise ContentPolicyError("Failed to insert or update content profile")

        db_levels = CategoryLevels(
            violence_gore=result["violence_gore_level"],
            sexual_content_nudity=result["sexual_content_nudity_level"],
            language_profanity=result["language_profanity_level"],
            horror_intensity=result["horror_intensity_level"],
            drugs_substances=result["drugs_substances_level"],
            sensitive_themes=result["sensitive_themes_level"],
            moral_complexity=result["moral_complexity_level"],
        )

        try:
            flags = result["sensitive_themes_flags"] or {}
            if isinstance(flags, str):
                flags = json.loads(flags)
        except (TypeError, ValueError):
            flags = {}

        return ContentProfile(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            levels=db_levels,
            sensitive_themes_flags=flags,
            is_system_default=result["is_system_default"],
            target_age_rating=result["target_age_rating"],
        )

    async def get_profile_by_id(self, profile_id: UUID) -> ContentProfile:
        """Fetch a content profile by ID or raise ContentProfileNotFound."""
        postgres = await self._get_postgres()
        query = """
            SELECT
                id,
                name,
                description,
                violence_gore_level,
                sexual_content_nudity_level,
                language_profanity_level,
                horror_intensity_level,
                drugs_substances_level,
                sensitive_themes_level,
                moral_complexity_level,
                sensitive_themes_flags,
                is_system_default,
                target_age_rating
            FROM content_levels
            WHERE id = $1
        """
        result = await postgres.fetch(query, profile_id)
        if result is None:
            raise ContentProfileNotFound(f"Content profile id={profile_id} not found")

        levels = CategoryLevels(
            violence_gore=result["violence_gore_level"],
            sexual_content_nudity=result["sexual_content_nudity_level"],
            language_profanity=result["language_profanity_level"],
            horror_intensity=result["horror_intensity_level"],
            drugs_substances=result["drugs_substances_level"],
            sensitive_themes=result["sensitive_themes_level"],
            moral_complexity=result["moral_complexity_level"],
        )

        try:
            flags = result["sensitive_themes_flags"] or {}
            if isinstance(flags, str):
                flags = json.loads(flags)
        except (TypeError, ValueError):
            flags = {}

        return ContentProfile(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            levels=levels,
            sensitive_themes_flags=flags,
            is_system_default=result["is_system_default"],
            target_age_rating=result["target_age_rating"],
        )

    async def list_profiles(self) -> Dict[str, ContentProfile]:
        """
        Return all content profiles keyed by name.

        This is primarily intended for admin tools and tests, not hot-path usage.
        """
        postgres = await self._get_postgres()
        query = """
            SELECT
                id,
                name,
                description,
                violence_gore_level,
                sexual_content_nudity_level,
                language_profanity_level,
                horror_intensity_level,
                drugs_substances_level,
                sensitive_themes_level,
                moral_complexity_level,
                sensitive_themes_flags,
                is_system_default,
                target_age_rating
            FROM content_levels
            ORDER BY name
        """
        rows = await postgres.fetch_all(query)
        profiles: Dict[str, ContentProfile] = {}
        for row in rows:
            levels = CategoryLevels(
                violence_gore=row["violence_gore_level"],
                sexual_content_nudity=row["sexual_content_nudity_level"],
                language_profanity=row["language_profanity_level"],
                horror_intensity=row["horror_intensity_level"],
                drugs_substances=row["drugs_substances_level"],
                sensitive_themes=row["sensitive_themes_level"],
                moral_complexity=row["moral_complexity_level"],
            )
            try:
                flags = row["sensitive_themes_flags"] or {}
                if isinstance(flags, str):
                    flags = json.loads(flags)
            except (TypeError, ValueError):
                flags = {}

            profiles[row["name"]] = ContentProfile(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                levels=levels,
                sensitive_themes_flags=flags,
                is_system_default=row["is_system_default"],
                target_age_rating=row["target_age_rating"],
            )
        return profiles

    # -------------------------------------------------------------------------
    # Per-player policy
    # -------------------------------------------------------------------------

    async def upsert_player_policy(
        self,
        player_id: UUID,
        base_profile_id: UUID,
        overrides: Optional[Dict[str, int]] = None,
        custom_rules: Optional[Dict[str, object]] = None,
    ) -> PlayerContentPolicy:
        """
        Create or update the per-player content policy row.
        """
        postgres = await self._get_postgres()

        overrides_json = json.dumps(overrides or {})
        custom_rules_json = json.dumps(custom_rules or {})

        query = """
            INSERT INTO player_content_profiles (
                player_id,
                base_level_id,
                overrides,
                custom_rules,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3::jsonb, $4::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (player_id)
            DO UPDATE SET
                base_level_id = EXCLUDED.base_level_id,
                overrides = EXCLUDED.overrides,
                custom_rules = EXCLUDED.custom_rules,
                updated_at = CURRENT_TIMESTAMP
            RETURNING
                player_id,
                base_level_id,
                overrides,
                custom_rules
        """

        result = await postgres.fetch(
            query,
            player_id,
            base_profile_id,
            overrides_json,
            custom_rules_json,
        )

        if result is None:
            raise ContentPolicyError("Failed to upsert player content policy")

        try:
            raw_overrides = result["overrides"] or {}
            if isinstance(raw_overrides, str):
                raw_overrides = json.loads(raw_overrides)
        except (TypeError, ValueError):
            raw_overrides = {}

        try:
            raw_custom_rules = result["custom_rules"] or {}
            if isinstance(raw_custom_rules, str):
                raw_custom_rules = json.loads(raw_custom_rules)
        except (TypeError, ValueError):
            raw_custom_rules = {}

        # Resolve profile name lazily at call-sites where needed; here we only
        # return ids and overrides.
        return PlayerContentPolicy(
            player_id=result["player_id"],
            base_profile_id=result["base_level_id"],
            overrides=raw_overrides,
            custom_rules=raw_custom_rules,
        )

    async def get_player_policy(self, player_id: UUID) -> PlayerContentPolicy:
        """
        Fetch the PlayerContentPolicy for a player.
        """
        postgres = await self._get_postgres()
        query = """
            SELECT
                p.player_id,
                p.base_level_id,
                p.overrides,
                p.custom_rules,
                c.name AS base_profile_name
            FROM player_content_profiles p
            LEFT JOIN content_levels c ON c.id = p.base_level_id
            WHERE p.player_id = $1
        """
        result = await postgres.fetch(query, player_id)
        if result is None:
            raise PlayerContentPolicyNotFound(f"No content policy for player {player_id}")

        try:
            overrides = result["overrides"] or {}
            if isinstance(overrides, str):
                overrides = json.loads(overrides)
        except (TypeError, ValueError):
            overrides = {}

        try:
            custom_rules = result["custom_rules"] or {}
            if isinstance(custom_rules, str):
                custom_rules = json.loads(custom_rules)
        except (TypeError, ValueError):
            custom_rules = {}

        return PlayerContentPolicy(
            player_id=result["player_id"],
            base_profile_id=result["base_level_id"],
            base_profile_name=result["base_profile_name"],
            overrides=overrides,
            custom_rules=custom_rules,
        )

    # -------------------------------------------------------------------------
    # Session policy snapshots
    # -------------------------------------------------------------------------

    async def snapshot_session_policy(
        self,
        session_id: UUID,
        player_id: UUID,
    ) -> SessionContentPolicySnapshot:
        """
        Compute and persist a per-session content policy snapshot.

        This method is intended to be called on session start. It:
        - loads the player's content policy,
        - loads the referenced content profile,
        - computes effective levels with overrides,
        - writes a row to `session_content_policy`,
        - returns the in-memory snapshot model.
        """
        postgres = await self._get_postgres()

        player_policy = await self.get_player_policy(player_id)
        if not player_policy.base_profile_id:
            raise ContentPolicyError(
                f"Player {player_id} has no base content profile configured"
            )

        profile = await self.get_profile_by_id(player_policy.base_profile_id)

        try:
            base_levels = profile.levels
            effective_levels = compute_effective_levels(
                base_levels, player_policy.overrides
            )
        except ValidationError as exc:
            raise ContentPolicyError(f"Invalid content levels: {exc}") from exc

        # Determine next policy_version for this session
        version_query = """
            SELECT COALESCE(MAX(policy_version) + 1, 1) AS next_version
            FROM session_content_policy
            WHERE session_id = $1
        """
        version_row = await postgres.fetch(version_query, session_id)
        next_version = version_row["next_version"] if version_row else 1

        snapshot = SessionContentPolicySnapshot(
            session_id=session_id,
            player_id=player_id,
            policy_version=int(next_version),
            base_profile_id=profile.id,
            base_profile_name=profile.name,
            effective_levels=effective_levels.to_mapping(),
            overrides=player_policy.overrides,
            custom_rules=player_policy.custom_rules,
        )

        insert_query = """
            INSERT INTO session_content_policy (
                id,
                session_id,
                player_id,
                base_level_id,
                effective_levels,
                overrides,
                custom_rules,
                policy_version,
                created_at,
                updated_at
            )
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5::jsonb,
                $6::jsonb,
                $7::jsonb,
                $8,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
        """

        await postgres.execute(
            insert_query,
            uuid4(),
            snapshot.session_id,
            snapshot.player_id,
            snapshot.base_profile_id,
            json.dumps(snapshot.effective_levels),
            json.dumps(snapshot.overrides),
            json.dumps(snapshot.custom_rules),
            snapshot.policy_version,
        )

        return snapshot


