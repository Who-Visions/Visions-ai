import json
import time
import os
import sys
import re

# Add parent dir to path to find tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.youtube_tools import YouTubeTools
from config import Config

# Configuration
INPUT_FILE = r"knowledge_base/inputs/indy_dev_dan_videos.json"
OUTPUT_DIR = r"knowledge_base/transcripts/indy_dev_dan" # Keeping dir name, but content will be JSON
INDEX_FILE = r"knowledge_base/indy_dev_dan_index.md"
INITIAL_DELAY = 10 # Vertex allows faster, but let's be safe
DELAY_INCREMENT = 5

def get_video_id(url):
    """Extracts video ID from YouTube URL."""
    try:
        match = re.search(r"v=([^&]+)", url)
        if match:
            return match.group(1)
        return url.split("/")[-1]
    except:
        return None

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def update_index(video_id, filename, title="Unknown"):
    """Appends the new transcript to the index file."""
    entry = f"- [{video_id}](file:///{os.path.abspath(filename).replace(os.sep, '/')}) - {title}\n"
    # Check if entry already exists to avoid duplicates
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            if video_id in f.read():
                return
    
    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def main():
    ensure_dir(OUTPUT_DIR)
    
    # Initialize Index if not exists
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write("# IndyDevDan Video Index (Agentic Library)\n\n")

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file {INPUT_FILE} not found.")
        return

    # Initialize Tools
    try:
        Config.validate()
        yt_tools = YouTubeTools(project_id=Config.VERTEX_PROJECT_ID, location=Config.VERTEX_LOCATION)
        print("✅ Tools initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize tools: {e}")
        return

    videos = data.get("videos", [])
    current_delay = INITIAL_DELAY

    print(f"Found {len(videos)} videos to process.")
    print(f"Starting with {current_delay}s delay...")

    for i, url in enumerate(videos):
        video_id = get_video_id(url)
        if not video_id:
            print(f"Skipping invalid URL: {url}")
            continue

        # Check if already processed (JSON)
        output_file = os.path.join(OUTPUT_DIR, f"{video_id}.json")
        if os.path.exists(output_file):
            print(f"[{i+1}/{len(videos)}] Skipping {video_id} (Already exists)")
            continue

        print(f"[{i+1}/{len(videos)}] Processing {video_id} (Vertex AI)...")
        
        # Retry loop for 429s or other transient errors
        retries = 3
        for attempt in range(retries):
            try:
                # 1. Extract Workflow/Intelligence
                # Using extract_workflow for high quality JSON
                result = yt_tools.extract_workflow(url)
                
                # 2. Validate Result
                if "error" in result.lower() and "{" in result:
                    # It returned an error JSON
                    print(f"  ⚠️  Vertex returned error: {result[:100]}...")
                    # Don't retry logic errors, but maybe rate limits?
                    if "429" in result or "quota" in result.lower():
                        raise Exception("Rate limit in response")
                    else:
                        # Save error but move on
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(result)
                        break

                # 3. Save JSON
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result)
                
                # 4. Update Index (Try to parse title)
                title = "Unknown"
                try:
                    data = json.loads(result)
                    title = data.get("title", "Unknown")
                except:
                    pass
                    
                update_index(video_id, output_file, title)
                print(f"  ✅ Saved to {output_file}")
                
                # Sleep and Reset Delay
                print(f"  -> Sleeping for {current_delay}s...")
                time.sleep(current_delay)
                current_delay = max(INITIAL_DELAY, current_delay - 2) # Recover speed slowly
                break # Success

            except Exception as e:
                print(f"  ❌ Error on attempt {attempt+1}: {e}")
                if attempt < retries - 1:
                    # Increase delay
                    current_delay += DELAY_INCREMENT
                    print(f"  -> Increasing delay to {current_delay}s and retrying...")
                    time.sleep(current_delay)
                else:
                    print(f"  ❌ Failed to process {video_id} after {retries} attempts.")
                    # Optionally save a failed placeholder?
                    break

if __name__ == "__main__":
    main()
