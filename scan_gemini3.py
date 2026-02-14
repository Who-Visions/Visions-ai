
import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Gemini3-Scanner")

# Load Env
load_dotenv()

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "endless-duality-480201-t3")
GLOBAL_LOCATION = "global"

def test_gemini_3_discovery():
    """
    Specifically tests for Gemini 3 models using the global endpoint.
    """
    logger.info(f"🌍 Connecting to Global Endpoint: {GLOBAL_LOCATION} for Project: {PROJECT_ID}")
    
    try:
        # Initialize client for Global
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=GLOBAL_LOCATION)
        
        logger.info("🔎 Listing models...")
        
        # New SDK list method pattern
        found_gemini_3 = False
        gemini_3_models = []
        
        try:
            # Try list() as iterator first (newer SDKs)
            for m in client.models.list():
                if "gemini-3" in m.name:
                    found_gemini_3 = True
                    gemini_3_models.append(m.name)
                    logger.info(f"   ✨ Found Gemini 3 Model: {m.name}")
        except Exception as e:
            logger.warning(f"  ⚠️  Error during model listing: {e}")

        if not found_gemini_3:
            logger.warning("  ⚠️  No Gemini 3 models explicitly found in list. Attempting direct generation check...")
            # Even if list fails or is empty/filtered, try to use it directly
            gemini_3_models = ["gemini-3-pro-preview", "gemini-3-flash-preview"]

        # Test Generation with Thinking Config
        logger.info("\n🧠 Testing Gemini 3 Thinking Capabilities...")
        
        model_id = "gemini-3-flash-preview"
        logger.info(f"   👉 Targeting: {model_id}")
        
        try:
            response = client.models.generate_content(
                model=model_id,
                contents="Explain the concept of 'Vibe Coding' in 1 sentence.",
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low")
                ),
            )
            logger.info(f"   ✅ Response Received:\n{response.text}")
            logger.info("   ✅ Thinking Level 'low' configuration accepted.")
            
        except Exception as e:
            logger.error(f"   ❌ Generation Failed or Model Not Available: {e}")
            
    except Exception as e:
        logger.critical(f"❌ Client Initialization Failed: {e}")

if __name__ == "__main__":
    test_gemini_3_discovery()
