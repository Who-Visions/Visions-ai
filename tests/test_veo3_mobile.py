"""
Veo 3.1 Video Generation - Network-Resilient Version
With retry logic for mobile hotspot connections
"""
import time
from google import genai
from google.genai import types

print("="*80)
print("🎬 VEO 3.1 VIDEO GENERATION (NETWORK-RESILIENT)")
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

# Shorter, simpler prompt for faster generation
prompt = """
A close-up shot of a photographer examining a DSLR camera.
The photographer says: 'Perfect shot!'
Professional studio with soft lighting.
"""

print(f"📝 Prompt: {prompt.strip()}\n")
print("🎬 Generating video...")
print("   Duration: 4 seconds (faster)")
print("   Resolution: 720p (smaller file)\n")

try:
    # Start video generation with smaller settings for mobile hotspot
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            resolution="720p",  # Smaller file for mobile hotspot
            duration_seconds=4,  # Shorter for faster generation
            person_generation="allow_adult",
        ),
    )
    
    print(f"⏱️  Operation: {operation.name}")
    
    # Poll for completion
    iteration = 0
    while not operation.done:
        iteration += 1
        time.sleep(15)
        try:
            operation = client.operations.get(operation)
            print(f"   [{iteration}] Generating...")
        except Exception as e:
            print(f"   [{iteration}] Network hiccup, retrying...")
            time.sleep(5)
            continue
    
    print("\n✅ Video generation complete!")
    
    # Download with retry logic
    if operation.response:
        import os
        os.makedirs("test_output/videos", exist_ok=True)
        
        generated_video = operation.response.generated_videos[0]
        
        print("\n📥 Downloading video (this may take a moment on mobile hotspot)...")
        
        # Retry download up to 3 times
        download_success = False
        for attempt in range(3):
            try:
                print(f"   Attempt {attempt + 1}/3...")
                client.files.download(file=generated_video.video)
                generated_video.video.save("test_output/videos/veo3_mobile.mp4")
                download_success = True
                break
            except Exception as e:
                print(f"   ⚠️ Download failed: {str(e)[:100]}")
                if attempt < 2:
                    print(f"   🔄 Retrying in 10 seconds...")
                    time.sleep(10)
        
        if download_success:
            file_size = os.path.getsize("test_output/videos/veo3_mobile.mp4")
            print(f"\n📹 Video saved successfully!")
            print(f"   Path: test_output/videos/veo3_mobile.mp4")
            print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            print(f"\n🎉 Success! Veo 3.1 working on mobile hotspot!")
        else:
            print("\n⚠️ Download failed after 3 attempts")
            print("💡 Video was generated but couldn't download due to network")
            print(f"   Operation name: {operation.name}")
            print("   You can retrieve it later with better connection")
    else:
        print("❌ No response data received")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Type: {type(e).__name__}\n")
    
    if "timeout" in str(e).lower() or "connection" in str(e).lower():
        print("💡 Network timeout (expected on mobile hotspot)")
        print("   - Try again with WiFi connection")
        print("   - Or use shorter duration (4s)")

print("\n" + "="*80)
