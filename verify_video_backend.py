import os
import requests
from visions_assistant.agent import get_chat_response

def test_video_analysis():
    print("🧪 Starting Video Backend Verification...")
    
    # 1. Download a small sample video (Big Buck Bunny)
    video_url = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4" # Small sample
    local_path = "temp_verification_video.mp4"
    
    if not os.path.exists(local_path):
        print(f"⬇️ Downloading sample video from {video_url}...")
        try:
            r = requests.get(video_url, stream=True)
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("✅ Download complete.")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return

    # 2. Call the agent
    print("🤖 Calling get_chat_response with video...")
    try:
        # Requesting thinking_level high just to test config passing too
        response = get_chat_response(
            user_message="Describe what happens in this video in detail.",
            video_path=local_path,
            config={"thinking_level": "high"}
        )
        
        print("\n✨ Response Received:\n")
        print(response)
        
        if "**Gemini 3 Video Analysis**" in response:
            print("\n✅ Verification SUCCESS: Gemini 3 Pro model used.")
        else:
            print("\n⚠️ Verification WARNING: Response format unexpected.")
            
    except Exception as e:
        print(f"\n❌ Backend Error: {e}")

if __name__ == "__main__":
    test_video_analysis()
