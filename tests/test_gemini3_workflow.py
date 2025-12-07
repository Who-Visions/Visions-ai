"""
Test Gemini 3 Pro Workflow Extraction from YouTube Tutorial
"""
from tools.youtube_tools import YouTubeTools

def test_gemini3_extraction():
    print("🧠 Testing Gemini 3 Pro Workflow Extraction...")
    
    yt = YouTubeTools(project_id="endless-duality-480201-t3", location="us-central1")
    
    # The "Nano Banana" video the user initially requested
    video_url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"  # Replace with actual
    
    # Or use the Gemini 3 tutorial as a test
    test_url = "https://www.youtube.com/watch?v=ku-N-eS1lgM"
    
    print(f"\n📹 Video: {test_url}")
    print("🔬 Extracting workflow with Gemini 3 Pro + Deep Thinking...")
    
    result = yt.extract_workflow(
        test_url,
        "Extract the step-by-step workflow for using Gemini 3 Pro as shown in this tutorial"
    )
    
    print("\n" + "="*80)
    print(result)
    print("="*80)

if __name__ == "__main__":
    test_gemini3_extraction()
