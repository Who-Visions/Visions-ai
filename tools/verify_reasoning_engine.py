import vertexai
from vertexai.preview import reasoning_engines
import os

PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"
RESOURCE_NAME = "projects/620633534056/locations/us-central1/reasoningEngines/1288754071590666240"

print(f"🚀 Initializing Vertex AI Verification for: {RESOURCE_NAME}")
vertexai.init(project=PROJECT_ID, location=LOCATION)

try:
    remote_agent = reasoning_engines.ReasoningEngine(RESOURCE_NAME)
    
    print("\n📨 Sending query...")
    response = remote_agent.query(
        question="Who are you? Confirm your initialization status and if you are using high-level Vertex AI logic (Rhea Noir v3)."
    )
    print(f"\n✅ SUCCESS! Response:\n{response}")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
