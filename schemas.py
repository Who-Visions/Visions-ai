"""
Structured Output Models for Visions AI
Using Pydantic for type-safe, validated responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

# ============================================================================
# Image Generation Schemas
# ============================================================================

class AspectRatio(str, Enum):
    """Supported aspect ratios"""
    SQUARE = "1:1"
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"
    TRADITIONAL_4_3 = "4:3"
    PORTRAIT_3_4 = "3:4"
    ULTRAWIDE_21_9 = "21:9"

class ImageGenerationRequest(BaseModel):
    """Structured request for image generation"""
    prompt: str = Field(description="Detailed image generation prompt")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.SQUARE, description="Desired aspect ratio")
    style: Optional[str] = Field(default=None, description="Optional style hint (e.g., 'cinematic', 'professional', 'artistic')")
    subject: Optional[str] = Field(default=None, description="Main subject of the image")
    lighting: Optional[str] = Field(default=None, description="Lighting description (e.g., 'dramatic', 'natural', 'soft')")

class ImageGenerationResult(BaseModel):
    """Structured result from image generation"""
    success: bool = Field(description="Whether generation succeeded")
    filepath: Optional[str] = Field(default=None, description="Path to generated image")
    source: Literal["vertex_ai", "ai_studio", "error"] = Field(description="Which service generated the image")
    model: str = Field(description="Model used for generation")
    generation_time_seconds: Optional[float] = Field(default=None, description="Time taken to generate")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

# ============================================================================
# Photography Analysis Schemas
# ============================================================================

class CameraSettings(BaseModel):
    """Camera settings extracted from image analysis"""
    aperture: Optional[str] = Field(default=None, description="Aperture f-stop (e.g., 'f/2.8')")
    shutter_speed: Optional[str] = Field(default=None, description="Shutter speed (e.g., '1/250')")
    iso: Optional[int] = Field(default=None, description="ISO sensitivity")
    focal_length: Optional[str] = Field(default=None, description="Focal length (e.g., '50mm')")
    camera_model: Optional[str] = Field(default=None, description="Camera model name")
    lens_model: Optional[str] = Field(default=None, description="Lens model name")

class ImageAnalysis(BaseModel):
    """Structured image analysis result"""
    summary: str = Field(description="Brief summary of the image")
    subject: str = Field(description="Main subject of the photograph")
    composition: str = Field(description="Description of composition and framing")
    lighting: str = Field(description="Analysis of lighting conditions")
    style: str = Field(description="Photographic style category")
    technical_quality: int = Field(ge=1, le=10, description="Technical quality rating (1-10)")
    artistic_quality: int = Field(ge=1, le=10, description="Artistic quality rating (1-10)")
    camera_settings: Optional[CameraSettings] = Field(default=None, description="Extracted camera settings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")

# ============================================================================
# Conversation & Memory Schemas
# ============================================================================

class ConversationTurn(BaseModel):
    """Single turn in a conversation"""
    user_message: str
    assistant_response: str
    timestamp: str
    session_id: Optional[str] = None
    contains_image: bool = False
    generated_image: bool = False

class MemoryEntry(BaseModel):
    """Structured memory entry"""
    timestamp: str
    type: Literal["conversation", "image_generation", "image_analysis", "preference", "feedback"]
    content: str
    metadata: dict = Field(default_factory=dict)

class MemoryStats(BaseModel):
    """Memory system statistics"""
    session_id: str
    short_term_entries: int
    long_term_conversations: int
    long_term_images: int
    session_start_time: str
    success_rate_percent: float = Field(ge=0, le=100)

# ============================================================================
# Photography Prompt Enhancement Schema
# ============================================================================

class EnhancedPrompt(BaseModel):
    """AI-enhanced photography prompt"""
    original_prompt: str = Field(description="User's original prompt")
    enhanced_prompt: str = Field(description="Professionally enhanced prompt")
    suggested_aspect_ratio: AspectRatio = Field(description="Recommended aspect ratio")
    style_elements: List[str] = Field(description="Key style elements to emphasize")
    technical_notes: List[str] = Field(description="Technical guidance for composition")
    reasoning: str = Field(description="Explanation of enhancements")

# ============================================================================
# Prompt Pattern Learning Schema
# ============================================================================

class PromptPattern(BaseModel):
    """Learned pattern from successful prompts"""
    pattern_id: str
    category: str = Field(description="Category (e.g., 'portrait', 'landscape', 'product')")
    common_keywords: List[str] = Field(description="Frequently used keywords")
    average_success_rate: float = Field(ge=0, le=100, description="Success rate percentage")
    usage_count: int = Field(description="Number of times pattern appears")
    example_prompt: str = Field(description="Example of successful prompt")
    recommendations: List[str] = Field(description="Recommendations for using this pattern")

# ============================================================================
# System Status Schema
# ============================================================================

class SystemStatus(BaseModel):
    """Current system status"""
    vertex_ai_available: bool = Field(description="Vertex AI endpoint accessible")
    vertex_ai_quota_status: Literal["available", "limited", "exhausted"] = Field(description="Quota status")
    ai_studio_available: bool = Field(description="AI Studio API accessible")
    ai_studio_quota_remaining: Optional[int] = Field(default=None, description="Remaining requests")
    memory_system_online: bool = Field(description="Memory system operational")
    active_model: str = Field(description="Currently active model")
    active_endpoint: Literal["vertex_ai_global", "vertex_ai_regional", "ai_studio"] = Field(description="Active endpoint")
    session_id: str
    uptime_seconds: float


# ============================================================================
# Example Usage Functions
# ============================================================================

def create_image_request(prompt: str, aspect_ratio: str = "1:1") -> ImageGenerationRequest:
    """Helper to create structured image generation request"""
    return ImageGenerationRequest(
        prompt=prompt,
        aspect_ratio=AspectRatio(aspect_ratio)
    )

def create_generation_result(success: bool, filepath: str = None, 
                            source: str = "ai_studio", model: str = "gemini-3-pro-image-preview",
                            generation_time: float = None, error: str = None) -> ImageGenerationResult:
    """Helper to create structured generation result"""
    return ImageGenerationResult(
        success=success,
        filepath=filepath,
        source=source,
        model=model,
        generation_time_seconds=generation_time,
        error_message=error
    )


if __name__ == "__main__":
    # Test the schemas
    print("="*80)
    print("TESTING STRUCTURED OUTPUT SCHEMAS")
    print("="*80)
    
    # Test image generation request
    request = create_image_request(
        "A professional photograph of a vintage camera on a wooden desk",
        "16:9"
    )
    print("\n📸 Image Generation Request:")
    print(request.model_dump_json(indent=2))
    
    # Test generation result
    result = create_generation_result(
        success=True,
        filepath="test_output/vintage_camera.jpg",
        source="ai_studio",
        generation_time=3.5
    )
    print("\n✅ Generation Result:")
    print(result.model_dump_json(indent=2))
    
    # Test enhanced prompt
    enhanced = EnhancedPrompt(
        original_prompt="photo of nyc",
        enhanced_prompt="A professional, cinematic photograph of New York City skyline at golden hour, featuring dramatic lighting with warm sunset tones, shot from an elevated perspective",
        suggested_aspect_ratio=AspectRatio.LANDSCAPE_16_9,
        style_elements=["cinematic", "golden hour", "elevated perspective"],
        technical_notes=["Use wide-angle lens", "Focus on architectural details", "Balance exposure for highlights"],
        reasoning="Enhanced with specific time of day, perspective, and technical guidance for better results"
    )
    print("\n🎨 Enhanced Prompt:")
    print(enhanced.model_dump_json(indent=2))
    
    # Test system status
    status = SystemStatus(
        vertex_ai_available=True,
        vertex_ai_quota_status="exhausted",
        ai_studio_available=True,
        ai_studio_quota_remaining=245,
        memory_system_online=True,
        active_model="gemini-3-pro-image-preview",
        active_endpoint="ai_studio",
        session_id="2025-12-05T04:20:00",
        uptime_seconds=1234.5
    )
    print("\n📊 System Status:")
    print(status.model_dump_json(indent=2))
    
    print("\n✅ All schemas working correctly!")
