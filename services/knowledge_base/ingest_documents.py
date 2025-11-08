"""
Knowledge Base Document Ingestion Pipeline
Ingests 23 narrative documents into PostgreSQL with pgvector embeddings.

Documents:
- 7 main narrative docs (00-OVERVIEW through 06-CROSS-WORLD-CONSISTENCY)
- 6 guides (emotional-storytelling, magic-systems, creatures, etc.)
- 10 experiences (dungeon-diving, portals, battles, etc.)
"""

import asyncio
import asyncpg
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple
import hashlib
import logging

# Embedding generation (AWS Bedrock Titan or OpenAI)
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Ingests narrative documents into Knowledge Base with embeddings."""
    
    def __init__(self):
        self.postgres_pool = None
        self.embedding_client = None
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        
        # Initialize embedding client
        if AWS_AVAILABLE:
            self.embedding_client = boto3.client('bedrock-runtime', region_name='us-east-1')
            self.embedding_model = 'amazon.titan-embed-text-v1'
            logger.info("Using AWS Bedrock Titan for embeddings")
        elif OPENAI_AVAILABLE:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.embedding_model = 'text-embedding-ada-002'
            logger.info("Using OpenAI ada-002 for embeddings")
        else:
            logger.warning("No embedding client available - will store documents without embeddings")
    
    async def connect_db(self):
        """Connect to PostgreSQL with pgvector."""
        self.postgres_pool = await asyncpg.create_pool(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5443')),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'Inn0vat1on!'),
            database=os.getenv('POSTGRES_DB', 'gaming_system_ai_core'),
            min_size=2,
            max_size=10
        )
        logger.info("Connected to PostgreSQL with pgvector")
    
    async def close_db(self):
        """Close database connection."""
        if self.postgres_pool:
            await self.postgres_pool.close()
    
    def chunk_document(self, content: str) -> List[str]:
        """
        Split document into chunks with overlap.
        Preserves paragraph boundaries when possible.
        """
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # Try to break at paragraph boundary
            if end < len(content):
                # Look for double newline (paragraph break)
                paragraph_break = content.rfind('\n\n', start, end)
                if paragraph_break != -1 and paragraph_break > start + self.chunk_size // 2:
                    end = paragraph_break
                else:
                    # Look for single newline
                    newline = content.rfind('\n', start, end)
                    if newline != -1 and newline > start + self.chunk_size // 2:
                        end = newline
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move forward with overlap
            start = end - self.chunk_overlap if end < len(content) else end
        
        return chunks
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        if not self.embedding_client:
            # Return zero vector if no client
            return [0.0] * 1536
        
        try:
            if AWS_AVAILABLE and isinstance(self.embedding_client, boto3.client.__class__):
                # AWS Bedrock Titan
                response = self.embedding_client.invoke_model(
                    modelId='amazon.titan-embed-text-v1',
                    body=json.dumps({'inputText': text[:8000]})  # Titan limit
                )
                result = json.loads(response['body'].read())
                return result['embedding']
            
            elif OPENAI_AVAILABLE:
                # OpenAI ada-002
                response = await openai.Embedding.acreate(
                    input=text[:8000],  # Token limit
                    model='text-embedding-ada-002'
                )
                return response['data'][0]['embedding']
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * 1536
    
    async def ingest_document(
        self,
        file_path: Path,
        document_type: str
    ) -> int:
        """
        Ingest single document into knowledge base.
        
        Args:
            file_path: Path to markdown file
            document_type: 'main', 'guide', or 'experience'
        
        Returns:
            Number of chunks inserted
        """
        logger.info(f"Ingesting: {file_path.name} (type: {document_type})")
        
        # Read document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first line
        lines = content.split('\n')
        title = lines[0].strip('#').strip() if lines else file_path.stem
        
        # Chunk document
        chunks = self.chunk_document(content)
        logger.info(f"  Split into {len(chunks)} chunks")
        
        # Insert chunks with embeddings
        inserted = 0
        async with self.postgres_pool.acquire() as conn:
            for idx, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.generate_embedding(chunk)
                
                # Insert into database
                await conn.execute(
                    """
                    INSERT INTO narrative_documents 
                    (title, source_file, content, chunk_index, total_chunks, 
                     document_type, embedding, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (source_file, chunk_index) DO UPDATE
                    SET content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    title,
                    str(file_path),
                    chunk,
                    idx,
                    len(chunks),
                    document_type,
                    embedding,
                    json.dumps({'file_name': file_path.name})
                )
                inserted += 1
        
        logger.info(f"  ✅ Inserted {inserted} chunks")
        return inserted
    
    async def ingest_all_documents(self, docs_dir: Path) -> Dict[str, int]:
        """
        Ingest all narrative documents.
        
        Returns:
            Statistics about ingestion
        """
        stats = {
            'main_docs': 0,
            'guides': 0,
            'experiences': 0,
            'total_chunks': 0
        }
        
        # Main narrative docs (00-06)
        main_docs = sorted(docs_dir.glob('[0-9][0-9]-*.md'))
        for doc in main_docs:
            chunks = await self.ingest_document(doc, 'main')
            stats['main_docs'] += 1
            stats['total_chunks'] += chunks
        
        # Guide docs
        guides_dir = docs_dir / 'guides'
        if guides_dir.exists():
            for doc in guides_dir.glob('*.md'):
                if doc.name != 'README.md':  # Skip README
                    chunks = await self.ingest_document(doc, 'guide')
                    stats['guides'] += 1
                    stats['total_chunks'] += chunks
        
        # Experience docs
        experiences_dir = docs_dir / 'experiences'
        if experiences_dir.exists():
            for doc in experiences_dir.glob('*.md'):
                chunks = await self.ingest_document(doc, 'experience')
                stats['experiences'] += 1
                stats['total_chunks'] += chunks
        
        return stats
    
    async def run(self):
        """Run complete ingestion pipeline."""
        try:
            logger.info("🚀 Starting Knowledge Base ingestion pipeline")
            
            # Connect to database
            await self.connect_db()
            
            # Find narrative docs directory
            docs_dir = Path('docs/narrative')
            if not docs_dir.exists():
                raise FileNotFoundError(f"Narrative docs directory not found: {docs_dir}")
            
            # Ingest all documents
            stats = await self.ingest_all_documents(docs_dir)
            
            # Report results
            logger.info("\n" + "="*60)
            logger.info("📊 INGESTION COMPLETE")
            logger.info("="*60)
            logger.info(f"  Main docs:        {stats['main_docs']}")
            logger.info(f"  Guide docs:       {stats['guides']}")
            logger.info(f"  Experience docs:  {stats['experiences']}")
            logger.info(f"  Total documents:  {stats['main_docs'] + stats['guides'] + stats['experiences']}")
            logger.info(f"  Total chunks:     {stats['total_chunks']}")
            logger.info("="*60)
            logger.info("✅ Knowledge Base ready for storyteller!")
            
            return stats
        
        finally:
            await self.close_db()


async def main():
    """Main entry point."""
    pipeline = DocumentIngestionPipeline()
    await pipeline.run()


if __name__ == '__main__':
    asyncio.run(main())

