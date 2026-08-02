"""
Test Video Generation with Imagen API (REST)
Direct API call to Vertex AI for video generation
"""
import os
import requests
import json
import time
import base64
from google.auth import default
from google.auth.transport.requests import Request

# Configuration
PROJECT_ID = "mineral-subject-487519-v6"
PROJECT_NUMBER = "885670388176"
LOCATION = "us-central1"

print("="*80)
print("🎬 TESTING VIDEO GENERATION - IMAGEN/VEO API")
print("="*80)

# Get credentials
print("\n🔑 Getting credentials...")
credentials, project = default()
credentials.refresh(Request())
access_token = credentials.token

print(f"✅ Authenticated to project: {project}")

# Video generation prompt
prompt = """
A cinematic pan across a modern photography studio.
Smooth camera movement from left to right showing professional equipment:
a DSLR camera on a tripod, softbox lighting, and white backdrop.
Dramatic lighting with warm tones. Professional quality.
"""

print(f"\n📝 Prompt: {prompt.strip()}\n")

# API endpoint
endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_NUMBER}/locations/{LOCATION}/publishers/google/models/imagen-3.0-generate-001:predict"

print(f"🔗 Endpoint: {endpoint}\n")

# Request payload
payload = {
    "instances": [
        {
            "prompt": prompt
        }
    ],
    "parameters": {
        "sampleCount": 1,
    }
}

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

try:
    print("🎬 Sending request to Imagen API...")
    response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Response received!")
        print(f"Response keys: {list(result.keys())}")
        
        # Check if we have predictions
        if "predictions" in result:
            predictions = result["predictions"]
            print(f"Predictions: {len(predictions)}")
            
            # Save results
            os.makedirs("test_output/videos", exist_ok=True)
            
            for i, pred in enumerate(predictions):
                print(f"\nPrediction {i+1}:")
                print(f"Keys: {list(pred.keys())}")
                
                # Save based on what we get back
                if "bytesBase64Encoded" in pred:
                    video_data = base64.b64decode(pred["bytesBase64Encoded"])
                    output_path = f"test_output/videos/imagen_video_{i+1}.mp4"
                    
                    with open(output_path, "wb") as f:
                        f.write(video_data)
                    
                    file_size = os.path.getsize(output_path)
                    print(f"  ✅ Saved to: {output_path}")
                    print(f"  📊 Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                else:
                    print(f"  Data: {pred}")
        
        print("\n🎉 Request successful!")
    else:
        print(f"\n❌ Error {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 404:
            print("\n💡 Model not found - Imagen 3.0 may not support video")
            print("   Image generation is available, but video may require Veo")
        elif response.status_code == 400:
            print("\n💡 Bad request - check if video generation is supported")
        elif response.status_code == 429:
            print("\n💡 Quota exhausted for video generation")

except requests.exceptions.Timeout:
    print("\n⏱️ Request timed out (>5 minutes)")
    print("Video generation typically takes 2-5 minutes")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

print("\n" + "="*80)
print("💡 NOTE: Video generation with Veo may require:")
print("   1. Specific region (us-east4)")
print("   2. Vertex AI Vision API enabled")
print("   3. Veo preview access")
print("="*80)
