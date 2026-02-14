from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "endless-duality-480201-t3")
LOCATION = "global"

print(f"Checking access to Gemini 3 Pro (Image Preview) in {LOCATION} via google.genai SDK...")

try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    # Try text generation first
    print("\nAttempting text generation...")
    model_id = "gemini-3-pro-image-preview" 
    response = client.models.generate_content(
        model=model_id,
        contents="Hello from check script!"
    )
    print(f"✅ Text Response: {response.text}")
    
    # Try image generation
    print("\nAttempting image generation...")
    response = client.models.generate_content(
        model=model_id,
        contents="A cute robot cat",
        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    )
    if response.parts and response.parts[0].inline_data:
        print("✅ Image generated successfully (bytes received).")
    else:
        print("❌ Image generation failed (no image data).")
        
except Exception as e:
    print(f"❌ Error: {e}")
