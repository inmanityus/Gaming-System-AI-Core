"""
Simple synchronous ingestion for immediate use.
Ingests narrative documents without embeddings (text search only for now).
"""

import psycopg2
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_documents():
    """Ingest all narrative documents into PostgreSQL."""
    
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5443,
        user='postgres',
        password='Inn0vat1on!',
        database='gaming_system_ai_core'
    )
    cur = conn.cursor()
    
    docs_dir = Path('../../docs/narrative')
    stats = {'main': 0, 'guides': 0, 'experiences': 0, 'chunks': 0}
    
    try:
        # Main docs (00-09)
        for doc in sorted(docs_dir.glob('[0-9][0-9]-*.md')):
            logger.info(f"Ingesting: {doc.name}")
            content = doc.read_text(encoding='utf-8')
            title = content.split('\n')[0].strip('#').strip()
            
            # Simple insert (one chunk per doc for now)
            cur.execute("""
                INSERT INTO narrative_documents 
                (title, source_file, content, chunk_index, total_chunks, document_type, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_file, chunk_index) DO NOTHING
            """, (title, str(doc), content, 0, 1, 'main', '{}'))
            stats['main'] += 1
            stats['chunks'] += 1
        
        # Guides
        guides_dir = docs_dir / 'guides'
        for doc in guides_dir.glob('*.md'):
            if doc.name != 'README.md':
                logger.info(f"Ingesting: guides/{doc.name}")
                content = doc.read_text(encoding='utf-8')
                title = content.split('\n')[0].strip('#').strip() if content else doc.stem
                
                cur.execute("""
                    INSERT INTO narrative_documents 
                    (title, source_file, content, chunk_index, total_chunks, document_type, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_file, chunk_index) DO NOTHING
                """, (title, str(doc), content, 0, 1, 'guide', '{}'))
                stats['guides'] += 1
                stats['chunks'] += 1
        
        # Experiences
        exp_dir = docs_dir / 'experiences'
        for doc in exp_dir.glob('*.md'):
            logger.info(f"Ingesting: experiences/{doc.name}")
            content = doc.read_text(encoding='utf-8')
            title = content.split('\n')[0].strip('#').strip() if content else doc.stem
            
            cur.execute("""
                INSERT INTO narrative_documents 
                (title, source_file, content, chunk_index, total_chunks, document_type, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_file, chunk_index) DO NOTHING
            """, (title, str(doc), content, 0, 1, 'experience', '{}'))
            stats['experiences'] += 1
            stats['chunks'] += 1
        
        conn.commit()
        
        logger.info("\n" + "="*60)
        logger.info("✅ INGESTION COMPLETE")
        logger.info("="*60)
        logger.info(f"  Main docs:       {stats['main']}")
        logger.info(f"  Guide docs:      {stats['guides']}")
        logger.info(f"  Experience docs: {stats['experiences']}")
        logger.info(f"  Total chunks:    {stats['chunks']}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    ingest_documents()

