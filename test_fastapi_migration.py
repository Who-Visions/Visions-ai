"""
FastAPI Test Script - Runs for 180 seconds
Tests all endpoints to verify CORS and functionality
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8080"
TEST_DURATION = 180  # seconds
START_TIME = time.time()

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ GET / - Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ GET / - Error: {e}")
        return False

def test_agent_json():
    """Test A2A agent.json endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/.well-known/agent.json")
        print(f"✓ GET /.well-known/agent.json - Status: {response.status_code}")
        data = response.json()
        print(f"  Agent Name: {data.get('name')}")
        print(f"  Version: {data.get('version')}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ GET /.well-known/agent.json - Error: {e}")
        return False

def test_models():
    """Test models endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        print(f"✓ GET /v1/models - Status: {response.status_code}")
        data = response.json()
        print(f"  Models: {len(data.get('data', []))}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ GET /v1/models - Error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers are present"""
    try:
        response = requests.options(f"{BASE_URL}/", headers={
            'Origin': 'http://example.com',
            'Access-Control-Request-Method': 'POST'
        })
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        print(f"✓ CORS Headers - Access-Control-Allow-Origin: {cors_header}")
        return cors_header is not None
    except Exception as e:
        print(f"✗ CORS Test - Error: {e}")
        return False

def main():
    print("=" * 60)
    print("FastAPI Migration Test - 180 Second Duration")
    print("=" * 60)
    print()
    
    # Wait for server to start
    print("Waiting 5 seconds for server to start...")
    time.sleep(5)
    
    test_count = 0
    success_count = 0
    
    while (time.time() - START_TIME) < TEST_DURATION:
        elapsed = int(time.time() - START_TIME)
        remaining = TEST_DURATION - elapsed
        
        print(f"\n[{elapsed}s / {TEST_DURATION}s] Running test cycle {test_count + 1}...")
        print("-" * 60)
        
        # Run all tests
        results = []
        results.append(test_health())
        results.append(test_agent_json())
        results.append(test_models())
        results.append(test_cors_headers())
        
        test_count += 1
        if all(results):
            success_count += 1
            print(f"✅ All tests passed in cycle {test_count}")
        else:
            print(f"⚠️  Some tests failed in cycle {test_count}")
        
        print(f"Time remaining: {remaining}s")
        
        # Wait 30 seconds before next test cycle
        if remaining > 30:
            time.sleep(30)
        else:
            break
    
    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total test cycles: {test_count}")
    print(f"Successful cycles: {success_count}")
    print(f"Success rate: {(success_count/test_count*100):.1f}%")
    print(f"Total duration: {int(time.time() - START_TIME)}s")
    print("=" * 60)

if __name__ == "__main__":
    main()
