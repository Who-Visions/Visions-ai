
import os
import sys
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SDKScanner")

# Load Env
load_dotenv()

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "endless-duality-480201-t3")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
GLOBAL_LOCATION = "global"

def scan_sdk_capabilities():
    """Scans the Google GenAI SDK for Gemini 3 capabilities."""
    logger.info(f"🛰️  Scanning SDK Capabilities for Project: {PROJECT_ID}")
    
    # 1. Inspect Thinking Types
    logger.info("🧠 Checking Thinking Configuration Support...")
    try:
        if hasattr(types, 'ThinkingConfig'):
            logger.info("✅ types.ThinkingConfig is available.")
            # Check fields
            # We can't easily inspect Pydantic models in all versions, but existence is key.
        else:
            logger.warning("⚠️  types.ThinkingConfig NOT found. SDK might be too old?")
            
        # Check ThinkingLevel Enum if possible
        if hasattr(types, 'ThinkingLevel'):
             logger.info(f"✅ types.ThinkingLevel is available: {dir(types.ThinkingLevel)}")
        else:
             logger.info("ℹ️  types.ThinkingLevel enum might be implicit (strings allowed).")
             
    except Exception as e:
        logger.error(f"❌ Type inspection failed: {e}")

    # 2. Check Global Endpoint for Gemini 3
    logger.info(f"🌍 Checking Global Endpoint ({GLOBAL_LOCATION})...")
    try:
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=GLOBAL_LOCATION)
        
        # Try finding the right list method
        if hasattr(client.models, 'list'):
            models_iter = client.models.list()
        elif hasattr(client.models, 'list_models'):
             models_iter = client.models.list_models()
        else:
            logger.error(f"❌ Could not find list method on client.models. Available: {dir(client.models)}")
            return False

        models = list(models_iter)
        
        gemini_3 = [m for m in models if "gemini-3" in m.name]
        
        if gemini_3:
            logger.info(f"✅ Found {len(gemini_3)} Gemini 3 models in GLOBAL location:")
            for m in gemini_3:
                print(f"   • {m.name} ({m.display_name})")
        else:
            logger.warning("⚠️  No Gemini 3 models found in GLOBAL location.")
            
    except Exception as e:
        logger.error(f"❌ Global Endpoint Check Failed: {e}")

    # 3. Check Regional Endpoint
    logger.info(f"VX Checking Regional Endpoint ({LOCATION})...")
    try:
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        # Just quick check
        models_regional = list(client.models.list_models())
        logger.info(f"✅ Regional endpoint accessible. Found {len(models_regional)} models.")
    except Exception as e:
        logger.error(f"❌ Regional Endpoint Check Failed: {e}")

    return True

if __name__ == "__main__":
    scan_sdk_capabilities()
