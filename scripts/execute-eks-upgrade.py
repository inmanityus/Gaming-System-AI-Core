#!/usr/bin/env python3
"""Execute EKS cluster upgrade via AWS CLI."""
import subprocess
import json
import sys
import time

cluster_name = "gaming-ai-gold-tier"
region = "us-east-1"
target_version = "1.32"

print(f"\n=== Executing EKS Upgrade ===")
print(f"Cluster: {cluster_name}")
print(f"Target Version: {target_version}")
print(f"Region: {region}\n")

# Execute upgrade command
print("[1] Executing upgrade command...")
cmd = [
    "aws", "eks", "update-cluster-version",
    "--name", cluster_name,
    "--version", target_version,
    "--region", region,
    "--output", "json"
]

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )
    
    print(f"Exit Code: {result.returncode}")
    print(f"Stdout Length: {len(result.stdout)}")
    print(f"Stderr Length: {len(result.stderr)}")
    
    if result.stdout:
        print("\nStdout:")
        print(result.stdout)
        try:
            data = json.loads(result.stdout)
            print("\nParsed JSON:")
            print(json.dumps(data, indent=2))
            if "update" in data:
                print(f"\n✅ Upgrade initiated!")
                print(f"Update ID: {data['update'].get('id', 'N/A')}")
                print(f"Status: {data['update'].get('status', 'N/A')}")
        except json.JSONDecodeError:
            print("Could not parse as JSON")
    
    if result.stderr:
        print("\nStderr:")
        print(result.stderr)
    
    # Wait and check status
    print("\n[2] Waiting 10 seconds...")
    time.sleep(10)
    
    print("[3] Checking cluster status...")
    status_cmd = [
        "aws", "eks", "describe-cluster",
        "--name", cluster_name,
        "--region", region,
        "--output", "json",
        "--query", "cluster.{Status:status,Version:version}"
    ]
    
    status_result = subprocess.run(
        status_cmd,
        capture_output=True,
        text=True,
        check=False
    )
    
    if status_result.stdout:
        print(status_result.stdout)
        try:
            status_data = json.loads(status_result.stdout)
            print(f"\n✅ Status: {status_data.get('Status')}")
            print(f"✅ Version: {status_data.get('Version')}")
            if status_data.get('Status') == 'UPDATING':
                print("\n✅✅✅ UPGRADE IS IN PROGRESS!")
            elif status_data.get('Version') == target_version:
                print("\n✅✅✅ UPGRADE COMPLETE!")
        except:
            pass
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)


