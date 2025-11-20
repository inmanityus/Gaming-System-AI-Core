"""
Aurora PostgreSQL Performance Testing
Tests that database latency meets the <100ms requirement
"""
import psycopg
from psycopg_pool import ConnectionPool
import boto3
import json
import numpy as np
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor


class AuroraPerformanceTester:
    def __init__(self):
        self.session = boto3.Session()
        self.secrets_client = self.session.client('secretsmanager')
        self.cloudwatch_client = self.session.client('cloudwatch')
        self.rds_client = self.session.client('rds')
        
    def get_db_credentials(self, secret_arn: str) -> Dict[str, str]:
        """Retrieve database credentials from Secrets Manager."""
        response = self.secrets_client.get_secret_value(SecretId=secret_arn)
        return json.loads(response['SecretString'])
    
    def create_connection_pool(self, endpoint: str, credentials: Dict[str, str]) -> ConnectionPool:
        """Create connection pool to Aurora cluster."""
        conninfo = f"host={endpoint} port=5432 dbname=gaming_system_ai_core user={credentials['username']} password={credentials['password']}"
        return ConnectionPool(
            conninfo,
            min_size=10,
            max_size=20,
            timeout=10,
            max_waiting=10
        )
    
    def measure_query_latency(
        self,
        pool: ConnectionPool,
        query: str,
        params: tuple = (),
        iterations: int = 100
    ) -> Dict[str, float]:
        """Measure query latency over multiple iterations."""
        latencies = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    cur.fetchall()
            
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        return {
            'mean': np.mean(latencies),
            'median': np.median(latencies),
            'p95': np.percentile(latencies, 95),
            'p99': np.percentile(latencies, 99),
            'min': np.min(latencies),
            'max': np.max(latencies),
            'std': np.std(latencies)
        }
    
    def test_simple_queries(self, pool: ConnectionPool) -> Dict[str, Dict]:
        """Test latency for simple queries."""
        results = {}
        
        # Test 1: Simple SELECT
        print("Testing simple SELECT...")
        results['simple_select'] = self.measure_query_latency(
            pool,
            "SELECT 1",
            iterations=200
        )
        
        # Test 2: Table scan with WHERE clause
        print("Testing table scan with WHERE...")
        results['table_scan'] = self.measure_query_latency(
            pool,
            """
            SELECT analysis_id, intelligibility_score 
            FROM audio_analytics.audio_metrics 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 10
            """,
            ('test_user_perf',),
            iterations=100
        )
        
        # Test 3: Join query
        print("Testing join query...")
        results['join_query'] = self.measure_query_latency(
            pool,
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
            iterations=100
        )
        
        # Test 4: Aggregation query
        print("Testing aggregation query...")
        results['aggregation'] = self.measure_query_latency(
            pool,
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
            iterations=50
        )
        
        return results
    
    def test_write_performance(self, pool: ConnectionPool) -> Dict[str, Dict]:
        """Test write operation latency."""
        results = {}
        
        # Test single INSERT
        print("Testing single INSERT...")
        single_inserts = []
        for i in range(50):
            start_time = time.perf_counter()
            
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO audio_analytics.audio_metrics 
                        (user_id, session_id, sample_rate, duration_seconds, 
                         intelligibility_score, confidence_level, archetype, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (f'perf_user_{i}', f'session_{i}', 48000, 3.5, 
                         0.85, 0.92, 'vampire_alpha', psycopg.types.json.Json({'test': 'perf'}))
                    )
            
            end_time = time.perf_counter()
            single_inserts.append((end_time - start_time) * 1000)
        
        results['single_insert'] = {
            'mean': np.mean(single_inserts),
            'median': np.median(single_inserts),
            'p95': np.percentile(single_inserts, 95),
            'p99': np.percentile(single_inserts, 99),
            'min': np.min(single_inserts),
            'max': np.max(single_inserts),
            'std': np.std(single_inserts)
        }
        
        # Test batch INSERT
        print("Testing batch INSERT...")
        batch_sizes = [10, 50, 100]
        
        for batch_size in batch_sizes:
            batch_latencies = []
            
            for iteration in range(10):
                records = [
                    (f'batch_user_{iteration}_{i}', f'batch_session_{iteration}_{i}', 
                     48000, 3.5, 0.85, 0.92, 'zombie_beta', psycopg.types.json.Json({'batch': True}))
                    for i in range(batch_size)
                ]
                
                start_time = time.perf_counter()
                
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.executemany(
                            """
                            INSERT INTO audio_analytics.audio_metrics 
                            (user_id, session_id, sample_rate, duration_seconds, 
                             intelligibility_score, confidence_level, archetype, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            records
                        )
                
                end_time = time.perf_counter()
                batch_latencies.append((end_time - start_time) * 1000)
            
            results[f'batch_insert_{batch_size}'] = {
                'mean': np.mean(batch_latencies),
                'median': np.median(batch_latencies),
                'p95': np.percentile(batch_latencies, 95),
                'p99': np.percentile(batch_latencies, 99),
                'records_per_second': (batch_size * 1000) / np.mean(batch_latencies)
            }
        
        return results
    
    def test_connection_pooling(self, pool: ConnectionPool) -> Dict[str, float]:
        """Test connection pool performance."""
        print("Testing connection pooling...")
        
        # Test rapid connection acquisition/release
        acquisition_times = []
        
        for _ in range(100):
            start_time = time.perf_counter()
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            end_time = time.perf_counter()
            acquisition_times.append((end_time - start_time) * 1000)
        
        return {
            'mean_acquisition_ms': np.mean(acquisition_times),
            'median_acquisition_ms': np.median(acquisition_times),
            'p95_acquisition_ms': np.percentile(acquisition_times, 95)
        }
    
    def stress_test_concurrent_queries(self, pool: ConnectionPool) -> Dict[str, Dict]:
        """Test performance under concurrent load."""
        print("Testing concurrent query performance...")
        
        concurrent_levels = [10, 25, 50, 100]
        results = {}
        
        for level in concurrent_levels:
            print(f"  Testing {level} concurrent queries...")
            
            def run_query():
                start = time.perf_counter()
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT * FROM audio_analytics.audio_metrics WHERE user_id = %s LIMIT 10",
                            ('stress_test_user',)
                        )
                        cur.fetchall()
                return (time.perf_counter() - start) * 1000
            
            # Run concurrent queries
            with ThreadPoolExecutor(max_workers=level) as executor:
                start_time = time.perf_counter()
                latencies = list(executor.map(lambda _: run_query(), range(level)))
                total_time = (time.perf_counter() - start_time) * 1000
            
            results[f'concurrent_{level}'] = {
                'mean_latency_ms': np.mean(latencies),
                'median_latency_ms': np.median(latencies),
                'p95_latency_ms': np.percentile(latencies, 95),
                'p99_latency_ms': np.percentile(latencies, 99),
                'total_time_ms': total_time,
                'queries_per_second': (level * 1000) / total_time
            }
        
        return results
    
    def publish_metrics_to_cloudwatch(self, namespace: str, metrics: Dict[str, Dict]):
        """Publish performance metrics to CloudWatch."""
        metric_data = []
        timestamp = datetime.now(timezone.utc)
        
        for test_name, results in metrics.items():
            if isinstance(results, dict) and 'mean' in results:
                metric_data.append({
                    'MetricName': f'{test_name}_mean_latency',
                    'Value': results['mean'],
                    'Unit': 'Milliseconds',
                    'Timestamp': timestamp
                })
                
                if 'p95' in results:
                    metric_data.append({
                        'MetricName': f'{test_name}_p95_latency',
                        'Value': results['p95'],
                        'Unit': 'Milliseconds',
                        'Timestamp': timestamp
                    })
                
                if 'p99' in results:
                    metric_data.append({
                        'MetricName': f'{test_name}_p99_latency',
                        'Value': results['p99'],
                        'Unit': 'Milliseconds',
                        'Timestamp': timestamp
                    })
        
        # Send metrics in batches of 25 (CloudWatch limit)
        for i in range(0, len(metric_data), 25):
            batch = metric_data[i:i+25]
            self.cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=batch
            )
    
    def print_report(self, results: Dict[str, Dict]):
        """Print performance test results."""
        print("\n" + "="*60)
        print("AURORA PERFORMANCE TEST RESULTS")
        print("="*60)
        
        # Query performance
        if 'queries' in results:
            print("\nQUERY PERFORMANCE:")
            for query_type, metrics in results['queries'].items():
                print(f"\n{query_type}:")
                print(f"  Mean latency: {metrics['mean']:.2f} ms")
                print(f"  Median latency: {metrics['median']:.2f} ms") 
                print(f"  95th percentile: {metrics['p95']:.2f} ms")
                print(f"  99th percentile: {metrics['p99']:.2f} ms")
                
                # Check against 100ms requirement
                if metrics['p95'] < 100:
                    print(f"  [PASS] PASSES <100ms requirement (p95)")
                else:
                    print(f"  [FAIL] FAILS <100ms requirement (p95)")
        
        # Write performance
        if 'writes' in results:
            print("\nWRITE PERFORMANCE:")
            for write_type, metrics in results['writes'].items():
                print(f"\n{write_type}:")
                print(f"  Mean latency: {metrics['mean']:.2f} ms")
                print(f"  Median latency: {metrics['median']:.2f} ms")
                if 'records_per_second' in metrics:
                    print(f"  Throughput: {metrics['records_per_second']:.0f} records/sec")
        
        # Connection pooling
        if 'connection_pool' in results:
            print("\nCONNECTION POOLING:")
            pool_metrics = results['connection_pool']
            print(f"  Mean acquisition: {pool_metrics['mean_acquisition_ms']:.2f} ms")
            print(f"  95th percentile: {pool_metrics['p95_acquisition_ms']:.2f} ms")
        
        # Concurrent load
        if 'concurrent_load' in results:
            print("\nCONCURRENT LOAD PERFORMANCE:")
            for level, metrics in results['concurrent_load'].items():
                print(f"\n{level}:")
                print(f"  Mean latency: {metrics['mean_latency_ms']:.2f} ms")
                print(f"  95th percentile: {metrics['p95_latency_ms']:.2f} ms")
                print(f"  Throughput: {metrics['queries_per_second']:.0f} queries/sec")
        
        # Overall assessment
        print("\n" + "="*60)
        print("OVERALL ASSESSMENT:")
        
        all_p95_values = []
        if 'queries' in results:
            for metrics in results['queries'].values():
                all_p95_values.append(metrics['p95'])
        
        if all_p95_values:
            max_p95 = max(all_p95_values)
            avg_p95 = np.mean(all_p95_values)
            
            print(f"Average P95 latency: {avg_p95:.2f} ms")
            print(f"Maximum P95 latency: {max_p95:.2f} ms")
            
            if max_p95 < 100:
                print("\n[SUCCESS] DATABASE MEETS <100ms LATENCY REQUIREMENT")
            else:
                print("\n[FAILURE] DATABASE DOES NOT MEET <100ms LATENCY REQUIREMENT")
        
        print("="*60 + "\n")


def main():
    # Get configuration from environment or defaults
    cluster_endpoint = os.getenv('DB_CLUSTER_ENDPOINT', 
                                'gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com')
    read_endpoint = os.getenv('DB_READ_ENDPOINT',
                             'gaming-system-aurora-db-cluster.cluster-ro-cal6eoegigyq.us-east-1.rds.amazonaws.com')
    secret_arn = os.getenv('DB_SECRET_ARN', 
                          'arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7')
    
    tester = AuroraPerformanceTester()
    
    print("Starting Aurora Performance Tests...")
    print(f"Cluster: {cluster_endpoint}")
    
    # Get credentials
    credentials = tester.get_db_credentials(secret_arn)
    
    # Create connection pools
    writer_pool = tester.create_connection_pool(cluster_endpoint, credentials)
    reader_pool = tester.create_connection_pool(read_endpoint, credentials)
    
    try:
        results = {}
        
        # Test read queries on reader endpoint
        print("\nTesting READ performance on reader endpoint...")
        results['queries'] = tester.test_simple_queries(reader_pool)
        
        # Test write operations on writer endpoint
        print("\nTesting WRITE performance on writer endpoint...")
        results['writes'] = tester.test_write_performance(writer_pool)
        
        # Test connection pooling
        results['connection_pool'] = tester.test_connection_pooling(reader_pool)
        
        # Stress test with concurrent queries
        results['concurrent_load'] = tester.stress_test_concurrent_queries(reader_pool)
        
        # Publish to CloudWatch
        print("\nPublishing metrics to CloudWatch...")
        tester.publish_metrics_to_cloudwatch('GamingSystem/Aurora/Performance', {
            **results.get('queries', {}),
            **results.get('writes', {}),
        })
        
        # Print report
        tester.print_report(results)
        
        # Return status for CI/CD
        all_p95_values = []
        for metrics in results['queries'].values():
            all_p95_values.append(metrics['p95'])
        
        max_p95 = max(all_p95_values) if all_p95_values else 0
        return 0 if max_p95 < 100 else 1
        
    finally:
        writer_pool.close()
        reader_pool.close()


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
