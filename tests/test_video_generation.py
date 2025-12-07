"""
Test Video Generation with Veo 3.1
Uses Vertex AI's Imagen API for video generation
"""
import os
import vertexai
from vertexai.preview.vision_models import VideoGenerationModel

# Configuration
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

print("="*80)
print("🎬 TESTING VIDEO GENERATION - VEO 3.1")
print("="*80)

# Video generation prompt
prompt = """
A professional photography studio shot: Slow pan across a modern photography workspace.
Camera slowly moves from left to right showing a DSLR camera on a tripod, 
professional softbox lighting, and a clean white backdrop. 
Dramatic cinematic lighting with warm tones. High quality, 4K resolution.
"""

print(f"\n📝 Prompt: {prompt.strip()}\n")

try:
    # Load the Veo model
    print("🔄 Loading Veo 3.1 model...")
    model = VideoGenerationModel.from_pretrained("veo-001")
    
    print("🎬 Generating video... (this may take 2-3 minutes)")
    
    # Generate video
    response = model.generate_videos(
        prompt=prompt,
        number_of_videos=1,
    )
    
    print(f"\n✅ Response received!")
    print(f"Videos generated: {len(response.videos)}")
    
    # Save videos
    os.makedirs("test_output/videos", exist_ok=True)
    
    for i, video in enumerate(response.videos):
        output_path = f"test_output/videos/veo_test_{i+1}.mp4"
        
        # Save video data
        with open(output_path, "wb") as f:
            f.write(video._image_bytes)
        
        file_size = os.path.getsize(output_path)
        print(f"\n📹 Video {i+1}:")
        print(f"   Saved to: {output_path}")
        print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    print("\n🎉 Video generation successful!")
    print("="*80)

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    
    if "404" in str(e):
        print("\n💡 Veo 3.1 may not be available in us-central1")
        print("   Try: us-east4 or check model availability")
    elif "403" in str(e) or "permission" in str(e).lower():
        print("\n💡 Check Vertex AI API permissions")
        print("   Enable: Vertex AI Vision API")
    elif "429" in str(e):
        print("\n💡 Quota exhausted - video generation has separate quotas")
    
    print("="*80)
