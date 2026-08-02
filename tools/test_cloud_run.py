import requests
import json
import os
import sys

def test_cloud_run(url):
    print(f"🚀 Testing Cloud Run Endpoint: {url}")
    
    # 1. Health Check
    try:
        health_resp = requests.get(f"{url}/health")
        print(f"🏥 Health Check: {health_resp.status_code} - {health_resp.json()}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return

    # 2. Basic Query
    print("\n📨 Sending text query...")
    query_payload = {
        "question": "Who are you and what are your core capabilities?",
        "user_id": "test_user_001"
    }
    try:
        resp = requests.post(f"{url}/query", json=query_payload)
        if resp.status_code == 200:
            print(f"✅ Response Received: {resp.json().get('response')[:200]}...")
        else:
            print(f"❌ Query Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Query Error: {e}")

    # 3. Tool Test: Image Generation
    print("\n🎨 Sending image generation query...")
    img_payload = {
        "question": "Generate an image of a neon cyberpunk city street in the rain.",
        "user_id": "test_user_001"
    }
    try:
        resp = requests.post(f"{url}/query", json=img_payload)
        if resp.status_code == 200:
            content = resp.json().get('response', '')
            if "IMAGE_GENERATED:" in content:
                print("✅ Image Generation Successful! (Base64 data received)")
            else:
                print(f"⚠️ Response received but no image tag found: {content[:200]}...")
        else:
            print(f"❌ Image Query Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Image Query Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_cloud_run.py <CLOUD_RUN_URL>")
        sys.exit(1)
    
    test_cloud_run(sys.argv[1].strip())
