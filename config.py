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
    REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "542433066447011840")
    REASONING_ENGINE_RESOURCE = (
        f"projects/620633534056/locations/{VERTEX_LOCATION}/"
        f"reasoningEngines/{REASONING_ENGINE_ID}"
    )
    
    # Model Configuration
    # RESTRICTION: Gemini 3 Global Models Only (User Mandate)
    PRIMARY_IMAGE_MODEL = "gemini-3-pro-preview" 
    FALLBACK_IMAGE_MODEL = "gemini-3-flash-preview"
    
    # Gemini 3 Thinking Levels (replaces deprecated thinking_budget)
    # low: Minimizes latency, good for simple queries
    # high: Deep reasoning, longer time-to-first-token
    # minimal: Flash-only, almost no thinking
    # medium: Flash-only, balanced thinking
    THINKING_LEVEL_SIMPLE = "low"
    THINKING_LEVEL_COMPLEX = "high"
    
    # Embedding Model (Gemini Embedding 001 - stable, high rate limits)
    EMBEDDING_MODEL = "gemini-embedding-001"
    EMBEDDING_DIMENSIONS = 768  # Can be 768, 1536, or 3072
    
    # Feature Flags
    ENABLE_AI_STUDIO_FALLBACK = True  # Enabled (Key updated)
    ENABLE_GEMINI_3_FLASH_FREE = True  # Gemini 3 Flash has free tier!
    ENABLE_QUOTA_ALERTS = os.getenv("ENABLE_QUOTA_ALERTS", "false").lower() == "true"
    
    # Knowledge Base
    CHUNK_SIZE = 4000  # Characters for RecursiveCharacterTextSplitter (Gemini has large context window)
    CHUNK_OVERLAP = 500
    # Storage
    GCS_BUCKET = f"{VERTEX_PROJECT_ID}-reasoning-artifacts"
    GCS_MEMORY_BUCKET = f"{VERTEX_PROJECT_ID}-visions-memory"
    VECTOR_STORE_PREFIX = "vector_store"
    
    # Gemini Live API (Native Audio)
    LIVE_AUDIO_MODEL = "gemini-live-2.5-flash-native-audio"
    LIVE_API_HOST = "us-central1-aiplatform.googleapis.com"
    LIVE_WS_PORT = int(os.getenv("VISIONS_LIVE_WS_PORT", "8080"))
    LIVE_HTTP_PORT = int(os.getenv("VISIONS_LIVE_HTTP_PORT", "8000"))
    LIVE_VOICE_NAME = os.getenv("VISIONS_VOICE", "Charon")  # Deep, authoritative
    AUDIO_INPUT_SAMPLE_RATE = 16000   # 16kHz PCM input (required)
    AUDIO_OUTPUT_SAMPLE_RATE = 24000  # 24kHz PCM output
    ENABLE_AFFECTIVE_DIALOG = True    # Emotional intelligence
    ENABLE_PROACTIVE_AUDIO = False    # Respond only when spoken to
    
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
