import sys
import os
import json

# Add parent dir to path to find tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.youtube_tools import YouTubeTools
from config import Config

TEST_VIDEO_URL = "https://www.youtube.com/watch?v=zTcDwqopvKE"

def test_vertex_ingestion():
    print(f"🔬 VERIFICATION: Testing YouTubeTools (Vertex AI) on {TEST_VIDEO_URL}...")
    
    # 1. Instantiate
    try:
        print("⏳ Initializing YouTubeTools...")
        # Validate config first
        Config.validate()
        tools = YouTubeTools(project_id=Config.VERTEX_PROJECT_ID, location=Config.VERTEX_LOCATION)
        print("✅ Tools Instantiated.")
    except Exception as e:
        print(f"❌ Instantiation Failed: {e}")
        return

    # 2. Extract Workflow (Gemini 3.0)
    print("⏳ requesting extract_workflow (Gemini 3.0)...")
    try:
        # Using a simpler prompt or standard call to verify access
        result = tools.extract_workflow(TEST_VIDEO_URL)
        
        print("\n--- RAW RESULT START ---")
        print(result[:500] + "... [truncated]")
        print("--- RAW RESULT END --- \n")
        
        if "error" in result.lower() and "{" in result:
             print("⚠️  Result contains error message.")
        else:
             print("✅ Valid Data Received from Vertex AI.")
             
        # Check if valid JSON
        try:
            data = json.loads(result)
            print(f"✅ JSON Parse Success. Keys: {list(data.keys())}")
        except:
            print("⚠️  Response was not valid JSON (might be raw text).")

    except Exception as e:
        print(f"❌ Extraction Failed: {e}")
        return

if __name__ == "__main__":
    test_vertex_ingestion()
