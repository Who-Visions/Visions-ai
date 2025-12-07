"""
Visions Cinema - "The Nano Banana Pattern" Implementation
Implements: Consistent Character -> Camera Control -> Image-to-Video
"""
import os
import time
import json
import base64
import random
from pathlib import Path
from typing import List, Optional
from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"
OUTPUT_DIR = Path("outputs/cinema")

def retry_with_backoff(func, retries=5, initial_delay=5):
    """
    Simple retry decorator for Quota handling.
    """
    def wrapper(*args, **kwargs):
        delay = initial_delay
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower() or "resource exhausted" in str(e).lower():
                    print(f"⚠️ Quota hit. Retrying in {delay}s... (Attempt {i+1}/{retries})")
                    time.sleep(delay)
                    delay *= 2 # Exponential backoff
                else:
                    raise e
        raise Exception("Max retries exceeded for Quota.")
    return wrapper

class VisionsCinema:
    def __init__(self):
        self.project_id = PROJECT_ID
        self.location = LOCATION
        # LAZY initialization - DON'T create clients here (causes pickling errors on deploy)
        self._client = None
        self._global_client = None
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    @property
    def client(self):
        """Regional client for Veo (us-central1) - lazy loaded."""
        if self._client is None:
            self._client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
        return self._client
    
    @property
    def global_client(self):
        """Global client for Gemini 3 Pro Image - lazy loaded."""
        if self._global_client is None:
            self._global_client = genai.Client(vertexai=True, project=self.project_id, location="global")
        return self._global_client
        
    @retry_with_backoff
    def generate_character_base(self, prompt: str, name: str) -> str:
        """
        Step 1: Create the Base Character using Gemini 3 Pro Image Preview
        """
        print(f"🎨 Creating Base Character: {name} (Gemini 3 Pro Image)...")
        print(f"📝 Prompt: {prompt}")
        
        # Use Gemini 3 Pro Image Preview (global routing)
        response = self.global_client.models.generate_images(
            model='gemini-3-pro-image-preview',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/png"
            )
        )
        
        if response and response.generated_images:
            filepath = OUTPUT_DIR / f"{name}_base.png"
            response.generated_images[0].image.save(str(filepath))
            print(f"✅ Base character saved to: {filepath}")
            return str(filepath)
        else:
            raise Exception("Failed to generate base character")

    @retry_with_backoff
    def generate_shot(self, base_image_path: str, shot_type: str, angle_prompt: str, character_description: str) -> str:
        """
        Step 3: Camera Angle Control using Gemini 3 Pro Image
        """
        print(f"📸 Generating Shot: {shot_type}...")
        
        full_prompt = (
            f"CINEMATIC SHOT: {shot_type}. "
            f"Character: {character_description}. "
            f"Action/Angle: {angle_prompt}. "
            "Ensure consistency with character features: [SAME HAIR, SAME CLOTHES, SAME FACE]. "
            "Photorealistic, 8k, movie still."
        )

        # Read base image for consistency (Gemini 3 Pro supports reference images)
        try:
            with open(base_image_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            print(f"❌ Could not read base image: {e}")
            return None
        
        # Use generate_content for Multimodal input (Text + Image)
        # This leverages Gemini 3 Pro's ability to use reference images
        # TIP: Put image BEFORE text for best results
        
        # Add technical specifications to prompt since ImageConfig might not be supported in generic `generate_content`
        full_prompt += " Output specs: Aspect Ratio 16:9, Photorealistic."

        response = self.global_client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                full_prompt
            ],
            config=types.GenerateContentConfig(
                media_resolution="high",       # Supported per docs
                response_mime_type="image/png" # Explicitly request image MIME if supported, or rely on prompt
            )
        )
        
        filepath = None
        if response.parts:
            for part in response.parts:
                if part.inline_data:
                    filepath = OUTPUT_DIR / f"shot_{shot_type.replace(' ','_')}_{int(time.time())}.png"
                    # SDK helper to save or we can write bytes manually
                    # part.as_image().save() works if PIL is installed, else write bytes
                    try:
                        part.as_image().save(str(filepath))
                    except:
                        with open(filepath, "wb") as f:
                            f.write(part.inline_data.data)
                    
                    print(f"✅ Shot saved to: {filepath}")
                    return str(filepath)
        
        print("❌ Failed to generate shot image.")
        return None

    @retry_with_backoff
    def animate_shot(self, image_path: str, prompt: str) -> str:
        """
        Step 4: Image to Video (Veo)
        """
        print(f"🎥 Animating Shot: {image_path}...")
        
        print("   Starting generation operation...")
        # Use types.Image.from_file as per SDK reference
        operation = self.client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            image=types.Image.from_file(location=image_path),
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                resolution="1080p",
                duration_seconds=5, 
                person_generation="allow_adult",
            ),
        )

        print(f"   Operation started: {operation.name}")
        
        # Poll
        while not operation.done:
            time.sleep(15) 
            print("   Waiting for video...")
            operation = self.client.operations.get(operation)
            
        if operation.response and operation.response.generated_videos:
             generated_video = operation.response.generated_videos[0]
             vid_path = str(Path(image_path).with_suffix('.mp4'))
             generated_video.video.save(vid_path)
             print(f"✅ Video output: {vid_path}")
             return vid_path
        else:
             print("❌ Video generation failed")
             if hasattr(operation, 'error') and operation.error:
                 print(f"   Error: {operation.error}")
             return None

def run_cinema_demo():
    print("🎬 VISIONS CINEMA: Starting Workflow...")
    cinema = VisionsCinema()
    
    # 1. Define Character
    char_desc = "A futuristic cyberpunk detective with neon blue hair, wearing a trench coat, glowing cybernetic eye, rainy street background"
    
    try:
        # 2. Generate Base
        base_img = cinema.generate_character_base(char_desc, "CyberDetective")
        
        # 3. Generate one specific angle (for speed in this test)
        # We'll do the 'Over Shoulder' as it's the complex one requested in the video
        angle_name = "Over Shoulder"
        angle_prompt = "Over the shoulder view looking at a holographic billboard, detective turning head slightly"
        
        shot_img = cinema.generate_shot(base_img, angle_name, angle_prompt, char_desc)
        
        # 4. Animate it
        if shot_img:
            print(f"\n🚀 Animating the Shot: {shot_img}")
            cinema.animate_shot(shot_img, f"The detective turns her head to look at the billboard, rain falling heavily. {angle_prompt}")
            
    except Exception as e:
        print(f"\n❌ Workflow Failed: {e}")

if __name__ == "__main__":
    run_cinema_demo()
