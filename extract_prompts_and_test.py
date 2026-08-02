
import os
import asyncio
from visions.skills.visual.service import VisionService, MODEL_NANO_BANANA_PRO
from visions.core.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prompts extracted from the Cookbook
PROMPTS = [
    {
        "name": "watercolor_map_germany",
        "text": "Generate a map of Germany in watercolor style, on which all federal states are labeled in ballpoint pen."
    },
    {
        "name": "tech_founder_portrait",
        "text": "Personal brand visual for a modern tech founder. Natural soft lighting, neutral tones, editorial portrait style, authentic expression, subtle depth of field, calm, confident, and approachable, designed for long-term credibility."
    },
    {
        "name": "vintage_patent_time_machine",
        "text": "A vintage patent document for Time Machine, styled after late 1800s United States Patent Office filings. The page features precise technical drawings with numbered callouts (Fig. 1, Fig. 2, Fig. 3) showing front, side, and exploded views. Handwritten annotations in fountain-pen ink describe mechanisms. The paper is aged ivory with foxing stains and soft fold creases. An official embossed seal and red wax stamp appear in the corner. A hand-signed inventor's name and date appear at the bottom. The entire image feels like a recovered archival document—authoritative, historic, and slightly mysterious."
    }
]

def test_prompts():
    print(f"Testing prompts with Model: {MODEL_NANO_BANANA_PRO} (Global Location)")
    
    # Initialize VisionService
    # Note: VisionService uses Config.VERTEX_PROJECT_ID and logic for global location internally
    service = VisionService()
    
    for prompt_data in PROMPTS:
        name = prompt_data["name"]
        text = prompt_data["text"]
        print(f"\n--- Generating: {name} ---")
        print(f"Prompt: {text[:100]}...")
        
        try:
            # We use the service's generate_image method which handles the client creation
            # The service should automatically use the global endpoint for this model
            result = service.generate_image(
                prompt=text,
                number_of_images=1,
                aspect_ratio="16:9",
                mode="pro", # Forces MODEL_NANO_BANANA_PRO
                output_path=f"test_gen_{name}.png"
            )
            
            if result and not result.startswith("Error"):
                print(f"✅ Success! Image saved to: {result}")
            else:
                print(f"❌ Failed: {result}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_prompts()
