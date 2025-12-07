import vertexai
from vertexai.preview import reasoning_engines
import base64
import os
import json
import time
import re

# Configuration
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"
# NEW DEPLOYMENT RESOURCE (Deploy #10 - Fixed Lazy Loading)
REASONING_ENGINE_RESOURCE = "projects/620633534056/locations/us-central1/reasoningEngines/6042524480117407744"

_remote_agent = None
_initialized = False

def _initialize_backend():
    global _remote_agent, _initialized
    if _initialized:
        return

    print("Initializing Vertex AI Backend...")
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print(f"Connecting to Reasoning Engine: {REASONING_ENGINE_RESOURCE}...")
        _remote_agent = reasoning_engines.ReasoningEngine(REASONING_ENGINE_RESOURCE)
    except Exception as e:
        print(f"Failed to connect to Reasoning Engine: {e}")
        _remote_agent = None
    _initialized = True

def get_chat_response(user_message: str, image_path: str = None):
    """
    Proxies the chat request to the Vertex AI Reasoning Engine.
    Supports optional image input.
    Handles JSON response and text-embedded images.
    """
    # Lazy init
    if not _initialized:
        _initialize_backend()

    image_base64 = None
    if image_path:
        if not os.path.exists(image_path):
            return f"Error: Image file not found at {image_path}"
        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return f"Error reading image: {e}"

    # Try Local Agent First (Development Mode)
    try:
        from agent import VisionsAgent
        print("⚡ Using Local VisionsAgent (Dev Mode)")
        local_agent = VisionsAgent()
        response_str = local_agent.query(question=user_message, image_base64=image_base64)
    except Exception as local_e:
        print(f"⚠️ Local Agent skipped: {local_e}. Falling back to Remote.")
        
        # Fallback to Remote Reasoning Engine
        if not _remote_agent:
             return f"System Error: Unable to connect to AI service. Local Error: {local_e}"
             
        try:
            # Call the 'query' method defined in the remote agent
            if image_base64:
                response_str = _remote_agent.query(question=user_message, image_base64=image_base64)
            else:
                response_str = _remote_agent.query(question=user_message)
        except Exception as remote_e:
             print(f"Error querying Reasoning Engine: {remote_e}")
             return "I'm sorry, I encountered an error while processing your request."

    try:
        text_output = response_str
        images = []

        # Try parsing as JSON
        try:
            data = json.loads(response_str)
            text_output = data.get("text", "")
            images = data.get("images", [])
        except json.JSONDecodeError:
            pass # Treat as raw string

        # Create output dir
        if not os.path.exists("generated_images"):
            os.makedirs("generated_images")

        # 1. Handle JSON-based images
        for i, img in enumerate(images):
            timestamp = int(time.time())
            ext = "png"
            if "jpeg" in img.get("mime_type", ""): ext = "jpg"
            filename = f"generated_images/img_{timestamp}_{i}.{ext}"
            try:
                img_bytes = base64.b64decode(img["data"])
                with open(filename, "wb") as f:
                    f.write(img_bytes)
                text_output += f"\n\n> [🖼️ **Image Generated:** `{filename}`]"
            except Exception as e:
                text_output += f"\n\n[Error saving JSON image: {e}]"

        # 2. Handle Text-Embedded images (Fallback/Tool Output leakage)
        # Look for the marker we set in the tool
        print(f"DEBUG RAW TEXT (Start): {text_output[:500]}") # DEBUG
        
        # Relaxed regex to capture whatever follows the marker
        match = re.search(r"IMAGE_GENERATED:(\S+)", text_output)
        if match:
            data_str = match.group(1)
            
            if data_str.startswith("http"):
                text_output += "\n\n[⚠️ **Warning:** The model hallucinated an image URL instead of generating an actual image file.]"
            else:
                try:
                    timestamp = int(time.time())
                    filename = f"generated_images/img_{timestamp}_tool.png"
                    
                    img_bytes = base64.b64decode(data_str)
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    
                    # Replace the huge string with a nice link
                    text_output = text_output.replace(match.group(0), f"\n> [🖼️ **Image Generated:** `{filename}`]")
                except Exception as e:
                    text_output += f"\n\n[❌ Error saving embedded image: {e}]"

        return text_output

    except Exception as e:
        print(f"Error querying Reasoning Engine: {e}")
        return "I'm sorry, I encountered an error while processing your request."
