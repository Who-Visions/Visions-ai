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
    
    # --- MODEL CONFIGURATION (Dec 2025 Standards) ---
    # STRICT RULE: Use Gemini 3 for EVERYTHING unless capability is explicitly missing.

    # 1. CORE AGENTIC BRAINS (Gemini 3) - GLOBAL ENDPOINT SUPPORTED
    # Used for: Reasoning, Planning, Coding, Text Chat, Search Grounding, Batch, Caching
    # Docs confirm: "Gemini 3 Flash/Pro (Preview)" support Global Endpoint.
    MODEL_PRO = "gemini-3-pro-preview"          
    MODEL_FLASH = "gemini-3-flash-preview"      
    
    MAX_OUTPUT_TOKENS_FLASH = 8192

    # 2. IMAGE GENERATION & EDITING (Gemini 3) - GLOBAL ENDPOINT SUPPORTED
    MODEL_IMAGE = "gemini-3-pro-image-preview"
    PRIMARY_IMAGE_MODEL = MODEL_IMAGE
    
    # Fallback Image Model (Imagen 4)
    MODEL_IMAGEN_FALLBACK = "imagen-4.0-generate-001"

    # Fast Image Generation (Gemini 2.5 Flash Image - "Nano Banana")
    MODEL_IMAGE_FAST = "gemini-2.5-flash-image"

    # Specialized Vision Tasks (Gemini 2.5 for Segmentation)
    # Gemini 3 is generalist; 2.5 is trained for generic segmentation.
    MODEL_IMAGE_SEGMENTATION = "gemini-2.5-flash"

    # Audio Understanding (Gemini 2.5 Flash)
    MODEL_AUDIO_UNDERSTANDING = "gemini-2.5-flash"
    MODEL_TRANSCRIPTION = "gemini-2.5-flash"

    # 3. VIDEO GENERATION (Veo 3.1)
    MODEL_VEO = "veo-3.1-generate-preview"
    MODEL_VEO_FAST = "veo-3.1-fast-generate-preview"

    # 4. MUSIC GENERATION (Lyria RealTime) - Experimental
    MODEL_LYRIA_REALTIME = "models/lyria-realtime-exp"
    LYRIA_SAMPLE_RATE = 48000
    LYRIA_CHANNELS = 2 # Stereo           

    # 3. LEGACY / CAPABILITY FALLBACKS (Gemini 2.5)
    # STRICTLY LIMITED: Only use these for features NOT present in Gemini 3.
    # NOTE: These may NOT support Global Endpoint and require specific regions.
    
    # Fallback A: Live API (Native Audio / Voice Mode)
    # Region: us-central1, us-east4, us-west1 (Standard for Live API)
    MODEL_LIVE_API = "gemini-live-2.5-flash-native-audio" 
    
    # Fallback B: Text-to-Speech (TTS)
    # Native controllable TTS (Single/Multi-speaker)
    MODEL_TTS = "gemini-2.5-flash-preview-tts"
    
    # Fallback C: Google Maps Grounding
    # Status: Gemini 3 does not support Maps Grounding.
    MODEL_MAPS = "gemini-2.5-flash"

    # Fallback D: Computer Use (Browser Automation)
    # Status: Specialized preview model required
    MODEL_COMPUTER_USE = "gemini-2.5-computer-use-preview-10-2025"
    
    # Deep Research Agent
    MODEL_DEEP_RESEARCH = "deep-research-pro-preview-12-2025"
    
    # ALIASES
    GROUNDING_MODEL = MODEL_FLASH  
    EMBEDDING_MODEL = "gemini-embedding-001" 
    
    # GENERATION CONFIG
    # Gemini 3 Thinking Levels
    # Note: Gemini 3 Pro supports only LOW and HIGH. Flash supports all.
    THINKING_LEVEL_MINIMAL = "MINIMAL"
    THINKING_LEVEL_LOW = "LOW"
    THINKING_LEVEL_MEDIUM = "MEDIUM"
    THINKING_LEVEL_HIGH = "HIGH" 
    
    DEFAULT_THINKING_LEVEL = THINKING_LEVEL_HIGH 
    
    # Gemini 3 Media Resolution
    MEDIA_RES_LOW = "low"
    MEDIA_RES_MEDIUM = "medium"
    MEDIA_RES_HIGH = "high"
    MEDIA_RES_ULTRA_HIGH = "ultra_high" 
    
    # Configured Media Resolution
    DEFAULT_MEDIA_RESOLUTION = os.getenv("DEFAULT_MEDIA_RESOLUTION", MEDIA_RES_MEDIUM)
    
    # Feature Flags
    ENABLE_AI_STUDIO_FALLBACK = True 
    ENABLE_GEMINI_3_FLASH_FREE = True 
    ENABLE_QUOTA_ALERTS = os.getenv("ENABLE_QUOTA_ALERTS", "false").lower() == "true"
    
    # Knowledge Base
    CHUNK_SIZE = 4000 
    CHUNK_OVERLAP = 500
    # Storage
    GCS_BUCKET = f"{VERTEX_PROJECT_ID}-reasoning-artifacts"
    GCS_MEMORY_BUCKET = f"{VERTEX_PROJECT_ID}-visions-memory"
    VECTOR_STORE_PREFIX = "vector_store"
    
    # Gemini Live API (Native Audio)
    # Docs: "Gemini 2.5 Flash with Gemini Live API native audio" -> gemini-live-2.5-flash-native-audio
    LIVE_AUDIO_MODEL = "gemini-live-2.5-flash-native-audio"
    LIVE_API_HOST = "us-central1-aiplatform.googleapis.com" # Regional Endpoint Required for Live
    LIVE_WS_PORT = int(os.getenv("VISIONS_LIVE_WS_PORT", "8080"))
    LIVE_HTTP_PORT = int(os.getenv("VISIONS_LIVE_HTTP_PORT", "8000"))
    LIVE_VOICE_NAME = os.getenv("VISIONS_VOICE", "Charon") 
    AUDIO_INPUT_SAMPLE_RATE = 16000   
    AUDIO_OUTPUT_SAMPLE_RATE = 24000  
    ENABLE_AFFECTIVE_DIALOG = True    
    ENABLE_PROACTIVE_AUDIO = False    
    
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
        print(f"Global Endpoint: {cls.VERTEX_GLOBAL_LOCATION} (For Gemini 3)")
        print(f"Reasoning Engine: {cls.REASONING_ENGINE_RESOURCE}")
        print(f"Primary Model: {cls.PRIMARY_IMAGE_MODEL}")
        print(f"AI Studio Fallback: {'✅ Enabled' if cls.ENABLE_AI_STUDIO_FALLBACK else '❌ Disabled'}")
        print(f"API Key Present: {'✅ Yes' if cls.GOOGLE_AI_STUDIO_API_KEY else '❌ No'}")
        print("="*80)


if __name__ == "__main__":
    # Test configuration
    Config.validate()
    Config.print_status()
