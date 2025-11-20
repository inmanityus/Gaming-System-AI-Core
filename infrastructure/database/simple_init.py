import boto3
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

print("Starting database initialization...")

try:
    # Get credentials
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret = client.get_secret_value(SecretId='arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7')
    creds = json.loads(secret['SecretString'])
    print("Got credentials")
    
    # Create database
    conn = psycopg2.connect(
        host='gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com',
        port=5432,
        database='postgres',
        user=creds['username'],
        password=creds['password']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        cur.execute('CREATE DATABASE gaming_system_ai_core;')
        print('Database created!')
    except psycopg2.errors.DuplicateDatabase:
        print('Database already exists')
    
    cur.close()
    conn.close()
    
    # Connect to new database and create minimal schema
    conn = psycopg2.connect(
        host='gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com',
        port=5432,
        database='gaming_system_ai_core',
        user=creds['username'],
        password=creds['password']
    )
    cur = conn.cursor()
    
    # Create schema
    cur.execute('CREATE SCHEMA IF NOT EXISTS audio_analytics;')
    cur.execute('CREATE SCHEMA IF NOT EXISTS ethelred;')
    print('Schemas created')
    
    # Create simple table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS audio_analytics.audio_metrics (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(255),
        intelligibility_score FLOAT
    );
    ''')
    print('Table created')
    
    # Insert test data
    cur.execute("INSERT INTO audio_analytics.audio_metrics (user_id, intelligibility_score) VALUES ('test_user_perf', 0.85);")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('Database initialization complete!')
    
except Exception as e:
    print(f'Error: {str(e)}')
