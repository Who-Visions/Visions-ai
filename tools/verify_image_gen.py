import vertexai
from vertexai.preview import reasoning_engines
import os
import base64

PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"
RESOURCE_NAME = "projects/620633534056/locations/us-central1/reasoningEngines/1288754071590666240"

print(f"🚀 Initializing Vertex AI Image Generation Test for: {RESOURCE_NAME}")
vertexai.init(project=PROJECT_ID, location=LOCATION)

try:
    remote_agent = reasoning_engines.ReasoningEngine(RESOURCE_NAME)
    
    # Triggering the native image generation logic
    prompt = "Generate a cinematic portrait of a cyberpunk explorer in the deserts of Mars, holding a glowing blue artifact. High detail, 8k, anamorphic lens flare."
    print(f"\n🎨 Requesting Image: {prompt}")
    
    # We use agent.query which routes to the image generator if the prompt implies it
    # and the GOD_MODE instructions tell it how to format the tool request or response.
    # However, the direct way is calling query.
    response = remote_agent.query(
        question=prompt
    )
    
    if "IMAGE_GENERATED:" in response:
        print("\n✅ SUCCESS! Image data received in response.")
        # Splitting to show we got actual data
        parts = response.split("IMAGE_GENERATED:")
        data_preview = parts[1][:50]
        print(f"📊 Data Preview: {data_preview}...")
    else:
        print(f"\n⚠️ Response received but no IMAGE_GENERATED tag found. Response snippet:\n{response[:200]}")
    
except Exception as e:
    print(f"\n❌ IMAGE TEST FAILED: {e}")
