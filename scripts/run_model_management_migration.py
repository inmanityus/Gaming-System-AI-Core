"""
Run Model Management migration.
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def run_migration():
    """Run migration SQL file."""
    # Read migration file
    migration_file = Path("database/migrations/006_model_management.sql")
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Connect to database
    # Use same connection settings as connection_pool.py
    # Try multiple password options
    passwords = [
        os.getenv("POSTGRES_PASSWORD"),
        os.getenv("DB_PASSWORD"),
        "postgres",  # Default
        "Inn0vat1on!"  # From startup script
    ]
    
    conn = None
    # Try databases in order of preference
    databases = [
        "gaming_system_ai_core",  # Project-specific database
        "postgres",  # Default PostgreSQL database
        "befreefitness"  # Another available database
    ]
    
    for database in databases:
        for password in passwords:
            if password:
                try:
                    conn = await asyncpg.connect(
                        host="localhost",
                        port=5443,
                        user="postgres",
                        password=password,
                        database=database
                    )
                    print(f"Connected to database: {database}")
                    break
                except Exception:
                    continue
        if conn:
            break
    
    if not conn:
        raise Exception("Could not connect to database with any password")
    
    try:
        # Execute migration
        await conn.execute(sql)
        print("Migration executed successfully")
    except Exception as e:
        print(f"Migration error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())

