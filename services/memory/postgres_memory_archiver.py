"""
PostgreSQL Memory Archiver - Level 3 (Async-Only)
Coder: Claude Sonnet 4.5
Peer Review Lessons Applied

CRITICAL: NEVER blocks gameplay - async writes ONLY

Features:
- Queue-based async writes
- Batch processing (100ms windows, 100 events/batch)
- Connection pooling
- NEVER read during gameplay
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)


@dataclass
class WriteEvent:
    """Event to write to PostgreSQL."""
    event_type: str
    npc_id: str
    data: Dict[str, Any]
    queued_at: datetime


class PostgresMemoryArchiver:
    """
    Level 3: PostgreSQL (async writes ONLY).
    
    Background writer processes queue without blocking.
    """
    
    def __init__(
        self,
        db_host: Optional[str] = None,
        db_port: Optional[int] = None,
        db_name: Optional[str] = None,
        batch_size: int = 100,
        batch_window_ms: int = 100
    ):
        import os
        self.db_host = db_host or os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = db_port or int(os.getenv("POSTGRES_PORT", "5443"))
        self.db_name = db_name or os.getenv("POSTGRES_DB", "gaming_system_ai_core")
        self.batch_size = batch_size
        self.batch_window_ms = batch_window_ms
        
        self.pool: Optional[Any] = None
        self.write_queue: Optional[asyncio.Queue] = None
        self._writer_task: Optional[asyncio.Task] = None
        self._running = False
        
        self._total_queued = 0
        self._total_written = 0
        
        logger.info(f"PostgresMemoryArchiver initialized")
    
    async def initialize(self) -> None:
        """Initialize connection pool and writer."""
        if not asyncpg:
            raise RuntimeError("asyncpg not available")
        
        self.pool = await asyncpg.create_pool(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user="postgres",
            min_size=2,
            max_size=10
        )
        
        self.write_queue = asyncio.Queue(maxsize=10000)
        self._running = True
        self._writer_task = asyncio.create_task(self._background_writer())
        
        logger.info("✅ PostgreSQL archiver started")
    
    async def _background_writer(self) -> None:
        """Background batch writer."""
        while self._running:
            try:
                batch = []
                
                try:
                    first = await asyncio.wait_for(
                        self.write_queue.get(),
                        timeout=self.batch_window_ms / 1000.0
                    )
                    batch.append(first)
                    
                    while len(batch) < self.batch_size and not self.write_queue.empty():
                        batch.append(self.write_queue.get_nowait())
                
                except asyncio.TimeoutError:
                    continue
                
                if batch:
                    await self._write_batch(batch)
                    self._total_written += len(batch)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Writer error: {e}")
                await asyncio.sleep(1)
    
    async def _write_batch(self, batch: List[WriteEvent]) -> None:
        """Write batch to PostgreSQL."""
        if not self.pool:
            return
        
        async with self.pool.acquire() as conn:
            for event in batch:
                try:
                    if event.event_type == "conversation_turn":
                        await conn.execute(
                            """INSERT INTO npc_conversations 
                            (npc_id, player_id, turn_number, player_input, npc_response, timestamp, metadata)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT DO NOTHING""",
                            event.npc_id,
                            event.data.get('player_id'),
                            event.data.get('turn_number'),
                            event.data.get('player_input'),
                            event.data.get('npc_response'),
                            event.data.get('timestamp'),
                            json.dumps(event.data.get('metadata', {}))
                        )
                except Exception as e:
                    logger.error(f"Write failed: {e}")
    
    async def queue_conversation_turn(
        self,
        npc_id: str,
        player_id: str,
        turn_number: int,
        player_input: str,
        npc_response: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Queue conversation turn (non-blocking)."""
        if not self.write_queue:
            return
        
        event = WriteEvent(
            event_type="conversation_turn",
            npc_id=npc_id,
            data={
                'player_id': player_id,
                'turn_number': turn_number,
                'player_input': player_input,
                'npc_response': npc_response,
                'timestamp': timestamp or datetime.now(),
                'metadata': metadata or {}
            },
            queued_at=datetime.now()
        )
        
        try:
            self.write_queue.put_nowait(event)
            self._total_queued += 1
        except asyncio.QueueFull:
            logger.error("Write queue full")
    
    async def close(self) -> None:
        """Close archiver."""
        self._running = False
        
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
        
        if self.pool:
            await self.pool.close()
        
        logger.info(f"Archiver closed: queued={self._total_queued}, written={self._total_written}")

