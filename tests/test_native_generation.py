#!/usr/bin/env python3
"""
Direct test of gemini-3-pro-image-preview's native image generation capability
"""
from google import genai
from google.genai import types
import vertexai
import base64
import os

PROJECT_ID = "endless-duality-480201-t3"

# Initialize
vertexai.init(project=PROJECT_ID, location="us-central1")
client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

print("🎨 Testing Native Image Generation with gemini-3-pro-image-preview\n")

prompt = "Generate a professional photograph of a modern photography studio with dramatic lighting"

print(f"📝 Prompt: {prompt}")
print("\n🔄 Generating...")

try:
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[prompt],
        config=types.GenerateContentConfig(
            temperature=1.0,
        )
    )
    
    print("\n✅ Response received!")
    print(f"Candidates: {len(response.candidates)}")
    
    if response.candidates:
        candidate = response.candidates[0]
        print(f"Parts in candidate: {len(candidate.content.parts)}")
        
        images_found = 0
        for i, part in enumerate(candidate.content.parts):
            print(f"\nPart {i}:")
            if part.text:
                print(f"  - Text: {part.text[:200]}")
            if part.inline_data:
                images_found += 1
                print(f"  - Image data found! MIME: {part.inline_data.mime_type}")
                print(f"  - Image size: {len(part.inline_data.data)} bytes")
                
                # Save image
                os.makedirs("test_output", exist_ok=True)
                filename = f"test_output/native_gen_{images_found}.png"
                with open(filename, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  - Saved to: {filename}")
        
        if images_found == 0:
            print("\n⚠️  No images were generated in the response")
        else:
            print(f"\n🎉 Successfully generated {images_found} image(s)!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
