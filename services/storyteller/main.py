# services/storyteller/main.py
"""
Storyteller service with capability integration
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

CAPABILITY_REGISTRY_URL = os.getenv("CAPABILITY_REGISTRY_URL", "http://capability-registry:8080")
UE5_VERSION = os.getenv("UE5_VERSION", "5.6.1")

def get_capabilities_for_version(version: str):
    """Get capabilities for a specific UE5 version"""
    try:
        response = httpx.get(f"{CAPABILITY_REGISTRY_URL}/api/v1/versions/{version}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching capabilities: {e}")
        return None

def main():
    """Main service loop"""
    print(f"Storyteller service starting...")
    print(f"UE5 Version: {UE5_VERSION}")
    print(f"Capability Registry URL: {CAPABILITY_REGISTRY_URL}")
    
    # Test capability registry connection
    capabilities = get_capabilities_for_version(UE5_VERSION)
    if capabilities:
        print(f"✅ Successfully connected to capability registry")
        print(f"   Found {len(capabilities.get('features', []))} features for UE5 {UE5_VERSION}")
    else:
        print(f"⚠️  Could not connect to capability registry")
    
    # Keep service running
    import time
    while True:
        time.sleep(60)
        print("Service heartbeat...")

if __name__ == "__main__":
    main()

