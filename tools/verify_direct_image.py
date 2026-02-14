import vertexai
from vertexai.preview import reasoning_engines
import os

PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"
RESOURCE_NAME = "projects/620633534056/locations/us-central1/reasoningEngines/3235435010521563136"

print(f"🚀 Initializing Direct Image Gen Test for: {RESOURCE_NAME}")
vertexai.init(project=PROJECT_ID, location=LOCATION)

try:
    remote_agent = reasoning_engines.ReasoningEngine(RESOURCE_NAME)
    
    # CALLING THE METHOD DIRECTLY (Feature of Reasoning Engine)
    prompt = "A high-tech cyberpunk laboratory on Mars, blue and red lighting, cinematic."
    print(f"\n🎨 Calling .generate_image('{prompt}') directly...")
    
    # This calls the VisionsAgent.generate_image() method on the remote server
    response = remote_agent.generate_image(prompt=prompt)
    
    if "IMAGE_GENERATED:" in response:
        print("\n✅ SUCCESS! Direct method call returned image data.")
        print(f"📊 Preview: {response[:100]}...")
    else:
        print(f"\n❌ FAILED: Unexpected response format:\n{response}")
    
except Exception as e:
    print(f"\n❌ DIRECT CALL FAILED: {e}")
