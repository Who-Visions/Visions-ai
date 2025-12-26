"""
Gemini-native Structured Output Wrapper
Inspired by OpenAI/LangChain but built for Google Gemini
"""
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import TypeVar, Type, Optional
import json
from visions.core.config import Config

from schemas import (
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageAnalysis,
    EnhancedPrompt,
    SystemStatus,
    PromptPattern
)

T = TypeVar('T', bound=BaseModel)


class StructuredGeminiClient:
    """
    Wrapper for Gemini that enforces structured outputs using Pydantic
    Combines Google's response_mime_type with Pydantic validation
    """
    
    def __init__(self, api_key: str = None, use_vertex: bool = False, 
                 project_id: str = None, location: str = "global"):
        """
        Initialize with either API key (AI Studio) or Vertex AI
        """
        if use_vertex:
            import vertexai
            vertexai.init(project=project_id, location="us-central1")
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.mode = "vertex"
        else:
            self.client = genai.Client(api_key=api_key)
            self.mode = "ai_studio"
    
    def generate_structured(
        self,
        model: str,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.7,
        **kwargs
    ) -> T:
        """
        Generate content with structured JSON output
        
        Args:
            model: Model name (e.g., "gemini-3-flash-preview")
            prompt: User prompt
            response_model: Pydantic model class for response
            temperature: Model temperature
            **kwargs: Additional config options
        
        Returns:
            Validated Pydantic model instance
        """
        # Get JSON schema from Pydantic model
        json_schema = response_model.model_json_schema()
        
        # Generate with structured output
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=json_schema,
                temperature=temperature,
                **kwargs
            )
        )
        
        # Validate and return
        return response_model.model_validate_json(response.text)
    
    async def generate_structured_async(
        self,
        model: str,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.7,
        **kwargs
    ) -> T:
        """Async version of generate_structured"""
        # Note: This is a placeholder - full async requires aiohttp
        # For now, we'll use the sync version
        return self.generate_structured(model, prompt, response_model, temperature, **kwargs)


# ============================================================================
# Practical Use Cases
# ============================================================================

class VisionStructuredAPI:
    """
    High-level API for Visions-specific structured operations
    """
    
    def __init__(self, api_key: str):
        self.client = StructuredGeminiClient(api_key=api_key)
        self.model = Config.MODEL_FLASH  # Fast model for structured tasks
    
    def enhance_prompt(self, user_prompt: str) -> EnhancedPrompt:
        """
        Take a basic prompt and enhance it with photography expertise
        
        Example:
            enhance_prompt("photo of nyc")
            -> Detailed professional photography prompt
        """
        system_prompt = f"""
You are an expert photography AI. Enhance the following user prompt into a professional photography prompt.

User's basic idea: {user_prompt}

Provide:
1. An enhanced, detailed prompt
2. Recommended aspect ratio
3. Style elements to emphasize
4. Technical photography notes
5. Reasoning for your enhancements
"""
        
        return self.client.generate_structured(
            model=self.model,
            prompt=system_prompt,
            response_model=EnhancedPrompt
        )
    
    def analyze_image_exif(self, analysis_text: str) -> ImageAnalysis:
        """
        Parse unstructured image analysis into structured format
        """
        prompt = f"""
Analyze this photography critique and extract structured information:

{analysis_text}

Provide a complete structured analysis including:
- Summary, subject, composition
- Lighting analysis
- Style classification
- Quality ratings (1-10)
- Camera settings if mentioned
- Improvement suggestions
"""
        
        return self.client.generate_structured(
            model=self.model,
            prompt=prompt,
            response_model=ImageAnalysis
        )
    
    def classify_prompt_pattern(self, prompt: str, usage_count: int, 
                                success_count: int) -> PromptPattern:
        """
        Classify and learn from successful prompt patterns
        """
        success_rate = (success_count / usage_count * 100) if usage_count > 0 else 0
        
        system_prompt = f"""
Analyze this image generation prompt and identify its pattern:

Prompt: {prompt}
Usage count: {usage_count}
Success rate: {success_rate:.1f}%

Classify this prompt into a category, extract common keywords, and provide recommendations
for similar prompts. Generate a unique pattern ID based on the category and keywords.
"""
        
        return self.client.generate_structured(
            model=self.model,
            prompt=system_prompt,
            response_model=PromptPattern
        )


# ============================================================================
# Example Usage & Testing
# ============================================================================

def demo_structured_outputs(api_key: str):
    """Demonstrate structured output capabilities"""
    visions = VisionStructuredAPI(api_key=api_key)
    
    print("="*80)
    print("🎯 GEMINI STRUCTURED OUTPUT DEMO")
    print("="*80)
    
    # 1. Prompt Enhancement
    print("\n📝 Testing Prompt Enhancement...")
    try:
        result = visions.enhance_prompt("photo of empire state building")
        print(f"\n✅ Enhanced Prompt:")
        print(f"   Original: {result.original_prompt}")
        print(f"   Enhanced: {result.enhanced_prompt}")
        print(f"   Aspect Ratio: {result.suggested_aspect_ratio}")
        print(f"   Style: {', '.join(result.style_elements)}")
        print(f"   Reasoning: {result.reasoning}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80)
    print("✅ Structured output demo complete!")
    print("="*80)


if __name__ == "__main__":
    # Test with hardcoded key for demo
    # In production, load from config
    API_KEY = "AIzaSyBRSb1uD8hWirVzSRSpQA_zPXffbCGR_7c"
    
    print("\n🚀 Initializing Gemini Structured Output System...\n")
    
    # Run demo
    demo_structured_outputs(API_KEY)
    
    print("\n💡 Key Benefits:")
    print("   - Type-safe outputs (Pydantic validation)")
    print("   - Guaranteed JSON structure")
    print("   - Easy integration with databases")
    print("   - Better error handling")
    print("   - Prompt pattern learning")
