"""
Environment Configuration for Visions AI
Load this with: from dotenv import load_dotenv; load_dotenv()
"""
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

class Config:
    """Visions AI Configuration"""
    
    # Google AI Studio (Fallback/Development)
    # IMPORTANT: Set this via environment variable, never hardcode!
    GOOGLE_AI_STUDIO_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
    
    # Vertex AI (Production)
    VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "endless-duality-480201-t3")
    VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
    VERTEX_GLOBAL_LOCATION = os.getenv("VERTEX_GLOBAL_LOCATION", "global")
    
    # Reasoning Engine
    REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "2538519480860395520")
    REASONING_ENGINE_RESOURCE = (
        f"projects/620633534056/locations/{VERTEX_LOCATION}/"
        f"reasoningEngines/{REASONING_ENGINE_ID}"
    )
    
    # Model Configuration
    PRIMARY_IMAGE_MODEL = "gemini-3-pro-image-preview"  # Global endpoint with dynamic routing
    FALLBACK_IMAGE_MODEL = "gemini-2.5-flash-image"  # Flash fallback for resilience
    
    # Feature Flags
    ENABLE_AI_STUDIO_FALLBACK = os.getenv("ENABLE_AI_STUDIO_FALLBACK", "true").lower() == "true"
    ENABLE_QUOTA_ALERTS = os.getenv("ENABLE_QUOTA_ALERTS", "false").lower() == "true"
    
    # Storage
    GCS_BUCKET = f"{VERTEX_PROJECT_ID}-reasoning-artifacts"
    VECTOR_STORE_PREFIX = "vector_store"
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        errors = []
        
        if not cls.VERTEX_PROJECT_ID:
            errors.append("VERTEX_PROJECT_ID is required")
        
        if cls.ENABLE_AI_STUDIO_FALLBACK and not cls.GOOGLE_AI_STUDIO_API_KEY:
            errors.append("GOOGLE_AI_STUDIO_API_KEY is required when AI Studio fallback is enabled")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def print_status(cls):
        """Print current configuration status"""
        print("="*80)
        print("VISIONS AI CONFIGURATION")
        print("="*80)
        print(f"Vertex Project: {cls.VERTEX_PROJECT_ID}")
        print(f"Vertex Location: {cls.VERTEX_LOCATION}")
        print(f"Global Endpoint: {cls.VERTEX_GLOBAL_LOCATION}")
        print(f"Reasoning Engine: {cls.REASONING_ENGINE_RESOURCE}")
        print(f"Primary Model: {cls.PRIMARY_IMAGE_MODEL}")
        print(f"AI Studio Fallback: {'✅ Enabled' if cls.ENABLE_AI_STUDIO_FALLBACK else '❌ Disabled'}")
        print(f"API Key Present: {'✅ Yes' if cls.GOOGLE_AI_STUDIO_API_KEY else '❌ No'}")
        print("="*80)


if __name__ == "__main__":
    # Test configuration
    Config.validate()
    Config.print_status()
