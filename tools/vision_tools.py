#!/usr/bin/env python3
"""
Vision Tools for Visions AI
Powered entirely by Gemini 3 Pro Image Preview - Google's flagship multimodal model.

Showcases Gemini 3 Pro's capabilities:
- Visual question answering (VQA)
- Image generation from text
- Image understanding and captioning
- Composition analysis
"""

from google import genai
from google.genai import types
from typing import Optional, Dict, List
import base64
from io import BytesIO
from PIL import Image as PIL_Image
import os


class VisionTools:
    """
    Comprehensive vision toolkit showcasing Gemini 3 Pro Image Preview.
    
    ONE MODEL for everything:
    - Visual understanding (VQA, captioning, analysis)
    - Image generation (text-to-image)
    - Multimodal reasoning
    """
    
    def __init__(self, project_id: str = "endless-duality-480201-t3", location: str = "global"):
        self.project_id = project_id
        self.location = location  # Always global for Gemini 3 Pro
        
        # Don't initialize client in __init__ - use property for lazy loading
        # This avoids pickling issues when deploying to Vertex AI
        self._client = None
        
        self.model = "gemini-3-pro-image-preview"  # THE flagship model
        # No print statements in __init__ - they cause issues during pickle
    
    @property
    def client(self):
        """Lazy-load the genai.Client to avoid pickling issues."""
        if self._client is None:
            self._client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location  # Global routing required
            )
        return self._client
    
    
    # ==================== Visual Understanding ====================
    
    
    def visual_question_answer(self, image_path: str, question: str) -> str:
        """
        Answer questions about an image using Gemini 3 Pro Image Preview.
        
        Perfect for composition analysis, technical feedback, lighting assessment.
        
        Args:
            image_path: Path to image file
            question: Question about the image
            
        Returns:
            Answer from Gemini 3 Pro
        """
        try:
            # Load image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Create image part
            image_part = types.Part.from_bytes(
                data=image_data,
                mime_type=self._get_mime_type(image_path)
            )
            
            # Query Gemini 3 Pro with vision understanding
            response = self.client.models.generate_content(
                model=self.model,
                contents=[question, image_part],
                config=types.GenerateContentConfig(
                    temperature=0.4,  # More factual for analysis
                    system_instruction=(
                        "You are an expert photography analyst. Provide detailed, "
                        "technical answers about composition, lighting, and visual elements. "
                        "Be specific and actionable."
                    )
                )
            )
            
            return response.text
            
        except Exception as e:
            return f"VQA Error: {str(e)}"
    
    
    def analyze_composition(self, image_path: str) -> Dict[str, str]:
        """
        Comprehensive composition analysis using Gemini 3 Pro VQA.
        
        Returns multiple aspects:
        - Rule of thirds adherence
        - Leading lines
        - Balance and symmetry
        - Visual weight distribution
        - Suggested improvements
        """
        questions = {
            "rule_of_thirds": "Does this image follow the rule of thirds? Where are the key focal points?",
            "leading_lines": "Identify any leading lines in this composition. How do they guide the viewer's eye?",
            "balance": "Analyze the visual balance and symmetry. Is it balanced or intentionally asymmetrical?",
            "visual_weight": "Where is the visual weight concentrated? Describe the distribution.",
            "improvements": "What are 3 specific compositional improvements that could be made to this image?"
        }
        
        analysis = {}
        for aspect, question in questions.items():
            print(f"🔍 Analyzing: {aspect}...")
            analysis[aspect] = self.visual_question_answer(image_path, question)
        
        return analysis
    
    
    def caption_image(self, image_path: str, style: str = "detailed") -> str:
        """
        Generate captions for images using Gemini 3 Pro.
        
        Args:
            image_path: Path to image
            style: "detailed", "concise", or "technical"
            
        Returns:
            Generated caption
        """
        style_prompts = {
            "detailed": "Provide a detailed description of this image, including all visual elements, composition, lighting, and mood.",
            "concise": "Write a concise, single-sentence caption for this image.",
            "technical": "Provide a technical description of this image focusing on camera settings, lighting setup, and photographic techniques used."
        }
        
        prompt = style_prompts.get(style, style_prompts["detailed"])
        return self.visual_question_answer(image_path, prompt)
    
    
    # ==================== Image Generation (Gemini 3 Pro) ====================
    
    def generate_image(
        self,
        prompt: str,
        output_path: Optional[str] = None,
        aspect_ratio: str = "1:1"
    ) -> str:
        """
        Generate images using Gemini 3 Pro Image Preview.
        
        Args:
            prompt: Description of desired image
            output_path: Where to save image (optional)
            aspect_ratio: "1:1", "16:9", "9:16", "4:3", "3:4"
            
        Returns:
            Path to generated image
        """
        try:
            print(f"🎨 Generating with Gemini 3 Pro: {prompt[:60]}...")
            
            # Generate with Gemini 3 Pro
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=1.0,  # Creative for generation
                    response_modalities=["image"],  # Request image output
                )
            )
            
            # Extract generated image
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        # Save image
                        if output_path is None:
                            output_path = f"generated_{hash(prompt) % 10000}.png"
                        
                        image_data = part.inline_data.data
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        
                        print(f"✅ Image generated and saved to: {output_path}")
                        return output_path
            
            return "Error: No image in response"
            
        except Exception as e:
            return f"Generation Error: {str(e)}"
    
    
    def edit_image_with_prompt(
        self,
        image_path: str,
        edit_instruction: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Edit an image using Gemini 3 Pro's multimodal understanding.
        
        Provides the image and instructions, Gemini 3 Pro generates edited version.
        
        Args:
            image_path: Path to original image
            edit_instruction: What changes to make
            output_path: Where to save edited image
            
        Returns:
            Path to edited image
        """
        try:
            # Load original image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            image_part = types.Part.from_bytes(
                data=image_data,
                mime_type=self._get_mime_type(image_path)
            )
            
            # Create edit prompt combining image + instruction
            full_prompt = f"Based on this image, {edit_instruction}. Generate the edited version."
            
            print(f"✏️ Editing with Gemini 3 Pro...")
            
            # Generate edited version
            response = self.client.models.generate_content(
                model=self.model,
                contents=[full_prompt, image_part],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_modalities=["image"]
                )
            )
            
            # Save edited image
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        if output_path is None:
                            base, ext = os.path.splitext(image_path)
                            output_path = f"{base}_edited{ext}"
                        
                        image_data = part.inline_data.data
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        
                        print(f"✅ Image edited and saved to: {output_path}")
                        return output_path
            
            return "Error: No edited image in response"
            
        except Exception as e:
            return f"Edit Error: {str(e)}"
    
    
    # ==================== Advanced Prompting (Nano Banana Pro Strategy) ====================
    
    def image_to_prompt(self, image_path: str) -> str:
        """
        Reverse engineer a prompt from an existing image.
        
        Analyzes composition, lighting, camera settings, and generates
        a detailed JSON prompt that could recreate similar images.
        
        Perfect for:
        - Learning from reference photos
        - Extracting techniques from examples
        - Student analysis of professional work
        
        Args:
            image_path: Path to reference image
            
        Returns:
            JSON prompt string
        """
        analysis_prompt = """
        Analyze this photography image and create a detailed JSON prompt for Gemini 3 Pro Image Preview.
        
        Extract and describe:
        
        1. SUBJECT & ACTION:
           - What/who is the main subject?
           - What action or pose?
        
        2. LIGHTING ANALYSIS:
           - Type (natural/studio/mixed)
           - Direction and quality (hard/soft)
           - Setup (if studio: key, fill, rim lights)
           - Estimated ratios
        
        3. CAMERA TECHNICAL:
           - Estimated focal length (based on perspective)
           - Aperture (based on depth of field)
           - Likely ISO and shutter speed
           - Camera angle and position
        
        4. COMPOSITION:
           - Rule of thirds adherence
           - Leading lines present?
           - Visual weight distribution
           - Negative space usage
        
        5. STYLE & QUALITY:
           - Photography style/genre
           - Color grading/mood
           - Post-processing apparent
        
        OUTPUT FORMAT (JSON):
        {
          "subject": "...",
          "action": "...",
          "environment": "...",
          "lighting": {
            "type": "...",
            "setup": "...",
            "ratio": "..."
          },
          "camera": {
            "model": "professional camera body",
            "lens": "estimated focal length and aperture",
            "settings": {"aperture": "...", "shutter": "...", "iso": ...}
          },
          "composition": {
            "rule": "...",
            "techniques": [...]
          },
          "style": "photorealistic, 8k, professional photography",
          "quality": "ultra-detailed, sharp focus"
        }
        
        Return ONLY the JSON, no other text.
        """
        
        print(f"🔍 Analyzing image: {os.path.basename(image_path)}...")
        return self.visual_question_answer(image_path, analysis_prompt)
    
    
    def generate_json_prompt(self, concept: str) -> str:
        """
        Generate a detailed JSON prompt from a simple concept using meta-prompting.
        Leverages Gemini 3 Pro's 'Sharper Thinking' strategies: Power Words & Design Keywords.
        
        Args:
            concept: Simple description (e.g., "portrait with shallow DoF")
            
        Returns:
            Detailed JSON prompt ready for generation
        """
        meta_prompt = f"""
        You are a **World-Class Photography Director and Expert Prompt Engineer** with over 80 years of experience.
        You have won multiple Pulitzer Prizes for visual storytelling and technical excellence.
        
        Your task is to create the **Ultimate JSON Prompt** for this concept: "{concept}"
        
        **STRATEGY:**
        1. **Critique**: First, mentally analyze the simple concept. What makes it boring? What would make it *breathtaking*?
        2. **Refine**: Apply "Power Words" and specific design keywords (e.g., "cinematic", "subtle gradients", "visual hierarchy", "glowing", "pristine").
        3. **Construct**: Build the JSON with technical precision.
        
        **REQUIRED ELEMENTS (The "Secret Sauce"):**
        
        1. **Subject**: Specific person/object. Make it *captivating*.
        2. **Technique**: The specific photographic principle (e.g., "Rembrandt Lighting", "Golden Ratio").
        3. **Lighting Setup (Crucial)**:
           - "Cinematic", "Volumetric", "Softbox", "God Rays"
           - Precise Ratios (e.g., 3:1 Split)
           - Color Temperatures (e.g., "Warm Sunset vs Cool Blue Hour")
        4. **Camera Details (Professional)**:
           - High-end Sensor (e.g., "Phase One IQ4", "Sony A1")
           - Prime Lens (e.g., "85mm f/1.2 G Master")
           - Settings: fast aperture for bokeh, low ISO for clarity.
        5. **Composition**:
           - "Rule of Thirds", "Leading Lines", "Dynamic Symmetry"
           - "Visual Flow", "Negative Space"
        6. **Arnheim Visual Theory**:
           - "Visual Weight", "Balance", "Perceptual Forces"
        7. **Quality Tokens (Power Words)**:
           - "8k", "photorealistic", "award-winning", "masterpiece", "ultra-detailed", "unreal engine 5 render style"
        
        OUTPUT: Complete JSON in this exact format:
        
        {{
          "subject": "...",
          "technique": "{concept}",
          "environment": "...",
          "lighting": {{
            "type": "...",
            "key_light": "...",
            "fill_light": "...",
            "ratio": "..."
          }},
          "camera": {{
            "model": "...",
            "lens": "...",
            "settings": {{"aperture": "...", "shutter": "...", "iso": ...}}
          }},
          "composition": {{
            "rule": "...",
            "subject_position": "...",
            "negative_space": "..."
          }},
          "arnheim_principle": "...",
          "style": "photorealistic, 8k, professional photography, ultra-detailed, award-winning",
          "quality": "sharp focus, professional lighting, studio quality, masterpiece"
        }}
        
        Return ONLY the JSON, no explanation.
        """
        
        print(f"🎨 Generating 'World-Class' JSON prompt for: {concept}...")
        
        # Use Gemini 3 Pro to generate the prompt
        response = self.client.models.generate_content(
            model=self.model,
            contents=[meta_prompt],
            config=types.GenerateContentConfig(
                temperature=0.8,  # Higher creativity for "Sharper" thinking
            )
        )
        
        return response.text
    
    
    def enhance_simple_prompt(self, simple_prompt: str) -> str:
        """
        Convert a basic prompt to detailed JSON using 'Expert Designer' strategy.
        
        Example:
            Input: "portrait photo"
            Output: Detailed JSON with camera, lighting, composition, power words.
        
        Args:
            simple_prompt: Basic description
            
        Returns:
            Enhanced JSON prompt
        """
        enhancement_prompt = f"""
        You are an **Expert Visual Designer and Photography Director** with a portfolio of award-winning work.
        
        Transform this basic request into a **Professional Grade** photography prompt (JSON):
        
        Input: "{simple_prompt}"
        
        **Enhancement Instructions:**
        1. **Elevate**: Make it sound expensive, high-end, and technically perfect.
        2. **Power Words**: Use words like "Nebulous", "Ethereal", "Pristine", "Gritty", "Cinematic", "Volumetric Fog", "Subsurface Scattering".
        3. **Specifics**: 
           - Camera: "Leica M11", "Hasselblad X2D"
           - Lighting: "Rembrandt", "Split", "Butterfly", "Practical Lights"
           - Lens: "Noctilux 50mm f/0.95"
        4. **Visual Theory**: Explicitly mention "Visual Weight", "Leading Lines", or "Dynamic Tension".
        
        Output as JSON with this structure:
        {{
          "subject": "enhanced from input",
          "lighting": {{"type": "...", "setup": "...", "mood": "..."}},
          "camera": {{"model": "...", "lens": "...", "settings": {{}}}},
          "composition": {{"rule": "...", "elements": ["...", "..."]}},
          "style": "photorealistic, 8k, professional, award-winning, cinematic",
          "power_words": ["...", "..."]
        }}
        
        Return ONLY JSON, no other text.
        """
        
        print(f"✨ Enhancing prompt with 'Sharper Thinking' strategies: '{simple_prompt[:50]}...'")
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[enhancement_prompt],
            config=types.GenerateContentConfig(temperature=0.7)
        )
        
        return response.text
    
    
    def analyze_ui_design(self, image_path: str) -> str:
        """
        Analyze a UI screenshot to extract 'Vibe Coding' ingredients.
        (Based on Ming's strategy for $5k+ websites).
        
        Extracts:
        - Layout (Bento, Split, Left-Align)
        - Visual Style (Glassmorphism, Flat, Brutalist, Linear-style)
        - Color Palette (Hex codes & Vibes)
        - Animations (Beam, Glow, Fade-ins)
        - Components (Cards, Heros, Sticky Headers)
        
        Args:
            image_path: Path to UI screenshot
            
        Returns:
            JSON string detailed design analysis
        """
        prompt = """
        You are a World-Class UI/UX Designer (Specialist in 'Vibe Coding').
        Analyze this screenshot ingredient-by-ingredient.
        
        Extract the following in JSON format:
        1. **Style**: (e.g., "Linear-like", "Glassmorphism", "Apple-style", "Brutalist")
        2. **Layout**: (e.g., "Bento Grid", "Split Hero", "Sticky Header")
        3. **Colors**: Dominant hex codes and the "Vibe" (e.g., "Muted Blue", "Neon Purple")
        4. **Typography**: Estimated font categories (e.g., "Space Mono", "Inter-like")
        5. **Animations**: Implied or visible effects (e.g., "Glow", "Beam", "Progressive Blur")
        6. **Components**: List key actionable components.
        
        JSON OUTPUT ONLY.
        """
        print(f"🎨 Analyzing UI Vibe: {os.path.basename(image_path)}...")
        return self.visual_question_answer(image_path, prompt)

    def generate_web_design_prompt(self, concept: str, style: str = "Modern SaaS") -> str:
        """
        Generate a 'Vibe Coding' prompt for building beautiful websites.
        Uses specific vocabulary (Glassmorphism, Beam Animations, Bento).
        
        Args:
            concept: What the website is for (e.g., "AI SDR Agency")
            style: Design direction
            
        Returns:
            A prompt optimized for Gemini 3 / Cursor.
        """
        meta_prompt = f"""
        Act as Ming (Expert Vibe Coder). 
        Write a high-converting, design-centric prompt to build a website for: "{concept}".
        Target Style: {style}.
        
        **REQUIRED KEYWORDS TO USE**:
        - "Glassmorphism" or "Claymorphism" (if applicable)
        - "Bento Grid Layout"
        - "Beam Animations" / "Glowing Borders"
        - "Progressive Blur" on headers
        - "Noise Texture" or "Subtle Gradients"
        - "Inter" or "Space Grotesk" typography
        
        **STRUCTURE THE PROMPT FOR AN AI CODER**:
        1. **Role**: "You are an expert web developer..."
        2. **Ingredients**: breakdown of the visual style.
        3. **Tech Stack**: React, Tailwind, Framer Motion.
        4. **Step-by-Step**: Hero -> Features -> Pricing.
        
        Output the PROMPT text only.
        """
        print(f"✨ Generating Vibe Coding Prompt for: {concept}...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=[meta_prompt],
            config=types.GenerateContentConfig(temperature=0.7)
        )
        return response.text
    
    
    # ==================== Video Understanding ====================

    def analyze_video(self, video_path: str, prompt: str) -> str:
        """
        Analyze video content using Gemini 3 Pro.
        
        Args:
            video_path: Path to video file
            prompt: Question or instruction for video analysis
            
        Returns:
            Analysis text from Gemini 3 Pro
        """
        import mimetypes
        try:
             print(f"🎬 Processing Video via VisionTools: {video_path}")
             
             # Read video data
             with open(video_path, "rb") as f:
                 video_data = f.read()
             
             # Determine mime
             mime_type, _ = mimetypes.guess_type(video_path)
             if not mime_type: mime_type = "video/mp4"
             
             video_part = types.Part.from_bytes(
                 data=video_data, 
                 mime_type=mime_type
             )
             
             # Generate with Gemini 3 Pro (Video capable)
             # Explicitly using gemini-3-pro-preview for video as per original implementation
             print("📤 Sending video payload to Gemini 3 Pro...")
             response = self.client.models.generate_content(
                 model="gemini-3-pro-preview", 
                 contents=[prompt, video_part],
                 config=types.GenerateContentConfig(
                     temperature=1.0
                 )
             )
             
             return f"**Gemini 3 Video Analysis**:\n{response.text}"
             
        except Exception as e:
             return f"Error analyzing video: {str(e)}"


    # ==================== Helper Methods ====================
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')


# ==================== Standalone Functions ====================

def quick_vqa(image_path: str, question: str, project_id: str = "endless-duality-480201-t3") -> str:
    """
    Quick VQA without instantiating class.
    
    Usage:
        answer = quick_vqa("photo.jpg", "What's the main subject?")
    """
    tools = VisionTools(project_id=project_id)
    return tools.visual_question_answer(image_path, question)


def quick_generate(prompt: str, output_path: str = None, project_id: str = "endless-duality-480201-t3") -> str:
    """
    Quick image generation with Gemini 3 Pro.
    
    Usage:
        path = quick_generate("a sunset over mountains")
    """
    tools = VisionTools(project_id=project_id)
    return tools.generate_image(prompt, output_path)


# ==================== Test/Demo ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Vision Tools Demo - Powered by Gemini 3 Pro")
    parser.add_argument("--image", help="Path to image (for VQA/caption/composition/edit/analyze)")
    parser.add_argument("--mode", choices=["vqa", "caption", "composition", "generate", "edit", "analyze", "json", "enhance"], 
                       default="generate", help="Operation mode")
    parser.add_argument("--question", help="Question for VQA mode")
    parser.add_argument("--prompt", help="Prompt for generate/edit mode OR concept for json/enhance mode")
    parser.add_argument("--output", help="Output path for generated/edited image")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🎨 VISIONS AI - VISION TOOLS")
    print("   Powered by Gemini 3 Pro Image Preview (Google's Flagship Model)")
    print("=" * 80)
    print()
    
    tools = VisionTools()
    
    if args.mode == "generate":
        if not args.prompt:
            print("❌ --prompt required for generate mode")
            print("Example: --mode generate --prompt 'a professional photography studio'")
        else:
            result = tools.generate_image(args.prompt, args.output)
            print(f"\n✅ Result: {result}")
    
    elif args.mode == "vqa":
        if not args.image:
            print("❌ --image required for VQA mode")
        else:
            question = args.question or "Describe this image in detail."
            print(f"❓ Question: {question}\n")
            answer = tools.visual_question_answer(args.image, question)
            print(f"💬 Answer:\n{answer}")
    
    elif args.mode == "caption":
        if not args.image:
            print("❌ --image required for caption mode")
        else:
            print("📝 Generating caption...\n")
            caption = tools.caption_image(args.image, style="detailed")
            print(f"📸 Caption:\n{caption}")
    
    elif args.mode == "composition":
        if not args.image:
            print("❌ --image required for composition mode")
        else:
            print("🔍 Analyzing composition...\n")
            analysis = tools.analyze_composition(args.image)
            for aspect, result in analysis.items():
                print(f"\n📊 {aspect.replace('_', ' ').title()}:")
                print(f"   {result}")
    
    elif args.mode == "edit":
        if not args.image or not args.prompt:
            print("❌ --image and --prompt required for edit mode")
            print("Example: --mode edit --image photo.jpg --prompt 'make the sky more dramatic'")
        else:
            result = tools.edit_image_with_prompt(args.image, args.prompt, args.output)
            print(f"\n✅ Result: {result}")
    
    elif args.mode == "analyze":
        if not args.image:
            print("❌ --image required for analyze mode")
            print("Example: --mode analyze --image reference.jpg")
        else:
            print("🔍 Analyzing image to extract JSON prompt...\n")
            json_prompt = tools.image_to_prompt(args.image)
            print(f"\n📋 Generated JSON Prompt:\n{json_prompt}")
    
    elif args.mode == "json":
        if not args.prompt:
            print("❌ --prompt required for json mode")
            print("Example: --mode json --prompt 'portrait with shallow depth of field'")
        else:
            json_prompt = tools.generate_json_prompt(args.prompt)
            print(f"\n📋 Generated JSON Prompt:\n{json_prompt}")
    
    elif args.mode == "enhance":
        if not args.prompt:
            print("❌ --prompt required for enhance mode")
            print("Example: --mode enhance --prompt 'sunset portrait'")
        else:
            enhanced = tools.enhance_simple_prompt(args.prompt)
            print(f"\n✨ Enhanced Prompt:\n{enhanced}")
    
    print("\n" + "=" * 80)
