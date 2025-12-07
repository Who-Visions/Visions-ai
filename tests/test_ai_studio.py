#!/usr/bin/env python3
"""
Test image generation using Google AI Studio API (alternative to Vertex AI)
This uses the free tier quotas which are separate from Vertex AI quotas
"""
from google import genai
from google.genai import types
import os

# Use the API key directly for testing (will move to env var later)
API_KEY = "AIzaSyBRSb1uD8hWirVzSRSpQA_zPXffbCGR_7c"

print("🎨 Testing Image Generation with Google AI Studio API")
print("This uses separate quotas from Vertex AI!\n")

# Initialize client with API key (NOT Vertex AI)
client = genai.Client(api_key=API_KEY)

prompt = "Generate a professional photograph of a modern photography studio with dramatic lighting, a DSLR camera on a tripod, and softboxes"

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
                filename = f"test_output/ai_studio_gen_{images_found}.png"
                with open(filename, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  - Saved to: {filename}")
        
        if images_found == 0:
            print("\n⚠️  No images were generated in the response")
            print("Response text:", response.text if hasattr(response, 'text') else "N/A")
        else:
            print(f"\n🎉 Successfully generated {images_found} image(s)!")
            print("\n💡 Google AI Studio API key is working!")
            print("This can be used as a fallback when Vertex AI quotas are exhausted.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
