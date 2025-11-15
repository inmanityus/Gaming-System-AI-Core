"""
Story State Manager - Core component for managing per-player story state.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import asyncpg
from loguru import logger

from .story_schemas import (
    StorySnapshot, ArcProgress, StoryDecision, EntityRelationship,
    Experience, DarkWorldStanding, DarkWorldFamily, ProgressState,
    ArcRole
)


class StoryStateManager:
    """Manages structured per-player story state."""
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres = postgres_pool
        self._snapshot_cache: Dict[str, Tuple[StorySnapshot, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def get_story_snapshot(
        self, 
        player_id: UUID,
        use_cache: bool = True
    ) -> StorySnapshot:
        """
        Get complete story snapshot for a player.
        
        Args:
            player_id: Player UUID
            use_cache: Whether to use cached snapshots
            
        Returns:
            Complete story state snapshot
        """
        # Check cache first
        cache_key = str(player_id)
        if use_cache and cache_key in self._snapshot_cache:
            snapshot, cached_at = self._snapshot_cache[cache_key]
            if datetime.utcnow() - cached_at < self._cache_ttl:
                logger.debug(f"Returning cached snapshot for player {player_id}")
                return snapshot
        
        logger.info(f"Building fresh snapshot for player {player_id}")
        
        async with self.postgres.acquire() as conn:
            # Get player metadata
            player_data = await conn.fetchrow(
                """
                SELECT broker_book_state, debt_of_flesh_state, surgeon_butcher_score
                FROM story_players
                WHERE player_id = $1
                """,
                player_id
            )
            
            if not player_data:
                # Initialize new player
                await self._initialize_player(player_id)
                player_data = {
                    'broker_book_state': {},
                    'debt_of_flesh_state': {},
                    'surgeon_butcher_score': 0.0
                }
            
            # Get arc progress
            arc_rows = await conn.fetch(
                """
                SELECT arc_id, arc_role, progress_state, last_beat_id, last_update_at
                FROM story_arc_progress
                WHERE player_id = $1
                ORDER BY last_update_at DESC
                """,
                player_id
            )
            
            # Get recent decisions (last 20)
            decision_rows = await conn.fetch(
                """
                SELECT decision_id, arc_id, npc_id, choice_label, 
                       outcome_tags, moral_weight, timestamp
                FROM story_decisions
                WHERE player_id = $1
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                player_id
            )
            
            # Get relationships
            relationship_rows = await conn.fetch(
                """
                SELECT entity_id, entity_type, relationship_score,
                       flags, last_interaction, last_interaction_at
                FROM story_relationships
                WHERE player_id = $1
                """,
                player_id
            )
            
            # Get experiences
            experience_rows = await conn.fetch(
                """
                SELECT experience_id, status, emotional_impact,
                       cross_references, started_at, completed_at
                FROM story_experiences
                WHERE player_id = $1
                ORDER BY started_at DESC
                """,
                player_id
            )
            
            # Get Dark World standings
            standing_rows = await conn.fetch(
                """
                SELECT family_name, standing_score, favors_owed,
                       debts_owed, betrayal_count, special_status, last_interaction
                FROM dark_world_standings
                WHERE player_id = $1
                """,
                player_id
            )
        
        # Build snapshot
        snapshot = StorySnapshot(
            player_id=player_id,
            surgeon_butcher_score=player_data['surgeon_butcher_score'],
            broker_book_state=player_data['broker_book_state'] or {},
            debt_of_flesh_state=player_data['debt_of_flesh_state'] or {},
            arc_progress=[
                ArcProgress(
                    arc_id=row['arc_id'],
                    arc_role=row['arc_role'],
                    progress_state=row['progress_state'],
                    last_beat_id=row['last_beat_id'],
                    last_update_at=row['last_update_at']
                )
                for row in arc_rows
            ],
            recent_decisions=[
                StoryDecision(
                    decision_id=row['decision_id'],
                    arc_id=row['arc_id'],
                    npc_id=row['npc_id'],
                    choice_label=row['choice_label'],
                    outcome_tags=row['outcome_tags'] or [],
                    moral_weight=row['moral_weight'],
                    timestamp=row['timestamp']
                )
                for row in decision_rows
            ],
            relationships=[
                EntityRelationship(
                    entity_id=row['entity_id'],
                    entity_type=row['entity_type'],
                    relationship_score=row['relationship_score'],
                    flags=row['flags'] or [],
                    last_interaction=row['last_interaction'],
                    last_interaction_at=row['last_interaction_at']
                )
                for row in relationship_rows
            ],
            dark_world_standings=[
                DarkWorldStanding(
                    family_name=row['family_name'],
                    standing_score=row['standing_score'],
                    favors_owed=row['favors_owed'],
                    debts_owed=row['debts_owed'],
                    betrayal_count=row['betrayal_count'],
                    special_status=row['special_status'] or [],
                    last_interaction=row['last_interaction']
                )
                for row in standing_rows
            ]
        )
        
        # Split experiences into active and completed
        for row in experience_rows:
            exp = Experience(
                experience_id=row['experience_id'],
                status=row['status'],
                emotional_impact=row['emotional_impact'] or {},
                cross_references=row['cross_references'] or [],
                started_at=row['started_at'],
                completed_at=row['completed_at']
            )
            if row['status'] in ['completed', 'failed']:
                snapshot.completed_experiences.append(exp)
            else:
                snapshot.active_experiences.append(exp)
        
        # Cache the snapshot
        if use_cache:
            self._snapshot_cache[cache_key] = (snapshot, datetime.utcnow())
        
        return snapshot
    
    async def update_arc_progress(
        self,
        player_id: UUID,
        arc_id: str,
        arc_role: ArcRole,
        progress_state: ProgressState,
        last_beat_id: Optional[str] = None
    ) -> None:
        """Update progress for a story arc."""
        async with self.postgres.acquire() as conn:
            # Use transaction for atomic update
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO story_arc_progress 
                        (player_id, arc_id, arc_role, progress_state, last_beat_id, last_update_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (player_id, arc_id) 
                    DO UPDATE SET
                        arc_role = EXCLUDED.arc_role,
                        progress_state = EXCLUDED.progress_state,
                        last_beat_id = EXCLUDED.last_beat_id,
                        last_update_at = EXCLUDED.last_update_at
                    """,
                    player_id, arc_id, arc_role, progress_state, 
                    last_beat_id, datetime.utcnow()
                )
        
        # Invalidate cache
        self._invalidate_cache(player_id)
    
    async def record_decision(
        self,
        player_id: UUID,
        decision: StoryDecision,
        session_id: Optional[UUID] = None
    ) -> None:
        """Record a key player decision."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO story_decisions 
                    (player_id, session_id, decision_id, arc_id, npc_id,
                     choice_label, outcome_tags, moral_weight, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                player_id, session_id, decision.decision_id, decision.arc_id,
                decision.npc_id, decision.choice_label, 
                json.dumps(decision.outcome_tags), decision.moral_weight,
                decision.timestamp
            )
            
            # Update surgeon/butcher score if moral weight is significant
            if abs(decision.moral_weight) > 0.01:
                await self._update_moral_score(player_id, decision.moral_weight)
        
        self._invalidate_cache(player_id)
    
    async def update_relationship(
        self,
        player_id: UUID,
        entity_id: str,
        entity_type: str,
        score_delta: Optional[float] = None,
        new_flags: Optional[List[str]] = None,
        interaction: Optional[str] = None
    ) -> EntityRelationship:
        """Update relationship with an NPC or faction."""
        async with self.postgres.acquire() as conn:
            # Get current state
            current = await conn.fetchrow(
                """
                SELECT relationship_score, flags
                FROM story_relationships
                WHERE player_id = $1 AND entity_id = $2
                """,
                player_id, entity_id
            )
            
            if current:
                new_score = current['relationship_score']
                if score_delta is not None:
                    new_score = max(-100, min(100, new_score + score_delta))
                
                flags = current['flags'] or []
                if new_flags:
                    flags = list(set(flags + new_flags))
                
                await conn.execute(
                    """
                    UPDATE story_relationships
                    SET relationship_score = $1, flags = $2, 
                        last_interaction = $3, last_interaction_at = $4,
                        updated_at = $5
                    WHERE player_id = $6 AND entity_id = $7
                    """,
                    new_score, json.dumps(flags), interaction,
                    datetime.utcnow() if interaction else None,
                    datetime.utcnow(), player_id, entity_id
                )
            else:
                # Create new relationship
                new_score = score_delta or 0.0
                flags = new_flags or []
                
                await conn.execute(
                    """
                    INSERT INTO story_relationships
                        (player_id, entity_id, entity_type, relationship_score,
                         flags, last_interaction, last_interaction_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    player_id, entity_id, entity_type, new_score,
                    json.dumps(flags), interaction,
                    datetime.utcnow() if interaction else None
                )
            
            # Return updated relationship
            result = EntityRelationship(
                entity_id=entity_id,
                entity_type=entity_type,
                relationship_score=new_score,
                flags=flags,
                last_interaction=interaction,
                last_interaction_at=datetime.utcnow() if interaction else None
            )
        
        self._invalidate_cache(player_id)
        return result
    
    async def update_dark_world_standing(
        self,
        player_id: UUID,
        family: DarkWorldFamily,
        standing_delta: Optional[float] = None,
        favor_delta: Optional[int] = None,
        debt_delta: Optional[int] = None,
        betrayal: bool = False,
        special_status: Optional[List[str]] = None
    ) -> DarkWorldStanding:
        """Update standing with a Dark World family."""
        async with self.postgres.acquire() as conn:
            # Get current state
            current = await conn.fetchrow(
                """
                SELECT standing_score, favors_owed, debts_owed, 
                       betrayal_count, special_status
                FROM dark_world_standings
                WHERE player_id = $1 AND family_name = $2
                """,
                player_id, family.value
            )
            
            if current:
                # Update existing
                new_standing = current['standing_score']
                if standing_delta:
                    new_standing = max(-100, min(100, new_standing + standing_delta))
                
                new_favors = max(0, current['favors_owed'] + (favor_delta or 0))
                new_debts = max(0, current['debts_owed'] + (debt_delta or 0))
                new_betrayals = current['betrayal_count'] + (1 if betrayal else 0)
                
                status_list = current['special_status'] or []
                if special_status:
                    status_list = list(set(status_list + special_status))
                
                await conn.execute(
                    """
                    UPDATE dark_world_standings
                    SET standing_score = $1, favors_owed = $2, debts_owed = $3,
                        betrayal_count = $4, special_status = $5,
                        last_interaction = $6, updated_at = $7
                    WHERE player_id = $8 AND family_name = $9
                    """,
                    new_standing, new_favors, new_debts, new_betrayals,
                    json.dumps(status_list), datetime.utcnow(), 
                    datetime.utcnow(), player_id, family.value
                )
            else:
                # Create new standing
                new_standing = standing_delta or 0.0
                new_favors = max(0, favor_delta or 0)
                new_debts = max(0, debt_delta or 0)
                new_betrayals = 1 if betrayal else 0
                status_list = special_status or []
                
                await conn.execute(
                    """
                    INSERT INTO dark_world_standings
                        (player_id, family_name, standing_score, favors_owed,
                         debts_owed, betrayal_count, special_status, last_interaction)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    player_id, family.value, new_standing, new_favors,
                    new_debts, new_betrayals, json.dumps(status_list),
                    datetime.utcnow()
                )
            
            # Return updated standing
            result = DarkWorldStanding(
                family_name=family,
                standing_score=new_standing,
                favors_owed=new_favors,
                debts_owed=new_debts,
                betrayal_count=new_betrayals,
                special_status=status_list,
                last_interaction=datetime.utcnow()
            )
        
        self._invalidate_cache(player_id)
        return result
    
    async def _initialize_player(self, player_id: UUID) -> None:
        """Initialize a new player's story state."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO story_players 
                    (player_id, broker_book_state, debt_of_flesh_state, 
                     surgeon_butcher_score)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (player_id) DO NOTHING
                """,
                player_id, json.dumps({}), json.dumps({}), 0.0
            )
            
            # Initialize neutral standings with all Dark World families
            for family in DarkWorldFamily:
                await conn.execute(
                    """
                    INSERT INTO dark_world_standings
                        (player_id, family_name, standing_score)
                    VALUES ($1, $2, 0.0)
                    ON CONFLICT (player_id, family_name) DO NOTHING
                    """,
                    player_id, family.value
                )
    
    async def _update_moral_score(
        self, 
        player_id: UUID, 
        moral_delta: float
    ) -> None:
        """Update the surgeon/butcher moral score."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                UPDATE story_players
                SET surgeon_butcher_score = GREATEST(-1.0, 
                    LEAST(1.0, surgeon_butcher_score + $1)),
                    updated_at = $2
                WHERE player_id = $3
                """,
                moral_delta, datetime.utcnow(), player_id
            )
    
    def _invalidate_cache(self, player_id: UUID) -> None:
        """Invalidate cached snapshot for a player."""
        cache_key = str(player_id)
        if cache_key in self._snapshot_cache:
            del self._snapshot_cache[cache_key]
