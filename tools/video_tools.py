"""
Veo 3.1 Video Generation Tools
Implements capabilities to generate high-fidelity videos using Veo 3.1 models via Gemini API.
"""
import time
import os
import logging
from typing import List, Optional, Union

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("⚠️ google.genai not found. Please install: pip install google-genai")
    genai = None
    types = None

# Configure logging
logger = logging.getLogger(__name__)

class VeoDirector:
    """
    Manages video generation tasks using Veo 3.1 models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not genai:
            raise ImportError("The 'google.genai' package is required for VeoDirector.")
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        # Initialize client
        self.client = genai.Client(http_options={'api_version': 'v1beta'}) 

    def generate_video(self, 
                       prompt: str, 
                       model: str = "veo-3.1-generate-preview",
                       negative_prompt: Optional[str] = None,
                       aspect_ratio: str = "16:9",
                       resolution: str = "720p",
                       duration_seconds: str = "8",
                       output_path: str = "generated_video.mp4") -> Optional[str]:
        """
        Generates a video from text using Veo 3.1.
        """
        logger.info(f"🎬 Starting Text-to-Video generation: {prompt[:50]}...")
        
        try:
            config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                duration_seconds=duration_seconds,
                negative_prompt=negative_prompt
            )

            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                config=config
            )
            
            return self._poll_and_save(operation, output_path)

        except Exception as e:
            logger.error(f"❌ Video Generation Failed: {e}")
            return None

    def animate_image(self, 
                      image_path: str,
                      prompt: str,
                      model: str = "veo-3.1-generate-preview",
                      negative_prompt: Optional[str] = None,
                      aspect_ratio: str = "16:9",
                      output_path: str = "animated_video.mp4") -> Optional[str]:
        """
        Generates a video from an initial image (Image-to-Video).
        """
        logger.info(f"🖼️🎬 Animating Image ({image_path})...")
        
        try:
            # Load image
            if not os.path.exists(image_path):
                 raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Using types.Image.from_file is standard in new SDK, or read bytes
            # For robustness, we check if the SDK supports passing path directly or needs bytes
            # The docs used `image=types.Image.from_file` or loaded `client.models.generate_content` parts.
            # Here we assume we load it locally.
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            
            image_blob = types.Image(image_bytes=img_bytes, mime_type="image/png") # Assuming PNG for now

            config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt,
                person_generation="allow_adult" # Required for image-to-video
            )

            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                image=image_blob,
                config=config
            )

            return self._poll_and_save(operation, output_path)

        except Exception as e:
            logger.error(f"❌ Image Animation Failed: {e}")
            return None

    def generate_with_references(self,
                                 prompt: str,
                                 reference_image_paths: List[str],
                                 model: str = "veo-3.1-generate-preview",
                                 output_path: str = "ref_guided_video.mp4") -> Optional[str]:
        """
        Generates a video using style/character reference images (up to 3).
        """
        logger.info(f"🎨 Generating with {len(reference_image_paths)} references...")
        
        try:
            references = []
            for path in reference_image_paths:
                with open(path, "rb") as f:
                    img_data = f.read()
                # Create VideoGenerationReferenceImage objects
                ref_obj = types.VideoGenerationReferenceImage(
                    image=types.Image(image_bytes=img_data, mime_type="image/png"),
                    reference_type="asset" # 'asset' uses it for subject/style
                )
                references.append(ref_obj)
            
            config = types.GenerateVideosConfig(
                reference_images=references,
                duration_seconds="8", # Must be 8s for references
                person_generation="allow_adult"
            )
            
            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                config=config
            )
            
            return self._poll_and_save(operation, output_path)

        except Exception as e:
            logger.error(f"❌ Reference Generation Failed: {e}")
            return None

    def _poll_and_save(self, operation, output_path: str) -> Optional[str]:
        """
        Internal helper to poll operation and save the result.
        """
        try:
            while not operation.done:
                logger.info("⏳ Waiting for video generation...")
                time.sleep(10)
                operation = self.client.operations.get(operation)
            
            if operation.response and operation.response.generated_videos:
                video_result = operation.response.generated_videos[0]
                logger.info(f"📥 Downloading video to {output_path}...")
                
                # Check directly if bytes are available or we need download helper
                # Docs simplify this to client.files.download usually if it's a file API ref
                # But sometimes it's inline bytes? SDK implies `video.video` is a file resource.
                
                # If it's a File API resource:
                self.client.files.download(file=video_result.video)
                video_result.video.save(output_path)
                
                logger.info(f"✅ Video saved: {output_path}")
                return output_path
            else:
                logger.error("❌ Operation completed but no video returned.")
                return None
                
        except Exception as e:
            logger.error(f"❌ Polling/Saving Failed: {e}")
            raise e
