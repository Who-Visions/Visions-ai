
"""
Isolated test for YouTubeTools
"""
from tools.youtube_tools import YouTubeTools

def test_tool():
    print("Testing YouTubeTools isolated...")
    # Initialize
    yt = YouTubeTools(project_id="endless-duality-480201-t3", location="us-central1")
    
    # Test Video
    url = "https://www.youtube.com/watch?v=ku-N-eS1lgM"
    print(f"Analyzing: {url}")
    
    # Call directly
    result = yt.analyze_video(url, "What are the main features of Gemini 3 mentioned?")
    print("\nResult:")
    print(result)

if __name__ == "__main__":
    test_tool()
