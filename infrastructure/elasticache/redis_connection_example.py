import json
import boto3
import redis
from rediscluster import RedisCluster

# Get credentials from Secrets Manager
def get_redis_credentials(secret_name="elasticache/ai-core-redis-cluster/auth-token"):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Connect to Redis cluster
def connect_redis_cluster():
    credentials = get_redis_credentials()
    
    startup_nodes = [{
        "host": credentials['configurationEndpoint'],
        "port": credentials['port']
    }]
    
    rc = RedisCluster(
        startup_nodes=startup_nodes,
        password=credentials['authToken'],
        decode_responses=True,
        skip_full_coverage_check=True,
        ssl=True,
        ssl_cert_reqs=None
    )
    
    return rc

# Example usage
if __name__ == "__main__":
    redis_client = connect_redis_cluster()
    
    # Test operations
    redis_client.set("test:ml:model", "model-v1.0")
    value = redis_client.get("test:ml:model")
    print(f"Retrieved value: {value}")
    
    # Cluster info
    info = redis_client.info()
    print(f"Cluster nodes: {len(info)}")
    
    redis_client.close()
