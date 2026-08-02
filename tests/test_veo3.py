"""
Veo 3.1 Video Generation Test
Based on official Google Colab example
"""
import time
from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "mineral-subject-487519-v6"
LOCATION = "us-central1"

print("="*80)
print("🎬 VEO 3.1 VIDEO GENERATION TEST")
print("="*80)

# Create client
print(f"\n🔗 Connecting to Vertex AI...")
print(f"   Project: {PROJECT_ID}")
print(f"   Location: {LOCATION}")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Load model
video_model = "veo-3.1-generate-001"  # High quality
# video_model_fast = "veo-3.1-fast-generate-001"  # Faster, lower latency

print(f"✅ Client created")
print(f"📹 Model: {video_model}\n")

# Video prompt
prompt = """
A professional photography studio tour. 
Smooth camera pan from left to right revealing:
- A modern DSLR camera on a professional tripod
- Dramatic softbox lighting setup with warm tones
- Clean white photography backdrop
- Professional studio environment
Cinematic lighting, high quality, 4K look.
"""

print(f"📝 Prompt:\n{prompt}")

# Generate video
print("\n🎬 Generating video...")
print("   This typically takes 2-3 minutes...")
print("   Duration: 6 seconds")
print("   Resolution: 1080p")
print("   Aspect Ratio: 16:9")
print("   Audio: Enabled\n")

try:
    operation = client.models.generate_videos(
        model=video_model,
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            number_of_videos=1,
            duration_seconds=6,
            resolution="1080p",
            person_generation="allow_adult",
            enhance_prompt=True,
            generate_audio=True,
        ),
    )
    
    print(f"⏱️  Operation started: {operation.name}")
    
    # Poll for completion
    iteration = 0
    while not operation.done:
        iteration += 1
        time.sleep(15)
        operation = client.operations.get(operation)
        print(f"   [{iteration}] Status: {operation.metadata.get('state', 'RUNNING')}...")
    
    print("\n✅ Video generation complete!")
    
    # Save result
    if operation.response:
        import os
        os.makedirs("test_output/videos", exist_ok=True)
        
        video_data = operation.result.generated_videos[0].video.video_bytes
        output_path = "test_output/videos/veo3_test.mp4"
        
        with open(output_path, "wb") as f:
            f.write(video_data)
        
        file_size = os.path.getsize(output_path)
        print(f"\n📹 Video saved:")
        print(f"   Path: {output_path}")
        print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        print(f"\n🎉 Success! Video generation working!")
    else:
        print("❌ No response data received")
        if operation.error:
            print(f"Error: {operation.error}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    
    error_str = str(e).lower()
    
    if "404" in error_str or "not found" in error_str:
        print("\n💡 Model not found. Possible issues:")
        print("   - Veo 3.1 may not be available in us-central1")
        print("   - Try region: us-east4")
        print("   - Check if you have Veo preview access")
    elif "403" in error_str or "permission" in error_str:
        print("\n💡 Permission denied. Check:")
        print("   - Vertex AI Vision API is enabled")
        print("   - Your account has Veo access")
        print("   - Service account has correct permissions")
    elif "429" in error_str:
        print("\n💡 Quota exhausted")
        print("   - Video generation has separate quota from images")
        print("   - Request quota increase in GCP Console")
    elif "invalid" in error_str or "400" in error_str:
        print("\n💡 Invalid request:")
        print("   - Check model name is correct")
        print("   - Verify config parameters")

print("\n" + "="*80)
