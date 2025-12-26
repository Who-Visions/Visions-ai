#!/usr/bin/env python3
"""
Dual-mode image generation: Vertex AI (primary) + Google AI Studio (fallback)
This ensures continuous availability even during quota exhaustion
"""
from google import genai
from google.genai import types
import vertexai
import os
import time
from datetime import datetime, timedelta
from visions.core.config import Config

class DualModeImageGenerator:
    """
    Image generator that uses Vertex AI first, falls back to AI Studio if quota exhausted
    Includes 60-second rate limiting to prevent 429 errors
    """
    def __init__(self, 
                 project_id: str = "endless-duality-480201-t3",
                 ai_studio_key: str = None,
                 rate_limit_seconds: int = 60):
        self.project_id = project_id
        self.ai_studio_key = ai_studio_key or os.getenv("GOOGLE_AI_STUDIO_API_KEY")
        self.rate_limit_seconds = rate_limit_seconds
        
        # Rate limiting tracking
        self.last_vertex_request = None
        self.last_ai_studio_request = None
        
        # Initialize Vertex AI client (global endpoint)
        vertexai.init(project=project_id, location="us-central1")
        self.vertex_client = genai.Client(
            vertexai=True, 
            project=project_id, 
            location="global"
        )
        
        # Initialize AI Studio client (if key available)
        self.ai_studio_client = None
        if self.ai_studio_key:
            self.ai_studio_client = genai.Client(api_key=self.ai_studio_key)
            print("✅ AI Studio fallback enabled")
        else:
            print("⚠️  AI Studio key not found - fallback disabled")
        
        print(f"⏱️  Rate limiting: {rate_limit_seconds}s cooldown between requests")
    
    def generate_image(self, prompt: str, retries: int = 2) -> dict:
        """
        Generate an image with automatic fallback and rate limiting
        
        Returns:
            dict with keys: success, source, data, mime_type, error
        """
        # Check rate limit for Vertex AI
        if self.last_vertex_request:
            time_since_last = (datetime.now() - self.last_vertex_request).total_seconds()
            if time_since_last < self.rate_limit_seconds:
                wait_time = self.rate_limit_seconds - time_since_last
                print(f"⏳ Rate limit: Waiting {wait_time:.1f}s before next request...")
                time.sleep(wait_time)
        
        # Try Vertex AI first
        print(f"🎨 Attempting to generate image via Vertex AI (global)...")
        try:
            # Update request timestamp
            self.last_vertex_request = datetime.now()
            
            response = self.vertex_client.models.generate_content(
                model=Config.MODEL_IMAGE,
                contents=[prompt],
                config=types.GenerateContentConfig(temperature=1.0)
            )
            
            # Extract image from response
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        print("✅ Image generated via Vertex AI")
                        return {
                            "success": True,
                            "source": "vertex_ai",
                            "data": part.inline_data.data,
                            "mime_type": part.inline_data.mime_type,
                            "error": None
                        }
            
            # No image in response
            raise Exception("No image in Vertex AI response")
        
        except Exception as vertex_error:
            error_msg = str(vertex_error)
            print(f"❌ Vertex AI failed: {error_msg}")
            
            # Check if it's a quota error (429)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print("⚡ Quota exhausted - switching to AI Studio fallback...")
                
                if not self.ai_studio_client:
                    return {
                        "success": False,
                        "source": "none",
                        "data": None,
                        "mime_type": None,
                        "error": "Vertex AI quota exhausted and AI Studio fallback not configured"
                    }
                
                # Fallback to AI Studio
                try:
                    # Check AI Studio rate limit
                    if self.last_ai_studio_request:
                        time_since_last = (datetime.now() - self.last_ai_studio_request).total_seconds()
                        if time_since_last < self.rate_limit_seconds:
                            wait_time = self.rate_limit_seconds - time_since_last
                            print(f"⏳ AI Studio rate limit: Waiting {wait_time:.1f}s...")
                            time.sleep(wait_time)
                    
                    print("🔄 Generating via Google AI Studio...")
                    
                    # Update AI Studio timestamp
                    self.last_ai_studio_request = datetime.now()
                    
                    response = self.ai_studio_client.models.generate_content(
                        model=Config.MODEL_IMAGE,
                        contents=[prompt],
                        config=types.GenerateContentConfig(temperature=1.0)
                    )
                    
                    if response.candidates:
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                print("✅ Image generated via AI Studio (fallback)")
                                return {
                                    "success": True,
                                    "source": "ai_studio",
                                    "data": part.inline_data.data,
                                    "mime_type": part.inline_data.mime_type,
                                    "error": None
                                }
                    
                    raise Exception("No image in AI Studio response")
                
                except Exception as ai_studio_error:
                    print(f"❌ AI Studio also failed: {ai_studio_error}")
                    return {
                        "success": False,
                        "source": "none",
                        "data": None,
                        "mime_type": None,
                        "error": f"Both Vertex AI and AI Studio failed. Vertex: {vertex_error}, AI Studio: {ai_studio_error}"
                    }
            else:
                # Not a quota error, return the Vertex AI error
                return {
                    "success": False,
                    "source": "vertex_ai",
                    "data": None,
                    "mime_type": None,
                    "error": error_msg
                }


def main():
    """Test the dual-mode generator"""
    print("="*80)
    print("DUAL-MODE IMAGE GENERATOR TEST")
    print("="*80)
    
    # Initialize with API key
    api_key = "AIzaSyBRSb1uD8hWirVzSRSpQA_zPXffbCGR_7c"
    generator = DualModeImageGenerator(ai_studio_key=api_key)
    
    # Test prompt
    prompt = "A professional photography studio with dramatic cinematic lighting"
    
    print(f"\n📝 Prompt: {prompt}\n")
    
    # Generate
    result = generator.generate_image(prompt)
    
    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    print(f"Success: {result['success']}")
    print(f"Source: {result['source']}")
    print(f"Error: {result['error']}")
    
    if result['success']:
        # Save the image
        os.makedirs("test_output", exist_ok=True)
        ext = "png" if "png" in result['mime_type'] else "jpg"
        filename = f"test_output/dual_mode_test.{ext}"
        
        with open(filename, "wb") as f:
            f.write(result['data'])
        
        print(f"✅ Image saved to: {filename}")
        print(f"Size: {len(result['data'])} bytes")
    else:
        print(f"❌ Generation failed")


if __name__ == "__main__":
    main()
