"""
Veo 3.1 Video Generation - Official Implementation
Based on official Google Gemini API documentation
"""
import time
from google import genai
from google.genai import types

print("="*80)
print("🎬 VEO 3.1 VIDEO GENERATION (OFFICIAL API)")
print("="*80)

# Configuration
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"

# Create client with Vertex AI
print("\n🔑 Creating Gemini API client...")
print(f"   Project: {PROJECT_ID}")
print(f"   Location: {LOCATION}")
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
print("✅ Client created\n")

# Video prompt with dialogue
prompt = """
A cinematic close-up shot of a professional photography studio.
A photographer examining a DSLR camera on a tripod says, 'This is the perfect setup.'
Dramatic lighting with warm tones from softbox lights. 
Professional studio environment with white backdrop visible.
The photographer smiles with satisfaction.
Audio: Soft ambient studio sounds, camera shutter clicking, photographer's voice.
"""

print(f"📝 Prompt:\n{prompt}")
print("\n🎬 Generating video with Veo 3.1...")
print("   Model: veo-3.1-generate-preview")
print("   Duration: 8 seconds")
print("   Resolution: 1080p")
print("   Audio: Enabled (dialogue + sound effects)\n")

try:
    # Start video generation
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            resolution="1080p",
            duration_seconds=8,
            person_generation="allow_adult",
        ),
    )
    
    print(f"⏱️  Operation started: {operation.name}")
    
    # Poll for completion
    iteration = 0
    while not operation.done:
        iteration += 1
        time.sleep(15)
        operation = client.operations.get(operation)
        
        # Safely get state from metadata
        if hasattr(operation, 'metadata') and operation.metadata is not None:
            state = operation.metadata.get('state', 'RUNNING')
        else:
            state = 'RUNNING'
        
        print(f"   [{iteration}] Waiting... ({state})")
    
    print("\n✅ Video generation complete!")
    
    # Download and save
    if operation.response:
        import os
        os.makedirs("test_output/videos", exist_ok=True)
        
        generated_video = operation.response.generated_videos[0]
        
        # Download the video
        client.files.download(file=generated_video.video)
        generated_video.video.save("test_output/videos/veo3_official.mp4")
        
        # Check file size
        file_size = os.path.getsize("test_output/videos/veo3_official.mp4")
        
        print(f"\n📹 Video saved:")
        print(f"   Path: test_output/videos/veo3_official.mp4")
        print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        print(f"\n🎉 Success! Veo 3.1 video generation working!")
        
    else:
        print("❌ No response data received")
        if hasattr(operation, 'error') and operation.error:
            print(f"Error: {operation.error}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Type: {type(e).__name__}")
    
    error_str = str(e).lower()
    
    if "404" in error_str or "not found" in error_str:
        print("\n💡 Model not available. Possible reasons:")
        print("   - Veo 3.1 Preview may not be available in your region")
        print("   - Model name: veo-3.1-generate-preview")
        print("   - Check: https://ai.google.dev/gemini-api/docs/models/veo")
    elif "403" in error_str or "permission" in error_str:
        print("\n💡 Permission denied:")
        print("   - Ensure you're authenticated: gcloud auth application-default login")
        print("   - Check project access to Veo 3.1")
    elif "429" in error_str or "quota" in error_str:
        print("\n💡 Quota exhausted:")
        print("   - Video generation has separate quotas")
        print("   - Check: https://console.cloud.google.com/iam-admin/quotas")
    elif "region" in error_str or "location" in error_str:
        print("\n💡 Regional restriction:")
        print("   - Veo 3.1 may not be available in all regions")
        print("   - EU/UK/CH/MENA have restrictions")
    
    print("\n📖 Full error details:")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("💡 Note: Veo 3.1 features:")
print("   - 8-second videos with native audio")
print("   - Dialogue, sound effects, ambient noise")
print("   - 720p or 1080p resolution")
print("   - Text-to-video, Image-to-video, Video extension")
print("="*80)
