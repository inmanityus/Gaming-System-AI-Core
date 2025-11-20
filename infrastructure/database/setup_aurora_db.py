#!/usr/bin/env python3
"""
Setup Aurora Gaming System AI Core Database
Creates schemas, tables, and initial data
"""
import os
import sys
import json
import boto3
import psycopg2
from psycopg2 import sql
import argparse
from pathlib import Path


def get_aurora_credentials():
    """Get Aurora database credentials from Secrets Manager."""
    secret_arn = "arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7"
    
    client = boto3.client('secretsmanager', region_name='us-east-1')
    try:
        response = client.get_secret_value(SecretId=secret_arn)
        credentials = json.loads(response['SecretString'])
        return credentials
    except Exception as e:
        print(f"Error retrieving credentials: {e}")
        sys.exit(1)


def execute_sql_file(host: str, username: str, password: str, db_name: str, sql_file: Path):
    """Execute SQL file on the Aurora database."""
    try:
        print(f"Connecting to Aurora at {host}...")
        conn = psycopg2.connect(
            host=host,
            port=5432,
            database=db_name,
            user=username,
            password=password,
            connect_timeout=30,
            sslmode='require'
        )
        conn.autocommit = False
        cur = conn.cursor()
        
        print("Connected successfully!")
        
        # Read SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Remove database creation commands (already exists)
        # and process the SQL
        sql_lines = []
        skip_until_connect = False
        for line in sql_content.split('\n'):
            if 'CREATE DATABASE' in line or 'DROP DATABASE' in line:
                skip_until_connect = True
            elif '\\c gaming_system_ai_core' in line:
                skip_until_connect = False
                continue
            elif not skip_until_connect:
                sql_lines.append(line)
        
        sql_content = '\n'.join(sql_lines)
        
        # Execute the SQL
        print("Executing database schema...")
        cur.execute(sql_content)
        conn.commit()
        
        print("Database schema created successfully!")
        
        # Verify setup
        cur.execute("""
            SELECT 
                schema_name,
                (SELECT COUNT(*) FROM information_schema.tables 
                 WHERE table_schema = s.schema_name) as table_count
            FROM information_schema.schemata s
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')
            ORDER BY schema_name
        """)
        
        print("\nDatabase Summary:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} tables")
        
        # Check initial data
        cur.execute("SELECT COUNT(*) FROM audio_analytics.archetype_profiles")
        archetype_count = cur.fetchone()[0]
        print(f"\nInitial data:")
        print(f"  - Archetype profiles: {archetype_count}")
        
        cur.execute("SELECT COUNT(*) FROM localization.language_stats")
        lang_count = cur.fetchone()[0]
        print(f"  - Language statistics: {lang_count}")
        
        cur.close()
        conn.close()
        
        print("\nDatabase setup completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function to setup the Aurora database."""
    parser = argparse.ArgumentParser(description='Setup Aurora Gaming System Database')
    parser.add_argument(
        '--sql-file',
        default='infrastructure/database/create_gaming_system_db.sql',
        help='Path to SQL file'
    )
    
    args = parser.parse_args()
    
    # Get Aurora endpoint
    cluster_endpoint = "gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com"
    db_name = "gaming_system_ai_core"
    
    print("Setting up Aurora Gaming System AI Core Database")
    print(f"  Endpoint: {cluster_endpoint}")
    print(f"  Database: {db_name}")
    
    # Get credentials
    print("\nRetrieving credentials from Secrets Manager...")
    credentials = get_aurora_credentials()
    
    # Execute SQL file
    sql_file = Path(args.sql_file)
    if not sql_file.exists():
        print(f"Error: SQL file not found: {sql_file}")
        sys.exit(1)
    
    execute_sql_file(
        host=cluster_endpoint,
        username=credentials['username'],
        password=credentials['password'],
        db_name=db_name,
        sql_file=sql_file
    )
    
    # Print connection info
    print(f"\nConnection Information:")
    print(f"  Host: {cluster_endpoint}")
    print(f"  Port: 5432")
    print(f"  Database: {db_name}")
    print(f"  Username: {credentials['username']}")
    print(f"  Password: Stored in Secrets Manager")
    print(f"\nTo connect with psql:")
    print(f"  psql -h {cluster_endpoint} -U {credentials['username']} -d {db_name}")


if __name__ == '__main__':
    main()
