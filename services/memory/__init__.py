"""
Memory Service - 3-Tier NPC History System

Architecture (Multi-Model Consensus):
- Level 1 (GPU Cache): Last 12-20 turns + relationship/quest cards (instant access)
- Level 2 (Redis): 30-day rolling window with session summaries (<1ms latency)
- Level 3 (PostgreSQL): Lifetime archive with async writes ONLY (never blocks)

Critical Rules:
- NEVER query PostgreSQL on hot path (GPT-5 Pro + Gemini 2.5 Pro mandate)
- GPU cache for real-time NPC interactions
- Redis for nearline history (30 days)
- PostgreSQL for analytics and long-term storage only

Multi-model collaboration:
- GPT-5 Pro: Storage tier separation
- Gemini 2.5 Pro: Cache eviction policies
- Perplexity: Redis integration patterns (per-NPC keys, atomic updates)
"""

__version__ = "1.0.0"
__author__ = "AI Core Team (Multi-Model Collaboration)"

from .gpu_cache_manager import GPUCacheManager
from .redis_memory_manager import RedisMemoryManager
from .postgres_memory_archiver import PostgresMemoryArchiver
from .memory_cards import MemoryCards, RelationshipCard, QuestStateCard

__all__ = [
    "GPUCacheManager",
    "RedisMemoryManager",
    "PostgresMemoryArchiver",
    "MemoryCards",
    "RelationshipCard",
    "QuestStateCard",
]

