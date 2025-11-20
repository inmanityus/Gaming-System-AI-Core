#!/usr/bin/env python3
"""
End-to-End Test for NATS Binary Messaging System
Tests the full flow: Client → ALB → Gateway → NATS → Service → Response
"""

import json
import time
import requests
import sys
from typing import Dict, Any

# Configuration
ALB_URL = "http://gateway-production-2098455312.us-east-1.elb.amazonaws.com"
TIMEOUT = 30

# Test colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
NC = '\033[0m'

def print_test(name: str, status: str = "RUNNING"):
    """Print test status"""
    color = YELLOW if status == "RUNNING" else GREEN if status == "PASS" else RED
    symbol = "..." if status == "RUNNING" else "[OK]" if status == "PASS" else "[FAIL]"
    print(f"{color}{symbol} {name}: {status}{NC}")

def test_health_check():
    """Test gateway health endpoint"""
    print_test("Gateway Health Check", "RUNNING")
    try:
        response = requests.get(f"{ALB_URL}/health", timeout=10)
        if response.status_code == 200:
            print_test("Gateway Health Check", "PASS")
            return True
        else:
            print_test("Gateway Health Check", f"FAIL (Status: {response.status_code})")
            return False
    except Exception as e:
        print_test("Gateway Health Check", f"FAIL ({str(e)})")
        return False

def test_service_discovery():
    """Test service discovery endpoint"""
    print_test("Service Discovery", "RUNNING")
    try:
        response = requests.get(f"{ALB_URL}/services", timeout=10)
        if response.status_code == 200:
            services = response.json()
            print(f"  Found {len(services)} services")
            for service in services[:5]:  # Show first 5
                print(f"    - {service}")
            print_test("Service Discovery", "PASS")
            return True
        else:
            print_test("Service Discovery", f"FAIL (Status: {response.status_code})")
            return False
    except Exception as e:
        print_test("Service Discovery", f"FAIL ({str(e)})")
        return False

def test_ai_integration_service():
    """Test AI Integration service through gateway"""
    print_test("AI Integration Service", "RUNNING")
    
    payload = {
        "request_id": f"test-{int(time.time())}",
        "model": "test-model",
        "prompt": "Hello, this is a test",
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            f"{ALB_URL}/ai-integration/generate",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Response received: {json.dumps(result, indent=2)[:200]}")
            print_test("AI Integration Service", "PASS")
            return True
        else:
            print_test("AI Integration Service", f"FAIL (Status: {response.status_code})")
            print(f"  Response: {response.text[:500]}")
            return False
    except Exception as e:
        print_test("AI Integration Service", f"FAIL ({str(e)})")
        return False

def test_world_state_service():
    """Test World State service through gateway"""
    print_test("World State Service", "RUNNING")
    
    # Test get state
    try:
        response = requests.get(
            f"{ALB_URL}/world-state/state/test-entity",
            timeout=10
        )
        
        if response.status_code in [200, 404]:  # 404 is ok if entity doesn't exist
            print(f"  GET Status: {response.status_code}")
            print_test("World State Service", "PASS")
            return True
        else:
            print_test("World State Service", f"FAIL (Status: {response.status_code})")
            return False
    except Exception as e:
        print_test("World State Service", f"FAIL ({str(e)})")
        return False

def test_auth_service():
    """Test Authentication service through gateway"""
    print_test("Authentication Service", "RUNNING")
    
    # Test token verification
    payload = {
        "token": "test-token-12345"
    }
    
    try:
        response = requests.post(
            f"{ALB_URL}/auth/verify",
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        # We expect 401 for invalid token, which means service is working
        if response.status_code in [200, 401, 403]:
            print(f"  Verify Status: {response.status_code}")
            print_test("Authentication Service", "PASS")
            return True
        else:
            print_test("Authentication Service", f"FAIL (Status: {response.status_code})")
            return False
    except Exception as e:
        print_test("Authentication Service", f"FAIL ({str(e)})")
        return False

def test_latency():
    """Test end-to-end latency"""
    print_test("Latency Test", "RUNNING")
    
    latencies = []
    for i in range(10):
        start = time.time()
        try:
            response = requests.get(f"{ALB_URL}/health", timeout=5)
            if response.status_code == 200:
                latency = (time.time() - start) * 1000  # ms
                latencies.append(latency)
        except:
            pass
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"  Avg: {avg_latency:.2f}ms")
        print(f"  Min: {min_latency:.2f}ms")
        print(f"  Max: {max_latency:.2f}ms")
        
        if avg_latency < 100:  # Target < 100ms
            print_test("Latency Test", "PASS")
            return True
        else:
            print_test("Latency Test", f"FAIL (Avg: {avg_latency:.2f}ms > 100ms)")
            return False
    else:
        print_test("Latency Test", "FAIL (No successful requests)")
        return False

def test_concurrent_requests():
    """Test concurrent request handling"""
    print_test("Concurrent Requests", "RUNNING")
    
    import concurrent.futures
    
    def make_request(i):
        try:
            response = requests.get(f"{ALB_URL}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success_count = sum(results)
    success_rate = (success_count / len(results)) * 100
    
    print(f"  Success rate: {success_rate:.1f}% ({success_count}/20)")
    
    if success_rate >= 95:
        print_test("Concurrent Requests", "PASS")
        return True
    else:
        print_test("Concurrent Requests", f"FAIL (Success rate: {success_rate:.1f}%)")
        return False

def main():
    """Run all tests"""
    print(f"{GREEN}=== NATS End-to-End Test Suite ==={NC}")
    print(f"Target: {ALB_URL}")
    print()
    
    tests = [
        ("Health Check", test_health_check),
        ("Service Discovery", test_service_discovery),
        ("AI Integration", test_ai_integration_service),
        ("World State", test_world_state_service),
        ("Authentication", test_auth_service),
        ("Latency", test_latency),
        ("Concurrent Requests", test_concurrent_requests),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print_test(name, f"ERROR: {str(e)}")
            results[name] = False
        print()
    
    # Summary
    print(f"{GREEN}=== Test Summary ==={NC}")
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        color = GREEN if result else RED
        symbol = "[OK]" if result else "[FAIL]"
        print(f"  {color}{symbol} {name}: {status}{NC}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{GREEN}[OK] All tests passed!{NC}")
        return 0
    else:
        print(f"{RED}[FAIL] Some tests failed{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
