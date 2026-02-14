"""
Vision Service
Powered by:
- Nano Banana (Gemini 2.5 Flash Image & Gemini 3 Pro Image Preview)
- Veo 3.1 (State-of-the-art Video Generation)

Handles VQA, image generation/editing, and high-fidelity video creation.
"""

from google import genai
from google.genai import types
from typing import Optional, Dict, List, Union, Any
import base64
import time
import os
import json
import logging
import mimetypes

logger = logging.getLogger(__name__)

# Model Constants
MODEL_NANO_BANANA_FAST = "gemini-2.5-flash-image"
MODEL_NANO_BANANA_PRO = "gemini-3-pro-image-preview"
MODEL_VEO = "veo-3.1-generate-001"
MODEL_VEO_FAST = "veo-3.1-fast-generate-001"

class VisionService:
    """
    Comprehensive vision toolkit for Who Visions OS.
    Integrates Nano Banana (Image) and Veo 3.1 (Video).
    """
    
    def __init__(self, project_id: str = "endless-duality-480201-t3", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self._client = None
        # Default text/analysis model
        self.analysis_model = "gemini-2.0-flash-exp" 

    @property
    def client(self):
        """Lazy-load the genai.Client."""
        if self._client is None:
            self._client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
        return self._client

    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'

    def _poll_operation(self, operation: Any, interval: int = 10) -> Any:
        """Polls a long-running operation until complete."""
        logger.info(f"Polling operation {operation.name}...")
        while not operation.done:
            time.sleep(interval)
            operation = self.client.operations.get(operation)
        return operation

    # =========================================================================
    #  NANO BANANA: IMAGE GENERATION & EDITING
    # =========================================================================

    def generate_image(self, 
                       prompt: str, 
                       output_path: Optional[str] = None, 
                       mode: str = "pro", 
                       aspect_ratio: str = "1:1",
                       person_generation: str = "allow_adult",
                       number_of_images: int = 1) -> Union[str, List[str]]:
        """
        Generate images using Nano Banana models.
        
        Args:
            prompt: Text description.
            output_path: Path to save image. If None, auto-generated.
            mode: "fast" (Gemini 2.5 Flash) or "pro" (Gemini 3 Pro).
            aspect_ratio: "1:1", "16:9", "9:16", "4:3", "3:4".
            person_generation: "allow_adult" or "dont_allow".
            number_of_images: Number of images to generate (1-4).
        """
        model = MODEL_NANO_BANANA_FAST if mode == "fast" else MODEL_NANO_BANANA_PRO
        
        try:
            logger.info(f"Generating image ({mode}): {prompt[:60]}...")
            
            config = types.GenerateContentConfig(
                temperature=1.0, 
                response_modalities=["image"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    person_generation=person_generation
                ),
                candidate_count=number_of_images
            )
            
            response = self.client.models.generate_content(
                model=model,
                contents=[prompt],
                config=config
            )
            
            saved_paths = []
            if response.candidates:
                for idx, candidate in enumerate(response.candidates):
                    for part in candidate.content.parts:
                        if part.inline_data:
                            # Generate path
                            if output_path:
                                if number_of_images > 1:
                                    base, ext = os.path.splitext(output_path)
                                    final_path = f"{base}_{idx}{ext}"
                                else:
                                    final_path = output_path
                            else:
                                final_path = f"generated_{hash(prompt) % 10000}_{idx}.png"
                            
                            # Save
                            image_data = part.inline_data.data
                            with open(final_path, "wb") as f:
                                f.write(image_data)
                            saved_paths.append(final_path)
            
            if not saved_paths:
                return "Error: No image in response"
                
            return saved_paths[0] if len(saved_paths) == 1 else saved_paths

        except Exception as e:
            logger.error(f"Image Generation Error: {e}")
            return f"Generation Error: {str(e)}"

    def edit_image(self, 
                   image_path: str, 
                   prompt: str, 
                   output_path: Optional[str] = None,
                   mode: str = "fast") -> str:
        """Edit an image with text instructions (Inpainting/Editing)."""
        model = MODEL_NANO_BANANA_FAST if mode == "fast" else MODEL_NANO_BANANA_PRO
        
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            image_part = types.Part.from_bytes(
                data=image_data,
                mime_type=self._get_mime_type(image_path)
            )
            
            response = self.client.models.generate_content(
                model=model,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(
                    response_modalities=["image"]
                )
            )
            
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.inline_data:
                    if output_path is None:
                        base, ext = os.path.splitext(image_path)
                        output_path = f"{base}_edited{ext}"
                    
                    with open(output_path, "wb") as f:
                        f.write(part.inline_data.data)
                    return output_path
            return "Error: No edited image generated"
        except Exception as e:
            return f"Edit Error: {str(e)}"

    # =========================================================================
    #  VEO 3.1: VIDEO GENERATION
    # =========================================================================

    def generate_video(self, 
                      prompt: str, 
                      output_path: Optional[str] = None,
                      aspect_ratio: str = "16:9",
                      resolution: str = "720p",
                      duration_seconds: str = "8",
                      negative_prompt: Optional[str] = None,
                      image_path: Optional[str] = None,
                      last_frame_path: Optional[str] = None,
                      use_fast: bool = False) -> str:
        """
        Generate video using Veo 3.1.
        
        Args:
            prompt: Text description of the video.
            output_path: Output .mp4 path.
            aspect_ratio: "16:9" or "9:16".
            resolution: "720p", "1080p" (8s only), "4k" (8s only).
            duration_seconds: "4", "6", or "8".
            negative_prompt: What to avoid.
            image_path: Optional start frame (Image-to-Video).
            last_frame_path: Optional end frame (Interpolation).
            use_fast: Use veo-3.1-fast-generate-preview.
        """
        model = MODEL_VEO_FAST if use_fast else MODEL_VEO
        logger.info(f"Starting Video Generation ({model}): {prompt[:60]}...")

        try:
            # Prepare config
            config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                duration_seconds=duration_seconds,
                negative_prompt=negative_prompt
            )

            # Handle inputs (Prompt + Optional Image)
            contents = [prompt]
            image = None
            
            if image_path:
                with open(image_path, "rb") as f:
                    img_bytes = f.read()
                image = types.Image(
                    image_bytes=img_bytes,
                    mime_type=self._get_mime_type(image_path)
                )

            if last_frame_path:
                with open(last_frame_path, "rb") as f:
                    last_bytes = f.read()
                config.last_frame = types.Image(
                    image_bytes=last_bytes,
                    mime_type=self._get_mime_type(last_frame_path)
                )

            # Start Operation
            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                image=image, # Primary image input for img2vid
                config=config
            )

            # Poll
            operation = self._poll_operation(operation)

            # Save
            if operation.response.generated_videos:
                video = operation.response.generated_videos[0].video
                final_path = output_path or f"veo_gen_{int(time.time())}.mp4"
                
                # Check if we need to download or if bytes are present
                if video.video_bytes:
                     with open(final_path, "wb") as f:
                        f.write(video.video_bytes)
                else:
                    self.client.files.download(file=video).save(final_path)
                
                logger.info(f"Video saved to {final_path}")
                return final_path
            
            return "Error: No video in response"

        except Exception as e:
            logger.error(f"Video Generation Error: {e}")
            return f"Video Error: {str(e)}"

    def extend_video(self,
                     input_video_path: str,
                     prompt: str,
                     output_path: Optional[str] = None) -> str:
        """Extend an existing Veo-generated video."""
        logger.info(f"Extending video {input_video_path}...")
        try:
            # Note: The API requires a Video object from a previous generation.
            # If we only have a file path, we might need to re-upload or use a stored reference.
            # For this implementation, we'll try to upload the video first if the SDK supports uploaded video for extension.
            # *CRITICAL*: Veo extension currently requires the video object from the previous operation response
            # or a freshly generated video in the context. If we are loading from disk, 
            # we must check if the SDK allows passing uploaded bytes as the 'video' argument.
            
            # Per documentation: "video: Video to be used for video extension. Video object from a previous generation"
            # This implies persistence of the object is key. 
            # For now, we will attempt to upload and pass it, but this might fail if the API strictly demands a GenerationArtifact.
            
            # Attempting standard file upload for context
            with open(input_video_path, "rb") as f:
                vid_bytes = f.read()
            
            # Constructing a Video object manually if possible, or using upload
            # The python SDK typed signature usually expects the successful generation response object.
            # This method works best if chained immediately after generation. 
            # For standalone, we might need to rely on ID/URI if persisted.
            
            logger.warning("Video extension typically requires the original generation response object. Proceeding with file upload attempt.")
            
            # Uploading as a fallback context
            # NOTE: Genuine extension of arbitrary mp4s is restricted. This must be a Veo video.
            # We will try to pass standard invocation.

             # Placeholder for actual SDK capability check
            return "Extension currently requires active generation session object."

        except Exception as e:
            return f"Extension Error: {e}"

    # =========================================================================
    #  ANALYSIS & UTILS
    # =========================================================================

    def visual_question_answer(self, image_path: str, question: str) -> str:
        """Answer questions about an image."""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            image_part = types.Part.from_bytes(
                data=image_data,
                mime_type=self._get_mime_type(image_path)
            )
            
            response = self.client.models.generate_content(
                model=self.analysis_model,
                contents=[question, image_part],
                config=types.GenerateContentConfig(temperature=0.4)
            )
            return response.text
        except Exception as e:
            return f"VQA Error: {str(e)}"

    def analyze_composition(self, image_path: str) -> Dict[str, str]:
        """Comprehensive composition analysis."""
        questions = {
            "rule_of_thirds": "Does this image follow the rule of thirds? Where are the key focal points?",
            "leading_lines": "Identify any leading lines in this composition. How do they guide the viewer's eye?",
            "balance": "Analyze the visual balance and symmetry. Is it balanced or intentionally asymmetrical?",
            "visual_weight": "Where is the visual weight concentrated? Describe the distribution.",
            "improvements": "What are 3 specific compositional improvements that could be made to this image?"
        }
        analysis = {}
        for aspect, question in questions.items():
            analysis[aspect] = self.visual_question_answer(image_path, question)
        return analysis

    def caption_image(self, image_path: str, style: str = "detailed") -> str:
        """Generate captions for images."""
        style_prompts = {
            "detailed": "Provide a detailed description of this image, including all visual elements, composition, lighting, and mood.",
            "concise": "Write a concise, single-sentence caption for this image.",
            "technical": "Provide a technical description of this image focusing on camera settings, lighting setup, and photographic techniques used."
        }
        prompt = style_prompts.get(style, style_prompts["detailed"])
        return self.visual_question_answer(image_path, prompt)

    def tag_image(self, image_path: str, allowed_tags: List[str] = None) -> List[str]:
        """Extract relevant keywords from an image."""
        tag_prompt = """
        You are an expert image tagger. Extract all relevant keywords/tags that describe
        the main items, style, color, and mood of this image.
        Return the tags as a JSON list of strings.
        Example: ["blue", "sunset", "landscape", "mountain"]
        """
        if allowed_tags:
            tag_prompt += f"\nAllowed tags (prefer these if applicable): {json.dumps(allowed_tags)}"
            
        response_text = self.visual_question_answer(image_path, tag_prompt)
        
        try:
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start != -1 and end != -1:
                generated_tags = json.loads(response_text[start:end])
            else:
                generated_tags = [t.strip() for t in response_text.replace('"', '').split(',')]

            if allowed_tags:
                final_tags = []
                allowed_set = set([t.lower() for t in allowed_tags])
                for tag in generated_tags:
                    if tag.lower() in allowed_set:
                        final_tags.append(tag.lower())
                return final_tags if final_tags else generated_tags
            
            return generated_tags
        except Exception as e:
            logger.error(f"Tag parsing failed: {e}")
            return []

    def image_to_prompt(self, image_path: str) -> str:
        """Reverse engineer a prompt from an existing image."""
        analysis_prompt = """
        Analyze this photography image and create a detailed image generation prompt.
        Focus on Subject, Action, Lighting, Camera, Composition, and Style.
        Return ONLY the prompt text.
        """
        return self.visual_question_answer(image_path, analysis_prompt)

    def analyze_video(self, video_path: str, prompt: str) -> str:
        """Analyze video content."""
        # Note: This uses standard gemini multimodal, NOT Veo.
        try:
             with open(video_path, "rb") as f:
                 video_data = f.read()
             
             video_part = types.Part.from_bytes(
                 data=video_data, 
                 mime_type=self._get_mime_type(video_path)
             )
             
             response = self.client.models.generate_content(
                 model=self.analysis_model,
                 contents=[prompt, video_part]
             )
             return f"**Video Analysis**:\n{response.text}"
        except Exception as e:
             return f"Error analyzing video: {str(e)}"
