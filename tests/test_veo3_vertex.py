"""
Veo 3.1 Video Generation - Vertex AI Compatible
Fixed: Downloads video bytes directly (no client.files.download)
"""
import time
from google import genai
from google.genai import types

print("="*80)
print("🎬 VEO 3.1 - VERTEX AI COMPATIBLE")
print("="*80)

# Configuration
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"

print("\n🔑 Creating client...")
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
print("✅ Ready\n")

# Simple prompt
prompt = """
Close-up: A photographer says 'Perfect shot!' while examining a camera.
Professional studio, warm lighting.
"""

print(f"📝 Prompt: {prompt.strip()}\n")
print("🎬 Generating 4-second video (720p)...\n")

try:
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            resolution="720p",
            duration_seconds=4,
            person_generation="allow_adult",
        ),
    )
    
    print(f"⏱️  Started: ...{operation.name[-20:]}")
    
    # Poll
    iteration = 0
    while not operation.done:
        iteration += 1
        time.sleep(15)
        operation = client.operations.get(operation)
        print(f"   [{iteration}] Generating...")
    
    print("\n✅ Generation complete!\n")
    
    # Save video - different method for Vertex AI
    if operation.response:
        import os
        os.makedirs("test_output/videos", exist_ok=True)
        
        video = operation.response.generated_videos[0].video
        
        # Method 1: Try to get video bytes directly
        if hasattr(video, 'video_bytes') and video.video_bytes:
            print("💾 Saving video bytes...")
            with open("test_output/videos/veo3_vertex.mp4", "wb") as f:
                f.write(video.video_bytes)
            
            size = os.path.getsize("test_output/videos/veo3_vertex.mp4")
            print(f"✅ Saved: test_output/videos/veo3_vertex.mp4")
            print(f"📊 Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
            print("\n🎉 SUCCESS!")
        
        # Method 2: If URI is available (GCS path)
        elif hasattr(video, 'uri') and video.uri:
            print(f"📍 Video stored at: {video.uri}")
            print("💡 Download with: gsutil cp {video.uri} ./video.mp4")
            print("   Or use GCS console")
        
        # Method 3: Show what's available
        else:
            print("📋 Video object attributes:")
            for attr in dir(video):
                if not attr.startswith('_'):
                    try:
                        val = getattr(video, attr)
                        if not callable(val):
                            print(f"   {attr}: {str(val)[:100]}")
                    except:
                        pass
    
    else:
        print("❌ No response")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
