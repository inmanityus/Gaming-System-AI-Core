#!/usr/bin/env python3
"""Initialize Aurora PostgreSQL database"""
import boto3
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_credentials():
    """Get database credentials from Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret_arn = 'arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7'
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response['SecretString'])

def main():
    print("Getting database credentials...")
    creds = get_db_credentials()
    
    # First, create the database
    print("Creating database...")
    try:
        conn = psycopg2.connect(
            host='gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com',
            port=5432,
            database='postgres',
            user=creds['username'],
            password=creds['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE gaming_system_ai_core;")
        cur.close()
        conn.close()
        print("Database created successfully!")
    except psycopg2.errors.DuplicateDatabase:
        print("Database already exists")
    except Exception as e:
        print(f"Error creating database: {e}")
    
    # Now connect to the new database and create schema
    print("Creating schemas and tables...")
    conn = psycopg2.connect(
        host='gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com',
        port=5432,
        database='gaming_system_ai_core',
        user=creds['username'],
        password=creds['password']
    )
    cur = conn.cursor()
    
    # Create schemas
    schemas = ['audio_analytics', 'engagement', 'users', 'ethelred']
    for schema in schemas:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        print(f"Created schema: {schema}")
    
    # Create audio_metrics table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audio_analytics.audio_metrics (
            id SERIAL PRIMARY KEY,
            analysis_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            sample_rate INTEGER NOT NULL CHECK (sample_rate > 0),
            duration_seconds FLOAT NOT NULL CHECK (duration_seconds > 0),
            intelligibility_score FLOAT NOT NULL CHECK (intelligibility_score >= 0 AND intelligibility_score <= 1),
            confidence_level FLOAT CHECK (confidence_level >= 0 AND confidence_level <= 1),
            archetype VARCHAR(100),
            archetype_matches JSONB,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Created audio_metrics table")
    
    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audio_metrics_user_session ON audio_analytics.audio_metrics(user_id, session_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audio_metrics_created_at ON audio_analytics.audio_metrics(created_at DESC);")
    
    # Create archetype_profiles table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audio_analytics.archetype_profiles (
            id SERIAL PRIMARY KEY,
            archetype_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            frequency_profile JSONB NOT NULL,
            spectral_characteristics JSONB NOT NULL,
            temporal_patterns JSONB NOT NULL,
            active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Created archetype_profiles table")
    
    # Insert archetype profiles
    profiles = [
        ('vampire_alpha', 'Vampire archetype', '{"low_freq": 0.3, "mid_freq": 0.5, "high_freq": 0.2}', '{"resonance": 0.8}', '{"cadence": "slow"}'),
        ('zombie_beta', 'Zombie archetype', '{"low_freq": 0.6, "mid_freq": 0.3, "high_freq": 0.1}', '{"resonance": 0.2}', '{"cadence": "irregular"}'),
        ('werewolf_gamma', 'Werewolf archetype', '{"low_freq": 0.5, "mid_freq": 0.3, "high_freq": 0.2}', '{"resonance": 0.5}', '{"cadence": "variable"}')
    ]
    
    for name, desc, freq, spectral, temporal in profiles:
        cur.execute("""
            INSERT INTO audio_analytics.archetype_profiles 
            (archetype_name, description, frequency_profile, spectral_characteristics, temporal_patterns) 
            VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
            ON CONFLICT (archetype_name) DO NOTHING;
        """, (name, desc, freq, spectral, temporal))
    
    # Insert test data
    print("Inserting test data...")
    for i in range(1, 101):
        archetype = ['vampire_alpha', 'zombie_beta', 'werewolf_gamma'][i % 3]
        cur.execute("""
            INSERT INTO audio_analytics.audio_metrics 
            (user_id, session_id, sample_rate, duration_seconds, intelligibility_score, confidence_level, archetype, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (analysis_id) DO NOTHING;
        """, (
            'test_user_perf',
            f'session_{i}',
            48000,
            3.5,
            0.75 + (i % 20) * 0.01,
            0.8 + (i % 15) * 0.01,
            archetype,
            json.dumps({'test': True, 'index': i})
        ))
    
    # Create ethelred view
    cur.execute("""
        CREATE OR REPLACE VIEW ethelred.audio_metrics AS
        SELECT * FROM audio_analytics.audio_metrics;
    """)
    print("Created ethelred view")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM audio_analytics.audio_metrics;")
    count = cur.fetchone()[0]
    print(f"Total records in audio_metrics: {count}")
    
    cur.execute("SELECT COUNT(*) FROM audio_analytics.archetype_profiles;")
    count = cur.fetchone()[0]
    print(f"Total archetype profiles: {count}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("Database initialization complete!")

if __name__ == '__main__':
    main()
