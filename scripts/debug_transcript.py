from youtube_transcript_api import YouTubeTranscriptApi
# Use a known ID
video_id = "zTcDwqopvKE"
api = YouTubeTranscriptApi()
try:
    print(f"Fetching {video_id}...")
    transcript = api.fetch(video_id)
    print(f"Transcript Type: {type(transcript)}")
    
    # Iterate and inspect first item
    count = 0
    for item in transcript:
        print(f"Item Type: {type(item)}")
        print(f"Dir Item: {dir(item)}")
        # Try attributes
        try:
            print(f"Text: {item.text}")
            print(f"Start: {item.start}")
            print(f"Duration: {item.duration}")
        except Exception as e:
            print(f"Attribute access failed: {e}")
        
        count += 1
        if count > 0: break 

except Exception as e:
    print(f"Error: {e}")
