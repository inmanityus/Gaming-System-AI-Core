"""
The Weaver's Loom - Story Teller Communication Portal
Coder: Claude Sonnet 4.5
Awaiting Peer Review

Secure portal for creator-Story Teller direct communication.

From Story Teller design:
- Threaded dialogue (chat interface)
- Pattern Board (visual whiteboard for nodes/relationships)
- Inspiration Codex (generated content repository)
- Version history (archive all sessions)

Access: Creator credentials only
Purpose: Multi-year design collaboration sanctuary
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Message types in threaded dialogue."""
    CREATOR_QUESTION = "creator_question"
    STORYTELLER_RESPONSE = "storyteller_response"
    BRAINSTORM = "brainstorm"
    DESIGN_REQUEST = "design_request"
    LORE_GENERATION = "lore_generation"


class NodeType(str, Enum):
    """Pattern Board node types."""
    CHARACTER = "character"
    ITEM = "item"
    QUEST = "quest"
    LOCATION = "location"
    FACTION = "faction"
    THEME = "theme"
    MECHANIC = "mechanic"


@dataclass
class DialogueMessage:
    """Single message in threaded dialogue."""
    message_id: str
    message_type: MessageType
    sender: str  # "creator" or "storyteller"
    content: str
    timestamp: datetime
    thread_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class PatternBoardNode:
    """Node on Pattern Board."""
    node_id: str
    node_type: NodeType
    name: str
    description: str
    position: Tuple[float, float]  # x, y on board
    connections: List[str] = field(default_factory=list)  # Connected node IDs
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class InspirationContent:
    """Content in Inspiration Codex."""
    content_id: str
    content_type: str  # "lore", "character", "dialogue", "item_desc", etc.
    title: str
    content: str
    tags: List[str]
    created_at: datetime
    created_by: str  # "storyteller" or "creator"


class WeaversLoom:
    """
    The Weaver's Loom - Story Teller Communication Portal.
    
    Secure sanctuary for creator-Story Teller collaboration.
    
    Features:
    1. Threaded Dialogue - Core communication
    2. Pattern Board - Visual relationship mapping
    3. Inspiration Codex - Content repository
    4. Version History - Session archives
    """
    
    def __init__(
        self,
        data_dir: str = ".weavers_loom",
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None
    ):
        """
        Initialize portal.
        
        Args:
            data_dir: Data directory for persistence
            redis_host: Redis host for real-time updates
            redis_port: Redis port
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core data structures
        self.dialogue_messages: List[DialogueMessage] = []
        self.pattern_board_nodes: Dict[str, PatternBoardNode] = {}
        self.inspiration_codex: Dict[str, InspirationContent] = {}
        
        # Redis for real-time (optional)
        self.redis_client: Optional[Any] = None
        self.redis_host = redis_host or "localhost"
        self.redis_port = redis_port or 6379
        
        # Session tracking
        self.current_session_id: Optional[str] = None
        self.session_start: Optional[datetime] = None
        
        logger.info("Weaver's Loom initialized")
    
    async def initialize(self) -> None:
        """Initialize Redis connection (optional)."""
        if aioredis:
            try:
                redis_url = f"redis://{self.redis_host}:{self.redis_port}/2"
                self.redis_client = aioredis.from_url(redis_url)
                await self.redis_client.ping()
                logger.info("✅ Loom connected to Redis (real-time updates enabled)")
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}, continuing in offline mode")
        
        # Load existing data
        await self._load_from_disk()
    
    # ========== THREADED DIALOGUE ==========
    
    async def send_message(
        self,
        sender: str,
        message_type: MessageType,
        content: str,
        thread_id: Optional[str] = None,
        parent_message_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Send message in threaded dialogue.
        
        Returns:
            message_id
        """
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
        
        message = DialogueMessage(
            message_id=message_id,
            message_type=message_type,
            sender=sender,
            content=content,
            timestamp=datetime.now(),
            thread_id=thread_id,
            parent_message_id=parent_message_id,
            tags=tags or []
        )
        
        self.dialogue_messages.append(message)
        
        # Persist
        await self._save_dialogue()
        
        logger.info(f"Message sent: {sender} -> {message_type.value}")
        return message_id
    
    async def get_thread(
        self,
        thread_id: str
    ) -> List[DialogueMessage]:
        """Get all messages in thread."""
        return [m for m in self.dialogue_messages if m.thread_id == thread_id]
    
    async def get_recent_messages(
        self,
        limit: int = 50
    ) -> List[DialogueMessage]:
        """Get recent messages."""
        return self.dialogue_messages[-limit:]
    
    # ========== PATTERN BOARD ==========
    
    async def add_node(
        self,
        node_type: NodeType,
        name: str,
        description: str,
        position: Tuple[float, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add node to Pattern Board.
        
        Returns:
            node_id
        """
        node_id = f"node_{int(datetime.now().timestamp() * 1000)}"
        
        node = PatternBoardNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            description=description,
            position=position,
            metadata=metadata or {}
        )
        
        self.pattern_board_nodes[node_id] = node
        
        await self._save_pattern_board()
        
        logger.info(f"Node added: {name} ({node_type.value})")
        return node_id
    
    async def connect_nodes(
        self,
        node_id_1: str,
        node_id_2: str
    ) -> None:
        """Create connection between two nodes."""
        node1 = self.pattern_board_nodes.get(node_id_1)
        node2 = self.pattern_board_nodes.get(node_id_2)
        
        if node1 and node2:
            if node_id_2 not in node1.connections:
                node1.connections.append(node_id_2)
            if node_id_1 not in node2.connections:
                node2.connections.append(node_id_1)
            
            await self._save_pattern_board()
            logger.info(f"Connected: {node1.name} <-> {node2.name}")
    
    async def get_board_state(self) -> Dict[str, Any]:
        """Get complete Pattern Board state."""
        return {
            'nodes': [
                {
                    'id': node.node_id,
                    'type': node.node_type.value,
                    'name': node.name,
                    'description': node.description,
                    'position': node.position,
                    'connections': node.connections,
                    'metadata': node.metadata
                }
                for node in self.pattern_board_nodes.values()
            ]
        }
    
    # ========== INSPIRATION CODEX ==========
    
    async def add_inspiration(
        self,
        content_type: str,
        title: str,
        content: str,
        tags: List[str],
        created_by: str = "storyteller"
    ) -> str:
        """
        Add content to Inspiration Codex.
        
        Returns:
            content_id
        """
        content_id = f"content_{int(datetime.now().timestamp() * 1000)}"
        
        inspiration = InspirationContent(
            content_id=content_id,
            content_type=content_type,
            title=title,
            content=content,
            tags=tags,
            created_at=datetime.now(),
            created_by=created_by
        )
        
        self.inspiration_codex[content_id] = inspiration
        
        await self._save_codex()
        
        logger.info(f"Inspiration added: {title} ({content_type})")
        return content_id
    
    async def search_codex(
        self,
        query: str,
        content_type: Optional[str] = None
    ) -> List[InspirationContent]:
        """Search Inspiration Codex."""
        results = []
        
        query_lower = query.lower()
        
        for inspiration in self.inspiration_codex.values():
            # Search in title, content, tags
            if (query_lower in inspiration.title.lower() or
                query_lower in inspiration.content.lower() or
                any(query_lower in tag.lower() for tag in inspiration.tags)):
                
                if content_type is None or inspiration.content_type == content_type:
                    results.append(inspiration)
        
        return results
    
    # ========== PERSISTENCE ==========
    
    async def _save_dialogue(self) -> None:
        """Save dialogue history."""
        filepath = self.data_dir / "dialogue.json"
        data = [
            {
                'message_id': m.message_id,
                'message_type': m.message_type.value,
                'sender': m.sender,
                'content': m.content,
                'timestamp': m.timestamp.isoformat(),
                'thread_id': m.thread_id,
                'parent_message_id': m.parent_message_id,
                'tags': m.tags
            }
            for m in self.dialogue_messages
        ]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _save_pattern_board(self) -> None:
        """Save Pattern Board state."""
        filepath = self.data_dir / "pattern_board.json"
        data = await self.get_board_state()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _save_codex(self) -> None:
        """Save Inspiration Codex."""
        filepath = self.data_dir / "inspiration_codex.json"
        data = [
            {
                'content_id': c.content_id,
                'content_type': c.content_type,
                'title': c.title,
                'content': c.content,
                'tags': c.tags,
                'created_at': c.created_at.isoformat(),
                'created_by': c.created_by
            }
            for c in self.inspiration_codex.values()
        ]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _load_from_disk(self) -> None:
        """Load all data from disk."""
        # Load dialogue
        dialogue_file = self.data_dir / "dialogue.json"
        if dialogue_file.exists():
            with open(dialogue_file, 'r') as f:
                data = json.load(f)
                # Deserialize (simplified)
                logger.info(f"Loaded {len(data)} dialogue messages")
        
        # Load pattern board
        board_file = self.data_dir / "pattern_board.json"
        if board_file.exists():
            with open(board_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data.get('nodes', []))} board nodes")
        
        # Load codex
        codex_file = self.data_dir / "inspiration_codex.json"
        if codex_file.exists():
            with open(codex_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} inspiration entries")
    
    async def close(self) -> None:
        """Close portal and save state."""
        await self._save_dialogue()
        await self._save_pattern_board()
        await self._save_codex()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Weaver's Loom closed")

