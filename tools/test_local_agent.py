
import os
import sys
import logging
logging.basicConfig(level=logging.INFO)
from visions.core.agent import VisionsAgent
from visions.core.config import Config

def test_simple():
    # Force use of API Key if vertex initialization fails or for local test
    # But here we want to test the Vertex AI logic as close as possible to the Reasoning Engine
    agent = VisionsAgent()
    
    prompt = "Generate a cinematic portrait of a cyberpunk explorer in the desert"
    print(f"Testing prompt: {prompt}")
    
    try:
        response = agent.query(prompt)
        print(f"\n--- Response (len={len(response)}) ---")
        if "IMAGE_GENERATED:" in response:
            idx = response.index("IMAGE_GENERATED:")
            text_part = response[:idx]
            b64_part = response[idx+len("IMAGE_GENERATED:"):]
            print(f"TEXT:\n{text_part[:1500]}")
            print(f"\n✅ IMAGE DATA PRESENT: {len(b64_part)} chars of base64")
        else:
            print(response[:2000])
        print("--- END ---")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple()
