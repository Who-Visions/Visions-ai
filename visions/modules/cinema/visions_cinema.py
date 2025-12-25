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
            model='imagen-3.0-generate-001',
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
        def generate_shot(self, base_image_path: str, shot_type: str, angle_prompt: str, character_description: str, lens_type: str = "standard") -> str:
            """
            Step 3: Camera Angle Control using Gemini 3 Pro Image (generate_images)
            """
            print(f"📸 Generating Shot: {shot_type} (Lens: {lens_type})...")
            
            # Lens Logic
            lens_specs = {
                "standard": "35mm prime lens, natural depth of field.",
                "anamorphic": "2.39:1 anamorphic lens, oval bokeh, blue horizontal lens flares, cinematic wide compression.",
                "tilt-shift": "Tilt-shift lens, miniature effect, extreme selective focus, sharp center with blurred top/bottom.",
                "macro": "100mm macro lens, extreme close-up, microscopic detail, paper-thin depth of field.",
                "wide": "14mm wide-angle lens, slight barrel distortion, deep focus, expansive environment.",
                "reality_bleed": "Practical projection mapping, volumetric blue hour lighting, digital noise overlay on physical surfaces, high contrast chiaroscuro."
            }
            
            spec = lens_specs.get(lens_type, lens_specs["standard"])
            
            full_prompt = (
                f"CINEMATIC SHOT: {shot_type}. "
                f"Lens Specification: {spec}. "
                f"Character: {character_description}. "
                f"Action/Angle: {angle_prompt}. "
                "Photorealistic, 8k, movie still."
            )
    
            # Using generate_images for native image synthesis
            response = self.global_client.models.generate_images(
                model='gemini-3-pro-image-preview',
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_mime_type="image/png"
                )
            )
            
            if response and response.generated_images:
                filepath = OUTPUT_DIR / f"shot_{shot_type.replace(' ','_')}_{int(time.time())}.png"
                response.generated_images[0].image.save(str(filepath))
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
    print("🎬 VISIONS CINEMA: Starting Anamorphic Test (Ghost)...")
    cinema = VisionsCinema()
    
    # 1. Define Character
    char_desc = "A futuristic cyberpunk detective, neon blue hair, trench coat, walking away into neon mist"
    
    try:
        # 2. Generate Base
        # base_img = cinema.generate_character_base(char_desc, "Ghost_Detective")
        print(f"👤 [DRY RUN] Simulating base character generation for: {char_desc}")
        base_img = "mock_output/ghost_base.png"
        
        # 3. Generate Anamorphic Shot
        angle_name = "Reality Bleed (Chiaroscuro)"
        angle_prompt = "Detective finding their own hologram projected onto the wet pavement. Blue hour lighting vs red warning holograms."
        
        # NOTE: In a real run, we would call API. For DRY RUN, we mock the output.
        print(f"🎭 [DRY RUN] Simulating shot generation for: {angle_name}")
        print(f"   Lens: reality_bleed")
        print(f"   Prompt: {angle_prompt}")
        shot_img = "mock_output/reality_bleed_shot.png" # Mock path
        # shot_img = cinema.generate_shot(base_img, angle_name, angle_prompt, char_desc, lens_type="reality_bleed")
        
        # 4. Animate it (DISABLED PER ECHO CONSTRAINTS - DRY RUN ONLY)
        if shot_img and False: # FORCE DISABLED
            print(f"\n🚀 Animating the Shot: {shot_img}")
            cinema.animate_shot(shot_img, f"The detective turns her head to look at the billboard, rain falling heavily. {angle_prompt}")
        else:
             print(f"\n🚫 Animation Skipped (DRY RUN PROTOCOL ACTIVE)")
            
    except Exception as e:
        print(f"\n❌ Workflow Failed: {e}")

if __name__ == "__main__":
    run_cinema_demo()
