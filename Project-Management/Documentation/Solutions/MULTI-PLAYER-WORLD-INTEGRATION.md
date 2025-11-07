# Multi-Player World Integration Solution
**Date**: 2025-01-29  
**Status**: Solution Architecture - Phase 2

---

## EXECUTIVE SUMMARY

Enables adding other players to existing worlds without rebuilding. Player interactions impact world evolution. All player worlds connected in a shared universe with cross-world avatar access.

### Key Features:
- Add players to existing worlds (no rebuild)
- Player interactions impact world evolution
- Connected universe of player worlds
- Cross-world avatar access

---

## 1. ARCHITECTURE

### 1.1 World Ownership Model

```python
class WorldOwnership:
    """
    Manages world ownership and permissions.
    """
    PRIMARY_OWNER = "primary"
    INVITED_PLAYER = "invited"
    READ_ONLY = "read_only"
    
    async def add_player_to_world(
        self,
        world_state_id: str,
        player_id: str,
        permission_level: str = "invited"
    ):
        """
        Add player to existing world without rebuilding.
        """
        # Add player to world_players table
        await self._add_world_player(
            world_state_id,
            player_id,
            permission_level
        )
        
        # Initialize player state in world
        await self._initialize_player_state(
            world_state_id,
            player_id
        )
        
        # Update NPC relationships
        await self._initialize_npc_relationships(
            world_state_id,
            player_id
        )
```

### 1.2 State Merging

```python
class WorldStateMerger:
    async def merge_player_influence(
        self,
        world_state_id: str,
        player_id: str
    ):
        """
        Merge new player's influence into existing world.
        
        Merges:
        - NPC relationships (initialize based on world state)
        - Faction standings (inherit from primary owner or neutral)
        - Storyline participation (join existing or create new)
        - Economic impact (add player to economy)
        """
        # Merge NPC relationships
        await self._merge_npc_relationships(world_state_id, player_id)
        
        # Merge faction standings
        await self._merge_faction_standings(world_state_id, player_id)
        
        # Merge storyline participation
        await self._merge_storyline_participation(world_state_id, player_id)
        
        # Merge economic state
        await self._merge_economic_state(world_state_id, player_id)
```

---

## 2. DATABASE SCHEMA

```sql
-- World player relationships
CREATE TABLE world_players (
    world_state_id UUID REFERENCES world_states(id),
    player_id UUID REFERENCES players(id),
    permission_level VARCHAR(20) NOT NULL,  -- primary, invited, read_only
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (world_state_id, player_id)
);

-- Cross-world avatar registry
CREATE TABLE player_avatars (
    player_id UUID PRIMARY KEY REFERENCES players(id),
    avatar_data JSONB NOT NULL,  -- Appearance, abilities, etc.
    accessible_from_worlds JSONB DEFAULT '[]',  -- World IDs where accessible
    updated_at TIMESTAMP DEFAULT NOW()
);

-- World evolution tracking
CREATE TABLE world_evolution (
    evolution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_state_id UUID REFERENCES world_states(id),
    player_id UUID REFERENCES players(id),
    change_type VARCHAR(50),  -- npc_relationship, faction, economic, etc.
    change_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 3. CROSS-WORLD AVATAR ACCESS

```python
class CrossWorldAvatarAccess:
    async def get_avatar_for_world(
        self,
        player_id: str,
        requesting_world_id: str
    ) -> Dict:
        """
        Get player avatar data for remote world access.
        """
        avatar = await self._get_avatar(player_id)
        
        # Verify access permission
        if not await self._can_access_from_world(player_id, requesting_world_id):
            raise PermissionError("Avatar not accessible from this world")
        
        return avatar
```

**END OF SOLUTION DOCUMENT**







