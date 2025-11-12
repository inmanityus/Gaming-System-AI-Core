#!/usr/bin/env python3
"""
Database Initialization Script
Creates tables and indexes for report storage.

P0-5: PostgreSQL schema initialization
"""

import asyncio
import psycopg
from psycopg.rows import dict_row
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


async def init_database(
    host: str = 'localhost',
    port: int = 5443,
    database: str = 'body_broker_qa',
    user: str = 'postgres',
    password: str = None
):
    """Initialize database with schema using psycopg3."""
    
    try:
        # Build connection string
        conninfo = f"host={host} port={port} dbname={database} user={user}"
        if password:
            conninfo += f" password={password}"
        
        # Connect to database
        logger.info(f"Connecting to database: {host}:{port}/{database}")
        conn = await psycopg.AsyncConnection.connect(conninfo)
        
        logger.info("Database connected successfully")
        
        # Load schema file
        schema_file = Path(__file__).parent / 'schema.sql'
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        logger.info(f"Loading schema from: {schema_file}")
        schema_sql = schema_file.read_text()
        
        # Execute schema
        logger.info("Executing schema...")
        await conn.execute(schema_sql)
        
        logger.info("Schema applied successfully")
        
        # Verify tables created
        conn.row_factory = dict_row
        cursor = await conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('reports', 'report_artifacts', 'report_events')
        """)
        
        tables = await cursor.fetchall()
        logger.info(f"Tables created: {[t['table_name'] for t in tables]}")
        
        # Close connection
        await conn.close()
        logger.info("Database initialization complete")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import os
    import platform
    
    # Get database credentials from environment
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', '5443'))
    database = os.getenv('DB_NAME', 'body_broker_qa')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')
    
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)
    logger.info(f"Host: {host}:{port}")
    logger.info(f"Database: {database}")
    logger.info(f"User: {user}")
    logger.info("=" * 60)
    
    # Fix for Windows ProactorEventLoop issue with psycopg
    if platform.system() == 'Windows':
        # Use SelectorEventLoop on Windows for psycopg compatibility
        import selectors
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Using SelectorEventLoop for Windows compatibility")
    
    success = asyncio.run(init_database(host, port, database, user, password))
    
    if success:
        logger.info("✅ Database initialization successful")
        sys.exit(0)
    else:
        logger.error("❌ Database initialization failed")
        sys.exit(1)

