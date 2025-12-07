from google import genai
from google.genai import types
import os
import time

PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "global"
MODEL_ID = "gemini-3-pro-image-preview"

def test_image_generation():
    print(f"🎨 Testing Image Generation with {MODEL_ID} (Global)...")
    
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    prompt = "Generate a hyper-realistic image of a futuristic camera lens reflecting a neon city, cyberpunk style, 8k resolution."
    print(f"Prompt: {prompt}")
    
    try:
        # Gemini 3 Pro Image uses generate_content for multimodal output
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json" # Optional: sometimes helps structure, but let's try default first
            )
        )
        
        print("Response received.")
        
        # Check for image parts
        if response.candidates:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data:
                        print(f"✅ Image Generated! Mime: {part.inline_data.mime_type}")
                        try:
                            import base64
                            # The SDK might wrap it, or it's raw bytes in .data
                            img_data = part.inline_data.data
                            if isinstance(img_data, str):
                                img_bytes = base64.b64decode(img_data)
                            else:
                                img_bytes = img_data
                                
                            with open("test_output.png", "wb") as f:
                                f.write(img_bytes)
                            print("💾 Saved to test_output.png")
                        except Exception as e:
                            print(f"Error saving image: {e}")
                    elif part.text:
                        print(f"Text: {part.text}")
                        
    except Exception as e:
        print(f"🔥 Error: {e}")

if __name__ == "__main__":
    test_image_generation()
