# Visions Assistant - Local Bridge v2.0.0
# Pure bridge to the Core Rhea Noir Engine

import os
import base64
import logging
from typing import Optional, Dict, Any

# Configure relative imports for the project structure
from visions.core.agent import VisionsAgent

logger = logging.getLogger("visions-bridge")

# Global singleton for the engine
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        try:
            logger.info("⚡ Initializing Rhea Noir Core Engine...")
            _engine = VisionsAgent()
        except Exception as e:
            logger.error(f"❌ Failed to initialize Core Engine: {e}")
            raise e
    return _engine

def get_chat_response(user_message: str, image_path: str = None, video_path: str = None, user_id: str = "default_user", config: dict = None):
    """
    Standardized entry for the Fleet Server.
    Maps file paths to base64 and proxies to the core engine.
    """
    engine = get_engine()
    
    # 1. Handle Visual Inputs
    image_base64 = None
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading image: {e}")

    # 2. Handle Video Inputs (Special Case)
    if video_path and os.path.exists(video_path):
        # Current engine handles video via VisionTools internally if prompted,
        # but for now we prioritize pure question/image flow.
        user_message += f"\n[Video analysis requested for: {video_path}]"

    # 3. Handle Image Generation Commands
    # If the message looks like a generation prompt, we use the imager
    gen_triggers = ["generate a", "create an image of", "draw a", "make a photo of"]
    if any(trigger in user_message.lower() for trigger in gen_triggers) and "image" in user_message.lower():
         logger.info("🎨 Image generation triggered via flow.")
         return engine.generate_image(user_message)

    # 4. Proxy Query
    try:
        return engine.query(
            question=user_message,
            image_base64=image_base64,
            user_id=user_id,
            config=config
        )
    except Exception as e:
        logger.error(f"Engine Query Failure: {e}")
        return f"I encountered an error while processing your request: {e}"
