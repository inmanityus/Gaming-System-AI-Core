#!/usr/bin/env python3
"""
Setup Gaming System AI Core Database
Creates database, schemas, tables, and initial data
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import argparse
from typing import Dict, Any
from pathlib import Path


def get_connection_params() -> Dict[str, Any]:
    """Get database connection parameters from environment or defaults."""
    return {
        'host': os.getenv('PGHOST', 'localhost'),
        'port': int(os.getenv('PGPORT', '5432')),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', 'Inn0vat1on!'),
    }


def create_database_if_not_exists(conn_params: Dict[str, Any], db_name: str) -> bool:
    """Create database if it doesn't exist."""
    # Connect to postgres database to create new database
    conn_params_copy = conn_params.copy()
    conn_params_copy['database'] = 'postgres'
    
    try:
        conn = psycopg2.connect(**conn_params_copy)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cur.fetchone() is not None
        
        if not exists:
            # Create database
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(db_name)
                )
            )
            print(f"✅ Created database: {db_name}")
            created = True
        else:
            print(f"ℹ️  Database already exists: {db_name}")
            created = False
        
        cur.close()
        conn.close()
        return created
        
    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)


def execute_sql_file(conn_params: Dict[str, Any], db_name: str, sql_file: Path):
    """Execute SQL file on the database."""
    conn_params_copy = conn_params.copy()
    conn_params_copy['database'] = db_name
    
    try:
        conn = psycopg2.connect(**conn_params_copy)
        cur = conn.cursor()
        
        # Read SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by major sections (CREATE SCHEMA, CREATE TABLE, etc.)
        # This is more reliable than executing the whole file at once
        sql_statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            # Skip comments and empty lines
            if line.strip().startswith('--') or not line.strip():
                continue
            
            # Skip \c command as we're already connected
            if line.strip().startswith('\\c'):
                continue
                
            current_statement.append(line)
            
            # Execute when we hit a semicolon at the end of a line
            if line.rstrip().endswith(';'):
                statement = '\n'.join(current_statement)
                if statement.strip():
                    sql_statements.append(statement)
                current_statement = []
        
        # Execute each statement
        total_statements = len(sql_statements)
        print(f"\n📝 Executing {total_statements} SQL statements...")
        
        for i, statement in enumerate(sql_statements):
            try:
                cur.execute(statement)
                # Show progress for long scripts
                if (i + 1) % 10 == 0 or (i + 1) == total_statements:
                    print(f"   Progress: {i + 1}/{total_statements} statements executed")
            except psycopg2.Error as e:
                print(f"\n❌ Error executing statement {i + 1}:")
                print(f"   Statement: {statement[:100]}...")
                print(f"   Error: {e}")
                conn.rollback()
                raise
        
        conn.commit()
        print(f"\n✅ Successfully executed all SQL statements")
        
        # Show summary of created objects
        cur.execute("""
            SELECT 
                schemaname,
                COUNT(*) as table_count
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            GROUP BY schemaname
            ORDER BY schemaname
        """)
        
        print("\n📊 Database Summary:")
        print("   Schemas and table counts:")
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[1]} tables")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error executing SQL file: {e}")
        sys.exit(1)


def verify_setup(conn_params: Dict[str, Any], db_name: str):
    """Verify the database setup is correct."""
    conn_params_copy = conn_params.copy()
    conn_params_copy['database'] = db_name
    
    try:
        conn = psycopg2.connect(**conn_params_copy)
        cur = conn.cursor()
        
        # Check schemas
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')
            ORDER BY schema_name
        """)
        schemas = [row[0] for row in cur.fetchall()]
        
        print("\n✅ Verification Results:")
        print(f"   Schemas created: {', '.join(schemas)}")
        
        # Check key tables
        key_tables = [
            ('audio_analytics', 'audio_metrics'),
            ('engagement', 'sessions'),
            ('localization', 'content'),
            ('language_system', 'tts_cache'),
            ('users', 'preferences')
        ]
        
        for schema, table in key_tables:
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (schema, table))
            exists = cur.fetchone()[0] > 0
            status = "✅" if exists else "❌"
            print(f"   {status} {schema}.{table}")
        
        # Check initial data
        cur.execute("SELECT COUNT(*) FROM audio_analytics.archetype_profiles")
        archetype_count = cur.fetchone()[0]
        print(f"\n   Initial data:")
        print(f"   - Archetype profiles: {archetype_count}")
        
        cur.execute("SELECT COUNT(*) FROM localization.language_stats")
        lang_count = cur.fetchone()[0]
        print(f"   - Language statistics: {lang_count}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Database setup completed successfully!")
        
    except psycopg2.Error as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)


def main():
    """Main function to setup the database."""
    parser = argparse.ArgumentParser(description='Setup Gaming System AI Core Database')
    parser.add_argument(
        '--db-name',
        default='gaming_system_ai_core',
        help='Database name to create (default: gaming_system_ai_core)'
    )
    parser.add_argument(
        '--sql-file',
        default='infrastructure/database/create_gaming_system_db.sql',
        help='Path to SQL file (default: infrastructure/database/create_gaming_system_db.sql)'
    )
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing database before creating'
    )
    
    args = parser.parse_args()
    
    # Get connection parameters
    conn_params = get_connection_params()
    
    print(f"🚀 Setting up Gaming System AI Core Database")
    print(f"   Host: {conn_params['host']}:{conn_params['port']}")
    print(f"   User: {conn_params['user']}")
    print(f"   Database: {args.db_name}")
    
    # Drop existing database if requested
    if args.drop_existing:
        print(f"\n⚠️  Dropping existing database: {args.db_name}")
        try:
            conn = psycopg2.connect(**{**conn_params, 'database': 'postgres'})
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            # Terminate existing connections
            cur.execute("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
            """, (args.db_name,))
            
            # Drop database
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(args.db_name)
                )
            )
            cur.close()
            conn.close()
            print(f"   Dropped database: {args.db_name}")
        except psycopg2.Error as e:
            print(f"   Warning: Could not drop database: {e}")
    
    # Create database
    create_database_if_not_exists(conn_params, args.db_name)
    
    # Execute SQL file
    sql_file = Path(args.sql_file)
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        sys.exit(1)
    
    execute_sql_file(conn_params, args.db_name, sql_file)
    
    # Verify setup
    verify_setup(conn_params, args.db_name)
    
    # Print connection info for tests
    print(f"\n📌 To use this database in tests, set these environment variables:")
    print(f"   export DB_HOST={conn_params['host']}")
    print(f"   export DB_PORT={conn_params['port']}")
    print(f"   export DB_NAME={args.db_name}")
    print(f"   export DB_USER={conn_params['user']}")
    print(f"   export DB_PASSWORD=<your_password>")
    
    print(f"\n   Or in Windows PowerShell:")
    print(f"   $env:DB_HOST = '{conn_params['host']}'")
    print(f"   $env:DB_PORT = '{conn_params['port']}'")
    print(f"   $env:DB_NAME = '{args.db_name}'")
    print(f"   $env:DB_USER = '{conn_params['user']}'")
    print(f"   $env:DB_PASSWORD = '<your_password>'")


if __name__ == '__main__':
    main()
