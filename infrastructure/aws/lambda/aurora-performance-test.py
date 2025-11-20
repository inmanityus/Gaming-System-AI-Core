"""
Lambda function to test Aurora performance from within VPC
"""
import json
import boto3
import psycopg
from psycopg_pool import ConnectionPool
import time
import statistics
from datetime import datetime


def get_db_credentials(secret_arn):
    """Retrieve database credentials from Secrets Manager."""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response['SecretString'])


def measure_query_latency(conn, query, params=(), iterations=50):
    """Measure query latency over multiple iterations."""
    latencies = []
    
    for _ in range(iterations):
        start_time = time.perf_counter()
        
        with conn.cursor() as cur:
            cur.execute(query, params)
            cur.fetchall()
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)
    
    return {
        'mean': statistics.mean(latencies),
        'median': statistics.median(latencies),
        'p95': statistics.quantiles(latencies, n=20)[18],  # 95th percentile
        'p99': statistics.quantiles(latencies, n=100)[98], # 99th percentile
        'min': min(latencies),
        'max': max(latencies),
        'std': statistics.stdev(latencies) if len(latencies) > 1 else 0
    }


def lambda_handler(event, context):
    """Lambda handler to run performance tests."""
    # Get environment variables
    cluster_endpoint = event.get('cluster_endpoint', 
                                'gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com')
    read_endpoint = event.get('read_endpoint',
                             'gaming-system-aurora-db-cluster.cluster-ro-cal6eoegigyq.us-east-1.rds.amazonaws.com')
    secret_arn = event.get('secret_arn', 
                          'arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7')
    
    # Get credentials
    credentials = get_db_credentials(secret_arn)
    
    # Create connection
    conninfo = f"host={read_endpoint} port=5432 dbname=gaming_system_ai_core user={credentials['username']} password={credentials['password']} sslmode=require"
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    try:
        # Connect to database
        with psycopg.connect(conninfo) as conn:
            # Test 1: Simple SELECT
            results['tests']['simple_select'] = measure_query_latency(
                conn,
                "SELECT 1",
                iterations=100
            )
            
            # Test 2: Table scan with WHERE clause
            results['tests']['table_scan'] = measure_query_latency(
                conn,
                """
                SELECT analysis_id, intelligibility_score 
                FROM audio_analytics.audio_metrics 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
                """,
                ('test_user_perf',),
                iterations=50
            )
            
            # Test 3: Join query
            results['tests']['join_query'] = measure_query_latency(
                conn,
                """
                SELECT 
                    am.analysis_id,
                    am.intelligibility_score,
                    ap.archetype_name,
                    ap.description
                FROM audio_analytics.audio_metrics am
                JOIN audio_analytics.archetype_profiles ap 
                    ON am.archetype = ap.archetype_name
                WHERE am.created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
                LIMIT 20
                """,
                iterations=50
            )
            
            # Test 4: Aggregation query
            results['tests']['aggregation'] = measure_query_latency(
                conn,
                """
                SELECT 
                    user_id,
                    COUNT(*) as total_analyses,
                    AVG(intelligibility_score) as avg_score,
                    MAX(intelligibility_score) as max_score,
                    MIN(intelligibility_score) as min_score
                FROM audio_analytics.audio_metrics
                WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
                GROUP BY user_id
                HAVING COUNT(*) > 5
                """,
                iterations=25
            )
        
        # Check if meets <100ms requirement
        all_p95_values = []
        for test_name, metrics in results['tests'].items():
            all_p95_values.append(metrics['p95'])
        
        max_p95 = max(all_p95_values)
        avg_p95 = statistics.mean(all_p95_values)
        
        results['summary'] = {
            'average_p95_latency_ms': avg_p95,
            'maximum_p95_latency_ms': max_p95,
            'meets_requirement': max_p95 < 100,
            'status': 'PASS' if max_p95 < 100 else 'FAIL'
        }
        
        # Publish to CloudWatch
        cloudwatch = boto3.client('cloudwatch')
        metric_data = []
        
        for test_name, metrics in results['tests'].items():
            metric_data.append({
                'MetricName': f'{test_name}_p95_latency',
                'Value': metrics['p95'],
                'Unit': 'Milliseconds',
                'Timestamp': datetime.now()
            })
        
        cloudwatch.put_metric_data(
            Namespace='GamingSystem/Aurora/Performance',
            MetricData=metric_data
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(results, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
