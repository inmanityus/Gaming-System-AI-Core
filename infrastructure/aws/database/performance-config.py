#!/usr/bin/env python3
"""
Aurora PostgreSQL Performance Configuration
Optimizes database for gaming workload with real-time requirements
"""
import boto3
import json
from typing import Dict, List, Any
from datetime import datetime


class AuroraPerformanceOptimizer:
    """Optimize Aurora PostgreSQL for high-speed gaming workloads."""
    
    def __init__(self, cluster_identifier: str, region: str = 'us-east-1'):
        self.cluster_identifier = cluster_identifier
        self.region = region
        self.rds_client = boto3.client('rds', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
    
    def get_performance_recommendations(self) -> Dict[str, Any]:
        """Generate performance recommendations based on workload."""
        return {
            "connection_pooling": {
                "max_connections": 5000,
                "pool_size": 100,
                "overflow": 50,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "recommendation": "Use RDS Proxy for connection pooling"
            },
            "query_optimization": {
                "indexes": self._get_index_recommendations(),
                "partitioning": self._get_partitioning_recommendations(),
                "materialized_views": self._get_materialized_view_recommendations()
            },
            "caching": {
                "query_cache_size": "256MB",
                "shared_buffers": "75% of instance memory",
                "effective_cache_size": "75% of instance memory",
                "redis_integration": True
            },
            "read_scaling": {
                "min_read_replicas": 1,
                "max_read_replicas": 15,
                "auto_scaling_target_cpu": 70,
                "read_write_splitting": True
            },
            "monitoring": {
                "performance_insights": True,
                "enhanced_monitoring": True,
                "slow_query_log": True,
                "log_min_duration": 1000  # ms
            }
        }
    
    def _get_index_recommendations(self) -> List[Dict[str, Any]]:
        """Get index recommendations for gaming workload."""
        return [
            {
                "table": "audio_analytics.audio_metrics",
                "index": "idx_user_session_created",
                "columns": ["user_id", "session_id", "created_at DESC"],
                "type": "BTREE",
                "reason": "Frequent queries by user and session with time ordering"
            },
            {
                "table": "audio_analytics.audio_metrics",
                "index": "idx_analysis_id",
                "columns": ["analysis_id"],
                "type": "HASH",
                "reason": "Fast lookup by unique analysis ID"
            },
            {
                "table": "engagement.sessions",
                "index": "idx_user_time_range",
                "columns": ["user_id", "start_time", "end_time"],
                "type": "BTREE",
                "reason": "Time-range queries for user sessions"
            },
            {
                "table": "engagement.sessions",
                "index": "idx_events_gin",
                "columns": ["events"],
                "type": "GIN",
                "reason": "Fast JSONB queries on event data"
            },
            {
                "table": "localization.content",
                "index": "idx_key_lang_version",
                "columns": ["content_key", "language_code", "version"],
                "type": "BTREE",
                "unique": True,
                "reason": "Unique constraint and fast lookups"
            },
            {
                "table": "language_system.tts_cache",
                "index": "idx_cache_key_hash",
                "columns": ["cache_key"],
                "type": "HASH",
                "reason": "O(1) cache lookups"
            }
        ]
    
    def _get_partitioning_recommendations(self) -> List[Dict[str, Any]]:
        """Get partitioning recommendations for large tables."""
        return [
            {
                "table": "audio_analytics.audio_metrics",
                "partition_by": "RANGE (created_at)",
                "interval": "MONTHLY",
                "retention": "12 months",
                "reason": "Time-based data with high volume"
            },
            {
                "table": "engagement.sessions",
                "partition_by": "RANGE (start_time)",
                "interval": "WEEKLY",
                "retention": "6 months",
                "reason": "Session data grows rapidly"
            },
            {
                "table": "language_system.tts_metrics",
                "partition_by": "RANGE (created_at)",
                "interval": "DAILY",
                "retention": "30 days",
                "reason": "High-frequency metrics data"
            }
        ]
    
    def _get_materialized_view_recommendations(self) -> List[Dict[str, Any]]:
        """Get materialized view recommendations."""
        return [
            {
                "name": "user_audio_summary_mv",
                "refresh": "CONCURRENT",
                "interval": "5 minutes",
                "query": """
                    SELECT 
                        user_id,
                        COUNT(*) as total_analyses,
                        AVG(intelligibility_score) as avg_intelligibility,
                        MAX(created_at) as last_analysis,
                        array_agg(DISTINCT archetype) as archetypes_used
                    FROM audio_analytics.audio_metrics
                    WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY user_id
                """,
                "reason": "Frequently accessed user summaries"
            },
            {
                "name": "active_sessions_mv",
                "refresh": "CONCURRENT",
                "interval": "1 minute",
                "query": """
                    SELECT 
                        user_id,
                        session_id,
                        start_time,
                        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time)) as duration_seconds,
                        jsonb_array_length(events) as event_count
                    FROM engagement.sessions
                    WHERE end_time IS NULL
                    AND start_time > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """,
                "reason": "Real-time active session tracking"
            }
        ]
    
    def apply_performance_parameters(self) -> Dict[str, Any]:
        """Apply performance-optimized parameters to the cluster."""
        parameters = {
            # Connection and memory
            "max_connections": "5000",
            "shared_buffers": "{DBInstanceClassMemory*3/4}",
            "effective_cache_size": "{DBInstanceClassMemory*3/4}",
            "work_mem": "32MB",
            "maintenance_work_mem": "2GB",
            
            # Write performance
            "wal_buffers": "16MB",
            "checkpoint_completion_target": "0.9",
            "checkpoint_timeout": "30min",
            "max_wal_size": "16GB",
            "min_wal_size": "2GB",
            
            # Query optimization
            "random_page_cost": "1.1",  # SSD optimized
            "effective_io_concurrency": "200",
            "max_parallel_workers_per_gather": "4",
            "max_parallel_workers": "32",
            "parallel_leader_participation": "on",
            
            # JIT compilation for complex queries
            "jit": "on",
            "jit_above_cost": "100000",
            
            # Statistics
            "default_statistics_target": "100",
            "autovacuum": "on",
            "autovacuum_max_workers": "10",
            "autovacuum_naptime": "10s",
            
            # Logging
            "log_statement": "ddl",
            "log_min_duration_statement": "1000",
            "log_checkpoints": "on",
            "log_connections": "off",  # Too verbose for gaming
            "log_disconnections": "off",
            
            # Extensions
            "shared_preload_libraries": "pg_stat_statements,auto_explain,pg_cron",
            "pg_stat_statements.track": "all",
            "pg_stat_statements.max": "10000",
            "auto_explain.log_min_duration": "5s",
            "auto_explain.log_analyze": "on"
        }
        
        try:
            # Create parameter group if it doesn't exist
            pg_name = f"{self.cluster_identifier}-performance-pg"
            self.rds_client.create_db_cluster_parameter_group(
                DBClusterParameterGroupName=pg_name,
                DBParameterGroupFamily='aurora-postgresql15',
                Description='Optimized for gaming workloads'
            )
        except self.rds_client.exceptions.DBParameterGroupAlreadyExistsFault:
            pass
        
        # Apply parameters
        self.rds_client.modify_db_cluster_parameter_group(
            DBClusterParameterGroupName=pg_name,
            Parameters=[
                {'ParameterName': k, 'ParameterValue': v, 'ApplyMethod': 'immediate'}
                for k, v in parameters.items()
            ]
        )
        
        return {
            "status": "success",
            "parameter_group": pg_name,
            "parameters_applied": len(parameters),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def create_performance_indexes(self, connection) -> List[Dict[str, Any]]:
        """Create performance indexes on the database."""
        results = []
        
        for index_def in self._get_index_recommendations():
            try:
                # Build CREATE INDEX statement
                unique = "UNIQUE" if index_def.get("unique") else ""
                index_type = f"USING {index_def['type']}" if index_def['type'] != 'BTREE' else ""
                columns = ", ".join(index_def['columns'])
                
                sql = f"""
                CREATE {unique} INDEX CONCURRENTLY IF NOT EXISTS {index_def['index']}
                ON {index_def['table']} {index_type} ({columns})
                """
                
                connection.execute(sql)
                
                results.append({
                    "index": index_def['index'],
                    "status": "created",
                    "reason": index_def['reason']
                })
                
            except Exception as e:
                results.append({
                    "index": index_def['index'],
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def enable_query_insights(self) -> Dict[str, Any]:
        """Enable Performance Insights and query analysis."""
        try:
            # Get cluster instances
            response = self.rds_client.describe_db_clusters(
                DBClusterIdentifier=self.cluster_identifier
            )
            
            instance_results = []
            for member in response['DBClusters'][0]['DBClusterMembers']:
                instance_id = member['DBInstanceIdentifier']
                
                # Enable Performance Insights
                self.rds_client.modify_db_instance(
                    DBInstanceIdentifier=instance_id,
                    PerformanceInsightsEnabled=True,
                    PerformanceInsightsRetentionPeriod=731,  # 2 years
                    EnablePerformanceInsights=True,
                    ApplyImmediately=True
                )
                
                instance_results.append({
                    "instance": instance_id,
                    "performance_insights": "enabled"
                })
            
            return {
                "status": "success",
                "instances_configured": len(instance_results),
                "details": instance_results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def setup_read_write_splitting(self) -> Dict[str, Any]:
        """Configure read/write splitting for optimal performance."""
        return {
            "configuration": {
                "write_endpoint": f"{self.cluster_identifier}.cluster-xxxxx.{self.region}.rds.amazonaws.com",
                "read_endpoint": f"{self.cluster_identifier}.cluster-ro-xxxxx.{self.region}.rds.amazonaws.com",
                "proxy_endpoint": f"{self.cluster_identifier}-proxy.proxy-xxxxx.{self.region}.rds.amazonaws.com"
            },
            "connection_strategy": {
                "writes": "Always use cluster endpoint or proxy",
                "reads": "Use read endpoint for SELECT queries",
                "transactions": "Stick to writer for consistency",
                "analytics": "Prefer read replicas"
            },
            "code_example": """
# Python example with read/write splitting
import asyncpg
import asyncio

class DatabasePool:
    def __init__(self, write_dsn, read_dsn):
        self.write_pool = None
        self.read_pool = None
        self.write_dsn = write_dsn
        self.read_dsn = read_dsn
    
    async def init(self):
        self.write_pool = await asyncpg.create_pool(
            self.write_dsn,
            min_size=10,
            max_size=50,
            command_timeout=60
        )
        self.read_pool = await asyncpg.create_pool(
            self.read_dsn,
            min_size=20,
            max_size=100,
            command_timeout=60
        )
    
    async def execute_write(self, query, *args):
        async with self.write_pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def execute_read(self, query, *args):
        async with self.read_pool.acquire() as conn:
            return await conn.fetch(query, *args)
            """
        }
    
    def get_monitoring_queries(self) -> Dict[str, str]:
        """Get useful monitoring queries for performance."""
        return {
            "active_connections": """
                SELECT 
                    datname,
                    usename,
                    application_name,
                    client_addr,
                    state,
                    COUNT(*) as connection_count
                FROM pg_stat_activity
                WHERE state != 'idle'
                GROUP BY datname, usename, application_name, client_addr, state
                ORDER BY connection_count DESC
            """,
            
            "slow_queries": """
                SELECT 
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time,
                    min_exec_time,
                    max_exec_time,
                    stddev_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > 1000  -- queries slower than 1 second
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """,
            
            "table_bloat": """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    ROUND(100 * pg_total_relation_size(schemaname||'.'||tablename) / 
                          pg_total_relation_size(schemaname||'.'||tablename)::numeric, 2) as bloat_percent
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20
            """,
            
            "missing_indexes": """
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                AND n_distinct > 100
                AND correlation < 0.1
                ORDER BY n_distinct DESC
            """,
            
            "cache_hit_ratio": """
                SELECT 
                    datname,
                    ROUND(100.0 * sum(heap_blks_hit) / 
                          (sum(heap_blks_hit) + sum(heap_blks_read)), 2) as cache_hit_ratio
                FROM pg_statio_user_tables
                GROUP BY datname
            """
        }


def main():
    """Main function to apply performance optimizations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize Aurora PostgreSQL Performance')
    parser.add_argument('--cluster', required=True, help='Aurora cluster identifier')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--apply', action='store_true', help='Apply optimizations')
    
    args = parser.parse_args()
    
    optimizer = AuroraPerformanceOptimizer(args.cluster, args.region)
    
    # Get recommendations
    recommendations = optimizer.get_performance_recommendations()
    print("Performance Recommendations:")
    print(json.dumps(recommendations, indent=2))
    
    if args.apply:
        # Apply parameters
        result = optimizer.apply_performance_parameters()
        print(f"\nParameter optimization: {result['status']}")
        
        # Enable insights
        insights_result = optimizer.enable_query_insights()
        print(f"Performance Insights: {insights_result['status']}")
        
        # Show splitting config
        splitting = optimizer.setup_read_write_splitting()
        print(f"\nRead/Write Splitting Configuration:")
        print(json.dumps(splitting['configuration'], indent=2))


if __name__ == '__main__':
    main()
