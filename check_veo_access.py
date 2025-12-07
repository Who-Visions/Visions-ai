"""
Quick diagnostic for Veo 3.1 availability
"""
from google import genai

PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"

print("🔍 Checking Veo 3.1 availability...")
print(f"   Project: {PROJECT_ID}")
print(f"   Location: {LOCATION}\n")

try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    print("✅ Client created successfully\n")
    
    # Try to list models
    print("📋 Attempting to list available models...")
    try:
        models = client.models.list()
        print(f"✅ Found {len(list(models))} models\n")
        
        # Check for Veo models
        veo_models = [m for m in client.models.list() if 'veo' in m.name.lower()]
        if veo_models:
            print(f"🎬 Veo models found: {len(veo_models)}")
            for model in veo_models:
                print(f"   - {model.name}")
        else:
            print("⚠️  No Veo models found in available models")
    except Exception as e:
        print(f"⚠️  Cannot list models: {e}")
    
    # Try simple video generation
    print("\n🎬 Attempting simple video generation...")
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt="A simple test: a ball rolling",
    )
    
    print(f"✅ Operation started: {operation.name}")
    print("   Veo 3.1 API is accessible!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"   Type: {type(e).__name__}\n")
    
    error_msg = str(e).lower()
    if "not found" in error_msg or "404" in error_msg:
        print("💡 Veo 3.1 model not available in this region/project")
        print("   Possible reasons:")
        print("   - Model only available in certain regions")
        print("   - Preview access required")
        print("   - Check: https://ai.google.dev/gemini-api/docs/models/veo")
    elif "permission" in error_msg or "403" in error_msg:
        print("💡 Permission denied")
        print("   - Verify Vertex AI API is enabled")
        print("   - Check IAM permissions for your account")
    elif "quota" in error_msg or "429" in error_msg:
        print("💡 Quota issue")
        print("   - Video generation has separate quotas")
