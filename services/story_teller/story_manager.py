"""
Story Manager - Core story node management and CRUD operations.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

# Type aliases for database connections
PostgreSQLPool = Any


class StoryNode:
    """Represents a story node with all necessary data."""
    
    def __init__(
        self,
        node_id: UUID,
        player_id: UUID,
        node_type: str,
        title: str,
        description: str,
        narrative_content: str,
        choices: List[Dict[str, Any]],
        status: str = "active",
        prerequisites: Optional[Dict[str, Any]] = None,
        consequences: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.node_id = node_id
        self.player_id = player_id
        self.node_type = node_type
        self.title = title
        self.description = description
        self.narrative_content = narrative_content
        self.choices = choices
        self.status = status
        self.prerequisites = prerequisites or {}
        self.consequences = consequences or {}
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "node_id": str(self.node_id),
            "player_id": str(self.player_id),
            "node_type": self.node_type,
            "title": self.title,
            "description": self.description,
            "narrative_content": self.narrative_content,
            "choices": self.choices,
            "status": self.status,
            "prerequisites": self.prerequisites,
            "consequences": self.consequences,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class StoryManager:
    """
    Manages story nodes and story progression.
    Handles CRUD operations for story content.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    async def create_story_node(
        self,
        player_id: UUID,
        node_type: str,
        title: str,
        description: str,
        narrative_content: str,
        choices: List[Dict[str, Any]],
        prerequisites: Optional[Dict[str, Any]] = None,
        consequences: Optional[Dict[str, Any]] = None,
    ) -> StoryNode:
        """
        Create a new story node.
        
        Args:
            player_id: Player UUID
            node_type: Type of story node (e.g., "dialogue", "action", "choice")
            title: Node title
            description: Node description
            narrative_content: Main story content
            choices: List of available choices
            prerequisites: Prerequisites for this node
            consequences: Consequences of this node
        
        Returns:
            Created story node
        """
        postgres = await self._get_postgres()
        
        query = """
            INSERT INTO story_nodes
            (player_id, node_type, title, description, narrative_content, choices, 
             status, prerequisites, consequences)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8::jsonb, $9::jsonb)
            RETURNING id, player_id, node_type, title, description, narrative_content,
                      choices, status, prerequisites, consequences, created_at, updated_at
        """
        
        result = await postgres.fetch(
            query,
            player_id,
            node_type,
            title,
            description,
            narrative_content,
            json.dumps(choices),
            "active",
            json.dumps(prerequisites or {}),
            json.dumps(consequences or {}),
        )
        
        return StoryNode(
            node_id=result["id"],
            player_id=result["player_id"],
            node_type=result["node_type"],
            title=result["title"],
            description=result["description"],
            narrative_content=result["narrative_content"],
            choices=json.loads(result["choices"]) if isinstance(result["choices"], str) else result["choices"],
            status=result["status"],
            prerequisites=json.loads(result["prerequisites"]) if isinstance(result["prerequisites"], str) else result["prerequisites"],
            consequences=json.loads(result["consequences"]) if isinstance(result["consequences"], str) else result["consequences"],
            created_at=result["created_at"].isoformat() if result["created_at"] else None,
            updated_at=result["updated_at"].isoformat() if result["updated_at"] else None,
        )
    
    async def get_story_node(self, node_id: UUID) -> Optional[StoryNode]:
        """
        Get a story node by ID.
        
        Args:
            node_id: Story node UUID
        
        Returns:
            Story node or None if not found
        """
        postgres = await self._get_postgres()
        
        query = """
            SELECT id, player_id, node_type, title, description, narrative_content,
                   choices, status, prerequisites, consequences, created_at, updated_at
            FROM story_nodes
            WHERE id = $1
        """
        
        result = await postgres.fetch(query, node_id)
        if not result:
            return None
        
        return StoryNode(
            node_id=result["id"],
            player_id=result["player_id"],
            node_type=result["node_type"],
            title=result["title"],
            description=result["description"],
            narrative_content=result["narrative_content"],
            choices=json.loads(result["choices"]) if isinstance(result["choices"], str) else result["choices"],
            status=result["status"],
            prerequisites=json.loads(result["prerequisites"]) if isinstance(result["prerequisites"], str) else result["prerequisites"],
            consequences=json.loads(result["consequences"]) if isinstance(result["consequences"], str) else result["consequences"],
            created_at=result["created_at"].isoformat() if result["created_at"] else None,
            updated_at=result["updated_at"].isoformat() if result["updated_at"] else None,
        )
    
    async def get_player_story_nodes(
        self, 
        player_id: UUID, 
        status: Optional[str] = None,
        node_type: Optional[str] = None
    ) -> List[StoryNode]:
        """
        Get all story nodes for a player.
        
        Args:
            player_id: Player UUID
            status: Optional status filter
            node_type: Optional node type filter
        
        Returns:
            List of story nodes
        """
        postgres = await self._get_postgres()
        
        conditions = ["player_id = $1"]
        params = [player_id]
        param_idx = 2
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if node_type:
            conditions.append(f"node_type = ${param_idx}")
            params.append(node_type)
            param_idx += 1
        
        query = f"""
            SELECT id, player_id, node_type, title, description, narrative_content,
                   choices, status, prerequisites, consequences, created_at, updated_at
            FROM story_nodes
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
        """
        
        results = await postgres.fetch_all(query, *params)
        
        nodes = []
        for result in results:
            nodes.append(StoryNode(
                node_id=result["id"],
                player_id=result["player_id"],
                node_type=result["node_type"],
                title=result["title"],
                description=result["description"],
                narrative_content=result["narrative_content"],
                choices=json.loads(result["choices"]) if isinstance(result["choices"], str) else result["choices"],
                status=result["status"],
                prerequisites=json.loads(result["prerequisites"]) if isinstance(result["prerequisites"], str) else result["prerequisites"],
                consequences=json.loads(result["consequences"]) if isinstance(result["consequences"], str) else result["consequences"],
                created_at=result["created_at"].isoformat() if result["created_at"] else None,
                updated_at=result["updated_at"].isoformat() if result["updated_at"] else None,
            ))
        
        return nodes
    
    async def update_story_node(
        self,
        node_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        narrative_content: Optional[str] = None,
        choices: Optional[List[Dict[str, Any]]] = None,
        status: Optional[str] = None,
        prerequisites: Optional[Dict[str, Any]] = None,
        consequences: Optional[Dict[str, Any]] = None,
    ) -> Optional[StoryNode]:
        """
        Update a story node.
        
        Args:
            node_id: Story node UUID
            title: New title
            description: New description
            narrative_content: New narrative content
            choices: New choices list
            status: New status
            prerequisites: New prerequisites
            consequences: New consequences
        
        Returns:
            Updated story node or None if not found
        """
        postgres = await self._get_postgres()
        
        updates = []
        params = []
        param_idx = 2  # Start after node_id
        
        if title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(title)
            param_idx += 1
        
        if description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(description)
            param_idx += 1
        
        if narrative_content is not None:
            updates.append(f"narrative_content = ${param_idx}")
            params.append(narrative_content)
            param_idx += 1
        
        if choices is not None:
            updates.append(f"choices = ${param_idx}::jsonb")
            params.append(json.dumps(choices))
            param_idx += 1
        
        if status is not None:
            updates.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if prerequisites is not None:
            updates.append(f"prerequisites = ${param_idx}::jsonb")
            params.append(json.dumps(prerequisites))
            param_idx += 1
        
        if consequences is not None:
            updates.append(f"consequences = ${param_idx}::jsonb")
            params.append(json.dumps(consequences))
            param_idx += 1
        
        if not updates:
            return await self.get_story_node(node_id)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"""
            UPDATE story_nodes
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING id, player_id, node_type, title, description, narrative_content,
                      choices, status, prerequisites, consequences, created_at, updated_at
        """
        
        params.insert(0, node_id)
        result = await postgres.fetch(query, *params)
        
        if not result:
            return None
        
        return StoryNode(
            node_id=result["id"],
            player_id=result["player_id"],
            node_type=result["node_type"],
            title=result["title"],
            description=result["description"],
            narrative_content=result["narrative_content"],
            choices=json.loads(result["choices"]) if isinstance(result["choices"], str) else result["choices"],
            status=result["status"],
            prerequisites=json.loads(result["prerequisites"]) if isinstance(result["prerequisites"], str) else result["prerequisites"],
            consequences=json.loads(result["consequences"]) if isinstance(result["consequences"], str) else result["consequences"],
            created_at=result["created_at"].isoformat() if result["created_at"] else None,
            updated_at=result["updated_at"].isoformat() if result["updated_at"] else None,
        )
    
    async def delete_story_node(self, node_id: UUID) -> bool:
        """
        Delete a story node (soft delete by setting status to 'deleted').
        
        Args:
            node_id: Story node UUID
        
        Returns:
            True if node was deleted
        """
        postgres = await self._get_postgres()
        
        query = """
            UPDATE story_nodes
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        result = await postgres.execute(query, node_id)
        return result is not None
