"""
ingest_youtube.py
Batch processes YouTube videos to extract knowledge for the Visions AI Knowledge Base.
Uses Gemini 3 Pro (via YouTubeTools) to watch and summarize videos.
"""
import os
import sys
import time
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path to import tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.youtube_tools import YouTubeTools
from config import Config

# List of videos to ingest (User provided)
# List of videos to ingest (User provided or from file)
VIDEO_LIST_FILE = "video_list.json"
VIDEO_LIST = []

if os.path.exists(VIDEO_LIST_FILE):
    try:
        with open(VIDEO_LIST_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                VIDEO_LIST = data
            elif isinstance(data, dict) and "videos" in data:
                # Convert list of URL strings to expected dict format
                VIDEO_LIST = []
                for v_url in data["videos"]:
                    # robustly finding ID
                    try:
                        v_id = v_url.split("v=")[-1].split("&")[0]
                        VIDEO_LIST.append({"url": v_url, "id": v_id})
                    except:
                        pass # Skip malformed URLs
            print(f"Loaded {len(VIDEO_LIST)} videos from {VIDEO_LIST_FILE}")
    except Exception as e:
        print(f"Error loading video list: {e}")

if not VIDEO_LIST:
    VIDEO_LIST = [] # Empty default if no file found

MAX_WORKERS = 1  # Sequential processing to avoid 429s
OUTPUT_DIR = "knowledge_base/transcripts"

def process_video(video, index, total):
    """
    Process a single video: Extract transcript/workflow and save to file.
    """
    # Initialize tools per thread to avoid "client closed" errors in multithreading
    youtube_tools = YouTubeTools(project_id=Config.VERTEX_PROJECT_ID, location=Config.VERTEX_LOCATION)
    
    video_id = video.get("id")
    video_url = video.get("url")
    output_path = os.path.join(OUTPUT_DIR, f"{video_id}.json")
    
    # Skip if already exists AND has valid content (not error)
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "error" not in content.lower():
            print(f"⏩ [{index}/{total}] Skipping {video_id} (Already valid JSON)")
            return
        else:
             print(f"🔄 [{index}/{total}] Retrying {video_id} (Previous error found)")

    print(f"🎬 [{index}/{total}] Processing {video_id}...")
    try:
        # Use simple summary for speed, or workflow for depth
        # For 'big ingestion', simple summary per video is likely safer for quotas
        # Using existing tool method
        json_result = youtube_tools.extract_workflow(video_url)
        
        # Verify if it's valid JSON
        try:
            parsed = json.loads(json_result)
            # Inject metadata
            parsed['video_id'] = video_id
            parsed['url'] = video_url
            final_content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
             # Fallback: wrap raw text in JSON structure
             print(f"   ⚠️ Invalid JSON returned for {video_id}, wrapping raw text...")
             if "Error" in json_result:
                 # Try simple analysis fallback if extraction failed
                 print(f"   ⚠️ Workflow extraction failed, trying simple analysis...")
                 simple_summary = youtube_tools.analyze_video(video_url)
                 final_content = json.dumps({
                     "video_id": video_id,
                     "url": video_url,
                     "summary": simple_summary,
                     "steps": []
                 }, indent=2)
             else:
                 final_content = json.dumps({
                     "video_id": video_id,
                     "url": video_url,
                     "raw_content": json_result
                 }, indent=2)

        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)
            
        print(f"✅ [{index}/{total}] Saved {video_id}")
        
    except Exception as e:
        print(f"❌ [{index}/{total}] Failed {video_id}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of videos to process")
    args = parser.parse_args()

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    videos = VIDEO_LIST[:args.limit] if args.limit else VIDEO_LIST
    print(f"🚀 Starting ingestion of {len(videos)} videos" + (f" (limited from {len(VIDEO_LIST)})" if args.limit else "") + "...")
    
    total = len(videos)
    
    # Sequential vs Parallel?
    # Parallel is faster but hits API rate limits hard.
    # Given >100 videos, let's use a small pool.
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, video in enumerate(videos):
            futures.append(executor.submit(process_video, video, i+1, total))
            
        for future in as_completed(futures):
            pass  # Just wait for completion
            
    print("\n✅ Ingestion complete.")

if __name__ == "__main__":
    main()
