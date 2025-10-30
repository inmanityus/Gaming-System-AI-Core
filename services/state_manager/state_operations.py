"""

State Operations - CRUD operations for game state management.

Integrates cache layer with PostgreSQL persistence.

"""



import json

from typing import Any, Dict, List, Optional

from uuid import UUID



from .cache_layer import CacheLayer

from .connection_pool import get_postgres_pool, PostgreSQLPool





class ConflictResolutionError(Exception):

    """Raised when optimistic locking conflict occurs."""

    pass





def _convert_state_dict(state_dict: dict) -> dict:

    """Convert state dict: UUIDs to strings, JSONB fields to Python objects."""

    # Convert UUIDs to strings for JSON serialization

    if state_dict.get("id"):

        state_dict["id"] = str(state_dict["id"])

    if state_dict.get("player_id"):

        state_dict["player_id"] = str(state_dict["player_id"])

    

    # Convert JSONB fields

    if state_dict.get("position"):

        state_dict["position"] = json.loads(state_dict["position"]) if isinstance(state_dict["position"], str) else state_dict["position"]

    if state_dict.get("active_quests"):

        state_dict["active_quests"] = json.loads(state_dict["active_quests"]) if isinstance(state_dict["active_quests"], str) else state_dict["active_quests"]

    if state_dict.get("session_data"):

        state_dict["session_data"] = json.loads(state_dict["session_data"]) if isinstance(state_dict["session_data"], str) else state_dict["session_data"]

    

    return state_dict





class StateOperations:

    """

    CRUD operations for game state management.

    Implements read-through and write-through caching with PostgreSQL persistence.

    """

    

    def __init__(self):

        self.cache = CacheLayer()

        self.postgres: Optional[PostgreSQLPool] = None

    

    async def _get_postgres(self) -> PostgreSQLPool:

        """Get PostgreSQL pool instance."""

        if self.postgres is None:

            self.postgres = await get_postgres_pool()

        return self.postgres

    

    async def create_game_state(

        self,

        player_id: UUID,

        current_world: str = "day",

        location: Optional[str] = None,

        position: Optional[Dict[str, float]] = None,

        active_quests: Optional[List[str]] = None,

        session_data: Optional[Dict[str, Any]] = None,

    ) -> Dict[str, Any]:

        """

        Create a new game state.

        

        Args:

            player_id: Player UUID

            current_world: "day" or "night"

            location: Current location identifier

            position: 3D coordinates {x, y, z}

            active_quests: List of active quest IDs

            session_data: Additional session data

        

        Returns:

            Created game state as dict

        """

        postgres = await self._get_postgres()

        

        # Insert into PostgreSQL

        query = """

            INSERT INTO game_states 

            (player_id, current_world, location, position, active_quests, session_data, is_active, version)

            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7, $8)

            RETURNING id, player_id, current_world, location, position, active_quests, 

                      session_data, is_active, version, created_at, updated_at

        """

        

        result = await postgres.fetch(

            query,

            player_id,

            current_world,

            location,

            json.dumps(position) if position else None,

            json.dumps(active_quests or []),

            json.dumps(session_data or {}),

            True,  # is_active

            1,  # version

        )

        

        state_dict = _convert_state_dict(dict(result))

        

        # Cache the new state

        await self.cache.set("game_state", UUID(state_dict["id"]), state_dict)

        

        return state_dict

    

    async def get_game_state(self, state_id: UUID) -> Optional[Dict[str, Any]]:

        """

        Get game state by ID (read-through cache).

        

        Args:

            state_id: Game state UUID

        

        Returns:

            Game state dict or None if not found

        """

        # Try cache first

        cached = await self.cache.get("game_state", state_id)

        if cached:

            return cached

        

        # Fallback to PostgreSQL

        postgres = await self._get_postgres()

        query = """

            SELECT id, player_id, current_world, location, position, active_quests,

                   session_data, is_active, version, created_at, updated_at

            FROM game_states

            WHERE id = $1

        """

        

        result = await postgres.fetch(query, state_id)

        if not result:

            return None

        

        state_dict = _convert_state_dict(dict(result))

        

        # Cache the result

        await self.cache.set("game_state", state_id, state_dict)

        

        return state_dict

    

    async def get_game_state_by_player(self, player_id: UUID, active_only: bool = True) -> Optional[Dict[str, Any]]:

        """

        Get active game state for a player.

        

        Args:

            player_id: Player UUID

            active_only: If True, only return active game states

        

        Returns:

            Game state dict or None if not found

        """

        postgres = await self._get_postgres()

        

        if active_only:

            query = """

                SELECT id, player_id, current_world, location, position, active_quests,

                       session_data, is_active, version, created_at, updated_at

                FROM game_states

                WHERE player_id = $1 AND is_active = TRUE

                ORDER BY updated_at DESC

                LIMIT 1

            """

        else:

            query = """

                SELECT id, player_id, current_world, location, position, active_quests,

                       session_data, is_active, version, created_at, updated_at

                FROM game_states

                WHERE player_id = $1

                ORDER BY updated_at DESC

                LIMIT 1

            """

        

        result = await postgres.fetch(query, player_id)

        if not result:

            return None

        

        state_dict = _convert_state_dict(dict(result))

        

        # Cache the result

        await self.cache.set("game_state", UUID(state_dict["id"]), state_dict)

        

        return state_dict

    

    async def update_game_state(

        self,

        state_id: UUID,

        expected_version: int,

        current_world: Optional[str] = None,

        location: Optional[str] = None,

        position: Optional[Dict[str, float]] = None,

        active_quests: Optional[List[str]] = None,

        session_data: Optional[Dict[str, Any]] = None,

        is_active: Optional[bool] = None,

    ) -> Dict[str, Any]:

        """

        Update game state with optimistic locking.

        

        Args:

            state_id: Game state UUID

            expected_version: Expected version number (for optimistic locking)

            current_world: Optional new world value

            location: Optional new location

            position: Optional new position

            active_quests: Optional new active quests

            session_data: Optional new session data

            is_active: Optional new active status

        

        Returns:

            Updated game state dict

        

        Raises:

            ConflictResolutionError: If version mismatch (optimistic locking conflict)

        """

        postgres = await self._get_postgres()

        

        # Build update query dynamically based on provided fields

        updates = []

        params = []

        param_idx = 2  # Start after state_id and expected_version

        

        if current_world is not None:

            updates.append(f"current_world = ${param_idx}")

            params.append(current_world)

            param_idx += 1

        

        if location is not None:

            updates.append(f"location = ${param_idx}")

            params.append(location)

            param_idx += 1

        

        if position is not None:

            updates.append(f"position = ${param_idx}::jsonb")

            params.append(json.dumps(position))

            param_idx += 1

        

        if active_quests is not None:

            updates.append(f"active_quests = ${param_idx}::jsonb")

            params.append(json.dumps(active_quests))

            param_idx += 1

        

        if session_data is not None:

            updates.append(f"session_data = ${param_idx}::jsonb")

            params.append(json.dumps(session_data))

            param_idx += 1

        

        if is_active is not None:

            updates.append(f"is_active = ${param_idx}")

            params.append(is_active)

            param_idx += 1

        

        if not updates:

            # No updates provided, just return current state

            return await self.get_game_state(state_id)

        

        # Always increment version for optimistic locking

        updates.append("version = version + 1")

        updates.append("updated_at = CURRENT_TIMESTAMP")

        

        query = f"""

            UPDATE game_states

            SET {', '.join(updates)}

            WHERE id = $1 AND version = ${param_idx}

            RETURNING id, player_id, current_world, location, position, active_quests,

                      session_data, is_active, version, created_at, updated_at

        """

        params.insert(0, state_id)  # state_id as $1

        params.append(expected_version)  # expected_version as last param

        

        result = await postgres.fetch(query, *params)

        

        if not result:

            # Version mismatch - conflict detected

            raise ConflictResolutionError(

                f"Optimistic locking conflict: expected version {expected_version} but current version differs"

            )

        

        state_dict = _convert_state_dict(dict(result))

        

        # Update cache

        await self.cache.set("game_state", state_id, state_dict)

        

        return state_dict

    

    async def delete_game_state(self, state_id: UUID):

        """

        Delete game state (soft delete by setting is_active = False).

        

        Args:

            state_id: Game state UUID

        """

        postgres = await self._get_postgres()

        

        query = """

            UPDATE game_states

            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP

            WHERE id = $1

        """

        

        await postgres.execute(query, state_id)

        

        # Invalidate cache

        await self.cache.delete("game_state", state_id)

